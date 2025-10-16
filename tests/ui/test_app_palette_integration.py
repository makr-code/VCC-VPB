from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import pytest

from vpb.ui.app_palette_integration import AppPaletteIntegration


class DummyController:
    def __init__(self) -> None:
        self.reload_calls = 0
        self.pick_calls: List[Dict[str, object]] = []

    def reload_palettes(self) -> None:
        self.reload_calls += 1

    def handle_palette_pick(self, item: Dict[str, object]) -> None:
        self.pick_calls.append(item)


class DummyProps:
    def __init__(self) -> None:
        self.set_hierarchy_calls: List[tuple[Optional[int], Optional[Dict[str, object]]]] = []
        self.refresh_hierarchy_options_args: List[List[str]] = []
        self.set_element_args: List[object] = []
        self._mode = "element"

    def set_hierarchy(self, index: Optional[int], data: Optional[Dict[str, object]]) -> None:
        self.set_hierarchy_calls.append((index, data))

    def refresh_hierarchy_options(self, names: List[str]) -> None:
        self.refresh_hierarchy_options_args.append(list(names))

    def set_element(self, element) -> None:
        self.set_element_args.append(element)


class DummyStatus:
    def __init__(self) -> None:
        self.messages: List[str] = []

    def set(self, message: str) -> None:
        self.messages.append(message)


class DummyHierCanvas:
    def __init__(self) -> None:
        self.selected_index: Optional[int] = None
        self.redraw_calls = 0

    def set_selected_index(self, index: Optional[int]) -> None:
        self.selected_index = index

    def redraw(self) -> None:
        self.redraw_calls += 1


@dataclass
class DummyElement:
    element_type: str = "TASK"
    name: str = "Element"
    description: str = ""
    responsible_authority: str = ""
    deadline_days: int = 0
    legal_basis: str = ""
    geo_reference: str = ""
    hierarchy: Optional[str] = None
    y: int = 0
    ref_file: str = ""
    collapsed: bool = False


class DummyCanvas:
    def __init__(self) -> None:
        self.hierarchy_categories: List[Dict[str, object]] = []
        self._hierarchy_color_cache: Dict[str, object] = {}
        self.undo_calls = 0
        self.redraw_calls = 0
        self.elements: Dict[str, DummyElement] = {"E1": DummyElement(y=10)}
        self.selected_id = "E1"

    def push_undo(self) -> None:
        self.undo_calls += 1

    def redraw_all(self) -> None:
        self.redraw_calls += 1


class DummyApp:
    def __init__(self) -> None:
        self.canvas = DummyCanvas()
        self.canvas_controller = DummyController()
        self.props = DummyProps()
        self.status = DummyStatus()
        self.hier_canvas = DummyHierCanvas()
        self._pref_hierarchy_categories: List[Dict[str, object]] = []
        self._selected_hierarchy_index: Optional[int] = None
        self._save_settings_calls = 0

    def _save_settings(self) -> None:
        self._save_settings_calls += 1

    def wait_window(self, dialog) -> None:
        pass


class DummyDialog:
    def __init__(self, app: DummyApp, category: Dict[str, object]) -> None:
        self.result = {"name": "Updated", "color": "#ff0000", "y0": 0, "y1": 100}


@pytest.fixture()
def app() -> DummyApp:
    return DummyApp()


def test_reload_and_pick_delegate_to_controller(app: DummyApp) -> None:
    integration = AppPaletteIntegration(app, category_dialog_cls=DummyDialog)
    integration.reload_palettes()
    integration.on_palette_pick({"name": "Task"})
    assert app.canvas_controller.reload_calls == 1
    assert app.canvas_controller.pick_calls == [{"name": "Task"}]


def test_apply_hierarchy_categories_updates_state(app: DummyApp) -> None:
    integration = AppPaletteIntegration(app, category_dialog_cls=DummyDialog)
    categories = [
        {"name": "Layer 1", "color": "#123456", "y0": 0, "y1": 100},
        {"name": "Layer 2", "color": "#abcdef", "y0": 110, "y1": 200},
    ]
    integration.apply_hierarchy_categories(categories, select_index=0, status_message="Done", push_undo=True)
    assert app.canvas.hierarchy_categories == categories
    assert app.canvas.undo_calls == 1
    assert app.canvas.redraw_calls >= 1
    assert app.hier_canvas.selected_index == 0
    assert app.hier_canvas.redraw_calls >= 1
    assert app._selected_hierarchy_index == 0
    assert app.props.set_hierarchy_calls[-1] == (0, categories[0])
    assert app.props.refresh_hierarchy_options_args[-1] == ["Layer 1", "Layer 2"]
    assert app._pref_hierarchy_categories == categories
    assert app._save_settings_calls == 1
    assert app.status.messages[-1] == "Done"


def test_update_hierarchy_category_validates_and_updates(app: DummyApp) -> None:
    integration = AppPaletteIntegration(app, category_dialog_cls=DummyDialog)
    app.canvas.hierarchy_categories = [
        {"name": "Old", "color": "#111111", "y0": 0, "y1": 10},
    ]
    success = integration.update_hierarchy_category(
        0,
        {"name": "New", "color": "#222222", "y0": "0", "y1": "100"},
    )
    assert success is True
    updated = app.canvas.hierarchy_categories[0]
    assert updated["name"] == "New"
    assert updated["color"] == "#222222"
    assert updated["y0"] == 0.0
    assert updated["y1"] == 100.0
    assert app.props.set_hierarchy_calls[-1][0] == 0


def test_update_hierarchy_category_invalid_name(monkeypatch, app: DummyApp) -> None:
    integration = AppPaletteIntegration(app, category_dialog_cls=DummyDialog)
    app.canvas.hierarchy_categories = [{"name": "Old", "color": "#111111", "y0": 0, "y1": 10}]
    errors: List[str] = []
    monkeypatch.setattr("vpb.ui.app_palette_integration.messagebox.showerror", lambda title, msg: errors.append(msg))
    success = integration.update_hierarchy_category(0, {"name": "", "color": "#ffffff", "y0": 0, "y1": 10})
    assert success is False
    assert errors


def test_open_hierarchy_dialog_applies_result(app: DummyApp) -> None:
    integration = AppPaletteIntegration(app, category_dialog_cls=DummyDialog)
    called: List[tuple[int, Dict[str, object]]] = []

    def fake_update(self, index: int, data: Dict[str, object]) -> None:
        called.append((index, data))

    integration.update_hierarchy_category = fake_update.__get__(integration, AppPaletteIntegration)  # type: ignore[assignment]
    integration.open_hierarchy_dialog(1, {"name": "Old"})
    assert called == [(1, {"name": "Updated", "color": "#ff0000", "y0": 0, "y1": 100})]
