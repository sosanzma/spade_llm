"""
Example demonstrating agent base memory functionality.

This example shows how to:
1. Enable agent base memory with a simple flag
2. Use memory tools to store and retrieve information
3. Observe how the agent learns over time

The agent will automatically have access to memory tools when base memory is enabled.
"""

import asyncio
import os
from spade_llm.agent.llm_agent import LLMAgent
from spade_llm.providers.llm_provider import LLMProvider
from spade_llm.utils.env_loader import load_env_vars

# Load environment variables
load_env_vars()

async def main():
    """Main example function."""
    
    # Get API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    # Create LLM provider
    provider = LLMProvider.create_openai(
        api_key=api_key,
        model="gpt-4o-mini"
    )
    
    # Create agent with base memory enabled
    agent = LLMAgent(
        jid="memory_agent@example.com",
        password="password123",
        provider=provider,
        agent_base_memory=True,  # This enables base memory automatically!
        system_prompt="""You are a helpful assistant with long-term memory capabilities.
        
        You have access to memory tools:
        - store_memory: Store important information for future use
        - search_memories: Search your memories for relevant information
        - list_memories: List memories by category
        
        Use these tools to learn and remember information across conversations.
        When you learn something new or important, store it in your memory.
        Before answering questions, search your memory for relevant information.
        
        Categories for memories:
        - fact: Concrete information (APIs, formats, configurations)
        - pattern: Behavioral patterns you observe
        - preference: User or system preferences
        - capability: Your own abilities or limitations
        """,
        verify_security=False
    )
    
    print("Agent created with base memory enabled!")
    print(f"Available tools: {[tool.name for tool in agent.get_tools()]}")
    
    # Start the agent
    await agent.start()
    
    # Simulate some learning interactions
    print("\n=== Demonstrating Memory Usage ===")
    
    # The agent would use these tools automatically during conversations
    # For demonstration, we'll show what tools are available
    
    # Find the memory tools
    store_tool = None
    search_tool = None
    list_tool = None
    
    for tool in agent.get_tools():
        if tool.name == "store_memory":
            store_tool = tool
        elif tool.name == "search_memories":
            search_tool = tool
        elif tool.name == "list_memories":
            list_tool = tool
    
    if store_tool and search_tool and list_tool:
        print("\n1. Storing some example memories...")
        
        # Store some example memories
        result1 = await store_tool.execute(
            category="fact",
            content="OpenAI API rate limit is 3000 RPM for GPT-4",
            context="Important for API usage planning"
        )
        print(f"Store result: {result1}")
        
        result2 = await store_tool.execute(
            category="preference",
            content="User prefers concise responses",
            context="Mentioned in conversation"
        )
        print(f"Store result: {result2}")
        
        result3 = await store_tool.execute(
            category="capability",
            content="I can process and analyze JSON data structures",
            context="Discovered during data analysis task"
        )
        print(f"Store result: {result3}")
        
        print("\n2. Searching memories...")
        
        # Search for API-related memories
        search_result = await search_tool.execute(query="API rate limit")
        print(f"Search result: {search_result}")
        
        print("\n3. Listing memories by category...")
        
        # List fact memories
        list_result = await list_tool.execute(category="fact")
        print(f"Facts: {list_result}")
        
        # List preference memories
        list_result = await list_tool.execute(category="preference")
        print(f"Preferences: {list_result}")
        
        # List capability memories
        list_result = await list_tool.execute(category="capability")
        print(f"Capabilities: {list_result}")
        
        print("\n4. Getting memory statistics...")
        
        # Get memory statistics
        stats = await agent.agent_base_memory.get_memory_stats()
        print(f"Memory stats: {stats}")
    
    print("\n=== Memory Demo Complete ===")
    print("In real usage, the LLM would automatically use these tools during conversations.")
    print("The agent now has persistent memory that survives restarts!")
    
    # Stop the agent
    await agent.stop()

if __name__ == "__main__":
    asyncio.run(main())