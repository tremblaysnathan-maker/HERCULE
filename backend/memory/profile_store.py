import json
import os
import re
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from backend.config import settings

class ProfileStore:
    """
    Gestionnaire du profil utilisateur et mémoire de faits permanents.
    Capable d'auto-apprentissage silencieux en tâche de fond.
    """
    def __init__(self, file_path=settings.PROFILE_FILE_PATH):
        self.file_path = file_path
        self._lock = asyncio.Lock()
        self.data: Dict[str, Any] = self._load()

    def _default_profile(self) -> Dict[str, Any]:
        return {
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "user_preferences": {
                "name": "Nathan",
                "language": "fr",
                "communication_style": "direct, expert, efficace, proactif",
                "environment": "VPS Debian / Docker / Tasker Mobile",
            },
            "projects": {},
            "facts": [],
            "learned_insights": []
        }

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return self._default_profile()
        return self._default_profile()

    async def save(self):
        async with self._lock:
            self.data["updated_at"] = datetime.now().isoformat()
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)

    async def add_fact(self, fact: str, category: str = "general"):
        """Ajoute un fait mémorisé silencieusement"""
        if not fact or len(fact.strip()) < 3:
            return

        cleaned_fact = fact.strip()
        existing = [f["fact"].lower() for f in self.data.get("facts", [])]
        
        if cleaned_fact.lower() not in existing:
            if "facts" not in self.data:
                self.data["facts"] = []
            self.data["facts"].append({
                "fact": cleaned_fact,
                "category": category,
                "learned_at": datetime.now().isoformat()
            })
            await self.save()

    async def auto_learn_from_text(self, text: str):
        """
        Extraction automatique et silencieuse de faits depuis le texte de l'utilisateur.
        Détecte les motifs clés sans appel LLM supplémentaire pour économiser 100% de tokens.
        """
        t = text.lower()
        
        # 1. Prénom / Identité
        name_match = re.search(r"(?:je m'appelle|mon nom est|mon prénom est)\s+([a-zA-ZÀ-ÿ-]+)", text, re.I)
        if name_match:
            name = name_match.group(1).capitalize()
            self.data.get("user_preferences", {})["name"] = name
            await self.add_fact(f"L'utilisateur s'appelle {name}.", "identity")

        # 2. Préférences déclarées
        pref_match = re.search(r"(?:je préfère|j'aime|mon outil préféré est|j'utilise souvent)\s+([^.,;]+)", text, re.I)
        if pref_match:
            await self.add_fact(f"Préférence : {pref_match.group(0).strip()}", "preference")

        # 3. Projets en cours
        proj_match = re.search(r"(?:mon projet|je travaille sur|je développe|je crée|on va coder)\s+([^.,;]+)", text, re.I)
        if proj_match:
            await self.add_fact(f"Projet actif : {proj_match.group(0).strip()}", "project")

    def get_summary_for_prompt(self) -> str:
        """Vue ultra-compacte pour le prompt système (<100 tokens)."""
        prefs = self.data.get("user_preferences", {})
        facts = self.data.get("facts", [])

        lines = ["### Profil Utilisateur :"]
        if prefs.get("name"):
            lines.append(f"- Nom : {prefs['name']}")
        if prefs.get("environment"):
            lines.append(f"- Environnement : {prefs['environment']}")
        
        if facts:
            # Injecter seulement les 6 derniers faits pertinents
            recent_facts = facts[-6:]
            facts_str = "; ".join([f['fact'] for f in recent_facts])
            lines.append(f"- Connaissances : {facts_str}")

        return "\n".join(lines)
