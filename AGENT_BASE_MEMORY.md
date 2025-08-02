# Agent Base Memory

Agent Base Memory is a new feature in SPADE_LLM that enables agents to store and retrieve long-term memories across conversations, allowing them to learn and improve over time.

## Overview

Unlike the existing Interaction Memory (which stores conversation-specific information), Agent Base Memory provides persistent storage for agent-level knowledge that spans multiple conversations and persists across agent restarts.

## Key Features

- **Zero Configuration**: Enable with just `agent_base_memory=True`
- **Automatic Tool Registration**: Memory tools are automatically available to the LLM
- **Flexible Storage**: Choose between persistent file-based or temporary in-memory storage
- **Categorized Storage**: Organize memories by type (fact, pattern, preference, capability)
- **Extensible Backend**: Easy to add new storage backends (PostgreSQL, ChromaDB, etc.)
- **Async-First**: Built with async/await patterns throughout

## Quick Start

```python
from spade_llm.agent.llm_agent import LLMAgent
from spade_llm.providers.llm_provider import LLMProvider

# Create agent with persistent memory (default)
agent = LLMAgent(
    jid="smart_agent@example.com",
    password="password",
    provider=your_provider,
    agent_base_memory=True  # This enables persistent memory!
)

# Create agent with in-memory database (temporary)
agent = LLMAgent(
    jid="test_agent@example.com",
    password="password", 
    provider=your_provider,
    agent_base_memory=(True, ":memory:")  # In-memory: deleted when agent stops!
)
```

That's it! The agent now has memory capabilities.

## Memory Categories

Agent Base Memory organizes information into four categories:

- **`fact`**: Concrete information (APIs, data formats, configurations)
- **`pattern`**: Behavioral patterns or trends observed
- **`preference`**: User preferences or system settings learned
- **`capability`**: Agent's own abilities or limitations discovered

## Auto-Registered Tools

When base memory is enabled, three tools are automatically registered:

### 1. `store_memory`
Stores information in long-term memory.

```json
{
  "category": "fact",
  "content": "OpenAI API rate limit is 3000 RPM for GPT-4",
  "context": "Important for API usage planning",
  "confidence": 0.9
}
```

### 2. `search_memories`
Searches memories for relevant information.

```json
{
  "query": "API rate limit",
  "limit": 10
}
```

### 3. `list_memories`
Lists memories by category.

```json
{
  "category": "fact",
  "limit": 20
}
```

## Usage Examples

### Basic Agent with Memory

```python
import asyncio
from spade_llm.agent.llm_agent import LLMAgent
from spade_llm.providers.llm_provider import LLMProvider

async def main():
    provider = LLMProvider.create_openai(api_key="your_key")
    
    agent = LLMAgent(
        jid="memory_agent@example.com",
        password="password",
        provider=provider,
        agent_base_memory=True,
        system_prompt="""You are a helpful assistant with long-term memory.
        Use your memory tools to learn and remember important information."""
    )
    
    await agent.start()
    # Agent now has persistent memory capabilities
    await agent.stop()

asyncio.run(main())
```

### Coexistence with Interaction Memory

```python
agent = LLMAgent(
    jid="agent@example.com",
    password="password",
    provider=provider,
    interaction_memory=True,   # Conversation-specific memory
    agent_base_memory=True     # Long-term agent memory
)
```

Both memory systems work together without conflicts.

## Storage Modes

Agent Base Memory supports two storage modes:

### **Persistent Storage (Default)**
```python
agent = LLMAgent(
    jid="agent@example.com",
    password="password",
    provider=provider,
    agent_base_memory=True  # File-based storage
)
```

**Characteristics:**
- **Persistence**: Memories survive agent restarts
- **Storage**: SQLite database files on disk
- **Use Cases**: Production agents, learning systems, long-term knowledge accumulation
- **Performance**: Slight disk I/O overhead, excellent for most use cases

### **In-Memory Storage (Temporary)**
```python
agent = LLMAgent(
    jid="test_agent@example.com",
    password="password",
    provider=provider,
    agent_base_memory=(True, ":memory:")  # RAM-only storage
)
```

**Characteristics:**
- **Temporary**: Memories deleted when agent stops
- **Storage**: RAM-only SQLite database
- **Use Cases**: Testing, development, privacy-sensitive operations, temporary agents
- **Performance**: Faster operations (no disk I/O), automatic cleanup

### **When to Use Each Mode**

