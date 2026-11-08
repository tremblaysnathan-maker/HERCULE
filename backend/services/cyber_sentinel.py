import hashlib
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from backend.config import settings

PARIS_TZ = ZoneInfo(settings.TIMEZONE)

class CyberSecuritySentinel:
    """
    Sentinelle Cybersécurité & Surveillance Dark Web pour Hercul :
    - Vérifie si tes adresses e-mails ont été compromises dans des fuites de données massives.
    - Teste la sécurité de tes mots de passe via l'API officielle K-Anonymity (sans jamais envoyer ton mot de passe).
    - Fournit des audits de sécurité et des recommandations d'experts.
    """

    async def check_password_leak(self, password: str) -> Dict[str, Any]:
        """
        Vérifie si un mot de passe a fuité sur le Dark Web.
        Utilise le protocole sécurisé K-Anonymity (seuls les 5 premiers caractères du hash SHA-1 sont envoyés).
        """
        try:
            sha1_hash = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
            prefix = sha1_hash[:5]
            suffix = sha1_hash[5:]

            url = f"https://api.pwnedpasswords.com/range/{prefix}"
            headers = {"User-Agent": "Hercul-AI-Security-Sentinel"}

            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.get(url, headers=headers)

            if res.status_code != 200:
                return {"status": "error", "message": "Service de vérification indisponible."}

            hashes = res.text.splitlines()
            leak_count = 0
            for line in hashes:
                h, count = line.split(":")
                if h.strip() == suffix:
                    leak_count = int(count)
                    break

            if leak_count > 0:
                return {
                    "status": "compromised",
                    "pwned": True,
                    "occurrences": leak_count,
                    "severity": "CRITIQUE" if leak_count > 100 else "ÉLEVÉE",
                    "message": (
                        f"🚨 **DANGER DE SÉCURITÉ** : Ce mot de passe a été trouvé dans **{leak_count:,} fuites de données** sur le Dark Web !\n"
                        "👉 **Recommandation** : Ne l'utilisez JAMAIS et modifiez-le immédiatement sur tous vos comptes."
                    )
                }
            else:
                return {
                    "status": "safe",
                    "pwned": False,
                    "occurrences": 0,
                    "message": "✅ **Excellent** : Ce mot de passe n'apparaît dans aucune base de données de piratage connue !"
                }

        except Exception as e:
            return {"status": "error", "message": f"Erreur audit mot de passe : {str(e)}"}

    async def check_email_breaches(self, email_address: str) -> Dict[str, Any]:
        """Vérifie si une adresse e-mail a été compromise dans des piratages de sites connus."""
        clean_email = email_address.strip().lower()
        try:
            # Audit open-source via XposedOrNot API
            url = f"https://api.xposedornot.com/v1/check-email/{clean_email}"
            headers = {"User-Agent": "Hercul-CyberSentinel"}

            async with httpx.AsyncClient(timeout=10) as client:
                res = await client.get(url, headers=headers)

            if res.status_code == 200:
                data = res.json()
                breaches = data.get("ExposedBreaches", {}).get("breaches_details", [])
                formatted = []
                for b in breaches:
                    formatted.append({
                        "site": b.get("breach"),
                        "date": b.get("xDate"),
                        "data_leaked": b.get("details")
                    })

                return {
                    "status": "leaked",
                    "email": clean_email,
                    "total_breaches": len(formatted),
                    "breaches": formatted,
                    "message": (
                        f"⚠️ **Attention** : L'adresse `{clean_email}` a été compromise dans **{len(formatted)} fuite(s) de données** (ex: {', '.join([f['site'] for f in formatted[:3]])}).\n"
                        "👉 Pensez à activer l'authentification à double facteur (2FA)."
                    )
                }
            elif res.status_code == 404:
                return {
                    "status": "clean",
                    "email": clean_email,
                    "total_breaches": 0,
                    "message": f"🛡️ **Tout est en ordre** : L'adresse `{clean_email}` n'apparaît dans aucune fuite publique répertoriée !"
                }
            else:
                return {"status": "clean", "email": clean_email, "message": f"🛡️ L'adresse `{clean_email}` est saine."}

        except Exception as e:
            return {"status": "error", "message": f"Erreur audit e-mail : {str(e)}"}

    async def run_full_security_audit(self, email_address: Optional[str] = None) -> Dict[str, Any]:
        """Exécute un audit de sécurité complet."""
        email_to_check = email_address or os.getenv("DEFAULT_ALERT_EMAIL", "contact@example.com")
        email_report = await self.check_email_breaches(email_to_check)
        
        return {
            "status": "success",
            "timestamp": datetime.now(PARIS_TZ).strftime("%d/%m/%Y à %H:%M"),
            "target_email": email_to_check,
            "email_audit": email_report,
            "best_practices": [
                "1. Utiliser un mot de passe unique de plus de 14 caractères par compte.",
                "2. Activer l'authentification à 2 facteurs (2FA / Passkey) sur vos comptes critiques.",
                "3. Vérifier régulièrement les clés SSH autorisées sur le serveur VPS."
            ]
        }

cyber_sentinel = CyberSecuritySentinel()
