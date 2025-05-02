"""LLM-capable agent implementation for SPADE."""

import asyncio
import logging
from typing import List, Optional, Dict, Any

from spade.agent import Agent
from spade.message import Message
from spade.template import Template

from ..behaviour import LLMBehaviour
from ..context import ContextManager
from ..mcp import MCPServerConfig, get_all_mcp_tools
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
    - MCP server support
    """

    def __init__(self,
                 jid: str,
                 password: str,
                 provider: LLMProvider,
                 system_prompt: Optional[str] = None,
                 mcp_servers: Optional[List[MCPServerConfig]] = None,
                 verify_security: bool = False):
        """
        Initialize an LLM-capable agent.

        Args:
            jid: The Jabber ID of the agent
            password: The password for the agent
            provider: The LLM provider to use
            system_prompt: Optional system instructions for the LLM
            mcp_servers: Optional list of MCP server configurations
            verify_security: Whether to verify security certificates
        """
        super().__init__(jid, password, verify_security=verify_security)

        # Create the context manager
        self.context = ContextManager(system_prompt=system_prompt)

        # Store the LLM provider
        self.provider = provider

        # Initialize tools collection
        self.tools: List[LLMTool] = []

        # Store MCP server configurations
        self.mcp_servers = mcp_servers or []

        # Create LLM behaviour
        self.llm_behaviour = LLMBehaviour(
            llm_provider=provider,
            context_manager=self.context
        )

    async def setup(self):
        """Set up the agent with LLM behaviour and MCP tools."""
        logger.info(f"LLMAgent starting: {self.jid}")

        # Register MCP tools if MCP servers are configured
        if self.mcp_servers:
            await self._setup_mcp_tools()

        # Add the LLM behaviour that will process messages
        template = Template()
        template.set_metadata("performative", "request")
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