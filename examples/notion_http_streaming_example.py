"""
Notion HTTP Streaming MCP Example

Demonstrates using Notion MCP server with HTTP Streaming transport and SPADE agents.
This example creates a simple chat interface to interact with Notion workspace.

Prerequisites:
- OpenAI API key
- XMPP server running
- Internet connection for Notion MCP service
"""

import asyncio
import getpass
import os
import spade

from spade_llm.agent import LLMAgent, ChatAgent
from spade_llm.providers import LLMProvider
from spade_llm.mcp import StreamableHttpServerConfig
from spade_llm.utils import load_env_vars
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
async def main():
    print("=== Notion HTTP Streaming MCP Example ===\n")
    
    # Load environment variables
    load_env_vars()
    
    # LLM Provider setup
    print("🔧 Setting up LLM Provider...")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        api_key = input("Enter your OpenAI API key: ")
    
    provider = LLMProvider.create_openai(
        api_key=api_key,
        model="gpt-4o-mini",
        temperature=0.7
    )
    
    # XMPP setup
    print("🌐 XMPP Server setup...")
    xmpp_server = input("Enter your XMPP server domain: ")
    
    # Agent credentials
    llm_jid = f"notion_agent@{xmpp_server}"
    llm_password = getpass.getpass(f"Enter password for {llm_jid}: ")
    
    human_jid = f"human@{xmpp_server}"
    human_password = getpass.getpass(f"Enter password for {human_jid}: ")
    
    # Notion MCP HTTP Streaming configuration
    print("📚 Setting up Notion MCP via HTTP Streaming...")
    notion_mcp = StreamableHttpServerConfig(
        name="NotionMCP",
        url="https://mcp.composio.dev/composio/server/902f9f2b-01dc-4af4-82ba-8707c3b11fe2/mcp?include_composio_helper_actions=true",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "SPADE_LLM/1.0"
        },
        timeout=30.0,
        sse_read_timeout=300.0,  # 5 minutes for long operations
        terminate_on_close=True,
        cache_tools=True
    )
    
    # Create Notion-enabled LLM agent
    print("🤖 Creating Notion Agent...")
    notion_agent = LLMAgent(
        jid=llm_jid,
        password=llm_password,
        provider=provider,
        system_prompt="""You are a helpful Notion assistant with access to Notion workspace tools.

You can help users:
- Create and manage Notion pages
- Search through Notion content
- Update and organize information
- Retrieve data from databases
- Manage workspace content

When using Notion tools:
1. Be clear about what actions you're performing
2. Provide feedback on successful operations
3. Help users understand the results
4. Suggest follow-up actions when appropriate

Always be helpful and explain what you're doing with the Notion workspace.""",
        mcp_servers=[notion_mcp],
        max_interactions_per_conversation=20,
        verify_security=False  # For demo purposes
    )
    
    # Start Notion agent
    print("🚀 Starting Notion Agent...")
    await notion_agent.start()
    print(f"✅ Notion agent started: {llm_jid}")
    
    # Wait for agent to be fully connected
    await asyncio.sleep(2.0)
    
    # Create human chat interface
    print("👤 Setting up Human Interface...")
    
    def display_response(message: str, sender: str):
        """Display agent responses with nice formatting."""
        print(f"\n📚 Notion Assistant:")
        print("=" * 50)
        print(message)
        print("=" * 50)
    

    
    chat_agent = ChatAgent(
        jid=human_jid,
        password=human_password,
        target_agent_jid=llm_jid,
        display_callback=display_response,

        verify_security=False
    )
    
    # Start chat agent
    await chat_agent.start()
    print(f"✅ Chat agent started: {human_jid}")
    
    # Display usage instructions
    print("\n" + "=" * 60)
    print("📚 NOTION WORKSPACE ASSISTANT")
    print("=" * 60)
    print("\n🎯 What you can do:")
    print("• 'Create a new page about [topic]'")
    print("• 'Search for pages containing [keyword]'")
    print("• 'Show me my recent pages'")
    print("• 'Update the page titled [title] with [content]'")
    print("• 'List all databases in my workspace'")
    print("• 'Create a task in my todo database'")
    print("\n💡 Tips:")
    print("• Be specific about what you want to do")
    print("• The agent will explain each step it takes")
    print("• Ask for help if you're not sure what's possible")
    print("\n📝 Type 'exit' to quit")
    print("-" * 60)
    
    # Run interactive chat
    try:
        await chat_agent.run_interactive(
            input_prompt="💬 You> ",
            exit_command="exit",
            response_timeout=90.0  # Longer timeout for Notion operations
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        # Clean shutdown
        print("\n🔄 Stopping agents...")
        await chat_agent.stop()
        await notion_agent.stop()
        print("✅ All agents stopped successfully")


if __name__ == "__main__":
    print("🚀 Starting Notion HTTP Streaming MCP Example...")
    print("📋 Make sure you have:")
    print("   • OpenAI API key")
    print("   • XMPP server running")
    print("   • Internet connection")
    print()
    
    try:
        spade.run(main())
    except KeyboardInterrupt:
        print("\n👋 Example terminated by user")
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        print("💡 Check your configuration and try again")