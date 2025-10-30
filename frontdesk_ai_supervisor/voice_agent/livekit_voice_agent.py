import asyncio
import os
from dotenv import load_dotenv
from livekit import agents
from livekit.agents import JobContext, AgentSession, Agent
from livekit.plugins import openai, silero

load_dotenv()  # Load environment from .env

SYSTEM_PROMPT = (
    "You are Frontdesk AI Voice Agent. "
    "You assist customers with appointments, pricing, and general enquiries. "
    "If you don't know something, politely say you’ll check with a supervisor. "
    "Keep replies short, polite, and natural."
)


# ------------------------------------------------------------
# ENTRYPOINT
# ------------------------------------------------------------
async def entrypoint(job: JobContext):
    print("[VOICE AGENT] 🎉 Room connected:", job.room.name)

    # Subscribe only to participant audio
    await job.connect(auto_subscribe=agents.AutoSubscribe.AUDIO_ONLY)
    print("[VOICE AGENT] 👤 Waiting for participant to join...")
    participant = await job.wait_for_participant()
    print("[VOICE AGENT] 👤 Participant joined:", participant.identity)

    # Individual components
    vad = silero.VAD.load()
    stt_engine = openai.STT(model="whisper-1")
    llm_engine = openai.LLM(model="gpt-4o-mini")
    tts_engine = openai.TTS(voice="alloy")

    # Create the agent with instructions
    agent = Agent(
        instructions=SYSTEM_PROMPT,
    )

    # Create the session
    session = AgentSession(
        vad=vad,
        stt=stt_engine,
        llm=llm_engine,
        tts=tts_engine,
    )

    await session.start(agent=agent, room=job.room)
    await session.generate_reply(
        instructions="Hello! Welcome to Frontdesk. How can I assist you today?"
    )

    print("[VOICE AGENT] ✅ Ready and listening...")


# ------------------------------------------------------------
# WORKER START
# ------------------------------------------------------------
async def start_worker():
    print("[VOICE AGENT] Connecting to LiveKit...")
    await agents.run(entrypoint)


if __name__ == "__main__":
    asyncio.run(start_worker())
