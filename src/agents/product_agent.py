import logging

from langchain_core.messages import HumanMessage, SystemMessage

from src.graph.state import HelixState, ProductData
from src.llm.providers import build_llm
from src.utils.parsers import safe_parse_analysis

logger = logging.getLogger("helix.agents.product")

SYSTEM_PROMPT = """Sos un especialista en gestión de catálogo y pricing para e-commerce.
Identificás productos con bajo rendimiento y proponés acciones de pricing o promociones.
Respondés SIEMPRE en español, en formato Markdown.
Sos específico: cada recomendación incluye el SKU, la acción y el impacto esperado."""

_LOW_SALES_THRESHOLD = 5
_HIGH_STOCK_THRESHOLD = 50


def _classify_products(products: list[ProductData]) -> dict:
    low_sales = [p for p in products if p["units_sold"] <= _LOW_SALES_THRESHOLD]
    overstock = [p for p in products if p["stock"] >= _HIGH_STOCK_THRESHOLD and p["units_sold"] <= _LOW_SALES_THRESHOLD]
    top_sellers = sorted(products, key=lambda x: x["revenue_ars"], reverse=True)[:3]
    return {"low_sales": low_sales, "overstock": overstock, "top_sellers": top_sellers}


def _format_product_list(products: list[ProductData]) -> str:
    if not products:
        return "_Ninguno_"
    lines = ["| SKU | Nombre | Vendidos | Stock | Precio ARS | Categoría |", "|---|---|---|---|---|---|"]
    for p in products:
        lines.append(
            f"| {p['sku']} | {p['name']} | {p['units_sold']} | {p['stock']} "
            f"| {p['price_ars']:,.0f} | {p['category']} |"
        )
    return "\n".join(lines)


def product_node(state: HelixState) -> dict:
    logger.info("Agente Producto iniciado para tienda: %s", state["store_name"])

    if not state.get("products"):
        logger.warning("No hay productos para analizar.")
        return {"product_analysis": [], "errors": ["Agente Producto: sin datos de productos."]}

    try:
        classified = _classify_products(state["products"])

        llm = build_llm()
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=f"""Analizá el catálogo de **{state['store_name']}** para el período **{state.get('period', 'no especificado')}**.

## Productos con ventas bajas (≤ {_LOW_SALES_THRESHOLD} unidades)

{_format_product_list(classified['low_sales'])}

## Productos con sobrestock Y ventas bajas (stock ≥ {_HIGH_STOCK_THRESHOLD})

{_format_product_list(classified['overstock'])}

## Top 3 productos por revenue

{_format_product_list(classified['top_sellers'])}

Generá un análisis con:
1. **Diagnóstico del catálogo** (1 párrafo)
2. **Productos a promover urgente** — con descuento sugerido o bundle
3. **Productos a revisar precio** — con razonamiento
4. **Aprendizajes de los top sellers** — qué replicar
5. **Próximos 3 pasos prioritarios**
"""
            ),
        ]

        response = llm.invoke(messages)
        analysis = safe_parse_analysis(response.content, "producto")
        logger.info("Agente Producto completado (%d chars).", len(analysis))
        return {"product_analysis": [analysis]}

    except Exception as exc:
        logger.error("Error fatal en Agente Producto: %s", exc, exc_info=True)
        return {
            "product_analysis": [],
            "errors": [f"Agente Producto falló: {exc}"],
        }
