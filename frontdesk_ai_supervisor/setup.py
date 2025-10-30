# setup.py
from setuptools import setup, find_packages

setup(
    name="frontdesk_ai_supervisor",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "livekit",
        "livekit-agents",
        "livekit-plugins-openai",
        "livekit-plugins-silero",
        "python-dotenv",
        "flask",
        "flask-cors",
        "firebase-admin",
        "requests",
        "openai",
        "pytest",
    ],
)