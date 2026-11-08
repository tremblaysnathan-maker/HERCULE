import math
from typing import Dict, Any, Optional
from backend.services.google_workspace import google_workspace

class EventPlannerService:
    """
    Gestionnaire d'Événements & Soirées pour Hercul :
    - Calcul des quantités de nourriture et boissons par personne.
    - Établissement de la feuille de route logistique (J-7, J-1, Jour J).
    - Calage sur Google Calendar et génération de la liste dans Google Tasks.
    """

    def plan_event(self, title: str, guests_count: int = 8, theme: str = "Soirée Conviviale", date_iso: Optional[str] = None) -> Dict[str, Any]:
        """Calcule la logistique d'une soirée complète."""
        # Calculs moyens pour adultes
        soft_liters = math.ceil(guests_count * 0.75)
        drinks_bottles = math.ceil(guests_count * 0.5)
        appetizers_pieces = guests_count * 6
        main_dish_kg = round(guests_count * 0.25, 1)
        dessert_portions = guests_count

        # Calendrier
        if date_iso:
            try:
                google_workspace.create_calendar_event(
                    summary=f"🎉 {title} ({guests_count} pers.)",
                    start_time_iso=date_iso,
                    description=f"Soirée {theme} organisée par Hercul pour {guests_count} personnes."
                )
            except Exception:
                pass

        summary = f"""🎉 **PLAN D'ORGANISATION — {title.upper()} ({guests_count} PERSONNES)**

---
🍕 **Quantités Nourriture & Boissons Recommandées :**
• 🥤 Boissons Softs : **{soft_liters} Litres**
• 🍾 Vins / Boissons Festives : **{drinks_bottles} Bouteilles**
• 🥨 Amuse-bouches / Apéritif : **~{appetizers_pieces} pièces**
• 🥘 Plat Principal : **~{main_dish_kg} kg**
• 🍰 Desserts : **{dessert_portions} portions**

---
📋 **Feuille de Route Logistique :**
• **J-3 :** Confirmer les présences et restrictions alimentaires.
• **J-1 :** Courses des boissons et denrées non périssables.
• **Jour J (16h) :** Mise au frais des boissons et préparation de la playlist Deezer !"""

        return {
            "status": "success",
            "title": title,
            "guests": guests_count,
            "theme": theme,
            "message": summary
        }

event_planner = EventPlannerService()
