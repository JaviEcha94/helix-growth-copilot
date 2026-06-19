"""
PDF exporter para reportes Helix Growth Copilot.
Convierte el reporte Markdown a un PDF branded con colores por prioridad.
"""
import logging
import re
from datetime import datetime
from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger("helix.utils.pdf")

# ── Dimensiones de página ────────────────────────────────────────────────────
_W, _H = A4
_LM = _RM = 1.75 * cm
_TM = 2.8 * cm
_BM = 1.8 * cm
_CW = _W - _LM - _RM  # ancho de contenido ≈ 17.5 cm

# ── Paleta de marca ──────────────────────────────────────────────────────────
C_PRIMARY     = HexColor("#6366f1")
C_DARK        = HexColor("#1e1b4b")
C_LIGHT_INDIGO = HexColor("#a5b4fc")
C_SURFACE     = HexColor("#f8f9ff")
C_BORDER      = HexColor("#e0e7ff")
C_BODY        = HexColor("#1f2937")
C_MUTED       = HexColor("#6b7280")

# ── Prioridad ────────────────────────────────────────────────────────────────
C_URGENT    = HexColor("#dc2626")   # rojo
C_ATTENTION = HexColor("#d97706")   # amarillo
C_OK        = HexColor("#16a34a")   # verde

# ── Color por agente (borde izquierdo H3) ────────────────────────────────────
_AGENT_COLOR = {
    "ads":      HexColor("#f59e0b"),
    "producto": HexColor("#3b82f6"),
    "cliente":  HexColor("#8b5cf6"),
    "seo":      HexColor("#10b981"),
}

_URGENT_KW    = {"crítico", "urgente", "pausar", "riesgo", "alerta", "pérdida", "caída"}
_ATTENTION_KW = {"optimizar", "atención", "revisar", "mejorar", "deficiente", "bajo"}
_OK_KW        = {"escalar", "excelente", "positivo", "mantener", "oportunidad", "crecimiento"}

_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FFFF\U00002600-\U000027BF\U0000FE00-\U0000FE0F]+",
    flags=re.UNICODE,
)


# ── Helpers de texto ─────────────────────────────────────────────────────────

def _strip_emoji(text: str) -> str:
    return _EMOJI_RE.sub("", text).strip()


def _md_to_rl(text: str) -> str:
    """Markdown inline → pseudo-XML que entiende Paragraph de ReportLab."""
    text = _strip_emoji(text)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*([^*]+?)\*", r"<i>\1</i>", text)
    return text


def _priority_color(text: str):
    lower = text.lower()
    if any(k in lower for k in _URGENT_KW):
        return C_URGENT
    if any(k in lower for k in _ATTENTION_KW):
        return C_ATTENTION
    if any(k in lower for k in _OK_KW):
        return C_OK
    return None


def _agent_color(heading: str) -> HexColor:
    lower = heading.lower()
    if "campa" in lower:
        return _AGENT_COLOR["ads"]
    if "cat" in lower or "producto" in lower:
        return _AGENT_COLOR["producto"]
    if "retenci" in lower or "cliente" in lower:
        return _AGENT_COLOR["cliente"]
    if "seo" in lower or "org" in lower or "visib" in lower:
        return _AGENT_COLOR["seo"]
    return C_PRIMARY


# ── Estilos ──────────────────────────────────────────────────────────────────

def _build_styles() -> dict:
    return {
        "title": ParagraphStyle(
            "hl_title", fontName="Helvetica-Bold", fontSize=20,
            textColor=C_DARK, spaceAfter=2, leading=24,
        ),
        "subtitle": ParagraphStyle(
            "hl_subtitle", fontName="Helvetica", fontSize=9,
            textColor=C_MUTED, spaceAfter=10, leading=12,
        ),
        "h2": ParagraphStyle(
            "hl_h2", fontName="Helvetica-Bold", fontSize=12,
            textColor=white, leading=15,
        ),
        "h3": ParagraphStyle(
            "hl_h3", fontName="Helvetica-Bold", fontSize=10,
            textColor=C_DARK, leading=13,
        ),
        "body": ParagraphStyle(
            "hl_body", fontName="Helvetica", fontSize=9,
            textColor=C_BODY, spaceAfter=4, leading=13,
        ),
        "bullet": ParagraphStyle(
            "hl_bullet", fontName="Helvetica", fontSize=9,
            textColor=C_BODY, spaceAfter=3, leading=13, leftIndent=10,
        ),
        "bullet_urgent": ParagraphStyle(
            "hl_bullet_urgent", fontName="Helvetica", fontSize=9,
            textColor=C_URGENT, spaceAfter=3, leading=13, leftIndent=10,
        ),
        "bullet_attention": ParagraphStyle(
            "hl_bullet_attention", fontName="Helvetica", fontSize=9,
            textColor=C_ATTENTION, spaceAfter=3, leading=13, leftIndent=10,
        ),
        "bullet_ok": ParagraphStyle(
            "hl_bullet_ok", fontName="Helvetica", fontSize=9,
            textColor=C_OK, spaceAfter=3, leading=13, leftIndent=10,
        ),
        "note": ParagraphStyle(
            "hl_note", fontName="Helvetica-Oblique", fontSize=8,
            textColor=C_MUTED, spaceAfter=4, leading=11, leftIndent=16,
        ),
        "th": ParagraphStyle(
            "hl_th", fontName="Helvetica-Bold", fontSize=8, textColor=white,
        ),
        "td": ParagraphStyle(
            "hl_td", fontName="Helvetica", fontSize=8,
            textColor=C_BODY, leading=11,
        ),
    }


