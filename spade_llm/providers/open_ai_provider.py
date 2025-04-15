import os
import logging
from typing import List, Dict, Any
from openai import OpenAI, OpenAIError
import asyncio
from .base_provider import LLMProvider
from ..context import ContextManager

logger = logging.getLogger("spade_llm.providers.openai")

class OpenAILLMProvider(LLMProvider):
    """
    Proveedor de LLM que utiliza la API de OpenAI.
    """

    def __init__(self,api_key: str,  model: str = "gpt-4o-mini", temperature: float = 0.7):
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.client = OpenAI(api_key=self.api_key)

    async def get_response(self, context: ContextManager) -> str:
        """
        Obtiene una respuesta del modelo de OpenAI basada en el contexto actual.
        """
        prompt = context.get_prompt()
        logger.info(f"Enviando prompt a OpenAI: {prompt}")

        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=prompt,
                temperature=self.temperature
            )
            return response.choices[0].message.content.strip()
        except OpenAIError as e:
            logger.error(f"Error al llamar a OpenAI: {e}")
            raise

    async def get_tool_calls(self, context: ContextManager) -> List[Dict[str, Any]]:
        """
        Obtiene llamadas a herramientas desde el modelo de OpenAI basadas en el contexto actual.
        """
        # Implementación futura si se requiere soporte para llamadas a herramientas
        return []
