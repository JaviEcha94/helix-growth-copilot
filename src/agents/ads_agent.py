import logging

from langchain_core.messages import HumanMessage, SystemMessage

from src.graph.state import CampaignData, HelixState
from src.llm.providers import build_llm
from src.utils.parsers import safe_parse_analysis

logger = logging.getLogger("helix.agents.ads")

SYSTEM_PROMPT = """Sos un especialista en performance marketing para e-commerce.
Analizás métricas de campañas publicitarias y das recomendaciones concretas.
Respondés SIEMPRE en español, en formato Markdown estructurado.
Sos directo: cada recomendación tiene una acción clara (escalar / optimizar / pausar)."""


def _compute_metrics(campaigns: list[CampaignData]) -> list[dict]:
    results = []
    for c in campaigns:
        roas = c["revenue_ars"] / c["spend_ars"] if c["spend_ars"] > 0 else 0.0
        cpa = c["spend_ars"] / c["conversions"] if c["conversions"] > 0 else float("inf")
        ctr = (c["clicks"] / c["impressions"] * 100) if c["impressions"] > 0 else 0.0
        results.append(
            {
                "name": c["name"],
                "spend_ars": c["spend_ars"],
                "revenue_ars": c["revenue_ars"],
                "roas": round(roas, 2),
                "cpa_ars": round(cpa, 2),
                "ctr_pct": round(ctr, 2),
                "conversions": c["conversions"],
            }
        )
    return sorted(results, key=lambda x: x["roas"], reverse=True)


def _build_context(metrics: list[dict]) -> str:
    lines = ["| Campaña | ROAS | CPA (ARS) | CTR% | Conversiones |", "|---|---|---|---|---|"]
    for m in metrics:
        cpa_str = f"{m['cpa_ars']:,.0f}" if m["cpa_ars"] != float("inf") else "∞"
        lines.append(
            f"| {m['name']} | {m['roas']} | {cpa_str} | {m['ctr_pct']}% | {m['conversions']} |"
        )
    return "\n".join(lines)


def ads_node(state: HelixState) -> dict:
    logger.info("Agente Ads iniciado para tienda: %s", state["store_name"])

    if not state.get("campaigns"):
        logger.warning("No hay campañas para analizar.")
        return {"ads_analysis": [], "errors": ["Agente Ads: sin datos de campañas."]}

    try:
        metrics = _compute_metrics(state["campaigns"])
        context_table = _build_context(metrics)

        llm = build_llm()
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=f"""Analizá las campañas de publicidad de **{state['store_name']}**
para el período **{state.get('period', 'no especificado')}**.

## Métricas calculadas

{context_table}

**Benchmarks de referencia para e-commerce argentino:**
- ROAS mínimo rentable: 3.0x
- CPA máximo aceptable: ARS 15.000
- CTR saludable: > 1.5%

Generá un análisis con:
1. **Diagnóstico rápido** (1 párrafo)
2. **Campañas a escalar** (ROAS > 4x) — con razón
3. **Campañas a optimizar** (ROAS 2-4x) — con acción específica
4. **Campañas a pausar** (ROAS < 2x) — con razón
5. **Próximos 3 pasos prioritarios**
"""
            ),
        ]

        response = llm.invoke(messages)
        analysis = safe_parse_analysis(response.content, "ads")
        logger.info("Agente Ads completado (%d chars).", len(analysis))
        return {"ads_analysis": [analysis]}

    except Exception as exc:
        logger.error("Error fatal en Agente Ads: %s", exc, exc_info=True)
        return {
            "ads_analysis": [],
            "errors": [f"Agente Ads falló: {exc}"],
        }
