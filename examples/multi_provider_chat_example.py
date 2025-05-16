"""
Unified SPADE_LLM example that allows choosing between different LLM providers:
- OpenAI
- Ollama
- LLM Studio (local models)

Users can comment/uncomment the configuration for the provider they want to use.
"""

import asyncio
import getpass
import logging
import os
import spade

from spade_llm.agent import LLMAgent, ChatAgent
from spade_llm.providers import LLMProvider
from spade_llm.utils import load_env_vars

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("example")


async def main():
    # Load environment variables from .env file
    env_vars = load_env_vars()

    # Ask for XMPP server
    xmpp_server = input("Enter your XMPP server domain: ")

    # ==========================================
    # LLM PROVIDER CONFIGURATION
    # ==========================================
    # Uncomment the provider you want to use

    # --- OPTION 1: OpenAI ---
    # Get OpenAI API key from environment variables or ask the user
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        openai_api_key = input("Enter your OpenAI API key: ")
        os.environ["OPENAI_API_KEY"] = openai_api_key

    llm_provider_openai = LLMProvider.create_openai(
        api_key=openai_api_key,
        model="gpt-4o-mini",
        temperature=0.7
    )
    system_prompt = "You are a helpful AI assistant.  You should be concise but informative in your responses."

    # --- OPTION 2: Ollama with Gemma ---
    llm_provider_ollama = LLMProvider.create_ollama(
        model="gemma3:1b",
        temperature=0.7,
        base_url="http://localhost:11434/v1",
        timeout=120.0
    )
    system_prompt = "You are a helpful AI assistant.  You should be concise but informative in your responses."

    # --- OPTION 3: LLM Studio with local model ---
    LOCAL_BASE_URL = "http://localhost:1234/v1"
    LOCAL_MODEL = "llama-3.2-1b-instruct"

    llm_provider_lm_studio = LLMProvider.create_lm_studio(
        model=LOCAL_MODEL,
        base_url=LOCAL_BASE_URL
    )
    system_prompt = "You are a helpful AI assistant.  You should be concise but informative in your responses."

    # ==========================================
    # AGENT CONFIGURATION
    # ==========================================

    # Smart agent creation
    smart_jid = f"smart@{xmpp_server}"
    smart_password = getpass.getpass("Enter Smart Agent password: ")

    # Create the LLM agent with the selected provider
    smart_agent = LLMAgent(
        jid=smart_jid,
        password=smart_password,
        provider=llm_provider_ollama,
        system_prompt=system_prompt,
        max_interactions_per_conversation=10,
    )

    # Start the SmartAgent
    await smart_agent.start()
    print(f"Smart agent {smart_jid} is running.")

    # ChatAgent
    human_jid = f"human@{xmpp_server}"
    human_password = getpass.getpass("Enter Human Agent password: ")

    # Define a custom function to display responses
    def display_response(message: str, sender: str):
        print(f"\nSmart agent response: '{message}'")

    # Define a function to log when a message is sent
    def on_send(message: str, recipient: str):
        print(f"Human sending: '{message}' to {recipient}")

    # Create the enhanced ChatAgent
    chat_agent = ChatAgent(
        jid=human_jid,
        password=human_password,
        target_agent_jid=smart_jid,
        display_callback=display_response,
        on_message_sent=on_send,
        verbose=False
    )

    await chat_agent.start()
    print(f"Chat agent {human_jid} is running.")

    print("\nYou can now chat with the smart agent. Type 'exit' to quit.")

    await chat_agent.run_interactive()

    await chat_agent.stop()
    await smart_agent.stop()
    print("Agents stopped. Goodbye!")


if __name__ == "__main__":
    spade.run(main())