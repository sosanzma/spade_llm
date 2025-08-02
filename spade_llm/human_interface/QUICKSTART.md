# Human-in-the-Loop Quick Start Guide

## Overview

The Human-in-the-Loop system allows SPADE LLM agents to consult with human experts through a web interface.

## Architecture

```
┌─────────────────────┐       XMPP        ┌──────────────────┐
│   SPADE LLM Agent   │ ◄──────────────► │  Human Expert    │
│    (Python)         │                   │  (Web Browser)   │
└─────────────────────┘                   └──────────────────┘
                                                    │
                                                    │ HTTP
                                                    ▼
                                          ┌──────────────────┐
                                          │   Web Server     │
                                          │   (Python)       │
                                          └──────────────────┘
```

## Step 1: Start the Web Server

The web server serves the HTML/JavaScript files to your browser:

```bash
# From your project directory
python -m spade_llm.human_interface.web_server

# Or specify a custom port
python -m spade_llm.human_interface.web_server 8888
```

This starts a simple HTTP server that serves the web interface files.

## Step 2: Open the Web Interface

Open your browser and navigate to:
```
http://localhost:8080
```

You'll see a login form where you need to enter:
- **WebSocket URL**: Your XMPP server's WebSocket endpoint
- **Expert JID**: The XMPP account for the human expert
- **Password**: The password for that account

## Step 3: Create Your Agent

In your Python code:

```python
from spade_llm import LLMAgent, HumanInTheLoopTool
from spade_llm.providers import OpenAIProvider

# Create the human tool FIRST
human_tool = HumanInTheLoopTool(
    human_expert_jid="expert@xmpp.server",  # Same JID as in web interface
    timeout=300.0  # 5 minutes
)

# Create the agent WITH the tool
agent = LLMAgent(
    jid="assistant@xmpp.server",
    password="password",
    provider=OpenAIProvider(api_key="..."),
    tools=[human_tool]  # Pass tools here
)

await agent.start()
```

## Step 4: How It Works

1. **User asks agent a question** → Agent receives message via XMPP
2. **Agent decides to consult human** → Uses the `ask_human_expert` tool
3. **Tool sends question to human** → Via XMPP to the web interface
4. **Human sees question in browser** → Real-time display
5. **Human types response** → In the web interface
6. **Response sent back to agent** → Via XMPP
7. **Agent uses human's answer** → To formulate final response
8. **Agent responds to user** → With combined knowledge

## Common Issues

### "Cannot connect to XMPP server"
- Verify your XMPP server is running
- Check WebSocket endpoint is enabled
- Ensure credentials are correct

### "No questions appearing"
- Verify the expert JID matches in both web interface and Python code
- Check the agent is actually calling the human tool
- Look at browser console for errors (F12)

### "Timeout waiting for human"
- Default timeout is 5 minutes
- Human must respond within this time
- Can be configured in `HumanInTheLoopTool(timeout=seconds)`

## Example Conversation Flow

```
User → Agent: "What's the WiFi password for our office?"
Agent → Human: "The user is asking: What's the WiFi password for our office?"
Human → Agent: "The WiFi password is SecureNetwork2024!"
Agent → User: "According to our expert, the WiFi password for our office is SecureNetwork2024!"
```

## Technical Details

- **Frontend**: Pure JavaScript (no build required)
- **Communication**: XMPP over WebSocket
- **Library**: xmpp.js (loaded from CDN)
- **Server**: Simple Python HTTP server
- **No Java required**: Despite XMPP, this is JavaScript, not Java
