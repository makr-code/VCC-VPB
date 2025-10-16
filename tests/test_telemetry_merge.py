import sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from merge_manager import MergeManager
from telemetry_manager import TelemetryManager


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
    def add_element(self, element_type, name, at, element_id=None, push_undo=True):
        eid = element_id or f"E{len(self.elements)+1}"
        el = DummyElement(eid, element_type, name, at[0], at[1])
        self.elements[eid] = el
        return el
    def add_connection(self, source_element, target_element, connection_type, name, connection_id=None, push_undo=True):
        if source_element not in self.elements or target_element not in self.elements:
            return None
        cid = connection_id or f"C{len(self.connections)+1}"
        self.connections[cid] = DummyConnection(cid, source_element, target_element, connection_type)
        return self.connections[cid]
    def push_undo(self):
        pass
    def redraw_all(self):
        pass


def test_merge_full_telemetry():
    canvas = DummyCanvas()
    canvas.add_element("TASK", "A", (0,0), element_id="A")
    tm = TelemetryManager()
    mm = MergeManager(canvas, telemetry=tm)
    payload = {"elements": [{"element_id": "A", "name": "A2"}, {"element_id": "B", "name": "B"}], "connections": []}
    mm.merge_full(payload, auto_rename=True)
    evs = tm.events("merge_full")
    assert len(evs) == 1
    ev = evs[0]
    assert ev.get("added_elements") == 1
    assert "duration_s" in ev


def test_patch_telemetry():
    canvas = DummyCanvas()
    tm = TelemetryManager()
    mm = MergeManager(canvas, telemetry=tm)
    patch = {"elements": [{"element_id": "P1", "name": "P1"}]} 
    mm.apply_add_only_patch(patch, auto_rename=True)
    evs = tm.events("patch_add_only")
    assert len(evs) == 1
    assert evs[0].get("added_elements") == 1