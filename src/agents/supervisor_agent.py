import logging
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage

from src.graph.state import HelixState
from src.llm.providers import build_llm
from src.utils.parsers import safe_parse_analysis

logger = logging.getLogger("helix.agents.supervisor")

SYSTEM_PROMPT = """Sos el director de estrategia de crecimiento de Helix, una fintech de pagos para e-commerce argentino.
Tu trabajo es sintetizar los análisis de 4 especialistas y producir un reporte ejecutivo priorizado.
El reporte debe ser accionable: el comerciante termina de leerlo y sabe exactamente qué hacer esta semana.
Respondés SIEMPRE en español, en formato Markdown bien estructurado.
Priorizás por impacto en revenue, no por facilidad de ejecución."""


def _collect_analyses(state: HelixState) -> dict[str, str]:
    return {
        "Ads": (state.get("ads_analysis") or [""])[0],
        "Producto": (state.get("product_analysis") or [""])[0],
        "Cliente": (state.get("customer_analysis") or [""])[0],
        "SEO": (state.get("seo_analysis") or [""])[0],
    }


def _format_analyses_block(analyses: dict[str, str]) -> str:
    blocks = []
    for agent, content in analyses.items():
        if content.strip():
            blocks.append(f"## Análisis del Especialista en {agent}\n\n{content}")
        else:
            blocks.append(f"## Análisis del Especialista en {agent}\n\n_No disponible._")
    return "\n\n---\n\n".join(blocks)


def supervisor_node(state: HelixState) -> dict:
    logger.info("Agente Supervisor iniciado — sintetizando análisis.")

    analyses = _collect_analyses(state)
    available = [k for k, v in analyses.items() if v.strip()]
    logger.info("Análisis disponibles para síntesis: %s", available)

    if not available:
        logger.error("Supervisor no tiene ningún análisis para sintetizar.")
        return {
            "final_report": "# Error: No hay análisis disponibles\n\nTodos los agentes fallaron. Revisá los logs.",
            "errors": ["Supervisor: ningún agente produjo análisis."],
        }

    analyses_block = _format_analyses_block(analyses)
    errors = state.get("errors", [])
    errors_note = (
        f"\n\n> **Nota:** Los siguientes agentes tuvieron errores: {', '.join(errors)}"
        if errors
        else ""
    )

    try:
        llm = build_llm()
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=f"""Sintetizá los siguientes análisis especializados para **{state['store_name']}**
(período: **{state.get('period', 'no especificado')}**) y producí el reporte ejecutivo final.

{analyses_block}

---

El reporte final debe tener esta estructura:

# Reporte de Crecimiento Helix — {state['store_name']}
**Período:** {state.get('period', 'no especificado')} | **Generado:** {datetime.now().strftime('%d/%m/%Y %H:%M')}

## Resumen Ejecutivo
_(3-4 oraciones: situación actual, mayor riesgo, mayor oportunidad)_

## Top 5 Acciones Esta Semana
_(Ordenadas por impacto. Cada acción: qué hacer, quién, métrica de éxito)_

## Análisis por Área

### Campañas Publicitarias
### Catálogo de Productos
### Retención de Clientes
### Visibilidad Orgánica (SEO)

## Métricas a Monitorear (próximas 2 semanas)
_(KPIs específicos con valores objetivo)_

## Riesgos a Mitigar
_(Máximo 3, con señal de alerta y plan de contingencia)_
{errors_note}
"""
            ),
        ]

        response = llm.invoke(messages)
        report = safe_parse_analysis(response.content, "supervisor")
        logger.info("Reporte final generado (%d chars).", len(report))
        return {"final_report": report}

    except Exception as exc:
        logger.error("Error fatal en Agente Supervisor: %s", exc, exc_info=True)
        fallback_report = _build_fallback_report(state, analyses)
        return {
            "final_report": fallback_report,
            "errors": [f"Supervisor LLM falló ({exc}) — reporte de emergencia generado."],
        }


def _build_fallback_report(state: HelixState, analyses: dict[str, str]) -> str:
    """Reporte de emergencia sin LLM cuando el supervisor falla."""
    lines = [
        f"# Reporte de Crecimiento Helix — {state['store_name']}",
        f"**Período:** {state.get('period', 'N/A')} | **Generado:** {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "",
        "> ⚠️ El agente supervisor falló. Este es un reporte de emergencia con los análisis crudos.",
        "",
    ]
    for agent, content in analyses.items():
        lines.append(f"## {agent}")
        lines.append(content if content.strip() else "_Sin análisis disponible._")
        lines.append("")
    return "\n".join(lines)
