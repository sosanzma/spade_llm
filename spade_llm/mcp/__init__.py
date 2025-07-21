"""MCP (Model Context Protocol) integration for SPADE_LLM."""

from .adapters import (
    MCPToolAdapter,
    SseMCPToolAdapter,
    StdioMCPToolAdapter,
    StreamableHttpMCPToolAdapter,
)
from .config import (
    MCPServerConfig,
    SseServerConfig,
    StdioServerConfig,
    StreamableHttpServerConfig,
)
from .factory import get_all_mcp_tools, get_mcp_server_tools, get_mcp_tool
from .session import MCPSession, create_mcp_session

__all__ = [
    # Adapters
    "MCPToolAdapter",
    "SseMCPToolAdapter",
    "StdioMCPToolAdapter",
    "StreamableHttpMCPToolAdapter",
    # Configs
    "MCPServerConfig",
    "SseServerConfig",
    "StdioServerConfig",
    "StreamableHttpServerConfig",
    # Factory functions
    "get_all_mcp_tools",
    "get_mcp_server_tools",
    "get_mcp_tool",
    # Session management
    "MCPSession",
    "create_mcp_session",
]
