import streamlit as st

from app.i18n import t
from app.state import persist


def _set_lang(lang: str) -> None:
    st.session_state["lang"] = lang
    persist()


def _toggle_density() -> None:
    st.session_state["density"] = "compact" if st.session_state["density"] == "comfortable" else "comfortable"
    persist()


def _relative_time(iso: str | None, T: dict) -> str:
    if not iso:
        return ""
    from datetime import datetime

    try:
        d = datetime.fromisoformat(iso)
    except ValueError:
        return ""
    diff = (datetime.now() - d).total_seconds()
    if diff < 60:
        return T["justNow"]
    minutes = int(diff // 60)
    if minutes < 60:
        return T["minAgo"].replace("{n}", str(minutes))
    return T["hourAgo"].replace("{n}", str(minutes // 60))


def render_header() -> None:
    T = t(st.session_state["lang"])

    left, right = st.columns([3, 4], vertical_alignment="center")
    with left:
        st.markdown(
            f"""
            <div style="display:flex;align-items:center;gap:12px;">
              <div class="helix-logo-badge">H</div>
              <div style="line-height:1.15;">
                <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:18px;">
                  Helix <span style="color:#94A3B8;font-weight:500;">Growth Copilot</span>
                </div>
                <div style="font-size:12px;color:#94A3B8;">{T['tagline']}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        c1, c2, c3 = st.columns([1.5, 1.3, 1.3])
        with c1:
            st.markdown(
                f'<div class="helix-status-dot" style="margin-top:6px;"><span></span>{T["statusOnline"]}</div>',
                unsafe_allow_html=True,
            )
        with c2:
            history = st.session_state["history"]
            label = f"🕓 {T['historyBtn']}" + (f" ({len(history)})" if history else "")
            with st.popover(label, use_container_width=True):
                st.markdown(f"**{T['historyTitle']}**")
                if not history:
                    st.caption(T["historyEmpty"])
                for entry in history:
                    score = entry["health_score"]
                    color = "#22C55E" if score >= 75 else "#F97316" if score >= 50 else "#EF4444"
                    b1, b2 = st.columns([3, 1])
                    with b1:
                        if st.button(entry["store_name"], key=f"hist_{entry['id']}", use_container_width=True):
                            st.session_state["screen"] = "report"
                            st.session_state["report_data"] = entry["report_data"]
                            st.session_state["generated_at_iso"] = entry["date_iso"]
                            st.session_state["show_history"] = False
                            st.rerun()
                        st.caption(_relative_time(entry["date_iso"], T))
                    with b2:
                        st.markdown(
                            f'<div style="text-align:center;font-weight:700;color:{color};padding-top:8px;">{score}</div>',
                            unsafe_allow_html=True,
                        )
        with c3:
            icon = "▦" if st.session_state["density"] == "compact" else "▤"
            label = T["densityCompact"] if st.session_state["density"] == "compact" else T["densityComfortable"]
            st.button(f"{icon} {label}", key="density_toggle", on_click=_toggle_density, use_container_width=True)

        _, lang_col = st.columns([2.3, 1.7])
        with lang_col:
            chosen = st.segmented_control(
                "lang", options=("ES", "EN", "PT"), default=st.session_state["lang"],
                key="lang_switch", label_visibility="collapsed",
            )
            if chosen and chosen != st.session_state["lang"]:
                _set_lang(chosen)
                st.rerun()

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)


def render_breadcrumb_and_back(on_back) -> None:
    T = t(st.session_state["lang"])
    screen = st.session_state["screen"]
    step_index = {"input": 0, "loading": 1, "error": 1, "report": 2}.get(screen, 0)

    parts = []
    for i, label in enumerate(T["crumbs"]):
        if i > 0:
            parts.append('<span class="arrow">→</span>')
        cls = "helix-crumb-active" if i == step_index else ("helix-crumb-done" if i < step_index else "helix-crumb-pending")
        parts.append(f'<span class="{cls}">{label}</span>')

    left, right = st.columns([5, 1])
    with left:
        st.markdown(f'<div class="helix-crumbs">{"".join(parts)}</div>', unsafe_allow_html=True)
    with right:
        if screen != "input":
            if st.button(f"← {T['back']}", key="back_btn", use_container_width=True):
                on_back()
                st.rerun()
