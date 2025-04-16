"""OpenAI provider for LLM integration."""

import os
import json
import logging
import asyncio
from typing import List, Dict, Any

from openai import OpenAI, OpenAIError

from .base_provider import LLMProvider
from ..context import ContextManager

logger = logging.getLogger("spade_llm.providers.openai")


class OpenAILLMProvider(LLMProvider):
    """
    LLM provider that uses the OpenAI API.
    
    This provider integrates with OpenAI's models to provide LLM capabilities
    to SPADE agents, including support for tools and function calling.
    """

    def __init__(self, 
                api_key: str,  
                model: str = "gpt-4o-mini", 
                temperature: float = 0.7):
        """
        Initialize the OpenAI LLM provider.
        
        Args:
            api_key: OpenAI API key.
            model: The OpenAI model to use.
            temperature: The temperature to use for generations.
        """
        super().__init__()
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.client = OpenAI(api_key=self.api_key)

    async def get_response(self, context: ContextManager) -> str:
        """
        Get a response from the OpenAI model based on the current context.
        
        Args:
            context: The conversation context manager.
            
        Returns:
            The model's response as a string.
            
        Raises:
            OpenAIError: If there's an issue with the OpenAI API call.
        """
        prompt = context.get_prompt()
        logger.info(f"Sending prompt to OpenAI: {prompt}")
        
        # Prepare tools if they exist
        tools = [tool.to_openai_tool() for tool in self.tools] if self.tools else None
        
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=prompt,
                temperature=self.temperature,
                tools=tools,
                tool_choice="auto" if tools else None
            )
            
            # Check if there are tool calls in the response
            message = response.choices[0].message
            if hasattr(message, 'tool_calls') and message.tool_calls:
                # Return empty content so that tool calls can be processed first
                logger.info("OpenAI suggested tool calls, returning empty response")
                return ""
            
            content = message.content or ""
            logger.info(f"Received response from OpenAI: {content[:100]}...")
            return content
        except OpenAIError as e:
            logger.error(f"Error calling OpenAI: {e}")
            raise

    async def get_tool_calls(self, context: ContextManager) -> List[Dict[str, Any]]:
        """
        Get tool calls from the OpenAI model based on the current context.
        
        Args:
            context: The conversation context manager.
            
        Returns:
            List of tool call specifications.
        """
        prompt = context.get_prompt()
        
        # Prepare tools
        tools = [tool.to_openai_tool() for tool in self.tools] if self.tools else None
        
        # If no tools, return empty list
        if not tools:
            return []
        
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=prompt,
                temperature=self.temperature,
                tools=tools,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            # Convert tool calls to the expected format
            if hasattr(message, 'tool_calls') and message.tool_calls:
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
                return tool_calls
            
            return []
        except OpenAIError as e:
            logger.error(f"Error calling OpenAI for tools: {e}")
            return []
