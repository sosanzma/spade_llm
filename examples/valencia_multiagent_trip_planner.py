"""
Valencia Multi-Agent Trip Planner with Shared Memory

Advanced multi-agent workflow with conditional routing and shared MCP memory:
Weather Check → Conditional Routing → Activity Planning → Airbnb Search → Final Plan

Agents:
- Weather Agent: Checks weather and routes to appropriate activity planner
- Route Planner: Plans bike routes if weather is good
- TicketMaster Agent: Finds events if weather is bad
- Airbnb Agent: Finds accommodation near planned activities
- Plan Maker: Creates final comprehensive plan from shared memory

MCP Servers:
- Valencia Smart City (weather, bike stations)
- TicketMaster (event search)
- Airbnb (accommodation search)
- Shared Memory (coordination between agents)
"""

import asyncio
import getpass
import os
from datetime import datetime
import spade
import logging
import json

from spade_llm.agent import LLMAgent, ChatAgent
from spade_llm.routing import RoutingResponse
from spade_llm.providers import LLMProvider
from spade_llm.mcp import StdioServerConfig, SseServerConfig
from spade_llm.utils import load_env_vars

PROMPT_WEATHER= """You are a Valencia trip planner that first extracts trip information, then analyzes weather to determine activities.
        
        Your workflow:
        1. FIRST, extract trip details from the user message:
           - Number of people/travelers
           - Check-in date (convert to YYYY-MM-DD format)
           - Check-out date (convert to YYYY-MM-DD format)
           - Budget (if mentioned)
           - Any preferences (if mentioned)
        
        2. Calculate the number of nights
        
        3. Store trip information in shared memory using 'store' tool with key "trip_info"
           Store as JSON string:
           {
               "num_travelers": X,
               "check_in": "YYYY-MM-DD",
               "check_out": "YYYY-MM-DD",
               "nights": X,
               "budget_per_night": "amount or flexible",
               "preferences": "any mentioned"
           }
        
        4. Check current Valencia weather using the weather API
        
        5. Store weather data in shared memory using 'store' tool with key "weather_data"
           Store as JSON string:
           {
               "temperature": X,
               "conditions": "description",
               "wind_kmh": X,
               "humidity": X,
               "assessment": "GOOD/POOR for cycling"
           }
        
        6. Route to appropriate activity planner based on weather
        
        Weather evaluation criteria:
        - GOOD for cycling: Temperature 15-30°C, no rain, wind < 30 km/h
        - POOR for cycling: Rain, extreme temperatures, high wind
        
        RESPONSE FORMAT:
        === TRIP INFORMATION ===
        ✅ Travelers: [X] people
        ✅ Check-in: [date]
        ✅ Check-out: [date]
        ✅ Duration: [X] nights
        ✅ Budget: [amount/flexible]
        
        === VALENCIA WEATHER ANALYSIS ===
        
        Current Conditions:
        - Temperature: [X]°C
        - Weather: [clear/rain/cloudy/etc]
        - Wind: [X] km/h 
        - Humidity: [X]%
        
        Weather Assessment: [GOOD/POOR for outdoor activities]
        
        [Then add ONE of these markers at the end:]
        - If weather is GOOD for cycling: "Perfect weather for exploring Valencia by bike! <BIKE_WEATHER>"
        - If weather is POOR for cycling: "Better to enjoy indoor activities today. <INDOOR_WEATHER>"
        """

