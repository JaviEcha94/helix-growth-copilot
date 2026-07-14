"""
Generación eager del PDF: se llama apenas el reporte queda listo (job
recién terminado o entrada de historial cargada), no cuando el usuario
clickea "Descargar PDF". Así el botón siempre es un st.download_button
real desde el primer click — evita el patrón de "generar" y luego
"descargar" en dos clicks separados, que se sentía como que no pasaba
nada al primer click.
"""
import logging

logger = logging.getLogger("helix.ui.pdf")


def generate_pdf_bytes(report_data: dict) -> tuple[bytes, str] | None:
    from src.utils.pdf_exporter import export_to_pdf

    try:
        path = export_to_pdf(
            report_data["final_report_md"],
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
