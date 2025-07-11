"""Tests for ContextManager class."""

import pytest
from unittest.mock import Mock

from spade_llm.context import ContextManager
from spade_llm.context._types import create_system_message, create_user_message, create_assistant_message


class TestContextManagerInitialization:
    """Test ContextManager initialization."""
    
    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        cm = ContextManager()
        
        assert cm.max_tokens == 4096
        assert cm._system_prompt is None
        assert cm._conversations == {}
        assert cm._active_conversations == set()
        assert cm._current_conversation_id is None
    
    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        cm = ContextManager(
            max_tokens=8192,
            system_prompt="Custom system prompt"
        )
        
        assert cm.max_tokens == 8192
        assert cm._system_prompt == "Custom system prompt"
        assert cm._conversations == {}
        assert cm._active_conversations == set()
    
    def test_init_values_dict(self):
        """Test that _values dict is initialized."""
        cm = ContextManager()
        assert hasattr(cm, '_values')
        assert isinstance(cm._values, dict)


class TestMessageHandling:
    """Test message handling functionality."""
    
    def test_add_message_dict_new_conversation(self, context_manager, conversation_id):
        """Test adding a message dict to a new conversation."""
        message_dict = create_user_message("Test message content")
        
        context_manager.add_message_dict(message_dict, conversation_id)
        
        assert conversation_id in context_manager._conversations
        assert conversation_id in context_manager._active_conversations
        assert context_manager._current_conversation_id == conversation_id
        assert len(context_manager._conversations[conversation_id]) == 1
        assert context_manager._conversations[conversation_id][0] == message_dict
    
    def test_add_message_dict_existing_conversation(self, context_manager, conversation_id):
        """Test adding a message dict to an existing conversation."""
        # Add first message
        msg1 = create_user_message("First message")
        context_manager.add_message_dict(msg1, conversation_id)
        
        # Add second message
        msg2 = create_user_message("Second message")
        context_manager.add_message_dict(msg2, conversation_id)
        
        messages = context_manager._conversations[conversation_id]
        assert len(messages) == 2
        assert messages[0] == msg1
        assert messages[1] == msg2
    
    def test_add_spade_message(self, context_manager, mock_message, conversation_id):
        """Test adding a SPADE message to context."""
        context_manager.add_message(mock_message, conversation_id)
        
        assert conversation_id in context_manager._conversations
        assert conversation_id in context_manager._active_conversations
        assert context_manager._current_conversation_id == conversation_id
        
        messages = context_manager._conversations[conversation_id]
        assert len(messages) == 1
        
        # Check that message was converted properly
        stored_msg = messages[0]
        assert stored_msg["role"] == "user"
        assert stored_msg["content"] == mock_message.body
        assert stored_msg["sender"] == str(mock_message.sender)
        assert stored_msg["receiver"] == str(mock_message.to)
        assert stored_msg["thread"] == mock_message.thread
    
    def test_add_assistant_message(self, context_manager, conversation_id):
        """Test adding an assistant message."""
        content = "Assistant response"
        
        # First add a user message to establish the conversation
        user_msg = create_user_message("User message")
        context_manager.add_message_dict(user_msg, conversation_id)
        
        # Add assistant message
        context_manager.add_assistant_message(content, conversation_id)
        
        messages = context_manager._conversations[conversation_id]
        assert len(messages) == 2
        
        assistant_msg = messages[1]
        assert assistant_msg["role"] == "assistant"
        assert assistant_msg["content"] == content
    
    def test_add_assistant_message_no_conversation(self, context_manager):
        """Test adding assistant message without active conversation."""
        # This should log a warning but not crash
        context_manager.add_assistant_message("Test content")
        
        # Should not create any conversation
        assert len(context_manager._conversations) == 0
    
    def test_add_tool_result(self, context_manager, conversation_id):
        """Test adding a tool result to context."""
        # First establish a conversation
        user_msg = create_user_message("User message")
        context_manager.add_message_dict(user_msg, conversation_id)
        
        # Add tool result
        result = {"status": "success", "data": "tool output"}
        tool_call_id = "call_123"
        
        context_manager.add_tool_result("test_tool", result, tool_call_id, conversation_id)
        
        messages = context_manager._conversations[conversation_id]
        assert len(messages) == 2
        
        tool_msg = messages[1]
        assert tool_msg["role"] == "tool"
        assert tool_msg["content"] == str(result)
        assert tool_msg["tool_call_id"] == tool_call_id
        assert tool_msg["tool_name"] == "test_tool"  # metadata
    
    def test_add_tool_result_no_conversation(self, context_manager):
        """Test adding tool result without active conversation logs warning."""
        # This should log a warning but not crash
        context_manager.add_tool_result("test_tool", {"result": "test"}, "call_123")
        
        # Should not create any conversation
        assert len(context_manager._conversations) == 0


