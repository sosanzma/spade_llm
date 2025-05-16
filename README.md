# SPADE_LLM

SPADE_LLM is an extension for [SPADE](https://github.com/javipalanca/spade) (Smart Python Agent Development Environment) that integrates Large Language Models (LLMs) capabilities into SPADE agents.

## Overview

SPADE_LLM extends SPADE's multi-agent framework by providing:

- Integration with multiple LLM providers (OpenAI, Ollama, LM Studio, vLLM)
- Tool-calling capabilities for agents
- Context management for conversations
- Model Context Protocol (MCP) support
- Routing mechanisms for inter-agent communication

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           SPADE_LLM                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐         │
│  │  LLMAgent   │───►│ LLMBehaviour │───►│ LLMProvider   │         │
│  │             │    │              │    │               │         │
│  └─────┬───────┘    └──────┬───────┘    └───────────────┘         │
│        │                   │                                       │
│        │                   ▼                                       │
│        │            ┌──────────────┐    ┌───────────────┐         │
│        │            │ContextManager│    │   LLMTool     │         │
│        │            │              │    │               │         │
│        │            └──────────────┘    └───────────────┘         │
│        │                                                           │
│        │            ┌──────────────┐    ┌───────────────┐         │
│        └───────────►│ MCP Session  │───►│  MCP Server   │         │
│                     │              │    │               │         │
│                     └──────────────┘    └───────────────┘         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                ▲
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                            SPADE                                    │
│                    (Multi-Agent Framework)                          │
└─────────────────────────────────────────────────────────────────────┘
```

### Core Components

- **LLMAgent**: Enhanced SPADE agent with LLM capabilities
- **LLMBehaviour**: Specialized behaviour for processing messages with LLMs
- **ContextManager**: Manages conversation history and context
- **LLMProvider**: Unified interface for LLM service integration (OpenAI, Ollama, LM Studio, vLLM)
- **LLMTool**: Framework for defining and executing tools
- **MCPServerConfig**: Configuration for Model Context Protocol servers

### Design Principles

SPADE_LLM follows a modular design where:

1. Agents maintain SPADE's asynchronous communication model
2. LLM interactions are abstracted through a unified provider
3. Tools can be native or adapted from external frameworks
4. Context management handles multi-conversation scenarios
5. MCP integration enables connection to external services

### LLM Behaviour Flow

```
┌─────────────────┐
│ Incoming Message│
└────────┬────────┘
         ▼
┌─────────────────────────────────────────────────┐
│           LLMBehaviour.run()                    │
├─────────────────────────────────────────────────┤
│                                                 │
│  1. Check conversation state                    │
│     ├─ Active → Continue                        │
│     └─ Inactive → Skip                          │
│                                                 │
│  2. Update context                              │
│     └─ Add message to ContextManager            │
│                                                 │
│  3. Process with LLM                            │
│     ├─ Send context to LLMProvider              │
│     └─ Receive response                         │
│                                                 │
│  4. Handle tool calls (if any)                  │
│     ├─ Execute tools                            │
│     ├─ Add results to context                   │
│     └─ Get final response from LLM              │
│                                                 │
│  5. Check termination conditions                │
│     ├─ Termination markers                      │
│     └─ Max interactions reached                 │
│                                                 │
│  6. Route response                              │
│     ├─ Apply routing function (if defined)      │
│     └─ Send to recipients                       │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Multi-Agent Communication Flow

```
┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│  Agent A │      │  Agent B │      │  Agent C │      │  Agent D │
│          │      │  (LLM)   │      │  (LLM)   │      │          │
└────┬─────┘      └────┬─────┘      └────┬─────┘      └────┬─────┘
     │                 │                 │                 │
     │    Message      │                 │                 │
     ├────────────────►│                 │                 │
     │                 │                 │                 │
     │                 ├─── Process ────►│                 │
     │                 │    with LLM     │                 │
     │                 │                 │                 │
     │                 │◄── Response ────┤                 │
     │                 │    + Routing    │                 │
     │                 │                 │                 │
     │                 │    Routed       │                 │
     │                 ├─────────────────┼────────────────►│
     │                 │    Message      │                 │
     │                 │                 │                 │
     │◄────────────────┼─────────────────┼─────────────────┤
     │    Final        │                 │    Response     │
     │    Response     │                 │                 │
     │                 │                 │                 │
```

## Installation

### Requirements

- Python 3.8+
- SPADE 3.3.0+

### Install via pip

```bash
pip install spade_llm
```

### Install from source

```bash
git clone https://github.com/sosanzma/spade_llm.git
cd spade_llm
pip install -e .
```

## Usage

### Basic Agent

```python
import spade
from spade_llm import LLMAgent
from spade_llm.providers import LLMProvider

async def main():
    # Configure provider using factory method
    provider = LLMProvider.create_openai(
        api_key="your-api-key",
        model="gpt-4o-mini"
    )
    
    # Create LLM agent
    agent = LLMAgent(
        jid="agent@xmpp-server.com",
        password="password",
        provider=provider,
        system_prompt="You are a helpful assistant"
    )
    
    await agent.start()

if __name__ == "__main__":
    spade.run(main())
```

### Using Different LLM Providers

```python
# OpenAI
provider_openai = LLMProvider.create_openai(
    api_key="your-openai-api-key",
    model="gpt-4o-mini"
)

# Ollama (local models)
provider_ollama = LLMProvider.create_ollama(
    model="llama3:8b",
    base_url="http://localhost:11434/v1",
    timeout=120.0
)

# LM Studio (local models)
provider_lm_studio = LLMProvider.create_lm_studio(
    model="mistral-7b",
    base_url="http://localhost:1234/v1"
)

```

### Agent with Tools

```python
from spade_llm import LLMAgent, LLMTool
# Define a custom tool
async def get_weather(location: str) -> str:
    # Implementation
    return f"Weather in {location}: Sunny, 22°C"

weather_tool = LLMTool(
    name="get_weather",
    description="Get current weather for a location",
    parameters={
        "type": "object",
        "properties": {
            "location": {"type": "string"}
        },
        "required": ["location"]
    },
    func=get_weather
)

# Create agent with tools
agent = LLMAgent(
    jid="agent@xmpp-server.com",
    password="password",
    provider=provider,
    tools=[weather_tool]
)
```

### LangChain Tool Integration

```python
from langchain_community.tools import DuckDuckGoSearchRun
from spade_llm.tools import LangChainToolAdapter

# Adapt LangChain tool
search_tool = LangChainToolAdapter(DuckDuckGoSearchRun())

agent = LLMAgent(
    jid="agent@xmpp-server.com",
    password="password",
    provider=provider,
    tools=[search_tool]
)
```

### MCP Server Integration

```python
from spade_llm.mcp import StdioServerConfig

# Configure MCP server
mcp_server = StdioServerConfig(
    name="CustomService",
    command="python",
    args=["path/to/mcp_server.py"],
    cache_tools=True
)

agent = LLMAgent(
    jid="agent@xmpp-server.com",
    password="password",
    provider=provider,
    mcp_servers=[mcp_server]
)
```

### Routing and Multi-Agent Communication

```python
from spade_llm import RoutingFunction, RoutingResponse

def custom_router(msg, response, context):
    if "urgent" in response.lower():
        return RoutingResponse(
            recipients="urgent-handler@server.com",
            metadata={"priority": "high"}
        )
    return "default-handler@server.com"

agent = LLMAgent(
    jid="router@server.com",
    password="password",
    provider=provider,
    routing_function=custom_router
)
```

## Features

### Context Management

- Automatic conversation tracking
- Multi-conversation support
- Context windowing for token limits
- Tool result integration

### Tool System

- Native tool definition
- LangChain adapter
- MCP tool discovery
- Asynchronous execution

### Conversation Lifecycle

- Termination markers
- Interaction limits
- Conversation state tracking
- Callback support

### Provider Abstraction

- Unified interface for LLM providers (OpenAI, Ollama, LM Studio, vLLM)
- Named factory methods for provider creation
- Tool format translation
- Response handling

## Supported LLM Providers

SPADE_LLM supports multiple LLM providers through a unified interface:

- **OpenAI**: API access to GPT models
- **Ollama**: Run local models like Llama, Mistral, Gemma, etc.
- **LM Studio**: GUI tool for running local models
- **vLLM**: High-performance inference engine

## Examples

The `examples/` directory contains several demonstrations:

- `multi_provider_chat_example.py`: Using different LLM providers
- `langchain_tools_example.py`: LangChain tool integration
- `ollama_with_tools_example.py`: Using tools with Ollama models
- `spanish_to_english_translator.py`: Simple translation agent
- `valencia_smartCity_mcp_example.py`: MCP server integration
- `document_workflow_example.py`: Multi-agent workflow

## License

MIT License

## Contributing

Contributions are welcome. Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## Support

For issues and questions:

- GitHub Issues: [Report bugs or request features]
- Documentation: [Extended documentation and examples]
- SPADE Documentation: [SPADE framework documentation]
