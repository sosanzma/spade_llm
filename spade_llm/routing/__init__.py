"""Routing functionality for SPADE_LLM agents."""

from .types import RoutingResponse, RoutingFunction
from .decorators import routing_rule

__all__ = ["RoutingResponse", "RoutingFunction", "routing_rule"]
