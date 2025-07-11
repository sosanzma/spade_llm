# Tools API

API reference for the SPADE_LLM tools system.

## LLMTool

Core tool class for defining executable functions.

### Constructor

```python
LLMTool(
    name: str,
    description: str,
    parameters: Dict[str, Any],
    func: Callable[..., Any]
)
```

**Parameters:**

- `name` - Unique tool identifier
- `description` - Tool description for LLM understanding
- `parameters` - JSON Schema parameter definition
- `func` - Python function to execute

### Methods

#### execute()

```python
async def execute(self, **kwargs) -> Any
```

Execute tool with provided arguments.

**Example:**

```python
result = await tool.execute(city="Madrid", units="celsius")
```

#### to_dict()

```python
def to_dict(self) -> Dict[str, Any]
```

Convert tool to dictionary representation.

#### to_openai_tool()

```python
def to_openai_tool(self) -> Dict[str, Any]
```

Convert to OpenAI tool format.

### Example

```python
from spade_llm import LLMTool

async def get_weather(city: str, units: str = "celsius") -> str:
    """Get weather for a city."""
    return f"Weather in {city}: 22°C, sunny"

weather_tool = LLMTool(
    name="get_weather",
    description="Get current weather information for a city",
    parameters={
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "Name of the city"
            },
            "units": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "default": "celsius"
            }
        },
        "required": ["city"]
    },
    func=get_weather
)
```

## Parameter Schema

Tools use JSON Schema for parameter validation:

### Basic Types

```python
# String parameter
"city": {
    "type": "string",
    "description": "City name"
}

# Number parameter  
"temperature": {
    "type": "number",
    "minimum": -100,
    "maximum": 100
}

# Boolean parameter
"include_forecast": {
    "type": "boolean",
    "default": False
}

# Array parameter
"cities": {
    "type": "array",
    "items": {"type": "string"},
    "maxItems": 10
}
```

### Complex Schema

```python
parameters = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Search query"
        },
        "filters": {
            "type": "object",
            "properties": {
                "date_range": {
                    "type": "object",
                    "properties": {
                        "start": {"type": "string", "format": "date"},
                        "end": {"type": "string", "format": "date"}
                    }
                },
                "category": {
                    "type": "string",
                    "enum": ["news", "blogs", "academic"]
                }
            }
        },
        "max_results": {
            "type": "integer",
            "minimum": 1,
            "maximum": 100,
            "default": 10
        }
    },
    "required": ["query"]
}
```

## LangChain Integration

### LangChainToolAdapter

```python
from spade_llm.tools import LangChainToolAdapter
from langchain_community.tools import DuckDuckGoSearchRun

# Create LangChain tool
search_lc = DuckDuckGoSearchRun()

# Adapt for SPADE_LLM
search_tool = LangChainToolAdapter(search_lc)

# Use with agent
agent = LLMAgent(
    jid="agent@example.com",
    password="password",
    provider=provider,
    tools=[search_tool]
)
```


## Best Practices

### Tool Design

- **Single Purpose**: Each tool should do one thing well
- **Clear Names**: Use descriptive tool names
- **Good Descriptions**: Help LLM understand when to use tools
- **Validate Inputs**: Always validate and sanitize parameters
- **Handle Errors**: Return meaningful error messages
- **Use Async**: Enable concurrent execution
