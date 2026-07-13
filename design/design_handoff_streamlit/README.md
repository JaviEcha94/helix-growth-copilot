# Handoff: Helix Growth Copilot — Streamlit Recreation

## Overview
Helix Growth Copilot is a multi-agent ecommerce growth analysis tool. Merchants enter data across 4 categories (Campaigns, Products, Customers, SEO), trigger an AI-agent analysis, and receive a report with prioritized actions and per-agent findings.

## About the Design Files
The bundled file (`Helix Growth Copilot.dc.html`) is a **design reference built in HTML** — a working prototype showing the intended look, copy, states, and interactions. It is not production code to paste into the app. The task is to **recreate this design in Streamlit** (Python), using Streamlit's own components/layout system (`st.columns`, `st.expander`, `st.progress`, `st.session_state`, custom CSS via `st.markdown`, etc.) rather than embedding the HTML directly.

## Fidelity
**High-fidelity.** Colors, typography, spacing, copy, and animation intent are final. Recreate pixel-close where Streamlit's component model allows; where Streamlit can't match an effect exactly (e.g. blurred glow, custom SVG gauges), approximate with the closest native or custom-CSS equivalent and note the gap.

## Screens / Views

### 1. Input (`st.session_state.screen == "input"`)
- **Purpose**: Merchant enters store data.
- **Layout**: Sticky header (logo + tagline + status dot + history/density/lang controls) → breadcrumb (Datos → Análisis → Reporte) → hero (eyebrow label, H1, subtitle, 3 tech chips: Multi-agente / RAG / LangGraph) → 4 collapsible cards in a 2-col responsive grid (Campañas 📊, Productos 📦, Clientes 👤, SEO 🔍) → CTA area (empty-state warning if no fields filled, "⚡ Generar Reporte" button, "Cargar datos de ejemplo" link, time estimate, first-run coachmark tooltip).
- **Cards**: header row is icon box + title + description + status badge (Completo/Pendiente/n of 4) + chevron, click toggles expand. Body reveals a field grid (labels, optional `?` tooltip, text input, green ✓ check when valid, red inline error text when invalid+touched).
- **Field validation by type**: `multiplier` (e.g. `3.5x`), `currency` (numeric), `percent` (0–100), `integer`, `domain` (regex), free `text`.

### 2. Loading (`screen == "loading"`)
- **Purpose**: Shows the 4 agents (Ads, Producto, Cliente, SEO) working sequentially.
- **Layout**: Centered title with subtle glow pulse, dynamic status line ("Analizando campañas…"), 4 agent status cards (○ waiting / ⟳ processing / ✓ done), animated striped progress bar with percentage, skeleton placeholders for the report, "Cancelar análisis" link.
- Progress drives which agent is "processing" vs "done" (roughly 0-25% agent 1, 25-50% agent 2, 50-75% agent 3, 75-100% agent 4).

### 3. Error (`screen == "error"`)
- Triggered by a demo toggle (simulates connection failure ~46% progress). Centered icon, title "No se pudo conectar", message, "Reintentar →" button that restarts the loading sequence.

### 4. Report (`screen == "report"`)
- **Header**: store name + "Análisis completado" badge, generated date + relative time ("hace X min"), buttons: Copiar resumen / Descargar PDF / Nuevo análisis.
- **Executive Summary card**: circular health-score gauge (0–100, red <50 / orange 50–74 / green ≥75, computed as average of per-agent severity scores), 3 KPI tiles (Ingresos recuperables $17.2k, Acciones urgentes, Agentes en atención), and a small 2-bar "Actual vs Proyectado (+12%)" projection chart.
- **Acciones Prioritarias**: orange/blue-gradient-bordered card, top-3 list, each row = agent icon, action text + supporting metric, priority badge (Urgente/Atención/Optimizar), and an "Aplicar" button that flips to a disabled "Aplicada ✓" state.
- **4 Agent Result cards** (grid, 2 cols): agent icon + name + overall priority badge (color-coded top border + glow matching severity) → 3 metric tiles (big number, label, colored delta, small 7-point sparkline trend) → bullet findings → highlighted recommendation box → "Ver análisis completo" toggle revealing one extra detail paragraph.
- **Footer**: "Generado por Helix Growth Copilot" + version/timestamp.

## Interactions & Behavior
- **Language switcher (ES/EN/PT)**: full UI string swap (see Design Tokens/i18n note below) — persisted to local storage/session.
- **History panel**: header "🕓 Historial" button opens a dropdown of up to 5 past generated reports (store name, relative time, health-score chip); clicking loads that report.
- **Density toggle**: "Cómodo"/"Compacto" — reduces padding/gaps across cards.
- **Persistence**: form field values, language, density, and history persist across reloads (localStorage in the HTML reference → use `st.session_state` + a small local file or browser storage equivalent in Streamlit).
- **Toasts**: bottom-center transient confirmation (data loaded, action applied, summary copied, analysis cancelled, generating PDF) — use `st.toast()`.
- **Copy resumen**: builds a plain-text summary (store + priority actions + per-agent recommendation) to clipboard.
- **Empty state**: clicking "Generar Reporte" with zero fields filled shows an inline warning instead of proceeding.
- **Coachmark**: first-visit-only tooltip near "Cargar datos de ejemplo", dismissed permanently once closed.
- **Accessibility**: focus-visible outlines on all interactive elements, `aria-expanded` on collapsible cards, `aria-pressed` on language buttons, `role="status"`/`aria-live="polite"` on toasts, `role="progressbar"` with `aria-valuenow` on the loading bar.

## State Management
Key state (mirror with `st.session_state`):
- `screen`: `input | loading | error | report`
- `lang`: `ES | EN | PT`
- `form`: dict of field key → value; `touched`: dict of field key → bool
- `expanded`: dict of card id → bool (input screen)
- `progress`: int 0–100; `agent_status`: list of 4 (`waiting|processing|done`)
- `density`: `comfortable | compact`
- `history`: list of `{id, store_name, date_iso, health_score}` (max 5)
- `actions_applied`: list of 3 bool; `expanded_results`: list of 4 bool
- `show_coachmark`: bool (one-time)

## Design Tokens
- **Colors**: background `#07070C`, surface `rgba(18,20,34,.55)` (glass/blur), primary blue `#2563EB`, accent teal `#00D4AA`, accent orange `#F97316`, success `#22C55E`, danger `#EF4444`, text `#FFFFFF` / secondary `#94A3B8`.
- **Typography**: headings/numbers `Space Grotesk` (600–700), labels/mono accents `JetBrains Mono`, body `Inter` (400–600).
- **Radius**: 10–18px depending on element size. **Shadows/glow**: colored box-shadows matching each severity color (e.g. red glow on urgent cards, blue glow on primary CTA).
- **Priority colors**: Urgente `#EF4444`, Atención `#F97316`, Optimizar/OK `#2563EB`/`#22C55E`.

## i18n
All copy exists in ES/EN/PT in the HTML reference's `I18N` object — reuse those exact strings (don't re-translate) when building the Streamlit string tables.

## Assets
No external image assets — icons are emoji, charts are inline SVG (gauge arc + sparkline polylines) generated from data, no illustrations used.

## Screenshots
See `screenshots/01-input.png`, `02-loading.png`, `03-report.png` for reference renders of each screen.

## Files
- `Helix Growth Copilot.dc.html` — full interactive HTML reference (open in any browser). Contains all copy, the `I18N` translation table, exact color/spacing values, and the complete interaction logic to mirror in Python/Streamlit.
- `screenshots/` — static captures of the 3 main screens.
