"""SettingsManager
--------------------
Kapselt Laden/Speichern der Projekt-Einstellungen (settings.json) sowie
Migration eines evtl. vorhandenen Legacy-Files `vpb_settings.json`.

Ziel: Entkopplung von Persistenz- und Transformationslogik aus der
monolithischen `VPBDesignerApp`.

Verantwortlichkeiten:
  - Robust laden (mit Defaults) und optional Migration
  - Bereitstellen strukturierter Properties
  - Speichern aktueller App-Zustände (Fenster, Sidebars, View, Styles, Ollama)

Die Klasse arbeitet absichtlich ohne direkte UI-Abhängigkeiten.
GUI-spezifische Dialoge verbleiben in der App.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from typing import Any, Dict, Optional


@dataclass
class LoadedSettings:
    # Ollama
    ollama_endpoint: str = "http://localhost:11434"
    ollama_model: str = "llama:latest"
    ollama_temperature: float = 0.2
    ollama_num_predict: int = 600
    # Window
    window: Dict[str, Any] = field(default_factory=dict)
    sidebars: Dict[str, Any] = field(default_factory=dict)
    view: Dict[str, Any] = field(default_factory=dict)
    element_styles: Dict[str, Any] = field(default_factory=dict)
    hierarchy_categories: Optional[list] = None
    navigation: Dict[str, Any] = field(default_factory=dict)
    onboarding: Dict[str, Any] = field(default_factory=dict)
    autosave: Dict[str, Any] = field(default_factory=dict)


class SettingsManager:
    def __init__(self, settings_path: str):
        self.settings_path = settings_path
        # Legacy-Datei: im gleichen Verzeichnis wie settings_path suchen (früher cwd)
        base_dir = os.path.dirname(os.path.abspath(settings_path)) or os.getcwd()
        self.legacy_path = os.path.join(base_dir, "vpb_settings.json")
        self.loaded = LoadedSettings()

    # ---- Laden ----
    def load(self) -> LoadedSettings:
        """Lädt Settings (robust). Bei Fehlern werden Defaults behalten."""
        data: Dict[str, Any] = {}
        try:
            path = self.settings_path
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    raw = json.load(f) or {}
                    if isinstance(raw, dict):
                        data = raw
            elif os.path.exists(self.legacy_path):
                with open(self.legacy_path, "r", encoding="utf-8") as f:
                    raw = json.load(f) or {}
                    if isinstance(raw, dict):
                        data = raw
        except Exception:
            data = {}

        L = LoadedSettings()
        # Ollama
        L.ollama_endpoint = str(data.get("ollama_endpoint") or L.ollama_endpoint)
        L.ollama_model = str(data.get("ollama_model") or L.ollama_model)
        try:
            t = float(data.get("ollama_temperature", L.ollama_temperature))
            L.ollama_temperature = max(0.0, min(1.0, t))
        except Exception:
            pass
        try:
            n = int(data.get("ollama_num_predict", L.ollama_num_predict))
            if n > 0:
                L.ollama_num_predict = n
        except Exception:
            pass
        # Window / Sidebars / View
        win = data.get("window")
        if isinstance(win, dict):
            L.window = win
        sb = data.get("sidebars")
        if isinstance(sb, dict):
            L.sidebars = sb
        vw = data.get("view")
        if isinstance(vw, dict):
            L.view = vw
        # Styles
        es = data.get("element_styles")
        if isinstance(es, dict):
            L.element_styles = es
        hc = data.get("hierarchy_categories")
        if isinstance(hc, list):
            L.hierarchy_categories = hc
        nav = data.get("navigation")
        if isinstance(nav, dict):
            L.navigation = nav
        onboarding = data.get("onboarding")
        if isinstance(onboarding, dict):
            L.onboarding = onboarding
        autosave = data.get("autosave")
        if isinstance(autosave, dict):
            L.autosave = autosave

        self.loaded = L
        return L

    # ---- Speichern ----
    def save_from_app(self, app: Any) -> bool:
        """Extrahiert Settings aus der App und schreibt sie nach `settings_path`.
        Gibt True bei (vermutlich) Erfolg zurück.
        """
        try:
            # Basis-Daten / Fallbacks
            try:
                w = int(app.winfo_width())
                h = int(app.winfo_height())
            except Exception:
                w, h = 1200, 800
            state = ""
            try:
                state = str(app.state())
            except Exception:
                state = ""
            x = y = None
            if state not in ("zoomed", "iconic"):
                try:
                    x = int(app.winfo_rootx())
                    y = int(app.winfo_rooty())
                except Exception:
                    x = y = None
            try:
                lw = int(app._left_pane.winfo_width()) if hasattr(app, "_left_pane") else int(getattr(app, "_sidebar_left_width", 250))
                rw = int(app._right_pane.winfo_width()) if hasattr(app, "_right_pane") else int(getattr(app, "_sidebar_right_width", 250))
            except Exception:
                lw, rw = int(getattr(app, "_sidebar_left_width", 250)), int(getattr(app, "_sidebar_right_width", 250))
            try:
                grid_visible = bool(app._grid_var.get())
            except Exception:
                grid_visible = True
            try:
                snap = bool(app._snap_var.get())
            except Exception:
                snap = False
            try:
                routing = str(app._route_var.get())
            except Exception:
                routing = "smart"
            try:
                element_styles = dict(app.canvas.element_style_overrides)
            except Exception:
                element_styles = {}
            onboarding_state = {
                "pan_hint_dismissed": bool(getattr(app, "_pan_hint_dismissed", False)),
            }
            autosave_state = {
                "enabled": bool(getattr(app, "_autosave_enabled", True)),
                "interval_minutes": int(max(1, int(getattr(app, "_autosave_interval_minutes", 3) or 3))),
            }
            data = {
                "ollama_endpoint": getattr(app, "_ollama_endpoint", "http://localhost:11434"),
                "ollama_model": getattr(app, "_ollama_model", "llama:latest"),
                "ollama_temperature": getattr(app, "_ollama_temperature", 0.2),
                "ollama_num_predict": getattr(app, "_ollama_num_predict", 600),
                "window": {"width": w, "height": h, "x": x, "y": y, "state": state},
                "sidebars": {"left_width": lw, "right_width": rw},
                "view": {
                    "grid_visible": grid_visible,
                    "snap_to_grid": snap,
                    "routing_style": routing,
                    "time_axis_enabled": bool(getattr(app.canvas, 'time_axis_enabled', True)),
                    "time_axis_interval": float(getattr(app.canvas, 'time_axis_interval', 100.0) or 100.0),
                    "mousewheel_behavior": getattr(app, "_mousewheel_behavior", "zoom-primary"),
                },
                "element_styles": element_styles,
                "hierarchy_categories": list(getattr(app.canvas, 'hierarchy_categories', [])),
                "navigation": {
                    "nudge_small": int(getattr(app, "_nudge_step_small", 2) or 2),
                    "nudge_big": int(getattr(app, "_nudge_step_big", 10) or 10),
                    "pan_small": int(getattr(app, "_pan_step_small", 30) or 30),
                    "pan_big": int(getattr(app, "_pan_step_big", 60) or 60),
                },
                "onboarding": onboarding_state,
                "autosave": autosave_state,
            }
            try:
                self.loaded.onboarding = onboarding_state
            except Exception:
                pass
            try:
                self.loaded.autosave = autosave_state
            except Exception:
                pass
            os.makedirs(os.path.dirname(self.settings_path) or '.', exist_ok=True)
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    # Convenience: Aktualisiere direkt Ollama-Werte in geladener Struktur
    def update_ollama(self, endpoint: str | None = None, model: str | None = None, temperature: float | None = None, num_predict: int | None = None):
        if endpoint is not None:
            self.loaded.ollama_endpoint = endpoint
        if model is not None:
            self.loaded.ollama_model = model
        if temperature is not None:
            try:
                self.loaded.ollama_temperature = max(0.0, min(1.0, float(temperature)))
            except Exception:
                pass
        if num_predict is not None:
            try:
                n = int(num_predict)
                if n > 0:
                    self.loaded.ollama_num_predict = n
            except Exception:
                pass

    # Zugriffsfunktionen für App (optional)
    def get_pref_grid_visible(self) -> Optional[bool]:
        gv = self.loaded.view.get("grid_visible") if isinstance(self.loaded.view, dict) else None
        return gv if isinstance(gv, bool) else None

    def get_pref_snap_to_grid(self) -> Optional[bool]:
        sp = self.loaded.view.get("snap_to_grid") if isinstance(self.loaded.view, dict) else None
        return sp if isinstance(sp, bool) else None

    def get_pref_routing_style(self) -> Optional[str]:
        rs = self.loaded.view.get("routing_style") if isinstance(self.loaded.view, dict) else None
        return rs if isinstance(rs, str) and rs else None

    def get_pref_time_axis_enabled(self) -> Optional[bool]:
        ta = self.loaded.view.get("time_axis_enabled") if isinstance(self.loaded.view, dict) else None
        return ta if isinstance(ta, bool) else None

    def get_pref_time_axis_interval(self) -> Optional[float]:
        try:
            tai = self.loaded.view.get("time_axis_interval") if isinstance(self.loaded.view, dict) else None
            if tai is None:
                return None
            return float(tai)
        except Exception:
            return None

    def get_pref_mousewheel_behavior(self) -> Optional[str]:
        mode = self.loaded.view.get("mousewheel_behavior") if isinstance(self.loaded.view, dict) else None
        if isinstance(mode, str) and mode in {"zoom-primary", "pan-primary"}:
            return mode
        return None

    def get_pref_pan_hint_dismissed(self) -> bool:
        onboarding = self.loaded.onboarding if isinstance(self.loaded.onboarding, dict) else {}
        flag = onboarding.get("pan_hint_dismissed") if isinstance(onboarding, dict) else None
        return bool(flag) if isinstance(flag, bool) else False

    def get_pref_autosave_enabled(self) -> Optional[bool]:
        autosave = self.loaded.autosave if isinstance(self.loaded.autosave, dict) else None
        if isinstance(autosave, dict):
            flag = autosave.get("enabled")
            if isinstance(flag, bool):
                return flag
        return None

    def get_pref_autosave_interval(self) -> Optional[int]:
        autosave = self.loaded.autosave if isinstance(self.loaded.autosave, dict) else None
        if isinstance(autosave, dict):
            try:
                value = int(autosave.get("interval_minutes", 0) or 0)
                if value > 0:
                    return value
            except Exception:
                return None
        return None
