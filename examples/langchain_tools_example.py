"""
LangChain Tools Example

Demonstrates using LangChain tools with SPADE agents.
"""

import asyncio
import getpass
import os
import spade

from spade_llm.agent import LLMAgent, ChatAgent
from spade_llm.providers import LLMProvider
from spade_llm.tools import LangChainToolAdapter
from spade_llm.utils import load_env_vars

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper


async def main():
    # Load environment
    load_env_vars()
    api_key = os.environ.get("OPENAI_API_KEY") or input("OpenAI API key: ")

    # Agent credentials
    smart_jid = input("Smart Agent JID: ")
    smart_password = getpass.getpass("Smart Agent password: ")

    # Create LangChain tools
    tools = [
        LangChainToolAdapter(DuckDuckGoSearchRun()),
        LangChainToolAdapter(WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper()))
    ]

    # Create provider (choose one)
    # Option 1: OpenAI
    provider = LLMProvider.create_openai(
        api_key=api_key,
        model="gpt-4o-mini"
    )

    # Option 2: Ollama (uncomment to use)
    # provider = LLMProvider.create_ollama(
    #     model="qwen3:4b",
    #     base_url="http://localhost:11434/v1"
    # )

    # Register tools
    for tool in tools:
        provider.register_tool(tool)

    # Create LLM agent
    smart_agent = LLMAgent(
        jid=smart_jid,
        password=smart_password,
        provider=provider,
        system_prompt="You are a helpful assistant with search and Wikipedia tools. Use them for current info.",
        tools=tools
    )

    await smart_agent.start()
    print(f"✓ Smart agent started: {smart_jid}")
    print("Available tools: Web Search, Wikipedia")

    # Human agent setup
    human_jid = input("\nHuman Agent JID: ")
    human_password = getpass.getpass("Human Agent password: ")

    chat = ChatAgent(
        jid=human_jid,
        password=human_password,
        target_agent_jid=smart_jid
    )

    await chat.start()
    print(f"✓ Chat agent started: {human_jid}")

    print("\nAvailable tools: Web Search, Wikipedia")
    print("Type 'exit' to quit\n")

    # Run chat
    await chat.run_interactive()

    # Cleanup
    await chat.stop()
    await smart_agent.stop()
    print("Agents stopped.")


if __name__ == "__main__":
    spade.run(main())