class TestPromptGeneration:
    """Test prompt generation functionality."""
    
    def test_get_prompt_empty_no_system(self, context_manager_no_system):
        """Test getting prompt with no conversations and no system prompt."""
        prompt = context_manager_no_system.get_prompt()
        assert prompt == []
    
    def test_get_prompt_empty_with_system(self, context_manager):
        """Test getting prompt with no conversations but with system prompt."""
        prompt = context_manager.get_prompt()
        
        assert len(prompt) == 1
        assert prompt[0]["role"] == "system"
        assert prompt[0]["content"] == "You are a helpful test assistant."
    
    def test_get_prompt_with_messages(self, context_manager, conversation_id):
        """Test getting prompt with messages."""
        # Add messages to conversation
        user_msg = create_user_message("Hello")
        assistant_msg = create_assistant_message("Hi there!")
        
        context_manager.add_message_dict(user_msg, conversation_id)
        context_manager.add_message_dict(assistant_msg, conversation_id)
        
        prompt = context_manager.get_prompt(conversation_id)
        
        # Should have system + user + assistant
        assert len(prompt) == 3
        assert prompt[0]["role"] == "system"
        assert prompt[1]["role"] == "user"
        assert prompt[1]["content"] == "Hello"
        assert prompt[2]["role"] == "assistant"
        assert prompt[2]["content"] == "Hi there!"
    
    def test_get_prompt_filters_metadata(self, context_manager, mock_message, conversation_id):
        """Test that prompt generation filters out internal metadata."""
        context_manager.add_message(mock_message, conversation_id)
        
        prompt = context_manager.get_prompt(conversation_id)
        
        # Should have system + user message
        assert len(prompt) == 2
        user_message = prompt[1]
        
        # Should only have role and content, not sender/receiver/thread
        assert set(user_message.keys()) == {"role", "content", "name"}
        assert "sender" not in user_message
        assert "receiver" not in user_message
        assert "thread" not in user_message
    
    def test_get_prompt_includes_tool_calls(self, context_manager, conversation_id):
        """Test that tool calls are included in prompt."""
        # Create assistant message with tool calls
        assistant_msg = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "test_tool",
                        "arguments": '{"param": "value"}'
                    }
                }
            ]
        }
        
        context_manager.add_message_dict(assistant_msg, conversation_id)
        
        prompt = context_manager.get_prompt(conversation_id)
        
        # Should include tool_calls in the prompt
        assert len(prompt) == 2  # system + assistant
        assistant_prompt = prompt[1]
        assert "tool_calls" in assistant_prompt
        assert assistant_prompt["tool_calls"] == assistant_msg["tool_calls"]
    
    def test_get_prompt_includes_tool_call_id(self, context_manager, conversation_id):
        """Test that tool messages include tool_call_id."""
        # Add a tool result message
        tool_msg = {
            "role": "tool",
            "content": "Tool result",
            "tool_call_id": "call_123",
            "tool_name": "test_tool"  # This is metadata and should not appear in prompt
        }
        
        context_manager.add_message_dict(tool_msg, conversation_id)
        
        prompt = context_manager.get_prompt(conversation_id)
        
        # Should have system + tool message
        assert len(prompt) == 2
        tool_prompt = prompt[1]
        assert tool_prompt["role"] == "tool"
        assert tool_prompt["content"] == "Tool result"
        assert tool_prompt["tool_call_id"] == "call_123"
        assert "tool_name" not in tool_prompt  # Metadata should be filtered out


class TestConversationManagement:
    """Test conversation management functionality."""
    
    def test_conversation_isolation(self, context_manager, conversation_id, different_conversation_id):
        """Test that different conversations are isolated."""
        # Add messages to different conversations
        msg1 = create_user_message("Message in conversation 1")
        msg2 = create_user_message("Message in conversation 2")
        
        context_manager.add_message_dict(msg1, conversation_id)
        context_manager.add_message_dict(msg2, different_conversation_id)
        
        # Check isolation
        conv1_messages = context_manager._conversations[conversation_id]
        conv2_messages = context_manager._conversations[different_conversation_id]
        
        assert len(conv1_messages) == 1
        assert len(conv2_messages) == 1
        assert conv1_messages[0] != conv2_messages[0]
        
        # Check prompts are different
        prompt1 = context_manager.get_prompt(conversation_id)
        prompt2 = context_manager.get_prompt(different_conversation_id)
        
        assert prompt1[1]["content"] == "Message in conversation 1"
        assert prompt2[1]["content"] == "Message in conversation 2"
    
    def test_get_active_conversations(self, context_manager, conversation_id, different_conversation_id):
        """Test getting list of active conversations."""
        # Initially no active conversations
        assert context_manager.get_active_conversations() == []
        
        # Add messages to create active conversations
        msg1 = create_user_message("Message 1")
        msg2 = create_user_message("Message 2")
        
        context_manager.add_message_dict(msg1, conversation_id)
        context_manager.add_message_dict(msg2, different_conversation_id)
        
        active = context_manager.get_active_conversations()
        assert set(active) == {conversation_id, different_conversation_id}
    
    def test_set_current_conversation(self, context_manager, conversation_id):
        """Test setting current conversation."""
        # Create a conversation first
        msg = create_user_message("Test message")
        context_manager.add_message_dict(msg, conversation_id)
        
        # Set it as current
        result = context_manager.set_current_conversation(conversation_id)
        assert result is True
        assert context_manager._current_conversation_id == conversation_id
    
    def test_set_current_conversation_nonexistent(self, context_manager):
        """Test setting current conversation to non-existent ID."""
        result = context_manager.set_current_conversation("nonexistent")
        assert result is False
        assert context_manager._current_conversation_id is None
    
    def test_get_conversation_history(self, context_manager, conversation_id):
        """Test getting conversation history."""
        # Add some messages
        user_msg = create_user_message("User message")
        assistant_msg = create_assistant_message("Assistant message")
        
        context_manager.add_message_dict(user_msg, conversation_id)
        context_manager.add_message_dict(assistant_msg, conversation_id)
        
        history = context_manager.get_conversation_history(conversation_id)
        
        assert len(history) == 2
        assert history[0] == user_msg
        assert history[1] == assistant_msg
    
    def test_get_conversation_history_nonexistent(self, context_manager):
        """Test getting history for non-existent conversation."""
        history = context_manager.get_conversation_history("nonexistent")
        assert history == []


