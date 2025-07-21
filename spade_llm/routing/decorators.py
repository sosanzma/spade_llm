"""Decorators and utilities for defining routing rules."""

from functools import wraps
from typing import Callable, Optional

from spade.message import Message

from .types import RoutingResponse


def routing_rule(priority: int = 0, name: Optional[str] = None):
    """
    Decorator for marking functions as routing rules with optional priority.

    Args:
        priority: Priority of the rule (higher values execute first)
        name: Optional name for the rule (defaults to function name)

    Returns:
        Decorated function with routing metadata

    Example:
        @routing_rule(priority=10)
        def high_priority_route(msg, response, context):
            if "urgent" in response.lower():
                return "priority_handler@server.com"
            return None
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper._is_routing_rule = True
        wrapper._priority = priority
        wrapper._rule_name = name or func.__name__

        return wrapper

    return decorator
