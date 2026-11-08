import re
from typing import List, Dict, Any

class TokenOptimizer:
    """
    Optimiseur de tokens de pointe pour Hercul v3.0.
    - Évaluation et compression dynamique
    - RAG conditionnel (désactivation intelligente pour les requêtes triviales)
    - Routage d'outils couvrant l'intégralité des 50+ outils et du Swarm Multi-Agents
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

        trivial_greetings = [
            "salut", "bonjour", "yo", "coucou", "hello", "merci", "ok",
            "d'accord", "bonne nuit", "a demain", "bye", "ça va", "ca va"
        ]
        if q in trivial_greetings or any(q.startswith(g + " ") for g in trivial_greetings if len(q) < 20):
            return False

        rag_triggers = [
            "tu te rappelles", "tu te souviens", "mon projet", "mes préférences",
            "notre discussion", "qu'est ce que j'ai dit", "comment s'appelle",
            "retrouve", "recherche dans nos", "c'était quoi", "sur quoi", "historique"
        ]
        return any(t in q for t in rag_triggers) or len(q.split()) >= 7

    @staticmethod
    def should_enable_tools(query: str) -> bool:
        """
        Détermine si la requête a besoin des schémas d'outils.
        Désactive les outils uniquement pour les salutations et petites conversations pures (~4 500 tokens économisés),
        et les active pour toute demande d'action, d'analyse, de Swarm, d'objectif ou de service.
        """
        q = query.strip().lower()
        if len(q) < 4:
            return False

        # Salutations et discussions purement conversationnelles sans outils
        pure_chat = [
            "salut", "bonjour", "bonsoir", "coucou", "yo", "hello", "hey",
            "ça va", "ca va", "comment vas-tu", "comment tu vas", "merci", "merci beaucoup",
            "ok", "d'accord", "super", "parfait", "génial", "cool", "bonne nuit", "a+", "bye",
            "qui es-tu", "comment tu t'appelles", "raconte une blague", "fais une blague"
        ]
        if q in pure_chat:
            return False

        # Mots-clés déclencheurs couvrant l'intégralité des 50+ outils & Multi-Agents
        action_triggers = [
            # Google Workspace & Productivité
            "agenda", "calendar", "rdv", "rendez-vous", "réunion", "événement", "evenement",
            "mail", "gmail", "email", "message", "brouillon", "envoie",
            "drive", "fichier", "document", "doc", "sheet", "tableur", "pdf", "fusionne", "filigrane",
            "tâche", "tache", "task", "todo", "to-do", "liste", "rappel", "rappelle", "minuteur", "timer", "alarme",
            # Multi-Agents Swarm, Objectifs Continus & Compétences Auto-Évolutives
            "swarm", "escouade", "multi-agent", "multi agent", "sous-agent", "équipe d'agents",
            "objectif", "goal", "continu", "étape", "etape", "avance", "progression",
            "compétence", "competence", "skill", "forge", "outil personnalisé", "leçon", "auto-amélioration",
            # Colis, Shopping, Voyages & Mobilité
            "colis", "suivi", "tracking", "amazon", "colissimo", "ups", "dhl", "chronopost", "mondial relay", "17track",
            "météo", "meteo", "trafic", "trajet", "route", "voyage", "maps", "gps", "coordonnées", "adresse", "itinéraire", "vol", "avion", "billet",
            "leboncoin", "vinted", "deal", "promo", "prix", "stock", "chasseur", "veille", "surveille",
            # Musique, Médias, Web & Scraping
            "deezer", "musique", "son", "chanson", "titre", "album", "artiste", "playlist",
            "cherche", "recherche", "web", "site", "page", "capture", "screenshot", "scrape", "flaresolverr",
            "youtube", "vidéo", "video", "résume", "resume", "convertis", "mp3", "mp4", "image", "télécharge", "telecharge",
            # Vie Quotidienne, Cuisine, Sport, Finance, Bricolage
            "repas", "menu", "recette", "courses", "ingrédient", "frigo", "péremption", "anti-gaspi", "panier",
            "sport", "strava", "course", "entraînement", "entrainement", "récupération", "fatigue",
            "facture", "budget", "dépense", "depense", "bilan", "dimanche", "abonnement", "épargne", "splitwise", "ticket",
            "bricolage", "diy", "construire", "bois", "outil", "soirée", "soiree", "fête", "fete", "invité", "anniversaire",
            # Second Cerveau, Schémas, Langues, Apprentissage
            "canvas", "obsidian", "mindmap", "carte mentale", "note", "markdown", "miroir",
            "diagramme", "schéma", "schema", "mermaid", "architecture",
            "réécris", "reecris", "corrige", "style", "formel", "traduis", "traduction", "anglais", "espagnol",
            "anki", "flashcard", "révision", "ocr", "scanne", "qr",
            # Système, Sécurité, Radio, Domotique, Téléphone
            "lumière", "maison", "domotique", "mode cinéma", "mode nuit",
            "sécurité", "securite", "mot de passe", "fuite", "pwned", "coffre", "vault", "secret", "guardrail",
            "serveur", "vps", "cpu", "ram", "disque", "santé", "system", "docker", "terminal", "bash", "shell", "commande",
            "radio", "sdr", "fréquence", "433", "ads-b", "souris", "clavier", "clique",
            "appelle", "téléphone", "urgence", "répondeur", "vocale", "briefing", "habitude", "tasker"
        ]

        if any(t in q for t in action_triggers):
            return True

        if any(w in q for w in ["qui a gagné", "actualité", "aujourd'hui", "nouvelles", "cours de", "combien coûte", "comment faire"]):
            return True

        # Pour les requêtes longues (> 10 mots), activer les outils par sécurité
        if len(q.split()) >= 10:
            return True

        return False

    @classmethod
    def prune_history(cls, messages: List[Dict[str, Any]], max_tokens: int = 1200) -> List[Dict[str, Any]]:
        """Élagage strict pour maintenir la conversation sous le budget de tokens."""
        if not messages:
            return []

        recent_msgs = messages[-6:] if len(messages) > 6 else messages
        pruned: List[Dict[str, Any]] = []
        accumulated_tokens = 0

        for msg in reversed(recent_msgs):
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
