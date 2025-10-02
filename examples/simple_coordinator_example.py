"""
Simple Coordinator Example - Minimal CoordinatorAgent Test

This example demonstrates the CoordinatorAgent's core functionality with
a small three-agent setup: Calculator, Reporter, and Saver.

PURPOSE:
This is a TESTING example to verify that the CoordinatorAgent mechanism works.
For realistic workflows, see coordinator_agent_example.py.

WORKFLOW:
1. User requests a calculation, formatted report, and persistence
2. Coordinator sends calculation to Calculator agent
3. Coordinator sends result to Reporter agent
4. Coordinator sends formatted report to Saver agent, which stores it in a text file
5. Coordinator returns completion message to user

PREREQUISITES:
1. Start SPADE built-in server in another terminal:
   spade run

2. Install dependencies:
   pip install spade_llm

VERIFICATION:
If the example outputs "30" as the calculation result and saves the formatted
report to disk, coordination works!

This example uses SPADE's default built-in server (localhost:5222) - no account registration needed!
"""

import asyncio
import os
import spade

from spade_llm.agent import LLMAgent, ChatAgent
from spade_llm.agent.coordinator_agent import CoordinatorAgent
from spade_llm.providers import LLMProvider
from spade_llm.tools import LLMTool
from spade_llm.utils import load_env_vars

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logging.getLogger("spade_llm").setLevel(logging.INFO)

# 1. AGENT PROMPTS
CALCULATOR_PROMPT = """You are a simple calculator agent.

When asked to calculate an expression:
1. Compute the result
2. Return ONLY the numeric answer (no explanation needed)

Examples:
- "Calculate (10 + 5) * 2" → "30"
- "What is 7 + 3?" → "10"
- "Compute 100 / 4" → "25"

Be concise and accurate.
"""

REPORTER_PROMPT = """You are a result formatting agent.

When given a calculation result to format:
1. Create a brief, clear statement with the result
2. Keep it to 1-2 sentences maximum

Examples:
- Input: "Format result: 30 for calculation (10 + 5) * 2"
  Output: "The result of (10 + 5) * 2 is 30."

- Input: "Format: 10 from 7 + 3"
  Output: "7 + 3 equals 10."

Be professional and concise.
"""


SAVER_PROMPT = """You are a storage agent that persists finalized reports.

When you receive a formatted report:
1. Call the save_report tool exactly once with the complete text to store.
2. After the tool call, acknowledge success to the coordinator (no additional formatting).

If you cannot save the file, explain why.
"""

REPORT_SAVE_PATH = os.path.join(os.path.dirname(__file__), "coordinator_report.txt")


def _create_save_report_tool(file_path: str) -> LLMTool:
    """Create an LLM tool that saves report text to the provided path."""

    def save_report(report_text: str) -> str:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as report_file:
            report_file.write(report_text)
        return f"Report saved to {file_path}"

    return LLMTool(
        name="save_report",
        description="Persist the finalized report text to disk",
        parameters={
            "type": "object",
            "properties": {
                "report_text": {
                    "type": "string",
                    "description": "The full report text to store",
                }
            },
            "required": ["report_text"],
        },
        func=save_report,
    )


