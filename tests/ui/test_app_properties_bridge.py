from __future__ import annotations

from typing import Dict, List, Optional

import pytest

from vpb.ui.app_properties_bridge import AppPropertiesBridge


class DummyStatus:
    def __init__(self) -> None:
        self.messages: List[str] = []

    def set(self, value: str) -> None:
        self.messages.append(value)


class DummyHierCanvas:
    def __init__(self) -> None:
        self.selected_index: Optional[int] = None

    def set_selected_index(self, index: Optional[int]) -> None:
        self.selected_index = index


class DummyProps:
    def __init__(self) -> None:
        self.hierarchy_calls: List[tuple[Optional[int], Optional[Dict[str, object]]]] = []
        self.elements: List[tuple[object, Optional[object]]] = []
        self._mode = "diagram"

    def set_hierarchy(self, index: Optional[int], data: Optional[Dict[str, object]]) -> None:
        self.hierarchy_calls.append((index, data))

    def set_element(self, element, connection=None) -> None:
        self.elements.append((element, connection))


class DummyCanvas:
    def __init__(self) -> None:
        self.selected_id: Optional[str] = None
        self.selected_conn_id: Optional[str] = None
        self.connections: Dict[str, DummyConnection] = {}
        self.elements: Dict[str, DummyElement] = {}
        self.hierarchy_categories: List[Dict[str, object]] = []
        self.undo_calls = 0
        self.redraw_calls = 0
        self.ensure_group_calls = 0
        self.revert_group_calls = 0

    def push_undo(self) -> None:
        self.undo_calls += 1

    def redraw_all(self) -> None:
        self.redraw_calls += 1

    def _ensure_ref_group(self, element) -> None:
        self.ensure_group_calls += 1

    def _revert_ref_group_if_needed(self, element) -> None:
        self.revert_group_calls += 1


class DummyConnection:
    def __init__(self) -> None:
        self.connection_type = "sequence"
        self.arrow_style = "none"
        self.routing_mode = "auto"
        self.description = ""


class DummyElement:
    def __init__(self) -> None:
        self.element_type = "TASK"
        self.name = "Old"
        self.description = ""
        self.responsible_authority = "Amt"
        self.deadline_days = 5
        self.legal_basis = "Old"
        self.geo_reference = "Old"
        self.hierarchy: Optional[str] = None
        self.y = 10
        self.ref_file = "ref.json"
        self.collapsed = False


class DummyApp:
    def __init__(self) -> None:
        self.canvas = DummyCanvas()
        self.props = DummyProps()
        self.status = DummyStatus()
        self.hier_canvas = DummyHierCanvas()
        self._selected_hierarchy_index: Optional[int] = 2
        self._update_calls: List[tuple[int, Dict[str, object]]] = []

    def _update_hierarchy_category(self, index: int, data: Dict[str, object]) -> None:
        self._update_calls.append((index, data))


@pytest.fixture()
def bridge() -> AppPropertiesBridge:
    app = DummyApp()
    return AppPropertiesBridge(app)


def test_on_selection_changed_resets_state(bridge: AppPropertiesBridge) -> None:
    app = bridge._app  # type: ignore[attr-defined]
    element = object()
    connection = object()
    bridge.on_selection_changed(element, connection)
    assert app._selected_hierarchy_index is None
    assert app.hier_canvas.selected_index is None
    assert app.props.hierarchy_calls[-1] == (None, None)
    assert app.props.elements[-1] == (element, connection)


def test_apply_properties_hierarchy_calls_update(bridge: AppPropertiesBridge) -> None:
    app = bridge._app  # type: ignore[attr-defined]
    bridge.apply_properties({
        "kind": "hierarchy",
        "index": "3",
        "name": "Layer",
        "color": "#ffffff",
        "y0": 0,
        "y1": 10,
    })
    assert app._update_calls == [(3, {"name": "Layer", "color": "#ffffff", "y0": 0, "y1": 10})]


def test_apply_properties_connection_updates_fields(bridge: AppPropertiesBridge) -> None:
    app = bridge._app  # type: ignore[attr-defined]
    conn = DummyConnection()
    app.canvas.connections["C1"] = conn
    app.canvas.selected_conn_id = "C1"
    bridge.apply_properties({
        "kind": "connection",
        "connection_type": "EVENT",
        "arrow_style": "arrow",
        "routing_mode": "straight",
        "description": "New",
    })
    assert app.canvas.undo_calls == 1
    assert conn.connection_type == "EVENT"
    assert conn.arrow_style == "arrow"
    assert conn.routing_mode == "straight"
    assert conn.description == "New"
    assert app.canvas.redraw_calls == 1
    assert app.status.messages[-1] == "Verbindung aktualisiert."


def test_apply_properties_element_updates_fields(bridge: AppPropertiesBridge) -> None:
    app = bridge._app  # type: ignore[attr-defined]
    element = DummyElement()
    app.canvas.elements["E1"] = element
    app.canvas.selected_id = "E1"
    app.canvas.hierarchy_categories = [
        {"name": "Layer", "y0": 0.0, "y1": 20.0},
    ]
    bridge.apply_properties({
        "element_type": "GROUP",
        "name": "New Name",
        "description": "Desc",
        "responsible_authority": "Amt Neu",
        "deadline_days": "7",
        "legal_basis": "Neu",
        "geo_reference": "Geo",
        "hierarchy": "Layer",
        "collapsed": True,
    })
    assert app.canvas.undo_calls == 1
    assert element.element_type == "GROUP"
    assert element.name == "New Name"
    assert element.description == "Desc"
    assert element.responsible_authority == "Amt Neu"
    assert element.deadline_days == 7
    assert element.legal_basis == "Neu"
    assert element.geo_reference == "Geo"
    assert element.hierarchy == "Layer"
    assert element.y == 10  # average of 0 and 20
    assert element.collapsed is True
    assert app.canvas.ensure_group_calls == 1
    assert app.canvas.redraw_calls == 1
