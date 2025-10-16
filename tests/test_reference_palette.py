import sys
import pathlib
import json

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vpb.ui.canvas_controller import CanvasController
from vpb.models import VPBElement
from vpb.ui.canvas import VPBCanvas


class DummyStatus:
    def __init__(self):
        self.message = None

    def set(self, message: str) -> None:
        self.message = message


class DummyCanvas:
    def __init__(self):
        self.last_add_mode = None

    def start_add_mode(self, element_type: str, default_name: str = "Neues Element", payload=None):
        self.last_add_mode = {
            "element_type": element_type,
            "default_name": default_name,
            "payload": payload,
        }


class DummyApp:
    def __init__(self):
        self.canvas = DummyCanvas()
        self.status = DummyStatus()

    def _is_text_input_focus(self):  # pragma: no cover - nicht benötigt, aber CanvasController fragt darauf
        return False


def test_handle_palette_pick_reference_payload():
    app = DummyApp()
    controller = CanvasController(app)
    item = {
        "type": "SUBPROCESS",
        "name": "Terminvereinbarung (Ref)",
        "fill": "#F0F4FF",
        "text_color": "#102A6B",
        "reference": {
            "id": "ref-termin",
            "snippet": "processes/terminvereinbarung_einfach.vpb.json",
            "name": "Terminvereinbarung – Bürgerbüro",
            "default_name": "Terminvereinbarung – Bürgerbüro",
            "element_type": "SUBPROCESS",
            "category": "Bürgerdienste",
            "label": "Terminvereinbarung",
            "description": "Standardtermin inkl. Bestätigung",
            "deadline_days": 5,
        },
    }

    controller.handle_palette_pick(item)

    result = app.canvas.last_add_mode
    assert result is not None, "Die Canvas sollte in den Add-Modus versetzt werden."
    assert result["element_type"] == "SUBPROCESS"
    assert "payload" in result and isinstance(result["payload"], dict)

    payload = result["payload"]
    assert payload["ref_process"]["ref_file"].endswith("terminvereinbarung_einfach.vpb.json")
    assert payload["ref_process"]["id"] == "ref-termin"
    assert payload["style"]["fill"] == "#F0F4FF"
    assert payload["style"]["text_color"] == "#102A6B"
    assert payload["properties"]["description"].startswith("Standardtermin")
    assert payload["properties"]["deadline_days"] == 5
    assert payload["extras"]["ref_process_category"] == "Bürgerdienste"
    assert "Referenzprozess" in app.status.message


class _PayloadCanvasStub:
    _apply_add_payload = VPBCanvas._apply_add_payload

    def __init__(self):
        self.calls = {"group": 0, "preview": 0}

    def _ensure_ref_group(self, element):
        self.calls["group"] += 1

    def _load_ref_preview(self, element):
        self.calls["preview"] += 1


def test_apply_add_payload_sets_metadata():
    canvas = _PayloadCanvasStub()
    element = VPBElement("S001", "SUBPROCESS", "Stub", 100, 200)

    payload = {
        "style": {"fill": "#123456", "outline": "#654321", "text_color": "#ffffff", "shape": "rect"},
        "properties": {
            "description": "Test Prozess",
            "responsible_authority": "Testamt",
            "legal_basis": "§ 1 TestG",
            "deadline_days": "14",
            "geo_reference": "Teststadt",
        },
        "extras": {"ref_process_label": "Label", "ref_process_category": "Kategorie"},
        "ref_process": {
            "id": "ref-test",
            "ref_file": "processes/test_snippet.vpb.json",
            "name": "Referenz Test",
            "original_type": "SUBPROCESS",
            "auto_group": True,
        },
    }

    canvas._apply_add_payload(element, payload)

    assert element.style_override == {
        "fill": "#123456",
        "outline": "#654321",
        "text_color": "#ffffff",
        "shape": "rect",
    }
    assert element.description == "Test Prozess"
    assert element.responsible_authority == "Testamt"
    assert element.legal_basis == "§ 1 TestG"
    assert element.deadline_days == 14
    assert element.geo_reference == "Teststadt"
    assert getattr(element, "ref_process_label") == "Label"
    assert getattr(element, "ref_process_category") == "Kategorie"
    assert element.name == "Referenz Test"
    assert element.original_element_type == "SUBPROCESS"
    assert element.ref_file == "processes/test_snippet.vpb.json"
    assert getattr(element, "ref_process_id") == "ref-test"
    assert canvas.calls["group"] == 1
    assert canvas.calls["preview"] == 1