PROMPT_ROUTE_PLANNER="""You are a Valencia bike route specialist. You receive requests when weather is good for cycling.
        
        Your workflow:
        1. Retrieve trip information from shared memory using 'retrieve' tool with key "trip_info"
        2. Retrieve weather data from shared memory using 'retrieve' tool with key "weather_data"
        3. Find interesting Valencia locations suitable for cycling, considering the trip duration
        4. Check ValenBici stations near these locations
        5. Plan a comprehensive bike route with start and end stations
        6. Store the route plan in shared memory with key "activity_plan"
        
        Focus on these places to start or end:
        - Ayuntamiento 
        - Xativa
        - Plaza de la Virgen
        
        IMPORTANT: 
        - The route should START from a ValenBici station with available bikes
        - Consider the number of travelers when checking bike availability
        - Plan activities appropriate for the trip duration
        
        Store in memory a JSON with:
        {
            "activity_type": "cycling",
            "num_travelers": X,
            "start_location": "station name and address",
            "key_locations": ["list of stops with addresses"],
            "total_distance": X,
            "duration_hours": X,
            "bike_availability": X,
            "recommended_for_days": X
        }
        
        RESPONSE FORMAT:
        === VALENCIA BIKE ROUTE PLAN ===
        
        Trip Details:
        - Travelers: [X] people
        - Duration: [X] days/nights
        - Weather conditions: [summary from memory]
        
        RECOMMENDED BIKE ROUTE:
        
        Starting Point: [ValenBici station with address]
        - Bikes available: [X] (enough for [X] travelers)
        - Walking distance from city center: [X] min
        
        Route Highlights:
        1. [Location] - [description]
        2. [Location] - [description]
        3. [Location] - [description]
        
        Total distance: [X] km
        Estimated duration: [X] hours
        
        The Airbnb agent will now find accommodation near the starting point.
        """
PROMPT_TICKET_MASTER = """You are a Valencia event specialist. You receive requests when weather is poor for outdoor activities.
        
        Your workflow:
        1. Retrieve trip information from shared memory using 'retrieve' tool with key "trip_info"
        2. Retrieve weather data from shared memory using 'retrieve' tool with key "weather_data"
        3. Search for events in Valencia during the stay period (check-in to check-out dates)
        4. Select the best 2-3 events considering variety, dates, and number of travelers
        5. Store the event plan in shared memory with key "activity_plan"
        
        IMPORTANT:
        - Only suggest events happening during the actual stay dates
        - Consider group size when recommending events
        - Mix different types of events for variety
        
        Focus on finding:
        - Concerts or music events
        - Theater or cultural shows
        - Sports events (basketball, football)
        - Family-friendly events if appropriate
        
        Store in memory a JSON with:
        {
            "activity_type": "events",
            "num_travelers": X,
            "main_event": {
                "name": "event name",
                "venue": "venue name",
                "address": "full address",
                "date": "YYYY-MM-DD",
                "time": "HH:MM",
                "price_range": "€X-Y per person"
            },
            "alternative_events": [
                {
                    "name": "event name",
                    "venue": "venue",
                    "date": "YYYY-MM-DD",
                    "price": "€X-Y"
                }
            ],
            "venue_locations": ["list of addresses for Airbnb search"]
        }
        
        RESPONSE FORMAT:
        === VALENCIA INDOOR EVENTS ===
        
        Trip Details:
        - Dates: [check-in] to [check-out] ([X] nights)
        - Travelers: [X] people
        - Weather: [summary - explaining why indoor activities are recommended]
        
        RECOMMENDED MAIN EVENT:
        Event: [name]
        Venue: [venue name and address]
        Date/Time: [when] (Day [X] of your trip)
        Price range: €[X-Y] per person (Total for [X] people: €[total])
        Description: [brief description]
        
        ALTERNATIVE OPTIONS:
        1. [Event name] at [venue] - [date] - €[X-Y] pp
        2. [Event name] at [venue] - [date] - €[X-Y] pp
        
        The Airbnb agent will now find accommodation near these venues.
        """
PROMPT_AIRBNB="""You are a Valencia accommodation specialist. You find the perfect Airbnb based on planned activities.
        
        Your workflow:
        1. FIRST retrieve trip information using 'retrieve' tool with key "trip_info" - CRITICAL!
           Extract: check_in, check_out, num_travelers, budget_per_night
        2. Retrieve activity plan from shared memory using 'retrieve' tool with key "activity_plan"
        3. Search for Airbnb accommodations with EXACT parameters:
           - Check-in date: [from trip_info]
           - Check-out date: [from trip_info]
           - Number of guests: [from trip_info]
           - Location: Near planned activities
           - Budget: [from trip_info if available]
        4. Select the best option considering location, price, and capacity
        5. Store COMPLETE accommodation details in shared memory with key "accommodation"
        
        CRITICAL SEARCH PARAMETERS:
        - MUST use exact check-in and check-out dates
        - MUST accommodate the exact number of travelers
        
        Location priorities:
        - For CYCLING: Near the bike route starting point or city center
        - For EVENTS: Near the main event venue or with good transport
        
        Store in memory a JSON with ALL these fields:
        {
            "name": "property name",
            "location": "full address",
            "url": "MANDATORY - full booking link",
            "check_in": "YYYY-MM-DD",
            "check_out": "YYYY-MM-DD",
            "nights": X,
            "guests_capacity": X,
            "price_per_night": X,
            "total_price": X,
            "rating": X,
            "amenities": ["list"],
            "distance_to_activity": "X km or X min walk"
        }
        
        RESPONSE FORMAT:
        === ACCOMMODATION SELECTION ===
        
        Search Parameters:
        - Check-in: [date]
        - Check-out: [date]
        - Nights: [X]
        - Guests: [X] people
        - Location priority: [activity location]
        
        SELECTED APARTMENT:
        Name: [name]
        Location: [address, neighborhood]
        
        Pricing:
        - €[X] per night
        - Total: €[Y] for [X] nights
        - For [X] guests
        
        Rating: [X]/5 ([Y] reviews)
        
        🔗 BOOKING LINK: [ACTUAL URL - MANDATORY]
        
        Why this choice:
        - Distance to [activity]: [specific distance/time]
        - Accommodates [X] people comfortably
        - [Other relevant factors]
        
        The Plan Maker will now compile the complete Valencia experience.
        """