| Scenario | Recommended Mode | Reason |
|----------|------------------|---------|
| Production deployment | Persistent | Need memory across restarts |
| Unit/integration testing | In-memory | Clean state, no file pollution |
| Development/prototyping | In-memory | Quick iteration, no cleanup needed |
| Privacy-sensitive operations | In-memory | No persistent traces |
| Learning/training agents | Persistent | Accumulate knowledge over time |
| Short-lived/batch agents | In-memory | Temporary operation, automatic cleanup |
| CI/CD pipelines | In-memory | Parallel execution, no file conflicts |

### **Custom File Paths**
```python
# Custom persistent location
agent = LLMAgent(
    jid="agent@example.com",
    password="password",
    provider=provider,
    agent_base_memory=(True, "/custom/memory/path")
)

# Use environment variable
import os
os.environ['SPADE_LLM_MEMORY_PATH'] = "/shared/memory"
agent = LLMAgent(
    jid="agent@example.com",
    password="password", 
    provider=provider,
    agent_base_memory=True  # Uses environment path
)
```

## Architecture

```
AgentBaseMemory (Public API)
├── MemoryBackend (Abstract Interface)
│   ├── SQLiteMemoryBackend (Current Implementation)
│   ├── PostgreSQLMemoryBackend (Future)
│   └── ChromaDBMemoryBackend (Future)
├── Memory Tools (Auto-registered)
│   ├── store_memory
│   ├── search_memories
│   └── list_memories
└── LLMAgent Integration (Zero-config)
```

## Storage Backend

### SQLite Backend (Default)
- **Dual Mode**: Supports both file-based and in-memory storage
- **File-based**: Stores memories in SQLite database files for persistence
- **In-memory**: RAM-only storage using `:memory:` for temporary usage
- **Async Support**: Uses `aiosqlite` for non-blocking operations
- **Performance**: Optimized with indexes for fast queries
- **Reliability**: ACID compliance prevents data corruption

### Custom Backends
The system is designed to support multiple backends:

```python
from spade_llm.memory.backends.base import MemoryBackend

class CustomBackend(MemoryBackend):
    async def initialize(self): ...
    async def store_memory(self, entry): ...
    # ... implement all abstract methods

# Use custom backend
agent = LLMAgent(
    jid="agent@example.com",
    password="password",
    provider=provider,
    agent_base_memory=True
)
# Custom backend integration would be added here
```

## Configuration

### Memory Path
Control where memories are stored:

```python
agent = LLMAgent(
    jid="agent@example.com",
    password="password",
    provider=provider,
    agent_base_memory=True,
    memory_path="/custom/memory/path"
)
```

### Environment Variables
Set default memory path:

```bash
export SPADE_LLM_MEMORY_PATH="/path/to/memories"
```

## File Structure

```
spade_llm/
├── memory/
│   ├── agent_base_memory.py          # Main memory class
│   ├── agent_base_memory_tools.py    # Auto-registered tools
│   └── backends/
│       ├── base.py                   # Abstract interface
│       └── sqlite.py                 # SQLite implementation
```

## Testing

Run the comprehensive test suite:

```bash
pytest tests/memory/test_agent_base_memory.py -v
pytest tests/memory/test_llm_agent_integration.py -v
```

## Performance

- **Memory Storage**: < 10ms for typical operations
- **Memory Retrieval**: < 50ms for typical queries
- **Concurrent Access**: Thread-safe SQLite operations
- **Storage Efficiency**: Minimal overhead per memory entry

## Migration from Interaction Memory

Agent Base Memory coexists with Interaction Memory:

- **Interaction Memory**: Conversation-specific facts (keep using)
- **Agent Base Memory**: Cross-conversation knowledge (new capability)

No migration is needed - enable both for comprehensive memory coverage.

## Future Enhancements

Planned features:

1. **PostgreSQL Backend**: For production deployments
2. **ChromaDB Backend**: For semantic search capabilities
3. **Memory Consolidation**: Automatic merging of similar memories
4. **Usage Analytics**: Track memory effectiveness
5. **Distributed Memory**: Multi-agent memory sharing

## Dependencies

The feature adds one new dependency:

```
aiosqlite>=0.17.0
```

This is automatically included when you install SPADE_LLM.

## Troubleshooting

### ImportError: aiosqlite
```bash
pip install aiosqlite>=0.17.0
```

### Permission Errors
Ensure the memory path is writable:
```python
agent = LLMAgent(..., memory_path="/writable/path")
```

### Database Lock Errors
SQLite uses WAL mode for better concurrency. If you encounter lock errors, check file permissions and disk space.

## Contributing

To add a new memory backend:

1. Inherit from `MemoryBackend`
2. Implement all abstract methods
3. Add tests in `tests/memory/`
4. Update documentation

See `backends/sqlite.py` for reference implementation.

## License

Agent Base Memory is part of SPADE_LLM and follows the same license.