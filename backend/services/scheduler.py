import os
import json
import uuid
import time
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import List, Dict, Any, Optional
from backend.config import settings

REMINDERS_FILE = settings.DATA_PATH / "reminders.json"
BRIEFING_FILE = settings.DATA_PATH / "briefing_config.json"
PARIS_TZ = ZoneInfo(settings.TIMEZONE)

class TaskScheduler:
    """
    Gestionnaire d'horloge ultra-précise (Europe/Paris), minuteurs à la seconde et rappels.
    """
    def __init__(self):
        self._lock = asyncio.Lock()
        self.reminders: List[Dict[str, Any]] = self._load_reminders()
        self.briefing_config: Dict[str, Any] = self._load_briefing_config()
        self.stopwatches: Dict[str, float] = {}
        self.pending_web_notifications: List[Dict[str, Any]] = []

    def get_current_time_details(self) -> Dict[str, Any]:
        now = datetime.now(PARIS_TZ)
        days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
        months = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
        
        return {
            "time": now.strftime("%H:%M:%S"),
            "hour_minute": now.strftime("%Hh%M"),
            "date": f"{days[now.weekday()]} {now.day} {months[now.month - 1]} {now.year}",
            "iso": now.isoformat(),
            "timezone": settings.TIMEZONE,
            "timestamp": now.timestamp()
        }

    def _load_reminders(self) -> List[Dict[str, Any]]:
        if os.path.exists(REMINDERS_FILE):
            try:
                with open(REMINDERS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _load_briefing_config(self) -> Dict[str, Any]:
        if os.path.exists(BRIEFING_FILE):
            try:
                with open(BRIEFING_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "enabled": True,
            "time": "08:00",
            "city": "Paris",
            "topics": "Intelligence Artificielle, Nouvelles Technologies, Espace",
            "last_sent": ""
        }

    async def save_reminders(self):
        async with self._lock:
            with open(REMINDERS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.reminders, f, indent=2, ensure_ascii=False)

    async def add_timer_or_reminder(
        self,
        message: str,
        delay_seconds: Optional[int] = None,
        delay_minutes: Optional[int] = None,
        target_time_str: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        now = datetime.now(PARIS_TZ)
        due_date = now

        if delay_seconds:
            due_date = now + timedelta(seconds=delay_seconds)
        elif delay_minutes:
            due_date = now + timedelta(minutes=delay_minutes)
        elif target_time_str:
            try:
                if ":" in target_time_str:
                    parts = [int(p) for p in target_time_str.split(":")]
                    due_date = now.replace(hour=parts[0], minute=parts[1], second=parts[2] if len(parts) > 2 else 0, microsecond=0)
                    if due_date <= now:
                        due_date += timedelta(days=1)
                else:
                    due_date = datetime.fromisoformat(target_time_str).replace(tzinfo=PARIS_TZ)
            except Exception:
                due_date = now + timedelta(minutes=15)
        else:
            due_date = now + timedelta(minutes=15)

        reminder_id = str(uuid.uuid4())[:8]
        reminder = {
            "id": reminder_id,
            "message": message.strip(),
            "created_at": now.isoformat(),
            "due_at": due_date.isoformat(),
            "due_timestamp": due_date.timestamp(),
            "user_id": str(user_id) if user_id else None,
            "status": "pending"
        }

        self.reminders.append(reminder)
        await self.save_reminders()

        human_time = due_date.strftime("%H:%M:%S")
        diff_seconds = max(1, int((due_date - now).total_seconds()))
        diff_str = f"{diff_seconds // 60} min {diff_seconds % 60}s" if diff_seconds >= 60 else f"{diff_seconds} secondes"

        print(f"⏱️ [Scheduler] Nouveau minuteur enregistré (ID: {reminder_id}) pour {human_time} ({diff_str}) : '{message}'")

        return {
            "status": "success",
            "reminder_id": reminder_id,
            "message": message,
            "due_time": human_time,
            "countdown": diff_str,
            "confirmation": f"⏱️ Minuteur réglé pour {human_time} (dans {diff_str}) : « {message} »"
        }

    def list_reminders(self) -> List[Dict[str, Any]]:
        now_ts = datetime.now(PARIS_TZ).timestamp()
        return [r for r in self.reminders if r.get("status") == "pending" and r.get("due_timestamp", 0) >= now_ts]

    async def cancel_reminder(self, reminder_id: str) -> Dict[str, Any]:
        for r in self.reminders:
            if r.get("id") == reminder_id or reminder_id.lower() == "all":
                r["status"] = "cancelled"
                await self.save_reminders()
                return {"status": "success", "message": f"Rappel {reminder_id} annulé."}
        return {"status": "error", "message": f"Rappel '{reminder_id}' non trouvé."}

    def start_stopwatch(self, timer_name: str = "default") -> Dict[str, Any]:
        self.stopwatches[timer_name] = time.time()
        return {"status": "success", "message": f"⏱️ Chronomètre '{timer_name}' démarré à 00:00:00."}

    def check_stopwatch(self, timer_name: str = "default") -> Dict[str, Any]:
        if timer_name not in self.stopwatches:
            return {"status": "error", "message": f"Aucun chronomètre actif sous le nom '{timer_name}'."}
        elapsed = time.time() - self.stopwatches[timer_name]
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        millis = int((elapsed - int(elapsed)) * 100)
        formatted = f"{minutes:02d}:{seconds:02d}.{millis:02d}"
        return {"status": "success", "elapsed_seconds": elapsed, "formatted": formatted, "message": f"⏱️ Temps écoulé : {formatted}"}

    async def run_scheduler_loop(self, reminder_notifier=None, briefing_generator=None):
        """Boucle de fond qui vérifie chaque seconde les minuteurs."""
        print("🕒 [Scheduler] Boucle d'arrière-plan du planificateur active.")
        while True:
            try:
                await asyncio.sleep(1)
                now = datetime.now(PARIS_TZ)
                now_ts = now.timestamp()
                today_str = now.strftime("%Y-%m-%d")
                current_time_str = now.strftime("%H:%M")

                due_reminders = []
                for r in self.reminders:
                    if r.get("status") == "pending":
                        due_ts = r.get("due_timestamp")
                        if not due_ts and "due_at" in r:
                            try:
                                due_ts = datetime.fromisoformat(r["due_at"]).timestamp()
                            except Exception:
                                due_ts = now_ts
                        
                        if due_ts and due_ts <= now_ts:
                            r["status"] = "completed"
                            due_reminders.append(r)

                if due_reminders:
                    await self.save_reminders()
                    for r in due_reminders:
                        print(f"🔔 [Scheduler] DÉCLENCHEMENT DU MINUTEUR : '{r['message']}'")
                        self.pending_web_notifications.append(r)
                        if reminder_notifier:
                            await reminder_notifier(r)

                cfg = self.briefing_config
                if cfg.get("enabled", True):
                    target_time = cfg.get("time", "08:00")
                    if current_time_str == target_time and cfg.get("last_sent") != today_str:
                        cfg["last_sent"] = today_str
                        if briefing_generator:
                            await briefing_generator(cfg)

            except Exception as e:
                print(f"[Scheduler] Erreur boucle : {e}")

    async def broadcast_notification(self, message: str, user_id: Optional[str] = None):
        """Diffuse une alerte proactive vers le Web et Discord."""
        notif = {
            "id": str(uuid.uuid4())[:8],
            "message": message,
            "due_at": datetime.now(PARIS_TZ).isoformat(),
            "status": "proactive_alert"
        }
        self.pending_web_notifications.append(notif)
        
        # Envoi Discord si le bot est actif
        try:
            from backend.discord_bot import bot, get_active_user_id
            target_id = user_id or get_active_user_id()
            if target_id and bot and bot.is_ready():
                user = await bot.fetch_user(int(target_id))
                if user:
                    await user.send(message)
        except Exception as e:
            print(f"[Scheduler] Erreur envoi broadcast Discord : {e}")

scheduler = TaskScheduler()
