"""Routing functionality for SPADE_LLM agents."""

from .decorators import routing_rule
from .types import RoutingFunction, RoutingResponse

__all__ = ["RoutingResponse", "RoutingFunction", "routing_rule"]
