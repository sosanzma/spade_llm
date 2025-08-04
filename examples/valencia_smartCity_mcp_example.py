"""
Valencia Smart City MCP Example

Demonstrates using Valencia Smart City MCP server with SPADE agents.

PREREQUISITES:
1. Start SPADE built-in server in another terminal:
   spade run
   
   (Advanced server configuration available but not needed)

2. Install dependencies:
   pip install spade_llm

This example uses SPADE's default built-in server (localhost:5222) - no account registration needed!
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

    # XMPP server configuration - using default SPADE settings
    xmpp_server = "localhost"
    print("🌐 Using SPADE built-in server (localhost:5222)")
    print("  No account registration needed!")
    # Advanced server configuration available but not needed
    
    # Agent credentials
    llm_jid = f"llm_agent@{xmpp_server}"
    llm_password = "llm_pass"  # Simple password (auto-registration with SPADE server)

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
    human_jid = f"human@{xmpp_server}"
    human_password = "human_pass"  # Simple password (auto-registration with SPADE server)

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