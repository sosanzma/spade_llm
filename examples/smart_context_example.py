"""
Smart Context Management Example - Research Agent Focus

This example demonstrates the SmartWindowSizeContext implementation with:
- ResearchAgent: Gathers information using tools (with context preservation)
- ChatAgent: Interactive user interface

Features:
- SmartWindowSizeContext with tool call/result pair preservation
- Step-by-step context debugging after each interaction
- Tool usage with context preservation
- Real-time conversation history tracking
"""

import asyncio
import getpass
import logging
import os
import spade
from typing import Dict, Any

from spade_llm.agent import LLMAgent, ChatAgent
from spade_llm.providers import LLMProvider
from spade_llm.tools import LangChainToolAdapter
from spade_llm.context.management import SmartWindowSizeContext
from spade_llm.utils import load_env_vars

# Import LangChain tools
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ContextDebugger:
    """Helper class to debug context management behavior"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.message_count = 0
        
    def log_context_usage(self, context_manager, conversation_id: str):
        """Log current context state"""
        if conversation_id in context_manager._conversations:
            messages = context_manager._conversations[conversation_id]
            self.message_count = len(messages)
            logger.info(f"[{self.agent_name}] Context: {self.message_count} messages in conversation {conversation_id}")
            
            # Log message types
            msg_types = {}
            for msg in messages:
                role = msg.get('role', 'unknown')
                msg_types[role] = msg_types.get(role, 0) + 1
            
            logger.info(f"[{self.agent_name}] Message types: {msg_types}")
        else:
            logger.info(f"[{self.agent_name}] No conversation found for ID: {conversation_id}")

async def main():
    """Main function demonstrating smart context management with research agent."""
    print("=== Smart Context Management Example - Research Focus ===\n")
    
    # Load environment
    load_env_vars()
    
    # Get credentials
    xmpp_server = input("Enter XMPP server domain: ")
    api_key = os.environ.get("OPENAI_API_KEY") or input("Enter OpenAI API key: ")
    
    # Agent configurations
    agents_config = {
        "research": f"researcher@{xmpp_server}",
        "human": f"human@{xmpp_server}"
    }
    
    # Get passwords
    passwords = {}
    for role, jid in agents_config.items():
        passwords[role] = getpass.getpass(f"Password for {role} agent ({jid}): ")
    
    # Create provider
    provider = LLMProvider.create_openai(
        api_key=api_key,
        model="gpt-4o-mini",
        temperature=0.7
    )
    
    # Create tools for research
    research_tools = [
        LangChainToolAdapter(WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper()))
    ]

    print("🔧 Setting up Research Agent with Smart Context Management...\n")
    
    research_context = SmartWindowSizeContext(
        max_messages=4,           # Small context window for testing
        preserve_initial=1,       # Keep firs message (initial objectives)
        prioritize_tools=True     # Prioritize tool results
    )
    

    research_agent = LLMAgent(
        jid=agents_config["research"],
        password=passwords["research"],
        provider=provider,
        tools=research_tools,
        context_management=research_context,
        system_prompt="""You are a Research Agent specializing in gathering information.
        
        Your role:
        1. Receive research topics/questions from users
        2. Use available tools to gather relevant information
        3. Provide structured research summaries
        
        Always structure your responses with:
        - Topic Summary
        - Key Findings (numbered list)
        - Sources Used
        
        Use tools when you need current information or specific data.""",
        max_interactions_per_conversation=10
    )



    
    chat_agent = ChatAgent(
        jid=agents_config["human"],
        password=passwords["human"],
        target_agent_jid=agents_config["research"],
        verbose=False
    )
    
    # Start agents
    print("🚀 Starting agents...")
    await research_agent.start()
    print(f"✓ Research Agent started: {agents_config['research']}")
    
    await chat_agent.start()
    print(f"✓ Chat Agent started: {agents_config['human']}")
    
    print("\n" + "="*70)
    print("🧠 SMART CONTEXT MANAGEMENT TESTING")
    print("="*70)
    print("Research Agent Configuration:")
    print(f"  • Max messages: {research_context.max_messages}")
    print(f"  • Preserve initial: {research_context.preserve_initial} messages")
    print(f"  • Prioritize tools: {research_context.prioritize_tools}")
    print("="*70)
    
    print("\n📖 INSTRUCTIONS:")
    print("• Ask research questions one by one")
    print("• After each response, you'll see detailed context debugging")
    print("• Watch how the context window manages messages and tool results")
    print("• Type 'exit' to quit")
    print("• Try asking 5-6 questions to see context trimming in action")
    print("\n💡 Suggested progression:")
    print("  1. 'Tell me about artificial intelligence'")
    print("  2. 'Research machine learning applications'") 
    print("  3. 'Look up deep learning techniques'")
    print("  4. 'Find information about neural networks'")
    print("  5. 'Search for AI ethics research'")
    print("  6. 'What about quantum computing?'")
    print("\n" + "="*70)

    await chat_agent.run_interactive()

    # Stop all agents
    print("\n🛑 Stopping agents...")
    await chat_agent.stop()
    await research_agent.stop()
    
    print("✅ Smart Context Management example completed!")
    
    # Final summary
    print(f"\n📊 SESSION SUMMARY:")
    print("Context management strategy preserved tool call/result pairs ✓")


if __name__ == "__main__":
    print("🔍 Prerequisites:")
    print("• OpenAI API key (set OPENAI_API_KEY or enter manually)")
    print("• XMPP server running and accessible")
    print("• Internet connection for Wikipedia tool")
    print("• 2 XMPP accounts created for the agents")
    print()
    
    spade.run(main())