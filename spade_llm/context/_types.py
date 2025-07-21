"""Type definitions for context management in SPADE_LLM.

This module centralizes all message type definitions and format conversions
for consistent message handling throughout the library.
"""

import json
import logging
from typing import Any, Dict, List, Optional, TypedDict, Union

from spade.message import Message

logger = logging.getLogger("spade_llm.context.types")


class BaseMessage(TypedDict):
    """Base structure for all message types."""

    role: str
    content: Optional[str]


class SystemMessage(BaseMessage):
    """System instructions for the LLM."""

    role: str
    content: str


class UserMessage(BaseMessage):
    """Message from a user."""

    role: str
    content: str
    name: Optional[str]


class ToolCallFunction(TypedDict):
    """Function specification in a tool call."""

    name: str
    arguments: str


class ToolCall(TypedDict):
    """Structure of a tool call."""

    id: str
    type: str
    function: ToolCallFunction


class AssistantMessage(BaseMessage):
    """Message from the assistant (LLM)."""

    role: str
    content: Optional[str]
    tool_calls: Optional[List[ToolCall]]


class ToolResultMessage(BaseMessage):
    """Result from a tool execution."""

    role: str
    content: str
    tool_call_id: str


# Type for any message in the context
ContextMessage = Union[SystemMessage, UserMessage, AssistantMessage, ToolResultMessage]


def create_system_message(content: str) -> SystemMessage:
    """Create a system message with the given content."""
    return {"role": "system", "content": content}


def create_user_message(content: str, name: Optional[str] = None) -> UserMessage:
    """Create a user message with the given content and optional name."""
    message = {"role": "user", "content": content}
    if name:
        message["name"] = name
    return message


def _sanitize_jid_for_name(jid: str) -> str:
    """
    Sanitize an XMPP JID for use as an OpenAI message name field.

    OpenAI name fields cannot contain: whitespace, <, |, \, /, >
    This function replaces these characters with underscores and removes the resource
    part of the JID if present.

    Args:
        jid: The XMPP JID to sanitize

    Returns:
        Sanitized name suitable for OpenAI message name field
    """
    # Remove resource part (everything after /) if present
    if "/" in jid:
        jid = jid.split("/")[0]

    # Replace forbidden characters with underscores
    forbidden_chars = [" ", "\t", "\n", "\r", "<", "|", "\\", "/", ">"]
    sanitized = jid
    for char in forbidden_chars:
        sanitized = sanitized.replace(char, "_")

    return sanitized


def spade_message_to_user_message(message: Message) -> UserMessage:
    """Convert a SPADE message to a UserMessage format."""
    user_message = {"role": "user", "content": message.body}

    # Add name if we have sender information
    if message.sender:
        user_message["name"] = _sanitize_jid_for_name(str(message.sender))

    return user_message


def create_assistant_message(content: str) -> AssistantMessage:
    """Format a text response as an AssistantMessage."""
    return {"role": "assistant", "content": content}


def create_assistant_tool_call_message(
    tool_calls: List[Dict[str, Any]],
) -> AssistantMessage:
    """Format tool calls as an AssistantMessage with tool_calls field."""
    formatted_calls = []

    for tc in tool_calls:
        args = tc.get("arguments", {})
        if isinstance(args, dict):
            args_str = json.dumps(args)
        else:
            args_str = args

        formatted_call = {
            "id": tc.get("id"),
            "type": "function",
            "function": {"name": tc.get("name"), "arguments": args_str},
        }
        formatted_calls.append(formatted_call)

    return {"role": "assistant", "content": None, "tool_calls": formatted_calls}


def create_tool_result_message(result: Any, tool_call_id: str) -> ToolResultMessage:
    """Format a tool result as a ToolResultMessage."""
    return {"role": "tool", "content": str(result), "tool_call_id": tool_call_id}