# ── Header y footer de página ────────────────────────────────────────────────

def _draw_page(c, doc, store_name: str, period: str, generated_at: str) -> None:
    c.saveState()

    # Header — barra oscura
    c.setFillColor(C_DARK)
    c.rect(0, _H - 2.2 * cm, _W, 2.2 * cm, fill=1, stroke=0)

    # Stripe de acento indigo
    c.setFillColor(C_PRIMARY)
    c.rect(0, _H - 2.2 * cm, 0.35 * cm, 2.2 * cm, fill=1, stroke=0)

    # HELIX
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(0.9 * cm, _H - 1.3 * cm, "HELIX")

    c.setFillColor(C_LIGHT_INDIGO)
    c.setFont("Helvetica", 7)
    c.drawString(0.9 * cm, _H - 1.85 * cm, "Growth Copilot")

    # Nombre de tienda + periodo (alineados a la derecha)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(_W - 0.9 * cm, _H - 1.3 * cm, store_name)

    c.setFillColor(C_LIGHT_INDIGO)
    c.setFont("Helvetica", 7)
    c.drawRightString(_W - 0.9 * cm, _H - 1.85 * cm, period)

    # Footer — barra gris clara
    c.setFillColor(HexColor("#f1f5f9"))
    c.rect(0, 0, _W, 1.2 * cm, fill=1, stroke=0)

    c.setStrokeColor(C_BORDER)
    c.setLineWidth(0.5)
    c.line(_LM, 1.2 * cm, _W - _RM, 1.2 * cm)

    c.setFillColor(C_MUTED)
    c.setFont("Helvetica", 7)
    c.drawString(_LM, 0.45 * cm, f"Generado: {generated_at}")
    c.drawCentredString(_W / 2, 0.45 * cm, f"Página {doc.page}")
    c.drawRightString(_W - _RM, 0.45 * cm, store_name)

    c.restoreState()


# ── Bloques de estructura ────────────────────────────────────────────────────

def _h2_block(title: str, styles: dict) -> Table:
    """Barra de sección H2 con fondo indigo."""
    t = Table([[Paragraph(title, styles["h2"])]], colWidths=[_CW])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_PRIMARY),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    return t


