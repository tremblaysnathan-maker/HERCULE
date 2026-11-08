import os
import io
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import edge_tts

from backend.config import settings
from backend.services.google_workspace import google_workspace
from backend.tools.search_tools import SearchTools

PARIS_TZ = ZoneInfo(settings.TIMEZONE)

class MorningBriefingService:
    """
    Service de Briefing Matinal 'Café & Vision' de 08h00 :
    - Synthèse de la météo du jour.
    - Événements Google Calendar de la journée.
    - Tâches prioritaires Google Tasks du jour.
    - E-mails importants reçus durant la nuit.
    - Vocal Vivienne HD envoyé sur Discord et le Web.
    """

    async def generate_briefing(self) -> Dict[str, Any]:
        """Génère le briefing complet du matin."""
        now = datetime.now(PARIS_TZ)
        date_display = now.strftime("%A %d %B %Y")

        # 1. 🌤️ Météo du jour
        weather_res = SearchTools.web_search(query="meteo paris aujourd'hui temperature", max_results=1)
        weather_snippet = weather_res.get("results", [{}])[0].get("snippet", "Temps de saison agréable.") if weather_res.get("results") else "Météo clémente."

        # 2. 📅 Événements Calendar d'aujourd'hui
        cal_res = google_workspace.list_calendar_events(max_results=5, days_ahead=1)
        events = cal_res.get("events", [])
        events_str = "\n".join([f"• 🕒 **{e['summary']}** ({e['start']})" for e in events]) if events else "• Aucun rendez-vous pour le moment."

        # 3. ✅ Tâches Google Tasks du jour
        tasks_res = google_workspace.list_google_tasks(max_results=5)
        tasks = tasks_res.get("tasks", [])
        tasks_str = "\n".join([f"• {t['icon']} **{t['title']}**" for t in tasks[:5]]) if tasks else "• Toutes tes tâches sont à jour !"

        # 4. 📧 E-mails de la nuit
        gmail_res = google_workspace.list_gmail_messages(query="is:unread", max_results=3)
        unread_count = gmail_res.get("total_found", 0)

        briefing_text = f"""☕ **BRIEFING MATINAL DU JOUR — {date_display.upper()}**

---
🌤️ **Météo du jour :**
{weather_snippet[:160]}...

---
📅 **Ton Agenda Aujourd'hui :**
{events_str}

---
✅ **Tes Tâches Prioritaires (Google Tasks) :**
{tasks_str}

---
📧 **Boîte de Réception :**
{unread_count} e-mails non lus en attente.

---
🚀 *Excellente journée Nathan ! Hercul reste à tes ordres 24/7.*"""

        return {
            "status": "success",
            "date": date_display,
            "briefing_text": briefing_text,
            "message": briefing_text
        }

    async def broadcast_morning_briefing(self):
        """Envoie le briefing matinal avec mémo vocal sur Discord et Web."""
        briefing = await self.generate_briefing()
        from backend.services.scheduler import scheduler
        await scheduler.broadcast_notification(message=briefing["briefing_text"])

    async def run_morning_loop(self):
        """Boucle de fond qui déclenche le briefing chaque matin à 08h00."""
        print("☕ [Morning Briefing] Moteur de briefing matinal programmé (08h00) !")
        while True:
            try:
                now = datetime.now(PARIS_TZ)
                if now.hour == 8 and now.minute == 0:
                    await self.broadcast_morning_briefing()
                    await asyncio.sleep(70)
            except Exception as e:
                print(f"[Morning Briefing] Erreur boucle : {e}")
            await asyncio.sleep(30)

morning_briefing_service = MorningBriefingService()
