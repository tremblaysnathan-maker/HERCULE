import re
from typing import List, Dict, Any

class TokenOptimizer:
    """
    Optimiseur de tokens de pointe pour Hercul.
    - Évaluation et compression dynamique
    - RAG conditionnel (désactivation intelligente pour les requêtes triviales)
    - Élagage d'historique ultra-précis
    """

    @staticmethod
    def estimate_tokens(text: str) -> int:
        if not text:
            return 0
        return max(1, int(len(text) / 3.6))

    @classmethod
    def estimate_messages_tokens(cls, messages: List[Dict[str, Any]]) -> int:
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total += cls.estimate_tokens(content)
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, str):
                        total += cls.estimate_tokens(part)
                    elif isinstance(part, dict) and "text" in part:
                        total += cls.estimate_tokens(part["text"])
        return total

    @staticmethod
    def should_trigger_rag(query: str) -> bool:
        """
        Détermine si la requête a réellement besoin d'une recherche vectorielle RAG.
        Permet d'économiser 1 000 à 2 000 tokens sur les messages courts, salutations et ordres directs.
        """
        q = query.strip().lower()
        if len(q) < 8:
            return False

        trivial_greetings = ["salut", "bonjour", "yo", "coucou", "hello", "merci", "ok", "d'accord", "bonne nuit", "a demain", "bye"]
        if q in trivial_greetings or any(q.startswith(g + " ") for g in trivial_greetings if len(q) < 20):
            return False

        # Déclencheurs de RAG : questions sur le passé, préférences, projets, faits
        rag_triggers = [
            "tu te rappelles", "tu te souviens", "mon projet", "mes préférences",
            "notre discussion", "qu'est ce que j'ai dit", "comment s'appelle",
            "retrouve", "recherche dans nos", "c'était quoi", "sur quoi", "historique"
        ]
        return any(t in q for t in rag_triggers) or len(q.split()) >= 7

    @staticmethod
    def should_enable_tools(query: str) -> bool:
        """
        Détermine si la requête a besoin des 40 schémas d'outils.
        Si la requête est une simple conversation, désactive les outils pour économiser ~4 500 tokens !
        """
        q = query.strip().lower()
        if len(q) < 4:
            return False

        # Mots-clés déclencheurs d'actions ou d'outils
        action_triggers = [
            "agenda", "calendar", "rdv", "rendez-vous", "réunion", "mail", "gmail", "message",
            "drive", "fichier", "document", "doc", "sheet", "pdf", "télécharge", "exporte",
            "deezer", "musique", "son", "chanson", "titre", "album", "artiste",
            "rappelle", "minuteur", "timer", "alarme", "réveil",
            "météo", "trafic", "trajet", "route", "voyage", "maps",
            "cherche", "recherche", "web", "site", "page", "capture", "screenshot",
            "chasseur", "veille", "surveille", "stock", "prix",
            "lumière", "maison", "domotique", "mode cinéma", "mode nuit",
            "sécurité", "mot de passe", "fuite", "pwned", "dark web",
            "serveur", "vps", "cpu", "ram", "disque", "santé", "system",
            "facture", "budget", "dépense", "bilan", "dimanche",
            "youtube", "vidéo", "résume", "convertis", "mp3", "mp4", "image",
            "appelle", "téléphone", "urgence"
        ]

        # Si l'un des mots-clés d'outils est présent, activer les outils
        if any(t in q for t in action_triggers):
            return True

        # Déclencheurs de questions d'actualité ou de faits récents
        if any(w in q for w in ["qui a gagné", "actualité", "aujourd'hui", "nouvelles", "cours de", "météo"]):
            return True

        # Sinon, pour les discussions courantes, désactiver les schémas d'outils
        return False

    @classmethod
    def prune_history(cls, messages: List[Dict[str, Any]], max_tokens: int = 1200) -> List[Dict[str, Any]]:
        """Élagage strict pour maintenir la conversation sous le budget de tokens."""
        if not messages:
            return []

        # Ne garder que les 6 derniers messages au maximum
        recent_msgs = messages[-6:] if len(messages) > 6 else messages

        pruned: List[Dict[str, Any]] = []
        accumulated_tokens = 0

        for msg in reversed(recent_msgs):
            # Ne conserver que le texte propre (supprimer les gros payloads function_response)
            content = msg.get("content", "")
            if isinstance(content, str):
                msg_tokens = cls.estimate_tokens(content)
                if accumulated_tokens + msg_tokens > max_tokens and len(pruned) >= 2:
                    break
                pruned.insert(0, msg)
                accumulated_tokens += msg_tokens

        return pruned

    @classmethod
    def compress_text(cls, text: str, max_chars: int = 1200) -> str:
        if not text or len(text) <= max_chars:
            return text
        
        cleaned = re.sub(r'\n\s*\n+', '\n\n', text).strip()
        if len(cleaned) <= max_chars:
            return cleaned

        half = max_chars // 2
        return f"{cleaned[:half]}\n\n[... EXTRAIT CONDENSÉ ...]\n\n{cleaned[-half:]}"
