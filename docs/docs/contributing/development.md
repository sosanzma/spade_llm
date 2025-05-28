# Development Guide

Detailed guide for SPADE_LLM development and testing.

## Development Environment

### Setup

```bash
# Clone repository
git clone https://github.com/sosanzma/spade_llm.git
cd spade_llm

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install development dependencies
pip install -e ".[dev,docs]"

# Setup pre-commit hooks
pre-commit install
```

### Project Structure

```
spade_llm/
├── spade_llm/          # Main package
│   ├── agent/          # Agent implementations
│   ├── behaviour/      # Behaviour classes
│   ├── context/        # Context management
│   ├── providers/      # LLM providers
│   ├── tools/          # Tool system
│   ├── routing/        # Message routing
│   ├── mcp/           # MCP integration
│   └── utils/         # Utilities
├── tests/             # Test suite
├── examples/          # Usage examples
├── docs/             # Documentation
└── requirements*.txt  # Dependencies
```

## Testing

### Test Organization

```
tests/
├── test_agent/        # Agent tests
├── test_behaviour/    # Behaviour tests
├── test_context/      # Context tests
├── test_providers/    # Provider tests
├── test_tools/        # Tool tests
├── test_routing/      # Routing tests
├── conftest.py        # Test configuration
└── factories.py       # Test factories
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=spade_llm --cov-report=html

# Run specific test module
pytest tests/test_agent/

# Run specific test
pytest tests/test_agent/test_llm_agent.py::test_agent_creation

# Run with verbose output
pytest -v -s
```

### Writing Tests

#### Test Structure

```python
import pytest
from unittest.mock import AsyncMock, Mock
from spade_llm import LLMAgent, LLMProvider

class TestLLMAgent:
    """Test LLMAgent functionality."""
    
    @pytest.fixture
    def mock_provider(self):
        """Create mock LLM provider."""
        provider = AsyncMock(spec=LLMProvider)
        provider.get_llm_response.return_value = {
            'text': 'Test response',
            'tool_calls': []
        }
        return provider
    
    @pytest.mark.asyncio
    async def test_agent_creation(self, mock_provider):
        """Test agent creation with mock provider."""
        agent = LLMAgent(
            jid="test@example.com",
            password="password",
            provider=mock_provider
        )
        
        assert agent.jid == "test@example.com"
        assert agent.provider == mock_provider
    
    @pytest.mark.asyncio
    async def test_agent_startup(self, mock_provider):
        """Test agent startup process."""
        agent = LLMAgent(
            jid="test@example.com",
            password="password",
            provider=mock_provider
        )
        
        # Mock XMPP connection
        with patch.object(agent, '_connect') as mock_connect:
            mock_connect.return_value = True
            await agent.start()
            
            assert agent.is_alive()
```

#### Testing Async Code

```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async function execution."""
    result = await async_function()
    assert result is not None

# For testing timeouts
@pytest.mark.asyncio
async def test_timeout_handling():
    """Test timeout handling."""
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(slow_function(), timeout=1.0)
```

#### Testing Tools

```python
@pytest.mark.asyncio
async def test_tool_execution():
    """Test tool execution."""
    async def test_function(param: str) -> str:
        return f"Result: {param}"
    
    tool = LLMTool(
        name="test_tool",
        description="Test tool",
        parameters={
            "type": "object",
            "properties": {"param": {"type": "string"}},
            "required": ["param"]
        },
        func=test_function
    )
    
    result = await tool.execute(param="test_value")
    assert result == "Result: test_value"
```

### Integration Tests

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_agent_workflow():
    """Test complete agent workflow."""
    # This would test with real XMPP server
    # Usually requires special setup
    pytest.skip("Requires XMPP server setup")
```

### Mocking Guidelines

#### Mock LLM Providers

```python
@pytest.fixture
def mock_openai_provider():
    """Mock OpenAI provider."""
    provider = AsyncMock(spec=LLMProvider)
    provider.get_llm_response.return_value = {
        'text': 'Mocked OpenAI response',
        'tool_calls': []
    }
    return provider

@pytest.fixture
def mock_provider_with_tools():
    """Mock provider that returns tool calls."""
    provider = AsyncMock(spec=LLMProvider)
    provider.get_llm_response.return_value = {
        'text': None,
        'tool_calls': [{
            'id': 'call_123',
            'name': 'test_tool',
            'arguments': {'param': 'value'}
        }]
    }
    return provider
```

#### Mock XMPP Connections

```python
@pytest.fixture
def mock_xmpp_agent():
    """Mock XMPP agent functionality."""
    with patch('spade.agent.Agent.__init__') as mock_init:
        mock_init.return_value = None
        with patch('spade.agent.Agent.start') as mock_start:
            mock_start.return_value = asyncio.Future()
            mock_start.return_value.set_result(None)
            yield mock_start
```

## Code Quality

### Style Guidelines

#### Code Formatting

```bash
# Format with Black
black spade_llm tests examples

# Check formatting
black --check spade_llm tests examples
```

#### Import Sorting

```bash
# Sort imports with isort
isort spade_llm tests examples

# Check import sorting
isort --check-only spade_llm tests examples
```

#### Linting

```bash
# Check with flake8
flake8 spade_llm tests examples

