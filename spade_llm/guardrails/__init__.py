"""Guardrails system for SPADE_LLM."""

from .base import Guardrail, GuardrailAction, GuardrailResult
from .implementations import (
    CustomFunctionGuardrail,
    KeywordGuardrail,
    LLMGuardrail,
    RegexGuardrail,
)
from .processor import apply_input_guardrails, apply_output_guardrails
from .types import CompositeGuardrail, InputGuardrail, OutputGuardrail

__all__ = [
    # Base classes
    "Guardrail",
    "GuardrailAction",
    "GuardrailResult",
    # Types
    "InputGuardrail",
    "OutputGuardrail",
    "CompositeGuardrail",
    # Implementations
    "KeywordGuardrail",
    "LLMGuardrail",
    "RegexGuardrail",
    "CustomFunctionGuardrail",
    # Processing functions
    "apply_input_guardrails",
    "apply_output_guardrails",
]