async def main():
    """Main function demonstrating minimal coordinator usage."""

    print("=" * 60)
    print("SIMPLE COORDINATOR EXAMPLE - Testing CoordinatorAgent")
    print("=" * 60)
    print()

    # 2. LOAD CONFIGURATION
    load_env_vars()

    # API Key (with fallback to input)
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        api_key = input("Enter OpenAI API key: ")

    if os.path.exists(REPORT_SAVE_PATH):
        os.remove(REPORT_SAVE_PATH)

    print("🔧 Configuration:")
    print(f"  • Server: localhost:5222 (SPADE built-in)")
    print(f"  • Provider: OpenAI (gpt-4o-mini)")
    print()

    # 3. CREATE PROVIDER
    provider = LLMProvider.create_openai(
        api_key=api_key,
        model="gpt-4o-mini"
    )

    # 4. CREATE SUBAGENTS
    print("🤖 Creating agents...")

    calculator = LLMAgent(
        jid="calculator@localhost",
        password="calc_pass",
        system_prompt=CALCULATOR_PROMPT,
        provider=provider,
        verify_security=False
    )
    print("  ✓ Calculator agent created")

    reporter = LLMAgent(
        jid="reporter@localhost",
        password="report_pass",
        system_prompt=REPORTER_PROMPT,
        provider=provider,
        verify_security=False
    )
    print("  ✓ Reporter agent created")

    saver = LLMAgent(
        jid="saver@localhost",
        password="save_pass",
        system_prompt=SAVER_PROMPT,
        provider=provider,
        tools=[_create_save_report_tool(REPORT_SAVE_PATH)],
        verify_security=False
    )
    print("  ✓ Saver agent created")

    # 5. CREATE COORDINATOR
    coordinator = CoordinatorAgent(
        jid="coordinator@localhost",
        password="coord_pass",
        subagent_ids=[
            "calculator@localhost",
            "reporter@localhost",
            "saver@localhost",
        ],
        coordination_session="calc_session",
        provider=provider,
        verify_security=False
    )
    print("  ✓ Coordinator agent created")
    print(f"    - Managing: calculator@localhost, reporter@localhost, saver@localhost")
    print(f"    - Session: calc_session")
    print()

    # 6. CREATE CHAT AGENT (user interface)
    completion_detected = asyncio.Event()
    final_response = []

    def display_callback(message: str, sender: str):
        """Callback to display responses and detect completion."""
        print(f"📩 Response from {sender}:")
        print(f"   {message}")
        print()

        if "<TASK_COMPLETE>" in message or "<END>" in message or "<DONE>" in message:
            print("✅ TASK COMPLETION DETECTED!")
            final_response.append(message)
            completion_detected.set()

    chat_agent = ChatAgent(
        jid="user@localhost",
        password="user_pass",
        target_agent_jid="coordinator@localhost",
        display_callback=display_callback,
        verify_security=False
    )
    print("  ✓ Chat agent created (user interface)")
    print()

    # 7. START ALL AGENTS
    print("🚀 Starting agents...")
    try:
        await calculator.start()
        print("  ✓ Calculator started")

        await reporter.start()
        print("  ✓ Reporter started")

        await saver.start()
        print("  ✓ Saver started")

        await coordinator.start()
        print("  ✓ Coordinator started")

        await chat_agent.start()
        print("  ✓ Chat agent started")

        print("\n⏳ Waiting for connections...")
        await asyncio.sleep(2)

        print("✅ All agents ready!")
        print()

        # 8. SEND TEST REQUEST
        print("=" * 60)
        print("TEST SCENARIO: Calculate (10 + 5) * 2, format it, and save to disk")
        print("=" * 60)
        print()

        test_request = """Please coordinate this calculation task step by step:

1. Ask the calculator agent to compute: (10 + 5) * 2
2. Ask the reporter agent to format the result nicely
3. Send the formatted output to the saver agent and have it call save_report with the exact text

Use your send_to_agent tool for each step. Work sequentially - wait for each response before proceeding.

When everything is complete, end your response with <TASK_COMPLETE>
"""

        print("📤 Sending coordination request to coordinator...")
        print()
        chat_agent.send_message(test_request)

        # Give time for the message to be sent by SendBehaviour
        await asyncio.sleep(1)

        print("⏳ Waiting for coordination to complete (max 60 seconds)...")
        print("   Watch for sequential agent interactions below:")
        print()

        # 9. WAIT FOR COMPLETION
        try:
            await asyncio.wait_for(completion_detected.wait(), timeout=60)
            print()
            print("=" * 60)
            print("COORDINATION COMPLETED SUCCESSFULLY!")
            print("=" * 60)



        except asyncio.TimeoutError:
            print()
            print("⚠️  Coordination timed out after 60 seconds")
            print("   Check that:")
            print("   • SPADE server is running (spade run)")
            print("   • OpenAI API key is valid")
            print("   • Network connection is stable")

    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 10. CLEANUP
        print()
        print("🛑 Stopping agents...")
        await chat_agent.stop()
        print("  ✓ Chat agent stopped")
        await coordinator.stop()
        print("  ✓ Coordinator stopped")
        await saver.stop()
        print("  ✓ Saver stopped")
        await reporter.stop()
        print("  ✓ Reporter stopped")
        await calculator.stop()
        print("  ✓ Calculator stopped")

        print()
        print("=" * 60)
        print("EXAMPLE COMPLETED")
        print("=" * 60)


if __name__ == "__main__":
    print()
    print("🔍 Prerequisites Check:")
    print("  • SPADE built-in server running? (spade run)")
    print("  • OpenAI API key available? (in .env or will prompt)")
    print()
    print("Press Ctrl+C to cancel, or wait to continue...")
    print()

    try:
        spade.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Example cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