PROMPT_PLANN_MAKER="""You are the Valencia trip plan compiler. You create a beautiful, comprehensive final plan from all stored information.
        
        Your workflow:
        1. Retrieve ALL data from shared memory (CRITICAL - all 4 keys):
           - "trip_info" - MUST have dates, travelers, budget
           - "weather_data" - Weather conditions
           - "activity_plan" - Planned activities (cycling or events)
           - "accommodation" - MUST have the booking URL
           
        2. VALIDATE critical information:
           - Check-in and check-out dates exist
           - Number of travelers is specified
           - Accommodation URL is present
           - Total nights calculated correctly
           
        3. Create comprehensive plan with ALL details
        4. Store the complete final plan in memory with key "final_plan"
        
        The plan MUST include:
        - Clear trip dates and duration
        - Number of travelers prominently displayed
        - Weather impact on activities
        - Detailed activity information
        - Complete accommodation details WITH BOOKING LINK
        - Accurate budget calculations based on actual nights
        
        RESPONSE FORMAT:
        🌟 === YOUR VALENCIA EXPERIENCE PLAN === 🌟
        Generated on: [date]
        
        📍 DESTINATION: Valencia, Spain
        
        👥 TRIP DETAILS
        - Travelers: [X] people
        - Check-in: [date] 
        - Check-out: [date]
        - Duration: [X] days / [X] nights
        
        🌤️ WEATHER FORECAST
        [Detailed weather conditions]
        Impact on your trip: [How weather shaped the plan]
        
        [Then, based on activity type:]
        
        [IF CYCLING:]
        🚴 VALENCIA BY BIKE ADVENTURE
        
        Perfect for: [X] cyclists
        
        Starting Point: [ValenBici station]
        - Address: [full address]
        - Bikes available: [X] (enough for your group)
        - Pick up your bikes here!
        
        Your Route ([X] km total):
        📍 Stop 1: [Place] - [What to see/do]
        📍 Stop 2: [Place] - [What to see/do]
        [etc...]
        
        Duration: [X] hours (including stops)
        Difficulty: [Easy/Moderate]
        Best time to start: [recommendation based on weather]
        
        [IF EVENTS:]
        🎭 VALENCIA CULTURAL EXPERIENCE
        
        For your group of [X] people
        
        Main Event:
        📅 [Event name]
        📍 Venue: [name and address]
        🕐 Date & Time: [when] (Day [X] of your trip)
        💶 Tickets: €[X-Y] per person (Total for [X]: €[total])
        
        Additional Options:
        [List other events with details and group pricing]
        
        🏨 YOUR ACCOMMODATION
        
        [Property name]
        📍 Address: [full address, neighborhood]
        
        Booking Details:
        - Check-in: [date]
        - Check-out: [date]  
        - Nights: [X]
        - Capacity: [X] guests
        
        🔗 BOOK NOW: [ACTUAL AIRBNB URL - CRITICAL!]
        
        💶 Price: €[X] per night
        💶 TOTAL: €[Y] for [X] nights
        ⭐ Rating: [X]/5 ([Y] reviews)
        ✨ Amenities: [list key amenities]
        🚶 Distance to activities: [specific distance]
        
        💰 BUDGET SUMMARY (for [X] people)
        - Accommodation: €[X] ([X] nights)
        - Activities: €[Y] [bike rental OR event tickets]
        - Estimated meals: €[Z] (€[per person/day] x [X] people x [X] days)
        - Local transport: €[A]
        - Total (estimated): €[TOTAL]
        
        📝 BOOKING CHECKLIST
        ✅ Book Airbnb: [URL again for emphasis]
        ✅ [Activity-specific booking needs]
        ✅ Check ValenBici app for bike availability (if cycling)
        
        ¡Disfruta Valencia! 🇪🇸
        
        ---
        """
