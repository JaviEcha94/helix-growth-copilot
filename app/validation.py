"""
Definición de las 4 tarjetas de input y sus campos, portada del bloque
CARD_ORDER/FIELD_KEYS/FIELD_TYPES/SAMPLE del HTML de referencia.
"""
import re

CARD_ORDER = ["campanas", "productos", "clientes", "seo"]

CARD_ICONS = {"campanas": "📊", "productos": "📦", "clientes": "👤", "seo": "🔍"}

FIELD_KEYS = {
    "campanas": ["roas", "cpa", "ctr", "budget"],
    "productos": ["skus", "units", "stock", "top"],
    "clientes": ["abandono", "segmentos", "ticket", "recompra"],
    "seo": ["temas", "competidores", "keywords", "dominio"],
}

FIELD_TYPES = {
    "campanas": ["multiplier", "currency", "percent", "currency"],
    "productos": ["integer", "integer", "integer", "text"],
    "clientes": ["percent", "integer", "currency", "percent"],
    "seo": ["text", "text", "integer", "domain"],
}

SAMPLE = {
    "roas": "3.5x", "cpa": "42", "ctr": "1.3", "budget": "12000",
    "skus": "142", "units": "2340", "stock": "870", "top": "Auriculares X",
    "abandono": "68", "segmentos": "4", "ticket": "54", "recompra": "22",
    "temas": "envíos gratis, reseñas", "competidores": "tiendaA, tiendaB",
    "keywords": "30", "dominio": "tiendanova.com",
}

_ERR_KEY = {
    "multiplier": "errMultiplier", "currency": "errCurrency", "percent": "errPercent",
    "integer": "errNumber", "domain": "errDomain", "text": None,
}


def validate_value(field_type: str, raw: str) -> str | None:
    """Retorna la clave de error i18n (o None si es válido/vacío)."""
    v = (raw or "").strip()
    if not v:
        return None
    if field_type == "multiplier":
        return None if re.fullmatch(r"\d+(\.\d+)?x?", v, re.IGNORECASE) else _ERR_KEY["multiplier"]
    if field_type == "currency":
        return None if re.fullmatch(r"\d+(\.\d+)?", v) else _ERR_KEY["currency"]
    if field_type == "percent":
        if not re.fullmatch(r"\d+(\.\d+)?", v):
            return _ERR_KEY["percent"]
        n = float(v)
        return None if 0 <= n <= 100 else _ERR_KEY["percent"]
    if field_type == "integer":
        return None if re.fullmatch(r"\d+", v) else _ERR_KEY["integer"]
    if field_type == "domain":
        return None if re.fullmatch(r"[a-z0-9-]+(\.[a-z0-9-]+)+", v, re.IGNORECASE) else _ERR_KEY["domain"]
    return None
