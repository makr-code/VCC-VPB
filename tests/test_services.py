import types
import pytest

from services.validation_service import ValidationService
from services import validation_service as validation_module
from services.ollama_service import OllamaService
from services import ollama_service as ollama_module
from services.merge_service import MergeService


def test_validation_service_success(monkeypatch):
    monkeypatch.setattr(validation_module, "validate_vpb_dict", lambda data, **kwargs: True, raising=False)
    monkeypatch.setattr(validation_module, "validate_vpb_json", lambda data: [], raising=False)

    svc = ValidationService()
    ok, err = svc.validate({"elements": [], "connections": []})

    assert ok is True
    assert err is None


def test_validation_service_schema_failure(monkeypatch):
    monkeypatch.setattr(validation_module, "validate_vpb_dict", lambda data, **kwargs: (False, "Schemafehler"), raising=False)
    monkeypatch.setattr(validation_module, "validate_vpb_json", lambda data: [], raising=False)

    svc = ValidationService()
    ok, err = svc.validate({})

    assert ok is False
    assert err == "Schemafehler"


def test_validation_service_prompt_exception(monkeypatch):
    monkeypatch.setattr(validation_module, "validate_vpb_dict", lambda data, **kwargs: True, raising=False)

    def _prompt_raise(data):
        raise RuntimeError("prompt kaputt")

    monkeypatch.setattr(validation_module, "validate_vpb_json", _prompt_raise, raising=False)

    svc = ValidationService()
    ok, err = svc.validate({})

    assert ok is False
    assert "prompt kaputt" in (err or "")


class _DummyStreamClient:
    def __init__(self, endpoint=None, model=None):
        self.endpoint = endpoint
        self.model = model

    def chat_stream(self, messages, options=None):
        for chunk in ["Hallo", " ", "Welt"]:
            yield chunk


class _DummyOptions:
    def __init__(self, temperature=None, num_predict=None):
        self.temperature = temperature
        self.num_predict = num_predict


def test_ollama_service_chat_stream(monkeypatch):
    monkeypatch.setattr(ollama_module, "OllamaClient", _DummyStreamClient, raising=False)
    monkeypatch.setattr(ollama_module, "OllamaOptions", _DummyOptions, raising=False)

    svc = OllamaService()
    payload = {
        "endpoint": "http://example",
        "model": "dummy",
        "temperature": 0.3,
        "num_predict": 42,
        "messages": [{"role": "user", "content": "Hallo"}],
    }

    chunks = list(svc.chat_stream(payload))
    assert chunks == ["Hallo", " ", "Welt"]

    result = svc.chat(payload)
    assert result == "Hallo Welt"


def test_ollama_service_fallback(monkeypatch):
    monkeypatch.setattr(ollama_module, "OllamaClient", None, raising=False)

    svc = OllamaService()
    payload = {"messages": []}

    chunks = list(svc.chat_stream(payload))
    assert chunks == ["[OllamaClient nicht verfügbar]"]

    result = svc.chat(payload)
    assert result == "[OllamaClient nicht verfügbar]"


def test_merge_service_full_returns_diagram():
    base = {
        "metadata": {},
        "elements": [
            {"element_id": "A", "element_type": "TASK", "name": "A", "x": 0, "y": 0},
        ],
        "connections": [],
    }
    incoming = {
        "metadata": {},
        "elements": [
            {"element_id": "A", "element_type": "TASK", "name": "A2", "x": 10, "y": 10},
            {"element_id": "B", "element_type": "TASK", "name": "B", "x": 40, "y": 20},
        ],
        "connections": [
            {"connection_id": "C1", "source_element": "A", "target_element": "B", "connection_type": "SEQUENCE"},
        ],
    }

    svc = MergeService()
    result = svc.merge_full({
        "base": base,
        "data": incoming,
        "auto_rename": True,
        "conflict_strategy": "duplicate",
    })

    assert result["added_elements"] >= 1
    assert result["added_connections"] == 1
    assert result["summary_lines"]
    diagram = result["diagram"]
    assert any(el["element_id"].startswith("B") for el in diagram["elements"])


def test_merge_service_patch_add_only():
    base = {
        "metadata": {},
        "elements": [
            {"element_id": "A", "element_type": "TASK", "name": "A", "x": 0, "y": 0},
        ],
        "connections": [],
    }
    patch = {
        "elements": [
            {"element_id": "P1", "element_type": "TASK", "name": "Patch", "x": 50, "y": 50},
        ],
        "connections": [],
    }

    svc = MergeService()
    result = svc.patch_add_only({"base": base, "patch": patch, "auto_rename": True})

    assert result["added_elements"] == 1
    diagram = result["diagram"]
    assert any(el["element_id"].startswith("P1") for el in diagram["elements"])
