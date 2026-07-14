import html
import math
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from app.i18n import PRIO_LABEL, t
from app.insights import severity_color
from app.state import toast

_CIRCUMFERENCE = 2 * math.pi * 52


def _fmt_money(v: float) -> str:
    if abs(v) >= 1000:
        return f"${v / 1000:.1f}k"
    return f"${v:,.0f}"


def _relative_time(iso: str | None, T: dict) -> str:
    if not iso:
        return ""
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


def _health_gauge(score: int, label: str) -> str:
    color = "#22C55E" if score >= 75 else "#F97316" if score >= 50 else "#EF4444"
    dash = _CIRCUMFERENCE * score / 100
    return f"""
    <div class="helix-gauge-wrap">
      <svg width="120" height="120" viewBox="0 0 120 120" style="transform:rotate(-90deg);">
        <circle cx="60" cy="60" r="52" fill="none" stroke="rgba(255,255,255,.08)" stroke-width="10"></circle>
        <circle cx="60" cy="60" r="52" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round"
          stroke-dasharray="{dash:.1f} {_CIRCUMFERENCE:.1f}"></circle>
      </svg>
      <div class="helix-gauge-center">
        <div class="helix-gauge-score">{score}</div>
        <div class="helix-gauge-label">{label}</div>
      </div>
    </div>
    """


def _build_summary_text(report_data: dict, T: dict) -> str:
    prio = PRIO_LABEL.get(st.session_state["lang"], PRIO_LABEL["ES"])
    lines = [f"{report_data['store_name']} — {T['analysisComplete']}", "", f"{T['priorityTitle']}:"]
    for action in report_data["priority_actions"]:
        lines.append(f"- [{prio[action['severity']]}] {action['text']} — {action['metric']}")
    lines.append("")
    for i, agent in enumerate(report_data["agents"]):
        rec = agent["recommendation"] or "—"
        lines.append(f"{T['agentNames'][i]} ({prio[agent['severity']]}): {rec}")
    return "\n".join(lines)


def _render_copy_button(text: str, label: str) -> None:
    safe_text = html.escape(text).replace("\n", "&#10;")
    components.html(
        f"""
        <textarea id="helix-copy-src" style="position:absolute;left:-9999px;">{safe_text}</textarea>
        <button id="helix-copy-btn" style="width:100%;background:transparent;color:#94A3B8;
          border:1px solid rgba(255,255,255,.25);border-radius:11px;padding:11px 16px;font-size:13.5px;
          font-weight:600;cursor:pointer;font-family:'Inter',sans-serif;">📋 {label}</button>
        <script>
          const btn = document.getElementById('helix-copy-btn');
          btn.addEventListener('click', () => {{
            const ta = document.getElementById('helix-copy-src');
            navigator.clipboard.writeText(ta.value).then(() => {{
              btn.innerText = '✓ Copiado';
              setTimeout(() => btn.innerText = '📋 {label}', 1800);
            }});
          }});
        </script>
        """,
        height=48,
    )


def _apply_action(i: int) -> None:
    st.session_state["actions_applied"][i] = True
    toast(t(st.session_state["lang"])["applied"])


def _toggle_result(i: int) -> None:
    st.session_state["expanded_results"][i] = not st.session_state["expanded_results"][i]


def _generate_pdf() -> None:
    from src.utils.pdf_exporter import export_to_pdf

    rd = st.session_state["report_data"]
    toast(t(st.session_state["lang"])["toastPdf"])
    path = export_to_pdf(rd["final_report_md"], store_name=rd["store_name"], period=rd["period"])
    with open(path, "rb") as f:
        st.session_state["pdf_bytes"] = f.read()
    st.session_state["pdf_name"] = path.split("/")[-1].split("\\")[-1]


