import streamlit as st

import components
import state
from config import PAGE_TITLE, PAGE_ICON

st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="centered")

components.load_css("styles.css")
state.init_state()

if st.session_state.interview_started:
    components.render_interview()
else:
    components.render_home()

st.html("""
    <div class="footer">
        AI Placement Interview · Built with Python, Streamlit &amp; Groq
    </div>
""")