import os
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from backend.config import settings
from backend.tools.registry import ToolRegistry

class GeminiClient:
    """
    Client d'orchestration pour l'API Google Gemini.
    Prend en charge Gemini 2.5 Pro, Flash, le Tool Calling natif et la multimodalité.
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
        Génère une réponse avec Gemini en gérant les déclarations d'outils.
        """
        if not self.client:
            raise ValueError("GEMINI_API_KEY n'est pas configurée dans le fichier .env")

        target_model = model_name or settings.GEMINI_PRO_MODEL

        # Configuration des outils
        config_args = {
            "system_instruction": system_instruction,
            "temperature": 0.3,
        }

        if use_tools:
            tools = [types.Tool(function_declarations=self.get_tool_declarations_for_gemini())]
            config_args["tools"] = tools

        config = types.GenerateContentConfig(**config_args)

        # Préparation des contenus au format Gemini
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Gestion des rôles Gemini : user / model
            gemini_role = "model" if role in ["model", "assistant"] else "user"
            
            if isinstance(content, str):
                contents.append(types.Content(
                    role=gemini_role,
                    parts=[types.Part.from_text(text=content)]
                ))
            elif isinstance(content, list):
                # Contenu structuré / multi-parts (images, function calls, function responses)
                contents.append(types.Content(
                    role=gemini_role,
                    parts=content
                ))

        response = self.client.models.generate_content(
            model=target_model,
            contents=contents,
            config=config
        )
        return response
