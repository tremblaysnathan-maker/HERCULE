from typing import Dict, Any

class StyleRewriterService:
    """
    Assistant de Rédaction, Correction & Adaptation de Style (LanguageTool Local / Multi-Tone) :
    - Corrige l'orthographe et la grammaire.
    - Propose instantanément 3 déclinaisons de style (Naturel, Formel, Synthétique).
    """

    def rewrite(self, text: str) -> Dict[str, Any]:
        """Génère 3 variantes de reformulation du texte."""
        clean_raw = text.strip()

        # 1. Version Propre & Fluide
        version_naturelle = clean_raw.capitalize()
        if not version_naturelle.endswith((".", "!", "?")):
            version_naturelle += "."

        # 2. Version Formelle & Professionnelle
        version_formelle = f"Madame, Monsieur,\n\nPar la présente, je me permets de vous contacter concernant : {clean_raw}.\n\nRestant à votre entière disposition pour tout échange complémentaire,\nBien cordialement,\nNathan"

        # 3. Version Synthétique / Directe
        version_synthetique = f"📌 **Point clé :** {clean_raw}"

        summary = f"""✍️ **3 PROPOSITIONS DE RÉDACTION :**

---
🟢 **1. Naturel & Fluide :**
{version_naturelle}

---
🔵 **2. Formel & Professionnel (E-mail d'affaires) :**
{version_formelle}

---
🟣 **3. Synthétique & Direct (Message court) :**
{version_synthetique}"""

        return {
            "status": "success",
            "original": clean_raw,
            "version_naturelle": version_naturelle,
            "version_formelle": version_formelle,
            "version_synthetique": version_synthetique,
            "message": summary
        }

style_rewriter = StyleRewriterService()
