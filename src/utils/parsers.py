import logging
import re

logger = logging.getLogger("helix.parsers")


def extract_markdown_section(text: str, heading: str) -> str:
    """Extrae una sección de un bloque Markdown por su heading."""
    pattern = rf"#+\s*{re.escape(heading)}.*?(?=^#+|\Z)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(0).strip()
    return ""


def safe_parse_analysis(raw: str, agent_name: str) -> str:
    """Valida que el output del agente sea usable; retorna fallback si está vacío."""
    if not raw or not raw.strip():
        logger.warning("Agente %s retornó análisis vacío — usando placeholder.", agent_name)
        return f"[{agent_name.upper()}] Análisis no disponible en esta ejecución."
    cleaned = raw.strip()
    if len(cleaned) < 50:
        logger.warning("Agente %s retornó análisis muy corto (%d chars).", agent_name, len(cleaned))
    return cleaned
