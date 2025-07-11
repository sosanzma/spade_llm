# Quick Start

Get your first SPADE_LLM agent running in minutes.

## Setup

### 1. Install
```bash
pip install spade_llm
```

### 2. Get LLM Access
**OpenAI** (easiest):
```bash
export OPENAI_API_KEY="your-api-key"
```

**Ollama** (free):
```bash
ollama pull llama3.1:8b
ollama serve
```

### 3. Create Agent

```python
import spade
from spade_llm import LLMAgent, LLMProvider

async def main():
    # Configure provider
    provider = LLMProvider.create_openai(
        api_key="your-api-key",
        model="gpt-4o-mini"
    )
    
    # Create agent
    agent = LLMAgent(
        jid="assistant@jabber.at",
        password="your-password",
        provider=provider,
        system_prompt="You are a helpful assistant"
    )
    
    await agent.start()
    print("Agent started!")
    
    # Keep running
    import asyncio
    await asyncio.sleep(60)
    await agent.stop()

if __name__ == "__main__":
    spade.run(main())
```

### 4. Run
```bash
python my_agent.py
```

## Alternative Providers

### Ollama
```python
provider = LLMProvider.create_ollama(
    model="llama3.1:8b"
)
```

### LM Studio
```python
provider = LLMProvider.create_lm_studio(
    model="local-model",
    base_url="http://localhost:1234/v1"
)
```

## Chat Example

Interactive chat agent:

```python
import spade
from spade_llm import LLMAgent, ChatAgent, LLMProvider

async def main():
    # LLM Agent
    provider = LLMProvider.create_openai(
        api_key="your-key",
        model="gpt-4o-mini"
    )
    
    llm_agent = LLMAgent(
        jid="assistant@jabber.at",
        password="password1",
        provider=provider
    )
    
    # Chat Agent (for human interaction)
    chat_agent = ChatAgent(
        jid="human@jabber.at", 
        password="password2",
        target_agent_jid="assistant@jabber.at"
    )
    
    await llm_agent.start()
    await chat_agent.start()
    
    # Start interactive chat
    await chat_agent.run_interactive()
    
    await chat_agent.stop()
    await llm_agent.stop()

if __name__ == "__main__":
    spade.run(main())
```

## Next Steps

- **[First Agent Tutorial](first-agent/)** - Detailed walkthrough
- **[Providers Guide](../guides/providers/)** - LLM provider configuration
- **[Tools System](../guides/tools-system/)** - Add function calling
- **[Examples](../reference/examples/)** - Complete working examples
