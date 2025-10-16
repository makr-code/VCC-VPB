from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from vpb.svg_exporter import CANVAS_MARGIN, DEFAULT_NODE_HEIGHT, DEFAULT_NODE_WIDTH, render_process_svg


def test_render_process_svg_contains_elements_and_connections() -> None:
    process_data = {
        "metadata": {"name": "SVG Test"},
        "elements": [
            {"element_id": "E1", "element_type": "TASK", "name": "Aufgabe", "x": 100, "y": 200},
            {"element_id": "E2", "element_type": "EVENT", "name": "Ende", "x": 400, "y": 200},
        ],
        "connections": [
            {"connection_id": "C1", "source_element": "E1", "target_element": "E2", "connection_type": "SEQUENCE"}
        ],
    }

    svg_text = render_process_svg(process_data)

    assert svg_text.startswith("<?xml"), "SVG sollte mit XML-Deklaration beginnen"
    assert "Aufgabe" in svg_text
    assert "Ende" in svg_text
    assert "polyline" in svg_text, "Verbindung sollte als polyline ausgegeben werden"
    assert "viewBox=\"0 0" in svg_text or "viewBox='0 0" in svg_text


def test_render_process_svg_uses_dynamic_bounds() -> None:
    process_data = {
        "metadata": {"name": "Dynamische Bounds", "version": "1.0", "owner": "Team"},
        "elements": [
            {"element_id": "A", "element_type": "TASK", "name": "Start", "x": 0, "y": 0},
            {"element_id": "B", "element_type": "TASK", "name": "Ende", "x": 400, "y": 200},
        ],
        "connections": [
            {"connection_id": "AB", "source_element": "A", "target_element": "B", "connection_type": "SEQUENCE"}
        ],
    }

    svg_text = render_process_svg(process_data)
    root = ET.fromstring(svg_text)

    width = float(root.attrib["width"])
    height = float(root.attrib["height"])

    half_w = DEFAULT_NODE_WIDTH / 2.0
    half_h = DEFAULT_NODE_HEIGHT / 2.0
    min_x = min(0 - half_w, 400 - half_w)
    max_x = max(0 + half_w, 400 + half_w)
    min_y = min(0 - half_h, 200 - half_h)
    max_y = max(0 + half_h, 200 + half_h)
    expected_width = (max_x - min_x) + 2 * CANVAS_MARGIN
    expected_height = (max_y - min_y) + 2 * CANVAS_MARGIN

    assert pytest.approx(expected_width, rel=1e-3) == width
    assert pytest.approx(expected_height, rel=1e-3) == height

    titles = [child.text or "" for child in root if child.tag.endswith("text")]
    assert any("Dynamische Bounds" in text for text in titles)
    assert any("Version" in text and "Verantwortlich" in text for text in titles)