def test_reference_palette_contains_admin_block():
    palette_path = ROOT / "palettes" / "reference_palette.json"
    with palette_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    categories = {cat.get("id"): cat for cat in data.get("categories", [])}
    assert "ref-verwaltung-recht" in categories, "Kategorie für Verwaltungsverfahren & Rechtsschutz fehlt."
    items = {item["reference"]["id"]: item for item in categories["ref-verwaltung-recht"].get("items", [])}

    expected = {
        "ref-bescheidserlass": "processes/verwaltungsverfahren_bescheid.vpb.json",
        "ref-anhoerung": "processes/verwaltungsverfahren_anhoerung.vpb.json",
        "ref-widerspruch": "processes/verwaltungsverfahren_widerspruch.vpb.json",
        "ref-anfechtungsklage": "processes/verwaltungsgericht_anfechtungsklage.vpb.json",
        "ref-verpflichtungsklage": "processes/verwaltungsgericht_verpflichtungsklage.vpb.json",
        "ref-eilverfahren-80-5": "processes/verwaltungsgericht_eilverfahren_80_5.vpb.json",
        "ref-fortsetzungsfeststellung": "processes/verwaltungsgericht_fortsetzungsfeststellungsklage.vpb.json",
    }

    assert set(items.keys()) == set(expected.keys())
    for ref_id, snippet in expected.items():
        assert items[ref_id]["reference"]["snippet"] == snippet
        assert items[ref_id]["reference"]["auto_group"] is True


def test_reference_palette_contains_environment_block():
    palette_path = ROOT / "palettes" / "reference_palette.json"
    with palette_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    categories = {cat.get("id"): cat for cat in data.get("categories", [])}
    assert "ref-bauen-umwelt" in categories, "Kategorie für Bauen & Umwelt fehlt."

    items = {item["reference"]["id"]: item for item in categories["ref-bauen-umwelt"].get("items", [])}

    expected = {
        "ref-bauantrag": "processes/bauantrag_pruefung_komplex.vpb.json",
        "ref-umweltpruefung": "processes/bauleitplanung_umweltpruefung_20250923_vpb.json",
        "ref-immissionsschutz-genehmigung": "processes/immissionsschutz_genehmigung.vpb.json",
        "ref-immissionsschutz-aenderung": "processes/immissionsschutz_aenderungsanzeige.vpb.json",
        "ref-immissionsschutz-monitoring": "processes/immissionsschutz_emissionsmonitoring.vpb.json",
        "ref-immissionsschutz-stoerfall": "processes/immissionsschutz_stoerfallmanagement.vpb.json",
        "ref-immissionsschutz-laermaktionsplan": "processes/immissionsschutz_laermaktionsplan.vpb.json",
        "ref-immissionsschutz-sondernutzung": "processes/immissionsschutz_sondernutzung.vpb.json",
    }

    assert set(items.keys()) == set(expected.keys())
    for ref_id, snippet in expected.items():
        assert items[ref_id]["reference"]["snippet"] == snippet
        assert items[ref_id]["reference"]["auto_group"] is True


def test_reference_palette_contains_internal_communications_block():
    palette_path = ROOT / "palettes" / "reference_palette.json"
    with palette_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    categories = {cat.get("id"): cat for cat in data.get("categories", [])}
    assert "ref-verwaltung-intern" in categories, "Kategorie für interne Verwaltungsprozesse fehlt."

    items = {item["reference"]["id"]: item for item in categories["ref-verwaltung-intern"].get("items", [])}

    assert {"ref-kommunikationsmittel", "ref-rechnungseingang", "ref-posteingang", "ref-beschlussvorlage"} <= set(items.keys())

    comm_ref = items["ref-kommunikationsmittel"]["reference"]
    assert comm_ref["snippet"] == "processes/verwaltung_kommunikationsmittel_flow.vpb.json"
    assert comm_ref["default_name"] == "Kommunikationsmittel koordinieren"
    assert comm_ref["auto_group"] is True

    invoice_ref = items["ref-rechnungseingang"]["reference"]
    assert invoice_ref["snippet"] == "processes/verwaltung_rechnungseingang_pruefung.vpb.json"
    assert invoice_ref["default_name"] == "Rechnungseingang prüfen"
    assert invoice_ref["auto_group"] is True

    mailroom_ref = items["ref-posteingang"]["reference"]
    assert mailroom_ref["snippet"] == "processes/verwaltung_posteingang_verteilung.vpb.json"
    assert mailroom_ref["default_name"] == "Posteingang verteilen"
    assert mailroom_ref["auto_group"] is True

    council_ref = items["ref-beschlussvorlage"]["reference"]
    assert council_ref["snippet"] == "processes/verwaltung_beschlussvorlage_erstellen.vpb.json"
    assert council_ref["default_name"] == "Beschlussvorlage erstellen"
    assert council_ref["auto_group"] is True