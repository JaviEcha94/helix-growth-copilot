import io
import logging
import os
import sys


def setup_logging() -> logging.Logger:
    level = os.getenv("LOG_LEVEL", "INFO").upper()

    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        # UTF-8 explícito para que caracteres especiales no revienten en Windows (cp1252).
        # Solo se crea si vamos a instalarlo: un TextIOWrapper descartado cierra el
        # buffer subyacente (sys.stdout.buffer) al ser recolectado por el GC, lo que
        # rompe stdout en procesos de larga vida que llaman setup_logging() más de
        # una vez (ej. Streamlit, que re-ejecuta el script en cada interacción).
        utf8_stream = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        handler = logging.StreamHandler(stream=utf8_stream)
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        root.addHandler(handler)

    return logging.getLogger("helix")
