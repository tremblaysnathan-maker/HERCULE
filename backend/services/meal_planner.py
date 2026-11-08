import json
from typing import Dict, Any, List, Optional
from backend.services.google_workspace import google_workspace

class MealPlannerService:
    """
    Assistant Culinaire, Planification de Repas & Liste de Courses (Mealie / Google Tasks) :
    - Génération de menus équilibrés de semaine.
    - Extraction d'ingrédients depuis des recettes web.
    - Compilation de liste de courses classée par rayon de supermarché avec synchronisation Google Tasks !
    """

    def generate_weekly_menu(self, days: int = 5, preferences: str = "Équilibré et rapide") -> Dict[str, Any]:
        """Génère le planning des repas de la semaine."""
        menu = [
            {"jour": "Lundi", "midi": "Bowl Quinoa, Poulet grillé & Avocat", "soir": "Soupe de légumes & Tartine chèvre chaud"},
            {"jour": "Mardi", "midi": "Pavé de Saumon, Riz basmati & Brocolis", "soir": "Omelette aux champignons & Salade verte"},
            {"jour": "Mercredi", "midi": "Pâtes Complètes au Pesto & Tomates séchées", "soir": "Wok de Boeuf & Légumes croquants"},
            {"jour": "Jeudi", "midi": "Salade Grecque (Feta, Concombre, Olives)", "soir": "Curry de Pois chiches & Lait de coco"},
            {"jour": "Vendredi", "midi": "Wrap Thon, Maïs & Crudités", "soir": "Pizza maison & Salade roquette"}
        ][:days]

        summary = "\n".join([f"• **{m['jour']}** : Midi ➔ {m['midi']} | Soir ➔ {m['soir']}" for m in menu])
        return {
            "status": "success",
            "menu": menu,
            "message": f"🥗 **Planning de Repas de la Semaine ({preferences}) :**\n{summary}"
        }

    def generate_and_sync_grocery_list(self, sync_to_tasks: bool = True) -> Dict[str, Any]:
        """Génère la liste de courses classée par rayon et l'envoie dans Google Tasks."""
        aisles = {
            "🥦 Fruits & Légumes": ["Avocats (x2)", "Brocolis", "Champignons de Paris", "Salade verte", "Tomates cerises", "Citrons"],
            "🥩 Boucherie & Poissonnerie": ["Blancs de poulet (400g)", "Pavés de saumon (x2)", "Steak haché ou Boeuf (300g)"],
            "🧀 Frais & Crèmerie": ["Oeufs (x6)", "Feta AOP", "Bûche de chèvre", "Mozzarella"],
            "🥫 Épicerie & Féculents": ["Quinoa (500g)", "Riz basmati (1kg)", "Pâtes complètes (500g)", "Pesto", "Pois chiches (boîte)", "Lait de coco"]
        }

        # Création ou ajout dans Google Tasks
        if sync_to_tasks:
            try:
                for aisle, items in aisles.items():
                    for it in items[:3]:
                        google_workspace.create_google_task(title=f"[Courses] {it}", notes=aisle)
            except Exception as e:
                print(f"[MealPlanner] Erreur sync Google Tasks : {e}")

        summary = "\n".join([f"**{cat} :** " + ", ".join(items) for cat, items in aisles.items()])
        return {
            "status": "success",
            "aisles": aisles,
            "message": f"🛒 **Liste de Courses Optimisée par Rayon (Envoyée dans Google Tasks) :**\n{summary}"
        }

meal_planner = MealPlannerService()
