"""Tests for the unified LLM provider implementation."""

import json
import pytest
from unittest.mock import MagicMock, Mock, patch, AsyncMock
from openai import OpenAI, OpenAIError

from spade_llm.providers.llm_provider import LLMProvider, ModelFormat
from spade_llm.context import ContextManager
from spade_llm.tools import LLMTool


class TestLLMProviderInit:
    """Test LLMProvider initialization and configuration."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        provider = LLMProvider()
        
        assert provider.api_key == "dummy"
        assert provider.model == "gpt-4o-mini"
        assert provider.temperature == 0.7
        assert provider.base_url is None
        assert provider.timeout == 60.0
        assert provider.max_tokens is None
        assert provider.model_format == ModelFormat.OPENAI
        assert provider.provider_name == "OpenAI"

    def test_init_with_custom_values(self):
        """Test initialization with custom values."""
        provider = LLMProvider(
            api_key="test-key",
            model="gpt-4",
            temperature=0.5,
            base_url="http://localhost:8000",
            timeout=120.0,
            max_tokens=1000,
            model_format=ModelFormat.OLLAMA,
            provider_name="CustomProvider"
        )
        
        assert provider.api_key == "test-key"
        assert provider.model == "gpt-4"
        assert provider.temperature == 0.5
        assert provider.base_url == "http://localhost:8000"
        assert provider.timeout == 120.0
        assert provider.max_tokens == 1000
        assert provider.model_format == ModelFormat.OLLAMA
        assert provider.provider_name == "CustomProvider"

    @patch('spade_llm.providers.llm_provider.OpenAI')
    def test_client_initialization(self, mock_openai):
        """Test that OpenAI client is initialized correctly."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        provider = LLMProvider(api_key="test-key", base_url="http://test.com")
        
        mock_openai.assert_called_once_with(
            api_key="test-key",
            base_url="http://test.com"
        )
        assert provider.client == mock_client

    @patch('spade_llm.providers.llm_provider.OpenAI')
    def test_client_initialization_no_base_url(self, mock_openai):
        """Test client initialization without base_url."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        provider = LLMProvider(api_key="test-key")
        
        mock_openai.assert_called_once_with(api_key="test-key")


class TestModelFormatDetection:
    """Test model format detection logic."""

    def test_detect_model_format_ollama_prefix(self):
        """Test detection of Ollama format with ollama/ prefix."""
        provider = LLMProvider()
        format_result = provider._detect_model_format("ollama/llama3:8b", None)
        assert format_result == ModelFormat.OLLAMA

    def test_detect_model_format_openai_gpt(self):
        """Test detection of OpenAI format with gpt- prefix."""
        provider = LLMProvider()
        format_result = provider._detect_model_format("gpt-4", None)
        assert format_result == ModelFormat.OPENAI

    def test_detect_model_format_openai_o1(self):
        """Test detection of OpenAI format with o1- prefix."""
        provider = LLMProvider()
        format_result = provider._detect_model_format("o1-preview", None)
        assert format_result == ModelFormat.OPENAI

    def test_detect_model_format_custom_slash(self):
        """Test detection of custom format with slash."""
        provider = LLMProvider()
        format_result = provider._detect_model_format("custom/model-name", None)
        assert format_result == ModelFormat.CUSTOM

    def test_detect_model_format_base_url_ollama(self):
        """Test format detection based on base_url containing ollama."""
        provider = LLMProvider()
        format_result = provider._detect_model_format("llama3", "http://localhost:11434/ollama")
        assert format_result == ModelFormat.OLLAMA

    def test_detect_model_format_default_openai(self):
        """Test default to OpenAI format."""
        provider = LLMProvider()
        format_result = provider._detect_model_format("some-model", None)
        assert format_result == ModelFormat.OPENAI


class TestProviderNameDetection:
    """Test provider name detection logic."""

    def test_detect_provider_name_no_base_url(self):
        """Test provider name when no base_url provided."""
        provider = LLMProvider()
        name = provider._detect_provider_name(None, ModelFormat.OPENAI)
        assert name == "OpenAI"

    def test_detect_provider_name_ollama(self):
        """Test detection of Ollama provider."""
        provider = LLMProvider()
        name = provider._detect_provider_name("http://localhost:11434/ollama", ModelFormat.OLLAMA)
        assert name == "Ollama"

    def test_detect_provider_name_vllm(self):
        """Test detection of vLLM provider."""
        provider = LLMProvider()
        name = provider._detect_provider_name("http://localhost:8000/vllm", ModelFormat.OPENAI)
        assert name == "vLLM"

    def test_detect_provider_name_lmstudio(self):
        """Test detection of LM Studio provider."""
        provider = LLMProvider()
        name = provider._detect_provider_name("http://localhost:1234/lmstudio", ModelFormat.OPENAI)
        assert name == "LM Studio"

    def test_detect_provider_name_localhost(self):
        """Test detection of localhost provider."""
        provider = LLMProvider()
        name = provider._detect_provider_name("http://localhost:8000", ModelFormat.OPENAI)
        assert name == "Local OpenAI-compatible"

    def test_detect_provider_name_127001(self):
        """Test detection of 127.0.0.1 provider."""
        provider = LLMProvider()
        name = provider._detect_provider_name("http://127.0.0.1:8000", ModelFormat.OPENAI)
        assert name == "Local OpenAI-compatible"

    def test_detect_provider_name_generic(self):
        """Test generic OpenAI-compatible provider detection."""
        provider = LLMProvider()
        name = provider._detect_provider_name("http://api.example.com", ModelFormat.OPENAI)
        assert name == "OpenAI-compatible"


class TestModelNamePreparation:
    """Test model name preparation for API calls."""

    def test_prepare_model_name_ollama_with_prefix(self):
        """Test preparation of Ollama model name with prefix."""
        provider = LLMProvider(model="ollama/llama3:8b", model_format=ModelFormat.OLLAMA)
        prepared = provider._prepare_model_name("ollama/llama3:8b")
        assert prepared == "llama3:8b"

    def test_prepare_model_name_ollama_without_prefix(self):
        """Test preparation of Ollama model name without prefix."""
        provider = LLMProvider(model="llama3:8b", model_format=ModelFormat.OLLAMA)
        prepared = provider._prepare_model_name("llama3:8b")
        assert prepared == "llama3:8b"

    def test_prepare_model_name_openai(self):
        """Test preparation of OpenAI model name (no change)."""
        provider = LLMProvider(model="gpt-4", model_format=ModelFormat.OPENAI)
        prepared = provider._prepare_model_name("gpt-4")
        assert prepared == "gpt-4"

    def test_prepare_model_name_custom(self):
        """Test preparation of custom model name (no change)."""
        provider = LLMProvider(model="custom/model", model_format=ModelFormat.CUSTOM)
        prepared = provider._prepare_model_name("custom/model")
        assert prepared == "custom/model"


class TestCreateMethods:
    """Test class methods for creating providers."""

    def test_create_openai(self):
        """Test creating OpenAI provider."""
        provider = LLMProvider.create_openai(
            api_key="test-key",
            model="gpt-4",
            temperature=0.5
        )
        
        assert provider.api_key == "test-key"
        assert provider.model == "gpt-4"
        assert provider.temperature == 0.5
        assert provider.provider_name == "OpenAI"
        assert provider.base_url is None

    def test_create_openai_with_kwargs(self):
        """Test creating OpenAI provider with additional kwargs."""
        provider = LLMProvider.create_openai(
            api_key="test-key",
            max_tokens=1000,
            timeout=30.0
        )
        
        assert provider.max_tokens == 1000
        assert provider.timeout == 30.0

    def test_create_ollama(self):
        """Test creating Ollama provider."""
        provider = LLMProvider.create_ollama(
            model="llama3:8b",
            base_url="http://localhost:11434/v1",
            temperature=0.8,
            timeout=180.0
        )
        
        assert provider.api_key == "dummy"
        assert provider.model == "ollama/llama3:8b"  # Should add prefix
        assert provider.base_url == "http://localhost:11434/v1"
        assert provider.temperature == 0.8
        assert provider.timeout == 180.0
        assert provider.provider_name == "Ollama"
        assert provider.model_format == ModelFormat.OLLAMA

    def test_create_ollama_with_prefix(self):
        """Test creating Ollama provider when model already has prefix."""
        provider = LLMProvider.create_ollama(model="ollama/llama3:8b")
        assert provider.model == "ollama/llama3:8b"  # Should not double-prefix

    def test_create_lm_studio(self):
        """Test creating LM Studio provider."""
        provider = LLMProvider.create_lm_studio(
            model="local-model",
            base_url="http://localhost:1234/v1",
            temperature=0.6
        )
        
        assert provider.api_key == "dummy"
        assert provider.model == "local-model"
        assert provider.base_url == "http://localhost:1234/v1"
        assert provider.temperature == 0.6
        assert provider.provider_name == "LM Studio"

    def test_create_vllm(self):
        """Test creating vLLM provider."""
        provider = LLMProvider.create_vllm(
            model="meta-llama/Llama-2-7b-hf",
            base_url="http://localhost:8000/v1"
        )
        
        assert provider.api_key == "dummy"
        assert provider.model == "meta-llama/Llama-2-7b-hf"
        assert provider.base_url == "http://localhost:8000/v1"
        assert provider.provider_name == "vLLM"

    def test_create_vllm_with_kwargs(self):
        """Test creating vLLM provider with additional kwargs."""
        provider = LLMProvider.create_vllm(
            model="test-model",
            max_tokens=2000,
            temperature=0.9
        )
        
        assert provider.max_tokens == 2000
        assert provider.temperature == 0.9


class TestGetLLMResponse:
    """Test the main get_llm_response method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_context = Mock(spec=ContextManager)
        self.mock_context.get_prompt.return_value = [{"role": "user", "content": "test"}]

    @patch('spade_llm.providers.llm_provider.asyncio.to_thread')
    @patch('spade_llm.providers.llm_provider.OpenAI')
    @pytest.mark.asyncio
    async def test_get_llm_response_text_only(self, mock_openai_class, mock_to_thread):
        """Test get_llm_response with text response only."""
        # Setup mocks
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_message = Mock()
        mock_message.content = "Test response"
        mock_message.tool_calls = None
        
        mock_response = Mock()
        mock_response.choices = [Mock(message=mock_message)]
        
        mock_to_thread.return_value = mock_response
        
        provider = LLMProvider()
        result = await provider.get_llm_response(self.mock_context)
        
        assert result["text"] == "Test response"
        assert result["tool_calls"] == []
        
        # Verify the API call
        mock_to_thread.assert_called_once()
        call_args = mock_to_thread.call_args[1]
        assert call_args["model"] == "gpt-4o-mini"
        assert call_args["temperature"] == 0.7
        assert call_args["timeout"] == 60.0

    @patch('spade_llm.providers.llm_provider.asyncio.to_thread')
    @patch('spade_llm.providers.llm_provider.OpenAI')
    @pytest.mark.asyncio
    async def test_get_llm_response_with_tools(self, mock_openai_class, mock_to_thread):
        """Test get_llm_response with tool calls."""
        # Setup mocks
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_tool_call = Mock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "test_tool"
        mock_tool_call.function.arguments = '{"param": "value"}'
        
        mock_message = Mock()
        mock_message.content = None
        mock_message.tool_calls = [mock_tool_call]
        
        mock_response = Mock()
        mock_response.choices = [Mock(message=mock_message)]
        
        mock_to_thread.return_value = mock_response
        
        # Create mock tool
        mock_tool = Mock(spec=LLMTool)
        mock_tool.to_openai_tool.return_value = {
            "function": {"name": "test_tool"},
            "type": "function"
        }
        
        provider = LLMProvider()
        result = await provider.get_llm_response(self.mock_context, tools=[mock_tool])
        
        assert result["text"] is None
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["id"] == "call_123"
        assert result["tool_calls"][0]["name"] == "test_tool"
        assert result["tool_calls"][0]["arguments"] == {"param": "value"}

    @patch('spade_llm.providers.llm_provider.asyncio.to_thread')
    @patch('spade_llm.providers.llm_provider.OpenAI')
    @pytest.mark.asyncio
    async def test_get_llm_response_with_max_tokens(self, mock_openai_class, mock_to_thread):
        """Test get_llm_response includes max_tokens when set."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_message = Mock()
        mock_message.content = "Test response"
        mock_message.tool_calls = None
        
        mock_response = Mock()
        mock_response.choices = [Mock(message=mock_message)]
        
        mock_to_thread.return_value = mock_response
        
        provider = LLMProvider(max_tokens=1000)
        await provider.get_llm_response(self.mock_context)
        
        # Check that max_tokens was included in the call
        call_args = mock_to_thread.call_args[1]
        assert call_args["max_tokens"] == 1000

    @patch('spade_llm.providers.llm_provider.asyncio.to_thread')
    @patch('spade_llm.providers.llm_provider.OpenAI')
    @pytest.mark.asyncio
    async def test_get_llm_response_json_decode_error(self, mock_openai_class, mock_to_thread):
        """Test handling of JSON decode error in tool arguments."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_tool_call = Mock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "test_tool"
        mock_tool_call.function.arguments = 'invalid json{'
        
        mock_message = Mock()
        mock_message.content = None
        mock_message.tool_calls = [mock_tool_call]
        
        mock_response = Mock()
        mock_response.choices = [Mock(message=mock_message)]
        
        mock_to_thread.return_value = mock_response
        
        provider = LLMProvider()
        result = await provider.get_llm_response(self.mock_context)
        
        # Should handle the error gracefully
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["arguments"] == {}  # Empty dict on error

    @patch('spade_llm.providers.llm_provider.asyncio.to_thread')
    @patch('spade_llm.providers.llm_provider.OpenAI')
    @pytest.mark.asyncio
    async def test_get_llm_response_openai_error(self, mock_openai_class, mock_to_thread):
        """Test handling of OpenAI API errors."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_to_thread.side_effect = OpenAIError("API Error")
        
        provider = LLMProvider()
        
        with pytest.raises(OpenAIError):
            await provider.get_llm_response(self.mock_context)

    @patch('spade_llm.providers.llm_provider.asyncio.to_thread')
    @patch('spade_llm.providers.llm_provider.OpenAI')
    @pytest.mark.asyncio
    async def test_get_llm_response_unexpected_error(self, mock_openai_class, mock_to_thread):
        """Test handling of unexpected errors."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_to_thread.side_effect = ValueError("Unexpected error")
        
        provider = LLMProvider()
        
        with pytest.raises(ValueError):
            await provider.get_llm_response(self.mock_context)

    @patch('spade_llm.providers.llm_provider.asyncio.to_thread')
    @patch('spade_llm.providers.llm_provider.OpenAI')
    @pytest.mark.asyncio
    async def test_get_llm_response_ollama_provider(self, mock_openai_class, mock_to_thread):
        """Test get_llm_response with Ollama provider (includes special logging)."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_message = Mock()
        mock_message.content = "Test response"
        mock_message.tool_calls = None
        
        mock_response = Mock()
        mock_response.choices = [Mock(message=mock_message)]
        
        mock_to_thread.return_value = mock_response
        
        # Create mock tool
        mock_tool = Mock(spec=LLMTool)
        mock_tool.to_openai_tool.return_value = {
            "function": {"name": "test_tool"},
            "type": "function"
        }
        
        provider = LLMProvider.create_ollama()
        result = await provider.get_llm_response(self.mock_context, tools=[mock_tool])
        
        # Should complete successfully and include tools in the call
        call_args = mock_to_thread.call_args[1]
        assert "tools" in call_args
        assert call_args["tool_choice"] == "auto"


class TestLegacyMethods:
    """Test legacy methods that delegate to get_llm_response."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_context = Mock(spec=ContextManager)

    @patch.object(LLMProvider, 'get_llm_response')
    @pytest.mark.asyncio
    async def test_get_response_returns_text(self, mock_get_llm_response):
        """Test get_response returns text from get_llm_response."""
        mock_get_llm_response.return_value = {
            "text": "Test response",
            "tool_calls": []
        }
        
        provider = LLMProvider()
        result = await provider.get_response(self.mock_context)
        
        assert result == "Test response"
        mock_get_llm_response.assert_called_once_with(self.mock_context, None)

    @patch.object(LLMProvider, 'get_llm_response')
    @pytest.mark.asyncio
    async def test_get_response_with_tools_parameter(self, mock_get_llm_response):
        """Test get_response passes tools parameter."""
        mock_get_llm_response.return_value = {"text": "Response", "tool_calls": []}
        
        mock_tools = [Mock()]
        provider = LLMProvider()
        await provider.get_response(self.mock_context, tools=mock_tools)
        
        mock_get_llm_response.assert_called_once_with(self.mock_context, mock_tools)

    @patch.object(LLMProvider, 'get_llm_response')
    @pytest.mark.asyncio
    async def test_get_tool_calls_returns_list(self, mock_get_llm_response):
        """Test get_tool_calls returns tool_calls from get_llm_response."""
        expected_calls = [{"id": "call_1", "name": "tool", "arguments": {}}]
        mock_get_llm_response.return_value = {
            "text": None,
            "tool_calls": expected_calls
        }
        
        provider = LLMProvider()
        result = await provider.get_tool_calls(self.mock_context)
        
        assert result == expected_calls
        mock_get_llm_response.assert_called_once_with(self.mock_context, None)

    @patch.object(LLMProvider, 'get_llm_response')
    @pytest.mark.asyncio
    async def test_get_tool_calls_empty_list(self, mock_get_llm_response):
        """Test get_tool_calls returns empty list when no tool_calls."""
        mock_get_llm_response.return_value = {
            "text": "Just text",
            "tool_calls": []
        }
        
        provider = LLMProvider()
        result = await provider.get_tool_calls(self.mock_context)
        
        assert result == []