def _h3_block(title: str, color: HexColor, styles: dict) -> Table:
    """H3 con stripe de color del agente a la izquierda."""
    t = Table([["", Paragraph(title, styles["h3"])]], colWidths=[0.3 * cm, _CW - 0.3 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), color),
        ("BACKGROUND", (1, 0), (1, -1), C_SURFACE),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (1, 0), (1, -1), 8),
        ("RIGHTPADDING", (1, 0), (1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _md_table(rows_lines: list[str], styles: dict) -> list:
    """Convierte líneas de tabla Markdown a un Table de ReportLab."""
    rows = []
    for line in rows_lines:
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows.append(cells)

    if not rows:
        return []

    n_cols = max(len(r) for r in rows)
    rows = [r + [""] * (n_cols - len(r)) for r in rows]

    para_rows = []
    for idx, row in enumerate(rows):
        style = styles["th"] if idx == 0 else styles["td"]
        para_rows.append([Paragraph(_md_to_rl(cell), style) for cell in row])

    col_w = _CW / n_cols
    t = Table(para_rows, colWidths=[col_w] * n_cols)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_PRIMARY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [C_SURFACE, white]),
        ("GRID", (0, 0), (-1, -1), 0.3, C_BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return [t, Spacer(1, 6)]


# ── Parser Markdown → flowables ───────────────────────────────────────────────

def _bullet_style(styles: dict, pc) -> ParagraphStyle:
    if pc == C_URGENT:
        return styles["bullet_urgent"]
    if pc == C_ATTENTION:
        return styles["bullet_attention"]
    if pc == C_OK:
        return styles["bullet_ok"]
    return styles["bullet"]


def _build_flowables(md: str, styles: dict) -> list:
    elements = []
    lines = md.split("\n")
    i = 0

    while i < len(lines):
        stripped = lines[i].strip()

        if not stripped:
            elements.append(Spacer(1, 4))
            i += 1
            continue

        # H1 — título principal
        if stripped.startswith("# ") and not stripped.startswith("## "):
            title = stripped[2:].strip()
            if " — " in title:
                title = title.split(" — ", 1)[-1].strip()
            elements.append(Paragraph(_md_to_rl(title), styles["title"]))
            i += 1
            continue

        # H2 — sección
        if stripped.startswith("## ") and not stripped.startswith("### "):
            heading = stripped[3:].strip()
            elements.append(Spacer(1, 10))
            elements.append(_h2_block(heading, styles))
            elements.append(Spacer(1, 6))
            i += 1
            continue

        # H3 — sub-sección de agente
        if stripped.startswith("### "):
            heading = stripped[4:].strip()
            elements.append(Spacer(1, 8))
            elements.append(_h3_block(heading, _agent_color(heading), styles))
            elements.append(Spacer(1, 4))
            i += 1
            continue

        # Separador de tabla → ignorar
        if re.match(r"^\|[\s\-|]+\|$", stripped):
            i += 1
            continue

        # Filas de tabla → recolectar bloque completo
        if stripped.startswith("|") and stripped.endswith("|"):
            table_lines = []
            while i < len(lines):
                s = lines[i].strip()
                if not s.startswith("|"):
                    break
                if not re.match(r"^\|[\s\-|]+\|$", s):
                    table_lines.append(s)
                i += 1
            elements.extend(_md_table(table_lines, styles))
            continue

        # Lista numerada
        m = re.match(r"^(\d+)\.\s+(.+)$", stripped)
        if m:
            content = m.group(2)
            text = f"<b>{m.group(1)}.</b> {_md_to_rl(content)}"
            elements.append(Paragraph(text, _bullet_style(styles, _priority_color(content))))
            i += 1
            continue

        # Lista con viñeta
        if stripped.startswith(("- ", "* ")):
            content = stripped[2:].strip()
            text = "• " + _md_to_rl(content)
            elements.append(Paragraph(text, _bullet_style(styles, _priority_color(content))))
            i += 1
            continue

        # Blockquote
        if stripped.startswith("> "):
            elements.append(Paragraph(_md_to_rl(stripped[2:].strip()), styles["note"]))
            i += 1
            continue

        # Regla horizontal
        if re.match(r"^-{3,}$", stripped):
            elements.append(Spacer(1, 4))
            elements.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER))
            elements.append(Spacer(1, 4))
            i += 1
            continue

        # Línea de meta (Período / Generado)
        if stripped.startswith("**") and ("Período" in stripped or "Generado" in stripped):
            elements.append(Paragraph(_md_to_rl(stripped), styles["subtitle"]))
            i += 1
            continue

        # Párrafo normal
        elements.append(Paragraph(_md_to_rl(stripped), styles["body"]))
        i += 1

    return elements


# ── Función pública ──────────────────────────────────────────────────────────

def export_to_pdf(
    markdown_text: str,
    store_name: str,
    period: str,
    output_path: str | None = None,
) -> str:
    """
    Exporta el reporte Markdown a PDF branded de Helix.
    Retorna la ruta del PDF generado.
    """
    if output_path is None:
        safe = re.sub(r"[^\w\s-]", "", store_name).strip().replace(" ", "_")
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
        output_path = f"outputs/{safe}_{ts}.pdf"

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now().strftime("%d/%m/%Y %H:%M")
    logger.info("Generando PDF: %s", out)

    def _page_cb(c, doc):
        _draw_page(c, doc, store_name, period, generated_at)

    doc = SimpleDocTemplate(
        str(out),
        pagesize=A4,
        leftMargin=_LM,
        rightMargin=_RM,
        topMargin=_TM,
        bottomMargin=_BM,
        title=f"Reporte Helix — {store_name}",
        author="Helix Growth Copilot",
        subject=f"Análisis de crecimiento — {period}",
    )

    styles = _build_styles()
    elements = _build_flowables(markdown_text, styles)
    doc.build(elements, onFirstPage=_page_cb, onLaterPages=_page_cb)

    size_kb = out.stat().st_size // 1024
    logger.info("PDF generado: %s (%d KB)", out, size_kb)
    return str(out)
