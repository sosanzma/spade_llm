"""SPADE_LLM - Extension de SPADE para integrar Large Language Models en agentes."""

from .version import __version__

from .behaviour import LLMBehaviour
from .context import ContextManager
from .tools import LLMTool
from .agent import LLMAgent
from .providers import LLMProvider, DummyLLMProvider

__all__ = [
    "LLMBehaviour", 
    "ContextManager", 
    "LLMTool", 
    "LLMAgent", 
    "LLMProvider",
    "DummyLLMProvider",
    "__version__"
]
