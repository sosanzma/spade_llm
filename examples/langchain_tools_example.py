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

from spade_llm.providers.open_ai_provider import OpenAILLMProvider
from spade_llm.behaviour import LLMBehaviour
from spade_llm.tools import LLMTool, LangChainToolAdapter
from spade_llm.utils import load_env_vars

# Import LangChain tools
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

# Enable detailed logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("example")


class SmartAgent(Agent):
    """An agent that uses LLMBehaviour with LangChain tools."""
    # Behavior will be injected from main()


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
                msg.set_metadata("type", "chat")  # Metadata for routing
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

    smart_agent = SmartAgent(smart_jid, smart_password)

    # Create OpenAI provider
    openai_provider = OpenAILLMProvider(
        api_key=openai_api_key,
        model="gpt-4o-mini"  # Use an appropriate model that supports function calling
    )

    # Create tools
    # 1. Native SPADE_LLM tool
    calculator_tool = LLMTool(
        name="calculator",
        description="Perform simple arithmetic calculations",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The arithmetic expression to calculate (e.g., '2 + 2 * 3')"
                }
            },
            "required": ["expression"]
        },
        func=lambda expression: eval(expression)
    )
    
    # 2. LangChain tools through the adapter
    search_tool = LangChainToolAdapter(
        DuckDuckGoSearchRun()
    )
    # Add more detailed description to help the LLM understand how to use it
    search_tool.description = "Search the web for current information using DuckDuckGo. Use this tool when you need to find recent information or current events."
    
    wikipedia_tool = LangChainToolAdapter(
        WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
    )
    # Add more detailed description to help the LLM understand how to use it
    wikipedia_tool.description = "Search Wikipedia for information about a specific topic. This is useful for getting detailed factual information about people, places, events, concepts, etc."

    # Create LLM behavior with tools
    llm_behavior = LLMBehaviour(
        llm_provider=openai_provider,
        termination_markers=["<TASK_COMPLETE>", "<END>", "<DONE>"],
        max_interactions_per_conversation=10,
        on_conversation_end=lambda conv_id, reason: print(f"Conversation {conv_id} ended: {reason}"),
        tools=[calculator_tool, search_tool, wikipedia_tool]
    )

    # Define a template for the SmartAgent
    smart_template = Template()
    smart_template.set_metadata("type", "chat")
    smart_agent.add_behaviour(llm_behavior, smart_template)
    
    # Start the SmartAgent
    await smart_agent.start()
    print(f"Smart agent {smart_jid} is running with tools:")
    print(f"- Calculator tool")
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
    print("- Calculator: For simple arithmetic")
    print("- Web Search: To search the internet")
    print("- Wikipedia: To query Wikipedia")
    print("\nType 'exit' to quit.\n")

    # Main interaction loop
    while True:
        user_input = await async_input("> ")
        if user_input.lower() == "exit":
            break
        human_agent.set("message_to_send", user_input)
        
        # Dar más tiempo para procesar herramientas complejas
        wait_time = 3.0  # 3 segundos para herramientas normales
        
        # Ajustar el tiempo de espera según la complejidad de la consulta
        if any(keyword in user_input.lower() for keyword in ["busca", "búsqueda", "internet", "google", "noticias"]):
            # Las búsquedas web pueden tardar significativamente más
            wait_time = 8.0  # 8 segundos para búsquedas web
            print(f"Esperando respuesta de búsqueda web (esto puede tardar hasta {wait_time} segundos)...")
        elif any(keyword in user_input.lower() for keyword in ["wikipedia", "definición", "quien es", "qué es"]):
            # Consultas de Wikipedia también pueden tardar
            wait_time = 6.0  # 6 segundos para consultas de Wikipedia
            print(f"Esperando respuesta de Wikipedia (esto puede tardar hasta {wait_time} segundos)...")
        
        await asyncio.sleep(wait_time)

    # Stop the agents
    await human_agent.stop()
    await smart_agent.stop()
    print("Agents stopped. Goodbye!")


if __name__ == "__main__":
    spade.run(main())