class TestIntegration:
    """Integration tests for the LLMProvider."""

    @pytest.mark.asyncio
    async def test_provider_workflow_text_response(self, context_manager):
        """Test complete workflow with text response."""
        with patch('spade_llm.providers.llm_provider.asyncio.to_thread') as mock_to_thread:
            mock_message = Mock()
            mock_message.content = "Hello, how can I help you?"
            mock_message.tool_calls = None
            
            mock_response = Mock()
            mock_response.choices = [Mock(message=mock_message)]
            mock_to_thread.return_value = mock_response
            
            provider = LLMProvider.create_openai("test-key")
            
            # Test the complete workflow
            llm_response = await provider.get_llm_response(context_manager)
            text_response = await provider.get_response(context_manager)  
            tool_calls = await provider.get_tool_calls(context_manager)
            
            assert llm_response["text"] == "Hello, how can I help you?"
            assert llm_response["tool_calls"] == []
            assert text_response == "Hello, how can I help you?"
            assert tool_calls == []

    @pytest.mark.asyncio
    async def test_provider_workflow_tool_calls(self, context_manager):
        """Test complete workflow with tool calls."""
        with patch('spade_llm.providers.llm_provider.asyncio.to_thread') as mock_to_thread:
            mock_tool_call = Mock()
            mock_tool_call.id = "call_abc123"
            mock_tool_call.function.name = "get_weather"
            mock_tool_call.function.arguments = '{"location": "Paris"}'
            
            mock_message = Mock()
            mock_message.content = None
            mock_message.tool_calls = [mock_tool_call]
            
            mock_response = Mock()
            mock_response.choices = [Mock(message=mock_message)]
            mock_to_thread.return_value = mock_response
            
            # Create a mock tool
            mock_tool = Mock(spec=LLMTool)
            mock_tool.to_openai_tool.return_value = {
                "type": "function",
                "function": {"name": "get_weather"}
            }
            
            provider = LLMProvider.create_openai("test-key")
            
            # Test the complete workflow
            llm_response = await provider.get_llm_response(context_manager, tools=[mock_tool])
            text_response = await provider.get_response(context_manager, tools=[mock_tool])
            tool_calls = await provider.get_tool_calls(context_manager, tools=[mock_tool])
            
            assert llm_response["text"] is None
            assert len(llm_response["tool_calls"]) == 1
            assert text_response is None
            assert len(tool_calls) == 1
            assert tool_calls[0]["name"] == "get_weather"
            assert tool_calls[0]["arguments"] == {"location": "Paris"}