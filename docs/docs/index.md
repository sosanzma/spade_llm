# SPADE-LLM : SPADE with Large Language Models 

<div style="text-align: center; margin: 2rem 0;">
  <span style="background: linear-gradient(135deg, #8e44ad, #9b59b6); color: white; padding: 0.5rem 1.5rem; border-radius: 25px; font-weight: 500;">
    🚀 Spade-LLM Extension
  </span>
</div>

Extension for [SPADE](https://github.com/javipalanca/spade) that integrates Large Language Models into multi-agent systems.

## Features

- **Multi-Provider Support**: OpenAI, Ollama, LM Studio, vLLM
- **Tool System**: Function calling with async execution
- **Memory System**: Dual memory architecture for agent learning and conversation continuity
- **Context Management**: Multi-conversation support with automatic cleanup
- **Message Routing**: Conditional routing based on LLM responses
- **Guardrails System**: Content filtering and safety controls for input/output
- **MCP Integration**: Model Context Protocol server support
- **Production Ready**: Comprehensive error handling and logging

## Quick Start

```python
import spade
from spade_llm import LLMAgent, LLMProvider

async def main():
    provider = LLMProvider.create_openai(
        api_key="your-api-key",
        model="gpt-4o-mini"
    )
    
    agent = LLMAgent(
        jid="assistant@example.com",
        password="password",
        provider=provider,
        system_prompt="You are a helpful assistant"
    )
    
    await agent.start()

if __name__ == "__main__":
    spade.run(main())
```

## Architecture

```mermaid
graph TB
    A[LLMAgent] --> B[LLMBehaviour]
    B --> C[ContextManager]
    B --> D[LLMProvider]
    B --> E[LLMTool]
    B --> I[Guardrails System]
    
    D --> F[OpenAI/Ollama/etc]
    E --> G[Python Functions]
    E --> H[MCP Servers]
    I --> J[Input Filters]
    I --> K[Output Filters]
```

## Documentation Structure

### Getting Started
- **[Installation](getting-started/installation.md)** - Setup and requirements
- **[Quick Start](getting-started/quickstart.md)** - Basic usage examples

### Core Guides
- **[Architecture](guides/architecture.md)** - SPADE_LLM general structure
- **[Providers](guides/providers.md)** - LLM provider configuration
- **[Tools System](guides/tools-system.md)** - Function calling capabilities
- **[Memory System](guides/memory.md)** - Agent learning and conversation continuity
- **[Context Management](guides/context-management.md)** - Context control and message management
- **[Conversations](guides/conversations.md)** - Conversation lifecycle and management
- **[Guardrails](guides/guardrails.md)** - Content filtering and safety controls
- **[Message Routing](guides/routing.md)** - Conditional message routing



### Reference
- **[API Reference](reference/)** - Complete API documentation
- **[Examples](reference/examples.md)** - Working code examples

## Examples

Explore the [examples directory](https://github.com/sosanzma/spade_llm/tree/main/examples) for complete working examples:

- **`multi_provider_chat_example.py`** - Chat with different LLM providers
- **`ollama_with_tools_example.py`** - Local models with tool calling
- **`guardrails_example.py`** - Content filtering and safety controls
- **`langchain_tools_example.py`** - LangChain tool integration
- **`valencia_multiagent_trip_planner.py`** - Multi-agent workflow


