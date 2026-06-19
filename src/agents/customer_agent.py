import logging

from langchain_core.messages import HumanMessage, SystemMessage

from src.graph.state import CustomerData, HelixState
from src.llm.providers import build_llm
from src.utils.parsers import safe_parse_analysis

logger = logging.getLogger("helix.agents.customer")

SYSTEM_PROMPT = """Sos un especialista en retención de clientes y CRO para e-commerce.
Analizás el comportamiento del cliente: abandono de carrito, segmentación y valor del ciclo de vida.
Respondés SIEMPRE en español, en formato Markdown.
Priorizás acciones con mayor impacto en revenue, no en vanity metrics."""

_HIGH_ABANDONMENT_THRESHOLD = 0.60
_LOW_REPEAT_THRESHOLD = 0.20


def _diagnose_health(metrics: CustomerData) -> list[str]:
    flags = []
    if metrics["cart_abandonment_rate"] >= _HIGH_ABANDONMENT_THRESHOLD:
        flags.append(
            f"Abandono de carrito CRÍTICO: {metrics['cart_abandonment_rate']:.0%} "
            f"(benchmark: < {_HIGH_ABANDONMENT_THRESHOLD:.0%})"
        )
    if metrics["repeat_purchase_rate"] <= _LOW_REPEAT_THRESHOLD:
        flags.append(
            f"Tasa de recompra BAJA: {metrics['repeat_purchase_rate']:.0%} "
            f"(benchmark: > {_LOW_REPEAT_THRESHOLD:.0%})"
        )
    return flags


def customer_node(state: HelixState) -> dict:
    logger.info("Agente Cliente iniciado para tienda: %s", state["store_name"])

    metrics = state.get("customer_metrics")
    if not metrics:
        logger.warning("No hay métricas de cliente para analizar.")
        return {"customer_analysis": [], "errors": ["Agente Cliente: sin métricas de cliente."]}

    try:
        health_flags = _diagnose_health(metrics)
        flags_text = "\n".join(f"- ⚠️ {f}" for f in health_flags) if health_flags else "- Sin alertas críticas detectadas."

        llm = build_llm()
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=f"""Analizá el comportamiento de clientes de **{state['store_name']}**
para el período **{state.get('period', 'no especificado')}**.

## Métricas clave

| Métrica | Valor |
|---|---|
| Sesiones totales | {metrics['total_sessions']:,} |
| Tasa de abandono de carrito | {metrics['cart_abandonment_rate']:.1%} |
| Tasa de recompra | {metrics['repeat_purchase_rate']:.1%} |
| Ticket promedio | ARS {metrics['avg_order_value_ars']:,.0f} |
| Segmentos top | {', '.join(metrics.get('top_segments', []))} |

## Alertas detectadas automáticamente

{flags_text}

Generá un análisis con:
1. **Diagnóstico de retención** (1 párrafo)
2. **Estrategia de recuperación de carritos abandonados** — secuencia concreta
3. **Acciones por segmento** — al menos 2 segmentos con tácticas específicas
4. **Palancas para aumentar recompra** — con métricas objetivo
5. **Próximos 3 pasos prioritarios**
"""
            ),
        ]

        response = llm.invoke(messages)
        analysis = safe_parse_analysis(response.content, "cliente")
        logger.info("Agente Cliente completado (%d chars).", len(analysis))
        return {"customer_analysis": [analysis]}

    except Exception as exc:
        logger.error("Error fatal en Agente Cliente: %s", exc, exc_info=True)
        return {
            "customer_analysis": [],
            "errors": [f"Agente Cliente falló: {exc}"],
        }
