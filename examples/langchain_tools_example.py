"""
Example demonstrating the use of LangChain tools within a SPADE_LLM agent.

This example shows how to use the LangChainToolAdapter to integrate
LangChain tools with SPADE_LLM agents.
"""

import asyncio
import getpass
import logging
import os

import spade

from spade.agent import Agent
from spade.template import Template
from spade.message import Message
from spade.behaviour import CyclicBehaviour

from spade_llm.agent import LLMAgent
from spade_llm.providers.open_ai_provider import OpenAILLMProvider
from spade_llm.tools import LangChainToolAdapter
from spade_llm.utils import load_env_vars

# Import LangChain tools
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

# Enable detailed logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("example")


class HumanAgent(Agent):
    """An agent that acts like a human user chatting with the LLM."""

    class SendBehaviour(CyclicBehaviour):
        """A behavior for sending pending messages to the smart agent."""

        async def run(self):
            message_to_send = self.get("message_to_send")
            if message_to_send:
                smart_jid = self.get("smart_agent_jid")
                msg = Message(to=smart_jid)
                msg.body = message_to_send
                msg.set_metadata("performative", "request")  # Metadata for routing
                print(f"Human sending: '{message_to_send}' to {smart_jid}")
                await self.send(msg)
                # Clear the message to avoid resending
                self.set("message_to_send", None)
            await asyncio.sleep(0.1)

    class ReceiveBehaviour(CyclicBehaviour):
        """A behavior for receiving and displaying messages from the smart agent."""

        async def on_start(self):
            print("Human agent receive behavior started. Waiting for messages...")

        async def run(self):
            # Aumentar aún más el timeout para permitir respuestas más lentas
            # Especialmente para herramientas que pueden tardar en procesar
            response = await self.receive(timeout=3.0)
            if response:
                print(f"\nResponse from smart agent: '{response.body}'")
                # Registrar información adicional para depuración
                logger.info(f"Received message from {response.sender} with thread: {response.thread}")
                
                # Enviar confirmación de recepción para mejorar la confiabilidad 
                if hasattr(self.agent, 'client') and self.agent.client:
                    try:
                        receipt = Message(to=str(response.sender))
                        receipt.body = "Message received"
                        receipt.set_metadata("type", "receipt")
                        receipt.thread = response.thread
                        await self.send(receipt)
                        logger.debug(f"Sent receipt to {response.sender}")
                    except Exception as e:
                        logger.warning(f"Could not send receipt: {e}")
            await asyncio.sleep(0.1)


async def async_input(prompt: str = "") -> str:
    """
    Run input() in a separate thread to avoid blocking the event loop.
    """
    return await asyncio.to_thread(input, prompt)


async def main():
    # Load environment variables from .env file
    env_vars = load_env_vars()
    
    # Get OpenAI API key from environment variables or ask the user
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        openai_api_key = await async_input("Enter your OpenAI API key: ")
        os.environ["OPENAI_API_KEY"] = openai_api_key

    smart_jid = await async_input("Enter Smart Agent JID: ")
    smart_password = getpass.getpass("Enter Smart Agent password: ")

    # Create LangChain tools
    search_tool = LangChainToolAdapter(
        DuckDuckGoSearchRun()
    )
    wikipedia_tool = LangChainToolAdapter(
        WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
    )

    # Create OpenAI provider
    openai_provider = OpenAILLMProvider(
        api_key=openai_api_key,
        model="gpt-4o-mini"  # Use an appropriate model that supports function calling
    )

    # Create LLM agent with all configuration in one step
    smart_agent = LLMAgent(
        jid=smart_jid,
        password=smart_password,
        provider=openai_provider,
        system_prompt=(
            "You are a helpful assistant with access to search tools. "
            "When the user asks a question that requires current information or facts, "
            "use the appropriate tool to find and provide accurate information."
        ),
        tools=[search_tool, wikipedia_tool],
        termination_markers=["<TASK_COMPLETE>", "<END>", "<DONE>"],
        max_interactions_per_conversation=10,
        on_conversation_end=lambda conv_id, reason: print(f"Conversation {conv_id} ended: {reason}")
    )
    
    # Start the LLMAgent
    await smart_agent.start()
    print(f"Smart agent {smart_jid} is running with tools:")
    print(f"- LangChain Search tool")
    print(f"- LangChain Wikipedia tool")

    # Setup and start the HumanAgent (agent simulating a human user)
    human_jid = await async_input("Enter Human Agent JID: ")
    human_password = getpass.getpass("Enter Human Agent password: ")

    human_agent = HumanAgent(human_jid, human_password)
    human_agent.set("smart_agent_jid", smart_jid)
    human_agent.set("message_to_send", None)

    # Add behaviors for sending and receiving messages
    send_behaviour = HumanAgent.SendBehaviour()
    receive_behaviour = HumanAgent.ReceiveBehaviour()
    
    # Template para recibir cualquier mensaje del agente inteligente
    receive_template = Template()
    receive_template.sender = smart_jid  # Solo recibir mensajes del agente inteligente
    
    human_agent.add_behaviour(send_behaviour)
    human_agent.add_behaviour(receive_behaviour, receive_template)
    
    await human_agent.start()
    print(f"Human agent {human_jid} is running.")

    print("\nYou can now chat with the smart agent. It can use:")
    print("- Web Search: To search the internet")
    print("- Wikipedia: To query Wikipedia")
    print("\nType 'exit' to quit.\n")

    # Main interaction loop
    while True:
        user_input = await async_input("> ")
        if user_input.lower() == "exit":
            break
        human_agent.set("message_to_send", user_input)
        
        # Dar tiempo para procesar herramientas complejas
        wait_time = 0.5  # Reduced since we'll wait in the loop
        await asyncio.sleep(wait_time)

    # Stop the agents
    await human_agent.stop()
    await smart_agent.stop()
    print("Agents stopped. Goodbye!")


if __name__ == "__main__":
    spade.run(main())
