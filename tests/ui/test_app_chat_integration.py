from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Callable, List, Optional

import pytest

from vpb.ui.app_chat_integration import AppChatIntegration


class DummySplit:
    def __init__(self, height: int = 400, pos: int = 200) -> None:
        self._height = height
        self._pos = pos
        self.set_calls: List[int] = []

    def winfo_height(self) -> int:
        return self._height

    def sashpos(self, index: int, value: Optional[int] = None) -> int:
        if value is None:
            return self._pos
        self._pos = value
        self.set_calls.append(value)
        return self._pos


class DummyAfterMixin:
    def __init__(self) -> None:
        self.after_calls: List[tuple[int, Callable[[], None]]] = []

    def after(self, delay: int, callback: Callable[[], None]) -> None:
        self.after_calls.append((delay, callback))


class DummyStatus:
    def __init__(self) -> None:
        self.messages: List[str] = []

    def set(self, message: str) -> None:
        self.messages.append(message)


class DummyChatController:
    def __init__(self) -> None:
        self.sent: List[str] = []

    def handle_send(self, message: str) -> None:
        self.sent.append(message)

    def append_block(self, title: str, payload) -> None:
        pass


class DummyChat:
    def __init__(self) -> None:
        self.focused = False
        self.entry = SimpleNamespace(get=lambda: "hello")
        self.cleared = False
        self.buttons: List[str] = []

    def focus_input(self) -> None:
        self.focused = True

    def clear_dynamic_actions(self) -> None:
        self.cleared = True

    def add_dynamic_button(self, label: str, callback: Callable[[], None]) -> None:
        self.buttons.append(label)

    def append_assistant(self, text: str) -> None:
        pass


class DummyCanvas:
    def __init__(self) -> None:
        self.elements = {}
        self.connections = {}
        self.push_calls = 0
        self.load_payload = None
        self.redraw_calls = 0

    def push_undo(self) -> None:
        self.push_calls += 1

    def load_from_dict(self, payload) -> None:
        self.load_payload = payload

    def redraw_all(self) -> None:
        self.redraw_calls += 1


class DummyActions:
    def __init__(self) -> None:
        self.fit_calls = 0

    def fit_to_diagram(self) -> None:
        self.fit_calls += 1


def make_app(**overrides):
    base = {
        "_mid_split": None,
        "after": lambda delay, cb: None,
        "chat": None,
        "status": None,
        "chat_controller": None,
        "canvas": None,
        "_actions": None,
        "_validate_vpb_data_safe": lambda data: (True, None),
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def test_ensure_chat_visible_adjusts_split() -> None:
    split = DummySplit(height=400, pos=280)
    app = make_app(_mid_split=split, after=lambda delay, cb: None)
    helper = AppChatIntegration(app)
    helper.ensure_chat_visible(min_height=220)
    assert split.sashpos(0) == 180
    assert split.set_calls[-1] == 180


def test_focus_chat_focuses_input_and_status() -> None:
    status = DummyStatus()
    chat = DummyChat()
    app = make_app(chat=chat, status=status)
    helper = AppChatIntegration(app)
    helper.focus_chat()
    assert chat.focused is True
    assert status.messages[-1] == "AI-Konsole aktiv"


def test_handle_ctrl_enter_sends_message_when_focus_in_chat() -> None:
    chat = DummyChat()
    controller = DummyChatController()

    def focus_get():
        return chat.entry

    app = make_app(chat=chat, chat_controller=controller, focus_get=focus_get)
    helper = AppChatIntegration(app)
    helper.handle_ctrl_enter()
    assert controller.sent == ["hello"]


def test_handle_ctrl_enter_falls_back_to_text_to_diagram() -> None:
    app = make_app(chat=DummyChat(), focus_get=lambda: object())
    helper = AppChatIntegration(app)
    calls: List[str] = []
    helper.text_to_diagram = lambda: calls.append("called")  # type: ignore[assignment]
    helper.handle_ctrl_enter()
    assert calls == ["called"]


def test_postprocess_chat_result_creates_buttons(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "metadata": {},
        "elements": [],
        "connections": [],
        "issues": ["warn"],
        "patch": {},
    }
    monkeypatch.setattr(
        "ollama_client.OllamaClient.extract_json",
        staticmethod(lambda buf: json.loads(buf)),
    )
    status = DummyStatus()
    chat = DummyChat()
    app = make_app(
        _chat_assistant_buffer=json.dumps(payload),
        chat=chat,
        status=status,
    )
    helper = AppChatIntegration(app)
    helper.postprocess_chat_result()
    assert chat.cleared is True
    expected = {"Diagramm ersetzen", "Diagramm mergen", "Diagnose-Patch anwenden"}
    assert expected <= set(chat.buttons)
    assert status.messages[-1] == "Diagnose: 1 Issues gefunden"


def test_apply_full_process_json_updates_canvas() -> None:
    canvas = DummyCanvas()
    actions = DummyActions()
    status = DummyStatus()
    sample = {"elements": [], "connections": []}
    app = make_app(canvas=canvas, status=status, _actions=actions)
    helper = AppChatIntegration(app)
    helper.apply_full_process_json(sample)
    assert canvas.push_calls == 1
    assert canvas.load_payload == sample
    assert canvas.redraw_calls == 1
    assert actions.fit_calls == 1
    assert status.messages[-1] == "LLM Diagramm übernommen"
