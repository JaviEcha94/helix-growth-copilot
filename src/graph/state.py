from typing import Annotated
from typing_extensions import TypedDict
import operator


class CampaignData(TypedDict):
    name: str
    spend_ars: float
    revenue_ars: float
    clicks: int
    impressions: int
    conversions: int


class ProductData(TypedDict):
    sku: str
    name: str
    units_sold: int
    revenue_ars: float
    stock: int
    price_ars: float
    category: str


class CustomerData(TypedDict):
    total_sessions: int
    cart_abandonment_rate: float
    repeat_purchase_rate: float
    avg_order_value_ars: float
    top_segments: list[str]


class HelixState(TypedDict):
    # --- Inputs ---
    store_name: str
    period: str
    campaigns: list[CampaignData]
    products: list[ProductData]
    customer_metrics: CustomerData
    competitor_domain: str

    # --- Outputs de agentes especializados ---
    # Operator add permite que múltiples nodos aporten a la misma lista (fan-in)
    ads_analysis: Annotated[list[str], operator.add]
    product_analysis: Annotated[list[str], operator.add]
    customer_analysis: Annotated[list[str], operator.add]
    seo_analysis: Annotated[list[str], operator.add]

    # --- Reporte final ---
    final_report: str

    # --- Metadata de ejecución ---
    errors: Annotated[list[str], operator.add]
