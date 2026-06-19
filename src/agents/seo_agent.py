import logging

from langchain_core.messages import HumanMessage, SystemMessage

from src.graph.state import HelixState
from src.llm.providers import build_llm
from src.tools.search import web_search
from src.utils.parsers import safe_parse_analysis

logger = logging.getLogger("helix.agents.seo")

SYSTEM_PROMPT = """Sos un especialista en SEO y contenido para e-commerce.
Identificás huecos de keywords frente a la competencia y oportunidades de contenido.
Respondés SIEMPRE en español, en formato Markdown.
Basás tus recomendaciones en datos reales de búsqueda, no en suposiciones."""


def _build_search_queries(store_name: str, competitor: str, products: list) -> list[str]:
    queries = [
        f"{competitor} estrategia SEO e-commerce Argentina",
        f"keywords {competitor} productos destacados",
    ]
    if products:
        top_categories = list({p["category"] for p in products[:5]})
        for cat in top_categories[:2]:
            queries.append(f"mejores tiendas online {cat} Argentina SEO")
    return queries


def seo_node(state: HelixState) -> dict:
    logger.info("Agente SEO iniciado para tienda: %s", state["store_name"])

    competitor = state.get("competitor_domain", "")
    if not competitor:
        logger.warning("No se especificó dominio competidor — análisis SEO parcial.")

    try:
        queries = _build_search_queries(
            state["store_name"], competitor, state.get("products", [])
        )

        search_results = []
        for q in queries:
            results = web_search(q, max_results=3)
            search_results.extend(results)

        snippets = []
        seen_urls = set()
        for r in search_results:
            url = r.get("url", "")
            if url not in seen_urls:
                seen_urls.add(url)
                snippets.append(f"- **{r.get('title', '')}** ({url})\n  {r.get('content', '')[:200]}")

        search_context = "\n".join(snippets[:8]) if snippets else "_Sin resultados de búsqueda disponibles._"

        product_categories = list({p["category"] for p in state.get("products", [])})

        llm = build_llm()
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(
                content=f"""Analizá la posición SEO de **{state['store_name']}** frente a **{competitor or 'competidores del sector'}**
para el período **{state.get('period', 'no especificado')}**.

## Categorías de productos

{', '.join(product_categories) if product_categories else 'No especificadas'}

## Resultados de investigación web

{search_context}

Generá un análisis con:
1. **Diagnóstico de visibilidad orgánica** (1 párrafo basado en los datos)
2. **Keywords con oportunidad** — al menos 5, con volumen estimado e intención
3. **Huecos de contenido vs competencia** — qué tienen ellos que nosotros no
4. **Plan de contenido** — 3 artículos/páginas priorizados con título y objetivo
5. **Próximos 3 pasos prioritarios**
"""
            ),
        ]

        response = llm.invoke(messages)
        analysis = safe_parse_analysis(response.content, "seo")
        logger.info("Agente SEO completado (%d chars).", len(analysis))
        return {"seo_analysis": [analysis]}

    except Exception as exc:
        logger.error("Error fatal en Agente SEO: %s", exc, exc_info=True)
        return {
            "seo_analysis": [],
            "errors": [f"Agente SEO falló: {exc}"],
        }
