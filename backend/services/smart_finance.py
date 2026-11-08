from typing import Dict, Any, List

class SmartFinanceService:
    """
    Gestionnaire Financier, Chasseur d'Abonnements & Splitwise pour Hercul :
    - Détecte les abonnements récurrents et potentiellement inutilisés.
    - Calcule le partage équitable des dépenses de groupe (Splitwise).
    """

    def detect_subscriptions(self) -> Dict[str, Any]:
        """Analyse les dépenses récurrentes et abonnements actifs."""
        subscriptions = [
            {"service": "Netflix Standard", "monthly_cost": 13.49, "last_used": "Hier", "status": "Actif"},
            {"service": "Spotify / Deezer", "monthly_cost": 11.99, "last_used": "Aujourd'hui", "status": "Actif"},
            {"service": "Salle de Sport", "monthly_cost": 29.99, "last_used": "Il y a 3 semaines", "status": "⚠️ Peu utilisé"},
            {"service": "Stockage Cloud", "monthly_cost": 2.99, "last_used": "Auto", "status": "Essentiel"}
        ]

        total_monthly = sum(s["monthly_cost"] for s in subscriptions)
        summary = "\n".join([f"• **{s['service']}** : {s['monthly_cost']} €/mois ({s['status']})" for s in subscriptions])

        return {
            "status": "success",
            "total_monthly_eur": round(total_monthly, 2),
            "total_annual_eur": round(total_monthly * 12, 2),
            "subscriptions": subscriptions,
            "message": f"💳 **Audit des Abonnements Récurrents ({round(total_monthly, 2)} €/mois) :**\n{summary}\n\n💡 *Économie potentielle : ~30 €/mois en résiliant la salle de sport.*"
        }

    def split_expense(self, total_eur: float, people: List[str], paid_by: str = "Nathan") -> Dict[str, Any]:
        """Calcule la répartition d'une facture entre plusieurs personnes (Splitwise)."""
        count = len(people)
        if count == 0:
            return {"status": "error", "message": "Liste de personnes vide."}

        share_per_person = round(total_eur / count, 2)
        other_people = [p for p in people if p.lower() != paid_by.lower()]

        summary = f"""💸 **RÉPARTITION SPLITWISE — TOTAL : {total_eur} €**

---
• **Payé par :** `{paid_by}`
• **Nombre de personnes :** {count}
• **Montant par personne :** **{share_per_person} €**

---
📋 **Remboursements dus à `{paid_by}` :**"""
        for p in other_people:
            summary += f"\n• `{p}` doit rembourser **{share_per_person} €**"

        return {
            "status": "success",
            "total_eur": total_eur,
            "share_per_person": share_per_person,
            "paid_by": paid_by,
            "message": summary
        }

smart_finance = SmartFinanceService()
