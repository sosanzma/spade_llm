"""LLM-capable agent implementation for SPADE."""

import asyncio
import logging
from typing import List, Optional, Dict, Any, Callable

from spade.agent import Agent
from spade.message import Message
from spade.template import Template

from ..behaviour import LLMBehaviour
from ..context import ContextManager
from ..mcp import MCPServerConfig, get_all_mcp_tools
from ..providers.base_provider import LLMProvider
from ..tools import LLMTool
from ..routing import RoutingFunction

logger = logging.getLogger("spade_llm.agent")

class LLMAgent(Agent):
    """
    A SPADE agent with integrated LLM capabilities.

    This agent extends the standard SPADE agent with:
    - Built-in LLM integration
    - Context management
    - Tool execution framework
    - MCP server support
    - Conditional routing based on LLM responses
    """

    def __init__(self,
                 jid: str,
                 password: str,
                 provider: LLMProvider,
                 reply_to: Optional[str] = None,
                 routing_function: Optional[RoutingFunction] = None,
                 system_prompt: Optional[str] = None,
                 mcp_servers: Optional[List[MCPServerConfig]] = None,
                 tools: Optional[List[LLMTool]] = None,
                 termination_markers: Optional[List[str]] = None,
                 max_interactions_per_conversation: Optional[int] = None,
                 on_conversation_end: Optional[Callable[[str, str], None]] = None,
                 verify_security: bool = False):
        """
        Initialize an LLM-capable agent.

        Args:
            jid: The Jabber ID of the agent
            password: The password for the agent
            provider: The LLM provider to use
            reply_to: JID to send responses to. If None the reply is to the original sender
            routing_function: Optional function for conditional routing based on response content
            system_prompt: Optional system instructions for the LLM
            mcp_servers: Optional list of MCP server configurations
            tools: Optional list of tools the agent can use
            termination_markers: List of strings that mark conversation completion
            max_interactions_per_conversation: Maximum number of back-and-forth exchanges in a conversation
            on_conversation_end: Callback function when a conversation ends (receives conversation_id and reason)
            verify_security: Whether to verify security certificates
        """
        super().__init__(jid, password, verify_security=verify_security)

        self.context = ContextManager(system_prompt=system_prompt)


        self.provider = provider
        self.reply_to = reply_to
        self.routing_function = routing_function
        self.tools: List[LLMTool] = tools or []

        self.mcp_servers = mcp_servers or []

        self.termination_markers = termination_markers or ["<TASK_COMPLETE>", "<END>", "<DONE>"]
        self.max_interactions_per_conversation = max_interactions_per_conversation
        self.on_conversation_end = on_conversation_end

        # Create LLM behaviour with all parameters
        self.llm_behaviour = LLMBehaviour(
            llm_provider=provider,
            reply_to=self.reply_to,
            routing_function=self.routing_function,
            context_manager=self.context,
            termination_markers=self.termination_markers,
            max_interactions_per_conversation=self.max_interactions_per_conversation,
            on_conversation_end=self.on_conversation_end,
            tools=self.tools
        )

    async def setup(self):
        """Set up the agent with LLM behaviour and MCP tools."""
        logger.info(f"LLMAgent starting: {self.jid}")

        # Register MCP tools if MCP servers are configured
        if self.mcp_servers:
            await self._setup_mcp_tools()

        # Register any tools directly with the provider
        for tool in self.tools:
            self.provider.register_tool(tool)

        # Add the LLM behaviour that will process messages
        template = Template()
        #template.set_metadata("performative", "request")
        self.add_behaviour(self.llm_behaviour, template)

    async def _setup_mcp_tools(self):
        """Set up tools from configured MCP servers."""
        try:
            # Get tools from all MCP servers
            mcp_tools = await get_all_mcp_tools(self.mcp_servers)

            # Register each tool with the agent and provider
            for tool in mcp_tools:
                self.add_tool(tool)

            logger.info(f"Registered {len(mcp_tools)} MCP tools from {len(self.mcp_servers)} servers")
        except Exception as e:
            logger.error(f"Error setting up MCP tools: {e}")

    def add_tool(self, tool: LLMTool):
        """
        Add a tool to the agent.

        Args:
            tool: The tool to add
        """
        self.tools.append(tool)
        # Notify the provider about the new tool
        self.provider.register_tool(tool)
        # Also register with the behaviour
        self.llm_behaviour.register_tool(tool)
        
    def reset_conversation(self, conversation_id: str) -> bool:
        """
        Reset a conversation to allow it to continue beyond its limits.
        
        Args:
            conversation_id: The ID of the conversation to reset
            
        Returns:
            bool: True if the conversation was reset, False if not found
        """
        return self.llm_behaviour.reset_conversation(conversation_id)
    
    def get_conversation_state(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current state of a conversation.
        
        Args:
            conversation_id: The ID of the conversation
            
        Returns:
            Dict or None: The conversation state if found, None otherwise
        """
        return self.llm_behaviour.get_conversation_state(conversation_id)