def render_report_screen(on_new_analysis) -> None:
    T = t(st.session_state["lang"])
    prio = PRIO_LABEL.get(st.session_state["lang"], PRIO_LABEL["ES"])
    rd = st.session_state["report_data"]
    if rd is None:
        st.session_state["screen"] = "input"
        st.rerun()
        return

    generated_at = st.session_state.get("generated_at") or ""
    relative = _relative_time(st.session_state.get("generated_at_iso"), T)

    st.markdown(
        """<style>
        .st-key-pdf_gen_btn button, .st-key-pdf_download_btn button{
          background:#F97316 !important; color:#fff !important; border:none !important;
        }
        .st-key-pdf_gen_btn button:hover, .st-key-pdf_download_btn button:hover{ background:#ea6a0c !important; }
        .st-key-new_analysis_btn button{
          background:transparent !important; color:#5b8cff !important; border:1px solid #2563EB !important;
        }
        </style>""",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
            <h2 style="font-size:25px;margin:0;">{rd['store_name']}</h2>
            <span style="display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:600;
              color:#22C55E;background:rgba(34,197,94,.12);padding:5px 11px;border-radius:99px;">
              <span style="width:7px;height:7px;border-radius:50%;background:#22C55E;"></span>{T['analysisComplete']}
            </span>
          </div>
          <p style="margin:6px 0 0;color:#94A3B8;font-size:13.5px;">{T['generatedOn']} {generated_at}
            <span style="color:#475569;"> · {relative}</span></p>""",
        unsafe_allow_html=True,
    )
    b1, b2, b3 = st.columns(3)
    with b1:
        _render_copy_button(_build_summary_text(rd, T), T["copySummary"])
    with b2:
        if st.session_state.get("pdf_bytes"):
            st.download_button(
                f"⬇ {T['downloadPDF']}", data=st.session_state["pdf_bytes"],
                file_name=st.session_state.get("pdf_name", "reporte.pdf"),
                mime="application/pdf", use_container_width=True, key="pdf_download_btn",
            )
        else:
            st.button(f"⬇ {T['downloadPDF']}", key="pdf_gen_btn", on_click=_generate_pdf, use_container_width=True)
    with b3:
        if st.button(T["newAnalysis"], key="new_analysis_btn", use_container_width=True):
            on_new_analysis()
            st.rerun()

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    # ---- Resumen ejecutivo ----
    st.markdown('<style>.st-key-exec_summary_card{background:var(--surface);backdrop-filter:blur(12px);'
                'border:1px solid var(--border);border-radius:18px;padding:20px 22px;}</style>', unsafe_allow_html=True)
    with st.container(key="exec_summary_card"):
        st.markdown(f"### 🧭 {T['execTitle']} <span style='font-size:12px;color:#94A3B8;font-weight:400;'>{T['execSub']}</span>", unsafe_allow_html=True)
        gcol, kcol = st.columns([1, 3])
        with gcol:
            st.markdown(_health_gauge(rd["health_score"], T["healthLabel"]), unsafe_allow_html=True)
        with kcol:
            kpis = rd["kpis"]
            k1, k2, k3 = st.columns(3)
            tiles = [
                (_fmt_money(kpis["recoverable_revenue"]), T["kpiRecoverable"], "#22C55E"),
                (str(kpis["urgent_count"]), T["kpiUrgent"], "#EF4444"),
                (str(kpis["attention_count"]), T["kpiAttention"], "#F97316"),
            ]
            for col, (value, label, color) in zip((k1, k2, k3), tiles):
                with col:
                    st.markdown(
                        f"""<div class="helix-kpi-tile"><div class="helix-kpi-value" style="color:{color};">{value}</div>
                            <div class="helix-kpi-label">{label}</div></div>""",
                        unsafe_allow_html=True,
                    )
        st.markdown("<div style='height:14px;border-top:1px solid rgba(255,255,255,.07);'></div>", unsafe_allow_html=True)
        uplift = rd["projection"]["uplift_pct"]
        actual_h, projected_h = 64, min(110, round(64 * (1 + uplift / 100)))
        st.markdown(f'<div style="font-size:12px;color:#94A3B8;margin-bottom:8px;">{T["projectionLabel"]}</div>', unsafe_allow_html=True)
        st.markdown(
            f"""<div style="display:flex;align-items:flex-end;gap:22px;height:110px;">
                <div style="display:flex;flex-direction:column;align-items:center;gap:6px;">
                  <div style="width:40px;height:{actual_h}px;background:rgba(148,163,184,.35);border-radius:8px 8px 0 0;"></div>
                  <div style="font-size:11px;color:#94A3B8;">{T['projectionActual']}</div>
                </div>
                <div style="display:flex;flex-direction:column;align-items:center;gap:6px;">
                  <div style="width:40px;height:{projected_h}px;background:linear-gradient(180deg,#22C55E,#16a34a);
                    border-radius:8px 8px 0 0;box-shadow:0 0 18px rgba(34,197,94,.5);"></div>
                  <div style="font-size:11px;color:#22C55E;font-weight:600;">{T['projectionProjected']} +{uplift}%</div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ---- Acciones prioritarias ----
    st.markdown(
        '<style>.st-key-priority_actions_card{background:linear-gradient(#0e1020,#0e1020) padding-box,'
        'linear-gradient(135deg,rgba(249,115,22,.75),rgba(37,99,235,.5)) border-box;border:1px solid transparent;'
        'border-radius:18px;padding:20px 22px;}</style>',
        unsafe_allow_html=True,
    )
    with st.container(key="priority_actions_card"):
        st.markdown(f"#### ⚡ {T['priorityTitle']} <span style='font-size:12px;color:#94A3B8;font-weight:400;'>{T['prioritySub']}</span>", unsafe_allow_html=True)
        for i, action in enumerate(rd["priority_actions"]):
            color, bg = severity_color(action["severity"])
            applied = st.session_state["actions_applied"][i] if i < len(st.session_state["actions_applied"]) else False
            acol1, acol2 = st.columns([5, 1])
            with acol1:
                st.markdown(
                    f"""<div class="helix-priority-item">
                        <span class="helix-priority-icon" style="background:{bg};">{action['icon']}</span>
                        <div class="helix-priority-text"><div class="t">{action['text']}</div><div class="m">{action['metric']}</div></div>
                        <span class="helix-badge" style="color:{color};background:{bg};">{prio[action['severity']]}</span>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with acol2:
                if applied:
                    st.button(T["applied"], key=f"applied_{i}", disabled=True, use_container_width=True)
                else:
                    st.button(T["applyAction"], key=f"apply_{i}", on_click=_apply_action, args=(i,), use_container_width=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ---- Tarjetas de resultado por agente ----
    icons = ["📊", "📦", "👤", "🔍"]
    cols = st.columns(2)
    for i, agent in enumerate(rd["agents"]):
        color, bg = severity_color(agent["severity"])
        key = f"agent_card_{i}"
        st.markdown(
            f'<style>.st-key-{key}{{background:var(--surface);backdrop-filter:blur(12px);'
            f'border:1px solid var(--border);border-top:3px solid {color};border-radius:18px;'
            f'padding:20px;margin-bottom:12px;}}</style>',
            unsafe_allow_html=True,
        )
        with cols[i % 2]:
            with st.container(key=key):
                st.markdown(
                    f"""<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
                        <span class="helix-priority-icon" style="background:{bg};">{icons[i]}</span>
                        <span style="font-family:'Space Grotesk',sans-serif;font-size:16px;font-weight:700;flex:1;">{T['agentNames'][i]}</span>
                        <span class="helix-badge" style="color:{color};background:{bg};">{prio[agent['severity']]}</span>
                    </div>""",
                    unsafe_allow_html=True,
                )
                mcols = st.columns(3)
                for mcol, metric in zip(mcols, agent["metrics"]):
                    with mcol:
                        st.markdown(
                            f"""<div class="helix-metric-tile"><div class="helix-metric-value">{metric['value']}</div>
                                <div class="helix-metric-label">{metric['label']}</div>
                                <div class="helix-metric-delta">{metric['delta']}</div></div>""",
                            unsafe_allow_html=True,
                        )
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                if agent["findings"]:
                    for f in agent["findings"]:
                        st.markdown(f'<div class="helix-finding"><span class="dot" style="background:{color};"></span><span>{html.escape(f)}</span></div>', unsafe_allow_html=True)
                st.markdown(
                    f"""<div class="helix-rec-box" style="border-left-color:{color};">
                        <div class="lbl">{T['recLabel']}</div><div>{html.escape(agent['recommendation'] or '—')}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
                expanded = st.session_state["expanded_results"][i] if i < len(st.session_state["expanded_results"]) else False
                st.button(
                    T["viewLess"] if expanded else T["viewFull"], key=f"expand_result_{i}",
                    on_click=_toggle_result, args=(i,),
                )
                if expanded:
                    st.markdown(agent["full_analysis"] or "_Análisis no disponible._")

    if rd["errors"]:
        with st.expander("⚠️ Advertencias del análisis"):
            for err in rd["errors"]:
                st.caption(err)

    st.markdown(
        f"""<div class="helix-footer">
            <span>🧬 {T['footerBy']}</span>
            <span class="mono">v1.0 · {generated_at}</span>
        </div>""",
        unsafe_allow_html=True,
    )
