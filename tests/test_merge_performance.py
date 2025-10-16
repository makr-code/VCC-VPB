import sys, pathlib, time, os
import random
import json

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
        self._undo_count += 1
    def redraw_all(self):
        pass


def _make_payload(n_new: int, existing_ids: list[str]):
    """Erzeuge ein Merge-JSON mit n_new neuen Elementen + einigen Referenzen.
    Ca. 5% der neuen Elemente kollidieren absichtlich mit bestehenden IDs.
    Connections verbinden lineare Kette und zufällige Querverbindungen.
    """
    elems = []
    collisions = max(1, n_new // 20)
    for i in range(n_new):
        if i < collisions and existing_ids:
            eid = random.choice(existing_ids)  # provoziert Auto-Rename / Update
        else:
            eid = f"N{i}"
        elems.append({
            "element_id": eid,
            "element_type": "TASK",
            "name": f"Task {i}",
            "x": (i % 50) * 10,
            "y": (i // 50) * 20,
            # verschachtelte Referenzen zum Test von deep rename
            "linked_elements": [{"ref": eid}],
        })
    # Connections (einfach Kette + ein paar Randoms)
    conns = []
    for i in range(n_new - 1):
        conns.append({
            "connection_id": f"NC{i}",
            "source_element": elems[i]["element_id"],
            "target_element": elems[i+1]["element_id"],
            "connection_type": "SEQUENCE"
        })
    for _ in range(min( max(1, n_new // 10), 50)):
        a, b = random.sample(elems, 2)
        conns.append({
            "connection_id": f"R{random.randint(0, 999999)}",
            "source_element": a["element_id"],
            "target_element": b["element_id"],
            "connection_type": "SEQUENCE"
        })
    return {"elements": elems, "connections": conns}


def test_merge_performance_log_only():
    # Szenarien: moderat halten damit Test-Suite schnell bleibt
    scenarios = [200, 500, 1000]
    seed = int(os.environ.get("VPB_MERGE_PERF_SEED", "42"))
    random.seed(seed)
    canvas = DummyCanvas()
    # Basis-Bestand (50 Elemente) für Kollisionen
    for i in range(50):
        canvas.add_element("TASK", f"Base {i}", (0, i*5), element_id=f"B{i}")
    mm = MergeManager(canvas)

    results = []
    for n in scenarios:
        payload = _make_payload(n, list(canvas.elements.keys()))
        start = time.perf_counter()
        res = mm.merge_full(payload, auto_rename=True, snap=False, update_mode="none")
        dur = time.perf_counter() - start
        results.append((n, dur, res.added_elements, res.added_connections, len(res.element_renames)))

    # Nur logging – kein Fail. Optionaler Schwellenwert via Env führt zu Assertion.
    threshold = os.environ.get("VPB_MERGE_PERF_MAX_MS")
    for (n, dur, added_e, added_c, renames) in results:
        print(f"PERF MERGE n={n}: {dur*1000:.1f} ms | added_e={added_e} added_c={added_c} renames={renames}")
        if threshold:
            try:
                thr_s = float(threshold)/1000.0
                assert dur <= thr_s, f"Merge {n} dauerte {dur:.3f}s > Threshold {thr_s:.3f}s"
            except ValueError:
                pass
    # Minimale Validierung: Anzahl Ergebnisse == Anzahl Szenarien
    assert len(results) == len(scenarios)
