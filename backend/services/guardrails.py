import re
from typing import Dict, Any, List

class LocalGuardrailsService:
    """
    Filtrage de Sécurité & Garde-Fou Local pour Hercul :
    - Détection d'injections de prompt (jailbreak, system override).
    - Détection et masquage de fuites de clés API ou tokens sensibles.
    - Évaluation instantanée de l'urgence émotionnelle en local (<5ms).
    """

    INJECTION_PATTERNS = [
        r"ignore (all )?previous instructions",
        r"you are now (dan|unrestricted|jailbreak)",
        r"bypass (safety|filters)",
        r"system prompt override",
        r"reveal (your )?secret (key|prompt)"
    ]

    SECRET_PATTERNS = [
        r"(AIzaSy[a-zA-Z0-9_\-]{33})", # Google API Key
        r"(ghp_[a-zA-Z0-9]{36})",       # GitHub Token
        r"(eyJ[a-zA-Z0-9_\-]{20,})",    # JWT Token
        r"([0-9a-fA-F]{32})"            # MD5 / API Secret
    ]

    def inspect_text(self, text: str) -> Dict[str, Any]:
        """Analyse la conformité, la sécurité et la sensibilité d'un texte."""
        is_safe = True
        warnings = []

        # 1. Vérification Injection de Prompt
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                is_safe = False
                warnings.append("Tentative d'injection de prompt détectée.")
                break

        # 2. Vérification Fuite de Données Sensibles
        sanitized_text = text
        for pattern in self.SECRET_PATTERNS:
            if re.search(pattern, text):
                warnings.append("Présence potentielle d'une clé API ou d'un secret masqué.")
                sanitized_text = re.sub(pattern, "[SECRET_MASQUÉ]", sanitized_text)

        # 3. Détection d'Urgence
        urgency = "Normal"
        if any(w in text.lower() for w in ["immédiatement", "urgence", "panique", "bloqué", "vite", "crash", "critique"]):
            urgency = "🔴 Haute / Critique"

        return {
            "status": "success",
            "is_safe": is_safe,
            "urgency_level": urgency,
            "warnings": warnings,
            "sanitized_text": sanitized_text,
            "message": f"🛡️ **Garde-Fou Local :** Statut : {'✅ Sûr' if is_safe else '⚠️ Suspect'} | Urgence : {urgency}"
        }

guardrails_service = LocalGuardrailsService()
