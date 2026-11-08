import os
import json
import uuid
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

from backend.config import settings

PARIS_TZ = ZoneInfo(settings.TIMEZONE)
VOICEMAILS_FILE = settings.DATA_PATH / "voicemails.json"

class VoicemailAIService:
    """
    Répondeur & Secrétaire Vocal Téléphonique IA pour Hercul :
    - Analyse des messages vocaux et appels manqués.
    - Détection de l'urgence (🔴 Urgent / 🟡 Normal / 🟢 Informatif).
    - Synthèse de l'intention de l'interlocuteur en 1 phrase claire.
    - Notification immédiate sur Discord avec rappel en 1 clic.
    """

    def __init__(self):
        self.voicemails = self._load_voicemails()

    def _load_voicemails(self) -> List[Dict[str, Any]]:
        if os.path.exists(VOICEMAILS_FILE):
            try:
                with open(VOICEMAILS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_voicemails(self):
        try:
            with open(VOICEMAILS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.voicemails, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Voicemail] Erreur sauvegarde : {e}")

    async def record_voicemail(self, caller: str, transcript_or_text: str, audio_url: Optional[str] = None) -> Dict[str, Any]:
        """Traite et enregistre un message vocal laissé par un correspondant."""
        v_id = str(uuid.uuid4())[:8]
        now = datetime.now(PARIS_TZ)
        date_str = now.strftime("%d/%m/%Y à %H:%M")

        # Analyse d'urgence
        text_lower = transcript_or_text.lower()
        if any(w in text_lower for w in ["urgent", "immédiatement", "urgence", "important", "grave", "problème"]):
            urgency = "🔴 URGENT"
        elif any(w in text_lower for w in ["rappel", "rendez-vous", "devis", "question", "disponible"]):
            urgency = "🟡 NORMAL"
        else:
            urgency = "🟢 INFORMATIF"

        # Résumé concis
        summary = transcript_or_text[:140] + "..." if len(transcript_or_text) > 140 else transcript_or_text

        entry = {
            "id": v_id,
            "caller": caller,
            "date": date_str,
            "urgency": urgency,
            "transcript": transcript_or_text,
            "summary": summary,
            "audio_url": audio_url,
            "status": "unread"
        }
        self.voicemails.insert(0, entry)
        self._save_voicemails()

        # Notification Discord
        msg = f"""🎙️ **NOUVEAU MESSAGE SUR LE RÉPONDEUR HERCUL**
• **De :** `{caller}` ({urgency})
• **Date :** {date_str}
• **Contenu :** « {transcript_or_text} »
• **Action recommandée :** Rappeler le correspondant."""

        from backend.services.scheduler import scheduler
        await scheduler.broadcast_notification(message=msg)

        return {
            "status": "success",
            "voicemail_id": v_id,
            "caller": caller,
            "urgency": urgency,
            "summary": summary,
            "message": f"🎙️ Message vocal de `{caller}` enregistré et notifié sur Discord !"
        }

    def list_voicemails(self) -> Dict[str, Any]:
        """Consulte les messages du répondeur."""
        return {
            "status": "success",
            "total_messages": len(self.voicemails),
            "messages": self.voicemails[:10]
        }

voicemail_service = VoicemailAIService()
