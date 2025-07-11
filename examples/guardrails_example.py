"""
Guardrails Example with Gemma Model from Ollama

Demonstrates input and output guardrails using two agents:
- LLMAgent: Handles LLM requests with integrated guardrails
- ChatAgent: Interactive user interface

Features:
- Input guardrails: keyword filtering, profanity filter
- Output guardrails: LLM-based safety validation
- Real-time guardrail action logging
"""

import asyncio
import getpass
import logging
import spade

from spade_llm.agent import LLMAgent, ChatAgent
from spade_llm.providers import LLMProvider
from spade_llm.guardrails import (
    KeywordGuardrail, LLMGuardrail,
    GuardrailAction, InputGuardrail, OutputGuardrail
)
from typing import List

logging.basicConfig(level=logging.INFO)


def create_input_guardrails() -> List[InputGuardrail]:
    """Create input guardrail pipeline."""
    # 1. Keyword guardrail - blocks harmful content
    keyword_guardrail = KeywordGuardrail(
        name="harmful_content_filter",
        blocked_keywords=["hack", "exploit", "malware", "virus", "illegal", "bomb"],
        action=GuardrailAction.BLOCK,
        case_sensitive=False,
        blocked_message="I cannot help with potentially harmful activities."
    )
    
    # 2. Profanity filter - replaces inappropriate words
    profanity_guardrail = KeywordGuardrail(
        name="profanity_filter", 
        blocked_keywords=["damn", "hell", "stupid", "idiot", "crap"],
        action=GuardrailAction.MODIFY,
        replacement="[FILTERED]",
        case_sensitive=False
    )

    return [keyword_guardrail, profanity_guardrail]


def create_output_guardrails(safety_provider: LLMProvider) -> List[OutputGuardrail]:
    """Create output guardrail pipeline."""
    # LLM-based safety checker
    safety_guardrail = LLMGuardrail(
        name="llm_safety_checker",
        provider=safety_provider,
        safety_prompt="""
        Analyze this AI response for safety. Check for harmful instructions, personal attacks, 
        inappropriate content, or anything that could cause harm.
        
        Respond with JSON: {{"safe": true/false, "reason": "explanation if unsafe"}}
        
        AI Response: {content}
        """,
        blocked_message="I apologize, but I cannot provide that response due to safety concerns."
    )
    
    return [safety_guardrail]


def on_guardrail_trigger(result):
    """Callback function for when guardrails are triggered."""
    if result.action == GuardrailAction.BLOCK:
        print(f"🚫 GUARDRAIL BLOCKED: {result.reason}")
    elif result.action == GuardrailAction.MODIFY:
        print(f"✏️  GUARDRAIL MODIFIED: {result.reason}")
    elif result.action == GuardrailAction.WARNING:
        print(f"⚠️  GUARDRAIL WARNING: {result.reason}")


async def main():
    """Main function demonstrating guardrails with two agents."""
    print("=== Guardrails Example with Gemma Model ===\n")
    
    # Get XMPP credentials
    xmpp_server = input("Enter XMPP server domain: ")
    
    llm_jid = f"llm_guardian@{xmpp_server}"
    llm_password = getpass.getpass("LLM Agent password: ")
    
    # Create Ollama providers
    main_provider = LLMProvider.create_ollama(
        model="gemma3:1b",
        temperature=0.7,
        base_url="http://localhost:11434/v1",
        timeout=120.0
    )
    
    safety_provider = LLMProvider.create_ollama(
        model="gemma3:1b",  # Using same model for safety check in demo
        temperature=0.3,    # Lower temperature for safety validation
        base_url="http://localhost:11434/v1",
        timeout=60.0
    )
    
    # Create guardrails
    input_guardrails = create_input_guardrails()
    output_guardrails = create_output_guardrails(safety_provider)
    
    # Create LLM agent with integrated guardrails
    llm_agent = LLMAgent(
        jid=llm_jid,
        password=llm_password,
        provider=main_provider,
        system_prompt="You are a helpful AI assistant with safety guardrails. Be concise and informative.",
        input_guardrails=input_guardrails,
        output_guardrails=output_guardrails,
        on_guardrail_trigger=on_guardrail_trigger
    )
    
    await llm_agent.start()
    print(f"✓ Guarded LLM agent started: {llm_jid}")
    print("🛡️  Guardrails system initialized!")
    print("• Input: keyword filter, profanity filter, personal info redaction")
    print("• Output: LLM safety validator")
    
    # Chat agent setup
    user_jid = f"user@{xmpp_server}"
    user_password = getpass.getpass("User Agent password: ")
    
    def display_response(message: str, sender: str):
        print(f"\n🤖 Guardian AI: {message}")
    
    def on_send(message: str, recipient: str):
        print(f"👤 You: {message}")
    
    chat = ChatAgent(
        jid=user_jid,
        password=user_password,
        target_agent_jid=llm_jid,
        display_callback=display_response,
        on_message_sent=on_send,
        verbose=False
    )
    
    await chat.start()
    print(f"✓ Chat agent started: {user_jid}")
    
    print("\n🧪 Test the guardrails system:")
    print("• Normal questions (should pass)")
    print("• Messages with profanity (will be filtered)")
    print("• Personal info like emails (will be redacted)")
    print("• Harmful requests (will be blocked)")
    print("\nType 'exit' to quit\n")
    
    # Run interactive chat
    await chat.run_interactive()
    
    # Cleanup
    await chat.stop()
    await llm_agent.stop()
    print("Agents stopped. Goodbye!")


if __name__ == "__main__":
    print("🔍 Prerequisites:")
    print("• Ollama running: ollama serve")
    print("• Gemma model: ollama pull gemma3:1b")
    print("• XMPP server running")
    print()
    
    spade.run(main())