PROMPT_OUTPUT = """You are a professional travel document creator. You receive comprehensive Valencia trip plans and create beautifully formatted markdown documents.

Your workflow:
1. Receive the final trip plan from the Plan Maker
2. Parse and extract ALL key information including:
   - Trip dates (check-in/check-out)
   - Number of travelers
   - Accommodation booking URL
   - Activity details
   - Budget breakdown
3. Create a professional markdown document with proper structure
4. Use the save_markdown_file tool to save the document

CRITICAL: The markdown MUST include:
- Trip dates prominently displayed
- Number of travelers
- Accommodation booking link as clickable markdown link
- Complete budget with calculations

## Document Structure:
```markdown
# 🌟 Valencia Experience Plan - [Check-in] to [Check-out]

## 👥 Trip Overview
- **Travelers**: [X] people
- **Check-in**: [date]
- **Check-out**: [date]
- **Duration**: [X] nights

## 🌤️ Weather Forecast
[Details]

## [🚴 or 🎭] Activities
[Detailed activity plan]

## 🏨 Accommodation
**[Property Name]**
- **Address**: [full address]
- **[Book Now on Airbnb](actual-url-here)** ← CLICKABLE LINK
- **Price**: €[X] per night (Total: €[Y] for [X] nights)
- **Rating**: ⭐ [X]/5

## 💰 Budget Summary
| Category | Cost | Details |
|----------|------|---------|
| Accommodation | €[X] | [X] nights × €[Y] |
| Activities | €[X] | [details] |
| Meals (est.) | €[X] | €[Y] × [people] × [days] |
| **TOTAL** | **€[X]** | For [X] people |

## 📝 Booking Checklist
- [ ] Book accommodation: [Link text](url)
- [ ] [Other items]
```

RESPONSE FORMAT:
=== CREATING VALENCIA TRAVEL DOCUMENT ===

Processing the comprehensive travel plan...
Extracting trip dates: [check-in] to [check-out]
Formatting for [X] travelers...

[Use save_markdown_file tool with the complete markdown content]

=== PROFESSIONAL VALENCIA TRAVEL DOCUMENT CREATED ===

📋 Document: valencia_trip_plan_[timestamp].md
✅ Status: Successfully created and formatted
✅ Includes: Clickable Airbnb booking link
✅ Trip dates: [check-in] to [check-out]

The comprehensive Valencia travel plan has been professionally formatted and saved!
"""

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger("spade_llm").setLevel(logging.INFO)


def weather_routing_function(msg, response, context):
    """Routes based on weather conditions to appropriate activity planner."""
    domain = str(msg.sender).split('@')[1]
    response_lower = response.lower()
    
    if "<bike_weather>" in response_lower:
        # Good weather - route to bike route planner
        return RoutingResponse(
            recipients=f"routeplanner@{domain}",
            transform=lambda x: x.replace("<BIKE_WEATHER>", "").strip(),
            metadata={"weather": "good", "activity": "cycling"}
        )
    elif "<indoor_weather>" in response_lower:
        # Bad weather - route to event finder
        return RoutingResponse(
            recipients=f"ticketmaster@{domain}",
            transform=lambda x: x.replace("<INDOOR_WEATHER>", "").strip(),
            metadata={"weather": "poor", "activity": "indoor"}
        )
    else:
        # Default to route planner if uncertain
        return RoutingResponse(recipients=f"routeplanner@{domain}")


