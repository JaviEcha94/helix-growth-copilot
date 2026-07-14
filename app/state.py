"""
Estado de sesión + persistencia local (Streamlit no tiene localStorage).
Persiste form/lang/density/history/coachmark en un JSON en disco, tal
como sugiere design/design_handoff_streamlit/README.md.
"""
import json
import logging
from pathlib import Path

import streamlit as st

logger = logging.getLogger("helix.ui.state")

_STATE_DIR = Path(".streamlit_state")
_STATE_FILE = _STATE_DIR / "helix_ui_state.json"

_PERSISTED_KEYS = ["form", "lang", "density", "history", "coachmark_seen"]

_DEFAULTS = {
    "screen": "input",
    "lang": "ES",
    "form": {},
    "touched": {},
    "expanded": {"campanas": True, "productos": False, "clientes": False, "seo": False},
    "density": "comfortable",
    "history": [],
    "coachmark_seen": False,
    "empty_warning": False,
    "store_name": "",
    "period": "",
    "actions_applied": [False, False, False],
    "expanded_results": [False, False, False, False],
    "show_history": False,
    "generated_at": None,
    "generated_at_iso": None,
    "report_data": None,
    "job": None,
    "pdf_cache": {},  # {lang: (bytes, filename)} — el PDF se traduce por idioma bajo demanda
}


def _load_persisted() -> dict:
    if not _STATE_FILE.exists():
        return {}
    try:
        with open(_STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("No se pudo leer estado persistido: %s", exc)
        return {}


def persist() -> None:
    try:
        _STATE_DIR.mkdir(parents=True, exist_ok=True)
        data = {k: st.session_state.get(k) for k in _PERSISTED_KEYS}
        with open(_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as exc:
        logger.warning("No se pudo persistir estado: %s", exc)


def init_session_state() -> None:
    if st.session_state.get("_initialized"):
        return
    persisted = _load_persisted()
    for key, default in _DEFAULTS.items():
        st.session_state.setdefault(key, persisted.get(key, default))
    if "coachmark_seen" not in persisted:
        st.session_state["show_coachmark"] = True
    else:
        st.session_state["show_coachmark"] = not st.session_state["coachmark_seen"]

    # Los widgets de texto usan key=f"field_{k}" como única fuente de verdad
    # (sin pasar también value=, que Streamlit desaconseja combinar con un
    # key ya presente en session_state). Acá se siembran esas keys una vez
    # a partir del form/valores persistidos, antes de que se creen los
    # widgets por primera vez.
    for key, value in st.session_state["form"].items():
        st.session_state.setdefault(f"field_{key}", value)

    st.session_state["_initialized"] = True


def toast(msg: str) -> None:
    st.toast(msg, icon="✅")
