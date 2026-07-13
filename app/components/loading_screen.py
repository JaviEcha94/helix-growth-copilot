import time

import streamlit as st

from app.background import progress_percent
from app.i18n import t


def _cancel(job) -> None:
    job.cancel()
    st.session_state["screen"] = "input"
    st.session_state["job"] = None
    from app.state import toast

    toast(t(st.session_state["lang"])["toastCancel"])


def render_loading_screen(on_finished, on_error) -> None:
    T = t(st.session_state["lang"])
    job = st.session_state.get("job")
    if job is None:
        st.session_state["screen"] = "input"
        st.rerun()
        return

    snap = job.snapshot()

    if snap["error"]:
        on_error(snap["error"])
        st.rerun()
        return

    pct = progress_percent(snap)
    done_agents = snap["agent_done"]

    if any(done_agents) and not all(done_agents):
        active_idx = done_agents.index(False)
        loading_msg = T["agentMsgs"][active_idx]
    elif snap["supervisor_done"] or all(done_agents):
        loading_msg = T["compiling"]
    else:
        loading_msg = T["agentMsgs"][0]

    st.markdown(f'<div class="helix-loading-title">{T["loadingTitle"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="helix-loading-msg">{loading_msg}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="helix-loading-sub">{T["loadingSub"]}</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    cols = st.columns(4)
    for i in range(4):
        if done_agents[i]:
            status = "done"
        elif False in done_agents and i == done_agents.index(False):
            status = "processing"
        else:
            status = "waiting"
        icon = "✓" if status == "done" else ("⟳" if status == "processing" else "○")
        status_text = {"done": T["statusDone"], "processing": T["statusProcessing"], "waiting": T["statusWaiting"]}[status]
        with cols[i]:
            st.markdown(
                f"""<div class="helix-agent-card {status}">
                    <div style="display:flex;align-items:center;gap:10px;">
                        <span class="helix-agent-icon {status}">{icon}</span>
                        <span class="helix-agent-name">{T['agentNames'][i]}</span>
                    </div>
                    <span class="helix-agent-sub">{T['agentSubs'][i]}</span>
                    <span class="helix-agent-status {status}">{status_text}</span>
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    pcol, lcol = st.columns([6, 1])
    with pcol:
        st.markdown(
            f"""<div class="helix-progress-outer" role="progressbar" aria-valuenow="{pct}" aria-valuemin="0" aria-valuemax="100">
                <div class="helix-progress-fill" style="width:{pct}%;"></div>
            </div>""",
            unsafe_allow_html=True,
        )
    with lcol:
        st.markdown(f"<div style='text-align:right;font-family:Space Grotesk,sans-serif;font-size:17px;font-weight:700;'>{pct}%</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
    _, ccol, _ = st.columns([2, 1, 2])
    with ccol:
        st.button(T["cancel"], key="cancel_btn", on_click=_cancel, args=(job,), use_container_width=True)

    if snap["finished"] and not snap["error"]:
        on_finished(snap["result"])
        st.rerun()
        return

    time.sleep(0.5)
    st.rerun()
