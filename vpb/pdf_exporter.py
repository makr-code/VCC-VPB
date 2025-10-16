from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from PIL import Image
from reportlab.lib.pagesizes import A4, A3, A5, LETTER, LEGAL, landscape, portrait
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas as pdf_canvas

from vpb_config import EXPORT_CONFIG, ExportConfig


_PAGE_SIZE_MAP = {
    "A5": A5,
    "A4": A4,
    "A3": A3,
    "LETTER": LETTER,
    "LEGAL": LEGAL,
}


@dataclass
class DiagramSummary:
    metadata: Dict[str, Any]
    elements: Sequence[Dict[str, Any]]
    connections: Sequence[Dict[str, Any]]

    @classmethod
    def from_process_dict(cls, data: Dict[str, Any]) -> "DiagramSummary":
        metadata = data.get("metadata") or {}
        elements = data.get("elements") or []
        connections = data.get("connections") or []
        return cls(metadata=dict(metadata), elements=list(elements), connections=list(connections))


def _resolve_page_size(config: Optional[ExportConfig]) -> Tuple[float, float]:
    if config is None:
        config = EXPORT_CONFIG
    name = (getattr(config, "pdf_page_size", "A4") or "A4").strip().upper()
    base = _PAGE_SIZE_MAP.get(name, A4)
    orientation = (getattr(config, "pdf_orientation", "landscape") or "landscape").strip().lower()
    if orientation in {"landscape", "quer"}:
        return landscape(base)
    if orientation in {"portrait", "hochformat"}:
        return portrait(base)
    return landscape(base)


def _draw_wrapped_text(
    pdf: pdf_canvas.Canvas,
    text: str,
    *,
    x: float,
    y: float,
    max_width: float,
    font_name: str = "Helvetica",
    font_size: float = 11,
    leading: float = 14,
) -> float:
    if not text:
        return y
    words = text.replace("\r", "").split()
    if not words:
        return y
    lines: List[str] = []
    current: List[str] = []
    for word in words:
        candidate = (" ".join(current + [word])).strip()
        width = pdfmetrics.stringWidth(candidate, font_name, font_size)
        if width <= max_width or not current:
            current.append(word)
            continue
        lines.append(" ".join(current))
        current = [word]
    if current:
        lines.append(" ".join(current))

    text_obj = pdf.beginText()
    text_obj.setTextOrigin(x, y)
    text_obj.setFont(font_name, font_size)
    text_obj.setLeading(leading)
    for line in lines:
        text_obj.textLine(line)
    pdf.drawText(text_obj)
    return y - leading * len(lines)


def _summarise_elements(summary: DiagramSummary) -> List[str]:
    lines: List[str] = []
    for idx, element in enumerate(summary.elements, start=1):
        etype = str(element.get("element_type") or "?").upper()
        name = str(element.get("name") or "(ohne Namen)")
        lines.append(f"{idx}. [{etype}] {name}")
        desc = (element.get("description") or "").strip()
        if desc:
            lines.append(f"    Beschreibung: {desc}")
        authority = (element.get("responsible_authority") or "").strip()
        if authority:
            lines.append(f"    Zuständig: {authority}")
        legal_basis = (element.get("legal_basis") or "").strip()
        if legal_basis:
            lines.append(f"    Rechtsgrundlage: {legal_basis}")
        deadline = element.get("deadline_days")
        if deadline not in (None, "", 0):
            lines.append(f"    Frist: {deadline} Tage")
    if not lines:
        lines.append("(Keine Elemente vorhanden)")
    return lines


def _summarise_connections(summary: DiagramSummary) -> List[str]:
    lines: List[str] = []
    for idx, conn in enumerate(summary.connections, start=1):
        source = conn.get("source_element") or "?"
        target = conn.get("target_element") or "?"
        ctype = conn.get("connection_type") or "SEQUENCE"
        lines.append(f"{idx}. {source} → {target} ({ctype})")
        desc = (conn.get("description") or "").strip()
        if desc:
            lines.append(f"    Hinweis: {desc}")
    if not lines:
        lines.append("(Keine Verbindungen vorhanden)")
    return lines


