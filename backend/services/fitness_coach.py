from typing import Dict, Any, Optional

class FitnessCoachService:
    """
    Coach Sportif, Suivi de Forme & Récupération (Strava / Google Fit / Health) :
    - Analyse des séances d'entraînement (Course à pied, Vélo, Musculation).
    - Calcul du score de récupération et conseils d'adaptation d'agenda.
    """

    def analyze_workout(self, activity_type: str = "Course à pied", distance_km: float = 5.0, duration_min: int = 28, avg_heart_rate: int = 152) -> Dict[str, Any]:
        """Analyse une séance sportive récente."""
        pace_min_km = round(duration_min / distance_km, 2) if distance_km > 0 else 0
        calories = int(duration_min * 10.5)

        summary = f"""🏃 **DÉBRIEFING SPORTIF — {activity_type.upper()}**

---
📊 **Métriques de la Séance :**
• Distance : **{distance_km} km**
• Durée : **{duration_min} minutes**
• Allure moyenne : **{pace_min_km} min/km**
• Fréquence cardiaque moyenne : **{avg_heart_rate} bpm**
• Dépense estimée : **~{calories} kcal**

---
💡 **Conseil du Coach Hercul :**
Séance bien rythmée en zone aérobie ! Pense à t'hydrater (au moins 500 ml d'eau) et prévois un coucher régulier ce soir pour optimiser la régénération musculaire."""

        return {
            "status": "success",
            "activity": activity_type,
            "distance_km": distance_km,
            "pace": pace_min_km,
            "calories": calories,
            "message": summary
        }

    def assess_recovery(self, sleep_hours: float = 7.5, resting_hr: int = 56) -> Dict[str, Any]:
        """Évalue l'état de récupération et adapte la journée."""
        readiness_score = min(100, int((sleep_hours / 8.0) * 60 + (70 - resting_hr) * 1.5))
        status_label = "🟢 Excellente" if readiness_score > 80 else "🟡 Modérée" if readiness_score > 60 else "🔴 Basse (Fatigue)"

        advice = "Tu es au sommet de ta forme ! Parfait pour attaquer des sessions de travail intenses ou une grosse séance de sport." if readiness_score > 75 else "Niveau de fatigue détecté. Allège tes tâches lourdes et privilégie une soirée calme."

        return {
            "status": "success",
            "readiness_score": readiness_score,
            "status_label": status_label,
            "sleep_hours": sleep_hours,
            "message": f"🔋 **Score de Récupération & Forme :** {readiness_score}/100 ({status_label})\n💡 {advice}"
        }

fitness_coach = FitnessCoachService()
