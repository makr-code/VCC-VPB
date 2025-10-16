from __future__ import annotations

import pytest

from vpb.xml_export import (
    render_vpb_xml,
    vpb_to_atok_xml,
    vpb_to_bpmn20_xml,
    vpb_to_eepk_xml,
)


SAMPLE_PROCESS = {
    "metadata": {
        "name": "Testprozess",
        "description": "Demo für XML-Export",
        "owner": "Testamt",
    },
    "elements": [
        {"element_id": "E_START", "element_type": "START_EVENT", "name": "Start", "x": 50, "y": 100},
        {"element_id": "F_A", "element_type": "FUNCTION", "name": "Schritt A", "x": 180, "y": 100},
        {
            "element_id": "GW_XOR",
            "element_type": "XOR_CONNECTOR",
            "name": "Entscheidung",
            "x": 320,
            "y": 100,
        },
        {"element_id": "F_B", "element_type": "FUNCTION", "name": "Schritt B", "x": 460, "y": 60},
        {"element_id": "F_C", "element_type": "FUNCTION", "name": "Schritt C", "x": 460, "y": 140},
        {"element_id": "E_END", "element_type": "END_EVENT", "name": "Ende", "x": 600, "y": 100},
    ],
    "connections": [
        {
            "connection_id": "C1",
            "source_element": "E_START",
            "target_element": "F_A",
            "connection_type": "SEQUENCE",
            "description": "Start zu Schritt A",
        },
        {
            "connection_id": "C2",
            "source_element": "F_A",
            "target_element": "GW_XOR",
            "connection_type": "SEQUENCE",
        },
        {
            "connection_id": "C3",
            "source_element": "GW_XOR",
            "target_element": "F_B",
            "connection_type": "SEQUENCE",
        },
        {
            "connection_id": "C4",
            "source_element": "GW_XOR",
            "target_element": "F_C",
            "connection_type": "SEQUENCE",
        },
        {
            "connection_id": "C5",
            "source_element": "F_B",
            "target_element": "E_END",
            "connection_type": "SEQUENCE",
        },
        {
            "connection_id": "C6",
            "source_element": "F_C",
            "target_element": "E_END",
            "connection_type": "SEQUENCE",
        },
    ],
}


def _normalise(text: str) -> str:
    return "".join(line.strip() for line in text.splitlines())


def test_eepk_xml_structure_contains_expected_sections():
    xml = vpb_to_eepk_xml(SAMPLE_PROCESS)
    normalised = _normalise(xml)
    assert "<eepk:Process" in xml
    assert "<eepk:Events>" in xml
    assert "<eepk:Functions>" in xml
    assert "<eepk:Flows>" in xml
    assert 'source="GW_XOR"' in normalised
    assert 'target="F_B"' in normalised


def test_bpmn_xml_contains_namespaces_and_shapes():
    xml = vpb_to_bpmn20_xml(SAMPLE_PROCESS)
    normalised = _normalise(xml)
    assert 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"' in xml
    assert "<bpmn:task" in xml
    assert "<bpmn:exclusiveGateway" in xml
    assert "<bpmndi:BPMNShape" in xml
    assert '<di:waypoint x="50.00" y="100.00"' in normalised


def test_render_vpb_xml_dispatches_formats_consistently():
    atok_xml = render_vpb_xml(SAMPLE_PROCESS, format="atok")
    assert atok_xml == vpb_to_atok_xml(SAMPLE_PROCESS)

    eepk_xml = render_vpb_xml(SAMPLE_PROCESS, format="eepk")
    assert eepk_xml == vpb_to_eepk_xml(SAMPLE_PROCESS)

    bpmn_xml = render_vpb_xml(SAMPLE_PROCESS, format="bpmn")
    assert bpmn_xml == vpb_to_bpmn20_xml(SAMPLE_PROCESS)


def test_render_vpb_xml_rejects_unknown_format():
    with pytest.raises(ValueError):
        render_vpb_xml(SAMPLE_PROCESS, format="unknown-format")