class TestContextClearing:
    """Test context clearing functionality."""
    
    def test_clear_specific_conversation(self, context_manager, conversation_id, different_conversation_id):
        """Test clearing a specific conversation."""
        # Add messages to two conversations
        msg1 = create_user_message("Message 1")
        msg2 = create_user_message("Message 2")
        
        context_manager.add_message_dict(msg1, conversation_id)
        context_manager.add_message_dict(msg2, different_conversation_id)
        
        # Clear first conversation
        context_manager.clear(conversation_id)
        
        # First conversation should be cleared, second should remain
        assert context_manager._conversations[conversation_id] == []
        assert len(context_manager._conversations[different_conversation_id]) == 1
        assert conversation_id not in context_manager._active_conversations
        assert different_conversation_id in context_manager._active_conversations
    
    def test_clear_current_conversation(self, context_manager, conversation_id):
        """Test clearing current conversation."""
        # Add message and set as current
        msg = create_user_message("Test message")
        context_manager.add_message_dict(msg, conversation_id)
        
        # Clear without specifying ID (should clear current)
        context_manager.clear()
        
        assert context_manager._conversations[conversation_id] == []
        assert conversation_id not in context_manager._active_conversations
        assert context_manager._current_conversation_id is None
    
    def test_clear_all_conversations(self, context_manager, conversation_id, different_conversation_id):
        """Test clearing all conversations."""
        # Add messages to multiple conversations
        msg1 = create_user_message("Message 1")
        msg2 = create_user_message("Message 2")
        
        context_manager.add_message_dict(msg1, conversation_id)
        context_manager.add_message_dict(msg2, different_conversation_id)
        
        # Clear all
        context_manager.clear('all')
        
        assert context_manager._conversations == {}
        assert context_manager._active_conversations == set()
        assert context_manager._current_conversation_id is None
    
    def test_clear_nonexistent_conversation(self, context_manager):
        """Test clearing a non-existent conversation doesn't error."""
        # This should not raise an error
        context_manager.clear("nonexistent")
        
        # State should remain unchanged
        assert context_manager._conversations == {}
        assert context_manager._active_conversations == set()


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_get_prompt_with_current_conversation_none(self, context_manager):
        """Test getting prompt when current conversation is None."""
        # Should return just system prompt
        prompt = context_manager.get_prompt()
        assert len(prompt) <= 1  # 0 if no system prompt, 1 if system prompt exists
    
    def test_multiple_assistant_messages(self, context_manager, conversation_id):
        """Test adding multiple assistant messages in sequence."""
        context_manager.add_assistant_message("Response 1", conversation_id)
        context_manager.add_assistant_message("Response 2", conversation_id)
        
        messages = context_manager._conversations[conversation_id]
        assert len(messages) == 2
        assert all(msg["role"] == "assistant" for msg in messages)
    
    def test_empty_message_content(self, context_manager, conversation_id):
        """Test handling empty message content."""
        empty_msg = create_user_message("")
        context_manager.add_message_dict(empty_msg, conversation_id)
        
        prompt = context_manager.get_prompt(conversation_id)
        user_message = prompt[1]
        assert user_message["content"] == ""
    
    def test_none_message_content(self, context_manager, conversation_id):
        """Test handling None message content."""
        none_msg = {"role": "assistant", "content": None}
        context_manager.add_message_dict(none_msg, conversation_id)
        
        prompt = context_manager.get_prompt(conversation_id)
        assistant_message = prompt[1]
        assert assistant_message["content"] is None
