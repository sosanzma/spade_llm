# Your First Agent

Step-by-step tutorial for creating a complete LLM-powered agent.

## Prerequisites

- SPADE_LLM installed
- OpenAI API key or local model running
- XMPP server access

## Step 1: Basic Agent

Create `my_agent.py`:

```python
import spade
from spade_llm import LLMAgent, LLMProvider

async def main():
    # Configure LLM provider
    provider = LLMProvider.create_openai(
        api_key="your-api-key",
        model="gpt-4o-mini",
        temperature=0.7
    )
    
    # Create agent
    agent = LLMAgent(
        jid="myagent@jabber.at", 
        password="mypassword",
        provider=provider,
        system_prompt="You are a helpful coding assistant"
    )
    
    await agent.start()
    print("Agent started successfully!")
    
    # Keep running
    import asyncio
    await asyncio.sleep(60)
    
    await agent.stop()
    print("Agent stopped")

if __name__ == "__main__":
    spade.run(main())
```

Run with: `python my_agent.py`

## Step 2: Add Tools

Add function calling capabilities:

```python
from spade_llm import LLMTool
from datetime import datetime

# Define tool function
async def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Create tool
time_tool = LLMTool(
    name="get_current_time",
    description="Get current date and time",
    parameters={"type": "object", "properties": {}, "required": []},
    func=get_current_time
)

# Add to agent
agent = LLMAgent(
    jid="myagent@jabber.at",
    password="mypassword", 
    provider=provider,
    system_prompt="You are a helpful assistant with access to time information",
    tools=[time_tool]  # Add tools here
)
```

## Step 3: Interactive Chat

Create interactive chat interface:

```python
from spade_llm import ChatAgent

async def main():
    # LLM Agent
    llm_agent = LLMAgent(
        jid="assistant@jabber.at",
        password="password1",
        provider=provider,
        system_prompt="You are a helpful assistant"
    )
    
    # Chat Agent for human interaction
    chat_agent = ChatAgent(
        jid="human@jabber.at",
        password="password2", 
        target_agent_jid="assistant@jabber.at"
    )
    
    await llm_agent.start()
    await chat_agent.start()
    
    print("Chat system ready! Type messages below.")
    print("Type 'exit' to quit.")
    
    # Start interactive chat
    await chat_agent.run_interactive()
    
    await chat_agent.stop()
    await llm_agent.stop()

if __name__ == "__main__":
    spade.run(main())
```

## Step 4: Conversation Management

Add conversation limits and callbacks:

```python
def on_conversation_end(conversation_id: str, reason: str):
    print(f"Conversation {conversation_id} ended: {reason}")

agent = LLMAgent(
    jid="assistant@jabber.at",
    password="password",
    provider=provider,
    system_prompt="You are a helpful assistant",
    max_interactions_per_conversation=10,
    termination_markers=["<DONE>", "goodbye"],
    on_conversation_end=on_conversation_end
)
```

## Step 5: Message Routing

Route responses to different recipients:

```python
def my_router(msg, response, context):
    """Route based on response content."""
    if "technical" in response.lower():
        return "tech-support@jabber.at"
    elif "sales" in response.lower():
        return "sales@jabber.at"
    else:
        return str(msg.sender)  # Reply to sender

agent = LLMAgent(
    jid="router@jabber.at",
    password="password",
    provider=provider,
    routing_function=my_router
)
```

## Complete Example

Here's a full-featured agent combining all concepts:

```python
import spade
from spade_llm import LLMAgent, ChatAgent, LLMProvider, LLMTool
from datetime import datetime

# Tool function
async def get_time() -> str:
    """Get current time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Routing function
def smart_router(msg, response, context):
    """Route based on content."""
    if "time" in response.lower():
        return "time-service@jabber.at"
    return str(msg.sender)

# Conversation callback
def on_end(conv_id: str, reason: str):
    print(f"Conversation ended: {conv_id} ({reason})")

async def main():
    # Create provider
    provider = LLMProvider.create_openai(
        api_key="your-api-key",
        model="gpt-4o-mini"
    )
    
    # Create tool
    time_tool = LLMTool(
        name="get_time",
        description="Get current time",
        parameters={"type": "object", "properties": {}, "required": []},
        func=get_time
    )
    
    # Create LLM agent
    llm_agent = LLMAgent(
        jid="smart-assistant@jabber.at",
        password="password1",
        provider=provider,
        system_prompt="You are a smart assistant with time access",
        tools=[time_tool],
        routing_function=smart_router,
        max_interactions_per_conversation=20,
        on_conversation_end=on_end
    )
    
    # Create chat agent
    chat_agent = ChatAgent(
        jid="human@jabber.at",
        password="password2",
        target_agent_jid="smart-assistant@jabber.at"
    )
    
    # Start agents
    await llm_agent.start()
    await chat_agent.start()
    
    print("Smart assistant ready!")
    print("Try asking: 'What time is it?' or 'Help me with Python'")
    
    # Interactive chat
    await chat_agent.run_interactive()
    
    # Cleanup
    await chat_agent.stop()
    await llm_agent.stop()

if __name__ == "__main__":
    spade.run(main())
```

## Testing Your Agent

1. **Run the agent**: `python my_agent.py`
2. **Send test messages** using an XMPP client
3. **Check agent responses** and tool execution
4. **Monitor conversation limits** and termination

## Troubleshooting

**Agent won't start**:
- Check XMPP credentials
- Verify server connectivity
- Try `verify_security=False` for development

**No LLM responses**:
- Verify API key
- Check provider configuration
- Test with simple queries first

**Tools not working**:
- Ensure tool functions are async
- Check parameter schema
- Verify tool registration

## Next Steps

- **[Tools System](../guides/tools-system/)** - Advanced tool development
- **[Message Routing](../guides/routing/)** - Complex routing patterns
- **[Examples](../reference/examples/)** - More complete examples
- **[API Reference](../reference/)** - Detailed documentation
