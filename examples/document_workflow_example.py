"""
Document Creation Workflow Example with SPADE_LLM.

This example demonstrates a multi-agent workflow for collaborative document creation:
1. Research Agent: Gathers information and creates initial drafts
2. Editor Agent: Improves and refines document drafts
3. Reviewer Agent: Reviews documents and approves or requests revisions
4. Publisher Agent: Publishes approved documents to file storage

The workflow shows how to implement:
- Sequential processing with the reply_to parameter
- Document revision loops
- Task completion with termination markers
- File storage for final documents
"""

import asyncio
import getpass
import logging
import os
from typing import Dict, Any
from datetime import datetime

import spade
from spade.agent import Agent
from spade.template import Template
from spade.message import Message
from spade.behaviour import CyclicBehaviour

from spade_llm import LLMAgent, RoutingResponse
from spade_llm.providers.open_ai_provider import OpenAILLMProvider
from spade_llm.tools import LangChainToolAdapter, LLMTool
from spade_llm.utils import load_env_vars

# Import LangChain tools
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper


# Enable detailed logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("document_workflow")



class RequestorAgent(Agent):
    """Agent that initiates the document creation workflow and receives the final result."""

    class SendRequestBehaviour(CyclicBehaviour):
        """Behavior for sending document creation requests."""

        async def run(self):
            message_to_send = self.get("message_to_send")
            if message_to_send:
                research_jid = self.get("research_agent_jid")
                msg = Message(to=research_jid)
                msg.body = message_to_send
                msg.set_metadata("performative", "request")
                msg.set_metadata("original_requester", str(self.agent.jid))
                msg.thread = f"doc_{hash(message_to_send)}"  # Create a unique thread ID
                
                print(f"Requestor sending: '{message_to_send}' to Research Agent")
                await self.send(msg)
                self.set("message_to_send", None)
            await asyncio.sleep(0.1)

    class ReceiveDocumentBehaviour(CyclicBehaviour):
        """Behavior for receiving the final document or updates."""

        async def run(self):
            response = await self.receive(timeout=1.0)
            if response:
                print("\n===== DOCUMENT RECEIVED =====")
                print(f"FROM: {response.sender}")
                print(f"THREAD: {response.thread}")
                print("\nCONTENT:")
                print(response.body)
                print("=============================\n")
                
                # If it contains a termination marker, the workflow is complete
                if "<TASK_COMPLETE>" in response.body:
                    print("\n🎉 Document workflow completed successfully! 🎉\n")
            await asyncio.sleep(0.1)


class PublisherAgent(Agent):
    """Agent that publishes approved documents to file storage."""

    class PublishDocumentBehaviour(CyclicBehaviour):
        """Behavior for receiving and publishing approved documents."""

        async def run(self):
            message = await self.receive(timeout=1.0)
            if message:
                print("\n===== PUBLISHER AGENT RECEIVED DOCUMENT =====")
                print(f"FROM: {message.sender}")
                print(f"THREAD: {message.thread}")
                print("\n--- Document Content ---")
                print(message.body)
                print("\n--- End of Document ---\n")
                
                # Save document to file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"published_document_{timestamp}.txt"
                
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"Document Published on: {datetime.now()}\n")
                        f.write(f"From: {message.sender}\n")
                        f.write(f"Thread: {message.thread}\n")
                        f.write("-" * 50 + "\n")
                        f.write(message.body)
                    
                    print(f"✅ Document successfully saved to: {filename}")
                except Exception as e:
                    print(f"❌ Error saving document: {e}")
                    
            await asyncio.sleep(0.1)


async def async_input(prompt: str = "") -> str:
    """Run input() in a separate thread to avoid blocking the event loop."""
    return await asyncio.to_thread(input, prompt)


def review_router(msg: Message, response: str, context: Dict[str, Any]) -> RoutingResponse:
    """
    Routing function for the reviewer agent.

    Determines whether a document should be:
    - Sent to publisher (if approved)
    - Sent back to editor (if needs revision)
    - Escalated to supervisor (if major issues)
    """
    response_lower = response.lower()

    if "<task_complete>" in response_lower:
        return RoutingResponse(
            recipients="publisher@sosanzma",
            transform=lambda x: x.replace("<TASK_COMPLETE>", "").strip()
        )
    elif "major issues" in response_lower or "rewrite" in response_lower:
        return RoutingResponse(
            recipients=["researcher@sosanzma"] )
    else:
        return RoutingResponse(
            recipients="editor@localhost")


