import logging
import os

from tavily import TavilyClient

logger = logging.getLogger("helix.tools.search")

_client: TavilyClient | None = None


def get_search_client() -> TavilyClient:
    global _client
    if _client is None:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "TAVILY_API_KEY no configurada. Agregala al .env para que el Agente SEO funcione."
            )
        _client = TavilyClient(api_key=api_key)
        logger.info("Tavily inicializado.")
    return _client


def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Wrapper de Tavily con logging y manejo de error no-fatal."""
    client = get_search_client()
    logger.debug("Búsqueda Tavily: %s", query)
    try:
        response = client.search(query=query, max_results=max_results)
        results = response.get("results", [])
        logger.info("Tavily devolvió %d resultados para: %s", len(results), query)
        return results
    except Exception as exc:
        logger.error("Error en búsqueda Tavily ('%s'): %s", query, exc)
        return []
