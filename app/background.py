"""
Ejecuta el grafo LangGraph real en un hilo de fondo y expone progreso
incremental para que la pantalla de "loading" pueda pintar cada agente
en tiempo real (en vez de una animación de timer falsa), y para que
"Cancelar análisis" pueda volver a la pantalla de input sin esperar a
que termine la corrida (el resultado del hilo huérfano se descarta por
run_id cuando llega).

IMPORTANTE: el hilo de fondo nunca debe llamar funciones `st.*` —
Streamlit las liga al hilo del script. Solo muta el `Job` bajo lock;
el hilo principal (el script de Streamlit) es el único que lee/pinta.
"""
import logging
import threading

logger = logging.getLogger("helix.ui.background")

_LIST_REDUCER_KEYS = {"ads_analysis", "product_analysis", "customer_analysis", "seo_analysis", "errors"}

NODE_TO_AGENT_INDEX = {
    "ads_agent": 0,
    "product_agent": 1,
    "customer_agent": 2,
    "seo_agent": 3,
}


class Job:
    def __init__(self, run_id: int, input_state: dict):
        self.run_id = run_id
        self.input_state = input_state
        self.lock = threading.Lock()
        self.agent_done = [False, False, False, False]
        self.supervisor_done = False
        self.accumulated = dict(input_state)
        self.error: str | None = None
        self.finished = False
        self.cancelled = False
        self.thread: threading.Thread | None = None

    def snapshot(self) -> dict:
        with self.lock:
            return {
                "agent_done": list(self.agent_done),
                "supervisor_done": self.supervisor_done,
                "error": self.error,
                "finished": self.finished,
                "result": dict(self.accumulated) if self.finished and not self.error else None,
            }

    def cancel(self) -> None:
        with self.lock:
            self.cancelled = True

    def _run(self) -> None:
        try:
            from src.graph.graph import build_graph

            graph = build_graph()
            for update in graph.stream(self.input_state, stream_mode="updates"):
                with self.lock:
                    if self.cancelled:
                        return
                for node_name, output in update.items():
                    if not output:
                        continue
                    with self.lock:
                        for key, value in output.items():
                            if key in _LIST_REDUCER_KEYS:
                                self.accumulated[key] = self.accumulated.get(key, []) + list(value)
                            else:
                                self.accumulated[key] = value
                        if node_name in NODE_TO_AGENT_INDEX:
                            self.agent_done[NODE_TO_AGENT_INDEX[node_name]] = True
                        elif node_name == "supervisor":
                            self.supervisor_done = True
            with self.lock:
                self.finished = True
        except Exception as exc:  # noqa: BLE001 — propagamos cualquier falla a la UI
            logger.error("Job de análisis falló: %s", exc, exc_info=True)
            with self.lock:
                self.error = str(exc)
                self.finished = True

    def start(self) -> None:
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()


def start_job(run_id: int, input_state: dict) -> Job:
    job = Job(run_id, input_state)
    job.start()
    return job


def progress_percent(snapshot: dict) -> int:
    done = sum(1 for d in snapshot["agent_done"] if d) + (1 if snapshot["supervisor_done"] else 0)
    return round(done / 5 * 100)