# Configuration in setup.cfg:
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,build,dist,.venv
```

#### Type Checking

```bash
# Check types with mypy
mypy spade_llm

# Configuration in pyproject.toml:
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
```

### Documentation Standards

#### Docstring Format

```python
def example_function(param1: str, param2: int = 0) -> str:
    """Brief description of the function.
    
    Longer description if needed. Explain the purpose,
    behavior, and any important details.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter with default value
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When invalid input is provided
        ConnectionError: When service is unavailable
        
    Example:
        ```python
        result = example_function("hello", 42)
        print(result)  # Output: processed result
        ```
    """
    # Implementation here
    pass
```

#### Class Documentation

```python
class ExampleClass:
    """Brief description of the class.
    
    Longer description explaining the class purpose,
    usage patterns, and important behavior.
    
    Attributes:
        attribute1: Description of attribute
        attribute2: Description of another attribute
        
    Example:
        ```python
        instance = ExampleClass(param="value")
        result = instance.method()
        ```
    """
    
    def __init__(self, param: str):
        """Initialize the class.
        
        Args:
            param: Configuration parameter
        """
        self.attribute1 = param
```

## Debugging

### Logging Configuration

```python
import logging

# Setup debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable specific loggers
logging.getLogger('spade_llm.agent').setLevel(logging.DEBUG)
logging.getLogger('spade_llm.providers').setLevel(logging.DEBUG)
```

### Debug Agent Behavior

```python
# Add debug prints to behaviour
class DebugLLMBehaviour(LLMBehaviour):
    async def run(self):
        print(f"Processing message: {self.get('message_count', 0)}")
        await super().run()
        print("Message processed")

# Use debug behaviour
agent.llm_behaviour = DebugLLMBehaviour(...)
```

### Testing with Real Services

```python
# For manual testing with real providers
async def test_with_real_openai():
    """Manual test with real OpenAI API."""
    if not os.getenv('OPENAI_API_KEY'):
        pytest.skip("No OpenAI API key provided")
    
    provider = LLMProvider.create_openai(
        api_key=os.getenv('OPENAI_API_KEY'),
        model="gpt-4o-mini"
    )
    
    context = ContextManager(system_prompt="You are helpful")
    context.add_message_dict(
        {"role": "user", "content": "Say hello"},
        "test_conversation"
    )
    
    response = await provider.get_llm_response(context)
    assert response['text'] is not None
    print(f"OpenAI response: {response['text']}")
```

## Performance Testing

### Benchmarking

```python
import time
import asyncio

async def benchmark_provider_response_time():
    """Benchmark provider response times."""
    provider = LLMProvider.create_openai(
        api_key=os.getenv('OPENAI_API_KEY'),
        model="gpt-4o-mini"
    )
    
    context = ContextManager()
    context.add_message_dict(
        {"role": "user", "content": "Hello"},
        "benchmark"
    )
    
    times = []
    for i in range(10):
        start = time.time()
        await provider.get_llm_response(context)
        end = time.time()
        times.append(end - start)
    
    avg_time = sum(times) / len(times)
    print(f"Average response time: {avg_time:.2f}s")
```

### Memory Usage Testing

```python
import tracemalloc
import gc

def test_memory_usage():
    """Test memory usage patterns."""
    tracemalloc.start()
    
    # Create many agents
    agents = []
    for i in range(100):
        agent = LLMAgent(
            jid=f"test{i}@example.com",
            password="password",
            provider=mock_provider
        )
        agents.append(agent)
    
    current, peak = tracemalloc.get_traced_memory()
    print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
    print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")
    
    # Cleanup
    del agents
    gc.collect()
    
    tracemalloc.stop()
```

## CI/CD Pipeline

### GitHub Actions

The project uses GitHub Actions for:

- **Testing** on multiple Python versions
- **Code quality** checks (linting, formatting)
- **Documentation** building and deployment
- **Security** scanning

### Local Pre-commit Checks

```bash
# Install pre-commit hooks
pre-commit install

# Run all hooks manually
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

### Release Process

1. **Update version** in `spade_llm/version.py`
2. **Update changelog** with new features and fixes
3. **Create release branch**
4. **Run full test suite**
5. **Create GitHub release**
6. **Deploy to PyPI** (automated)

## Troubleshooting

### Common Issues

#### Import Errors

```bash
# Reinstall in development mode
pip install -e .

# Check Python path
python -c "import sys; print(sys.path)"
```

#### Test Failures

```bash
# Run specific failing test with verbose output
pytest -vvs tests/path/to/failing_test.py::test_name

# Check test isolation
pytest --lf  # Run last failed tests
```

#### XMPP Connection Issues

```bash
# Test XMPP server connectivity
telnet localhost 5222

# Check firewall settings
# Verify XMPP server is running
```

### Debug Environment

```python
# Create debug configuration
DEBUG_CONFIG = {
    'log_level': logging.DEBUG,
    'verify_security': False,
    'timeout': 120.0,
    'max_retries': 1
}

# Use in tests
agent = LLMAgent(
    jid="debug@example.com",
    password="password",
    provider=provider,
    **DEBUG_CONFIG
)
```

This development guide should help you contribute effectively to SPADE_LLM. For specific questions, check the existing issues or create a new one.
