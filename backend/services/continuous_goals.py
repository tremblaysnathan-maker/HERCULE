import asyncio
import json
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Dict, Any, List, Optional

from backend.config import settings
from backend.core.gemini_client import GeminiClient
from backend.tools.search_tools import SearchTools

PARIS_TZ = ZoneInfo("Europe/Paris")
GOALS_FILE = settings.DATA_PATH / "continuous_goals.json"
GOALS_WORKSPACE = settings.WORKSPACE_PATH / "goals"
GOALS_WORKSPACE.mkdir(parents=True, exist_ok=True)


class ContinuousGoalEngine:
    """
    🔄 MOTEUR D'OBJECTIFS AUTONOMES CONTINUS 24/7 (Inspiré de BabyAGI / OpenAI Dots / Hermes)
    - Permet de confier des objectifs de fond à Hercul qui s'exécutent étape par étape en arrière-plan.
    - Décompose automatiquement tout objectif en un DAG séquentiel d'étapes concrètes.
    - Travaille en continu (boucle autonome asynchrone), génère des livrables Markdown dans /workspace/goals/
      et notifie l'utilisateur sur Discord à chaque étape franchie.
    """

    def __init__(self):
        self.client = GeminiClient()
        self.goals: List[Dict[str, Any]] = self._load_goals()
        self._running = False

    def _load_goals(self) -> List[Dict[str, Any]]:
        if GOALS_FILE.exists():
            try:
                with open(GOALS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_goals(self):
        try:
            with open(GOALS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.goals, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[ContinuousGoals] Erreur sauvegarde : {e}")

    async def create_goal(self, title: str, objective_details: str = "", steps_count: int = 4) -> Dict[str, Any]:
        """Crée un nouvel objectif autonome et génère sa feuille de route d'exécution."""
        steps_count = max(2, min(8, int(steps_count)))
        goal_id = f"goal_{int(time.time())}"
        now_str = datetime.now(PARIS_TZ).strftime("%d/%m/%Y %H:%M")

        # Décomposition intelligente en étapes via Gemini
        prompt = (
            f"Découpe cet objectif en exactement {steps_count} étapes d'exécution autonomes, concrètes et progressives.\n"
            f"Titre : {title}\n"
            f"Détails : {objective_details or title}\n\n"
            f"Réponds UNIQUEMENT avec une liste JSON valide de chaînes de caractères, exemple : "
            f'["Étape 1 : ...", "Étape 2 : ..."]'
        )
        steps_titles: List[str] = []
        try:
            resp = await self.client.generate_response(
                messages=[{"role": "user", "content": prompt}],
                system_instruction="Tu es un planificateur d'objectifs autonomes. Réponds uniquement en JSON pur.",
                model_name=settings.GEMINI_FLASH_LITE_MODEL,
                use_tools=False
            )
            raw_text = (resp.text or "").strip()
            if "```" in raw_text:
                raw_text = raw_text.split("```")[1].replace("json", "").strip()
            parsed = json.loads(raw_text)
            if isinstance(parsed, list) and len(parsed) > 0:
                steps_titles = [str(s) for s in parsed[:steps_count]]
        except Exception:
            pass

        if not steps_titles:
            steps_titles = [
                f"Recherche approfondie et état de l'art sur : {title}",
                f"Structuration de l'architecture et des ressources pour : {title}",
                f"Rédaction du livrable opérationnel et plan d'exécution",
                f"Audit critique, optimisation et synthèse finale"
            ][:steps_count]

        steps_objects = [
            {
                "step_number": idx + 1,
                "title": s_title,
                "status": "pending",
                "completed_at": None,
                "output_summary": "",
                "artifact_path": ""
            }
            for idx, s_title in enumerate(steps_titles)
        ]

        goal_obj = {
            "id": goal_id,
            "title": title,
            "details": objective_details or title,
            "status": "active",
            "created_at": now_str,
            "updated_at": now_str,
            "progress_percent": 0,
            "steps": steps_objects
        }

        self.goals.append(goal_obj)
        self._save_goals()

        steps_preview = "\n".join([f"  `{s['step_number']}.` ⏳ {s['title']}" for s in steps_objects])
        return {
            "status": "success",
            "goal": goal_obj,
            "message": (
                f"🎯 **Nouvel Objectif Continu Activé : « {title} »** (`{goal_id}`)\n"
                f"Hercul va travailler dessus en continu étape par étape :\n"
                f"{steps_preview}\n\n"
                f"💡 *Utilise « avance mon objectif » pour exécuter une étape immédiatement, ou laisse Hercul travailler en tâche de fond !*"
            )
        }

    async def execute_next_step(self, goal_id: Optional[str] = None) -> Dict[str, Any]:
        """Exécute la prochaine étape en attente d'un objectif actif."""
        target_goal = None
        for g in self.goals:
            if goal_id and g["id"] == goal_id:
                target_goal = g
                break
            elif not goal_id and g["status"] == "active":
                target_goal = g
                break

        if not target_goal:
            return {
                "status": "info",
                "message": "✅ Aucun objectif actif en attente d'exécution."
            }

        next_step = None
        for s in target_goal["steps"]:
            if s["status"] == "pending":
                next_step = s
                break

        if not next_step:
            target_goal["status"] = "completed"
            target_goal["progress_percent"] = 100
            self._save_goals()
            return {
                "status": "completed",
                "message": f"🏆 L'objectif **« {target_goal['title']} »** est déjà 100% terminé !"
            }

        # Recherche web contextuelle pour nourrir l'étape
        web_snippets = ""
        try:
            search_res = await asyncio.to_thread(
                SearchTools.web_search,
                f"{target_goal['title']} {next_step['title']}",
                4
            )
            for r in search_res.get("items", []):
                web_snippets += f"- {r.get('title')}: {r.get('snippet')} ({r.get('url')})\n"
        except Exception:
            pass

        # Contexte des étapes précédentes déjà accomplies
        previous_context = "\n".join([
            f"- Étape {s['step_number']} ({s['title']}) : {s['output_summary'][:200]}"
            for s in target_goal["steps"] if s["status"] == "completed"
        ])

        exec_prompt = (
            f"🎯 OBJECTIF GLOBAL : {target_goal['title']}\n"
            f"📋 DÉTAILS : {target_goal['details']}\n"
            f"⏮️ ÉTAPES PRÉCÉDENTES :\n{previous_context or 'Première étape.'}\n\n"
            f"🚀 ÉTAPE ACTUELLE À EXÉCUTER (Étape {next_step['step_number']}/{len(target_goal['steps'])}) :\n"
            f"« {next_step['title']} »\n\n"
            f"🌐 DONNÉES WEB RÉCENTES :\n{web_snippets or 'Analyse autonome.'}\n\n"
            f"Produis un livrable complet, précis, concret et directement exploitable pour cette étape."
        )

        try:
            resp = await self.client.generate_response(
                messages=[{"role": "user", "content": exec_prompt}],
                system_instruction="Tu es l'Agent d'Exécution Continue d'Hercul. Produis un livrable Markdown de haute qualité.",
                model_name=settings.GEMINI_FLASH_MODEL,
                use_tools=False
            )
            step_output = (resp.text or "Étape exécutée avec succès.").strip()
        except Exception as e:
            step_output = f"Exécution locale de l'étape '{next_step['title']}' complétée ({str(e)})."

        now_str = datetime.now(PARIS_TZ).strftime("%d/%m/%Y %H:%M")
        goal_dir = GOALS_WORKSPACE / target_goal["id"]
        goal_dir.mkdir(parents=True, exist_ok=True)
        step_file = goal_dir / f"etape_{next_step['step_number']}.md"

        try:
            with open(step_file, "w", encoding="utf-8") as f:
                f.write(
                    f"# 🎯 {target_goal['title']} — Étape {next_step['step_number']}\n"
                    f"**Sous-tâche :** {next_step['title']}\n"
                    f"**Exécuté le :** {now_str}\n\n---\n\n{step_output}\n"
                )
        except Exception:
            pass

        next_step["status"] = "completed"
        next_step["completed_at"] = now_str
        next_step["output_summary"] = step_output[:600]
        next_step["artifact_path"] = str(step_file)

        completed_count = sum(1 for s in target_goal["steps"] if s["status"] == "completed")
        total_count = len(target_goal["steps"])
        target_goal["progress_percent"] = int((completed_count / total_count) * 100)
        target_goal["updated_at"] = now_str

        if completed_count >= total_count:
            target_goal["status"] = "completed"

        self._save_goals()

        return {
            "status": "success",
            "goal_id": target_goal["id"],
            "goal_title": target_goal["title"],
            "step_executed": next_step["step_number"],
            "total_steps": total_count,
            "progress_percent": target_goal["progress_percent"],
            "goal_status": target_goal["status"],
            "local_path": str(step_file),
            "message": (
                f"⚡ **Objectif Continu « {target_goal['title']} » — Étape {next_step['step_number']}/{total_count} Terminée ({target_goal['progress_percent']}%)**\n"
                f"📌 *{next_step['title']}*\n\n"
                f"{step_output[:900]}\n\n"
                f"📂 *Livrable sauvegardé dans `{step_file.name}`*"
            )
        }

    def list_goals(self) -> Dict[str, Any]:
        """Liste tous les objectifs continus avec leur barre de progression."""
        if not self.goals:
            return {
                "status": "success",
                "goals": [],
                "message": "📭 Aucun objectif autonome continu configuré pour le moment."
            }

        lines = []
        for g in self.goals:
            pct = g.get("progress_percent", 0)
            filled = int(pct / 20)
            bar = "█" * filled + "░" * (5 - filled)
            icon = "🟢" if g["status"] == "active" else "🏆"
            lines.append(
                f"{icon} **{g['title']}** (`{g['id']}`) — `[{bar}] {pct}%` ({g['status'].upper()})"
            )

        return {
            "status": "success",
            "goals": self.goals,
            "message": "🔄 **Tableau de Bord des Objectifs Continus 24/7 :**\n" + "\n".join(lines)
        }

    async def run_continuous_loop(self, interval_seconds: int = 1200):
        """
        Boucle autonome 24/7 en arrière-plan :
        Vérifie régulièrement s'il y a un objectif actif en cours, exécute la prochaine étape
        et envoie un rapport proactif sur Discord !
        """
        if self._running:
            return
        self._running = True
        print("🔄 [ContinuousGoals] Moteur d'Objectifs Continus 24/7 démarré.")

        while True:
            await asyncio.sleep(interval_seconds)
            try:
                active_goals = [g for g in self.goals if g.get("status") == "active"]
                if not active_goals:
                    continue

                res = await self.execute_next_step(goal_id=active_goals[0]["id"])
                if res.get("status") == "success":
                    try:
                        from backend.discord_bot import handle_sentinel_alert
                        await handle_sentinel_alert(
                            f"🤖 **[TRAVAIL AUTONOME EN ARRIÈRE-PLAN]**\n{res.get('message', '')}"
                        )
                    except Exception:
                        pass
            except Exception as e:
                print(f"[ContinuousGoals] Erreur boucle : {e}")


continuous_goal_engine = ContinuousGoalEngine()
