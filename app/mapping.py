"""
Adaptador: convierte el formulario agregado de 16 campos (input screen)
en el esquema HelixState que espera src/graph/graph.py.

El formulario del mockup es deliberadamente agregado (un valor por
métrica), no una lista de campañas/productos individuales como
examples/sample_input.json. Por eso se construye UNA campaña y UN
producto sintéticos, resueltos hacia atrás desde los valores agregados,
de forma que los cálculos reales de cada agente (ROAS, CPA, CTR,
abandono, etc.) reproduzcan exactamente lo que el comerciante ingresó.

`extra` trae valores que no forman parte de HelixState pero que el
motor de insights (app/insights.py) necesita para armar las tarjetas
(ej. cantidad total de SKUs, keywords objetivo, temas a investigar).
"""
import re

_BASELINE_IMPRESSIONS = 100_000
_RECOVERY_RATE_ASSUMPTION = 0.15  # % de carritos abandonados que se logran recuperar


def _num(raw, default: float = 0.0) -> float:
    if raw is None:
        return default
    s = str(raw).strip().lower().replace(",", ".")
    s = re.sub(r"[^0-9.]", "", s)
    if not s:
        return default
    try:
        return float(s)
    except ValueError:
        return default


def _int(raw, default: int = 0) -> int:
    return int(round(_num(raw, default)))


def _split_list(raw: str) -> list[str]:
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


def form_to_helix_state(form: dict, store_name: str, period: str) -> tuple[dict, dict]:
    roas = _num(form.get("roas"), 0.0)
    cpa = _num(form.get("cpa"), 0.0)
    ctr = _num(form.get("ctr"), 0.0)
    budget = _num(form.get("budget"), 0.0)

    skus_total = _int(form.get("skus"), 0)
    units = _int(form.get("units"), 0)
    stock = _int(form.get("stock"), 0)
    top_product = (form.get("top") or "").strip() or "Producto principal"

    abandono = _num(form.get("abandono"), 0.0)
    segmentos = _int(form.get("segmentos"), 0)
    ticket = _num(form.get("ticket"), 0.0)
    recompra = _num(form.get("recompra"), 0.0)

    temas = _split_list(form.get("temas", ""))
    competidores = _split_list(form.get("competidores", ""))
    keywords_target = _int(form.get("keywords"), 0)
    dominio_propio = (form.get("dominio") or "").strip()

    # --- Campaña sintética (back-solve desde ROAS/CPA/CTR/budget) ---
    spend_ars = budget
    revenue_ars = spend_ars * roas
    conversions = int(round(spend_ars / cpa)) if cpa > 0 else 0
    impressions = _BASELINE_IMPRESSIONS
    clicks = int(round(impressions * ctr / 100))
    campaign = {
        "name": f"Campañas activas — {store_name}" if store_name else "Campañas activas",
        "spend_ars": spend_ars,
        "revenue_ars": revenue_ars,
        "clicks": clicks,
        "impressions": impressions,
        "conversions": conversions,
    }

    # --- Producto sintético (agregado de catálogo) ---
    price_ars = ticket if ticket > 0 else (revenue_ars / units if units > 0 else 0.0)
    product = {
        "sku": "AGREGADO-01",
        "name": top_product,
        "units_sold": units,
        "revenue_ars": price_ars * units,
        "stock": stock,
        "price_ars": price_ars,
        "category": "General",
    }

    # --- Cliente: estimar "sesiones" como carritos totales derivados del abandono ---
    orders = units
    abandonment_rate = abandono / 100
    if abandonment_rate < 0.99 and orders > 0:
        total_sessions = int(round(orders / (1 - abandonment_rate)))
    else:
        total_sessions = orders
    segment_labels = [f"Segmento {i}" for i in range(1, min(segmentos, 10) + 1)] or ["Sin segmentar"]
    customer_metrics = {
        "total_sessions": total_sessions,
        "cart_abandonment_rate": abandonment_rate,
        "repeat_purchase_rate": recompra / 100,
        "avg_order_value_ars": ticket,
        "top_segments": segment_labels,
    }

    competitor_domain = competidores[0] if competidores else ""

    helix_state = {
        "store_name": store_name or "Mi comercio",
        "period": period or "Período actual",
        "campaigns": [campaign],
        "products": [product],
        "customer_metrics": customer_metrics,
        "competitor_domain": competitor_domain,
    }

    extra = {
        "skus_total": skus_total,
        "keywords_target": keywords_target,
        "temas": temas,
        "competidores": competidores,
        "dominio_propio": dominio_propio,
        "roas": roas, "cpa": cpa, "ctr": ctr, "budget": budget,
        "units": units, "stock": stock,
        "abandono": abandono, "recompra": recompra, "ticket": ticket, "segmentos": segmentos,
    }
    return helix_state, extra
