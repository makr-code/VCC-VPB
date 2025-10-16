from __future__ import annotations

from typing import List

import pytest

from vpb.ui.app_actions import AppActions


class DummyGridVar:
    def __init__(self, value: bool) -> None:
        self._value = value

    def get(self) -> bool:
        return self._value

    def set(self, value: bool) -> None:
        self._value = value


class DummyStatus:
    def __init__(self) -> None:
        self.messages: List[str] = []

    def set(self, message: str) -> None:
        self.messages.append(message)


class DummyCanvas:
    def __init__(self) -> None:
        self.grid_visible = False
        self.redraw_calls = 0

    def redraw_all(self) -> None:
        self.redraw_calls += 1


class DummyController:
    def __init__(self) -> None:
        self.calls: List[str] = []

    def delete_selected(self) -> None:
        self.calls.append("delete_selected")

    def duplicate_selected(self) -> None:
        self.calls.append("duplicate_selected")

    def toggle_snap(self) -> None:
        self.calls.append("toggle_snap")

    def toggle_link_mode(self) -> None:
        self.calls.append("toggle_link_mode")

    def undo(self) -> None:
        self.calls.append("undo")

    def redo(self) -> None:
        self.calls.append("redo")

    def reset_view(self) -> None:
        self.calls.append("reset_view")

    def fit_to_diagram(self) -> None:
        self.calls.append("fit_to_diagram")


class DummyApp:
    def __init__(self) -> None:
        self._grid_var = DummyGridVar(True)
        self.canvas = DummyCanvas()
        self.status = DummyStatus()
        self.canvas_controller = DummyController()


@pytest.fixture()
def actions() -> AppActions:
    return AppActions(DummyApp())


def test_toggle_grid_updates_canvas(actions: AppActions) -> None:
    app = actions._app  # type: ignore[attr-defined]
    actions.toggle_grid()
    assert app.canvas.grid_visible is True
    assert app.canvas.redraw_calls == 1
    assert app.status.messages[-1] == "Grid sichtbar"
    app._grid_var.set(False)
    actions.toggle_grid()
    assert app.canvas.grid_visible is False
    assert app.status.messages[-1] == "Grid verborgen"


def test_edit_actions_delegate_to_controller(actions: AppActions) -> None:
    controller = actions._app.canvas_controller  # type: ignore[attr-defined]
    actions.delete_selected()
    actions.duplicate_selected()
    actions.toggle_snap()
    actions.toggle_link_mode()
    actions.undo()
    actions.redo()
    assert controller.calls == [
        "delete_selected",
        "duplicate_selected",
        "toggle_snap",
        "toggle_link_mode",
        "undo",
        "redo",
    ]


def test_view_actions_delegate(actions: AppActions) -> None:
    controller = actions._app.canvas_controller  # type: ignore[attr-defined]
    actions.reset_view()
    actions.fit_to_diagram()
    assert controller.calls[-2:] == ["reset_view", "fit_to_diagram"]
