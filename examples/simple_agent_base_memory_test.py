"""
Simple Agent Base Memory Test - NEW SYNTAX

This example demonstrates agent base memory using the new tuple syntax for path configuration.
No environment variables needed - paths are configured directly in the agent constructor.
"""

import asyncio
import getpass
import os
import spade

from spade_llm import load_env_vars
from spade_llm.agent import LLMAgent, ChatAgent
from spade_llm.providers import LLMProvider
from spade_llm.routing import RoutingResponse


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
    """Simple agent base memory test with NEW SYNTAX."""
    print("=== Simple Agent Base Memory Test - NEW SYNTAX ===\n")
    
    # Define custom memory path using new syntax (no environment variables needed!)
    custom_memory_path = "C:\\Users\\manel\\PycharmProjects\\spade_llm\\spade_llm\\data\\agent_based_memory"
    print(f"🎯 Using custom memory path: {custom_memory_path}")
    
    # Get credentials
    load_env_vars()
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
        model="gpt-4o-mini",
        temperature=0.3
    )
    
    print("🔧 Setting up agents with NEW SYNTAX memory configuration...\n")
    
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
        If asked about availability, be clear about weekend restrictions."""
    )
    
    # API Agent - NEW SYNTAX: Custom path for agent base memory
    api_agent = LLMAgent(
        jid=agents_config["api_agent"],
        password=passwords["api_agent"],
        provider=provider,
        routing_function=api_agent_router,
        system_prompt=f"""You are an API Integration Agent that learns about database capabilities.

        MEMORY DATABASE STRUCTURE - Use ONLY these 3 categories:
        1. "connection" - Host, port, authentication, security details
        2. "capability" - What the database can/cannot do, limits, availability
        3. "format" - Data formats, protocols, query syntax preferences
        
        SEARCH STRATEGY - Use SPECIFIC keywords for each category:
        - For connection info: search_memories("connection")
        - For capabilities: search_memories("capability") 
        - For data formats: search_memories("format")
        
        WORKFLOW:
        1. Human asks question → Identify category (connection/capability/format)
        2. Search memory using category keyword: search_memories("[category]")
        3. If found relevant info: Answer directly using stored knowledge
        4. If NO relevant info found: Contact database agent with <QUERY_DATABASE>
        5. When database responds: Store answer in correct category
        
        STORAGE EXAMPLES:
        - store_memory(category="connection", content="MySQL database on port 3306 at db.internal.company.com, requires token db_token_123")
        - store_memory(category="capability", content="Maximum 1000 records per query, available Monday-Friday 9AM-5PM GMT only")
        - store_memory(category="format", content="Prefers JSON format for data exchange, supports batch operations")
        
        SEARCH EXAMPLES:
        Human: "What port does the database use?" → search_memories("connection")
        Human: "What are the database limits?" → search_memories("capability")  
        Human: "What format does it prefer?" → search_memories("format")
        
        CRITICAL RULES:
        - ALWAYS search memory first with the correct category keyword
        - If search returns empty or irrelevant results, IMMEDIATELY contact database agent
        - NEVER guess or make up information
        - Store responses in the correct category for future searches
        
        ROUTING:
        - <QUERY_DATABASE> = Send to database agent
        - No marker = Respond to human
        
        Database JID: {agents_config["db_agent"]}""",
        
        # 🆕 NEW SYNTAX: Tuple format (enabled, custom_path)
        agent_base_memory=(True, custom_memory_path)
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
    print("🆕 NEW SYNTAX DEMONSTRATION")
    print("="*70)
    print("✅ No environment variables needed!")
    print("✅ Direct path configuration in agent constructor!")
    print("✅ Agent base memory with persistent learning!")
    print("="*70)
    
    print("\n🧰 Available Memory Tools:")
    tool_names = [tool.name for tool in api_agent.get_tools()]
    for tool_name in tool_names:
        print(f"  • {tool_name}")
    
    print(f"\n📁 Memory File Location:")
    
    if api_agent.agent_base_memory:
        backend = api_agent.agent_base_memory.backend
        print(f"🗄️  Agent Base Memory: {backend.db_path}")
    
    print(f"\n🎯 Memory configured with custom path: {custom_memory_path}")
    
    print(f"\n📖 TEST SUGGESTIONS (organized by category):")
    print("🔗 CONNECTION questions:")
    print("  • 'What port does the database use?'")
    print("  • 'What authentication is needed?'")
    print("  • 'What is the database host?'")
    print("\n⚡ CAPABILITY questions:")
    print("  • 'What are the database limits?'") 
    print("  • 'Is the database available on weekends?'")
    print("  • 'What can the database do?'")
    print("\n📄 FORMAT questions:")
    print("  • 'What data format does it prefer?'")
    print("  • 'Does it support batch operations?'")
    print("\n🔄 Then ask the same questions again to see memory in action!")
    print("\n" + "="*70)
    
    # Show current memory stats
    if api_agent.agent_base_memory:
        try:
            stats = await api_agent.agent_base_memory.get_memory_stats()
            print(f"📊 Current memory stats: {stats['total_memories']} memories stored")
            if stats['category_counts']:
                for category, count in stats['category_counts'].items():
                    print(f"  • {category}: {count} memories")
        except:
            print("📊 Memory database will be created on first use")
    
    await chat_agent.run_interactive()
    
    # Show final memory state
    print("\n📊 FINAL MEMORY STATE:")
    if api_agent.agent_base_memory:
        try:
            stats = await api_agent.agent_base_memory.get_memory_stats()
            print(f"API Agent learned {stats['total_memories']} total memories:")
            
            for category in ['fact', 'pattern', 'preference', 'capability']:
                if category in stats['category_counts']:
                    count = stats['category_counts'][category]
                    print(f"\n{category.title()}s ({count}):")
                    memories = await api_agent.agent_base_memory.get_memories_by_category(category, limit=10)
                    for memory in memories:
                        print(f"  • {memory.content}")
                        if memory.context:
                            print(f"    Context: {memory.context}")
        except Exception as e:
            print(f"Could not retrieve memory stats: {e}")
    
    # Show file locations
    print(f"\n📁 Memory files created:")
    if api_agent.agent_base_memory:
        backend = api_agent.agent_base_memory.backend
        print(f"  🗄️  {backend.db_path}")
        print("💾 This memory persists across agent restarts!")
    
    # Stop agents
    print("\n🛑 Stopping agents...")
    await chat_agent.stop()
    await api_agent.stop()
    await db_agent.stop()
    
    print("✅ NEW SYNTAX memory test completed!")
    print(f"\n🎉 SUCCESS: Memory files created at specified custom path!")
    print(f"📍 {custom_memory_path}")


if __name__ == "__main__":
    print("🔍 Prerequisites:")
    print("• OpenAI API key (set OPENAI_API_KEY or enter manually)")
    print("• XMPP server running and accessible")
    print("• 3 XMPP accounts created for the agents")
    print()
    print("🆕 NEW SYNTAX FEATURES:")
    print("• agent_base_memory=(True, 'C:\\\\path\\\\to\\\\memory')")
    print("• No environment variables needed")
    print("• Direct path configuration in constructor")
    print("• Persistent agent learning across restarts")
    print()
    
    spade.run(main())