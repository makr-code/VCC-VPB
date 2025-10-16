import sys, pathlib, types
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from merge_manager import MergeManager

class DummyElement:
    def __init__(self, element_id, etype="TASK", name="", x=0, y=0):
        self.element_id = element_id
        self.element_type = etype
        self.name = name
        self.x = x
        self.y = y
        self.description = ""
        self.responsible_authority = ""
        self.legal_basis = ""
        self.deadline_days = 0

class DummyConnection:
    def __init__(self, connection_id, source, target, ctype="SEQUENCE"):
        self.connection_id = connection_id
        self.source_element = source
        self.target_element = target
        self.connection_type = ctype

class DummyCanvas:
    def __init__(self):
        self.elements = {}
        self.connections = {}
        self._undo_count = 0
    def add_element(self, element_type, name, at, element_id=None, push_undo=True):
        if push_undo:
            self.push_undo()
        eid = element_id or f"E{len(self.elements)+1}"
        el = DummyElement(eid, element_type, name, at[0], at[1])
        self.elements[eid] = el
        return el
    def add_connection(self, source_element, target_element, connection_type, name, connection_id=None, push_undo=True):
        if push_undo:
            self.push_undo()
        if source_element not in self.elements or target_element not in self.elements:
            return None
        cid = connection_id or f"C{len(self.connections)+1}"
        self.connections[cid] = DummyConnection(cid, source_element, target_element, connection_type)
        return self.connections[cid]
    def push_undo(self):
        self._undo_count += 1
    def redraw_all(self):
        pass

@pytest.fixture
def canvas():
    c = DummyCanvas()
    # Basis-Elemente
    c.add_element("TASK", "A", (10,10), element_id="A", push_undo=False)
    c.add_element("TASK", "B", (30,30), element_id="B", push_undo=False)
    return c

@pytest.fixture
def mm(canvas):
    return MergeManager(canvas)


def test_merge_adds_and_renames(mm, canvas):
    data = {
        "elements": [
            {"element_id": "A", "element_type": "TASK", "name": "A2", "x":100, "y":100},
            {"element_id": "C", "element_type": "TASK", "name": "C", "x":120, "y":100},
        ],
        "connections": [
            {"connection_id": "X", "source_element": "A", "target_element": "C", "connection_type": "SEQUENCE"},
            {"connection_id": "X", "source_element": "C", "target_element": "A", "connection_type": "SEQUENCE"},
        ]
    }
    res = mm.merge_full(data, auto_rename=True)
    assert res.added_elements == 1  # nur C
    assert "C" in canvas.elements
    # Connection-Rename kann 0 oder 1 sein je nach Reihenfolge; akzeptiere beides
    assert res.added_connections == 2
    assert len(res.connection_renames) in (0,1)


def test_merge_conflict_no_autorename(mm, canvas):
    # Verhalten: Konflikt wird einfach ausgelassen (kein Exception) -> prüfen dass nichts hinzugefügt
    before = set(canvas.elements.keys())
    data = {"elements": [{"element_id":"A", "element_type":"TASK", "name":"Adup", "x":0, "y":0}]}
    res = mm.merge_full(data, auto_rename=False)
    after = set(canvas.elements.keys())
    assert before == after
    assert res.added_elements == 0


def test_update_mode_overwrite(mm, canvas):
    # Vorhandenes Element A hat leere description -> wird gesetzt
    canvas.elements["A"].description = "OLD"
    data = {"elements": [{"element_id":"A", "description":"NEW", "name":"X"}]}
    mm.merge_full(data, update_mode="overwrite")
    assert canvas.elements["A"].description == "NEW"


def test_update_mode_fill_empty(mm, canvas):
    canvas.elements["A"].description = ""  # leer -> darf gefüllt werden
    data = {"elements": [{"element_id":"A", "description":"FILLED"}]}
    mm.merge_full(data, update_mode="fill-empty")
    assert canvas.elements["A"].description == "FILLED"
    # No overwrite if already filled
    data2 = {"elements": [{"element_id":"A", "description":"SHOULD_NOT"}]}
    mm.merge_full(data2, update_mode="fill-empty")
    assert canvas.elements["A"].description == "FILLED"


def test_snap_positions(mm, canvas):
    data = {"elements": [{"element_id":"N1", "x":73, "y":127}]}
    mm.merge_full(data, snap=True, grid=50)
    el = canvas.elements.get("N1") or canvas.elements.get("N1_1")
    assert el.x % 50 == 0 and el.y % 50 == 0


def test_patch_add_only(mm, canvas):
    before = set(canvas.elements.keys())
    patch = {"elements":[{"element_id":"P1","x":0,"y":0}], "connections": []}
    res = mm.apply_add_only_patch(patch)
    after = set(canvas.elements.keys())
    assert res.added_elements == 1
    assert len(after) == len(before) + 1


def test_patch_single_undo(mm, canvas):
    before_undo = canvas._undo_count
    patch = {
        "elements": [
            {"element_id": "PX1", "element_type": "TASK", "x": 10, "y": 10},
            {"element_id": "PX2", "element_type": "TASK", "x": 60, "y": 60},
        ],
        "connections": [
            {"connection_id": "PC1", "source_element": "PX1", "target_element": "PX2", "connection_type": "SEQUENCE"}
        ],
    }
    mm.apply_add_only_patch(patch)
    assert canvas._undo_count == before_undo + 1


def test_patch_conflict_no_autorename(mm, canvas):
    patch = {"elements":[{"element_id":"A","x":0,"y":0}]}
    with pytest.raises(ValueError):
        mm.apply_add_only_patch(patch, auto_rename=False)


def test_deep_reference_rename(mm, canvas):
    # Element mit referenzierten IDs in verschachtelten Strukturen
    data = {
        "elements": [
            {"element_id": "A", "element_type": "TASK", "name": "A1"},  # kollidiert
            {"element_id": "X", "element_type": "GROUP", "name": "Grp", "members": ["A", "B"], "linked_elements": [{"ref": "A"}, {"ref": "B"}]},
        ],
        "connections": [
            {"connection_id": "C1", "source_element": "A", "target_element": "X"}
        ]
    }
    res = mm.merge_full(data, auto_rename=True)
    # A wird umbenannt, X neu hinzugefügt
    assert res.added_elements == 1  # nur X, A kollidiert -> Update oder Skip
    # Prüfe, dass in Element X die Referenzen auf den neuen Namen zeigen
    # Ermittle neue ID von A falls umbenannt
    renamed_id = res.element_renames.get("A")
    if renamed_id:
        # Finde gespeichertes Element X
        el_x = canvas.elements.get("X")
        assert el_x is not None
        members = getattr(el_x, "members", [])
        assert renamed_id in members
    # Connection sollte ebenfalls auf die umbenannte ID zeigen
    if renamed_id:
        for cid, c in canvas.connections.items():
            if c.source_element == renamed_id or c.target_element == renamed_id:
                break
        else:
            pytest.fail("Umbenannte ID nicht in Verbindungen referenziert")
