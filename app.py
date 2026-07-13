"""
Helix Growth Copilot — interfaz Streamlit.

Recrea design/design_handoff_streamlit/ conectado al pipeline
multi-agente real (src/graph/graph.py) en vez de datos de demo.

Uso: streamlit run app.py
"""
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src.utils.logging_config import setup_logging  # noqa: E402

setup_logging()

from app.background import start_job  # noqa: E402
from app.components.error_screen import render_error_screen
from app.components.header import render_breadcrumb_and_back, render_header
from app.components.input_screen import render_input_screen
from app.components.loading_screen import render_loading_screen
from app.components.report_screen import render_report_screen
from app.insights import build_report_data
from app.mapping import form_to_helix_state
from app.state import init_session_state, persist
from app.styles import COMPACT_CSS, CSS

st.set_page_config(page_title="Helix Growth Copilot", page_icon="🧬", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)

init_session_state()

if st.session_state.get("density") == "compact":
    st.markdown(COMPACT_CSS, unsafe_allow_html=True)


def _start_analysis(input_state: dict, extra: dict) -> None:
    st.session_state["run_id_counter"] = st.session_state.get("run_id_counter", 0) + 1
    run_id = st.session_state["run_id_counter"]
    st.session_state["last_input_state"] = input_state
    st.session_state["last_extra"] = extra
    st.session_state["job"] = start_job(run_id, input_state)
    st.session_state["screen"] = "loading"


def on_generate() -> None:
    store_name = st.session_state.get("store_name", "").strip()
    period = st.session_state.get("period", "").strip()
    input_state, extra = form_to_helix_state(st.session_state["form"], store_name, period)
    _start_analysis(input_state, extra)
    st.rerun()


def on_job_finished(accumulated_result: dict) -> None:
    extra = st.session_state["last_extra"]
    store_name = st.session_state["last_input_state"]["store_name"]
    period = st.session_state["last_input_state"]["period"]
    report_data = build_report_data(extra, accumulated_result, store_name, period)

    now = datetime.now()
    st.session_state["report_data"] = report_data
    st.session_state["generated_at"] = now.strftime("%d/%m/%Y · %H:%M")
    st.session_state["generated_at_iso"] = now.isoformat()
    st.session_state["actions_applied"] = [False, False, False]
    st.session_state["expanded_results"] = [False, False, False, False]
    st.session_state["pdf_bytes"] = None
    st.session_state["job"] = None

    history_entry = {
        "id": int(now.timestamp() * 1000),
        "store_name": store_name,
        "date_iso": now.isoformat(),
        "health_score": report_data["health_score"],
        "report_data": report_data,
    }
    st.session_state["history"] = [history_entry] + st.session_state.get("history", [])[:4]
    persist()
    st.session_state["screen"] = "report"


def on_job_error(error_msg: str) -> None:
    st.session_state["last_error"] = error_msg
    st.session_state["job"] = None
    st.session_state["screen"] = "error"


def on_retry() -> None:
    input_state = st.session_state.get("last_input_state")
    extra = st.session_state.get("last_extra")
    if input_state and extra:
        _start_analysis(input_state, extra)


def on_new_analysis() -> None:
    st.session_state["screen"] = "input"
    st.session_state["report_data"] = None
    st.session_state["pdf_bytes"] = None


def on_back() -> None:
    screen = st.session_state["screen"]
    if screen == "loading":
        job = st.session_state.get("job")
        if job:
            job.cancel()
        st.session_state["job"] = None
        st.session_state["screen"] = "input"
    elif screen in ("report", "error"):
        st.session_state["screen"] = "input"


render_header()
render_breadcrumb_and_back(on_back)

screen = st.session_state["screen"]
if screen == "input":
    render_input_screen(on_generate)
elif screen == "loading":
    render_loading_screen(on_job_finished, on_job_error)
elif screen == "error":
    render_error_screen(on_retry)
elif screen == "report":
    render_report_screen(on_new_analysis)
