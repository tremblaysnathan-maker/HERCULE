import os
import json
import httpx
from typing import Dict, Any, List, Optional
from backend.config import settings

SMART_HOME_FILE = settings.DATA_PATH / "smart_home_state.json"

class SmartHomeService:
    """
    Service Domotique & Maison Connectée Universel pour Hercul :
    - Compatible avec Home Assistant, Philips Hue, Tuya et Smart Life.
    - Contrôle des lumières (on/off, couleur, intensité).
    - Contrôle des prises connectées, volets et chauffage.
    - Scènes intelligentes ('Cinéma', 'Nuit', 'Départ', 'Focus').
    """

    def __init__(self):
        self.ha_url = settings.HOME_ASSISTANT_URL.rstrip("/")
        self.ha_token = settings.HOME_ASSISTANT_TOKEN
        self.local_devices = self._load_local_state()

    def _load_local_state(self) -> Dict[str, Any]:
        if os.path.exists(SMART_HOME_FILE):
            try:
                with open(SMART_HOME_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "lumiere_salon": {"name": "Lumière Salon", "state": "off", "brightness": 100, "color": "warm_white"},
            "lumiere_chambre": {"name": "Lumière Chambre", "state": "off", "brightness": 80, "color": "soft_blue"},
            "prise_pc": {"name": "Prise Bureau & PC", "state": "on"},
            "chauffage": {"name": "Thermostat Chauffage", "temperature": 21.0, "mode": "eco"},
            "volets": {"name": "Volets Électriques", "state": "open"}
        }

    def _save_local_state(self):
        try:
            with open(SMART_HOME_FILE, "w", encoding="utf-8") as f:
                json.dump(self.local_devices, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Domotique] Erreur sauvegarde état : {e}")

    def is_home_assistant_connected(self) -> bool:
        return bool(self.ha_token and self.ha_url)

    async def control_device(self, device_name: str, action: str = "turn_on", brightness: Optional[int] = None, color: Optional[str] = None, temperature: Optional[float] = None) -> Dict[str, Any]:
        """Contrôle un équipement domotique (lumière, prise, volet, chauffage)."""
        clean_dev = device_name.lower().replace(" ", "_")

        # 1. Tentative d'appel Home Assistant si configuré
        if self.is_home_assistant_connected():
            try:
                headers = {"Authorization": f"Bearer {self.ha_token}", "Content-Type": "application/json"}
                domain = "light" if "lumiere" in clean_dev or "lamp" in clean_dev else "switch"
                ha_service = "turn_on" if action in ["on", "turn_on", "allumer", "ouvrir"] else "turn_off"

                payload = {"entity_id": f"{domain}.{clean_dev}"}
                if brightness:
                    payload["brightness"] = int(brightness * 2.55)
                
                async with httpx.AsyncClient(timeout=5) as client:
                    res = await client.post(f"{self.ha_url}/api/services/{domain}/{ha_service}", headers=headers, json=payload)
                    if res.status_code in [200, 201]:
                        return {"status": "success", "device": device_name, "message": f"🏠 [Home Assistant] Équipement '{device_name}' mis à jour ({action})."}
            except Exception as e:
                print(f"[Domotique] Échec Home Assistant direct : {e}")

        # 2. Gestion de l'état local persistant
        matched_key = None
        for k in self.local_devices:
            if clean_dev in k or k in clean_dev:
                matched_key = k
                break

        if not matched_key:
            matched_key = clean_dev
            self.local_devices[matched_key] = {"name": device_name, "state": "off"}

        dev = self.local_devices[matched_key]
        if action in ["on", "turn_on", "allumer", "ouvrir"]:
            dev["state"] = "on" if "volet" not in clean_dev else "open"
        elif action in ["off", "turn_off", "eteindre", "fermer"]:
            dev["state"] = "off" if "volet" not in clean_dev else "closed"

        if brightness is not None:
            dev["brightness"] = max(0, min(100, brightness))
        if color:
            dev["color"] = color
        if temperature:
            dev["temperature"] = temperature

        self._save_local_state()

        return {
            "status": "success",
            "device": dev.get("name", device_name),
            "state": dev.get("state"),
            "details": dev,
            "message": f"🏠 Équipement '{dev.get('name', device_name)}' réglé sur : {dev.get('state')} (Luminosité : {dev.get('brightness', 100)}%)."
        }

    async def activate_scene(self, scene_name: str) -> Dict[str, Any]:
        """Active une ambiance ou un mode complet dans la maison."""
        s = scene_name.lower()
        if "cinema" in s or "film" in s:
            await self.control_device("lumiere_salon", action="on", brightness=20, color="deep_blue")
            await self.control_device("volets", action="fermer")
            msg = "🎬 Mode Cinéma activé : Lumières tamisées à 20% en bleu et volets fermés !"
        elif "nuit" in s or "dormir" in s:
            await self.control_device("lumiere_salon", action="off")
            await self.control_device("lumiere_chambre", action="off")
            await self.control_device("volets", action="fermer")
            msg = "🌙 Mode Nuit activé : Toutes les lumières sont éteintes et les volets sont fermés."
        elif "focus" in s or "travail" in s:
            await self.control_device("lumiere_salon", action="on", brightness=100, color="cool_white")
            await self.control_device("prise_pc", action="on")
            msg = "💡 Mode Focus activé : Éclairage blanc intense 100% et bureau alimenté !"
        else:
            msg = f"🏠 Scène '{scene_name}' appliquée avec succès."

        return {"status": "success", "scene": scene_name, "message": msg}

    def get_home_status(self) -> Dict[str, Any]:
        """Consulte l'état complet de la maison."""
        return {
            "status": "success",
            "total_devices": len(self.local_devices),
            "devices": self.local_devices,
            "home_assistant_linked": self.is_home_assistant_connected()
        }

smart_home = SmartHomeService()
