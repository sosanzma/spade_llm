---
title: SPADE-LLM Documentation - Multi-Agent LLM Framework for Python
description: Complete documentation for SPADE-LLM, a Python framework for integrating Large Language Models into multi-agent systems. OpenAI GPT, Ollama, LM Studio support for AI agents and chatbots.
keywords: SPADE-LLM, multi-agent systems, large language models, OpenAI, GPT, Ollama, Python AI framework, chatbot development, distributed AI, agent communication
---

# SPADE-LLM: Large Language Model Integration for Multi-Agent Systems

<div style="text-align: center; margin: 1rem 0;">
  <img src="assets/images/spade_llm_logo.png" alt="SPADE-LLM Logo" style="max-width: 200px; width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 16px rgba(142, 68, 173, 0.2);">
</div>

**SPADE-LLM** is a Python framework that extends [SPADE](https://github.com/javipalanca/spade) multi-agent platform with Large Language Model capabilities. Build AI agents powered by OpenAI GPT, Ollama, LM Studio, and other LLM providers for distributed AI applications, intelligent chatbots, and collaborative agent systems.

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "SPADE-LLM",
  "description": "Python framework for Large Language Model integration in multi-agent systems",
  "url": "https://sosanzma.github.io/spade_llm/",
  "applicationCategory": "DeveloperApplication",
  "operatingSystem": "Cross-platform",
  "programmingLanguage": "Python",
  "license": "https://opensource.org/licenses/MIT",
  "downloadUrl": "https://pypi.org/project/spade-llm/",
  "codeRepository": "https://github.com/sosanzma/spade_llm",
  "author": {
    "@type": "Person",
    "name": "Manel Soler Sanz"
  },
  "keywords": ["SPADE", "LLM", "multi-agent", "OpenAI", "GPT", "Ollama", "AI", "chatbot", "Python"],
  "softwareVersion": "latest",
  "requirements": "Python 3.10+",
  "featureList": [
    "Multi-LLM Provider Support",
    "Advanced Tool System", 
    "Context Management",
    "Memory Extensions",
    "Message Routing",
    "Content Safety Guardrails",
    "MCP Integration",
    "Human-in-the-Loop"
  ]
}
</script>

## Features

- **Multi-Provider Support**: OpenAI, Ollama, LM Studio, vLLM
- **Tool System**: Function calling with async execution
- **Memory System**: Dual memory architecture for agent learning and conversation continuity
- **Context Management**: Multi-conversation support with automatic cleanup
- **Message Routing**: Conditional routing based on LLM responses
- **Guardrails System**: Content filtering and safety controls for input/output
- **MCP Integration**: Model Context Protocol server support
- **Production Ready**: Comprehensive error handling and logging

## Architecture

```mermaid
graph LR
    A[LLMAgent] --> C[ContextManager]
    A --> D[LLMProvider]
    A --> E[LLMTool]
    A --> G[Guardrails]
    A --> M[Memory]
    D --> F[OpenAI/Ollama/etc]
    G --> H[Input/Output Filtering]
    E --> I[Human-in-the-Loop]
    E --> J[MCP]
    E --> P[CustomTool/LangchainTool]
    J --> K[STDIO]
    J --> L[HTTP Streaming]
    M --> N[Agent-based]
    M --> O[Agent-thread]
```

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


