"""
Valencia Smart City MCP Example

Demonstrates using Valencia Smart City MCP server with SPADE agents.
"""

import asyncio
import getpass
import os
import spade

from spade_llm.agent import LLMAgent, ChatAgent
from spade_llm.providers import LLMProvider
from spade_llm.mcp import StdioServerConfig
from spade_llm.utils import load_env_vars


async def main():
    # Load environment
    load_env_vars()
    api_key = os.environ.get("OPENAI_API_KEY") or input("OpenAI API key: ")

    # Agent credentials
    llm_jid = input("LLM Agent JID: ")
    llm_password = getpass.getpass("LLM Agent password: ")

    # Valencia Smart City MCP server configuration
    valencia_mcp = StdioServerConfig(
        name="ValenciaSmart",
        command="uv",
        args= ["run", "valencia_traffic_mcp.py"],
        cache_tools=True
    )

    # Create provider
    provider = LLMProvider.create_openai(
        api_key=api_key,
        model="gpt-4o-mini"
    )

    # Create LLM agent with MCP
    llm_agent = LLMAgent(
        jid=llm_jid,
        password=llm_password,
        provider=provider,
        system_prompt="You are a helpful assistant with access to Valencia city data tools. Provide weather, traffic and city info.",
        mcp_servers=[valencia_mcp]
    )

    await llm_agent.start()
    print(f"✓ LLM agent started: {llm_jid}")

    # Human agent setup
    human_jid = input("\nHuman Agent JID: ")
    human_password = getpass.getpass("Human Agent password: ")

    # Simple response display
    def display_response(message: str, sender: str):
        print(f"\n🌆 Valencia Smart: {message}")

    chat = ChatAgent(
        jid=human_jid,
        password=human_password,
        target_agent_jid=llm_jid,
        display_callback=display_response
    )

    await chat.start()
    print(f"✓ Chat agent started: {human_jid}")

    print("\n=== Valencia Smart City Assistant ===")
    print("Ask about Valencia weather, traffic, or city info")
    print("Type 'exit' to quit\n")

    # Run chat
    await chat.run_interactive(
        input_prompt="You> ",
        exit_command="exit"
    )

    # Cleanup
    await chat.stop()
    await llm_agent.stop()
    print("Agents stopped.")


if __name__ == "__main__":
    spade.run(main())