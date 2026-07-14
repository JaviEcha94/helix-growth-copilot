"""
Generación eager del PDF: se llama apenas el reporte queda listo (job
recién terminado o entrada de historial cargada), no cuando el usuario
clickea "Descargar PDF". Así el botón siempre es un st.download_button
real desde el primer click — evita el patrón de "generar" y luego
"descargar" en dos clicks separados, que se sentía como que no pasaba
nada al primer click.

Los agentes (src/agents/*.py) tienen hardcodeado responder siempre en
español, así que el reporte real (y por lo tanto el PDF) sale en
español sin importar el idioma de la UI. Cuando el idioma activo no es
ES, se traduce el markdown con un llamado extra al LLM antes de armar
el PDF — se cachea por idioma para no repetir la traducción.
"""
import logging

logger = logging.getLogger("helix.ui.pdf")

_LANG_NAME = {"EN": "English", "PT": "português do Brasil"}

_TRANSLATE_SYSTEM_PROMPT = """Sos un traductor técnico especializado en reportes de negocio.
Traducís el documento Markdown que te pasan al idioma pedido, preservando EXACTAMENTE
la estructura: mismos encabezados (#, ##, ###), mismas tablas, listas, negritas y saltos
de línea. Traducís únicamente el texto en lenguaje natural (incluidos los nombres de
columnas de tablas y encabezados de sección). No agregues comentarios ni texto fuera
del documento traducido."""


def _translate_markdown(markdown_text: str, target_lang: str) -> str:
    from langchain_core.messages import HumanMessage, SystemMessage

    from src.llm.providers import build_llm

    lang_name = _LANG_NAME.get(target_lang, target_lang)
    llm = build_llm()
    messages = [
        SystemMessage(content=_TRANSLATE_SYSTEM_PROMPT),
        HumanMessage(content=f"Traducí este documento a {lang_name}:\n\n{markdown_text}"),
    ]
    response = llm.invoke(messages)
    return response.content


def generate_pdf_bytes(report_data: dict, lang: str = "ES") -> tuple[bytes, str] | None:
    from src.utils.pdf_exporter import export_to_pdf

    try:
        markdown_text = report_data["final_report_md"]
        if lang != "ES":
            markdown_text = _translate_markdown(markdown_text, lang)

        path = export_to_pdf(
            markdown_text,
            store_name=report_data["store_name"],
            period=report_data["period"],
        )
        with open(path, "rb") as f:
            data = f.read()
        name = path.replace("\\", "/").split("/")[-1]
        return data, name
    except Exception as exc:  # noqa: BLE001 — se degrada al botón de reintento manual
        logger.error("No se pudo generar el PDF automáticamente: %s", exc, exc_info=True)
        return None
