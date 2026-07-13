"""
Motor de insights — deriva todo lo que necesita la pantalla de reporte
(severidad, health score, KPIs, acciones prioritarias, tiles de métricas)
en Python puro, a partir de los datos reales (sin pedirle al LLM que
devuelva JSON estructurado, que es frágil). Los textos de "findings" y
"recomendación" sí vienen del markdown real que devolvió cada agente.

No hay series temporales reales en un input de una sola foto (snapshot),
así que a diferencia del mockup no se muestran sparklines inventados:
las tiles de métrica muestran únicamente valor + delta textual.
"""
import re

_SEVERITY_SCORE = {"urgent": 40, "attention": 65, "optimize": 70, "ok": 90}
_SEVERITY_WEIGHT = {"urgent": 3, "attention": 2, "optimize": 1, "ok": 0}
_SEVERITY_COLOR = {
    "urgent": ("#EF4444", "rgba(239,68,68,.14)"),
    "attention": ("#F97316", "rgba(249,115,22,.14)"),
    "optimize": ("#2563EB", "rgba(37,99,235,.14)"),
    "ok": ("#22C55E", "rgba(34,197,94,.14)"),
}
_RECOVERY_RATE = 0.15

_BULLET_RE = re.compile(r"^\s*(?:[-*]|\d+\.)\s+(.+)$", re.MULTILINE)
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_ITALIC_RE = re.compile(r"(?<!\*)\*([^*]+?)\*(?!\*)")


def severity_color(level: str) -> tuple[str, str]:
    return _SEVERITY_COLOR.get(level, _SEVERITY_COLOR["ok"])


