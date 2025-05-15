"""OpenAI-compatible provider for LLM integration."""

import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
from enum import Enum

from openai import OpenAI, OpenAIError

from .base_provider import LLMProvider
from ..context import ContextManager

logger = logging.getLogger("spade_llm.providers.openai_compatible")


class ModelFormat(Enum):
    """Supported model format conventions."""
    OPENAI = "openai"  # Standard OpenAI format (e.g., "gpt-4")
    OLLAMA = "ollama"  # Ollama format (e.g., "ollama/llama3:latest")
    CUSTOM = "custom"  # Custom format (e.g., "custom/model-name")


class OpenAICompatibleProvider(LLMProvider):
    """
    Generic LLM provider for OpenAI-compatible APIs.
    
    This provider works with any service that implements the OpenAI API specification,
    including:
    - OpenAI itself
    - Ollama (with /v1 endpoint)
    - vLLM
    - LM Studio
    - Any other OpenAI-compatible service
    
    It provides a unified interface for all these services while handling their
    specific quirks and requirements.
    """

    def __init__(self, 
                api_key: str = "dummy",  
                model: str = "gpt-4o-mini", 
                temperature: float = 0.7,
                base_url: Optional[str] = None,
                timeout: Optional[float] = None,
                max_tokens: Optional[int] = None,
                model_format: Optional[ModelFormat] = None,
                provider_name: Optional[str] = None):
        """
        Initialize the OpenAI-compatible LLM provider.
        
        Args:
            api_key: API key. For local models without auth, can be any string.
            model: The model to use. Format depends on the service.
            temperature: Temperature for generation (0.0 to 1.0).
            base_url: Base URL for the API endpoint. Examples:
                     - OpenAI: None (uses default)
                     - Ollama: "http://localhost:11434/v1"
                     - vLLM: "http://localhost:8000/v1"
                     - Custom: "https://your-api.com/v1"
            timeout: Timeout in seconds for API calls.
            max_tokens: Maximum tokens to generate.
            model_format: Format convention for model names.
            provider_name: Name of the provider for logging purposes.
        """
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.base_url = base_url
        self.timeout = timeout or 60.0
        self.max_tokens = max_tokens
        self.model_format = model_format or self._detect_model_format(model, base_url)
        self.provider_name = provider_name or self._detect_provider_name(base_url, self.model_format)
        
        # Initialize client
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
            
        logger.info(f"Initializing {self.provider_name} provider with model: {self.model}")
        if self.base_url:
            logger.info(f"Using base URL: {self.base_url}")
        
        self.client = OpenAI(**client_kwargs)

    def _detect_model_format(self, model: str, base_url: Optional[str]) -> ModelFormat:
        """Detect the model format based on the model name and base URL."""
        if model.startswith("ollama/"):
            return ModelFormat.OLLAMA
        elif model.startswith("gpt-") or model.startswith("o1-"):
            return ModelFormat.OPENAI
        elif "/" in model:
            return ModelFormat.CUSTOM
        else:
            # Default based on base_url
            if base_url and "ollama" in base_url.lower():
                return ModelFormat.OLLAMA
            return ModelFormat.OPENAI

    def _detect_provider_name(self, base_url: Optional[str], model_format: ModelFormat) -> str:
        """Detect the provider name for logging."""
        if not base_url:
            return "OpenAI"
        
        url_lower = base_url.lower()
        if "ollama" in url_lower:
            return "Ollama"
        elif "vllm" in url_lower:
            return "vLLM"
        elif "lmstudio" in url_lower:
            return "LM Studio"
        elif "localhost" in url_lower or "127.0.0.1" in url_lower:
            return "Local OpenAI-compatible"
        else:
            return "OpenAI-compatible"

    def _prepare_model_name(self, model: str) -> str:
        """Prepare the model name for the API call based on the format."""
        if self.model_format == ModelFormat.OLLAMA and model.startswith("ollama/"):
            # Remove the "ollama/" prefix for Ollama API
            return model[7:]
        return model

    async def get_llm_response(self, context: ContextManager) -> Dict[str, Any]:
        """
        Get complete response from the LLM including both text and tool calls.
        
        Args:
            context: The conversation context manager
            
        Returns:
            Dictionary containing:
            - 'text': The text response (None if there are tool calls)
            - 'tool_calls': List of tool calls (empty if there are none)
        """
        prompt = context.get_prompt()
        logger.info(f"Sending prompt to {self.provider_name} ({self.model})")
        logger.debug(f"Prompt: {prompt}")
        
        # Prepare tools if they exist
        tools = None
        if self.tools:
            tools = [tool.to_openai_tool() for tool in self.tools]
            logger.debug(f"Available tools: {[tool['function']['name'] for tool in tools]}")
        
        try:
            # Prepare the completion kwargs
            completion_kwargs = {
                "model": self._prepare_model_name(self.model),
                "messages": prompt,
                "temperature": self.temperature,
                "timeout": self.timeout
            }
            
            # Add optional parameters
            if self.max_tokens:
                completion_kwargs["max_tokens"] = self.max_tokens
            
            if tools:
                completion_kwargs["tools"] = tools
                completion_kwargs["tool_choice"] = "auto"
                
                # Note for Ollama users
                if self.provider_name == "Ollama":
                    logger.info("Using Ollama with tool support. Ensure you're using a tool-capable model (e.g., Llama 3.1+)")
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                **completion_kwargs
            )
            
            message = response.choices[0].message
            result = {'tool_calls': [], 'text': None}
            
            # Process tool calls if present
            if hasattr(message, 'tool_calls') and message.tool_calls:
                logger.info(f"{self.provider_name} suggested {len(message.tool_calls)} tool calls")
                
                tool_calls = []
                for tc in message.tool_calls:
                    try:
                        if isinstance(tc.function.arguments, str):
                            args = json.loads(tc.function.arguments)
                        else:
                            args = tc.function.arguments
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse tool arguments: {tc.function.arguments}, error: {e}")
                        args = {}
                    
                    tool_call = {
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": args
                    }
                    tool_calls.append(tool_call)
                    logger.debug(f"Tool call: {tool_call}")
                
                result['tool_calls'] = tool_calls
            else:
                content = message.content or ""
                if content:
                    logger.info(f"Received text response from {self.provider_name}: {content[:100]}...")
                else:
                    logger.warning(f"Received empty response from {self.provider_name}")
                result['text'] = content
                
            return result
            
        except OpenAIError as e:
            logger.error(f"OpenAI API error with {self.provider_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error with {self.provider_name}: {e}", exc_info=True)
            raise

    @classmethod
    def create_openai(cls, api_key: str, model: str = "gpt-4o-mini", **kwargs):
        """Factory method to create an OpenAI provider."""
        return cls(api_key=api_key, model=model, provider_name="OpenAI", **kwargs)

    @classmethod
    def create_ollama(cls, model: str = "llama3.1", 
                      base_url: str = "http://localhost:11434/v1", **kwargs):
        """
        Factory method to create an Ollama provider.
        
        Note: Ollama now supports tool calling with compatible models (e.g., Llama 3.1+).
        Ensure you're using a model that supports tools/function calling.
        
        Args:
            model: The model to use (default: llama3.1 which supports tools)
            base_url: Ollama's OpenAI-compatible endpoint (must include /v1)
            **kwargs: Additional arguments passed to the provider
        """
        if not model.startswith("ollama/"):
            model = f"ollama/{model}"
        return cls(
            api_key="dummy",
            model=model,
            base_url=base_url,
            provider_name="Ollama",
            model_format=ModelFormat.OLLAMA,
            **kwargs
        )

    @classmethod
    def create_vllm(cls, model: str, base_url: str = "http://localhost:8000/v1", **kwargs):
        """Factory method to create a vLLM provider."""
        return cls(
            api_key="dummy",
            model=model,
            base_url=base_url,
            provider_name="vLLM",
            **kwargs
        )

    @classmethod
    def create_lm_studio(cls, model: str, base_url: str = "http://localhost:1234/v1", **kwargs):
        """Factory method to create an LM Studio provider."""
        return cls(
            api_key="dummy",
            model=model,
            base_url=base_url,
            provider_name="LM Studio",
            **kwargs
        )
