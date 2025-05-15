"""SPADE_LLM - Extension de SPADE para integrar Large Language Models en agentes."""

from .version import __version__

from .behaviour import LLMBehaviour
from .context import ContextManager
from .tools import LLMTool
from .agent import LLMAgent, ChatAgent
from .providers import LLMProvider, OpenAILLMProvider
from .utils import load_env_vars
from .routing import RoutingFunction, RoutingResponse

__all__ = [
    "LLMBehaviour", 
    "ContextManager", 
    "LLMTool", 
    "LLMAgent",
    "ChatAgent", 
    "LLMProvider",
    "OpenAILLMProvider",
    "load_env_vars",
    "RoutingFunction",
    "RoutingResponse",
    "__version__"
]
