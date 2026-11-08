import os
import asyncio
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from backend.config import settings
from backend.tools.registry import ToolRegistry


class GeminiClient:
    """
    Client d'orchestration asynchrone non-bloquant pour l'API Google Gemini.
    - Exécution thread-safe non-bloquante (asyncio.to_thread) pour permettre au Swarm Multi-Agents
      de tourner en parallèle à pleine vitesse.
    - Auto-Healing & Fallback intelligent de modèles en cas de surcharge ou d'erreur réseau.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    def get_tool_declarations_for_gemini(self) -> List[types.FunctionDeclaration]:
        """Convertit les outils du registre en FunctionDeclarations pour l'API Gemini."""
        declarations = []
        raw_tools = ToolRegistry.get_tool_declarations()
        for t in raw_tools:
            declarations.append(
                types.FunctionDeclaration(
                    name=t["name"],
                    description=t["description"],
                    parameters=t.get("parameters")
                )
            )
        return declarations

    async def generate_response(
        self,
        messages: List[Dict[str, Any]],
        system_instruction: str,
        model_name: Optional[str] = None,
        use_tools: bool = True
    ):
        """
        Génère une réponse avec Gemini de manière 100% asynchrone avec Auto-Healing.
        """
        if not self.client:
            raise ValueError("GEMINI_API_KEY n'est pas configurée dans le fichier .env")

        target_model = model_name or settings.GEMINI_PRO_MODEL

        config_args = {
            "system_instruction": system_instruction,
            "temperature": 0.3,
        }

        if use_tools:
            tools = [types.Tool(function_declarations=self.get_tool_declarations_for_gemini())]
            config_args["tools"] = tools

        config = types.GenerateContentConfig(**config_args)

        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            gemini_role = "model" if role in ["model", "assistant"] else "user"

            if isinstance(content, str):
                contents.append(types.Content(
                    role=gemini_role,
                    parts=[types.Part.from_text(text=content)]
                ))
            elif isinstance(content, list):
                contents.append(types.Content(
                    role=gemini_role,
                    parts=content
                ))

        # Chaîne d'Auto-Healing (Modèle demandé -> Modèle Flash configuré -> gemini-2.5-flash -> gemini-2.0-flash)
        fallback_chain = []
        for m in [target_model, settings.GEMINI_FLASH_MODEL, "gemini-2.5-flash", "gemini-2.0-flash"]:
            if m and m not in fallback_chain:
                fallback_chain.append(m)

        last_err = None
        for candidate_model in fallback_chain:
            try:
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=candidate_model,
                    contents=contents,
                    config=config
                )
                return response
            except Exception as e:
                last_err = e
                err_str = str(e).lower()
                # Si le modèle n'est pas trouvé ou surchargé, basculer automatiquement sur le suivant
                if any(k in err_str for k in ["not found", "404", "429", "quota", "unavailable", "503", "overloaded"]):
                    continue
                break

        raise last_err
