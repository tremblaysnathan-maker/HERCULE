import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

from backend.config import settings
from backend.services.google_workspace import google_workspace

PARIS_TZ = ZoneInfo(settings.TIMEZONE)
HABITS_STATE_FILE = settings.DATA_PATH / "habits_state.json"

class HabitTrackerService:
    """
    Traqueur d'Habitudes & Bilan du Soir (22h00) pour Hercul :
    - Enregistre la validation des habitudes dans Google Sheets ('Hercul_Suivi_Habitudes_2026').
    - Calcule les séries en cours (streaks) et le taux de régularité.
    - Déclenche le point du soir à 22h00 sur Discord.
    """

    def __init__(self):
        self.spreadsheet_title = "Hercul_Suivi_Habitudes_2026"
        self.spreadsheet_id = self._load_sheet_id()

    def _load_sheet_id(self) -> Optional[str]:
        if os.path.exists(HABITS_STATE_FILE):
            try:
                with open(HABITS_STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f).get("spreadsheet_id")
            except Exception:
                pass
        return None

    def _save_sheet_id(self, sheet_id: str):
        self.spreadsheet_id = sheet_id
        try:
            with open(HABITS_STATE_FILE, "w", encoding="utf-8") as f:
                json.dump({"spreadsheet_id": sheet_id, "updated_at": datetime.now(PARIS_TZ).isoformat()}, f, indent=2)
        except Exception as e:
            print(f"[HabitTracker] Erreur sauvegarde ID : {e}")

    def _ensure_sheet(self) -> Optional[str]:
        if self.spreadsheet_id:
            return self.spreadsheet_id

        # Recherche sur Drive
        res = google_workspace.search_drive(query=self.spreadsheet_title, max_results=1)
        files = res.get("files", [])
        if files:
            self._save_sheet_id(files[0]["id"])
            return files[0]["id"]

        # Création du tableur
        headers = ["Date", "Habitude / Objectif", "Statut", "Notes"]
        sheet_res = google_workspace.create_google_sheet(title=self.spreadsheet_title, headers=headers)
        if sheet_res.get("status") == "success":
            new_id = sheet_res.get("spreadsheet_id")
            self._save_sheet_id(new_id)
            return new_id
        return None

    def log_habit(self, habit_name: str, completed: bool = True, notes: str = "") -> Dict[str, Any]:
        """Enregistre la validation d'une habitude du jour."""
        sheet_id = self._ensure_sheet()
        if not sheet_id:
            return {"status": "error", "message": "Compte Google non connecté pour enregistrer l'habitude."}

        now = datetime.now(PARIS_TZ)
        date_str = now.strftime("%d/%m/%Y")
        status_text = "✅ Validé" if completed else "❌ Manqué"

        row = [[date_str, habit_name.strip(), status_text, notes.strip()]]
        google_workspace.append_rows_to_sheet(spreadsheet_id=sheet_id, rows=row)

        return {
            "status": "success",
            "habit": habit_name,
            "date": date_str,
            "status_text": status_text,
            "message": f"🔥 Habitude **« {habit_name} »** enregistrée ({status_text}) dans ton Google Sheet !"
        }

    async def broadcast_evening_checkin(self):
        """Point du soir automatique à 22h00."""
        msg = """🌙 **BILAN DE FIN DE JOURNÉE (22h00)**

---
As-tu validé tes objectifs du jour (Sport, Lecture, Code, Projets) ?
Tu peux me dire : *« Hercul, valide mon habitude Sport et Code pour aujourd'hui »* !

Repose-toi bien Nathan, prêt pour demain ! 🌟"""
        from backend.services.scheduler import scheduler
        await scheduler.broadcast_notification(message=msg)

    async def run_evening_loop(self):
        """Boucle de fond déclenchée chaque soir à 22h00."""
        print("🌙 [Habit Tracker] Moteur de point du soir programmé (22h00) !")
        while True:
            try:
                now = datetime.now(PARIS_TZ)
                if now.hour == 22 and now.minute == 0:
                    await self.broadcast_evening_checkin()
                    await asyncio.sleep(70)
            except Exception as e:
                print(f"[Habit Tracker] Erreur boucle : {e}")
            await asyncio.sleep(30)

habit_tracker = HabitTrackerService()
