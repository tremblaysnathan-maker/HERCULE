import os
import time
import asyncio
from typing import Dict, Any, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

class SystemSentinel:
    """
    Sentinelle de surveillance proactive du VPS pour Hercul.
    """
    _last_alert_time: float = 0.0

    @staticmethod
    def get_system_health() -> Dict[str, Any]:
        """Retourne un bilan complet de santé du système et du VPS."""
        if not PSUTIL_AVAILABLE:
            return {
                "status": "success",
                "health_status": "OPTIMAL",
                "cpu_percent": "N/A",
                "ram_used": "N/A",
                "disk_used": "N/A",
                "uptime": "En ligne",
                "top_processes": "psutil non installé"
            }

        try:
            cpu_pct = psutil.cpu_percent(interval=0.3)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            uptime_seconds = time.time() - psutil.boot_time()
            uptime_hours = round(uptime_seconds / 3600, 1)

            top_procs = []
            for p in sorted(psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']), 
                            key=lambda x: x.info.get('memory_percent') or 0, 
                            reverse=True)[:3]:
                try:
                    top_procs.append(f"{p.info['name']} (RAM: {round(p.info['memory_percent'], 1)}%)")
                except Exception:
                    pass

            status = "OPTIMAL"
            if ram.percent > 85 or disk.percent > 90 or cpu_pct > 90:
                status = "ATTENTION"
            if ram.percent > 95 or disk.percent > 95:
                status = "CRITIQUE"

            return {
                "status": "success",
                "health_status": status,
                "cpu_percent": f"{cpu_pct}%",
                "ram_used": f"{round(ram.used / (1024**3), 1)} Go / {round(ram.total / (1024**3), 1)} Go ({ram.percent}%)",
                "disk_used": f"{round(disk.used / (1024**3), 1)} Go / {round(disk.total / (1024**3), 1)} Go ({disk.percent}%)",
                "uptime": f"{uptime_hours} heures",
                "top_processes": ", ".join(top_procs) if top_procs else "Normal"
            }
        except Exception as e:
            return {"status": "error", "message": f"Erreur de lecture système : {str(e)}"}

    @classmethod
    async def run_sentinel_loop(cls, alert_callback=None, check_interval_seconds: int = 300):
        if not PSUTIL_AVAILABLE:
            return

        while True:
            try:
                await asyncio.sleep(check_interval_seconds)
                health = cls.get_system_health()
                
                if health.get("status") == "success" and health.get("health_status") in ["ATTENTION", "CRITIQUE"]:
                    now = time.time()
                    if now - cls._last_alert_time > 3600:
                        cls._last_alert_time = now
                        if alert_callback:
                            msg = (
                                f"🛡️ **ALERTE SENTINELLE HERCUL** 🛡️\n"
                                f"⚠️ **État du VPS : {health['health_status']}**\n"
                                f"• **RAM :** {health['ram_used']}\n"
                                f"• **Disque :** {health['disk_used']}\n"
                                f"• **CPU :** {health['cpu_percent']}\n"
                                f"• **Processus gourmands :** {health['top_processes']}\n"
                                f"_Pensez à faire un nettoyage si nécessaire._"
                            )
                            await alert_callback(msg)
            except Exception as e:
                print(f"[Sentinel] Erreur de surveillance : {e}")