async def main():
    print("🌦️ === Valencia Multi-Agent Trip Planner with Shared Memory === 🌦️\n")
    
    # Load environment
    load_env_vars()
    api_key = os.environ.get("OPENAI_API_KEY") or input("OpenAI API key: ")
    UPV_OLLAMA_BASE_URL =  os.environ.get("UPV_OLLAMA_BASE_URL")
    # XMPP server configuration
    XMPP_SERVER = input("XMPP server domain: ")
    
    # Agent credentials configuration
    agents_config = {
        "weather": (f"weather@{XMPP_SERVER}", "Weather Analysis Agent"),
        "routeplanner": (f"routeplanner@{XMPP_SERVER}", "Bike Route Planner Agent"),
        "ticketmaster": (f"ticketmaster@{XMPP_SERVER}", "Event Finder Agent"),
        "airbnb": (f"airbnb@{XMPP_SERVER}", "Airbnb Search Agent"),
        "planmaker": (f"planmaker@{XMPP_SERVER}", "Final Plan Maker Agent"),
        "output": (f"output@{XMPP_SERVER}", "Output Agent"),
        "human": (f"human@{XMPP_SERVER}", "Human Interface Agent")

    }
    
    # Get passwords for all agents
    passwords = {}
    for role, (jid, label) in agents_config.items():
        passwords[role] = getpass.getpass(f"{label} password: ")
    
    # Create LLM provider


    provider = LLMProvider.create_ollama(
        model='qwen2.5:latest',
        base_url=UPV_OLLAMA_BASE_URL,
        temperature=0.7,
        timeout=60.0  # Timeout generoso para modelos grandes
    )
    provider = LLMProvider.create_openai(
        api_key=api_key,
        model="gpt-4.1-mini-2025-04-14",
        temperature=0.7
    )

    # MCP Server configurations
    print("\n📡 Configuring MCP servers...")
    
    # Shared Memory MCP (all agents will use this)
    memory_mcp = StdioServerConfig(
        name="SharedMemory",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-memory"],
        env=  {
        "MEMORY_FILE_PATH": "C:/Users/manel/PycharmProjects/spade_llm/memory.json"
    },
        cache_tools=True
    )
    
    # Valencia Smart City MCP (weather + bike stations)
    valencia_mcp = StdioServerConfig(
        name="ValenciaSmart",
        command="C:/Users/manel/PycharmProjects/SmartCityMCP/.venv/Scripts/python.exe",
        args=["C:/Users/manel/PycharmProjects/SmartCityMCP/valencia_traffic_mcp.py"],
        cache_tools=True
    )
    
    # TicketMaster MCP (SSE-based)
    ticketmaster_mcp = StdioServerConfig(
        name="TicketMaster",
        command="npx",
        args=["-y", "@delorenj/mcp-server-ticketmaster"],
        env={"TICKETMASTER_API_KEY": "GcNooYKBKFedAB5tvi2jvWfaHB49CF1T"}
    )
    
    # Airbnb MCP
    airbnb_mcp = StdioServerConfig(
        name="AirbnbSearch",
        command="npx",
        args=["-y", "@openbnb/mcp-server-airbnb", "--ignore-robots-txt"],
        cache_tools=True
    )
    # Custom tool for markdown file creation
    from spade_llm.tools import LLMTool
    
    def save_markdown_file(content: str, filename: str = None) -> str:
        """
        Save content as a markdown file.
        
        Args:
            content: The markdown content to save
            filename: Optional filename (will generate timestamp-based name if not provided)
        
        Returns:
            Success message with filename
        """
        from datetime import datetime
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"valencia_trip_plan_{timestamp}.md"
        
        # Ensure .md extension
        if not filename.endswith('.md'):
            filename += '.md'
            
        # Save to examples directory
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"✅ Markdown file successfully saved as: {filename}"
        except Exception as e:
            return f"❌ Error saving file: {str(e)}"
    
    # Create the custom tool
    markdown_save_tool = LLMTool(
        name="save_markdown_file",
        description="Save travel plan content as a markdown file",
        parameters={
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The markdown content to save to file"
                },
                "filename": {
                    "type": "string",
                    "description": "Optional filename (without extension). If not provided, generates timestamp-based name"
                }
            },
            "required": ["content"]
        },
        func=save_markdown_file
    )

    
    # Create agents dictionary
    agents = {}
    
    # 1. Weather Agent - First step in the workflow
    print("🌤️ Creating Weather Analysis Agent...")
    agents["weather"] = LLMAgent(
        jid=agents_config["weather"][0],
        password=passwords["weather"],
        provider=provider,
        routing_function=weather_routing_function,
        system_prompt=PROMPT_WEATHER,
        mcp_servers=[valencia_mcp, memory_mcp]
    )
    
    # 2. Route Planner Agent - For good weather
    print("🚴 Creating Bike Route Planner Agent...")
    agents["routeplanner"] = LLMAgent(
        jid=agents_config["routeplanner"][0],
        password=passwords["routeplanner"],
        provider=provider,
        reply_to=agents_config["airbnb"][0],
        system_prompt=PROMPT_ROUTE_PLANNER,
        mcp_servers=[valencia_mcp, memory_mcp]
    )
    
    # 3. TicketMaster Agent - For bad weather
    print("🎭 Creating Event Finder Agent...")
    agents["ticketmaster"] = LLMAgent(
        jid=agents_config["ticketmaster"][0],
        password=passwords["ticketmaster"],
        provider=provider,
        reply_to=agents_config["airbnb"][0],
        system_prompt=PROMPT_TICKET_MASTER,
        mcp_servers=[ticketmaster_mcp, memory_mcp]
    )
    
    # 4. Airbnb Agent - Finds accommodation based on planned activities
    print("🏨 Creating Airbnb Search Agent...")
    agents["airbnb"] = LLMAgent(
        jid=agents_config["airbnb"][0],
        password=passwords["airbnb"],
        provider=provider,
        reply_to=agents_config["planmaker"][0],
        system_prompt=PROMPT_AIRBNB,
        mcp_servers=[airbnb_mcp, memory_mcp]
    )
    
    # 5. Plan Maker Agent - Creates final comprehensive plan
    print("📋 Creating Final Plan Maker Agent...")
    agents["planmaker"] = LLMAgent(
        jid=agents_config["planmaker"][0],
        password=passwords["planmaker"],
        reply_to=agents_config["output"][0],
        provider=provider,
        system_prompt=PROMPT_PLANN_MAKER,
        mcp_servers=[memory_mcp],
        termination_markers=["Plan stored in shared memory"]
    )
    # 6. Output Agent (for final plan storage as markdown)
    print("📄 Creating Output Agent...")

    agents["output"] = LLMAgent(
        jid=agents_config["output"][0],
        password=passwords["output"],
        provider=provider,
        tools=[markdown_save_tool],
        mcp_servers=[memory_mcp],
        system_prompt=PROMPT_OUTPUT,
        termination_markers=["document ready", "Successfully created and formatted"]
    )
    # 6. Human Interface Agent
    print("👤 Creating Human Interface Agent...")

    
    agents["human"] = ChatAgent(
        jid=agents_config["human"][0],
        password=passwords["human"],
        target_agent_jid=agents_config["weather"][0]
    )
    
    # Start all agents
    print("\n🚀 Starting all agents...")
    for name, agent in agents.items():
        await agent.start()
        print(f"✅ {name.capitalize()} agent started")
    
    print("\n" + "="*70)
    print("🌦️ VALENCIA INTELLIGENT TRIP PLANNER 🌦️")
    print("="*70)
    print("\nThis system will:")
    print("1. Check current Valencia weather")
    print("2. Recommend cycling routes (good weather) OR events (bad weather)")
    print("3. Find perfect accommodation near your activities")
    print("4. Create a comprehensive trip plan")
    print("\n" + "="*70)
    print("✅ Any preferences (optional)")
    print("\n⚠️  IMPORTANT: Missing information will be filled with defaults!")
    print("\n📌 EXAMPLE INPUT:")
    print("'2 people visiting Valencia from 2025/05/29 to 2025/05/30 with budget €100-150 per night'")
    print("\nType 'exit' to quit\n")
    print("-"*70)
    
    # Run interactive workflow
    await agents["human"].run_interactive(
        input_prompt="🧳 Your trip details> ",
        exit_command="exit",
        response_timeout=90.0  # Longer timeout for complex multi-agent processing
    )
    
    # Stop all agents
    print("\n🔄 Stopping all agents...")
    for name, agent in agents.items():
        await agent.stop()
        print(f"✅ {name.capitalize()} agent stopped")
    
    print("\n👋 Valencia Multi-Agent Trip Planner completed. ¡Buen viaje!")


if __name__ == "__main__":
    spade.run(main())
