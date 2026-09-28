"""
Thin wrapper around every Groq API call the app makes.

Every function here does exactly one job: build on a prompt (from
prompts.py) and return plain text. Nothing in this module touches
st.session_state, so it can be tested or reused independently of the
Streamlit UI.
"""

import streamlit as st

from config import get_groq_client, CHAT_MODEL, SPEECH_MODEL
import prompts


def ask_groq(prompt: str) -> str:
    """Send a single-turn prompt to the chat model and return the reply."""

    client = get_groq_client()

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
        )
        return response.choices[0].message.content.strip()

    except Exception as exc:
        return f"ERROR: {exc}"


def transcribe_audio(audio_bytes: bytes) -> str:
    """Convert recorded speech to text. Returns '' (and shows an error) on failure."""

    client = get_groq_client()

    try:
        transcription = client.audio.transcriptions.create(
            file=("answer.wav", audio_bytes),
            model=SPEECH_MODEL,
            response_format="json",
            temperature=0.0,
        )
        return transcription.text.strip()

    except Exception as exc:
        st.error(f"Speech-to-text failed: {exc}")
        return ""


def generate_first_question(resume_text: str, mode: str) -> str:
    return ask_groq(prompts.first_question_prompt(resume_text, mode))


def generate_next_question(
    resume_text: str,
    mode: str,
    history: str,
    next_number: int,
) -> str:
    return ask_groq(
        prompts.next_question_prompt(resume_text, mode, history, next_number)
    )


def evaluate_answer(mode: str, question: str, answer: str) -> str:
    return ask_groq(prompts.evaluation_prompt(mode, question, answer))


def generate_correct_answer(
    mode: str,
    question: str,
    answer: str,
    evaluation: str,
) -> str:
    return ask_groq(
        prompts.correct_answer_prompt(mode, question, answer, evaluation)
    )


def generate_final_report(
    resume_text: str,
    mode: str,
    history: str,
    total_questions: int,
) -> str:
    return ask_groq(
        prompts.final_report_prompt(resume_text, mode, history, total_questions)
    )