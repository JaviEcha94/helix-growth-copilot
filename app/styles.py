"""
CSS global inyectado una vez por app.py — porta los design tokens del
handoff (colores, tipografía, radios, glow) al layout de Streamlit.
"""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root{
  --bg:#07070C; --surface:rgba(18,20,34,.55); --surface-solid:#0e1020;
  --border:rgba(255,255,255,.09);
  --blue:#2563EB; --teal:#00D4AA; --orange:#F97316;
  --success:#22C55E; --danger:#EF4444;
  --text:#FFFFFF; --text2:#94A3B8; --text3:#64748b;
}

@keyframes spin{to{transform:rotate(360deg)}}
@keyframes pulseDot{0%,100%{opacity:1}50%{opacity:.3}}
@keyframes screenIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
@keyframes fadeSlideIn{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@keyframes barGlow{0%,100%{box-shadow:0 0 10px rgba(37,99,235,.45)}50%{box-shadow:0 0 22px rgba(37,99,235,.9)}}
@keyframes sheen{0%{background-position:0% 0}100%{background-position:220% 0}}
@keyframes ringPulse{0%{transform:scale(.8);opacity:.7}70%{transform:scale(1.5);opacity:0}100%{opacity:0}}
@keyframes blobFloat{0%,100%{transform:translate(0,0)}50%{transform:translate(0,30px)}}
@keyframes titleGlow{0%,100%{text-shadow:0 0 18px rgba(37,99,235,.45)}50%{text-shadow:0 0 30px rgba(37,99,235,.8)}}
@keyframes stripeMove{from{background-position:0 0}to{background-position:28px 0}}

html, body, [class*="css"]{ font-family:'Inter',system-ui,-apple-system,sans-serif; }
.stApp{
  background:var(--bg) !important;
  color:var(--text);
}
.stApp:before{
  content:"";
  position:fixed; top:-180px; right:-100px; width:600px; height:600px; border-radius:50%;
  background:radial-gradient(circle,rgba(37,99,235,.28),transparent 70%); filter:blur(24px);
  pointer-events:none; z-index:0; animation:blobFloat 11s ease-in-out infinite;
}
.stApp:after{
  content:"";
  position:fixed; bottom:-220px; left:-160px; width:540px; height:540px; border-radius:50%;
  background:radial-gradient(circle,rgba(249,115,22,.18),transparent 70%); filter:blur(24px);
  pointer-events:none; z-index:0; animation:blobFloat 13s ease-in-out infinite reverse;
}
.block-container{ padding-top:1.1rem; max-width:1180px; position:relative; z-index:1; }
#MainMenu, footer{ visibility:hidden; }

h1,h2,h3,h4, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3{
  font-family:'Space Grotesk',sans-serif !important; letter-spacing:-.02em;
}
code, .mono{ font-family:'JetBrains Mono',monospace !important; }

.helix-eyebrow{
  font-family:'JetBrains Mono',monospace; font-size:11.5px; letter-spacing:.18em;
  text-transform:uppercase; color:#5b8cff; margin-bottom:6px; display:flex; align-items:center; gap:8px;
}
.helix-eyebrow:before{ content:""; width:6px; height:6px; border-radius:50%; background:var(--blue); box-shadow:0 0 9px var(--blue); }

.helix-chip{
  font-family:'JetBrains Mono',monospace; font-size:11px; letter-spacing:.03em; color:#93b4ff;
  background:rgba(37,99,235,.12); border:1px solid rgba(37,99,235,.32);
  padding:5px 11px; border-radius:7px; display:inline-block; margin:2px 6px 2px 0;
  box-shadow:0 0 14px rgba(37,99,235,.12);
}

.helix-badge{ font-size:12px; font-weight:600; padding:4px 10px; border-radius:99px; white-space:nowrap; }
.helix-badge.complete{ color:var(--success); background:rgba(34,197,94,.12); }
.helix-badge.pending{ color:var(--text2); background:rgba(148,163,184,.1); }

.helix-status-dot{ display:inline-flex; align-items:center; gap:7px; font-size:12.5px; color:var(--text2); }
.helix-status-dot span{ width:8px; height:8px; border-radius:50%; background:var(--success); box-shadow:0 0 8px var(--success); animation:pulseDot 2.2s infinite; display:inline-block; }

.helix-crumbs{ display:flex; align-items:center; gap:9px; font-size:13px; margin-bottom:6px; }
.helix-crumbs .arrow{ color:#475569; font-size:12px; }
.helix-crumb-active{ color:#fff; font-weight:600; }
.helix-crumb-done{ color:var(--success); font-weight:500; }
.helix-crumb-pending{ color:#475569; font-weight:500; }

.helix-logo-badge{
  width:40px; height:40px; border-radius:12px;
  background:linear-gradient(135deg,#2563EB,#00D4AA 55%,#F97316);
  display:flex; align-items:center; justify-content:center;
  font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:21px; color:#fff;
  box-shadow:0 0 26px rgba(37,99,235,.6);
}

.helix-priority-item{
  display:flex; align-items:center; gap:14px; padding:13px 15px;
  background:rgba(7,7,12,.5); border:1px solid rgba(255,255,255,.06); border-radius:12px;
  margin-bottom:10px;
}
.helix-priority-icon{ width:40px; height:40px; border-radius:11px; display:flex; align-items:center; justify-content:center; font-size:18px; flex-shrink:0; }
.helix-priority-text{ flex:1; min-width:0; }
.helix-priority-text .t{ font-size:14.5px; font-weight:600; }
.helix-priority-text .m{ font-size:12.5px; color:var(--text2); margin-top:2px; }

.helix-metric-tile{
  background:rgba(7,7,12,.55); border:1px solid rgba(255,255,255,.05); border-radius:11px; padding:12px;
}
.helix-metric-value{ font-family:'Space Grotesk',sans-serif; font-size:22px; font-weight:700; letter-spacing:-.01em; }
.helix-metric-label{ font-size:11.5px; color:var(--text2); margin-top:2px; }
.helix-metric-delta{ font-size:11px; font-weight:500; margin-top:2px; }

.helix-rec-box{ background:rgba(255,255,255,.03); border-left:3px solid var(--blue); border-radius:0 10px 10px 0; padding:13px 15px; margin-top:10px; }
.helix-rec-box .lbl{ font-family:'JetBrains Mono',monospace; font-size:10.5px; font-weight:600; letter-spacing:.08em; text-transform:uppercase; color:var(--text2); margin-bottom:5px; }

.helix-finding{ display:flex; gap:10px; align-items:flex-start; font-size:13.5px; color:#cbd5e1; line-height:1.45; margin-bottom:6px; }
.helix-finding .dot{ width:6px; height:6px; border-radius:50%; margin-top:6px; flex-shrink:0; }

.helix-gauge-wrap{ position:relative; width:120px; height:120px; flex-shrink:0; }
.helix-gauge-center{ position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; }
.helix-gauge-score{ font-family:'Space Grotesk',sans-serif; font-size:32px; font-weight:700; }
.helix-gauge-label{ font-size:10px; color:var(--text2); letter-spacing:.04em; text-align:center; }

.helix-kpi-tile{ background:rgba(7,7,12,.5); border:1px solid rgba(255,255,255,.06); border-radius:12px; padding:14px; }
.helix-kpi-value{ font-family:'Space Grotesk',sans-serif; font-size:21px; font-weight:700; }
.helix-kpi-label{ font-size:11.5px; color:var(--text2); margin-top:4px; }

.helix-agent-card{ border-radius:14px; padding:16px; display:flex; flex-direction:column; gap:8px; backdrop-filter:blur(8px); transition:all .3s; }
.helix-agent-card.waiting{ background:rgba(255,255,255,.02); border:1px solid rgba(255,255,255,.06); }
.helix-agent-card.processing{ background:rgba(37,99,235,.1); border:1px solid rgba(37,99,235,.4); box-shadow:0 0 26px rgba(37,99,235,.28); }
.helix-agent-card.done{ background:rgba(34,197,94,.06); border:1px solid rgba(34,197,94,.25); }
.helix-agent-icon{ font-size:17px; display:inline-block; }
.helix-agent-icon.processing{ color:#5b8cff; animation:spin 1s linear infinite; }
.helix-agent-icon.done{ color:var(--success); }
.helix-agent-icon.waiting{ color:#475569; }
.helix-agent-name{ font-family:'Space Grotesk',sans-serif; font-size:13.5px; font-weight:600; }
.helix-agent-sub{ font-size:12px; color:var(--text2); }
.helix-agent-status{ font-size:12px; font-weight:500; }
.helix-agent-status.processing{ color:#5b8cff; }
.helix-agent-status.done{ color:var(--success); }
.helix-agent-status.waiting{ color:#64748b; }

.helix-progress-outer{ position:relative; height:12px; background:rgba(18,20,34,.7); border:1px solid rgba(255,255,255,.06); border-radius:99px; overflow:hidden; box-shadow:inset 0 1px 4px rgba(0,0,0,.55); }
.helix-progress-fill{ position:relative; height:100%; background:repeating-linear-gradient(45deg,#2563EB 0,#2563EB 10px,#60a5fa 10px,#60a5fa 20px); background-size:28px 28px; border-radius:99px; animation:stripeMove .6s linear infinite, barGlow 1.8s ease-in-out infinite; box-shadow:0 0 16px rgba(37,99,235,.75); transition:width .3s ease; }

.helix-loading-title{ font-family:'Space Grotesk',sans-serif; font-size:25px; font-weight:700; text-align:center; animation:titleGlow 3s ease-in-out infinite; }
.helix-loading-msg{ text-align:center; color:var(--blue); font-size:14.5px; font-weight:500; min-height:20px; }
.helix-loading-sub{ text-align:center; color:#64748b; font-size:12.5px; font-family:'JetBrains Mono',monospace; }

.helix-error-icon{ width:72px; height:72px; border-radius:20px; background:rgba(239,68,68,.12); border:1px solid rgba(239,68,68,.4); display:flex; align-items:center; justify-content:center; font-size:32px; margin:0 auto 20px; box-shadow:0 0 30px rgba(239,68,68,.2); }

.helix-footer{ margin-top:24px; padding-top:18px; border-top:1px solid rgba(255,255,255,.07); display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; color:#64748b; font-size:12.5px; }

/* Streamlit widget re-skin */
div[data-testid="stTextInput"] input{
  background:rgba(7,7,12,.6) !important; border:1px solid rgba(255,255,255,.1) !important;
  border-radius:10px !important; color:#fff !important;
}
div[data-testid="stTextInput"] input:focus{ border-color:var(--blue) !important; box-shadow:0 0 0 3px rgba(37,99,235,.18) !important; }
.stButton>button{ border-radius:11px !important; font-family:'Space Grotesk',sans-serif !important; font-weight:600 !important; }
.stButton>button:focus-visible{ outline:2px solid #93b4ff !important; }

/* Las tarjetas de input del mockup son compactas: el gap por defecto de
   Streamlit entre widgets (16px) sumado a la línea de validación aparte
   hacía que cada campo se viera muy separado del siguiente. */
div[data-testid="stExpanderDetails"] [data-testid="stVerticalBlock"]{ gap:0.3rem !important; }
div[data-testid="stExpanderDetails"] [data-testid="stMarkdownContainer"] p{ margin:0 !important; }

.helix-coachmark{
  background:linear-gradient(135deg,#2563EB,#00D4AA); color:#07070C; padding:10px 14px; border-radius:12px;
  font-size:12.5px; font-weight:600; box-shadow:0 12px 34px rgba(37,99,235,.5); text-align:center; margin-top:8px;
}
</style>
"""

COMPACT_CSS = """
<style>
.st-key-exec_summary_card, .st-key-priority_actions_card, [class*="st-key-agent_card_"]{
  padding:12px 14px !important;
}
.helix-metric-tile, .helix-kpi-tile{ padding:8px !important; }
.helix-priority-item{ padding:8px 10px !important; }
div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stVerticalBlock"]{ gap:0.4rem !important; }
</style>
"""
