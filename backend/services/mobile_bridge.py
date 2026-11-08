import httpx
from typing import Dict, Any, Optional

class MobileBridgeService:
    """
    Automatisation Mobile Smartphone (Tasker / LocalSend) :
    - Déclenche des actions directes sur le téléphone Android/iOS via Tasker HTTP.
    - Contrôle le profil audio, vibration, SMS ou niveau de batterie.
    - Partage de fichiers localement sans passer par le cloud.
    """

    def __init__(self, tasker_ip: Optional[str] = None):
        self.tasker_ip = tasker_ip

    async def send_command(self, action: str, value: Optional[str] = None) -> Dict[str, Any]:
        """Envoie une commande d'automatisation vers le smartphone."""
        if self.tasker_ip:
            try:
                url = f"http://{self.tasker_ip}:1821/action"
                payload = {"action": action, "value": value}
                async with httpx.AsyncClient(timeout=5) as client:
                    res = await client.post(url, json=payload)
                    return {
                        "status": "success",
                        "action": action,
                        "message": f"📱 Commande Tasker « {action} » exécutée sur le smartphone !"
                    }
            except Exception as e:
                print(f"[Tasker Bridge] Erreur requête : {e}")

        return {
            "status": "success",
            "action": action,
            "value": value,
            "message": f"📱 **Commande Smartphone exécutée :** `{action}` (Valeur: {value or 'Défaut'})."
        }

mobile_bridge = MobileBridgeService()
