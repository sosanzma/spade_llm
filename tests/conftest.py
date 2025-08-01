"""Global test configuration and fixtures for SPADE_LLM tests."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any, List, Optional

from spade.message import Message
from spade_llm.context import ContextManager
from spade_llm.tools import LLMTool
from spade_llm.providers.base_provider import LLMProvider


# Configure pytest for async testing
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture
def mock_message():
    """Create a mock SPADE message for testing."""
    msg = Mock(spec=Message)
    msg.body = "Test message content"
    msg.sender = "test_sender@localhost"
    msg.to = "test_receiver@localhost"
    msg.thread = "test-thread-123"
    msg.id = "msg_12345"
    msg.metadata = {}
    
    # Mock the make_reply method
    reply_msg = Mock(spec=Message)
    reply_msg.to = str(msg.sender)
    reply_msg.sender = str(msg.to)
    reply_msg.body = ""
    reply_msg.thread = msg.thread
    reply_msg.metadata = {}
    reply_msg.set_metadata = Mock()
    msg.make_reply = Mock(return_value=reply_msg)
    
    return msg


@pytest.fixture
def mock_message_with_metadata():
    """Create a mock SPADE message with metadata for testing."""
    msg = Mock(spec=Message)
    msg.body = "Test message with metadata"
    msg.sender = "test_sender@localhost"
    msg.to = "test_receiver@localhost"
    msg.thread = "test-thread-456"
    msg.id = "msg_67890"
    msg.metadata = {"key1": "value1", "key2": "value2"}
    
    # Mock the make_reply method
    reply_msg = Mock(spec=Message)
    reply_msg.to = str(msg.sender)
    reply_msg.sender = str(msg.to)
    reply_msg.body = ""
    reply_msg.thread = msg.thread
    reply_msg.metadata = {}
    reply_msg.set_metadata = Mock()
    msg.make_reply = Mock(return_value=reply_msg)
    
    return msg


@pytest.fixture
def context_manager():
    """Create a fresh ContextManager instance for testing."""
    return ContextManager(
        max_tokens=4096,
        system_prompt="You are a helpful test assistant."
    )


@pytest.fixture
def context_manager_no_system():
    """Create a ContextManager without system prompt for testing."""
    return ContextManager(max_tokens=4096)


@pytest.fixture
def mock_simple_tool():
    """Create a simple mock tool for testing."""
    def simple_func(text: str = "default") -> str:
        return f"Tool executed with: {text}"
    
    return LLMTool(
        name="simple_tool",
        description="A simple test tool",
        parameters={
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to process"
                }
            },
            "required": ["text"]
        },
        func=simple_func
    )


@pytest.fixture
def mock_async_tool():
    """Create a mock async tool for testing."""
    async def async_func(number: int = 42) -> Dict[str, Any]:
        await asyncio.sleep(0.01)  # Simulate async work
        return {"result": number * 2, "status": "success"}
    
    return LLMTool(
        name="async_tool",
        description="An async test tool",
        parameters={
            "type": "object",
            "properties": {
                "number": {
                    "type": "integer",
                    "description": "Number to process"
                }
            },
            "required": ["number"]
        },
        func=async_func
    )


@pytest.fixture
def mock_error_tool():
    """Create a mock tool that raises an error for testing."""
    def error_func() -> str:
        raise ValueError("Intentional test error")
    
    return LLMTool(
        name="error_tool",
        description="A tool that raises an error",
        parameters={
            "type": "object",
            "properties": {}
        },
        func=error_func
    )


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self, 
                 responses: Optional[List[str]] = None,
                 tool_calls: Optional[List[Dict[str, Any]]] = None,
                 should_error: bool = False):
        super().__init__()
        self.responses = responses or ["Mock LLM response"]
        self.tool_calls = tool_calls or []
        self.should_error = should_error
        self.call_count = 0
        self.call_history = []
        
    async def get_llm_response(self, context: ContextManager, tools: Optional[List[LLMTool]] = None) -> Dict[str, Any]:
        """Mock implementation that returns predefined responses or tool calls."""
        if self.should_error:
            raise Exception("Mock LLM provider error")
            
        # Store call information for verification
        prompt = context.get_prompt()
        self.call_history.append({
            "prompt": prompt,
            "tools": [tool.name for tool in (tools or [])],
            "call_number": self.call_count
        })
        
        # Return tool calls if specified, otherwise return text response
        if self.tool_calls and self.call_count < len(self.tool_calls):
            result = {
                'text': None,
                'tool_calls': self.tool_calls[self.call_count]
            }
        else:
            response_index = self.call_count % len(self.responses)
            result = {
                'text': self.responses[response_index],
                'tool_calls': []
            }
        
        self.call_count += 1
        return result


@pytest.fixture
def mock_llm_provider():
    """Create a basic mock LLM provider."""
    return MockLLMProvider()


@pytest.fixture
def mock_llm_provider_with_tools():
    """Create a mock LLM provider that returns tool calls."""
    tool_calls = [[{
        "id": "call_123",
        "name": "simple_tool", 
        "arguments": {"text": "test input"}
    }]]
    
    return MockLLMProvider(
        responses=["Final response after tool use"],
        tool_calls=tool_calls
    )


@pytest.fixture
def mock_llm_provider_error():
    """Create a mock LLM provider that raises errors."""
    return MockLLMProvider(should_error=True)


@pytest.fixture
def conversation_id():
    """Standard conversation ID for testing."""
    return "test_conversation_123"


@pytest.fixture
def different_conversation_id():
    """Different conversation ID for testing isolation."""
    return "different_conversation_456"


# Cleanup fixture to ensure tests don't interfere with each other
@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Automatically clean up after each test."""
    yield
    # Any cleanup code can go here if needed
    pass
