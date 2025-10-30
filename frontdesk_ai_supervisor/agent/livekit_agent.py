import asyncio
from datetime import datetime
from database.firebase_manager import FirebaseManager

class LiveAgent:
    """
    Simulated LiveKit AI Voice Agent for the Frontdesk system.
    Handles incoming voice (or simulated text) calls and creates
    help requests in the Firebase database.
    """

    def __init__(self, db: FirebaseManager, notify_callback=None):
        self.db = db
        self.notify_callback = notify_callback
        print("[LiveAgent] Initialized successfully ✅")

    async def receive_call(self, caller_phone: str, question: str):
        """Simulates receiving a call and creates a help request."""
        print(f"\n📞 Incoming call from {caller_phone}: {question}")

        # Create a new pending request in the database
        req = self.db.create_request({
            "caller_phone": caller_phone,
            "question": question,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        })

        if self.notify_callback:
            self.notify_callback(req)

        print(f"[LiveAgent] Request created: {req['request_id']}")
        return req

    def check_timeouts(self):
        """Optional: check if any pending requests are stale."""
        print("[LiveAgent] (Simulated) timeout check complete.")
