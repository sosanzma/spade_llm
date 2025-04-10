# SPADE_LLM

Extension for SPADE (Smart Python Agent Development Environment) to integrate Large Language Models in agents.

## Features

- Specialized behaviour for LLM interaction
- Context management with token awareness
- Tool-calling framework
- High-level API for creating LLM-capable agents
- Provider abstraction for different LLM services

## Installation

```bash
pip install spade_llm
```

## Basic Usage

```python
from spade_llm import LLMAgent
from spade_llm.providers import OpenAIProvider  # This will be implemented later

# Create an LLM provider
provider = OpenAIProvider(api_key="your-api-key")

# Create an agent with LLM capabilities
agent = LLMAgent(
    jid="your-agent@your-xmpp-server.org",
    password="your-password",
    provider=provider,
    system_prompt="You are a helpful assistant agent"
)

# Run the agent
await agent.start()
```

## Development Status

This project is in early development. APIs may change significantly between versions.

## License

MIT License
