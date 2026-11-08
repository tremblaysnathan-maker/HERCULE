import asyncio
from typing import Dict, Any, List, Optional
from google.genai import types
from backend.config import settings
from backend.core.gemini_client import GeminiClient
from backend.core.prompts import HERCUL_SYSTEM_INSTRUCTION, TASKER_FAST_INSTRUCTION
from backend.memory.memory_manager import MemoryManager
from backend.memory.token_optimizer import TokenOptimizer
from backend.tools.registry import ToolRegistry
from backend.services.scheduler import scheduler
from backend.services.guardrails import guardrails_service
from backend.services.skill_creator import skill_forge


class HerculAgent:
    """
    Moteur autonome ReAct & Multi-Agents pour Hercul v3.0.
    - Synchronisation temporelle temps réel (Europe/Paris)
    - Filtrage de sécurité Guardrails (<5ms)
    - Mémoire procédurale & Auto-évolution (Skill Forge)
    - Exécution proactive d'outils et du Swarm Multi-Agents
    - Optimisation de tokens maximale
    """
    def __init__(self, memory_manager: Optional[MemoryManager] = None):
        self.memory = memory_manager or MemoryManager()
        self.client = GeminiClient()

    async def chat(
        self,
        message: str,
        session_id: str = "default_session",
        fast_mode: bool = False,
        model_override: Optional[str] = None
    ) -> Dict[str, Any]:
        # 0. Garde-Fou Local (<5ms) : Détection d'injections & Urgence
        guard_check = guardrails_service.inspect_text(message)
        if not guard_check.get("is_safe", True):
            return {
                "response": "🛡️ **Garde-Fou Hercul :** Cette requête contient une tentative d'injection système non autorisée et a été bloquée.",
                "session_id": session_id,
                "model_used": "local_guardrail",
                "tools_executed": [],
                "estimated_context_tokens": 0
            }

        # 1. Récupération de l'heure et date réelles de France (Europe/Paris)
        time_info = scheduler.get_current_time_details()
        time_header = (
            f"### Contexte Temporel Actuel (France / Europe/Paris) :\n"
            f"- Date : {time_info['date']}\n"
            f"- Heure exacte : {time_info['time']} ({time_info['hour_minute']})"
        )

        # 2. Contexte calibré, mémoire vectorielle & mémoire procédurale auto-évolutive
        context_data = self.memory.build_context_for_prompt(session_id=session_id, user_query=message)
        procedural_ctx = skill_forge.get_procedural_context_for_prompt()

        system_prompt = HERCUL_SYSTEM_INSTRUCTION if not fast_mode else TASKER_FAST_INSTRUCTION
        full_system_instruction = f"{system_prompt}\n\n{time_header}\n\n{context_data['profile_context']}"
        if procedural_ctx:
            full_system_instruction += f"\n\n{procedural_ctx}"
        if context_data['relevant_memories_context']:
            full_system_instruction += f"\n\n{context_data['relevant_memories_context']}"

        messages_history: List[Dict[str, Any]] = list(context_data["pruned_history"])
        messages_history.append({"role": "user", "content": message})

        # 3. Routage Intelligent des Outils & Modèles
        enable_tools = TokenOptimizer.should_enable_tools(message) if not fast_mode else False

        if model_override:
            selected_model = model_override
        elif not enable_tools or fast_mode:
            selected_model = settings.GEMINI_FLASH_LITE_MODEL
        else:
            selected_model = settings.GEMINI_FLASH_MODEL

        tools_executed = []
        max_turns = 5
        current_turn = 0
        final_answer = ""

        self.memory.add_to_session(session_id=session_id, role="user", content=message)

        # 4. Boucle ReAct autonome optimisée
        while current_turn < max_turns:
            current_turn += 1
            try:
                response = await self.client.generate_response(
                    messages=messages_history,
                    system_instruction=full_system_instruction,
                    model_name=selected_model,
                    use_tools=enable_tools
                )
            except Exception as e:
                final_answer = f"⚠️ Erreur de communication Gemini : {str(e)}"
                break

            function_calls = []
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        function_calls.append(part.function_call)

            if not function_calls:
                final_answer = response.text or "Action effectuée avec succès."
                break

            function_response_parts = []
            for fc in function_calls:
                tool_name = fc.name
                tool_args = dict(fc.args) if fc.args else {}

                # Injection de l'user_id pour les rappels si session Discord
                if tool_name == "set_timer_or_reminder" and session_id.startswith("discord_"):
                    tool_args["user_id"] = session_id.replace("discord_", "")

                raw_output = await ToolRegistry.execute_tool(
                    name=tool_name,
                    args=tool_args,
                    memory_manager=self.memory
                )

                # Compression drastique du payload pour éviter de gonfler le contexte
                tool_output = ToolRegistry._compress_output(raw_output)

                tools_executed.append({
                    "tool": tool_name,
                    "arguments": tool_args,
                    "result": tool_output
                })

                function_response_parts.append(
                    types.Part.from_function_response(
                        name=tool_name,
                        response={"result": tool_output}
                    )
                )

            messages_history.append({
                "role": "model",
                "content": response.candidates[0].content.parts
            })
            messages_history.append({
                "role": "user",
                "content": function_response_parts
            })

        # 5. Synthèse de secours humaine intelligente si final_answer est vide ou générique
        if not final_answer or final_answer.strip() in ["", "Action effectuée avec succès.", "Action accomplie."]:
            if tools_executed:
                last_tool = tools_executed[-1]
                last_res = last_tool.get("result", {})
                if isinstance(last_res, dict) and last_res.get("message"):
                    final_answer = last_res["message"]
                elif isinstance(last_res, dict) and last_res.get("status") == "error":
                    final_answer = f"⚠️ {last_res.get('message', 'Une erreur est survenue.')}"
                else:
                    final_answer = "L'action demandée a été effectuée avec succès !"
            else:
                final_answer = "Action effectuée avec succès."

        # 6. Enregistrement & consolidation silencieuse
        self.memory.add_to_session(session_id=session_id, role="assistant", content=final_answer)

        asyncio.create_task(
            self.memory.consolidate_memory(
                session_id=session_id,
                user_message=message,
                assistant_response=final_answer
            )
        )

        return {
            "response": final_answer,
            "session_id": session_id,
            "model_used": selected_model,
            "tools_executed": tools_executed,
            "urgency": guard_check.get("urgency_level", "Normal"),
            "estimated_context_tokens": context_data["estimated_context_tokens"]
        }
