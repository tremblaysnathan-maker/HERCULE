import os
import json
import uuid
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

from backend.config import settings
from backend.services.browser_agent import browser_agent

PARIS_TZ = ZoneInfo(settings.TIMEZONE)
WATCH_TASKS_FILE = settings.DATA_PATH / "web_hunter_tasks.json"

class WebHunterService:
    """
    Chasseur & Veilleur Web 24/7 pour Hercul :
    - Surveille les prix, annonces, disponibilités et stocks sur n'importe quel site web.
    - Prend des captures d'écran et alerte immédiatement Nathan sur Discord en cas de changement.
    """

    def __init__(self):
        self.tasks = self._load_tasks()

    def _load_tasks(self) -> List[Dict[str, Any]]:
        if os.path.exists(WATCH_TASKS_FILE):
            try:
                with open(WATCH_TASKS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_tasks(self):
        try:
            with open(WATCH_TASKS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[WebHunter] Erreur sauvegarde tâches : {e}")

    def add_watch_task(self, url: str, condition: str, label: str) -> Dict[str, Any]:
        """Ajoute une surveillance de page web."""
        task_id = str(uuid.uuid4())[:8]
        new_task = {
            "id": task_id,
            "url": url.strip(),
            "condition": condition.strip(),
            "label": label.strip(),
            "created_at": datetime.now(PARIS_TZ).strftime("%d/%m/%Y à %H:%M"),
            "status": "active",
            "last_check": None,
            "last_result": None
        }
        self.tasks.append(new_task)
        self._save_tasks()

        return {
            "status": "success",
            "task_id": task_id,
            "label": label,
            "url": url,
            "condition": condition,
            "message": f"🕵️ Surveillance active configurée (ID: {task_id}) pour **« {label} »** sur `{url}` !"
        }

    def list_watch_tasks(self) -> Dict[str, Any]:
        """Liste les surveillances en cours."""
        return {
            "status": "success",
            "total_tasks": len(self.tasks),
            "tasks": self.tasks
        }

    def remove_watch_task(self, task_id: str) -> Dict[str, Any]:
        """Supprime une surveillance."""
        initial_len = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.get("id") != task_id and task_id.lower() != "all"]
        if len(self.tasks) < initial_len or task_id.lower() == "all":
            self._save_tasks()
            return {"status": "success", "message": f"🗑️ Surveillance {task_id} supprimée."}
        return {"status": "error", "message": f"Tâche '{task_id}' introuvable."}

    async def run_check_cycle(self) -> List[Dict[str, Any]]:
        """Exécute un cycle de vérification sur toutes les tâches actives."""
        if not self.tasks:
            return []

        alerts = []
        for t in self.tasks:
            if t.get("status") != "active":
                continue

            url = t.get("url")
            label = t.get("label")
            condition = t.get("condition")

            try:
                # Lecture de la page
                page_data = await browser_agent.browse_and_read(url)
                content = page_data.get("content", "")
                t["last_check"] = datetime.now(PARIS_TZ).strftime("%d/%m/%Y à %H:%M")

                # Détection de condition
                triggered = False
                if condition.lower() in content.lower():
                    triggered = True

                if triggered:
                    # Capture d'écran
                    shot = await browser_agent.take_page_screenshot(url)
                    msg = (
                        f"🎯 **ALERTE CHASSEUR WEB : {label}** !\n"
                        f"👉 La condition « {condition} » a été détectée sur `{url}`.\n"
                        f"📸 Capture d'écran enregistrée : `{shot.get('filename')}`"
                    )
                    from backend.services.scheduler import scheduler
                    await scheduler.broadcast_notification(message=msg)
                    alerts.append({"task_id": t["id"], "label": label, "url": url})

            except Exception as e:
                print(f"[WebHunter] Erreur scan tâche {t.get('id')} : {e}")

        self._save_tasks()
        return alerts

    async def run_loop(self):
        """Boucle de fond de surveillance 24/7."""
        print("🕵️ [Web Hunter] Moteur de surveillance web 24/7 démarré !")
        while True:
            try:
                await self.run_check_cycle()
            except Exception as e:
                print(f"[Web Hunter] Erreur boucle : {e}")
            # Vérifie toutes les 15 minutes
            await asyncio.sleep(900)

web_hunter = WebHunterService()
