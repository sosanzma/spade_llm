"""
Simple example of a SPADE agent that uses OpenAI to translate Spanish text to English.
This agent will:
1. Only translate from Spanish to English
2. Terminate the conversation and stop when it receives text that is not in Spanish
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
from spade_llm.context import ContextManager
from spade_llm.utils import load_env_vars

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("example")


class TranslatorAgent(Agent):
    """Agent that translates Spanish to English using LLMBehaviour from OpenAI."""
    # The behaviour is injected from main()


class HumanAgent(Agent):
    """Agent that acts as a human user that chats with the translator agent."""

    class SendBehaviour(CyclicBehaviour):
        """Behaviour for sending pending messages to the translator agent."""

        async def run(self):
            message_to_send = self.get("message_to_send")
            if message_to_send:
                translator_jid = self.get("translator_agent_jid")
                msg = Message(to=translator_jid)
                msg.body = message_to_send
                msg.set_metadata("type", "chat")  # Metadata for routing
                print(f"Human sending: '{message_to_send}' to {translator_jid}")
                await self.send(msg)
                # Clear the message to avoid resending
                self.set("message_to_send", None)
            await asyncio.sleep(0.1)

    class ReceiveBehaviour(CyclicBehaviour):
        """Behaviour for receiving and displaying messages from the translator agent."""

        async def run(self):
            response = await self.receive(timeout=0.1)
            if response:
                print(f"\nTranslation: '{response.body}'")
                
                # Check if this is a non-Spanish detection response
                if "This is not Spanish text" in response.body:
                    print("Non-Spanish text detected. Initiating shutdown...")
                    
                    # 1. Marcar una bandera global de terminación
                    self.agent.set("stop_agents", True)
                    
                    # 2. Crear una tarea asíncrona para detener el agente
                    # Esto permite que el método run() termine normalmente
                    self.agent.submit(self.agent.stop())
                    
                    # 3. Matar este comportamiento para que no siga procesando mensajes
                    self.kill()
                    return
                
                # Signal that we've received a response and are ready for new input
                self.agent.set("waiting_for_input", True)
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

    translator_jid = await async_input("Enter the Translator Agent JID: ")
    translator_password = getpass.getpass("Enter the Translator Agent password: ")

    translator_agent = TranslatorAgent(translator_jid, translator_password)

    # System prompt that instructs the LLM to translate Spanish to English
    # and to terminate the conversation when it detects non-Spanish input
    system_prompt = """
    You are a Spanish-to-English translator. Your task is to take Spanish text and translate it accurately to English.

    IMPORTANT RULES:
    1. ONLY respond with the English translation of the input. Do not include any special markers in your translation.
    2. Do NOT add any explanation or commentary to your translations.
    3. If the input is NOT in Spanish, ONLY THEN respond with exactly: "This is not Spanish text. [TRANSLATION_COMPLETE]"
       - The marker [TRANSLATION_COMPLETE] must only be included when detecting non-Spanish input.
       - NEVER include this marker when translating normal Spanish text.
    4. Keep the same tone, formality level, and style in your translations.
    5. For names, proper nouns, or specific terms, maintain their original form when appropriate.
    """

    # Create context manager with the system prompt
    context_manager = ContextManager(system_prompt=system_prompt)
    
    # Create OpenAI provider
    openai_provider = OpenAILLMProvider(api_key=openai_api_key)

    # Create LLM behavior with termination markers
    # Use a more unique termination marker that won't appear in regular translations
    llm_behavior = LLMBehaviour(
        llm_provider=openai_provider,
        context_manager=context_manager,
        termination_markers=["[TRANSLATION_COMPLETE]"],
        max_interactions_per_conversation=20,
        on_conversation_end=lambda conv_id, reason: print(f"Conversation {conv_id} terminated: {reason}")
    )

    # Define a template for routing (filtered by metadata "type":"chat")
    template = Template()
    template.set_metadata("type", "chat")
    translator_agent.add_behaviour(llm_behavior, template)

    # Start the TranslatorAgent
    await translator_agent.start()
    print(f"Translator agent {translator_jid} is running.")

    # Setup and start the HumanAgent (agent that simulates human user)
    human_jid = await async_input("Enter the Human Agent JID: ")
    human_password = getpass.getpass("Enter the Human Agent password: ")

    human_agent = HumanAgent(human_jid, human_password)
    human_agent.set("translator_agent_jid", translator_jid)
    human_agent.set("message_to_send", None)
    human_agent.set("waiting_for_input", True)  # Initialize to true so we prompt for input immediately
    human_agent.set("stop_agents", False)       # Flag to control agent shutdown

    # Add behaviours for sending and receiving messages
    send_behaviour = HumanAgent.SendBehaviour()
    receive_behaviour = HumanAgent.ReceiveBehaviour()
    human_agent.add_behaviour(send_behaviour)
    human_agent.add_behaviour(receive_behaviour)

    await human_agent.start()
    print(f"Human agent {human_jid} is running.")

    print("\nYou can now chat with the Spanish-to-English translator.")
    print("Type Spanish text to be translated to English.")
    print("Type non-Spanish text to terminate the conversation and stop the agents.")
    print("Type 'exit' to quit the program.\n")

    # Main interaction loop to read user input asynchronously
    while True:
        # Verificar si debemos detener los agentes
        if human_agent.get("stop_agents"):
            print("Shutting down the system...")
            break
        
        # Only prompt for input when we're ready (after receiving a response or at the start)
        if human_agent.get("waiting_for_input"):
            user_input = await async_input("> ")
            if user_input.lower() == "exit":
                break
            
            # Set the message to send and mark that we're no longer waiting for input
            human_agent.set("message_to_send", user_input)
            human_agent.set("waiting_for_input", False)
        
        # Small sleep to prevent CPU hogging
        await asyncio.sleep(0.1)

    # Al salir del bucle:
    await human_agent.stop()
    await translator_agent.stop()
    print("Agents stopped. Goodbye!")


if __name__ == "__main__":
    spade.run(main())
