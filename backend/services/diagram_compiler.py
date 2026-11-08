import os
from typing import Dict, Any, List
from backend.config import settings

class DiagramCompilerService:
    """
    Compilateur de Diagrammes Mermaid.js & PlantUML pour Hercul :
    - Génère du code Mermaid et des schémas d'architecture SVG/Markdown.
    - Idéal pour visualiser des workflows, bases de données et flux réseau.
    """

    def __init__(self):
        self.diagrams_dir = settings.WORKSPACE_PATH / "diagrams"
        self.diagrams_dir.mkdir(parents=True, exist_ok=True)

    def generate_diagram(self, title: str, diagram_type: str = "flowchart", elements: List[str] = None) -> Dict[str, Any]:
        """Génère un diagramme Mermaid.js complet."""
        clean_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        file_path = self.diagrams_dir / f"{clean_title}.mmd"

        mermaid_code = f"graph TD\n"
        mermaid_code += f"    Core[🧠 {title}]\n"

        if elements:
            for i, elem in enumerate(elements):
                n_id = f"Node{i+1}"
                mermaid_code += f"    Core --> {n_id}[{elem}]\n"
        else:
            mermaid_code += "    Core --> A[Frontend HUD]\n    Core --> B[Backend Agent]\n    Core --> C[Services & Outils]\n"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(mermaid_code)

        return {
            "status": "success",
            "title": title,
            "filename": f"{clean_title}.mmd",
            "local_path": str(file_path),
            "mermaid_code": mermaid_code,
            "message": f"📊 **Diagramme Mermaid généré :** `{file_path.name}` !\n```mermaid\n{mermaid_code}```"
        }

diagram_compiler = DiagramCompilerService()
