# Memory API

API reference for agent memory and learning capabilities.

## AgentInteractionMemory

Manages agent interaction memory with persistent storage.

### Constructor

```python
AgentInteractionMemory(
    agent_id: str,
    storage_dir: Optional[str] = None
)
```

**Parameters:**
- `agent_id` (str): Unique identifier for the agent
- `storage_dir` (str, optional): Custom storage directory path

**Example:**

```python
from spade_llm.memory import AgentInteractionMemory

# Default storage location
memory = AgentInteractionMemory("agent@example.com")

# Custom storage location
memory = AgentInteractionMemory(
    agent_id="agent@example.com",
    storage_dir="/custom/memory/path"
)
```

### Methods

#### add_information()

```python
def add_information(
    self, 
    conversation_id: str, 
    information: str
) -> str
```

Add information to conversation memory.

**Parameters:**
- `conversation_id` (str): Unique conversation identifier
- `information` (str): Information to store

**Returns:**
- `str`: Confirmation message

**Example:**

```python
memory.add_information(
    "user1_session",
    "User prefers JSON responses over XML"
)
```

#### get_information()

```python
def get_information(
    self, 
    conversation_id: str
) -> List[str]
```

Get stored information for a conversation.

**Parameters:**
- `conversation_id` (str): Conversation identifier

**Returns:**
- `List[str]`: List of stored information strings

**Example:**

```python
info_list = memory.get_information("user1_session")
# Returns: ["User prefers JSON responses", "API token: abc123"]
```

#### get_context_summary()

```python
def get_context_summary(
    self, 
    conversation_id: str
) -> Optional[str]
```

Get formatted summary of conversation memory.

**Parameters:**
- `conversation_id` (str): Conversation identifier

**Returns:**
- `Optional[str]`: Formatted summary string or None if no memory

**Example:**

```python
summary = memory.get_context_summary("user1_session")
# Returns: "Previous interactions:\n- User prefers JSON responses\n- API token: abc123"
```

#### clear_conversation()

```python
def clear_conversation(
    self, 
    conversation_id: str
) -> bool
```

Clear memory for a specific conversation.

**Parameters:**
- `conversation_id` (str): Conversation identifier

**Returns:**
- `bool`: True if successful, False otherwise

**Example:**

```python
success = memory.clear_conversation("user1_session")
```

#### get_all_conversations()

```python
def get_all_conversations(self) -> List[str]
```

Get list of all conversation IDs with stored memory.

**Returns:**
- `List[str]`: List of conversation IDs

**Example:**

```python
conversations = memory.get_all_conversations()
# Returns: ["user1_session", "user2_session", "api_session"]
```

### Storage Format

The memory system uses JSON file storage with the following structure:

```json
{
    "agent_id": "agent@example.com",
    "interactions": {
        "conversation_id": [
            {
                "content": "User prefers JSON responses",
                "timestamp": "2025-01-09T10:30:00.000Z"
            },
            {
                "content": "API token: db_token_123",
                "timestamp": "2025-01-09T10:35:00.000Z"
            }
        ]
    }
}
```

### Example Usage

```python
from spade_llm.memory import AgentInteractionMemory

# Create memory instance
memory = AgentInteractionMemory("support_agent@example.com")

# Store information
memory.add_information("customer_123", "Customer prefers email notifications")
memory.add_information("customer_123", "Account type: premium")

# Retrieve information
info_list = memory.get_information("customer_123")
print(info_list)  # ["Customer prefers email notifications", "Account type: premium"]

# Get formatted summary
summary = memory.get_context_summary("customer_123")
print(summary)
# Output: "Previous interactions:\n- Customer prefers email notifications\n- Account type: premium"

# Clear conversation memory
memory.clear_conversation("customer_123")
```

## Memory Tools

### remember_interaction_info

Tool function available to LLMs for storing information.

```python
def remember_interaction_info(information: str) -> str
```

**Parameters:**
- `information` (str): Information to store in memory

**Returns:**
- `str`: Confirmation message

**LLM Usage:**

```json
{
    "name": "remember_interaction_info",
    "description": "Store important information for future reference",
    "parameters": {
        "type": "object",
        "properties": {
            "information": {
                "type": "string",
                "description": "Important information to remember"
            }
        },
        "required": ["information"]
    }
}
```

### get_interaction_history

Tool function for retrieving stored memory.

```python
def get_interaction_history() -> str
```

**Returns:**
- `str`: Formatted history of stored interactions

**LLM Usage:**

```json
{
    "name": "get_interaction_history",
    "description": "Get previous interaction information",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
}
```

## Memory Integration

### LLMAgent Integration

Memory is integrated into `LLMAgent` via the `interaction_memory` parameter:

```python
from spade_llm.agent import LLMAgent

agent = LLMAgent(
    jid="memory_agent@example.com",
    password="password",
    provider=provider,
    interaction_memory=True,  # Enable memory
    system_prompt="You have memory capabilities."
)
```

### Conversation Threading

Memory integrates with conversation threading:

```python
# Conversation ID generation
conversation_id = msg.thread or f"{msg.sender}_{msg.to}"

# Memory is isolated per conversation
memory.add_information(conversation_id, "User session data")
```

### Context Injection

Memory is automatically injected into conversations:

```python
# System message automatically added
{
    "role": "system",
    "content": "Previous interactions:\n- User prefers JSON\n- API token: abc123"
}
```

## Memory Lifecycle

### Conversation States

Memory integrates with conversation state management:

```python
# Conversation states
class ConversationState:
    ACTIVE = "active"
    COMPLETED = "completed"
    ERROR = "error"
    TIMEOUT = "timeout"
    MAX_INTERACTIONS_REACHED = "max_interactions_reached"
```

### State Tracking

```python
# Conversation state structure
{
    "conversation_id": "user1_session",
    "state": "active",
    "interaction_count": 5,
    "max_interactions": 10,
    "created_at": "2025-01-09T10:00:00Z",
    "last_interaction": "2025-01-09T10:30:00Z"
}
```



## Performance Considerations

### File System Limits

- **File Size**: JSON files grow with conversation length
- **I/O Operations**: Each operation requires file read/write
- **Concurrency**: Multiple agents may cause file contention

