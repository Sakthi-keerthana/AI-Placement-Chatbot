"""
Application configuration.

Loads environment variables, builds the Groq client once, and holds the
constants that the rest of the app depends on. Centralizing these avoids
magic strings/numbers scattered across the codebase.
"""

import os

import streamlit as st
from dotenv import load_dotenv
from groq import Groq


load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

PAGE_TITLE = "AI Placement Interview"
PAGE_ICON = "🎯"

TOTAL_QUESTIONS = 10
CHAT_MODEL = "openai/gpt-oss-20b"
SPEECH_MODEL = "whisper-large-v3-turbo"

INTERVIEW_MODES = [
    "Full Interview",
    "Technical Round",
    "Coding Round",
    "Project Round",
    "HR Round",
]


@st.cache_resource(show_spinner=False)
def get_groq_client() -> Groq:
    """
    Build (and cache) a single Groq client for the lifetime of the app.

    st.cache_resource ensures the client is created once per session
    instead of being rebuilt on every rerun/interaction.
    """

    if not GROQ_API_KEY:
        st.error("GROQ_API_KEY is missing from your .env file.")
        st.stop()

    return Groq(api_key=GROQ_API_KEY)