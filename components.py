"""
UI rendering. Every function here is responsible for drawing one part
of the screen; the actual interview logic lives in state.py / ai_service.py
so this module stays focused on presentation.
"""

import html

import streamlit as st
from streamlit_mic_recorder import mic_recorder

import ai_service
import resume_service
import state
from config import TOTAL_QUESTIONS, INTERVIEW_MODES

MESSAGE_STYLES = {
    "question": ("chat-question", "AI Interviewer · Question {n}"),
    "answer": ("chat-answer", "You · Answer {n}"),
    "evaluation": ("chat-evaluation", "Evaluation · Question {n}"),
    "correct_answer": ("chat-correct", "Ideal answer · Question {n}"),
}


def load_css(path: str = "styles.css") -> None:
    try:
        with open(path, "r", encoding="utf-8") as file:
            st.html(f"<style>{file.read()}</style>")
    except FileNotFoundError:
        st.error(f"{path} was not found.")


# =========================================================
# PROGRESS TRACKER
# =========================================================

def render_progress() -> None:
    current = st.session_state.question_number
    completed = state.get_answered_count()
    remaining = TOTAL_QUESTIONS - completed
    percentage = min(int((completed / TOTAL_QUESTIONS) * 100), 100)
    mode = html.escape(st.session_state.interview_mode)

    st.html(f"""
        <div class="progress-fixed-wrapper">
            <div class="progress-card">
                <div class="progress-top">
                    <div>
                        <div class="progress-mode">{mode}</div>
                        <div class="progress-main-title">
                            Question {current} of {TOTAL_QUESTIONS}
                        </div>
                    </div>
                    <div class="progress-number">{percentage}%</div>
                </div>
                <div class="progress-shell">
                    <div class="progress-fill" style="width:{percentage}%"></div>
                </div>
                <div class="progress-info">
                    <span>{completed} completed</span>
                    <span>{remaining} remaining</span>
                </div>
            </div>
        </div>
        <div class="progress-space"></div>
    """)


# =========================================================
# CHAT HISTORY
# =========================================================

def render_chat_history() -> None:
    for message in st.session_state.messages:
        style = MESSAGE_STYLES.get(message.get("type"))
        if not style:
            continue

        css_class, label_template = style
        number = message.get("question_number")
        content = html.escape(message.get("content", ""))
        label = label_template.format(n=number)

        st.html(f"""
            <div class="chat-message {css_class}">
                <div class="chat-label">{label}</div>
                <div class="chat-content">{content}</div>
            </div>
        """)


# =========================================================
# HOME PAGE
# =========================================================

def render_home() -> None:
    st.html("""
        <div class="hero">
            <div class="hero-title">AI Placement Interview</div>
            <div class="hero-rule"></div>
            <div class="hero-subtitle">
                Upload your resume and practice a personalized placement
                interview, question by question, with feedback after every answer.
            </div>
        </div>
    """)

    st.html("""
        <div class="glass-card">
            <div class="section-title">Upload your resume</div>
            <div class="answer-hint">PDF format only.</div>
        </div>
    """)

    uploaded_file = st.file_uploader(
        "Resume", type=["pdf"], label_visibility="collapsed"
    )

    if uploaded_file:
        _handle_resume_upload(uploaded_file)

    st.html("""
        <div class="glass-card">
            <div class="section-title">Choose interview mode</div>
        </div>
    """)

    st.session_state.interview_mode = st.radio(
        "Interview Mode",
        INTERVIEW_MODES,
        horizontal=True,
        label_visibility="collapsed",
    )

    st.write("")

    if st.button("Start interview", use_container_width=True):
        if not st.session_state.resume_text:
            st.warning("Please upload your resume first.")
        else:
            state.start_new_interview()
            st.rerun()


def _handle_resume_upload(uploaded_file) -> None:
    try:
        resume_text = resume_service.extract_resume_text(uploaded_file)

        if resume_text:
            st.session_state.resume_text = resume_text
            st.success("Resume uploaded successfully.")
        else:
            st.warning("Could not extract text from this PDF.")

    except Exception as exc:
        st.error(f"Could not read the resume: {exc}")


