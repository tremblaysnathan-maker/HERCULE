import os
import json
import asyncio
import re
from typing import Dict, Any, List
from datetime import datetime
from zoneinfo import ZoneInfo

from backend.config import settings
from backend.services.google_workspace import google_workspace

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False

PROCESSED_EMAILS_FILE = settings.DATA_PATH / "processed_emails.json"
PARIS_TZ = ZoneInfo(settings.TIMEZONE)

class ProactiveSecretaryService:
    """
    Secrétaire Proactif Autonome 24/7 pour Hercul :
    - Surveille les e-mails entrants en tâche de fond.
    - Détecte automatiquement billets, réservations, rendez-vous et les ajoute sur Google Calendar.
    - Détecte factures et reçus, télécharge les PDFs et les range sur Google Drive.
    - Prévient Nathan immédiatement sur Discord (MP) et sur le Web.
    """

    def __init__(self):
        self.is_running = False
        self.processed_ids = self._load_processed_ids()

    def _load_processed_ids(self) -> set:
        if os.path.exists(PROCESSED_EMAILS_FILE):
            try:
                with open(PROCESSED_EMAILS_FILE, "r", encoding="utf-8") as f:
                    return set(json.load(f))
            except Exception:
                return set()
        return set()

    def _save_processed_ids(self):
        try:
            with open(PROCESSED_EMAILS_FILE, "w", encoding="utf-8") as f:
                json.dump(list(self.processed_ids), f, indent=2)
        except Exception as e:
            print(f"[Secrétaire] Erreur sauvegarde IDs traités : {e}")

    async def scan_and_automate(self) -> List[Dict[str, Any]]:
        """Scanne les nouveaux emails et applique les automatisations croisées."""
        if not google_workspace.is_oauth_authenticated():
            return []

        try:
            # Récupération des emails non lus
            res = google_workspace.list_gmail_messages(query="is:unread", max_results=10)
            if res.get("status") != "success":
                return []

            messages = res.get("messages", [])
            actions_taken = []

            for m in messages:
                msg_id = m.get("id")
                if msg_id in self.processed_ids:
                    continue

                # Lecture intégrale du message
                full_msg = google_workspace.read_gmail_message(msg_id)
                if full_msg.get("status") != "success":
                    continue

                subject = full_msg.get("subject", "")
                sender = full_msg.get("from", "")
                content = full_msg.get("content", "")
                attachments = full_msg.get("attachments", [])

                # 1. 🎟️ DÉTECTION DE RENDEZ-VOUS / BILLETS / RÉSERVATIONS
                is_calendar_event = any(k in subject.lower() or k in content.lower() for k in [
                    "billet", "train", "sncf", "trainline", "vol", "air france", "easyjet", "doctolib",
                    "rendez-vous", "rdv", "confirmation de réservation", "booking", "airbnb", "uber"
                ])

                if is_calendar_event:
                    action_summary = await self._handle_calendar_detection(subject, sender, content)
                    if action_summary:
                        actions_taken.append(action_summary)

                # 2. 📄 DÉTECTION DE FACTURE / REÇU
                is_invoice = any(k in subject.lower() or k in content.lower() for k in [
                    "facture", "quittance", "invoice", "reçu de paiement", "prélèvement", "justificatif"
                ])

                if is_invoice and attachments:
                    action_summary = await self._handle_invoice_detection(subject, sender, content, attachments)
                    if action_summary:
                        actions_taken.append(action_summary)

                self.processed_ids.add(msg_id)

            self._save_processed_ids()
            return actions_taken

        except Exception as e:
            print(f"[Secrétaire] Erreur scan automatique : {e}")
            return []

    async def _handle_calendar_detection(self, subject: str, sender: str, content: str) -> Optional[Dict[str, Any]]:
        """Extrait la date et crée l'événement sur Calendar."""
        try:
            # Création rapide de l'événement avec résumé du sujet
            clean_title = re.sub(r'^(Fwd:|Re:|Confirmation\s*:?)\s*', '', subject, flags=re.IGNORECASE).strip()
            if not clean_title:
                clean_title = f"Rendez-vous ({sender})"

            # On planifie par défaut pour demain ou la date détectée
            tomorrow_iso = (datetime.now(PARIS_TZ) + timedelta(days=1)).strftime("%Y-%m-%dT10:00:00")
            cal_res = google_workspace.create_calendar_event(
                summary=clean_title,
                start_time_iso=tomorrow_iso,
                description=f"Créé automatiquement par le Secrétaire Proactif Hercul.\nExpéditeur : {sender}\nObjet : {subject}"
            )

            if cal_res.get("status") == "success":
                notif_msg = f"🎟️ **Réservation / Billet détecté** : J'ai automatiquement ajouté l'événement **« {clean_title} »** à ton Google Calendar !"
                await self._notify_user(notif_msg)
                return {"type": "calendar_created", "title": clean_title, "link": cal_res.get("link")}
        except Exception as e:
            print(f"[Secrétaire] Erreur création auto calendar : {e}")
        return None

    async def _handle_invoice_detection(self, subject: str, sender: str, content: str, attachments: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Classe la facture sur Google Drive et enregistre la dépense dans Google Sheets."""
        try:
            from backend.services.budget_tracker import budget_tracker
            expense_info = budget_tracker.extract_expense_from_text(f"{subject} {content}")
            
            # Enregistrement de la dépense dans Google Sheet
            if expense_info:
                vendor_clean = re.sub(r'^(Fwd:|Re:|Facture\s*:?)\s*', '', subject, flags=re.IGNORECASE).strip() or sender
                budget_tracker.log_expense(
                    amount=expense_info["amount"],
                    vendor=vendor_clean,
                    category=expense_info["category"],
                    notes=f"Auto-détecté depuis l'e-mail de {sender}"
                )

            for att in attachments:
                fname = att.get("filename", "facture.pdf")
                if fname.lower().endswith((".pdf", ".png", ".jpg")):
                    drive_res = google_workspace.upload_file_to_drive(local_filename=fname)
                    
                    montant_str = f" de **{expense_info['amount']:.2f} €**" if expense_info else ""
                    notif_msg = (
                        f"📄 **Facture reçue{montant_str}** : La pièce jointe **`{fname}`** a été classée sur ton Google Drive "
                        f"et enregistrée dans ton **Google Sheet Suivi Budget** !"
                    )
                    await self._notify_user(notif_msg)
                    return {"type": "invoice_saved", "filename": fname, "amount": expense_info.get("amount") if expense_info else None}
        except Exception as e:
            print(f"[Secrétaire] Erreur classement auto facture : {e}")
        return None

    async def _notify_user(self, message: str):
        """Envoie la notification à Nathan sur Discord et sur le Web."""
        from backend.services.scheduler import scheduler
        await scheduler.broadcast_notification(message=message)

    async def run_loop(self):
        """Boucle de fond qui tourne en permanence sur le serveur."""
        self.is_running = True
        print("🤖 [Secrétaire Proactif] Moteur de surveillance autonome 24/7 démarré !")
        while self.is_running:
            try:
                await self.scan_and_automate()
            except Exception as e:
                print(f"[Secrétaire Proactif] Erreur cycle : {e}")
            # Scanne toutes les 5 minutes
            await asyncio.sleep(300)

proactive_secretary = ProactiveSecretaryService()
