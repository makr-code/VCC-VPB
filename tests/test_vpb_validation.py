import sys
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vpb_app import VPBDesignerApp
from vpb_diff import validate_add_only_diff, apply_add_only_diff


def _sample_doc():
    return {
        "metadata": {"name": "Demo"},
        "elements": [
            {"element_id": "A", "element_type": "FUNCTION", "name": "A", "x": 0, "y": 0},
            {"element_id": "B", "element_type": "FUNCTION", "name": "B", "x": 100, "y": 0},
        ],
        "connections": [
            {
                "connection_id": "C1",
                "source_element": "A",
                "target_element": "B",
                "connection_type": "SEQUENCE",
            }
        ],
    }


def test_validate_vpb_data_safe_returns_tuple(monkeypatch):
    captured = {}

    def fake_validate(data, allowed_elements=None, allowed_connections=None):
        captured["args"] = (tuple(allowed_elements or ()), tuple(allowed_connections or ()))
        return False, "boom"

    monkeypatch.setattr("vpb_schema.validate_vpb_dict", fake_validate)
    ok, err = VPBDesignerApp._validate_vpb_data_safe(None, _sample_doc())
    assert not ok
    assert err == "boom"
    assert "FUNCTION" in captured["args"][0]


def test_validate_vpb_data_safe_typeerror_retry(monkeypatch):
    calls = {"count": 0}

    def fake_validate(data):
        calls["count"] += 1
        return True

    monkeypatch.setattr("vpb_schema.validate_vpb_dict", fake_validate)
    ok, err = VPBDesignerApp._validate_vpb_data_safe(None, _sample_doc())
    assert ok
    assert err is None
    assert calls["count"] == 1


def test_validate_vpb_data_safe_exception(monkeypatch):
    def fake_validate(*args, **kwargs):
        raise ValueError("kaputt")

    monkeypatch.setattr("vpb_schema.validate_vpb_dict", fake_validate)
    ok, err = VPBDesignerApp._validate_vpb_data_safe(None, _sample_doc())
    assert not ok
    assert "kaputt" in (err or "")


def test_validate_add_only_diff_accepts_valid_payload():
    diff = {
        "elements": [
            {"element_id": "C", "element_type": "FUNCTION", "name": "C"},
        ],
        "connections": [
            {
                "connection_id": "C2",
                "source_element": "B",
                "target_element": "C",
                "connection_type": "SEQUENCE",
            }
        ],
    }
    ok, err = validate_add_only_diff(
        diff,
        existing_element_ids=["A", "B"],
        allowed_element_types=["FUNCTION"],
        allowed_connection_types=["SEQUENCE"],
    )
    assert ok
    assert err is None


def test_validate_add_only_diff_rejects_collisions():
    diff = {
        "elements": [
            {"element_id": "A", "element_type": "FUNCTION", "name": "dupe"},
        ]
    }
    ok, err = validate_add_only_diff(
        diff,
        existing_element_ids=["A"],
        allowed_element_types=["FUNCTION"],
        allowed_connection_types=["SEQUENCE"],
    )
    assert not ok
    assert "kollidiert" in (err or "")


def test_validate_add_only_diff_rejects_unknown_connection():
    diff = {
        "elements": [
            {"element_id": "C", "element_type": "FUNCTION", "name": "C"},
        ],
        "connections": [
            {
                "connection_id": "C2",
                "source_element": "A",
                "target_element": "X",
                "connection_type": "SEQUENCE",
            }
        ],
    }
    ok, err = validate_add_only_diff(
        diff,
        existing_element_ids=["A"],
        allowed_element_types=["FUNCTION"],
        allowed_connection_types=["SEQUENCE"],
    )
    assert not ok
    assert "unbekannte Elemente" in (err or "")


def test_apply_add_only_diff_merges_data():
    doc = _sample_doc()
    diff = {
        "metadata": {"note": "ignored"},
        "elements": [
            {"element_id": "C", "element_type": "FUNCTION", "name": "C", "x": 200, "y": 0},
        ],
        "connections": [
            {
                "connection_id": "C2",
                "source_element": "B",
                "target_element": "C",
                "connection_type": "SEQUENCE",
            }
        ],
    }
    merged = apply_add_only_diff(doc, diff)
    assert len(merged["elements"]) == 3
    assert merged["elements"][-1]["element_id"] == "C"
    assert len(merged["connections"]) == 2
    assert merged["metadata"]["name"] == "Demo"
    assert "note" not in merged["metadata"]
