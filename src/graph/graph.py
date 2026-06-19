import logging

from langgraph.graph import END, START, StateGraph

from src.agents.ads_agent import ads_node
from src.agents.customer_agent import customer_node
from src.agents.product_agent import product_node
from src.agents.seo_agent import seo_node
from src.agents.supervisor_agent import supervisor_node
from src.graph.state import HelixState

logger = logging.getLogger("helix.graph")


def build_graph():
    """
    Construye el grafo multi-agente de Helix.

    Topología:
        START
          ├─► ads_agent      ─┐
          ├─► product_agent  ─┤
          ├─► customer_agent ─┼─► supervisor ─► END
          └─► seo_agent      ─┘

    Los 4 agentes especializados corren en paralelo (fan-out desde START).
    El supervisor espera a todos antes de sintetizar (fan-in).
    """
    graph = StateGraph(HelixState)

    graph.add_node("ads_agent", ads_node)
    graph.add_node("product_agent", product_node)
    graph.add_node("customer_agent", customer_node)
    graph.add_node("seo_agent", seo_node)
    graph.add_node("supervisor", supervisor_node)

    # Fan-out: START → los 4 agentes en paralelo
    graph.add_edge(START, "ads_agent")
    graph.add_edge(START, "product_agent")
    graph.add_edge(START, "customer_agent")
    graph.add_edge(START, "seo_agent")

    # Fan-in: todos los agentes → supervisor
    graph.add_edge("ads_agent", "supervisor")
    graph.add_edge("product_agent", "supervisor")
    graph.add_edge("customer_agent", "supervisor")
    graph.add_edge("seo_agent", "supervisor")

    graph.add_edge("supervisor", END)

    compiled = graph.compile()
    logger.info("Grafo Helix compilado exitosamente.")
    return compiled
