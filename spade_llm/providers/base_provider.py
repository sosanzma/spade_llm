"""Base provider for LLM integration."""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from ..context import ContextManager
from ..tools import LLMTool

logger = logging.getLogger("spade_llm.providers")


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    This class defines the interface that all LLM providers must implement,
    allowing for consistent interaction regardless of the underlying LLM service.
    """
    
    def __init__(self):
        """Initialize the LLM provider."""
        self.tools = []
    
    @abstractmethod
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
        pass
    
    def register_tool(self, tool: LLMTool) -> None:
        """
        Register a tool with the provider.
        
        Args:
            tool: The tool to register
        """
        self.tools.append(tool)
        
    # Legacy methods that delegate to the new unified method
    async def get_response(self, context: ContextManager) -> Optional[str]:
        """
        Get a response from the LLM based on the current context.
        
        Args:
            context: The conversation context manager
            
        Returns:
            The LLM's response as a string, or None if tool calls should be processed first
        """
        response = await self.get_llm_response(context)
        return response.get('text')
        
    async def get_tool_calls(self, context: ContextManager) -> List[Dict[str, Any]]:
        """
        Get tool calls from the LLM based on the current context.
        
        Args:
            context: The conversation context manager
            
        Returns:
            List of tool call specifications
        """
        response = await self.get_llm_response(context)
        return response.get('tool_calls', [])
