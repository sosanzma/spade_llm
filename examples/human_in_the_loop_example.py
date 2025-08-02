"""
Example of using the Human-in-the-Loop tool with SPADE LLM.

This example demonstrates how to create an agent that can consult
with a human expert when needed.

Prerequisites:
1. Start an XMPP server with WebSocket support
2. Create two XMPP accounts: one for the agent and one for the human expert
3. Start the web interface: python -m spade_llm.human_interface.web_server
4. Open http://localhost:8080 and connect as the human expert
"""

import asyncio
import getpass
import logging
import spade

from spade_llm.agent import LLMAgent, ChatAgent
from spade_llm.tools import HumanInTheLoopTool
from spade_llm.providers import LLMProvider
from spade_llm.utils import load_env_vars

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    # Load environment variables
    env_vars = load_env_vars()
    
    # XMPP Configuration
    XMPP_SERVER = "sosanzma"
    AGENT_JID = f"agent1@{XMPP_SERVER}"
    AGENT_PASSWORD  = getpass.getpass(f"Password for agent {AGENT_JID}: ")
    HUMAN_JID = f"human1@{XMPP_SERVER}"
    USER_JID = f"chat@{XMPP_SERVER}"
    USER_PASSWORD = getpass.getpass(f"Password for agent {USER_JID}: ")
    
    # Create OpenAI provider
    provider = LLMProvider.create_openai(
        api_key=env_vars["OPENAI_API_KEY"],
        model="gpt-4o-mini",
        temperature=0.7
    )
    
    # System prompt that encourages using human expert
    system_prompt = """You are a helpful AI assistant with access to a human expert.
    
When you encounter questions that:
- Require real-world, current information you don't have
- Need human judgment or opinion
- Involve company-specific or proprietary information
- Require clarification about ambiguous requests

You should consult with the human expert using the ask_human_expert tool.

Always be clear about when you're providing your own knowledge vs. information from the human expert."""
    
    # Create the human-in-the-loop tool
    human_tool = HumanInTheLoopTool(
        human_expert_jid=HUMAN_JID,
        timeout=300.0,  # 5 minutes
        name="ask_human_expert",
        description="""Ask a human expert for help when you need:
        - Current information not in your training data
        - Clarification on ambiguous requests  
        - Human judgment or opinions
        - Company-specific information
        - Verification of important facts"""
    )
    
    # Create the LLM agent with the human tool
    agent = LLMAgent(
        jid=AGENT_JID,
        password=AGENT_PASSWORD,
        provider=provider,
        system_prompt=system_prompt,
        tools=[human_tool],  # Pass tools in constructor
        verify_security=False
    )

    # Start the agent
    await agent.start()
    logger.info(f"Agent {AGENT_JID} started successfully")
    
    # Wait for agent to fully connect to XMPP server
    await asyncio.sleep(10.0)
    
    # Verify agent is properly connected
    if agent.client is None:
        logger.error("Agent client is None after initialization")
        return
    logger.info("Agent client verified as connected")
    
    # Create a chat interface for testing
    chat_agent = ChatAgent(
        jid=USER_JID,
        password=USER_PASSWORD,
        target_agent_jid=AGENT_JID,
        verify_security=False
    )
    
    await chat_agent.start()
    logger.info(f"Chat interface {USER_JID} connected")
    
    # Wait for chat agent to fully connect
    await asyncio.sleep(3.0)
    
    print("\n" + "="*60)
    print("Human-in-the-Loop Example")
    print("="*60)
    print(f"\n1. Make sure the human expert is connected at: http://localhost:8080")
    print(f"   Expert JID: {HUMAN_JID}")
    print(f"\n2. Try asking questions that require human expertise:")
    print("   - 'What's the WiFi password for our office?'")
    print("   - 'Should we proceed with the Johnson proposal?'") 
    print("   - 'What's the current status of Project X?'")
    print("\n3. The agent will consult the human expert when needed")
    print("\nType 'exit' to quit\n")
    
    # Run interactive chat
    await chat_agent.run_interactive(
        input_prompt="You: ",
        exit_command="exit",
        response_timeout=60.0  # Longer timeout for human responses
    )
    
    # Clean up
    await chat_agent.stop()
    await agent.stop()
    logger.info("Example finished")


if __name__ == "__main__":
    # Instruction for the user
    print("\nBefore running this example:")
    print("1. Start the human expert web interface:")
    print("   python -m spade_llm.human_interface.web_server")
    print("\n2. Open http://localhost:8080 in your browser")
    print("3. Connect using the human expert credentials")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    input()
    
    spade.run(main())
