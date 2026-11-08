import os
import json
import base64
import urllib.parse
import httpx
from typing import Dict, Any, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

from backend.config import settings

PARIS_TZ = ZoneInfo(settings.TIMEZONE)

class PhoneVoiceService:
    """
    Service de Téléphonie Vocale Réelle pour Hercul :
    - Passe de vrais appels téléphoniques sur portables ou fixes (Twilio API).
    - Lit des messages avec voix de synthèse française haute qualité.
    - Déclenche des appels de réveil ou d'urgence garantis si l'utilisateur ne répond pas sur Discord.
    """

    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_phone = settings.TWILIO_PHONE_NUMBER
        self.default_user_phone = settings.USER_PHONE_NUMBER

    def is_configured(self) -> bool:
        return bool(self.account_sid and self.auth_token and self.from_phone)

    async def make_phone_call(self, to_phone_number: str, text_to_speak: str) -> Dict[str, Any]:
        """Passe un véritable appel téléphonique et lit le texte avec la voix d'Hercul."""
        if not self.is_configured():
            return {
                "status": "simulation",
                "message": (
                    f"📞 [Simulation d'appel] Appel vers {to_phone_number} : « {text_to_speak} ».\n"
                    "💡 Pour activer les vrais appels téléphoniques, ajoute tes identifiants TWILIO_ACCOUNT_SID, "
                    "TWILIO_AUTH_TOKEN et TWILIO_PHONE_NUMBER dans ton fichier .env."
                )
            }

        try:
            # Formatage du TwiML avec voix française
            twiml_content = f"""<Response>
                <Say voice="Polly.Celine" language="fr-FR">{text_to_speak}</Say>
                <Pause length="1"/>
                <Say voice="Polly.Celine" language="fr-FR">Message terminé. Au revoir.</Say>
            </Response>"""

            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Calls.json"
            auth = (self.account_sid, self.auth_token)

            data = {
                "To": to_phone_number.strip(),
                "From": self.from_phone.strip(),
                "Twiml": twiml_content
            }

            async with httpx.AsyncClient() as client:
                res = await client.post(url, data=data, auth=auth)
                res_data = res.json()

            if res.status_code in [200, 201]:
                call_sid = res_data.get("sid")
                return {
                    "status": "success",
                    "call_sid": call_sid,
                    "to": to_phone_number,
                    "message": f"📞 Appel téléphonique en cours vers {to_phone_number} (SID: {call_sid}) !"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Erreur Twilio ({res.status_code}) : {res_data.get('message', 'Échec appel')}"
                }

        except Exception as e:
            return {"status": "error", "message": f"Erreur lors de l'appel téléphonique : {str(e)}"}

    async def trigger_emergency_call(self, reason: str, phone_number: Optional[str] = None) -> Dict[str, Any]:
        """Déclenche un appel d'urgence prioritaire vers Nathan."""
        target_phone = phone_number or self.default_user_phone
        if not target_phone:
            return {
                "status": "error",
                "message": "Aucun numéro de téléphone configuré (USER_PHONE_NUMBER dans le .env ou spécifié)."
            }

        urgent_message = f"Alerte urgente Hercul pour Nathan. Motif : {reason}. Veuillez vérifier votre serveur et vos messages immédiatement."
        return await self.make_phone_call(to_phone_number=target_phone, text_to_speak=urgent_message)

phone_service = PhoneVoiceService()
