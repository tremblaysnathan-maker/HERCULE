import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from backend.config import settings

class VectorStore:
    """
    Mémoire vectorielle à long terme pour Hercul basée sur ChromaDB.
    Stocke les conversations, résumés, actions, et documents de manière persistante.
    """
    def __init__(self, persist_dir=str(settings.CHROMA_PATH)):
        self.persist_dir = persist_dir
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        # Collection pour les souvenirs épisodiques
        self.episodes = self.client.get_or_create_collection(
            name="hercul_episodic_memory",
            metadata={"description": "Souvenirs des discussions et actions passées"}
        )
        # Collection pour la base de connaissances et documents
        self.knowledge = self.client.get_or_create_collection(
            name="hercul_knowledge_base",
            metadata={"description": "Connaissances indexées, fichiers et notes"}
        )

    def add_memory(self, text: str, metadata: Optional[Dict[str, Any]] = None, collection_name: str = "episodes") -> str:
        """Enregistre un souvenir dans la mémoire à long terme."""
        if not text or not text.strip():
            return ""

        doc_id = str(uuid.uuid4())
        meta = metadata or {}
        meta["timestamp"] = datetime.now().isoformat()

        target = self.episodes if collection_name == "episodes" else self.knowledge
        target.add(
            documents=[text.strip()],
            metadatas=[meta],
            ids=[doc_id]
        )
        return doc_id

    def search_memory(self, query: str, n_results: int = settings.MAX_LONG_TERM_RECALL_RESULTS, collection_name: str = "episodes") -> List[Dict[str, Any]]:
        """Recherche sémantique dans la mémoire à long terme."""
        if not query or not query.strip():
            return []

        target = self.episodes if collection_name == "episodes" else self.knowledge
        try:
            count = target.count()
            if count == 0:
                return []
            
            actual_n = min(n_results, count)
            results = target.query(
                query_texts=[query],
                n_results=actual_n
            )
            
            memories = []
            if results and "documents" in results and results["documents"]:
                docs = results["documents"][0]
                metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
                dists = results["distances"][0] if "distances" in results else [0.0] * len(docs)
                
                for doc, meta, dist in zip(docs, metas, dists):
                    memories.append({
                        "content": doc,
                        "metadata": meta,
                        "distance": dist
                    })
            return memories
        except Exception as e:
            print(f"[VectorStore] Erreur recherche : {e}")
            return []

    def get_stats(self) -> Dict[str, int]:
        return {
            "episodic_memories_count": self.episodes.count(),
            "knowledge_items_count": self.knowledge.count()
        }
