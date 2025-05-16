"""SPADE_LLM context management module."""

from .context_manager import ContextManager
from ._types import (
    # Message type definitions
    ContextMessage, SystemMessage, UserMessage, AssistantMessage, ToolResultMessage,
    ToolCall, ToolCallFunction,
    
    # Helper functions for message creation
    create_system_message, create_user_message, spade_message_to_user_message,
    create_assistant_message, create_assistant_tool_call_message, create_tool_result_message
)

__all__ = [
    "ContextManager",
    # Message types
    "ContextMessage", "SystemMessage", "UserMessage", "AssistantMessage", 
    "ToolResultMessage", "ToolCall", "ToolCallFunction",
    # Helper functions
    "create_system_message", "create_user_message", "spade_message_to_user_message",
    "create_assistant_message", "create_assistant_tool_call_message", "create_tool_result_message"
]
