import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
import requests

from .base_provider import LLMProvider
from ..context import ContextManager

logger = logging.getLogger("spade_llm.providers.ollama")


class OllamaLLMProvider(LLMProvider):
    """
    LLM provider that uses Ollama's local API.

    This provider integrates with Ollama, a tool for running large language models locally.
    Ollama provides a REST API that's different from OpenAI's, so this provider handles
    the necessary translations between formats.

    Note: Ollama does not natively support function calling/tools, so tool calls
    will be handled through prompt engineering when tools are registered.
    """

    def __init__(self,
                 base_url: str = "http://localhost:11434",
                 model: str = "llama2",
                 temperature: float = 0.7,
                 timeout: float = 300.0,
                 num_predict: int = -1,
                 top_k: int = 40,
                 top_p: float = 0.9):
        """
        Initialize the Ollama LLM provider.

        Args:
            base_url: Base URL for the Ollama API (default: http://localhost:11434)
            model: The Ollama model to use (e.g., "llama2", "codellama", "mistral")
            temperature: Temperature for generation (0.0 to 1.0)
            timeout: Timeout in seconds for API calls
            num_predict: Maximum number of tokens to generate (-1 for no limit)
            top_k: Limits token selection to top K tokens
            top_p: Nucleus sampling parameter
        """
        super().__init__()
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.num_predict = num_predict
        self.top_k = top_k
        self.top_p = top_p

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass

    def _check_model_available_sync(self) -> bool:
        """
        Synchronous version: Check if the specified model is available in Ollama.

        Returns:
            bool: True if model is available, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                available_models = [model["name"] for model in data.get("models", [])]
                return self.model in available_models
            return False
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return False

    async def check_model_available(self) -> bool:
        """
        Check if the specified model is available in Ollama.

        Returns:
            bool: True if model is available, False otherwise
        """
        return await asyncio.to_thread(self._check_model_available_sync)

    def _pull_model_sync(self) -> bool:
        """
        Synchronous version: Pull the model if it's not available locally.

        Returns:
            bool: True if model was successfully pulled, False otherwise
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": self.model},
                timeout=self.timeout
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error pulling model: {e}")
            return False

    async def pull_model(self) -> bool:
        """
        Pull the model if it's not available locally.

        Returns:
            bool: True if model was successfully pulled, False otherwise
        """
        return await asyncio.to_thread(self._pull_model_sync)

    def _convert_messages_to_ollama_format(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert messages from SPADE_LLM format to Ollama format.

        Args:
            messages: Messages in SPADE_LLM format

        Returns:
            Messages in Ollama format
        """
        ollama_messages = []

        # Track if we've processed a system message
        system_message = None

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                # Store system message to prepend to first user message
                system_message = content
            elif role == "function":
                # Ollama doesn't support function messages, convert to assistant
                function_name = msg.get("name", "function")
                ollama_messages.append({
                    "role": "assistant",
                    "content": f"Function {function_name} result: {content}"
                })
            else:
                # For the first user message, prepend system message if we have one
                if role == "user" and system_message and not ollama_messages:
                    content = f"{system_message}\n\n{content}"
                    system_message = None  # Only prepend once

                ollama_messages.append({
                    "role": role,
                    "content": content
                })

        return ollama_messages

    def _create_tool_prompt(self, tools: List[Any]) -> str:
        """
        Create a prompt that describes available tools for models that don't support native function calling.

        Args:
            tools: List of available tools

        Returns:
            A string describing the tools
        """
        if not tools:
            return ""

        tool_descriptions = ["You have access to the following tools:"]

        for tool in tools:
            tool_info = tool.to_openai_tool()
            function_info = tool_info.get("function", {})

            tool_desc = f"\n- {function_info.get('name', 'Unknown')}: {function_info.get('description', 'No description')}"

            parameters = function_info.get('parameters', {}).get('properties', {})
            if parameters:
                tool_desc += "\n  Parameters:"
                for param_name, param_info in parameters.items():
                    required = param_name in function_info.get('parameters', {}).get('required', [])
                    tool_desc += f"\n    - {param_name}: {param_info.get('type', 'any')} {'(required)' if required else '(optional)'}"
                    if 'description' in param_info:
                        tool_desc += f" - {param_info['description']}"

            tool_descriptions.append(tool_desc)

        tool_descriptions.append("\nTo use a tool, respond with a JSON object in this format:")
        tool_descriptions.append('{"tool_call": {"name": "tool_name", "arguments": {...}}}')
        tool_descriptions.append("After using a tool, wait for the result before continuing.")

        return "\n".join(tool_descriptions)

    def _extract_tool_call(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Extract tool call from model response.

        Args:
            response: The model's response

        Returns:
            Tool call dict if found, None otherwise
        """
        try:
            # Look for JSON in the response
            import re
            json_pattern = r'\{[^{}]*"tool_call"[^{}]*\}'
            matches = re.findall(json_pattern, response, re.DOTALL)

            if matches:
                # Try to parse the first match
                tool_call_json = matches[0]
                tool_call_data = json.loads(tool_call_json)

                if "tool_call" in tool_call_data:
                    tool_call = tool_call_data["tool_call"]
                    return {
                        "id": f"call_{hash(json.dumps(tool_call))}",
                        "name": tool_call.get("name"),
                        "arguments": tool_call.get("arguments", {})
                    }
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.debug(f"Failed to extract tool call: {e}")

        return None

    def _call_ollama_api_sync(self, endpoint: str, method: str = "POST",
                              json_data: Optional[Dict] = None,
                              timeout: Optional[float] = None) -> requests.Response:
        """
        Synchronous helper to call Ollama API.

        Args:
            endpoint: The API endpoint (e.g., "/api/chat")
            method: HTTP method (GET or POST)
            json_data: JSON data for POST requests
            timeout: Request timeout

        Returns:
            requests.Response
        """
        url = f"{self.base_url}{endpoint}"
        timeout = timeout or self.timeout

        if method == "GET":
            response = requests.get(url, timeout=timeout)
        else:
            response = requests.post(url, json=json_data, timeout=timeout)

        return response

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
        logger.info("OllamaProvider.get_llm_response called")
        messages = context.get_prompt()
        logger.info(f"Messages from context: {messages}")

        # Convert messages to Ollama format
        ollama_messages = self._convert_messages_to_ollama_format(messages)
        logger.info(f"Converted messages: {ollama_messages}")

        # Add tool descriptions to the last user message if tools are available
        if self.tools and ollama_messages:
            tool_prompt = self._create_tool_prompt(self.tools)
            if tool_prompt:
                # Find the last user message and append tool descriptions
                for i in range(len(ollama_messages) - 1, -1, -1):
                    if ollama_messages[i]["role"] == "user":
                        ollama_messages[i]["content"] += f"\n\n{tool_prompt}"
                        break

        request_data = {
            "model": self.model,
            "messages": ollama_messages,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.num_predict,
                "top_k": self.top_k,
                "top_p": self.top_p
            },
            "stream": False
        }

        logger.info(f"Request data: {json.dumps(request_data, indent=2)}")
        logger.info(f"URL: {self.base_url}/api/chat")

        try:
            response = await asyncio.to_thread(
                self._call_ollama_api_sync,
                "/api/chat",
                "POST",
                request_data,
                30.0  # 30 seconds timeout
            )

            logger.info(f"Response status: {response.status_code}")

            if response.status_code != 200:
                error_text = response.text
                logger.error(f"Ollama API error: {response.status_code} - {error_text}")

                # Check if model needs to be pulled
                if "model not found" in error_text.lower():
                    logger.info(f"Model {self.model} not found, attempting to pull...")
                    if await self.pull_model():
                        # Retry the request
                        response = await asyncio.to_thread(
                            self._call_ollama_api_sync,
                            "/api/chat",
                            "POST",
                            request_data,
                            30.0
                        )
                        if response.status_code != 200:
                            raise Exception(f"Ollama API error after pull: {response.status_code}")
                    else:
                        raise Exception(f"Failed to pull model {self.model}")
                else:
                    raise Exception(f"Ollama API error: {response.status_code} - {error_text}")

            response_data = response.json()
            message_content = response_data.get("message", {}).get("content", "")

            # Check if the response contains a tool call
            if self.tools:
                tool_call = self._extract_tool_call(message_content)
                if tool_call:
                    logger.info("Ollama suggested a tool call (via prompt engineering)")
                    return {
                        'tool_calls': [tool_call],
                        'text': None
                    }

            # Regular text response
            logger.info(f"Received response from Ollama: {message_content[:100]}...")
            return {
                'text': message_content,
                'tool_calls': []
            }

        except Exception as e:
            logger.error(f"Error calling Ollama API: {type(e).__name__}: {e}")
            raise

    def _list_models_sync(self) -> List[str]:
        """
        Synchronous version: List all available models in Ollama.

        Returns:
            List of model names
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model["name"] for model in data.get("models", [])]
            return []
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []

    async def list_models(self) -> List[str]:
        """
        List all available models in Ollama.

        Returns:
            List of model names
        """
        return await asyncio.to_thread(self._list_models_sync)