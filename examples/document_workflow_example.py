"""
Document Creation Workflow Example

Multi-agent workflow for collaborative document creation:
Research -> Editor -> Reviewer -> Publisher
"""

import asyncio
import getpass
import os
from datetime import datetime
import spade

from spade_llm.agent import LLMAgent, ChatAgent
from spade_llm.routing import RoutingResponse
from spade_llm.providers.openai_compatible_provider import OpenAICompatibleProvider
from spade_llm.tools import LangChainToolAdapter
from spade_llm.utils import load_env_vars

# Import LangChain tools
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper


def review_router(msg, response, context):
    """Routes reviewer decisions to publisher or back to editor."""
    response_lower = response.lower()

    if "<task_complete>" in response_lower:
        return RoutingResponse(
            recipients="publisher@sosanzma",
            transform=lambda x: x.replace("<TASK_COMPLETE>", "").strip()
        )
    elif "major issues" in response_lower:
        return RoutingResponse(recipients=["researcher@sosanzma"])
    else:
        return RoutingResponse(recipients="editor@localhost")


async def main():
    # Load environment
    load_env_vars()
    api_key = os.environ.get("OPENAI_API_KEY") or input("OpenAI API key: ")

    XMPP_SERVER = input("you XMPP_SERVER: ")
    # Agent credentials
    agents_config = {
        "researcher": (f"researcher@{XMPP_SERVER}", "Research Agent"),
        "editor": (f"editor@{XMPP_SERVER}", "Editor Agent"),
        "reviewer": (f"reviewer@{XMPP_SERVER}", "Reviewer Agent"),
        "publisher": (f"publisher@{XMPP_SERVER}", "Publisher Agent"),
        "human": (f"human@{XMPP_SERVER}", "Human Agent")
    }

    # Get passwords
    passwords = {}
    for role, (jid, label) in agents_config.items():
        passwords[role] = getpass.getpass(f"{label} password: ")

    # Create provider
    provider = OpenAICompatibleProvider.create_openai(
        api_key=api_key,
        model="gpt-4o-mini"
    )


    # Create tools
    tools = [
        LangChainToolAdapter(DuckDuckGoSearchRun()),
        LangChainToolAdapter(WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper()))
    ]

    # Create agents
    agents = {}

    # Research Agent
    agents["researcher"] = LLMAgent(
        jid=agents_config["researcher"][0],
        password=passwords["researcher"],
        provider=provider,
        reply_to=agents_config["editor"][0],
        system_prompt="Research topics and create initial document drafts with title, sections, and conclusion.",
        tools=tools
    )

    # Editor Agent
    agents["editor"] = LLMAgent(
        jid=agents_config["editor"][0],
        password=passwords["editor"],
        provider=provider,
        reply_to=agents_config["reviewer"][0],
        system_prompt="Improve drafts for clarity, structure, and style. Return complete documents."
    )

    # Reviewer Agent
    agents["reviewer"] = LLMAgent(
        jid=agents_config["reviewer"][0],
        password=passwords["reviewer"],
        provider=provider,
        routing_function=review_router,
        system_prompt="Review documents. If approved: include '<TASK_COMPLETE>'. If not: specify changes.",
        termination_markers=["<TASK_COMPLETE>"]
    )

    # Publisher Agent (simple agent that saves files)
    class PublisherAgent(spade.agent.Agent):
        async def setup(self):
            class PublishBehaviour(spade.behaviour.CyclicBehaviour):
                async def run(self):
                    msg = await self.receive(timeout=1.0)
                    if msg:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"published_document_{timestamp}.txt"
                        with open(filename, 'w') as f:
                            f.write(msg.body)
                        print(f"✓ Document saved to: {filename}")
                    await asyncio.sleep(0.1)

            self.add_behaviour(PublishBehaviour())

    agents["publisher"] = PublisherAgent(
        agents_config["publisher"][0],
        passwords["publisher"]
    )

    # Human Agent (using ChatAgent)
    def display_callback(message, sender):
        print(f"\n📄 Document from {sender}:\n{message}\n")
        if "<TASK_COMPLETE>" in message:
            print("✅ Workflow completed!\n")

    agents["human"] = ChatAgent(
        jid=agents_config["human"][0],
        password=passwords["human"],
        target_agent_jid=agents_config["researcher"][0],
        display_callback=display_callback
    )

    # Start all agents
    for agent in agents.values():
        await agent.start()

    print("\n=== Document Creation Workflow ===")
    print("Research → Editor → Reviewer → Publisher")
    print("\nType document topics, 'exit' to quit\n")

    # Run interactive chat
    await agents["human"].run_interactive(
        input_prompt="Topic> ",
        exit_command="exit"
    )

    # Stop all agents
    for agent in agents.values():
        await agent.stop()

    print("Workflow stopped.")


if __name__ == "__main__":
    spade.run(main())