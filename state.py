"""
Everything related to st.session_state lives here: the default shape,
initialization, and the transitions between interview stages
(start / reset / record an answer / move on).

Centralizing this stops session-state keys from being invented ad hoc
throughout the UI code.
"""

import streamlit as st

import ai_service

DEFAULTS = {
    "interview_started": False,
    "interview_completed": False,
    "messages": [],
    "question_number": 0,
    "current_question": "",
    "resume_text": "",
    "interview_mode": "",
    "current_evaluation": "",
    "current_correct_answer": "",
    "evaluation_done": False,
    "correct_answer_shown": False,
    "final_report": "",
    "audio_key": 0,
    "interview_id": 0,
}


def init_state() -> None:
    """Populate any missing session_state keys with their defaults."""

    for key, value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_interview() -> None:
    """Return to the home screen. Keeps the uploaded resume for convenience."""

    for key, value in DEFAULTS.items():
        if key not in ("resume_text", "interview_mode"):
            st.session_state[key] = value


def start_new_interview() -> None:
    """Kick off a brand new interview session and generate question 1."""

    reset_interview()

    st.session_state.interview_id += 1
    st.session_state.interview_started = True
    st.session_state.question_number = 1

    question = ai_service.generate_first_question(
        st.session_state.resume_text,
        st.session_state.interview_mode,
    )

    st.session_state.current_question = question
    _append_message("question", 1, question)


def record_answer(question_number: int, answer: str) -> None:
    """Save the student's answer, then generate and store its evaluation."""

    _append_message("answer", question_number, answer)

    evaluation = ai_service.evaluate_answer(
        st.session_state.interview_mode,
        st.session_state.current_question,
        answer,
    )

    st.session_state.current_evaluation = evaluation
    st.session_state.evaluation_done = True
    _append_message("evaluation", question_number, evaluation)


def reveal_correct_answer() -> None:
    """Generate and store the model answer for the current question."""

    student_answer = _latest_message_content("answer")

    correct_answer = ai_service.generate_correct_answer(
        st.session_state.interview_mode,
        st.session_state.current_question,
        student_answer,
        st.session_state.current_evaluation,
    )

    st.session_state.current_correct_answer = correct_answer
    st.session_state.correct_answer_shown = True
    _append_message(
        "correct_answer", st.session_state.question_number, correct_answer
    )


def advance_to_next_question() -> None:
    """Generate the next question and reset the per-question flags."""

    next_question = ai_service.generate_next_question(
        st.session_state.resume_text,
        st.session_state.interview_mode,
        get_interview_history(),
        st.session_state.question_number + 1,
    )

    st.session_state.question_number += 1
    st.session_state.current_question = next_question
    st.session_state.current_evaluation = ""
    st.session_state.current_correct_answer = ""
    st.session_state.evaluation_done = False
    st.session_state.correct_answer_shown = False
    st.session_state.audio_key += 1

    _append_message("question", st.session_state.question_number, next_question)


def get_interview_history() -> str:
    """Render the full Q&A/evaluation transcript as plain text for prompts."""

    labels = {
        "question": "Question",
        "answer": "Student Answer",
        "evaluation": "Evaluation",
        "correct_answer": "Correct Answer",
    }

    lines = []
    for message in st.session_state.messages:
        label = labels.get(message.get("type"))
        if label:
            lines.append(
                f"{label} {message.get('question_number')}: {message.get('content', '')}"
            )

    return "\n".join(lines)


def get_answered_count() -> int:
    return sum(1 for m in st.session_state.messages if m.get("type") == "answer")


def _append_message(message_type: str, number: int, content: str) -> None:
    st.session_state.messages.append(
        {
            "role": "assistant" if message_type != "answer" else "user",
            "type": message_type,
            "question_number": number,
            "content": content,
        }
    )


def _latest_message_content(message_type: str) -> str:
    for message in reversed(st.session_state.messages):
        if message.get("type") == message_type:
            return message.get("content", "")
    return ""