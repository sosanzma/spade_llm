# Your First LLM Agent

In this tutorial, you'll learn how to create your first SPADE-LLM agent step by step. We'll start with a basic setup and gradually add features to understand the core concepts.

## Prerequisites

Before starting, ensure you have:
- Python 3.10 or higher installed
- SPADE-LLM installed (`pip install spade_llm`)
- An XMPP server running (for local testing, you can use [Prosody](https://prosody.im/))
- Access to at least one LLM provider (OpenAI API key or local Ollama installation)

## Step 1: Basic Agent Setup

Let's start with the simplest possible SPADE-LLM agent. Create `my_first_agent.py`:

```python
import spade
from spade_llm import LLMAgent, LLMProvider

async def main():
    # Create an LLM provider
    provider = LLMProvider.create_openai(
        api_key="your-api-key-here",
        model="gpt-4o-mini",
        temperature=0.7
    )
    
    # Create the LLM agent
    agent = LLMAgent(
        jid="assistant@localhost",
        password="password123",
        provider=provider,
        system_prompt="You are a helpful assistant."
    )
    
    # Start the agent
    await agent.start()
    print("✅ Agent started successfully!")
    
    # Keep the agent running
    await agent.wait_until_finished()

if __name__ == "__main__":
    spade.run(main())
```

### Understanding the Components

**LLMProvider**: Your interface to different LLM services. SPADE-LLM supports multiple providers:

```python
# OpenAI
provider = LLMProvider.create_openai(
    api_key="your-api-key",
    model="gpt-4o-mini"
)

# Ollama (local)
provider = LLMProvider.create_ollama(
    model="llama3.1:8b",
    base_url="http://localhost:11434/v1"
)

# LM Studio (local)
provider = LLMProvider.create_lm_studio(
    model="local-model",
    base_url="http://localhost:1234/v1"
)
```

**LLMAgent**: The core component that connects to XMPP, receives messages, processes them through the LLM, and sends responses back.

Run with: `python my_first_agent.py`

## Step 2: Creating an Interactive Chat

To make your agent interactive, you'll need a `ChatAgent` to handle user input. Create `interactive_agent.py`:

```python
import spade
import getpass
from spade_llm import LLMAgent, ChatAgent, LLMProvider

async def main():
    # Get XMPP server details
    xmpp_server = input("Enter XMPP server domain (e.g., localhost): ") or "localhost"
    
    # Create LLM provider
    provider = LLMProvider.create_openai(
        api_key="your-api-key",
        model="gpt-4o-mini"
    )
    
    # Create the LLM agent
    llm_agent = LLMAgent(
        jid=f"assistant@{xmpp_server}",
        password=getpass.getpass("LLM agent password: "),
        provider=provider,
        system_prompt="You are a helpful assistant. Keep responses concise and friendly."
    )
    
    # Create the chat agent for user interaction
    chat_agent = ChatAgent(
        jid=f"user@{xmpp_server}",
        password=getpass.getpass("Chat agent password: "),
        target_agent_jid=f"assistant@{xmpp_server}"
    )
    
    try:
        # Start both agents
        await llm_agent.start()
        await chat_agent.start()
        
        print("✅ Agents started successfully!")
        print("💬 You can now chat with your AI assistant")
        print("Type 'exit' to quit\n")
        
        # Run interactive chat
        await chat_agent.run_interactive()
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    finally:
        # Clean up
        await chat_agent.stop()
        await llm_agent.stop()
        print("✅ Agents stopped successfully!")

if __name__ == "__main__":
    spade.run(main())
```

### Adding Custom Display

You can customize how responses are displayed:

```python
def display_response(message: str, sender: str):
    print(f"\n🤖 Assistant: {message}")
    print("-" * 50)

def on_message_sent(message: str, recipient: str):
    print(f"👤 You: {message}")

chat_agent = ChatAgent(
    jid=f"user@{xmpp_server}",
    password=chat_password,
    target_agent_jid=f"assistant@{xmpp_server}",
    display_callback=display_response,
    on_message_sent=on_message_sent
)
```

## Step 3: Adding Error Handling

Always include proper error handling in production code:

```python
import spade
import logging
from spade_llm import LLMAgent, ChatAgent, LLMProvider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    try:
        # Create provider with error handling
        provider = LLMProvider.create_openai(
            api_key="your-api-key",
            model="gpt-4o-mini",
            timeout=30.0  # Set timeout
        )
        
        # Create agents with error handling
        llm_agent = LLMAgent(
            jid="assistant@localhost",
            password="password123",
            provider=provider,
            system_prompt="You are a helpful assistant.",
            verify_security=False  # For testing only
        )
        
        await llm_agent.start()
        logger.info("✅ LLM Agent started successfully")
        
        # Your chat logic here...
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        print("💡 Check your configuration and try again")
    finally:
        # Always clean up
        if 'llm_agent' in locals():
            await llm_agent.stop()
        if 'chat_agent' in locals():
            await chat_agent.stop()

if __name__ == "__main__":
    spade.run(main())
```

## Complete Example with Best Practices

Here's a complete, production-ready example that demonstrates best practices:

```python
import spade
import getpass
import logging
from spade_llm import LLMAgent, ChatAgent, LLMProvider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    print("🚀 Starting your first SPADE-LLM agent!")
    
    # Configuration
    xmpp_server = input("XMPP server domain (default: localhost): ") or "localhost"
    
    # Create provider (choose one)
    provider_type = input("Provider (openai/ollama): ").lower()
    
    if provider_type == "openai":
        api_key = getpass.getpass("OpenAI API key: ")
        provider = LLMProvider.create_openai(
            api_key=api_key,
            model="gpt-4o-mini",
            timeout=30.0
        )
    else:  # ollama
        model = input("Ollama model (default: llama3.1:8b): ") or "llama3.1:8b"
        provider = LLMProvider.create_ollama(
            model=model,
            base_url="http://localhost:11434/v1",
            timeout=60.0
        )
    
    # Get passwords
    llm_password = getpass.getpass("LLM agent password: ")
    chat_password = getpass.getpass("Chat agent password: ")
    
    # Create agents
    llm_agent = LLMAgent(
        jid=f"assistant@{xmpp_server}",
        password=llm_password,
        provider=provider,
        system_prompt="You are a helpful and friendly AI assistant. Keep responses concise but informative.",
        verify_security=False  # For development only
    )
    
    def display_response(message: str, sender: str):
        print(f"\n🤖 Assistant: {message}")
        print("-" * 50)
    
    def on_message_sent(message: str, recipient: str):
        print(f"👤 You: {message}")
    
    chat_agent = ChatAgent(
        jid=f"user@{xmpp_server}",
        password=chat_password,
        target_agent_jid=f"assistant@{xmpp_server}",
        display_callback=display_response,
        on_message_sent=on_message_sent,
        verify_security=False  # For development only
    )
    
    try:
        # Start agents
        await llm_agent.start()
        await chat_agent.start()
        
        logger.info("✅ Agents started successfully!")
        print("💬 Start chatting with your AI assistant")
        print("Type 'exit' to quit\n")
        
        # Run interactive chat
        await chat_agent.run_interactive()
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        print("💡 Check your configuration and try again")
    finally:
        # Clean up
        try:
            await chat_agent.stop()
            await llm_agent.stop()
            logger.info("✅ Agents stopped successfully!")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    spade.run(main())
```

## Testing Your Agent

1. **Run the agent**: `python my_first_agent.py`
2. **Choose your provider**: OpenAI or Ollama
3. **Enter your credentials**: API key and XMPP passwords
4. **Start chatting**: Type messages and get responses

## Common Issues and Solutions

### Connection Problems
- **Agent won't start**: Check XMPP credentials and server availability
- **Authentication failed**: Verify JID format and passwords
- **Network issues**: Ensure XMPP server is accessible

### LLM Provider Issues
- **OpenAI errors**: Verify API key and account credits
- **Ollama not responding**: Check if `ollama serve` is running
- **Timeout errors**: Increase timeout values for slow models

### Performance Tips
- Use appropriate model sizes for your hardware
- Set reasonable timeouts based on your provider
- Monitor token usage for cost optimization
- Use local models (Ollama) for development

## Next Steps

Now that you have a working agent, explore these advanced features:

1. **[Custom Tools Tutorial](tools-tutorial.md)** - Add function calling capabilities
2. **[Guardrails Tutorial](guardrails-tutorial.md)** - Implement safety and content filtering  
3. **[Advanced Agent Tutorial](advanced-agent.md)** - Multi-agent workflows and integrations

Each tutorial builds on the concepts you've learned here, gradually adding more sophisticated capabilities to your agents.
