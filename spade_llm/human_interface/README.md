# Human Expert Web Interface

This web interface allows human experts to receive and respond to queries from SPADE LLM agents through a browser.

## ⚠️ Important: This is NOT a Java application

This is a **web-based JavaScript application** that runs in your browser. No Java installation is required.

## How it works

1. **Python Web Server**: A simple HTTP server (written in Python) serves the web files
2. **JavaScript Client**: The browser runs JavaScript code that connects to your XMPP server
3. **XMPP Communication**: Uses the xmpp.js library (loaded from CDN) to communicate

## Features

- 🌐 Web-based interface (no installation required)
- 🔐 Secure XMPP connection via WebSocket
- 💬 Real-time message reception
- 🔔 Browser notifications for new queries
- 📝 Context-aware query display
- ✅ Query status tracking
- 🔍 Debug logging (in development mode)

## Quick Start

### 1. Start the Web Server

```bash
# From the project root
python -m spade_llm.human_interface.web_server

# Or specify a custom port
python -m spade_llm.human_interface.web_server 8888
```

The server will start on `http://localhost:8080` by default.

### 2. Open the Interface

Navigate to `http://localhost:8080` in your web browser.

### 3. Connect to XMPP Server

Fill in the connection form:

- **WebSocket Service URL**: The XMPP WebSocket endpoint (e.g., `ws://localhost:5280/xmpp-websocket`)
- **Expert JID**: Your XMPP account (e.g., `expert@xmpp.server`)
- **Password**: Your XMPP password

### 4. Respond to Queries

Once connected, you'll see incoming queries from agents. Each query shows:

- Query ID
- Sender (agent JID)
- Question
- Context (if provided)
- Timestamp

Type your response and click "Send Response" or press Enter.

## Usage in SPADE LLM

To use this interface with your agents:

```python
from spade_llm import LLMAgent, HumanInTheLoopTool
from spade_llm.providers import OpenAIProvider

# Create the agent
agent = LLMAgent(
    jid="assistant@xmpp.server",
    password="password",
    provider=OpenAIProvider(api_key="..."),
)

# Create the human-in-the-loop tool
human_tool = HumanInTheLoopTool(
    agent=agent,
    human_expert_jid="expert@xmpp.server",  # Same JID used in web interface
    timeout=300.0,  # 5 minutes
)

# Add the tool to the agent
agent.add_tool(human_tool)
```

## Requirements

- Modern web browser (Chrome, Firefox, Safari, Edge)
- XMPP server with WebSocket support
- Valid XMPP account for the human expert

## Security Notes

- Use `wss://` (secure WebSocket) in production
- The interface uses XMPP authentication
- No data is stored on the server - all communication is real-time

## Troubleshooting

### Connection Issues

1. Verify the XMPP server is running
2. Check WebSocket endpoint is accessible
3. Confirm credentials are correct
4. Look at browser console for errors (F12)

### Message Format

The interface expects messages in this format:
```
[Query ID] Question
Context: Additional context
(Please reply to this message to provide your answer)
```

Messages with different formats will still be displayed but may not parse correctly.

## Development

To modify the interface:

1. Edit files in `spade_llm/human_interface/web_client/`
2. Refresh the browser to see changes
3. No build process required - vanilla JavaScript

The debug panel is automatically shown when accessing from `localhost`.
