"""LLM-capable agent implementation for SPADE."""

import logging
from typing import Optional, List, Dict, Any

from spade.agent import Agent
from spade.message import Message
from spade.template import Template

from ..behaviour import LLMBehaviour
from ..context import ContextManager
from ..providers.base_provider import LLMProvider
from ..tools import LLMTool

logger = logging.getLogger("spade_llm.agent")


class LLMAgent(Agent):
    """
    A SPADE agent with integrated LLM capabilities.
    
    This agent extends the standard SPADE agent with:
    - Built-in LLM integration
    - Context management
    - Tool execution framework
    """
    
    def __init__(self, 
                jid: str, 
                password: str, 
                provider: LLMProvider,
                system_prompt: Optional[str] = None,
                verify_security: bool = False):
        """
        Initialize an LLM-capable agent.
        
        Args:
            jid: The Jabber ID of the agent
            password: The password for the agent
            provider: The LLM provider to use
            system_prompt: Optional system instructions for the LLM
            verify_security: Whether to verify security certificates
        """
        super().__init__(jid, password, verify_security=verify_security)
        
        # Create the context manager
        self.context = ContextManager(system_prompt=system_prompt)
        
        # Store the LLM provider
        self.provider = provider
        
        # Initialize tools collection
        self.tools = []
        
        # Create LLM behaviour
        self.llm_behaviour = LLMBehaviour(
            llm_provider=provider,
            context_manager=self.context
        )
    
    async def setup(self):
        """Set up the agent with LLM behaviour."""
        logger.info(f"LLMAgent starting: {self.jid}")
        
        # Add the LLM behaviour that will process messages
        template = Template()
        template.set_metadata("performative", "request")
        self.add_behaviour(self.llm_behaviour, template)
        
    def add_tool(self, tool: LLMTool):
        """
        Add a tool to the agent.
        
        Args:
            tool: The tool to add
        """
        self.tools.append(tool)
        # Notify the provider about the new tool
        self.provider.register_tool(tool)
