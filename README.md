# SPADE_LLM

Extension for SPADE (Smart Python Agent Development Environment) to integrate Large Language Models in agents.

## Features

- Specialized behaviour for LLM interaction
- Tool-calling framework
- Provider abstraction for different LLM services



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



## License

MIT License
