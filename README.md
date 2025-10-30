Frontdesk AI Supervisor — Voice & Text Assistant
🚀 Overview

Frontdesk AI Supervisor is an intelligent customer assistant that handles both voice and text-based queries.
It connects with LiveKit for real-time voice conversations and uses an AI-based workflow to:

Understand customer questions (via speech-to-text).

Provide automatic responses (via LLM).

Escalate or log supervisor requests when the agent is unsure.

The system is built for Phase 1 of the assessment — focusing on structure, clarity, and scalable design.

⚙️ Setup Instructions

1️⃣ Clone the repository

git clone https://github.com/harish0999-coder/frontdesk-ai-supervisor.git
cd frontdesk-ai-supervisor


2️⃣ Create and activate virtual environment

python -m venv .venv
.\.venv\Scripts\activate


3️⃣ Install dependencies

pip install -r requirements.txt


4️⃣ Set environment variables
Create a .env file in the root folder:

LIVEKIT_URL=wss://your-livekit-server.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
OPENAI_API_KEY=your_openai_key (optional)


5️⃣ Run the system

Text-based mode:

python run_agent.py


Choose 1 for Text mode.

Voice-based mode (LiveKit):

python run_agent.py


Choose 2 for Voice mode.

🧠 Design Notes

Layered Design

agent/ → Core AI logic (text mode, database integration).

voice_agent/ → LiveKit voice integration.

run_agent.py → Main entry for CLI selection and workflow control.

Modules

FirebaseManager handles backend data storage.

KnowledgeBase provides FAQ lookup and AI fallback.

HelpRequestHandler escalates uncertain cases to supervisor.

LiveAgent integrates all layers for a full conversational loop.

Voice Integration

Uses livekit-agents for speech-to-text (STT), text-to-speech (TTS), and AI responses.

If OpenAI API is unavailable, falls back to Local Simulated STT/TTS for testing.

Error Handling

Validates .env credentials.

Logs detailed exceptions for LiveKit or API issues.

🧩 Key Decisions Made

Focused on a modular structure rather than one long file for scalability.

Chose LiveKit Agents SDK for real-time streaming voice.

Added fallback offline engines for local testing without network.

Designed the Supervisor escalation logic for Phase 2 integration.
