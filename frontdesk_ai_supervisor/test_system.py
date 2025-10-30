import asyncio
from database.firebase_manager import FirebaseManager
from agent.knowledge_base import KnowledgeBase
from agent.help_request_handler import HelpRequestHandler
from agent.livekit_agent import LiveAgentSimulator, notify_console

async def demo():
    db = FirebaseManager()
    kb = KnowledgeBase(db)
    handler = HelpRequestHandler(db, kb, notify_callback=notify_console, timeout_seconds=10)
    agent = LiveAgentSimulator(db, kb, handler, notify_callback=notify_console)

    # simulate a call with a known question
    res1 = await agent.handle_incoming_call("555-0001", "What time are you open?", "sid-1")
    print("res1:", res1)

    # simulate a call with unknown question -> creates request
    res2 = await agent.handle_incoming_call("555-0002", "Do you do eyebrow tattoos?", "sid-2")
    print("res2:", res2)

    # list pending
    print("Pending:", handler.get_pending_requests())

if __name__ == "__main__":
    asyncio.run(demo())
