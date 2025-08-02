# Human-in-the-Loop Architecture Implementation

## Overview

This document details the implementation of the Human-in-the-Loop system in SPADE_LLM, including architectural decisions, component interactions, workflow design, and technical challenges resolved during development.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Component Design](#component-design)
3. [Workflow Implementation](#workflow-implementation)
4. [Message Template System](#message-template-system)
5. [Technical Challenges and Solutions](#technical-challenges-and-solutions)
6. [Code Changes Summary](#code-changes-summary)
7. [Testing and Validation](#testing-and-validation)

## System Architecture

### High-Level Overview

The Human-in-the-Loop system enables LLM agents to consult with human experts during their reasoning process through XMPP messaging. The architecture consists of several interconnected components:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   ChatAgent     │    │    LLMAgent      │    │ Human Expert    │
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │SendBehaviour│ │────┤ │LLMBehaviour  │ │    │ │ Web Client  │ │
│ │RecvBehaviour│ │    │ │              │ │    │ │ (Browser)   │ │
│ └─────────────┘ │    │ │ ┌──────────┐ │ │    │ └─────────────┘ │
└─────────────────┘    │ │ │HiL Tool  │ │ │    └─────────────────┘
                       │ │ └──────────┘ │ │             │
                       │ └──────────────┘ │             │
                       └──────────────────┘             │
                                │                       │
                                │    XMPP Messages      │
                                └───────────────────────┘
                                        │
                       ┌─────────────────┴─────────────────┐
                       │        OpenFire XMPP Server      │
                       │                                   │
                       │ ┌─────────────┐ ┌─────────────┐   │
                       │ │  WebSocket  │ │ XMPP Client │   │
                       │ │   Gateway   │ │  Interface  │   │
                       │ └─────────────┘ └─────────────┘   │
                       └───────────────────────────────────┘
```

### Core Components

#### 1. HumanInTheLoopTool (`spade_llm/tools/human_in_the_loop.py`)

**Purpose**: LLM tool that enables agents to ask questions to human experts.

**Key Features**:
- Schema-based parameter validation for LLM interactions
- Dynamic behaviour creation for each human consultation
- Timeout management with configurable duration
- Automatic agent binding and lifecycle management

**Implementation Details**:
```python
class HumanInTheLoopTool(LLMTool):
    def __init__(self, human_expert_jid: str, timeout: float = 300.0, ...):
        # Tool configuration and schema definition
        
    async def _ask_human(self, question: str, context: Optional[str] = None) -> str:
        # Creates HumanInteractionBehaviour
        # Manages behaviour lifecycle
        # Handles timeouts and errors
```

#### 2. HumanInteractionBehaviour (`spade_llm/behaviour/human_interaction.py`)

**Purpose**: OneShotBehaviour that handles individual human consultations.

**Architecture Pattern**: Dynamic Behaviour Creation
- Created on-demand for each human consultation
- Uses XMPP thread IDs for message correlation
- Implements defensive programming for agent connectivity

**Key Features**:
- UUID-based query correlation
- Defensive agent connection handling
- Configurable timeout support
- Structured message formatting

**Lifecycle**:
1. **Initialization**: Sets up query parameters and generates unique query ID
2. **Execution**: Sends formatted question to human expert via XMPP
3. **Waiting**: Blocks on `receive()` with timeout for human response
4. **Completion**: Returns response to tool or handles timeout/errors

#### 3. Web Interface (`spade_llm/human_interface/`)

**Components**:
- **WebSocket Server** (`web_server.py`): XMPP gateway for web clients
- **Web Client** (`web_client/`): Browser-based interface for human experts

**Technical Implementation**:
- WebSocket to XMPP protocol translation
- Real-time message delivery and response handling
- XMPP.js library integration for browser compatibility

## Component Design

### Tool Integration Pattern

The Human-in-the-Loop tool follows the standard SPADE_LLM tool pattern:

```python
# LLM can call this tool during reasoning
{
    "name": "ask_human_expert",
    "description": "Ask a human expert for help when you need clarification...",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "The specific question..."},
            "context": {"type": "string", "description": "Additional context..."}
        },
        "required": ["question"]
    }
}
```

### Dynamic Behaviour Architecture

Unlike static behaviours that are added during agent setup, the HumanInteractionBehaviour is created dynamically:

**Traditional Pattern** (ChatAgent, LLMAgent):
```python
# Setup phase - behaviours added once
async def setup(self):
    behaviour = SomeBehaviour()
    self.add_behaviour(behaviour)
```

**Dynamic Pattern** (HumanInTheLoopTool):
```python
# Runtime - behaviour created per interaction
async def _ask_human(self, question: str, context: str = None):
    interaction = HumanInteractionBehaviour(...)  # New instance
    self._agent.add_behaviour(interaction)        # Add dynamically
    await interaction.join(timeout=self.timeout)  # Wait for completion
```

### Message Correlation Strategy

**Problem**: How to match human responses to specific questions in a multi-conversation environment.

**Solution**: XMPP Thread-based Correlation
- Each query gets a unique 8-character UUID: `str(uuid.uuid4())[:8]`
- XMPP `thread` field used for correlation: `msg.thread = self.query_id`
- Human responses inherit the thread ID automatically
- Behaviour waits only for messages with matching thread

### Agent Binding Pattern

**Challenge**: Tools need access to the agent that owns them for XMPP operations.

**Solution**: Automatic Agent Binding
```python
class HumanInTheLoopTool(LLMTool):
    def set_agent(self, agent: Agent):
        """Called automatically when tool is added to agent"""
        self._agent = agent
        
# In LLMAgent._register_tool():
if hasattr(tool, 'set_agent') and callable(getattr(tool, 'set_agent')):
    tool.set_agent(self)
```

## Workflow Implementation

### End-to-End Flow

1. **Tool Invocation**
   ```
   LLM decides it needs human input
   ↓
   Calls ask_human_expert(question="...", context="...")
   ↓
   HumanInTheLoopTool._ask_human() executed
   ```

2. **Behaviour Creation**
   ```
   Create HumanInteractionBehaviour instance
   ↓
   Add to agent with query_id and timeout
   ↓
   Start behaviour execution
   ```

3. **Question Transmission**
   ```
   Format question with context and instructions
   ↓
   Create XMPP Message with thread=query_id
   ↓
   Send to human expert JID
   ```

4. **Human Response Workflow**
   ```
   Human Expert receives message via WebSocket
   ↓
   Reviews question and context in web interface
   ↓
   Types response and sends via web client
   ↓
   WebSocket server forwards to XMPP
   ↓
   Message delivered with same thread ID
   ```

5. **Response Processing**
   ```
   HumanInteractionBehaviour receives response
   ↓
   Matches thread ID to correlation query
   ↓
   Stores response in behaviour.response
   ↓
   Behaviour completes
   ```

6. **Tool Completion**
   ```
   HumanInTheLoopTool checks behaviour.response
   ↓
   Returns human response to LLM
   ↓
   LLM continues reasoning with human input
   ```

### Timeout Handling

**Architecture**: Nested Timeout Design
- **Tool Level**: `HumanInTheLoopTool.timeout` (default: 300s)
- **Behaviour Level**: `HumanInteractionBehaviour.timeout` (passed from tool)
- **Join Level**: `await interaction.join(timeout=self.timeout)`
- **Receive Level**: `await self.receive(timeout=self.timeout)`

**Implementation**:
```python
# Tool creates behaviour with timeout
interaction = HumanInteractionBehaviour(
    human_jid=self.human_jid,
    question=question,
    context=context,
    timeout=self.timeout  # Pass tool timeout to behaviour
)

# Tool waits for behaviour completion
await interaction.join(timeout=self.timeout)

# Behaviour waits for human response
response_msg = await self.receive(timeout=self.timeout)
```

### Error Handling Strategy

**Connection Errors**:
- Defensive checks for `agent.client` availability
- Graceful handling of XMPP send failures
- Continuation of workflow even if send() raises exceptions

**Timeout Scenarios**:
- Behaviour-level timeout via `receive(timeout=...)`
- Tool-level timeout via `join(timeout=...)`
- Automatic behaviour cleanup on timeout

**Exception Propagation**:
```python
try:
    await interaction.join(timeout=self.timeout)
    return interaction.response or "No response received"
except TimeoutError:
    self._agent.remove_behaviour(interaction)  # Cleanup
    return "Timeout: Human expert did not respond..."
except Exception as e:
    # Clean up and return error message
    return f"Error consulting human expert: {str(e)}"
```

## Message Template System

### Problem Statement

Before implementing templates, the LLMBehaviour was receiving ALL XMPP messages, including:
- Messages intended for LLM processing (from ChatAgent, other LLMAgents)
- Human expert responses (intended only for HumanInteractionBehaviour)

This caused **double processing** where human responses were:
1. Correctly processed by HumanInteractionBehaviour (as tool responses)
2. Incorrectly processed by LLMBehaviour (as new user messages)

### Solution: Template-Based Message Filtering

**Implementation Strategy**: Use SPADE's Template system to ensure each behaviour only receives intended messages.

#### Template Assignment Pattern

**LLMBehaviour Template**:
```python
# In LLMAgent.setup()
template = Template()
template.set_metadata("message_type", "llm")
self.add_behaviour(self.llm_behaviour, template)
```

**HumanInteractionBehaviour Template**:
```python
# No template - receives all messages
# This allows it to receive human expert responses
self.add_behaviour(interaction)  # No template parameter
```

#### Message Marking Strategy

**ChatAgent Messages** (targeting LLM agents):
```python
msg = Message(to=target_jid)
msg.body = message_to_send
msg.set_metadata("message_type", "llm")  # Mark for LLM processing
```

**LLMBehaviour Responses** (to other agents):
```python
reply = Message(to=recipient)
reply.body = response
reply.set_metadata("message_type", "llm")  # Mark for LLM processing
```

**HumanInteractionBehaviour Messages** (to humans):
```python
msg = Message(to=self.human_jid)
msg.body = self._format_question()
# No message_type metadata - this is for human experts
```

### Message Flow with Templates

```
ChatAgent ──["message_type"="llm"]──> LLMBehaviour ✓
                                     HumanInteractionBehaviour ✗

LLMAgent ──["message_type"="llm"]──> LLMBehaviour ✓
                                    HumanInteractionBehaviour ✗

Human Expert ──[no metadata]──> LLMBehaviour ✗
                                HumanInteractionBehaviour ✓
```

### Template Architecture Benefits

1. **Automatic Filtering**: SPADE handles message routing at the framework level
2. **Performance**: No manual message inspection in behaviour code
3. **Scalability**: Easy to add new message types and behaviours
4. **Separation of Concerns**: Each behaviour only handles its intended messages
5. **Debugging**: Clear message flow paths reduce debugging complexity

## Technical Challenges and Solutions

### Challenge 1: Dynamic Behaviour Connectivity

**Problem**: Dynamically added behaviours sometimes encountered `TypeError: object NoneType can't be used in 'await' expression` when trying to send messages.

**Root Cause**: `agent.client` was `None` when dynamic behaviours executed immediately after being added.

**Solution**: Defensive programming with connection verification:
```python
# Wait for agent connection if possible
if hasattr(self.agent, 'connected_event'):
    try:
        await self.agent.connected_event.wait()
    except Exception as e:
        logger.warning(f"Could not wait for agent connection: {e}")

# Defensive check
if not self.agent or not self.agent.client:
    logger.error(f"Agent XMPP client not available")
    return
```

### Challenge 2: Receive Without Timeout

**Problem**: Using `await self.receive()` without timeout caused immediate return with `None` because SPADE internally uses `queue.get_nowait()`.

**Root Cause**: SPADE's `receive()` method implementation:
```python
# SPADE internal code
def receive(self, timeout=None):
    if timeout:
        return await asyncio.wait_for(self.queue.get(), timeout)
    else:
        return self.queue.get_nowait()  # Returns None immediately if no message
```

**Solution**: Always specify timeout for blocking receive:
```python
# Before (incorrect)
response_msg = await self.receive()  # Returns None immediately

# After (correct)
response_msg = await self.receive(timeout=self.timeout)  # Blocks until message or timeout
```

### Challenge 3: Double Message Processing

**Problem**: Human expert responses were being processed twice - once by HumanInteractionBehaviour (correct) and once by LLMBehaviour (incorrect).

**Root Cause**: Both behaviours were receiving all XMPP messages.

**Solution**: Template-based message filtering (detailed in Message Template System section).

### Challenge 4: Timeout Architecture Redundancy

**Problem**: Original implementation had redundant timeouts:
- `join(timeout=300.0)` at tool level
- `receive(timeout=300.0)` at behaviour level

**Solution**: Dynamic timeout passing:
```python
# Tool passes its timeout to behaviour
interaction = HumanInteractionBehaviour(
    timeout=self.timeout  # Dynamic timeout from tool
)

# Behaviour uses passed timeout
response_msg = await self.receive(timeout=self.timeout)
```

## Code Changes Summary

### New Files Created

1. **`spade_llm/tools/human_in_the_loop.py`**
   - HumanInTheLoopTool implementation
   - Agent binding mechanism
   - Timeout and error handling

2. **`spade_llm/behaviour/human_interaction.py`**
   - HumanInteractionBehaviour implementation
   - XMPP message correlation
   - Dynamic timeout support

3. **`examples/human_in_the_loop_example.py`**
   - Complete working example
   - Integration demonstration
   - Best practices showcase

### Modified Files

#### `spade_llm/agent/llm_agent.py`
- Added template-based behaviour registration
- Enhanced tool binding for HumanInTheLoopTool
- Template creation with `message_type: "llm"`

#### `spade_llm/agent/chat_agent.py`
- Added `message_type: "llm"` metadata to outgoing messages
- Both `SendBehaviour` and `send_message_async()` updated

#### `spade_llm/behaviour/llm_behaviour.py`
- Added Template import
- Enhanced message filtering through templates
- Added `message_type: "llm"` to outgoing responses

#### `spade_llm/human_interface/web_client/index.html`
- Updated WebSocket URL to match OpenFire configuration
- Added fallback CDN loading for XMPP.js library

### Configuration Changes

#### Example Configuration Updates
- Fixed JID format (added missing `@` symbols)
- Updated XMPP server configuration
- Changed from `asyncio.run()` to `spade.run()`

## Testing and Validation

### Test Scenarios

1. **Basic Functionality**
   - LLM agent asks question to human expert
   - Human provides response via web interface
   - LLM receives response and continues reasoning

2. **Timeout Handling**
   - No human response within timeout period
   - Graceful degradation with timeout message
   - Proper behaviour cleanup

3. **Concurrent Consultations**
   - Multiple simultaneous human consultations
   - Proper message correlation via thread IDs
   - No cross-contamination between consultations

4. **Error Scenarios**
   - Human expert offline
   - Network connectivity issues
   - Invalid JID configurations

### Validation Criteria

✅ **Message Isolation**: Human expert responses only processed by HumanInteractionBehaviour
✅ **Template Filtering**: LLMBehaviour only receives `message_type: "llm"` messages  
✅ **Timeout Management**: Configurable timeouts work at both tool and behaviour levels
✅ **Correlation**: Multiple concurrent consultations don't interfere with each other
✅ **Error Handling**: Graceful handling of connection and timeout errors
✅ **Integration**: Works seamlessly with existing ChatAgent and LLMAgent architecture

## Future Enhancements

### Potential Improvements

1. **Response Quality Metrics**
   - Track response times
   - Human expert availability indicators
   - Response quality feedback loops

2. **Multi-Human Consultation**
   - Route questions to multiple experts
   - Aggregate responses
   - Expert specialization routing

3. **Persistent Human Context**
   - Maintain conversation history with human experts
   - Context-aware follow-up questions
   - Human expert session management

4. **Advanced Templates**
   - Priority-based message routing
   - Role-based access control
   - Message type hierarchies

### Architectural Considerations

- **Scalability**: Current design supports concurrent consultations but may need optimization for high-volume scenarios
- **Security**: Add authentication and authorization for human expert access
- **Monitoring**: Implement metrics and logging for human consultation patterns
- **Fallback Strategies**: Implement fallback mechanisms when human experts are unavailable

## Conclusion

The Human-in-the-Loop implementation provides a robust, scalable foundation for human-AI collaboration in SPADE_LLM. The template-based message filtering system ensures clean separation of concerns, while the dynamic behaviour pattern allows for flexible, on-demand human consultations.

Key architectural decisions:
- **Template-based filtering** for message isolation
- **Dynamic behaviour creation** for per-consultation lifecycle management  
- **Thread-based correlation** for multi-conversation support
- **Defensive programming** for robust error handling
- **Configurable timeouts** for flexible deployment scenarios

The implementation successfully addresses the core requirements while maintaining compatibility with existing SPADE_LLM architecture and providing a foundation for future enhancements.