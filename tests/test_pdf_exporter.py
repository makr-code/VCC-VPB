from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from vpb.pdf_exporter import render_process_pdf


def test_render_process_pdf_creates_pdf(tmp_path: Path) -> None:
    image = Image.new("RGB", (400, 300), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((50, 50, 350, 250), outline="black", width=4)
    draw.line((50, 250, 350, 50), fill="blue", width=3)

    process_data = {
        "metadata": {
            "name": "Testprozess",
            "description": "Eine kurze Beschreibung für den PDF-Export.",
            "version": "1.0",
            "owner": "QA-Team",
        },
        "elements": [
            {
                "element_id": "E1",
                "element_type": "TASK",
                "name": "Aufgabe 1",
                "description": "Erster Schritt",
                "responsible_authority": "Amt A",
                "legal_basis": "§1",
                "deadline_days": 5,
            },
            {
                "element_id": "E2",
                "element_type": "EVENT",
                "name": "Ereignis",
                "description": "Signal",
            },
        ],
        "connections": [
            {
                "connection_id": "C1",
                "source_element": "E1",
                "target_element": "E2",
                "connection_type": "SEQUENCE",
                "description": "Weiterleitung",
            }
        ],
    }

    output_path = tmp_path / "prozess.pdf"
    render_process_pdf(image, process_data, str(output_path))
    image.close()

    assert output_path.exists()
    content = output_path.read_bytes()
    assert content.startswith(b"%PDF"), "PDF-Datei hat keinen gültigen Header"
    assert len(content) > 500, "PDF-Datei ist unerwartet klein"
