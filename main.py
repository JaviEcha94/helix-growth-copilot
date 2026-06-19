"""
Helix Growth Copilot — punto de entrada.

Uso:
    python main.py
    python main.py --input examples/sample_input.json
    python main.py --input examples/sample_input.json --output reports/mi_reporte.md
"""
import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from src.utils.logging_config import setup_logging  # noqa: E402

logger = setup_logging()


def validate_input(data: dict) -> list[str]:
    """Valida la estructura del input antes de invocar el grafo. Retorna lista de errores."""
    errors = []
    required_fields = ["store_name", "period", "campaigns", "products", "customer_metrics"]
    for field in required_fields:
        if field not in data:
            errors.append(f"Campo requerido ausente: '{field}'")

    if "campaigns" in data and not isinstance(data["campaigns"], list):
        errors.append("'campaigns' debe ser una lista.")
    if "products" in data and not isinstance(data["products"], list):
        errors.append("'products' debe ser una lista.")
    if "customer_metrics" in data and not isinstance(data["customer_metrics"], dict):
        errors.append("'customer_metrics' debe ser un objeto.")

    return errors


def save_report(report: str, output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")
    logger.info("Reporte guardado en: %s", path)


def main():
    parser = argparse.ArgumentParser(description="Helix Growth Copilot — Multi-agente LangGraph")
    parser.add_argument("--input", default="examples/sample_input.json", help="JSON de input")
    parser.add_argument(
        "--output",
        default=None,
        help="Ruta para guardar el reporte (default: reports/YYYY-MM-DD_HH-MM.md)",
    )
    args = parser.parse_args()

    # Carga de input
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error("Archivo de input no encontrado: %s", input_path)
        sys.exit(1)

    with open(input_path, encoding="utf-8") as f:
        input_data = json.load(f)

    # Validación temprana — falla rápido antes de consumir tokens
    validation_errors = validate_input(input_data)
    if validation_errors:
        for err in validation_errors:
            logger.error("Validación fallida: %s", err)
        sys.exit(1)

    logger.info(
        "Input validado. Tienda: %s | Período: %s",
        input_data["store_name"],
        input_data["period"],
    )

    # Importación diferida para que los errores de .env fallen tarde con mensaje claro
    from src.graph.graph import build_graph

    graph = build_graph()

    logger.info("Invocando grafo multi-agente Helix...")
    result = graph.invoke(input_data)

    # Report del estado final
    errors = result.get("errors", [])
    if errors:
        for err in errors:
            logger.warning("Error no fatal registrado: %s", err)

    final_report = result.get("final_report", "")
    if not final_report:
        logger.error("El grafo no produjo reporte final.")
        sys.exit(1)

    # Guardar reporte Markdown
    output_path = args.output or f"reports/{datetime.now().strftime('%Y-%m-%d_%H-%M')}.md"
    save_report(final_report, output_path)

    # Exportar PDF en outputs/
    from src.utils.pdf_exporter import export_to_pdf

    safe_name = re.sub(r"[^\w\s-]", "", input_data["store_name"]).strip().replace(" ", "_")
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
    pdf_path = f"outputs/{safe_name}_{ts}.pdf"

    try:
        export_to_pdf(
            final_report,
            store_name=input_data["store_name"],
            period=input_data["period"],
            output_path=pdf_path,
        )
    except Exception as exc:
        logger.error("PDF export falló (el Markdown sí fue guardado): %s", exc)
        pdf_path = None

    print("\n" + "=" * 60)
    print(f"  Reporte Markdown: {output_path}")
    if pdf_path:
        print(f"  Reporte PDF:      {pdf_path}")
    if errors:
        print(f"  Advertencias:     {len(errors)} (ver logs)")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
