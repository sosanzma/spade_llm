# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=spade_llm --cov-report=term-missing

# Run specific test file
pytest tests/test_agent/test_llm_agent.py

# Run tests with specific markers
pytest -m unit
pytest -m integration
pytest -m slow

# Run tests using tox (multiple Python versions)
tox
```

### Code Quality
```bash
# Format code with black
black spade_llm/

# Sort imports with isort
isort spade_llm/

# Run flake8 linting
flake8 --ignore=E501 spade_llm

# Run flake8 through tox
tox -e flake8

# Run coverage analysis
tox -e coverage
```

### Installation & Setup
```bash
# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"

# Install all optional dependencies
pip install -e ".[all]"
```

## Environment Variables

```bash
# Configure memory storage path
export SPADE_LLM_MEMORY_PATH="/custom/memory/path"
```

## Architecture Overview

SPADE_LLM extends the SPADE multi-agent framework with Large Language Model capabilities. The system follows a layered architecture:

### Core Components

1. **LLMAgent** (spade_llm/agent/llm_agent.py) - Main orchestrator that extends SPADE's Agent class, integrating all system components including providers, context management, tools, MCP servers, guardrails, and routing functions.

2. **LLMBehaviour** (spade_llm/behaviour/llm_behaviour.py) - Cyclic behavior that processes incoming XMPP messages, manages conversation state, handles tool execution loops (up to 20 iterations), and applies guardrails.

3. **ContextManager** (spade_llm/context/context_manager.py) - Manages conversation history across multiple concurrent conversations, storing messages by conversation ID and handling system prompts with proper metadata filtering.

4. **LLMProvider** (spade_llm/providers/base_provider.py) - Abstract interface for different LLM services (OpenAI, Gemini, Ollama, etc.) that standardizes communication and tool calling.

5. **LLMTool** (spade_llm/tools/llm_tool.py) - Tool system supporting both sync/async functions with schema-based validation and automatic execution handling.

6. **Guardrails** (spade_llm/guardrails/base.py) - Content filtering system that can PASS, MODIFY, BLOCK, or issue WARNINGS on input/output content.

7. **MCP Integration** (spade_llm/mcp/session.py) - Model Context Protocol support for external tool and service integration with connection pooling and caching.

### Key Patterns

- **Multi-conversation support**: Per-conversation context isolation with automatic lifecycle management
- **Tool chaining**: LLMs can make multiple sequential tool calls before providing final responses  
- **Provider abstraction**: Clean separation enabling easy switching between LLM providers
- **Async/sync bridge**: Unified handling of both async and sync tool functions using asyncio.to_thread()

### Project Structure

- `spade_llm/agent/` - Core agent implementations (LLMAgent, ChatAgent)
- `spade_llm/behaviour/` - Message processing behaviors  
- `spade_llm/context/` - Conversation and context management
- `spade_llm/providers/` - LLM provider implementations
- `spade_llm/tools/` - Tool system and LangChain adapter
- `spade_llm/guardrails/` - Content filtering and safety controls
- `spade_llm/mcp/` - Model Context Protocol integration
- `spade_llm/routing/` - Message routing system
- `spade_llm/utils/` - Utilities (environment loading, etc.)
- `examples/` - Working examples and demonstrations
- `tests/` - Comprehensive test suite with unit and integration tests

### Dependencies

- Core: SPADE 3.3.0+, OpenAI 1.0.0+, Pydantic 2.0.0+, aiohttp 3.8.0+
- Development: pytest, black, isort, flake8, coverage, tox, pre-commit
- Optional: google-generativeai, anthropic (for additional LLM providers)

### Test Organization

Tests follow the package structure and use pytest with asyncio support. Test markers include:
- `unit` - Unit tests for individual components
- `integration` - Integration tests across components  
- `slow` - Longer-running tests
- `asyncio` - Async test functions

Coverage target is 80% with HTML and XML reports generated automatically.

## Documentation Guidelines

### Writing Style

When writing or updating documentation for SPADE_LLM:

**AVOID marketing adjectives and promotional language:**
- ❌ sophisticated, intelligent, creative, amazing, powerful
- ❌ advanced, cutting-edge, innovative, robust, elegant
- ❌ seamless, revolutionary, outstanding, excellent, perfect
- ❌ brilliant, fantastic, incredible, remarkable, exceptional
- ❌ superior, premium, enhanced, optimized, streamlined
- ❌ state-of-the-art, magic happens, cutting-edge

**USE objective, technical language:**
- ✅ "The SmartWindowSizeContext uses an algorithm" (not "sophisticated algorithm")
- ✅ "Context management with message selection" (not "advanced context management")
- ✅ "Management combining sliding window..." (not "intelligent management")
- ✅ "Reliable termination" (not "robust termination")
- ✅ "Extended strategies" (not "advanced strategies")

**Focus on:**
- Clear, factual descriptions of functionality
- Technical accuracy over promotional language
- Objective benefits and capabilities
- Practical usage and implementation details

This maintains a professional, technical tone appropriate for developer documentation.