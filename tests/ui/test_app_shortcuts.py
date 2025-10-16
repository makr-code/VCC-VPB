from __future__ import annotations

from typing import Dict, Optional

import pytest

from vpb.ui.app_shortcuts import AppShortcuts


class DummyController:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple]] = []

    def cancel_link_mode(self) -> None:
        self.calls.append(("cancel_link_mode", ()))

    def zoom_at_view(self, factor: float) -> None:
        self.calls.append(("zoom_at_view", (factor,)))

    def zoom_reset(self) -> None:
        self.calls.append(("zoom_reset", ()))

    def set_view_scale(self, value: float) -> None:
        self.calls.append(("set_view_scale", (value,)))


class DummyApp:
    def __init__(self) -> None:
        self.bindings: Dict[str, object] = {}
        self.canvas_controller = DummyController()
        self.text_focus = False
        self.log: list[str] = []

    def bind_all(self, sequence: str, handler) -> None:  # type: ignore[override]
        self.bindings[sequence] = handler

    def _is_text_input_focus(self) -> bool:
        return self.text_focus

    def save_document(self) -> None:
        self.log.append("save_document")

    def save_document_as(self) -> None:
        self.log.append("save_document_as")

    def open_document(self) -> None:
        self.log.append("open_document")

    def new_document(self) -> None:
        self.log.append("new_document")

    def _delete_selected(self) -> None:
        self.log.append("delete_selected")

    def _duplicate_selected(self) -> None:
        self.log.append("duplicate_selected")

    def _toggle_link_mode(self) -> None:
        self.log.append("toggle_link_mode")

    def _select_all(self) -> None:
        self.log.append("select_all")

    def _copy_selection(self) -> None:
        self.log.append("copy_selection")

    def _cut_selection(self) -> None:
        self.log.append("cut_selection")

    def _paste_clipboard(self) -> None:
        self.log.append("paste_clipboard")

    def _zoom_selection(self) -> None:
        self.log.append("zoom_selection")

    def _center_selection(self) -> None:
        self.log.append("center_selection")

    def _group_from_selection(self) -> None:
        self.log.append("group_from_selection")

    def _ungroup_selected(self) -> None:
        self.log.append("ungroup_selected")

    def _reset_view(self) -> None:
        self.log.append("reset_view")

    def _fit_to_diagram(self) -> None:
        self.log.append("fit_to_diagram")

    def _handle_ctrl_enter(self, _event: Optional[object] = None) -> None:
        self.log.append("ctrl_enter")

    def _focus_chat(self) -> None:
        self.log.append("focus_chat")

    def _handle_arrow(self, sx: int, sy: int, big: bool = False) -> None:
        self.log.append(f"arrow:{sx},{sy},{int(big)}")


@pytest.fixture()
def shortcuts_app() -> DummyApp:
    app = DummyApp()
    AppShortcuts(app).register()
    return app


def test_common_shortcuts_trigger_methods(shortcuts_app: DummyApp) -> None:
    handler = shortcuts_app.bindings["<Control-s>"]
    handler()
    assert shortcuts_app.log[-1] == "save_document"

    shortcuts_app.text_focus = True
    delete_handler = shortcuts_app.bindings["<Delete>"]
    delete_handler()
    assert shortcuts_app.log[-1] != "delete_selected"

    shortcuts_app.text_focus = False
    delete_handler()
    assert shortcuts_app.log[-1] == "delete_selected"

    link_handler = shortcuts_app.bindings["l"]
    shortcuts_app.text_focus = False
    result = link_handler()
    assert shortcuts_app.log[-1] == "toggle_link_mode"
    assert result == "break"


def test_controller_shortcuts_delegate(shortcuts_app: DummyApp) -> None:
    zoom_handler = shortcuts_app.bindings["<Control-minus>"]
    zoom_handler()
    assert shortcuts_app.canvas_controller.calls[-1] == ("zoom_at_view", (1 / 1.1,))

    escape_handler = shortcuts_app.bindings["<Escape>"]
    escape_handler()
    assert shortcuts_app.canvas_controller.calls[-1] == ("cancel_link_mode", ())


def test_arrow_shortcuts_use_handle_arrow(shortcuts_app: DummyApp) -> None:
    left_handler = shortcuts_app.bindings["<Left>"]
    left_handler()
    assert shortcuts_app.log[-1] == "arrow:-1,0,0"

    shift_right_handler = shortcuts_app.bindings["<Shift-Right>"]
    shift_right_handler()
    assert shortcuts_app.log[-1] == "arrow:1,0,1"
