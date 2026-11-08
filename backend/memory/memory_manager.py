import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.config import settings
from backend.memory.token_optimizer import TokenOptimizer
from backend.memory.profile_store import ProfileStore
from backend.memory.vector_store import VectorStore

class MemoryManager:
    """
    Gestionnaire central de mémoire pour Hercul.
    - RAG conditionnel (désactivé si inutile pour diviser la conso de tokens)
    - Auto-apprentissage silencieux en arrière-plan
    - Historique de session élagué
    """
    def __init__(self):
        self.profile = ProfileStore()
        self.vector_store = VectorStore()
        self.session_history: Dict[str, List[Dict[str, Any]]] = {}

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        if session_id not in self.session_history:
            self.session_history[session_id] = []
        return self.session_history[session_id]

    def add_to_session(self, session_id: str, role: str, content: Any):
        history = self.get_session_history(session_id)
        history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

    def build_context_for_prompt(self, session_id: str, user_query: str) -> Dict[str, Any]:
        """Construit le contexte minimal et le plus pertinent."""
        # 1. Profil permanent condensé
        profile_summary = self.profile.get_summary_for_prompt()
        
        # 2. RAG Conditionnel : Ne chercher que si la requête le nécessite
        memories_text = ""
        if TokenOptimizer.should_trigger_rag(user_query):
            relevant_memories = self.vector_store.search_memory(
                query=user_query,
                n_results=3 # Seulement 3 souvenirs max pour économiser les tokens
            )
            if relevant_memories:
                memories_list = [f"- {m['content']}" for m in relevant_memories]
                memories_text = "### Souvenirs pertinents :\n" + "\n".join(memories_list)

        # 3. Historique de session élagué
        raw_history = self.get_session_history(session_id)
        pruned_history = TokenOptimizer.prune_history(
            messages=raw_history,
            max_tokens=3000
        )

        estimated_tokens = (
            TokenOptimizer.estimate_tokens(profile_summary) +
            TokenOptimizer.estimate_tokens(memories_text) +
            TokenOptimizer.estimate_messages_tokens(pruned_history)
        )

        return {
            "profile_context": profile_summary,
            "relevant_memories_context": memories_text,
            "pruned_history": pruned_history,
            "estimated_context_tokens": estimated_tokens
        }

    async def consolidate_memory(self, session_id: str, user_message: str, assistant_response: str):
        """
        Consolidation silencieuse en tâche de fond (background).
        N'interrompt jamais l'utilisateur et ne ralentit pas la réponse.
        """
        try:
            # 1. Auto-apprentissage de faits clés
            await self.profile.auto_learn_from_text(user_message)

            # 2. Indexation vectorielle sélective (seulement si le message a du contenu substantiel)
            if len(user_message) > 15:
                entry = f"Utilisateur: {user_message}\nHercul: {assistant_response}"
                self.vector_store.add_memory(
                    text=entry,
                    metadata={"session_id": session_id}
                )
        except Exception as e:
            print(f"[Silent Memory] Erreur consolidation : {e}")

    def get_stats(self) -> Dict[str, Any]:
        return {
            "profile_facts_count": len(self.profile.data.get("facts", [])),
            "active_sessions_count": len(self.session_history),
            **self.vector_store.get_stats()
        }
