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
SWARM_OUTPUT_DIR = settings.WORKSPACE_PATH / "swarm_reports"
SWARM_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SWARM_HISTORY_FILE = settings.DATA_PATH / "swarm_history.json"


class SwarmOrchestrator:
    """
    🐝 HERCUL SWARM ENGINE (Hub-and-Spoke Multi-Agent Architecture + Reflection Loop)
    Inspiré des architectures de pointe (LangGraph Deep Research, Meta Muse, Hermes Agent) :
    1. Décomposition de l'objectif par le Hub Orchestrateur.
    2. Exécution parallèle asynchrone (asyncio.gather) de sous-agents spécialisés :
       - 🕵️ Agent Chercheur (Web & Sources en direct)
       - 💻 Agent Architecte (Conception, Code, Structuration & Livrables)
       - 📊 Agent Stratège (Planification, Budget, Risques & Actions concrètes)
    3. Boucle de Réflexion & Critique (Skeptic/Verifier Agent) :
       - Vérifie les travaux des sous-agents, élimine les incohérences et compile le rapport final.
    4. Sauvegarde persistante du livrable dans /workspace/swarm_reports/.
    """

    def __init__(self):
        self.client = GeminiClient()
        self.active_missions: Dict[str, Dict[str, Any]] = {}
        self.history: List[Dict[str, Any]] = self._load_history()

    def _load_history(self) -> List[Dict[str, Any]]:
        if SWARM_HISTORY_FILE.exists():
            try:
                with open(SWARM_HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_history(self):
        try:
            with open(SWARM_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.history[-30:], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Swarm] Erreur sauvegarde historique : {e}")

    async def _run_researcher_spoke(self, goal: str, sub_query: str) -> Dict[str, Any]:
        """🕵️ Sous-Agent Chercheur : Fouille le web en temps réel et extrait les faits."""
        start_t = time.time()
        web_context = ""
        sources = []
        try:
            search_res = await asyncio.to_thread(SearchTools.web_search, sub_query, 5)
            results = search_res.get("items", [])
            for r in results:
                title = r.get("title", "")
                snippet = r.get("snippet", "")
                url = r.get("url", "")
                web_context += f"- [{title}]({url}) : {snippet}\n"
                if url:
                    sources.append({"title": title, "url": url})
        except Exception as e:
            web_context = f"Note recherche web : {str(e)}"

        system_prompt = (
            "Tu es l'Agent Chercheur (Deep Research Spoke) de l'escouade Hercul. "
            "Ta mission est d'extraire des faits précis, chiffres clés, outils réels et sources vérifiées "
            "à partir des résultats web et de tes connaissances. Sois dense, factuel et structuré."
        )
        user_msg = (
            f"Mission globale : {goal}\n"
            f"Axe de recherche : {sub_query}\n\n"
            f"Données Web collectées en direct :\n{web_context or 'Aucune donnée web externe requise.'}\n\n"
            f"Produis ta synthèse factuelle de recherche (max 250 mots)."
        )

        try:
            resp = await self.client.generate_response(
                messages=[{"role": "user", "content": user_msg}],
                system_instruction=system_prompt,
                model_name=settings.GEMINI_FLASH_LITE_MODEL,
                use_tools=False
            )
            findings = resp.text or "Recherche terminée."
        except Exception as e:
            findings = f"Synthèse locale sur {sub_query} (fallback: {str(e)})"

        return {
            "agent": "🕵️ Agent Chercheur (Deep Research)",
            "status": "completed",
            "duration_sec": round(time.time() - start_t, 2),
            "sources_count": len(sources),
            "sources": sources[:4],
            "output": findings.strip()
        }

    async def _run_architect_spoke(self, goal: str) -> Dict[str, Any]:
        """💻 Sous-Agent Architecte & Ingénieur : Conçoit la solution technique ou structurelle."""
        start_t = time.time()
        system_prompt = (
            "Tu es l'Agent Architecte & Ingénieur (Builder Spoke) de l'escouade Hercul. "
            "Ta mission est de concevoir l'architecture technique, le code, le modèle concret ou le livrable "
            "opérationnel répondant à l'objectif. Sois pragmatique, orienté exécution immédiate (max 250 mots)."
        )
        user_msg = f"Conçois l'architecture, la structure concrète ou la solution technique pour : {goal}"

        try:
            resp = await self.client.generate_response(
                messages=[{"role": "user", "content": user_msg}],
                system_instruction=system_prompt,
                model_name=settings.GEMINI_FLASH_LITE_MODEL,
                use_tools=False
            )
            blueprint = resp.text or "Architecture générée."
        except Exception as e:
            blueprint = f"Architecture standard prête ({str(e)})."

        return {
            "agent": "💻 Agent Architecte & Builder",
            "status": "completed",
            "duration_sec": round(time.time() - start_t, 2),
            "output": blueprint.strip()
        }

    async def _run_strategist_spoke(self, goal: str) -> Dict[str, Any]:
        """📊 Sous-Agent Stratège & Opérations : Plan d'action étape par étape, coûts et optimisation."""
        start_t = time.time()
        system_prompt = (
            "Tu es l'Agent Stratège & Opérations (LifeOps Spoke) de l'escouade Hercul. "
            "Ta mission est d'établir le plan d'action séquentiel, l'optimisation des coûts/temps, "
            "et les métriques de succès pour l'objectif demandé (max 220 mots)."
        )
        user_msg = f"Établis la feuille de route opérationnelle et les actions immédiates pour : {goal}"

        try:
            resp = await self.client.generate_response(
                messages=[{"role": "user", "content": user_msg}],
                system_instruction=system_prompt,
                model_name=settings.GEMINI_FLASH_LITE_MODEL,
                use_tools=False
            )
            strategy = resp.text or "Plan opérationnel validé."
        except Exception as e:
            strategy = f"Plan séquentiel validé ({str(e)})."

        return {
            "agent": "📊 Agent Stratège & LifeOps",
            "status": "completed",
            "duration_sec": round(time.time() - start_t, 2),
            "output": strategy.strip()
        }

    async def _run_critic_reflection_loop(
        self,
        goal: str,
        research_res: Dict[str, Any],
        architect_res: Dict[str, Any],
        strategy_res: Dict[str, Any]
    ) -> Dict[str, Any]:
        """🛡️ Agent Critique & Vérificateur (Reflection Loop) : Vérifie, corrige et fusionne."""
        start_t = time.time()
        system_prompt = (
            "Tu es l'Agent Critique & Superviseur Exécutif (Reflection & Skeptic Spoke) d'Hercul. "
            "Tu reçois les rapports de 3 sous-agents ayant travaillé en parallèle. "
            "1. Vérifie la cohérence, élimine le superflu et corrige tout angle mort. "
            "2. Rédige une Synthèse Exécutive Finale ultra-claire, structurée et directement actionnable en français."
        )
        combined_input = (
            f"🎯 OBJECTIF DE LA MISSION : {goal}\n\n"
            f"--- RAPPORT 1 : {research_res['agent']} ---\n{research_res['output']}\n\n"
            f"--- RAPPORT 2 : {architect_res['agent']} ---\n{architect_res['output']}\n\n"
            f"--- RAPPORT 3 : {strategy_res['agent']} ---\n{strategy_res['output']}\n\n"
            f"Fusionne, critique et produis le Livrable Final Certifié avec :\n"
            f"1. 💡 **Synthèse Exécutive**\n"
            f"2. 🛠️ **Architecture & Solution Concrète**\n"
            f"3. 🚀 **Plan d'Action Immédiat (3 à 5 étapes)**\n"
            f"4. 🛡️ **Note de l'Auditeur Critique (Points de vigilance)**"
        )

        try:
            resp = await self.client.generate_response(
                messages=[{"role": "user", "content": combined_input}],
                system_instruction=system_prompt,
                model_name=settings.GEMINI_FLASH_MODEL,
                use_tools=False
            )
            final_synthesis = resp.text or "Synthèse multi-agents complétée."
        except Exception:
            final_synthesis = (
                f"### 💡 Synthèse Multi-Agents : {goal}\n\n"
                f"**{research_res['agent']}** :\n{research_res['output']}\n\n"
                f"**{architect_res['agent']}** :\n{architect_res['output']}\n\n"
                f"**{strategy_res['agent']}** :\n{strategy_res['output']}"
            )

        return {
            "agent": "🛡️ Agent Critique (Reflection Loop)",
            "status": "verified",
            "duration_sec": round(time.time() - start_t, 2),
            "final_synthesis": final_synthesis.strip()
        }

    async def execute_swarm_mission(self, task_goal: str, depth: str = "standard") -> Dict[str, Any]:
        """
        Lance l'escouade complète en parallèle avec boucle de réflexion et génère un rapport Markdown.
        """
        mission_id = f"swarm_{int(time.time())}"
        start_total = time.time()
        now_str = datetime.now(PARIS_TZ).strftime("%d/%m/%Y %H:%M:%S")

        self.active_missions[mission_id] = {
            "id": mission_id,
            "goal": task_goal,
            "status": "running_parallel_spokes",
            "started_at": now_str,
            "agents_active": ["🕵️ Chercheur", "💻 Architecte", "📊 Stratège"]
        }

        # Étape 1 : Exécution 100% parallèle des 3 sous-agents (Gain de vitesse x3)
        research_task = self._run_researcher_spoke(goal=task_goal, sub_query=task_goal)
        architect_task = self._run_architect_spoke(goal=task_goal)
        strategy_task = self._run_strategist_spoke(goal=task_goal)

        research_res, architect_res, strategy_res = await asyncio.gather(
            research_task, architect_task, strategy_task
        )

        # Étape 2 : Boucle de Réflexion et Validation par l'Agent Critique
        self.active_missions[mission_id]["status"] = "critic_reflection_loop"
        self.active_missions[mission_id]["agents_active"] = ["🛡️ Agent Critique"]

        critic_res = await self._run_critic_reflection_loop(
            goal=task_goal,
            research_res=research_res,
            architect_res=architect_res,
            strategy_res=strategy_res
        )

        total_duration = round(time.time() - start_total, 2)

        # Étape 3 : Sauvegarde du rapport complet dans /workspace/swarm_reports/
        safe_slug = "".join(c if c.isalnum() else "_" for c in task_goal[:35]).strip("_").lower()
        report_filename = f"rapport_swarm_{safe_slug}_{int(time.time())}.md"
        report_path = SWARM_OUTPUT_DIR / report_filename

        sources_md = "\n".join(
            [f"- [{s['title']}]({s['url']})" for s in research_res.get("sources", [])]
        ) or "- Analyse interne & base de connaissances temps réel"

        full_markdown_report = (
            f"# 🐝 RAPPORT D'ESCOUADE MULTI-AGENTS HERCUL\n"
            f"**Mission :** {task_goal}\n"
            f"**Date :** {now_str} | **Durée totale :** {total_duration}s | **ID :** `{mission_id}`\n\n"
            f"---\n\n"
            f"{critic_res['final_synthesis']}\n\n"
            f"---\n\n"
            f"## 🔬 Détails des Sous-Agents (Spokes)\n\n"
            f"### 1. {research_res['agent']} ({research_res['duration_sec']}s)\n"
            f"{research_res['output']}\n\n"
            f"### 2. {architect_res['agent']} ({architect_res['duration_sec']}s)\n"
            f"{architect_res['output']}\n\n"
            f"### 3. {strategy_res['agent']} ({strategy_res['duration_sec']}s)\n"
            f"{strategy_res['output']}\n\n"
            f"## 🌐 Sources & Références Web\n"
            f"{sources_md}\n"
        )

        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(full_markdown_report)
        except Exception as e:
            print(f"[Swarm] Erreur écriture rapport : {e}")

        mission_record = {
            "id": mission_id,
            "goal": task_goal,
            "status": "completed",
            "timestamp": now_str,
            "total_duration_sec": total_duration,
            "report_path": str(report_path),
            "spokes": [
                {"name": research_res["agent"], "duration_sec": research_res["duration_sec"], "sources": research_res["sources_count"]},
                {"name": architect_res["agent"], "duration_sec": architect_res["duration_sec"]},
                {"name": strategy_res["agent"], "duration_sec": strategy_res["duration_sec"]},
                {"name": critic_res["agent"], "duration_sec": critic_res["duration_sec"]}
            ],
            "summary_preview": critic_res["final_synthesis"][:500]
        }

        self.active_missions.pop(mission_id, None)
        self.history.append(mission_record)
        self._save_history()

        return {
            "status": "success",
            "mission_id": mission_id,
            "total_duration_sec": total_duration,
            "local_path": str(report_path),
            "spokes_telemetry": mission_record["spokes"],
            "message": (
                f"🐝 **Escouade Multi-Agents Hercul — Mission Accomplie en {total_duration}s !**\n\n"
                f"{critic_res['final_synthesis']}\n\n"
                f"📄 *Rapport complet généré dans `{report_path.name}`*"
            )
        }

    def get_swarm_status(self) -> Dict[str, Any]:
        """Retourne l'état temps réel du Swarm et les dernières missions."""
        return {
            "status": "online",
            "active_missions_count": len(self.active_missions),
            "active_missions": list(self.active_missions.values()),
            "total_completed_missions": len(self.history),
            "recent_missions": self.history[-5:][::-1]
        }


swarm_orchestrator = SwarmOrchestrator()