def _md_inline_to_html(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = _BOLD_RE.sub(r"<b>\1</b>", text)
    text = _ITALIC_RE.sub(r"<i>\1</i>", text)
    return text


def extract_bullets(md: str, limit: int = 3) -> list[str]:
    if not md:
        return []
    bullets = [m.strip() for m in _BULLET_RE.findall(md)]
    return bullets[:limit]


_NEXT_STEPS_RE = re.compile(r"pr[oó]ximos|pasos\s+priorit", re.IGNORECASE)


def _split_at_next_steps(md: str) -> tuple[str, str]:
    """Los prompts de los agentes piden "Próximos 3 pasos prioritarios" como
    ítem de lista numerada (no como heading Markdown '#'), así que se busca
    por substring en vez de con extract_markdown_section. Devuelve
    (cuerpo_antes, sección_pasos_siguientes)."""
    match = _NEXT_STEPS_RE.search(md or "")
    if not match:
        return md or "", ""
    return md[: match.start()], md[match.start():]


def extract_recommendation(md: str) -> str:
    """Primer punto de la sección de próximos pasos; si no hay, primer bullet."""
    if not md:
        return ""
    body, next_steps = _split_at_next_steps(md)
    bullets = extract_bullets(next_steps, limit=1) if next_steps else []
    if not bullets:
        bullets = extract_bullets(md, limit=1)
    return bullets[0] if bullets else md.strip().split("\n")[0]


def _ads_insight(extra: dict) -> dict:
    roas, cpa, ctr = extra["roas"], extra["cpa"], extra["ctr"]
    if roas < 2:
        severity = "urgent"
    elif roas < 3:
        severity = "attention"
    elif roas < 4:
        severity = "optimize"
    else:
        severity = "ok"
    metrics = [
        {"label": "ROAS", "value": f"{roas:g}x", "delta": ("▼" if roas < 3 else "▲") + f" vs meta 3.0x"},
        {"label": "CPA", "value": f"${cpa:,.0f}", "delta": ("▲" if cpa > 15000 else "▼") + " vs benchmark $15.000"},
        {"label": "CTR", "value": f"{ctr:g}%", "delta": ("▼" if ctr < 1.5 else "▲") + " vs benchmark 1.5%"},
    ]
    return {"severity": severity, "metrics": metrics}


def _product_insight(extra: dict) -> dict:
    units, stock = extra["units"], extra["stock"]
    daily_sales = units / 30 if units > 0 else 0
    runway_days = (stock / daily_sales) if daily_sales > 0 else float("inf")
    if runway_days < 7:
        severity = "urgent"
    elif runway_days < 21:
        severity = "attention"
    else:
        severity = "ok"
    runway_label = "sin ventas" if runway_days == float("inf") else f"~{runway_days:.0f} días"
    metrics = [
        {"label": "SKUs totales", "value": str(extra["skus_total"]), "delta": ""},
        {"label": "Unidades vendidas (30d)", "value": str(units), "delta": ""},
        {"label": "Stock disponible", "value": str(stock), "delta": f"cobertura {runway_label}"},
    ]
    return {"severity": severity, "metrics": metrics}


def _customer_insight(extra: dict) -> dict:
    abandono, recompra, ticket = extra["abandono"], extra["recompra"], extra["ticket"]
    if abandono >= 60:
        severity = "urgent"
    elif abandono >= 40:
        severity = "attention"
    else:
        severity = "ok"
    metrics = [
        {"label": "Abandono carrito", "value": f"{abandono:g}%", "delta": "▲ sobre benchmark 60%" if abandono >= 60 else "dentro de benchmark"},
        {"label": "Recompra", "value": f"{recompra:g}%", "delta": "▼ bajo benchmark 20%" if recompra < 20 else "▲ saludable"},
        {"label": "Ticket promedio", "value": f"${ticket:,.0f}", "delta": ""},
    ]
    return {"severity": severity, "metrics": metrics}


def _seo_insight(extra: dict) -> dict:
    has_competitor = bool(extra["competidores"])
    severity = "optimize" if has_competitor else "attention"
    metrics = [
        {"label": "Dominio", "value": extra["dominio_propio"] or "—", "delta": ""},
        {"label": "Keywords objetivo", "value": str(extra["keywords_target"]), "delta": ""},
        {"label": "Temas a investigar", "value": str(len(extra["temas"])), "delta": "" if has_competitor else "sin competidores cargados"},
    ]
    return {"severity": severity, "metrics": metrics}


def compute_agent_insights(extra: dict) -> list[dict]:
    """Orden fijo: Ads, Producto, Cliente, SEO (igual que el mockup)."""
    return [_ads_insight(extra), _product_insight(extra), _customer_insight(extra), _seo_insight(extra)]


def compute_health_score(agent_insights: list[dict]) -> int:
    total = sum(_SEVERITY_SCORE[a["severity"]] for a in agent_insights)
    return round(total / len(agent_insights))


def compute_recoverable_revenue(extra: dict) -> float:
    """orders≈unidades vendidas; carritos abandonados ≈ orders/(1-abandono) - orders."""
    orders = extra["units"]
    abandonment_rate = extra["abandono"] / 100
    if abandonment_rate <= 0 or abandonment_rate >= 1 or orders <= 0:
        return 0.0
    total_carts = orders / (1 - abandonment_rate)
    abandoned_carts = total_carts - orders
    return abandoned_carts * extra["ticket"] * _RECOVERY_RATE


def compute_kpis(agent_insights: list[dict], extra: dict) -> dict:
    urgent_count = sum(1 for a in agent_insights if a["severity"] == "urgent")
    attention_count = sum(1 for a in agent_insights if a["severity"] == "attention")
    return {
        "recoverable_revenue": compute_recoverable_revenue(extra),
        "urgent_count": urgent_count,
        "attention_count": attention_count,
    }


def compute_priority_actions(agent_insights: list[dict], extra: dict) -> list[dict]:
    icons = ["📊", "📦", "👤", "🔍"]
    candidates = [
        {"icon": icons[0], "agent_index": 0,
         "text": f"Optimizar campañas — ROAS actual {extra['roas']:g}x",
         "metric": f"${extra['budget']:,.0f} de presupuesto activo · CPA ${extra['cpa']:,.0f}",
         "severity": agent_insights[0]["severity"]},
        {"icon": icons[1], "agent_index": 1,
         "text": "Reponer stock antes del quiebre",
         "metric": f"{extra['stock']} unidades en stock · {extra['units']} vendidas en 30d",
         "severity": agent_insights[1]["severity"]},
        {"icon": icons[2], "agent_index": 2,
         "text": "Activar recuperación de carrito abandonado",
         "metric": f"{extra['abandono']:g}% de abandono · ~${compute_recoverable_revenue(extra):,.0f} recuperables/mes",
         "severity": agent_insights[2]["severity"]},
        {"icon": icons[3], "agent_index": 3,
         "text": "Completar datos de competencia para el análisis SEO" if agent_insights[3]["severity"] == "attention" else "Publicar contenido para las keywords objetivo",
         "metric": f"{extra['keywords_target']} keywords objetivo · {len(extra['competidores'])} competidores cargados",
         "severity": agent_insights[3]["severity"]},
    ]
    candidates.sort(key=lambda c: _SEVERITY_WEIGHT[c["severity"]], reverse=True)
    return candidates[:3]


def compute_projection(kpis: dict, extra: dict) -> dict:
    """Barra 'Actual vs Proyectado' — % de suba estimado a partir del ingreso recuperable."""
    current_revenue = extra["budget"] * extra["roas"] + extra["ticket"] * extra["units"]
    if current_revenue > 0:
        uplift_pct = min(40, round((kpis["recoverable_revenue"] / current_revenue) * 100))
    else:
        uplift_pct = 0
    return {"uplift_pct": uplift_pct}


_ANALYSIS_KEYS = ["ads_analysis", "product_analysis", "customer_analysis", "seo_analysis"]


def build_report_data(extra: dict, accumulated: dict, store_name: str, period: str) -> dict:
    """Combina los números reales (insights) con el markdown real de cada agente.
    El resultado no depende del idioma de la UI — los nombres/labels se resuelven
    en el momento de renderizar, así el usuario puede cambiar ES/EN/PT sin
    tener que regenerar el análisis."""
    agent_insights = compute_agent_insights(extra)
    health_score = compute_health_score(agent_insights)
    kpis = compute_kpis(agent_insights, extra)
    projection = compute_projection(kpis, extra)
    priority_actions = compute_priority_actions(agent_insights, extra)

    analyses = []
    for key in _ANALYSIS_KEYS:
        values = accumulated.get(key) or []
        analyses.append(values[0] if values else "")

    agents = []
    for i, insight in enumerate(agent_insights):
        raw_md = analyses[i]
        body, next_steps = _split_at_next_steps(raw_md)
        findings = extract_bullets(body, limit=3) or extract_bullets(raw_md, limit=3)
        agents.append({
            "severity": insight["severity"],
            "metrics": insight["metrics"],
            "findings": findings,
            "recommendation": extract_recommendation(raw_md),
            "full_analysis": raw_md,
        })

    return {
        "store_name": store_name,
        "period": period,
        "health_score": health_score,
        "kpis": kpis,
        "projection": projection,
        "priority_actions": priority_actions,
        "agents": agents,
        "errors": accumulated.get("errors", []),
        "final_report_md": accumulated.get("final_report", ""),
    }
