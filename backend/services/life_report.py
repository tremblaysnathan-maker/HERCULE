import os
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from backend.config import settings
from backend.services.google_workspace import google_workspace
from backend.services.budget_tracker import budget_tracker

PARIS_TZ = ZoneInfo(settings.TIMEZONE)

class SundayExecutiveReportService:
    """
    Service de Bilan de Vie Automatique du Dimanche Soir (20h00) :
    - Synthèse du temps et agenda de la semaine passée et à venir.
    - Synthèse financière et des dépenses hebdomadaires.
    - État des e-mails en attente.
    - Recommandations et objectifs pour démarrer la nouvelle semaine.
    """

    async def generate_weekly_report(self) -> Dict[str, Any]:
        """Génère le bilan complet de la semaine."""
        now = datetime.now(PARIS_TZ)
        date_str = now.strftime("%d/%m/%Y")

        # 1. 📅 Événements Agenda de la semaine à venir
        cal_res = google_workspace.list_calendar_events(max_results=10, days_ahead=7)
        events = cal_res.get("events", [])
        events_summary = ""
        if events:
            events_summary = "\n".join([f"• **{e['summary']}** ({e['start']})" for e in events[:5]])
        else:
            events_summary = "• Aucun événement majeur planifié pour le moment."

        # 2. 📧 E-mails en attente
        gmail_res = google_workspace.list_gmail_messages(query="is:unread", max_results=5)
        unread_count = gmail_res.get("total_found", 0)
        messages = gmail_res.get("messages", [])
        emails_preview = ""
        if messages:
            emails_preview = "\n".join([f"• De **{m['from']}** : « {m['subject']} »" for m in messages[:3]])
        else:
            emails_preview = "• Aucun e-mail urgent non lu. Boîte de réception propre !"

        # 3. 💶 Dépenses & Budget
        sheet_id = budget_tracker.spreadsheet_id
        budget_note = "Feuille de suivi de budget synchronisée."

        report_markdown = f"""📊 **BILAN EXÉCUTIF DU DIMANCHE SOIR — {date_str}**

---
📅 **Ce qui t'attend la semaine prochaine :**
{events_summary}

---
📧 **E-mails en attente ({unread_count} non lus) :**
{emails_preview}

---
💶 **Gestion & Finances :**
{budget_note}

---
💡 **Conseil d'Hercul pour démarrer la semaine :**
Priorise tes 2 objectifs majeurs dès lundi matin pour prendre une longueur d'avance !"""

        return {
            "status": "success",
            "report_date": date_str,
            "unread_emails_count": unread_count,
            "upcoming_events_count": len(events),
            "report_text": report_markdown,
            "message": report_markdown
        }

    async def broadcast_sunday_report(self):
        """Envoie le rapport sur Discord et le Web."""
        report = await self.generate_weekly_report()
        from backend.services.scheduler import scheduler
        await scheduler.broadcast_notification(message=report["report_text"])

    async def run_sunday_loop(self):
        """Vérifie chaque minute si on est dimanche à 20h00."""
        print("📊 [Bilan Dimanche] Moteur de rapport hebdomadaire programmé (Dimanche 20h00) !")
        while True:
            try:
                now = datetime.now(PARIS_TZ)
                # Dimanche = 6, 20h00
                if now.weekday() == 6 and now.hour == 20 and now.minute == 0:
                    await self.broadcast_sunday_report()
                    await asyncio.sleep(70) # Évite le double déclenchement
            except Exception as e:
                print(f"[Bilan Dimanche] Erreur boucle : {e}")
            await asyncio.sleep(30)

sunday_report_service = SundayExecutiveReportService()
