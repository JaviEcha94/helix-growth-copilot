import time

import streamlit as st

from app.background import progress_percent
from app.i18n import t

# Groq/Cerebras a veces responden en menos de un segundo: sin este piso, todo
# el pipeline (4 agentes + supervisor) puede terminar antes de que la UI
# alcance a pintar un solo frame de "Analizando...", y el usuario ve saltar
# directo del formulario al reporte. Estas constantes fuerzan una duración
# mínima visible, revelando cada etapa de a una aunque el trabajo real ya
# haya terminado (nunca al revés: si el trabajo real tarda más, se muestra
# el progreso real sin demora extra).
_MIN_LOADING_SECONDS = 4.0
_STAGE_SECONDS = _MIN_LOADING_SECONDS / 5  # 4 agentes + compilación del supervisor


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

    elapsed = time.time() - st.session_state.get("job_started_at", time.time())
    reveal_count = min(5, int(elapsed // _STAGE_SECONDS) + 1)
    done_agents = [real and (i < min(reveal_count, 4)) for i, real in enumerate(snap["agent_done"])]
    supervisor_revealed = snap["supervisor_done"] and reveal_count >= 5
    snap = {**snap, "agent_done": done_agents, "supervisor_done": supervisor_revealed}
    pct = progress_percent(snap)

    if any(done_agents) and not all(done_agents):
        active_idx = done_agents.index(False)
        loading_msg = T["agentMsgs"][active_idx]
    elif snap["supervisor_done"] or all(done_agents):
        loading_msg = T["compiling"]
    else:
        loading_msg = T["agentMsgs"][0]

    # El mockup centra toda la pantalla de carga en una columna angosta
    # (max-width 780px) en vez de usar todo el ancho del layout, como
    # input/reporte — sin esto las tarjetas de agente quedan muy anchas
    # y dispersas.
    st.markdown(
        '<style>.st-key-loading_wrap{ max-width:780px; margin:0 auto; }'
        '.st-key-cancel_btn button{ background:transparent !important; border:none !important; '
        'color:#94A3B8 !important; text-decoration:underline !important; text-underline-offset:3px !important; }'
        '.st-key-cancel_btn button:hover{ color:#fff !important; }'
        "</style>",
        unsafe_allow_html=True,
    )
    with st.container(key="loading_wrap"):
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
            ring = (
                '<span style="position:absolute;inset:0;border-radius:50%;border:1.5px solid #2563EB;'
                'animation:ringPulse 1.4s ease-out infinite;"></span>'
                if status == "processing" else ""
            )
            with cols[i]:
                st.markdown(
                    f'<div class="helix-agent-card {status}">'
                    f'<div style="display:flex;align-items:center;gap:10px;">'
                    f'<span style="position:relative;display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;">'
                    f'{ring}<span class="helix-agent-icon {status}">{icon}</span>'
                    f'</span>'
                    f'<span class="helix-agent-name">{T["agentNames"][i]}</span>'
                    f'</div>'
                    f'<span class="helix-agent-sub">{T["agentSubs"][i]}</span>'
                    f'<span class="helix-agent-status {status}">{status_text}</span>'
                    f'</div>',
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

        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        st.markdown(
            """<div class="helix-card-plain">
                <div class="helix-skeleton" style="height:18px;width:38%;"></div>
                <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:14px;">
                    <div class="helix-skeleton" style="height:64px;"></div>
                    <div class="helix-skeleton" style="height:64px;"></div>
                    <div class="helix-skeleton" style="height:64px;"></div>
                </div>
                <div class="helix-skeleton" style="height:13px;width:90%;margin-top:14px;"></div>
                <div class="helix-skeleton" style="height:13px;width:70%;margin-top:8px;"></div>
            </div>""",
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        _, ccol, _ = st.columns([2, 1, 2])
        with ccol:
            st.button(T["cancel"], key="cancel_btn", on_click=_cancel, args=(job,), use_container_width=True)

    if snap["finished"] and not snap["error"] and reveal_count >= 5:
        on_finished(snap["result"])
        st.rerun()
        return

    time.sleep(0.5)
    st.rerun()
