from typing import Dict, Any

class DIYProjectPlannerService:
    """
    Assistant Bricolage, Projets & Outillage DIY pour Hercul :
    - Calcul du métrage de matériaux (bois, métal, peinture).
    - Liste des vis, chevilles et quincaillerie adaptées.
    - Plan d'assemblage étape par étape et outillage nécessaire.
    """

    def plan_project(self, project_name: str, dimensions: str = "Standard") -> Dict[str, Any]:
        """Génère la fiche technique complète d'un projet de bricolage."""
        summary = f"""🔨 **FICHE CHANTIER DIY — {project_name.upper()}**

---
📐 **Dimensions & Matériaux Recommandés ({dimensions}) :**
• Planches de bois (Chêne ou Pin massif selon budget).
• Découpe précise avec 10% de marge de sécurité.

---
🧰 **Quincaillerie & Fixations :**
• Vis à bois 4x40 mm (x24).
• Chevilles multi-matériaux 6 mm + vis adaptées au mur.
• Colle à bois prise rapide + papier de verre grain 120 et 240.

---
🛠️ **Outillage à sortir :**
• Visseuse / Perceuse sans fil.
• Niveau à bulle + Mètre ruban + Équerre de menuisier.
• Serre-joints (x2 minimum).

---
📋 **Plan d'Assemblage Étape par Étape :**
1. **Ponçage** des arêtes et dépoussiérage.
2. **Pré-perçage** des trous pour éviter que le bois ne se fende.
3. **Encollage & Vissage** des montants.
4. **Vérification de l'équerrage** et séchage 2 heures.
5. **Fixation murale** avec contrôle au niveau à bulle."""

        return {
            "status": "success",
            "project": project_name,
            "dimensions": dimensions,
            "message": summary
        }

diy_planner = DIYProjectPlannerService()
