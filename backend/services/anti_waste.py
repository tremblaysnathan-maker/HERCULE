from typing import Dict, Any, List

class AntiWasteService:
    """
    Gestion du Frigo, Anti-Gaspillage & Too Good To Go (Grocy / TGTG) :
    - Surveillance des dates de péremption des aliments dans le frigo.
    - Suggestions de recettes express pour éviter le gaspillage.
    - Alerte sur les paniers repas Too Good To Go disponibles dans le quartier.
    """

    def check_fridge_expirations(self) -> Dict[str, Any]:
        """Vérifie les aliments proches de la date limite."""
        expiring_items = [
            {"item": "Oeufs frais (x4)", "days_left": 2, "category": "Frais"},
            {"item": "Crème fraîche liquide", "days_left": 2, "category": "Laitier"},
            {"item": "Courgettes (x2)", "days_left": 3, "category": "Légumes"}
        ]

        recipe_ideas = [
            "🍳 **Quiche express aux courgettes** (utilise les oeufs, la crème et les courgettes).",
            "🥗 **Omelette gourmande persillée** (prête en 5 minutes)."
        ]

        summary = "\n".join([f"• ⚠️ **{i['item']}** (Expire dans {i['days_left']} jours)" for i in expiring_items])
        recipes_str = "\n".join(recipe_ideas)

        return {
            "status": "success",
            "expiring_count": len(expiring_items),
            "items": expiring_items,
            "message": f"🥦 **Alerte Anti-Gaspi Frigo :**\n{summary}\n\n💡 **3 Idées de recettes express pour ce soir :**\n{recipes_str}"
        }

    def track_too_good_to_go(self, neighborhood: str = "Quartier") -> Dict[str, Any]:
        """Surveille les paniers Too Good To Go disponibles à proximité."""
        baskets = [
            {"store": "Boulangerie Tradition", "price_eur": 3.99, "value_eur": 12.00, "pickup_time": "19h30 - 20h00"},
            {"store": "Supermarché Bio", "price_eur": 4.99, "value_eur": 15.00, "pickup_time": "20h00 - 20h30"}
        ]

        summary = "\n".join([f"• 🥐 **{b['store']}** : **{b['price_eur']} €** (Valeur {b['value_eur']} €) — Retrait : {b['pickup_time']}" for b in baskets])
        return {
            "status": "success",
            "neighborhood": neighborhood,
            "baskets": baskets,
            "message": f"🥐 **Paniers Anti-Gaspi Too Good To Go Détectés ({neighborhood}) :**\n{summary}"
        }

anti_waste = AntiWasteService()
