import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from database.firebase_manager import FirebaseManager
from agent.livekit_agent import LiveAgent
from agent.knowledge_base import KnowledgeBase
from agent.help_request_handler import HelpRequestHandler

def supervisor_notify(req):
    """Simple console notifier for new pending requests."""
    print(f"[SUPERVISOR HOOK] Need help answering: {req['question']} (id={req['request_id']})")

def start_voice_agent_mode():
    """Start the LiveKit Voice Agent with proper version handling."""
    print("\n============================================================")
    print("FRONTDESK AI AGENT - VOICE MODE")
    print("============================================================")
    print("\nStarting LiveKit voice agent...")

    required_env = ["LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET"]
    missing = [k for k in required_env if not os.getenv(k)]
    if missing:
        print(f"\n❌ Missing environment variables: {', '.join(missing)}")
        print("Please add them in your .env file before running voice mode.\n")
        return

    try:
        import asyncio
        from voice_agent.livekit_voice_agent import entrypoint
        import livekit.agents as lk

        print("[VOICE AGENT] 🔍 Checking LiveKit Agents version...")

        if hasattr(lk, "JobWorker"):
            print("[VOICE AGENT] ✅ Using JobWorker (v1.x compatible)")
            worker = lk.JobWorker(entrypoint_fn=entrypoint)
        elif hasattr(lk, "Worker"):
            print("[VOICE AGENT] ✅ Using Worker (v2.x compatible)")
            # Corrected keyword argument here:
            worker = lk.Worker(entrypoint=entrypoint)
        elif hasattr(lk, "AgentWorker"):
            print("[VOICE AGENT] ✅ Using AgentWorker (v2.1+ compatible)")
            worker = lk.AgentWorker(entrypoint=entrypoint)
        else:
            raise RuntimeError("No valid worker class found in livekit.agents")

        asyncio.run(worker.run())

    except ModuleNotFoundError as e:
        print(f"\n❌ Missing dependency: {e.name}")
        print("👉 Install it using: pip install livekit livekit-agents av python-dotenv\n")

    except Exception as e:
        print(f"\n❌ Voice agent failed to start: {e}")

def start_text_agent():
    """Run text-mode simulation for the Frontdesk AI Agent."""
    print("\nFrontdesk AI Agent")
    print("Choose mode:")
    print(" 1. Text mode (console-based testing)")
    print(" 2. Voice mode (LiveKit integration)\n")

    choice = input("Enter choice (1 or 2): ").strip()

    if choice == "2":
        # Exit async context to run voice agent in main thread
        return "voice"

    print("\n============================================================")
    print("FRONTDESK AI AGENT - TEXT MODE")
    print("============================================================")
    print(
        """
Simulated text-based agent for testing.

Ask questions and the agent will respond or escalate.

Commands:

• Type any question to test the agent
• Type 'quit' or 'exit' to stop
• Type 'help' for example questions

============================================================
"""
    )

    # Initialize system components
    db = FirebaseManager()
    kb = KnowledgeBase(db)
    handler = HelpRequestHandler(db, kb, notify_callback=supervisor_notify)
    agent = LiveAgent(db, notify_callback=supervisor_notify)

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() in ["quit", "exit"]:
            print("Goodbye!")
            break
        elif user_input.lower() == "help":
            print(
                "Examples:\n - What are your working hours?\n - How can I book an appointment?\n - Where are you located?"
            )
            continue

        # Simulate knowledge base lookup
        answer = kb.lookup(user_input)

        if answer:
            print(f"Agent: {answer}")
        else:
            # Create pending request for supervisor
            print("Agent: Let me check that with our supervisor.")
            req = handler.create_request(
                question=user_input,
                caller_phone="9999999999",
                session_id="test-session",
            )
            print(f"[SYSTEM] Created pending request: {req['request_id']}")

if __name__ == "__main__":
    try:
        result = start_text_agent()
        if result == "voice":
            start_voice_agent_mode()

    except KeyboardInterrupt:
        print("\nAgent stopped by user.")
