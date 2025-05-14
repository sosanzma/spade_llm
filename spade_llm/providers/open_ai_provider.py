"""OpenAI provider for LLM integration."""

import json
import logging
import asyncio
from typing import List, Dict, Any, Optional

from openai import OpenAI, OpenAIError

from .base_provider import LLMProvider
from ..context import ContextManager

logger = logging.getLogger("spade_llm.providers.openai")


class OpenAILLMProvider(LLMProvider):
    """
    LLM provider that uses the OpenAI API.
    
    This provider integrates with OpenAI's models to provide LLM capabilities
    to SPADE agents, including support for tools and function calling.
    
    It can also be used with OpenAI-compatible local APIs by providing a custom base_url.
    """

    def __init__(self, 
                api_key: str,  
                model: str = "gpt-4o-mini", 
                temperature: float = 0.7,
                base_url: Optional[str] = None,
                timeout: Optional[float] = None):
        """
        Initialize the OpenAI LLM provider.
        
        Args:
            api_key: OpenAI API key. For local models, this can be any string.
            model: The model to use.
            temperature: The temperature to use for generations.
            base_url: Optional custom base URL for OpenAI-compatible APIs (e.g., local models).
                     If not provided, uses the default OpenAI API endpoint.
            timeout: Optional timeout in seconds for API calls. Useful for slower local models.
        """
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.base_url = base_url
        self.timeout = timeout or 60.0  # Default 60s timeout, can be higher for local models
        
        # Initialize client with optional base_url
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
            logger.info(f"Using custom base URL: {self.base_url}")
        
        self.client = OpenAI(**client_kwargs)

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
        logger.info(f"Sending prompt to {'local model' if self.base_url else 'OpenAI'}: {prompt}")
        
        # Prepare tools if they exist
        tools = [tool.to_openai_tool() for tool in self.tools] if self.tools else None
        
        try:
            # Note: For local models, tool support may vary
            completion_kwargs = {
                "model": self.model,
                "messages": prompt,
                "temperature": self.temperature,
                "timeout": self.timeout
            }
            
            # Only add tools if they exist and warn for local models
            if tools:
                if self.base_url:
                    logger.warning("Tool support may vary for local models. Some models may not support function calling.")
                completion_kwargs["tools"] = tools
                completion_kwargs["tool_choice"] = "auto"
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                **completion_kwargs
            )
            
            message = response.choices[0].message
            result = {'tool_calls': [], 'text': None}
            
            # Process tool calls if present
            if hasattr(message, 'tool_calls') and message.tool_calls:
                logger.info("LLM suggested tool calls")
                
                tool_calls = []
                for tc in message.tool_calls:
                    try:
                        args = json.loads(tc.function.arguments)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse tool arguments: {tc.function.arguments}")
                        args = {"error": "Invalid JSON"}
                    
                    tool_calls.append({
                        "id": tc.id,
                        "name": tc.function.name,
                        "arguments": args
                    })
                
                result['tool_calls'] = tool_calls
            else:
                # Process text response
                content = message.content or ""
                logger.info(f"Received text response from {'local model' if self.base_url else 'OpenAI'}: {content[:100]}...")
                result['text'] = content
                
            return result
            
        except OpenAIError as e:
            logger.error(f"Error calling {'local model' if self.base_url else 'OpenAI'}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise
