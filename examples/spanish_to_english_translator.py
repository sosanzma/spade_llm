"""
Spanish to English Translator Example

Demonstrates a SPADE agent that translates Spanish text to English using OpenAI.
The agent terminates when it receives non-Spanish text.
"""

import asyncio
import getpass
import os
import spade
from spade_llm.agent import LLMAgent, ChatAgent
from spade_llm.providers.openai_compatible_provider import OpenAICompatibleProvider
from spade_llm.utils import load_env_vars

TRANSLATOR_PROMPT = """
You are a Spanish-to-English translator. Translate Spanish text to English.

Rules:
1. Only respond with the English translation
2. If input is NOT Spanish, respond: "This is not Spanish text. [DONE]"
3. Keep the same tone and style in translations
"""


async def main():
    # Load environment
    load_env_vars()

    # Get API key
    api_key = os.environ.get("OPENAI_API_KEY") or input("OpenAI API key: ")

    # Translator agent setup
    translator_jid = input("Translator agent JID: ")
    translator_password = getpass.getpass("Translator password: ")

    translator = LLMAgent(
        jid=translator_jid,
        password=translator_password,
        provider=OpenAICompatibleProvider.create_openai(
            api_key=api_key,
            model="gpt-4o-mini",
            temperature=0.3
        ),
        system_prompt=TRANSLATOR_PROMPT,
        termination_markers=["[DONE]"]
    )

    await translator.start()
    print(f"Translator started: {translator_jid}")

    # Chat agent setup
    human_jid = input("Chat agent JID: ")
    human_password = getpass.getpass("Chat password: ")

    # Simple callback to detect shutdown
    shutdown = False

    def check_response(message: str, sender: str):
        nonlocal shutdown
        print(f"\nTranslation: {message}")
        if "This is not Spanish text" in message:
            shutdown = True
            print("\nNon-Spanish detected. Shutting down...")

    chat = ChatAgent(
        jid=human_jid,
        password=human_password,
        target_agent_jid=translator_jid,
        display_callback=check_response
    )

    await chat.start()
    print(f"Chat started: {human_jid}")

    print("\nType Spanish text to translate (or non-Spanish to exit)")
    print("Type 'exit' to quit\n")

    # Run interactive chat
    await chat.run_interactive(exit_command="exit")

    # Cleanup
    await chat.stop()
    await translator.stop()
    print("Agents stopped.")


if __name__ == "__main__":
    spade.run(main())