# =========================================================
# INTERVIEW PAGE
# =========================================================

def render_interview() -> None:
    render_progress()
    render_chat_history()

    if st.session_state.interview_completed:
        _render_completion()
        return

    _render_answer_composer()
    _render_post_answer_actions()


def _render_completion() -> None:
    st.html("""
        <div class="completion-card">
            <div class="completion-title">Interview completed</div>
            <div class="completion-text">
                You've answered all 10 questions. Generate your personalized
                performance report below.
            </div>
        </div>
    """)

    if st.button("Generate final report", use_container_width=True):
        with st.spinner("Analyzing your complete interview..."):
            report = ai_service.generate_final_report(
                st.session_state.resume_text,
                st.session_state.interview_mode,
                state.get_interview_history(),
                TOTAL_QUESTIONS,
            )
        st.session_state.final_report = report
        st.rerun()

    if st.session_state.final_report:
        render_report()


def _render_answer_composer() -> None:
    st.html("""
        <div class="current-answer-card">
            <div class="section-title">Your answer</div>
            <div class="answer-hint">Type your answer, or use the microphone.</div>
        </div>
    """)

    # A fresh widget key per question avoids Streamlit's
    # "widget already instantiated" error when moving between questions.
    answer_key = (
        f"answer_text_{st.session_state.interview_id}_"
        f"{st.session_state.question_number}"
    )

    mic_col, text_col = st.columns([0.09, 0.91], vertical_alignment="bottom")

    with mic_col:
        audio = mic_recorder(
            start_prompt="🎙️",
            stop_prompt="⏹️",
            just_once=True,
            use_container_width=False,
            key=f"mic_{st.session_state.audio_key}",
        )

    _process_recorded_audio(audio, answer_key)

    with text_col:
        answer = st.text_area(
            "Answer",
            placeholder="Type your answer here...",
            height=90,
            label_visibility="collapsed",
            key=answer_key,
        )

    st.write("")

    if st.button("Submit answer →", use_container_width=True):
        final_answer = answer.strip()

        if not final_answer:
            st.warning(
                "Please type an answer or record one using the microphone."
            )
        else:
            with st.spinner("Evaluating your answer..."):
                state.record_answer(st.session_state.question_number, final_answer)
            st.rerun()


def _process_recorded_audio(audio, answer_key: str) -> None:
    """Transcribe newly recorded audio and merge it into the answer box."""

    if not audio or not audio.get("bytes"):
        return

    with st.spinner("Converting your answer to text..."):
        transcript = ai_service.transcribe_audio(audio["bytes"])

    if not transcript:
        return

    existing_text = st.session_state.get(answer_key, "").strip()
    st.session_state[answer_key] = (
        f"{existing_text} {transcript}".strip() if existing_text else transcript
    )
    st.session_state.audio_key += 1
    st.rerun()


def _render_post_answer_actions() -> None:
    if not st.session_state.evaluation_done:
        return

    st.write("")

    if not st.session_state.correct_answer_shown:
        if st.button("Show correct answer", use_container_width=True):
            with st.spinner("Preparing the ideal answer..."):
                state.reveal_correct_answer()
            st.rerun()
        return

    if st.session_state.question_number < TOTAL_QUESTIONS:
        if st.button("Continue to next question →", use_container_width=True):
            with st.spinner("Preparing the next question..."):
                state.advance_to_next_question()
            st.rerun()
    else:
        st.session_state.interview_completed = True
        st.rerun()


# =========================================================
# FINAL REPORT
# =========================================================

def render_report() -> None:
    st.html(f"""
        <div class="report-card">
            <div class="report-header">Final interview report</div>
            <div class="report-mode">{html.escape(st.session_state.interview_mode)}</div>
        </div>
    """)

    st.markdown(st.session_state.final_report)

    st.html("""
        <div class="report-note">
            This report is based on your answers, evaluations and
            performance throughout the interview.
        </div>
    """)

    st.write("")

    if st.button("← Back to home", use_container_width=True):
        state.reset_interview()
        st.rerun()