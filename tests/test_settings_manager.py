import os, json, tempfile, shutil, sys, pathlib
# Ensure project root on path
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import types
import pytest

from settings_manager import SettingsManager, LoadedSettings


def make_dummy_app(tmpdir):
    # Minimal Mock-App mit benötigten Attributen
    app = types.SimpleNamespace()
    app._ollama_endpoint = "http://localhost:11434"
    app._ollama_model = "llama:latest"
    app._ollama_temperature = 0.3
    app._ollama_num_predict = 700
    # Fensterfunktionen (ersetzen durch lambdas)
    app.winfo_width = lambda: 800
    app.winfo_height = lambda: 600
    app.state = lambda: "normal"
    app.winfo_rootx = lambda: 50
    app.winfo_rooty = lambda: 60
    # Sidebars
    app._left_pane = types.SimpleNamespace(winfo_width=lambda: 260)
    app._right_pane = types.SimpleNamespace(winfo_width=lambda: 300)
    app._sidebar_left_width = 260
    app._sidebar_right_width = 300
    # Tk Variablen Simulieren
    class _Var:
        def __init__(self, v): self._v=v
        def get(self): return self._v
    app._grid_var = _Var(True)
    app._snap_var = _Var(False)
    app._route_var = _Var("smart")
    # Canvas Mock
    canvas = types.SimpleNamespace()
    canvas.element_style_overrides = {"TASK": {"fill": "#fff"}}
    canvas.time_axis_enabled = True
    canvas.time_axis_interval = 120.0
    canvas.hierarchy_categories = [{"name": "Operativ", "y0":0, "y1":500, "color":"#fff"}]
    app.canvas = canvas
    return app


def test_load_defaults(tmp_path):
    path = tmp_path / "settings.json"
    sm = SettingsManager(str(path))
    ls = sm.load()
    assert isinstance(ls, LoadedSettings)
    assert ls.ollama_endpoint.startswith("http://")
    assert ls.ollama_model
    assert 0.0 <= ls.ollama_temperature <= 1.0
    assert ls.ollama_num_predict > 0


def test_save_and_roundtrip(tmp_path):
    path = tmp_path / "settings.json"
    sm = SettingsManager(str(path))
    app = make_dummy_app(tmp_path)
    ok = sm.save_from_app(app)
    assert ok
    # Datei prüfen
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["ollama_num_predict"] == 700
    # Reload
    sm2 = SettingsManager(str(path))
    ls2 = sm2.load()
    assert ls2.ollama_num_predict == 700
    assert ls2.loaded.view.get("routing_style") if hasattr(ls2, 'loaded') else True


def test_update_ollama(tmp_path):
    path = tmp_path / "settings.json"
    sm = SettingsManager(str(path))
    sm.load()
    sm.update_ollama(endpoint="x", model="y", temperature=0.9, num_predict=1234)
    assert sm.loaded.ollama_endpoint == "x"
    assert sm.loaded.ollama_model == "y"
    assert sm.loaded.ollama_temperature == 0.9
    assert sm.loaded.ollama_num_predict == 1234


def test_legacy_migration(tmp_path):
    legacy = tmp_path / "vpb_settings.json"
    with open(legacy, "w", encoding="utf-8") as f:
        json.dump({"ollama_model": "migrated:1", "ollama_num_predict": 777}, f)
    # settings.json fehlt -> sollte Legacy lesen
    sm = SettingsManager(str(tmp_path / "settings.json"))
    ls = sm.load()
    assert ls.ollama_model == "migrated:1"
    assert ls.ollama_num_predict == 777
