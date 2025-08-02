"""
Simple Agent Memory Test with Routing

Minimal example to test Agent Thread Memory functionality with real agent interaction.
Uses routing to allow API Agent to decide between querying Database Agent or responding to Human.
"""

import asyncio
import getpass
import os
import spade

from spade_llm.agent import LLMAgent, ChatAgent
from spade_llm.providers import LLMProvider
from spade_llm.routing import RoutingResponse
from spade_llm.utils import load_env_vars


def api_agent_router(msg, response, context):
    """Routes API Agent responses based on content markers."""
    response_lower = response.lower()
    domain = str(msg.sender).split('@')[1]
    
    if "<query_database>" in response_lower:
        # API Agent wants to query database agent
        return RoutingResponse(
            recipients=f"database@{domain}",
            transform=lambda x: x.replace("<QUERY_DATABASE>", "").replace("<query_database>", "").strip()
        )
    else:
        # API Agent is ready to respond back to human (or whoever sent the message)
        return RoutingResponse(recipients=f"human@{domain}")


async def main():
    """Simple memory test with routing-enabled API agent."""
    print("=== Simple Agent Memory Test with Routing ===\n")
    
    # Load environment
    load_env_vars()
    
    # Get credentials
    xmpp_server = input("Enter XMPP server domain: ")
    api_key = os.environ.get("OPENAI_API_KEY") or input("Enter OpenAI API key: ")
    
    # Agent configurations
    agents_config = {
        "api_agent": f"api@{xmpp_server}",
        "db_agent": f"database@{xmpp_server}",
        "human": f"human@{xmpp_server}"
    }
    
    # Get passwords
    passwords = {}
    for role, jid in agents_config.items():
        passwords[role] = getpass.getpass(f"Password for {role} ({jid}): ")
    
    # Create provider
    provider = LLMProvider.create_openai(
        api_key=api_key,
        model="gpt-4.1-mini-2025-04-14",
        temperature=0.7
    )
    
    print("🔧 Setting up agents with memory and routing capabilities...\n")
    
    # Database Agent - Provides services
    db_agent = LLMAgent(
        jid=agents_config["db_agent"],
        password=passwords["db_agent"],
        provider=provider,
        system_prompt="""You are a Database Agent that manages MySQL databases.
        
        Your capabilities:
        - MySQL database on port 3306
        - Requires authentication token: "db_token_123"
        - Supports batch operations for efficiency
        - Available ONLY Monday-Friday 9 AM to 5 PM GMT (NOT available on weekends)
        - Prefers JSON format for data exchange
        - Maximum 1000 records per query
        - Database host: db.internal.company.com
        
        When asked about your capabilities, be very specific and complete.
        Always provide concrete technical details with exact values.
        If asked about availability, be clear about weekend restrictions.""",
        interaction_memory=False
    )
    
    # API Agent - Routes between database queries and human responses
    api_agent = LLMAgent(
        jid=agents_config["api_agent"],
        password=passwords["api_agent"],
        provider=provider,
        routing_function=api_agent_router,
        system_prompt=f"""You are an API Integration Agent that learns about other agents and helps humans.

        CRITICAL RULES:
        1. NEVER make up or invent information about the database agent
        2. ONLY use remember_interaction_info AFTER receiving real responses from database agent
        3. If you don't have specific information, you MUST query the database agent

        ROUTING RULES:
        - If you need to query the database agent for information, add <QUERY_DATABASE> at the END of your message
        - If you're ready to respond to the human, DO NOT add any markers
        
        WHEN TO USE <QUERY_DATABASE>:
        - Any question about database capabilities, ports, authentication, availability
        - Any question about database schedules, hours, formats, limits
        - ANY question you cannot answer from previous stored memory
        
        WORKFLOW:
        1. When human asks about database:
           a) Check if you have this EXACT information in memory
           b) If NO: Send query to database agent with <QUERY_DATABASE>
           c) Wait for database response
           d) Use remember_interaction_info to store the REAL response
           e) Answer human with the REAL information received
        
        2. If you have EXACT information in memory:
           - Use stored knowledge to respond directly
        
        EXAMPLES:
        Human: "What authentication does the database need?"
        You: "What authentication methods do you support? <QUERY_DATABASE>"
        
        Human: "Is database available on saturdays?"
        You: "What are your availability hours and which days are you available? <QUERY_DATABASE>"
        
        The database agent JID is: {agents_config["db_agent"]}
        
        REMEMBER: Always query first, never guess or invent!""",
        interaction_memory=True

    )
    
    # Human interface
    chat_agent = ChatAgent(
        jid=agents_config["human"],
        password=passwords["human"],
        target_agent_jid=agents_config["api_agent"],
        verbose=False
    )
    
    # Start agents
    print("🚀 Starting agents...")
    await db_agent.start()
    print(f"✓ Database Agent started: {agents_config['db_agent']}")
    
    await api_agent.start()
    print(f"✓ API Agent started: {agents_config['api_agent']}")
    
    await chat_agent.start()
    print(f"✓ Chat Agent started: {agents_config['human']}")
    
    print("\n" + "="*70)
    print("🧠 AGENT MEMORY + ROUTING TESTING")
    print("="*70)
    print("API Agent has:")
    print("  • Interaction memory enabled (learns from database agent)")
    print("  • Routing capability (decides database query vs human response)")
    print("Database Agent provides technical information")
    print("="*70)
    
    print("\n📖 TEST INSTRUCTIONS:")
    print("1. Ask API Agent about database capabilities it doesn't know yet")
    print("2. API Agent will route query to Database Agent (<QUERY_DATABASE>)")
    print("3. API Agent learns and stores technical details in memory")
    print("4. API Agent responds back to you with learned information")
    print("5. Ask again - API Agent should use stored memory (no database query)")
    print("\n💡 Example messages:")
    print("  • 'What are the database agent capabilities?'")
    print("  • 'What authentication does the database need?'")
    print("  • 'What data formats does the database support?'")
    print("  • 'What are the database limits and ports?'")
    print("\n🔗 Routing Flow:")
    print("  Human → API Agent → [<QUERY_DATABASE>] → Database Agent → API Agent → Human")
    print("  Human → API Agent → [memory exists] → Human (direct response)")
    print("\n" + "="*70)
    
    # Show memory file location
    if api_agent.interaction_memory:
        print(f"📁 Memory will be stored at: {api_agent.interaction_memory.storage_path}")
    
    await chat_agent.run_interactive()
    
    # Show final memory state
    print("\n📊 FINAL MEMORY STATE:")
    if api_agent.interaction_memory:
        all_interactions = api_agent.interaction_memory.get_all_interactions()
        if all_interactions:
            print("API Agent learned:")
            for conv_id, memories in all_interactions.items():
                print(f"\nConversation: {conv_id}")
                for memory in memories:
                    print(f"  • {memory['content']} (at {memory['timestamp']})")
        else:
            print("No memories stored yet.")
        
        print(f"\n📁 Memory file: {api_agent.interaction_memory.storage_path}")
    
    # Stop agents
    print("\n🛑 Stopping agents...")
    await chat_agent.stop()
    await api_agent.stop()
    await db_agent.stop()
    
    print("✅ Memory + Routing test completed!")


if __name__ == "__main__":
    print("🔍 Prerequisites:")
    print("• OpenAI API key (set OPENAI_API_KEY or enter manually)")
    print("• XMPP server running and accessible")
    print("• 3 XMPP accounts created for the agents")
    print()
    
    spade.run(main())