async def setup_agents():
    """Create and configure all agents in the workflow."""
    # Load environment variables from .env file
    env_vars = load_env_vars()
    
    # Get OpenAI API key
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        openai_api_key = await async_input("Enter your OpenAI API key: ")
        os.environ["OPENAI_API_KEY"] = openai_api_key

    # Get JIDs for all agents
    requestor_jid = "requestor@sosanzma"
    requestor_password = getpass.getpass("Enter Requestor Agent password: ")
    
    research_jid = "researcher@sosanzma"
    research_password = getpass.getpass("Enter Research Agent password: ")
    
    editor_jid = "editor@sosanzma"
    editor_password = getpass.getpass("Enter Editor Agent password: ")
    
    reviewer_jid = "reviewer@sosanzma"
    reviewer_password = getpass.getpass("Enter Reviewer Agent password: ")
    
    publisher_jid = "publisher@sosanzma"
    publisher_password = getpass.getpass("Enter Publisher Agent password: ")

    
    # Create OpenAI provider (shared by all agents)
    openai_provider = OpenAILLMProvider(
        api_key=openai_api_key,
        model="gpt-4o-mini"  # Or other appropriate model
    )

    # Create LangChain tools for Research Agent
    search_tool = LangChainToolAdapter(DuckDuckGoSearchRun())
    wikipedia_tool = LangChainToolAdapter(WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper()))

    # Create Research Agent
    research_agent = LLMAgent(
        jid=research_jid,
        password=research_password,
        provider=openai_provider,
        reply_to=editor_jid,
        system_prompt=(
            "You are a research agent responsible for creating initial document drafts. "
            "When given a topic or request, research it thoroughly and create a well-structured "
            "initial draft using search and Wikipedia tools to gather accurate information. "
            "Your response should be a complete, well-formatted document with: "
            "1. A clear title and introduction "
            "2. Several main sections with factual information "
            "3. A conclusion summarizing key points "
            "Format the document using Markdown with proper headings and structure. "
            "The entire document should be comprehensive but concise. "
            "Your entire response will be forwarded directly to the editor agent for refinement."
        ),
        tools=[search_tool, wikipedia_tool]
    )

    # Create Editor Agent
    editor_agent = LLMAgent(
        jid=editor_jid,
        password=editor_password,
        provider=openai_provider,
        reply_to=reviewer_jid,  # Siguiente en el flujo
        system_prompt=(
            "You are an editor agent responsible for improving document drafts. "
            "You will receive complete document drafts from the research team. "
            "Your job is to enhance the structure, clarity, readability, and style, "
            "while keeping the factual content intact. Make the document more engaging "
            "and professional. Pay special attention to: "
            "1. Improving the flow and organization "
            "2. Enhancing clarity and readability "
            "3. Fixing any grammatical or stylistic issues "
            "4. Making the document more engaging "
            "Your entire response will be the complete, improved document in Markdown format."
        )
    )

    # Create Reviewer Agent
    reviewer_agent = LLMAgent(
        jid=reviewer_jid,
        password=reviewer_password,
        provider=openai_provider,
        routing_function=review_router,
        system_prompt=(
            "You are a reviewer agent responsible for evaluating document quality. "
            "You will receive edited documents that need final review. "
            "Examine documents for overall quality. "
            "1. If approved: include the full article and  '<TASK_COMPLETE>' at the beginning  in your response "
            "2. If minor issues: mention specific changes needed "
            "3. If major issues: use 'major issues' or 'rewrite' in response"
            "Important : each revision will increase the cost of the production, just suggest a revision when"
            "a relevant error is present the document, otherwise mak it as complete"

        ),
        termination_markers=["<TASK_COMPLETE>", "<END>", "<DONE>"],
        )


    # Create Requestor Agent (user proxy)
    requestor_agent = RequestorAgent(requestor_jid, requestor_password)
    requestor_agent.set("research_agent_jid", research_jid)
    requestor_agent.set("message_to_send", None)
    
    # Add behaviors for sending requests and receiving documents
    send_behaviour = RequestorAgent.SendRequestBehaviour()
    receive_behaviour = RequestorAgent.ReceiveDocumentBehaviour()
    
    # Template to receive final documents
    receive_template = Template()
    
    requestor_agent.add_behaviour(send_behaviour)
    requestor_agent.add_behaviour(receive_behaviour, receive_template)

    # Create Publisher Agent
    publisher_agent = PublisherAgent(publisher_jid, publisher_password)
    
    # Add behavior for publishing documents
    publish_behaviour = PublisherAgent.PublishDocumentBehaviour()
    publisher_agent.add_behaviour(publish_behaviour)

    # Create and return all the agents
    return {
        "requestor": requestor_agent,
        "research": research_agent,
        "editor": editor_agent,
        "reviewer": reviewer_agent,
        "publisher": publisher_agent
    }



async def main():
    # Setup all agents
    agents = await setup_agents()
    
    # Start all agents
    for role, agent in agents.items():
        await agent.start()
        print(f"{role.capitalize()} agent {agent.jid} is running.")
        await asyncio.sleep(1)


    
    print("\n===== DOCUMENT CREATION WORKFLOW =====")
    print("Research Agent → Editor Agent → Reviewer Agent → Publisher Agent")
    print("         ↑                           ↓")
    print("         ← ← ← ← ← ← ← ← ← ← ← ← ← ←")
    print("=========================================\n")
    
    print("Enter document requests. Type 'exit' to quit.\n")
    
    # Main interaction loop
    while True:
        user_input = await async_input("Document request> ")
        if user_input.lower() == "exit":
            break
            
        request = (
            f"Please create a document about: {user_input}\n\n"
            f"Include an introduction, main sections with key information, "
            f"and a conclusion. The document should be informative and well-structured."
        )
        
        agents["requestor"].set("message_to_send", request)
        await asyncio.sleep(0.5)  # Give time for message to be sent

    # Stop all agents
    for role, agent in agents.items():
        await agent.stop()
        print(f"{role.capitalize()} agent stopped.")

    print("Workflow terminated. Goodbye!")


if __name__ == "__main__":
    spade.run(main())
