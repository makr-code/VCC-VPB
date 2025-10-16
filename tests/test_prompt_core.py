import json
import os
import tempfile

from vpb_ai_logic import (
    build_prompt_with_examples_text_to_vpb,
    build_prompt_with_examples_next_steps,
    build_prompt_with_examples_diagnose_fix,
    validate_model_output,
)
from vpb_prompt_core import set_before_send_hook, set_after_response_hook
from ollama_client import OllamaClient, dirtyjson

# Simple hook capture
_SENT = []
_RESP = []

def _before(meta, prompt):
    _SENT.append((meta, prompt))

def _after(meta, raw, validation):
    _RESP.append((meta, raw, validation))

set_before_send_hook(_before)
set_after_response_hook(_after)

def test_text_to_vpb_prompt_meta():
    prompt, meta = build_prompt_with_examples_text_to_vpb(
        description="Ein einfacher Antrag mit Prüfung und Bescheid.",
        element_types=["START_EVENT", "FUNCTION", "GATEWAY", "END_EVENT"],
        connection_types=["SEQUENCE"],
        example_tags=["antrag"],
        return_meta=True,
    )
    assert "Beispiele (nur lesen" in prompt
    assert meta.mode == "text_to_vpb"
    assert meta.version.startswith("v")


def test_validate_text_to_vpb_success():
    # Minimal valides JSON für text_to_vpb
    output = json.dumps({
        "metadata": {"name": "X", "description": ""},
        "elements": [
            {"element_id": "S1", "element_type": "START_EVENT", "name": "Start", "x": 0, "y": 0, "description": "", "responsible_authority": "", "legal_basis": "", "deadline_days": 0, "geo_reference": ""},
            {"element_id": "E1", "element_type": "END_EVENT", "name": "Ende", "x": 50, "y": 0, "description": "", "responsible_authority": "", "legal_basis": "", "deadline_days": 0, "geo_reference": ""}
        ],
        "connections": [
            {"connection_id": "C1", "source_element": "S1", "target_element": "E1", "connection_type": "SEQUENCE", "description": ""}
        ]
    })
    report = validate_model_output(output, mode="text_to_vpb", allow_element_types=["START_EVENT","END_EVENT"], allow_connection_types=["SEQUENCE"])
    assert report["fatal"] is False
    assert not any(issue for issue in report["issues"] if issue["severity"] == "error")


def test_validate_next_steps_conflict():
    # existing ID Konflikt
    output = json.dumps({
        "elements": [
            {"element_id": "S1", "element_type": "START_EVENT", "name": "Neu", "x": 0, "y": 0}
        ],
        "connections": []
    })
    report = validate_model_output(output, mode="next_steps", existing_ids=["S1"], allow_element_types=["START_EVENT"], allow_connection_types=["SEQUENCE"])
    assert report["fatal"] is True or any(i for i in report["issues"] if i["code"] == "add_only.element_id_conflict")


def test_validate_diagnose_leak_detection():
    leak_output = "Beispiele (nur lesen, NICHT kopieren oder ausgeben):\n{ }"
    report = validate_model_output(leak_output, mode="diagnose_fix")
    assert any(i for i in report["issues"] if i["code"] == "json.parse_error" or i["code"] == "leak.examples_echo")


def test_validate_next_steps_lenient_missing_connections():
    output = json.dumps({
        "elements": [
            {"element_id": "N1", "element_type": "FUNCTION", "name": "Neu", "x": 0, "y": 0}
        ]
    })
    report = validate_model_output(
        output,
        mode="next_steps",
        allow_element_types=["FUNCTION"],
        allow_connection_types=["SEQUENCE"],
        tolerance="lenient",
    )
    assert report["fatal"] is False
    assert report.get("repairs")
    assert isinstance(report["parsed"], dict)
    assert report["parsed"].get("connections") == []


def test_validate_text_to_vpb_lenient_defaults():
    output = json.dumps({
        "metadata": {"name": "", "description": None},
        "elements": [
            {
                "element_id": "S1",
                "element_type": "START_EVENT",
                "name": "Start",
                "x": "0",
                "y": "50",
                "description": None,
                "responsible_authority": None,
                "legal_basis": None,
                "deadline_days": "5",
                "geo_reference": None,
            }
        ],
        "connections": [],
    })
    report = validate_model_output(
        output,
        mode="text_to_vpb",
        allow_element_types=["START_EVENT"],
        allow_connection_types=["SEQUENCE"],
        tolerance="lenient",
    )
    assert report["fatal"] is False
    elem = report["parsed"]["elements"][0]
    assert elem["description"] == ""
    assert elem["responsible_authority"] == "unbekannt"
    assert elem["deadline_days"] == 5
    assert any("elements" in rep for rep in report.get("repairs", []))


def test_extract_json_trailing_comma():
    raw = "Antwort```json {\n  \"foo\": 1,\n}\n```"
    parsed = OllamaClient.extract_json(raw)
    assert parsed == {"foo": 1}


def test_extract_json_dirtyjson_single_quotes():
    if dirtyjson is None:
        import pytest
        pytest.skip("dirtyjson nicht verfügbar")
    raw = "Hier das Ergebnis: { 'foo': 'bar', }"
    parsed = OllamaClient.extract_json(raw)
    assert parsed == {"foo": "bar"}

