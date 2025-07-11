"""
Ollama Tool Calling Example

Demonstrates how to use tools with SPADE agents and Ollama.
"""

import asyncio
import getpass
from datetime import datetime
import spade

from spade_llm.agent import LLMAgent, ChatAgent
from spade_llm.providers import LLMProvider
from spade_llm.tools import LLMTool


# Simple tool functions
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculate_math(expression: str) -> str:
    """Safely evaluate a mathematical expression."""
    try:
        result = eval(expression, {"__builtins__": {}})
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


def get_weather(city: str) -> str:
    """Get simulated weather for a city."""
    weather_data = {
        "madrid": "22°C, sunny",
        "london": "15°C, cloudy",
        "new york": "18°C, rainy",
        "tokyo": "25°C, clear"
    }
    return weather_data.get(city.lower(), f"No data for {city}")


async def main():
    print("=== Ollama Tool Calling Example ===\n")

    # LLM agent setup
    llm_jid = input("LLM agent JID: ")
    llm_password = getpass.getpass("LLM password: ")

    # Create tools
    tools = [
        LLMTool(
            name="get_current_time",
            description="Get current date and time",
            parameters={"type": "object", "properties": {}, "required": []},
            func=get_current_time
        ),
        LLMTool(
            name="get_weather",
            description="Get weather for a city",
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"}
                },
                "required": ["city"]
            },
            func=get_weather
        )
    ]

    # Create provider
    provider = LLMProvider.create_ollama(
        model="qwen3:4b",
        base_url="http://localhost:11434/v1"
    )

    # Create LLM agent with tools
    llm_agent = LLMAgent(
        jid=llm_jid,
        password=llm_password,
        provider=provider,
        system_prompt="You are a helpful assistant with tools: get_current_time, calculate_math, get_weather",
        tools=tools  # Tools are now passed directly to the agent
    )

    await llm_agent.start()
    print(f"✓ LLM agent started: {llm_jid}")

    # Chat agent setup
    user_jid = input("User agent JID: ")
    user_password = getpass.getpass("User password: ")

    chat = ChatAgent(
        jid=user_jid,
        password=user_password,
        target_agent_jid=llm_jid
    )

    await chat.start()
    print(f"✓ Chat agent started: {user_jid}")

    print("\nTry: What time is it? |  Weather in Madrid")
    print("Type 'exit' to quit\n")

    # Run chat
    await chat.run_interactive()

    # Cleanup
    await chat.stop()
    await llm_agent.stop()
    print("Agents stopped.")


if __name__ == "__main__":
    spade.run(main())