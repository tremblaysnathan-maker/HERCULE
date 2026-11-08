import os
import json
import uuid
from typing import Dict, Any, List
from backend.config import settings

class ObsidianCanvasService:
    """
    Générateur de Cartes Mentales Visuelles Obsidian Canvas (.canvas) :
    - Crée des graphes d'idées avec nœuds colorés, textes et flèches directionnelles.
    - Fichiers directement lisibles et éditables dans Obsidian.
    """

    def __init__(self):
        self.canvas_dir = settings.WORKSPACE_PATH / "canvas"
        self.canvas_dir.mkdir(parents=True, exist_ok=True)

    def create_mindmap(self, title: str, central_topic: str, subtopics: List[str]) -> Dict[str, Any]:
        """Génère un fichier .canvas avec le sujet central relié à ses sous-thèmes."""
        clean_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        file_path = self.canvas_dir / f"{clean_title}.canvas"

        center_id = "node_center"
        nodes = [
            {
                "id": center_id,
                "x": 0,
                "y": 0,
                "width": 300,
                "height": 100,
                "color": "5", # Cyan
                "text": f"## 🎯 {central_topic}"
            }
        ]
        edges = []

        colors = ["1", "2", "3", "4", "6"]
        angles = [(-350, -200), (350, -200), (-350, 200), (350, 200), (0, 300), (0, -300)]

        for i, sub in enumerate(subtopics):
            pos_x, pos_y = angles[i % len(angles)]
            n_id = f"node_sub_{i+1}"
            col = colors[i % len(colors)]

            nodes.append({
                "id": n_id,
                "x": pos_x,
                "y": pos_y,
                "width": 260,
                "height": 80,
                "color": col,
                "text": f"### {sub}"
            })

            edges.append({
                "id": f"edge_{i+1}",
                "fromNode": center_id,
                "fromSide": "right" if pos_x > 0 else "left",
                "toNode": n_id,
                "toSide": "left" if pos_x > 0 else "right"
            })

        canvas_data = {
            "nodes": nodes,
            "edges": edges
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(canvas_data, f, indent=2, ensure_ascii=False)

        return {
            "status": "success",
            "filename": f"{clean_title}.canvas",
            "local_path": str(file_path),
            "nodes_count": len(nodes),
            "message": f"🧠 **Carte Mentale Obsidian Canvas générée :** `{file_path.name}` ({len(subtopics)} branches créées) !"
        }

obsidian_canvas = ObsidianCanvasService()
