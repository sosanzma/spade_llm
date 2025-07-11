"""Configuration classes for MCP server connections."""

import abc
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union


@dataclass
class MCPServerConfig(abc.ABC):
    """Base configuration for MCP servers.

    This abstract class defines the common configuration parameters
    for all MCP server types.
    """

    name: str
    """A descriptive name for the server."""

    cache_tools: bool = False
    """Whether to cache the tools list from the server.

    If True, tools will only be fetched once from the server.
    If False, tools will be fetched each time they are needed.
    """


@dataclass
class StdioServerConfig(MCPServerConfig):
    """Configuration for MCP servers using stdio transport.

    This configuration is used for MCP servers that communicate via standard I/O,
    typically command-line tools or local services.
    """

    command: str = field(default=None)
    """The command to execute to start the server."""

    args: List[str] = field(default_factory=list)
    """Command line arguments to pass to the command."""

    env: Optional[Dict[str, str]] = None
    """Environment variables to set for the command."""

    cwd: Optional[Union[str, Path]] = None
    """Working directory for the command."""

    encoding: str = "utf-8"
    """Text encoding to use for communication."""

    encoding_error_handler: str = "strict"
    """Error handler for encoding issues."""

    read_timeout_seconds: float = 5.0
    """Timeout for read operations in seconds."""
    
    def __post_init__(self):
        """Validate required fields after initialization."""
        if self.command is None:
            raise ValueError("command is required for StdioServerConfig")


@dataclass
class SseServerConfig(MCPServerConfig):
    """Configuration for MCP servers using SSE transport.

    This configuration is used for MCP servers that communicate via HTTP with
    Server-Sent Events (SSE), typically remote services or web APIs.
    """

    url: str = field(default=None)
    """The URL of the SSE endpoint."""

    headers: Optional[Dict[str, str]] = None
    """HTTP headers to include in requests."""

    timeout: float = 5.0
    """Connection timeout in seconds."""

    sse_read_timeout: float = 300.0  # 5 minutes
    """Read timeout for SSE connection in seconds."""
    
    def __post_init__(self):
        """Validate required fields after initialization."""
        if self.url is None:
            raise ValueError("url is required for SseServerConfig")


@dataclass
class StreamableHttpServerConfig(MCPServerConfig):
    """Configuration for MCP servers using Streamable HTTP transport.

    This configuration is used for MCP servers that communicate via
    the Streamable HTTP protocol, which provides improved session
    management and stability over SSE.
    """

    url: str = field(default=None)
    """The URL of the Streamable HTTP endpoint."""

    headers: Optional[Dict[str, str]] = None
    """HTTP headers to include in requests."""

    timeout: float = 30.0
    """Connection timeout in seconds."""

    sse_read_timeout: float = 300.0  # 5 minutes
    """Read timeout for SSE stream in seconds."""

    terminate_on_close: bool = True
    """Whether to terminate the connection when closed."""
    
    def __post_init__(self):
        """Validate required fields after initialization."""
        if self.url is None:
            raise ValueError("url is required for StreamableHttpServerConfig")
