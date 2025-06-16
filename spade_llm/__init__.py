"""SPADE_LLM - Extension de SPADE para integrar Large Language Models en agentes."""

from .version import __version__

from .behaviour import LLMBehaviour, HumanInteractionBehaviour
from .context import ContextManager
from .tools import LLMTool, HumanInTheLoopTool
from .agent import LLMAgent, ChatAgent
from .providers import LLMProvider
from .utils import load_env_vars
from .routing import RoutingFunction, RoutingResponse
from .guardrails import (
    Guardrail, GuardrailAction, GuardrailResult,
    InputGuardrail, OutputGuardrail, CompositeGuardrail,
    KeywordGuardrail, LLMGuardrail, RegexGuardrail, CustomFunctionGuardrail
)

__all__ = [
    "LLMBehaviour", 
    "HumanInteractionBehaviour",
    "ContextManager", 
    "LLMTool", 
    "HumanInTheLoopTool",
    "LLMAgent",
    "ChatAgent", 
    "LLMProvider",
    "load_env_vars",
    "RoutingFunction",
    "RoutingResponse",
    # Guardrails
    "Guardrail",
    "GuardrailAction", 
    "GuardrailResult",
    "InputGuardrail",
    "OutputGuardrail",
    "CompositeGuardrail",
    "KeywordGuardrail",
    "LLMGuardrail",
    "RegexGuardrail",
    "CustomFunctionGuardrail",
    "__version__"
]
