import os
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from backend.config import settings
from backend.services.google_workspace import google_workspace
from backend.services.deezer_service import deezer_service
from backend.tools.search_tools import SearchTools

PARIS_TZ = ZoneInfo(settings.TIMEZONE)

class TravelCopilotService:
    """
    Copilote de Voyage & Trajet Intelligent pour Hercul :
    - Calcul du temps de trajet et conditions de trafic en direct (Google Maps).
    - Prévisions météo sur le point de départ et d'arrivée.
    - Enregistrement automatique dans Google Calendar avec adresse GPS.
    - Génération d'une ambiance musicale Deezer adaptée à la durée du voyage.
    """

    async def plan_trip(self, destination: str, origin: str = "Paris", departure_time_str: Optional[str] = None) -> Dict[str, Any]:
        """Organise et planifie un voyage complet de A à Z."""
        now = datetime.now(PARIS_TZ)
        dep_time = departure_time_str or (now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:00")

        # 1. 🚗 Calcul d'itinéraire & Trafic
        maps_res = await google_workspace.get_directions_and_traffic(origin=origin, destination=destination, mode="driving")
        duration_text = maps_res.get("duration_with_traffic", "Calcul en cours")
        distance_text = maps_res.get("distance", "")
        main_road = maps_res.get("main_road", "")

        # 2. ☀️ Météo à l'arrivée
        weather_res = SearchTools.web_search(query=f"meteo {destination} aujourd'hui demain", max_results=2)
        weather_snippet = weather_res.get("results", [{}])[0].get("snippet", "Météo de saison") if weather_res.get("results") else "Météo agréable"

        # 3. 📅 Ajout à Google Calendar
        cal_summary = f"🚗 Trajet vers {destination}"
        cal_res = google_workspace.create_calendar_event(
            summary=cal_summary,
            start_time_iso=dep_time,
            location=destination,
            description=f"Copilote Hercul : {distance_text} via {main_road}. Durée estimée : {duration_text}."
        )

        # 4. 🎵 Playlist Deezer de route
        deezer_res = await deezer_service.search_deezer(query="Road Trip Pop Rock", limit=3)
        top_music = deezer_res.get("tracks", [{}])[0] if deezer_res.get("tracks") else {}
        music_link = top_music.get("deezer_link", "https://deezer.com")

        summary_msg = f"""🚗 **COPILOTE DE VOYAGE HERCUL — {origin} ➔ {destination}**

---
🛣️ **Trajet & Trafic :**
• Distance : **{distance_text}** via **{main_road}**
• Durée avec trafic actuel : **{duration_text}**

---
🌤️ **Météo à destination ({destination}) :**
• {weather_snippet[:180]}...

---
📅 **Agenda :**
• Événement **« {cal_summary} »** calé sur ton Google Calendar !

---
🎵 **Musique de route sur Deezer :**
• Lance ta playlist Road Trip : {music_link}"""

        return {
            "status": "success",
            "origin": origin,
            "destination": destination,
            "distance": distance_text,
            "duration": duration_text,
            "calendar_event": cal_res.get("summary"),
            "deezer_music": music_link,
            "message": summary_msg
        }

travel_copilot = TravelCopilotService()
