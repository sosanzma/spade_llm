"""Type definitions for routing system."""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union

from spade.message import Message


@dataclass
class RoutingResponse:
    """
    Encapsulates a routing decision with optional transformations and metadata.

    This class provides a more expressive way to define routing beyond simple
    string destinations, allowing for message transformation and metadata attachment.
    """

    recipients: Union[str, List[str]]
    """One or more JID destinations for the message."""

    transform: Optional[Callable[[str], str]] = None
    """Optional function to transform the message before sending."""

    metadata: Optional[Dict[str, Any]] = None
    """Optional metadata to attach to the outgoing message."""


RoutingFunction = Callable[[Message, str, Dict[str, Any]], Union[str, RoutingResponse]]
"""
Type alias for routing functions.

A routing function takes:
- msg: The original SPADE message
- response: The LLM's response text
- context: Additional context (conversation_id, etc.)

And returns either:
- A string JID for simple routing
- A RoutingResponse for advanced routing with transformations
"""