def _draw_list(
    pdf: pdf_canvas.Canvas,
    *,
    lines: Iterable[str],
    x: float,
    y: float,
    max_width: float,
    font_name: str = "Helvetica",
    font_size: float = 10,
    leading: float = 13,
) -> float:
    current_y = y
    for raw_line in lines:
        line = raw_line.rstrip()
        current_y = _draw_wrapped_text(
            pdf,
            line,
            x=x,
            y=current_y,
            max_width=max_width,
            font_name=font_name,
            font_size=font_size,
            leading=leading,
        )
    return current_y


def render_process_pdf(
    image: Image.Image,
    process_data: Dict[str, Any],
    output_path: str,
    *,
    config: Optional[ExportConfig] = None,
) -> None:
    """Render a PDF file containing the diagram image and textual details."""

    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA")

    summary = DiagramSummary.from_process_dict(process_data)
    page_width, page_height = _resolve_page_size(config)
    pdf = pdf_canvas.Canvas(output_path, pagesize=(page_width, page_height))

    margin = 20 * mm
    content_width = page_width - 2 * margin

    top_y = page_height - margin

    title = str(summary.metadata.get("name") or "VPB Prozess")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(margin, top_y, title)
    top_y -= 24

    subtitle_bits: List[str] = []
    version = summary.metadata.get("version")
    if version:
        subtitle_bits.append(f"Version: {version}")
    owner = summary.metadata.get("owner")
    if owner:
        subtitle_bits.append(f"Verantwortlich: {owner}")
    if subtitle_bits:
        pdf.setFont("Helvetica", 11)
        pdf.drawString(margin, top_y, " | ".join(subtitle_bits))
        top_y -= 18

    description = str(summary.metadata.get("description") or "").strip()
    if description:
        pdf.setFont("Helvetica", 11)
        top_y = _draw_wrapped_text(
            pdf,
            description,
            x=margin,
            y=top_y,
            max_width=content_width,
            font_name="Helvetica",
            font_size=11,
            leading=15,
        )
        top_y -= 12

    stats_line = (
        f"Elemente: {len(summary.elements)} | Verbindungen: {len(summary.connections)}"
    )
    pdf.setFont("Helvetica", 10)
    pdf.drawString(margin, top_y, stats_line)
    top_y -= 22

    # Diagram image
    img_width, img_height = image.size
    img_buffer = io.BytesIO()
    # transparent background -> white
    if image.mode == "RGBA":
        background = Image.new("RGBA", image.size, (255, 255, 255, 255))
        background.alpha_composite(image)
        image_to_save = background.convert("RGB")
    else:
        image_to_save = image
    image_to_save.save(img_buffer, format="PNG")
    img_buffer.seek(0)
    img_reader = ImageReader(img_buffer)

    available_height = top_y - margin
    if available_height <= 0:
        pdf.showPage()
        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(margin, page_height - margin, title)
        available_height = page_height - 2 * margin
        top_y = page_height - margin

    scale = min(content_width / img_width, available_height / img_height, 1.0)
    scaled_w = img_width * scale
    scaled_h = img_height * scale
    pdf.drawImage(
        img_reader,
        margin,
        margin + max(0, (available_height - scaled_h) / 2),
        width=scaled_w,
        height=scaled_h,
        preserveAspectRatio=True,
        anchor='sw',
    )

    pdf.showPage()

    # Second page with details
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(margin, page_height - margin, "Prozess-Details")
    current_y = page_height - margin - 28

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(margin, current_y, "Elemente")
    current_y -= 16
    pdf.setFont("Helvetica", 10)
    current_y = _draw_list(
        pdf,
        lines=_summarise_elements(summary),
        x=margin,
        y=current_y,
        max_width=content_width,
        font_size=10,
        leading=14,
    )

    current_y -= 20
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(margin, current_y, "Verbindungen")
    current_y -= 16
    pdf.setFont("Helvetica", 10)
    _draw_list(
        pdf,
        lines=_summarise_connections(summary),
        x=margin,
        y=current_y,
        max_width=content_width,
        font_size=10,
        leading=14,
    )

    pdf.save()
