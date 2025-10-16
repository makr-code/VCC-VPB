#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Kompatible JSON-Struktur (vereinfachte Annahmen):
{
    "metadata": { ... },
    "elements": [
        {"element_id": "E001", "element_type": "START_EVENT", "name": "...", "x": 100, "y": 200, ...},
        ...
    ],
    "connections": [
        {"connection_id": "C001", "source_element": "E001", "target_element": "F001", "connection_type": "SEQUENCE", ...},
        ...
    ]
}

Hinweis: Dieses Minimal-Tool ist bewusst unabhängig von den (teilweise fehlenden)
UDS3/Backend-Modulen und konzentriert sich auf die Visualisierung.
"""

from __future__ import annotations

import datetime
import hashlib
import io
import json
import os
import queue
import re
import shutil
import sys
import threading
import time
import traceback
import uuid
from typing import Dict, Iterable, List, Optional, Tuple

import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, simpledialog, ttk

from controller.app_controller import AppController
from merge_manager import MergeManager, MergeResult
from services.ingestion_service import IngestionService
from services.merge_service import MergeService
from services.ollama_service import OllamaService
from services.validation_service import ValidationService
from settings_manager import SettingsManager
from telemetry_manager import TelemetryManager
from vpb.models import VPBConnection, VPBElement
from vpb.styles import CONNECTION_STYLES, ELEMENT_STYLES
from vpb.ui import (
    CanvasController,
    ChatController,
    PropertiesController,
    TaskController,
    add_code_editor_tab,
    add_xml_viewer_tab,
    add_diagram_tab,
    configure_canvas_interactions,
    create_chat_console,
    create_main_layout,
    create_main_menu,
    create_main_toolbar,
    create_right_sidebar,
    create_status_bar,
    show_shortcut_overlay,
)
from vpb.ui.app_actions import AppActions
from vpb.ui.app_chat_integration import AppChatIntegration
from vpb.ui.app_palette_integration import AppPaletteIntegration
from vpb.ui.app_properties_bridge import AppPropertiesBridge
from vpb.ui.app_shortcuts import AppShortcuts
from vpb.ui.app_task_dispatch import AppTaskDispatch
from vpb.pdf_exporter import render_process_pdf
from vpb.svg_exporter import render_process_svg
from vpb.xml_export import render_vpb_xml
from vpb_config import EXPORT_CONFIG
from vpb_ingestion_wizard import IngestionWizardDialog, IngestionWizardRequest

def _trace_startup(msg: str):
    try:
        with open(os.path.join(os.getcwd(), "startup_trace.log"), "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now().isoformat()} {msg}\n")
    except Exception:
        pass

_trace_startup("module loaded")
try:
    # Optional: lokaler Ollama-Client
    from ollama_client import OllamaClient, OllamaOptions, OllamaJob  # type: ignore
except Exception:
    OllamaClient = None  # type: ignore
    OllamaOptions = None  # type: ignore
    OllamaJob = None  # type: ignore
    
class VPBDesignerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        _trace_startup("Tk root created")
        self.title("VPB Process Designer (Minimal)")
        # Default-Geometrie, wird durch geladene Settings ggf. überschrieben
        self.geometry("1200x800")
        try:
            self.iconbitmap(default=None)
        except Exception:
            pass

        self._current_path: Optional[str] = None
        # Ollama-Settings (einfach)
        self._ollama_endpoint: str = "http://localhost:11434"
        self._ollama_model: str = "llama:latest"
        self._ollama_temperature = 0.2
        self._ollama_num_predict = 600

        # Platzhalter für geladene UI-Settings
        self._pref_geometry: Optional[dict] = None  # {w,h,x,y,state}
        self._pref_sidebar_left: Optional[int] = None
        self._pref_sidebar_right: Optional[int] = None
        self._pref_grid_visible: Optional[bool] = None
        self._pref_snap_to_grid: Optional[bool] = None
        self._pref_routing_style: Optional[str] = None

        # Zusätzliche View-Prefs: Zeitachse
        self._pref_time_axis_enabled: Optional[bool] = None
        self._pref_time_axis_interval: Optional[float] = None
        self._pref_element_styles: dict = {}
        self._pref_hierarchy_categories: list = []
        
        # Weitere App-State Variablen
        self._mousewheel_behavior = "zoom-primary"
        self._pan_hint_dismissed = False
        self._autosave_enabled = True
        self._autosave_interval_minutes = 5
        self._autosave_after_id: Optional[str] = None
        self._merge_snap_enabled = True
        self._merge_update_mode = "fill-empty"
        self._auto_rename_enabled = True
        
        # UI-Control Variablen für Menü
        self._grid_var: Optional[tk.BooleanVar] = None
        self._snap_var: Optional[tk.BooleanVar] = None
        self._time_axis_var: Optional[tk.BooleanVar] = None
        self._route_var: Optional[tk.StringVar] = None
        self._mousewheel_mode_var: Optional[tk.StringVar] = None
        self._merge_snap_var: Optional[tk.BooleanVar] = None
        self._merge_mode_var: Optional[tk.StringVar] = None
        self._auto_rename_var: Optional[tk.BooleanVar] = None
        
        # Settings Manager
        try:
            import os
            settings_path = os.path.join(os.getcwd(), "settings.json")
            self._settings_manager = SettingsManager(settings_path)
        except Exception:
            self._settings_manager = None
        
        # Settings laden
        try:
            self._load_settings()
        except Exception:
            pass
        
        # Status-Handler (vor UI-Erstellung)
        self.status = StatusHolder()
        self._ollama_status = StatusHolder()
        
        # Hauptlayout erstellen
        _trace_startup("creating main layout")
        try:
            layout = create_main_layout(
                self,
                self._pref_sidebar_left,
                self._pref_sidebar_right,
                on_palette_pick=self._on_palette_pick,
                on_palette_reload=self._reload_palettes,
            )
            
            # Layout-Komponenten zuweisen
            self._paned = layout.paned
            self._left_pane = layout.left_pane
            self._mid_pane = layout.mid_pane
            self._right_pane = layout.right_pane
            self._palette = layout.palette
            self._arrange_panel = layout.arrange_panel
            self._mid_split = layout.mid_split
            self._mid_notebook = layout.mid_notebook
            self._chat_console_wrap = layout.chat_console_wrap
            self._sidebar_left_width = layout.sidebar_left_width
            self._sidebar_right_width = layout.sidebar_right_width
        except Exception as e:
            _trace_startup(f"layout creation error: {e}")
            # Fallback: minimales Layout
            self._create_minimal_layout()
        
        # Canvas erstellen
        _trace_startup("creating canvas")
        try:
            from vpb.ui.canvas import VPBCanvas, HierarchyCanvas
            
            # Diagramm-Tab erstellen
            canvas_tab_components = add_diagram_tab(self._mid_notebook)
            self.canvas = canvas_tab_components[1]  # VPBCanvas ist das zweite Element
            self.ruler_canvas = canvas_tab_components[2]  # Erstes RulerCanvas  
            self.hier_canvas = canvas_tab_components[4]  # HierarchyCanvas
            
            # Canvas-Interaktionen konfigurieren (mit Dummy-Scrollbars für jetzt)
            dummy_x_scroll = tk.Scrollbar(self._mid_notebook, orient=tk.HORIZONTAL)
            dummy_y_scroll = tk.Scrollbar(self._mid_notebook, orient=tk.VERTICAL)
            configure_canvas_interactions(self, self.canvas, dummy_x_scroll, dummy_y_scroll)
            
            # Code- und XML-Tabs erstellen  
            add_code_editor_tab(self._mid_notebook)
            add_xml_viewer_tab(self._mid_notebook)
        except Exception as e:
            _trace_startup(f"canvas creation error: {e}")
            # Fallback Canvas
            self._create_minimal_canvas()
        
        # UI-Control Variablen initialisieren (nach Tk-Init)
        try:
            self._grid_var = tk.BooleanVar(master=self, value=True)
            self._snap_var = tk.BooleanVar(master=self, value=False)
            self._time_axis_var = tk.BooleanVar(master=self, value=True)
            self._route_var = tk.StringVar(master=self, value="smart")
            self._mousewheel_mode_var = tk.StringVar(master=self, value=self._mousewheel_behavior)
            self._merge_snap_var = tk.BooleanVar(master=self, value=self._merge_snap_enabled)
            self._merge_mode_var = tk.StringVar(master=self, value=self._merge_update_mode)
            self._auto_rename_var = tk.BooleanVar(master=self, value=self._auto_rename_enabled)
        except Exception as e:
            _trace_startup(f"ui vars creation error: {e}")
        
        # Menü und Toolbar erstellen
        _trace_startup("creating menu and toolbar")
        try:
            create_main_menu(self)
            self.toolbar = create_main_toolbar(self)
        except Exception as e:
            _trace_startup(f"menu/toolbar creation error: {e}")
        
        def _suggest_next_step(self):
            if hasattr(self, "_chat_integration"):
                self._chat_integration.suggest_next_step()
    
    def _create_minimal_layout(self):
        """Fallback: Erstellt ein minimales Layout wenn das Hauptlayout fehlschlägt."""
        try:
            # Hauptframe
            main_frame = tk.Frame(self)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Placeholder für Layout-Variablen
            self._left_pane = tk.Frame(main_frame)
            self._mid_pane = tk.Frame(main_frame)
            self._right_pane = tk.Frame(main_frame)
            self._chat_console_wrap = tk.Frame(main_frame)
            
            # Einfaches Grid-Layout
            self._left_pane.pack(side=tk.LEFT, fill=tk.Y, padx=2)
            self._right_pane.pack(side=tk.RIGHT, fill=tk.Y, padx=2) 
            self._mid_pane.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Notebook für mittleren Bereich
            self._mid_notebook = ttk.Notebook(self._mid_pane)
            self._mid_notebook.pack(fill=tk.BOTH, expand=True)
        except Exception:
            pass
    
    def _create_minimal_canvas(self):
        """Fallback: Erstellt ein minimales Canvas wenn die Haupterstellung fehlschlägt."""
        try:
            canvas_frame = tk.Frame(self._mid_notebook, bg="white")
            self._mid_notebook.add(canvas_frame, text="Diagramm")
            
            # Minimaler Canvas mit notwendigen Dummy-Methoden
            canvas = tk.Canvas(canvas_frame, bg="white", width=800, height=600)
            canvas.pack(fill=tk.BOTH, expand=True)
            
            # Erweitere den Canvas mit den benötigten Methoden
            def dummy_method(*args, **kwargs):
                pass
            
            def to_dict():
                return {"metadata": {}, "elements": [], "connections": []}
            
            canvas.center_time_axis_vertical = dummy_method
            canvas.redraw_all = dummy_method
            canvas.to_dict = to_dict
            canvas.load_from_dict = dummy_method
            canvas.auto_layout = dummy_method
            canvas.fit_to_diagram = dummy_method
            
            self.canvas = canvas
            
            # Dummy-Objekte für Kompatibilität
            self.hier_canvas = None
            self.ruler_canvas = None
        except Exception:
            pass
    
    def _on_palette_pick(self, item: dict):
        """Handler für Palette-Elementauswahl."""
        try:
            if hasattr(self, "_palette_integration"):
                self._palette_integration.on_palette_pick(item)
        except Exception:
            pass
    
    def _reload_palettes(self):
        """Lädt Paletten neu."""
        try:
            if hasattr(self, "_palette_integration"):
                self._palette_integration.reload_palettes()
        except Exception:
            pass
    
    def _apply_code_changes(self, code_text: str):
        """Anwenden von Code-Änderungen."""
        try:
            import json
            data = json.loads(code_text)
            # Validierung und Anwendung hier
            if hasattr(self.canvas, "load_from_dict"):
                self.canvas.load_from_dict(data)
                self.canvas.redraw_all() 
        except Exception as e:
            messagebox.showerror("Code → Diagramm", f"Fehler: {e}")
    
    def _refresh_xml_view(self, silent: bool = False):
        """XML-Ansicht aktualisieren."""
        try:
            # XML-Generierung und Update hier
            pass
        except Exception as e:
            if not silent:
                messagebox.showerror("XML-Export", f"Fehler: {e}")


    # ----- Fehlende UI-Handler Methoden -----
    def new_document(self):
        """Erstellt ein neues Dokument."""
        try:
            if hasattr(self.canvas, "clear"):
                self.canvas.clear()
            self._current_path = None
            self.status.set("Neues Dokument erstellt")
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Erstellen: {e}")
    
    def open_document(self):
        """Öffnet ein vorhandenes Dokument."""
        try:
            from tkinter import filedialog
            file_path = filedialog.askopenfilename(
                title="VPB-Dokument öffnen",
                filetypes=[("VPB JSON", "*.vpb.json"), ("JSON", "*.json"), ("Alle", "*.*")]
            )
            if file_path:
                self._load_file(file_path)
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Öffnen: {e}")
    
    def save_document(self):
        """Speichert das aktuelle Dokument."""
        try:
            if self._current_path:
                self._save_file(self._current_path)
            else:
                self.save_document_as()
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern: {e}")
    
    def save_document_as(self):
        """Speichert das Dokument unter einem neuen Namen."""
        try:
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                title="VPB-Dokument speichern",
                defaultextension=".vpb.json",
                filetypes=[("VPB JSON", "*.vpb.json"), ("JSON", "*.json"), ("Alle", "*.*")]
            )
            if file_path:
                self._save_file(file_path)
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern: {e}")
    
    def _load_file(self, file_path: str):
        """Lädt eine VPB-Datei."""
        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if hasattr(self.canvas, "load_from_dict"):
                self.canvas.load_from_dict(data)
            self._current_path = file_path
            self.status.set(f"Geladen: {file_path}")
        except Exception as e:
            raise e
    
    def _save_file(self, file_path: str):
        """Speichert eine VPB-Datei."""
        try:
            import json
            data = self.canvas.to_dict() if hasattr(self.canvas, "to_dict") else {"metadata": {}, "elements": [], "connections": []}
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._current_path = file_path
            self.status.set(f"Gespeichert: {file_path}")
        except Exception as e:
            raise e
    
    def _add_element_dialog(self):
        """Dialog zum Hinzufügen von Elementen."""
        messagebox.showinfo("Element hinzufügen", "Element-Dialog würde hier erscheinen")
    
    def _align_selected(self, alignment: str):
        """Richtet ausgewählte Elemente aus."""
        messagebox.showinfo("Ausrichten", f"Ausrichten: {alignment}")
    
    def _distribute_selected(self, direction: str):
        """Verteilt ausgewählte Elemente."""
        messagebox.showinfo("Verteilen", f"Verteilen: {direction}")
    
    def _arrange_selection_circular(self):
        """Ordnet Auswahl in einem Kreis an."""
        messagebox.showinfo("Anordnen", "Kreisförmige Anordnung")
    
    def _delete_selected(self):
        """Löscht ausgewählte Elemente.""" 
        messagebox.showinfo("Löschen", "Ausgewählte Elemente löschen")
    
    def _duplicate_selected(self):
        """Dupliziert ausgewählte Elemente."""
        messagebox.showinfo("Duplizieren", "Ausgewählte Elemente duplizieren")
    
    def _toggle_snap(self):
        """Togglet Snap-to-Grid."""
        messagebox.showinfo("Snap", "Snap-to-Grid umgeschaltet")
    
    def _toggle_link_mode(self):
        """Togglet Link-Modus."""
        messagebox.showinfo("Link", "Link-Modus umgeschaltet")
    
    def _undo(self):
        """Rückgängig."""
        messagebox.showinfo("Undo", "Rückgängig")
    
    def _redo(self):
        """Wiederholen."""
        messagebox.showinfo("Redo", "Wiederholen")
    
    def _reset_view(self):
        """Setzt die Ansicht zurück."""
        messagebox.showinfo("View", "Ansicht zurücksetzen")
    
    def _fit_to_diagram(self):
        """Passt die Ansicht an das Diagramm an."""
        if hasattr(self.canvas, "fit_to_diagram"):
            self.canvas.fit_to_diagram()
    
    def _zoom_selection(self):
        """Zoomt auf die Auswahl."""
        messagebox.showinfo("Zoom", "Zoom auf Auswahl")
        
    def _center_selection(self):
        """Zentriert die Auswahl."""
        messagebox.showinfo("Center", "Auswahl zentrieren")
    
    def _toggle_grid(self):
        """Togglet das Grid."""
        messagebox.showinfo("Grid", "Grid umgeschaltet")
    
    def _toggle_time_axis(self):
        """Togglet die Zeitachse."""
        messagebox.showinfo("Time Axis", "Zeitachse umgeschaltet")
    
    def _set_time_interval_dialog(self):
        """Dialog für Zeitintervall."""
        messagebox.showinfo("Time", "Zeitintervall-Dialog")
    
    def _open_hierarchy_manager(self):
        """Öffnet Hierarchie-Manager."""
        messagebox.showinfo("Hierarchie", "Hierarchie-Manager")
    
    def _apply_routing_style(self):
        """Wendet Routing-Stil an."""
        pass
    
    def _validate_process_dialog(self):
        """Prozess-Validierung."""
        messagebox.showinfo("Validierung", "Prozess-Validierung")
    
    def _edit_element_styles(self):
        """Bereits implementiert - siehe oben."""
        pass
    
    def _configure_navigation_dialog(self):
        """Navigation konfigurieren."""
        messagebox.showinfo("Navigation", "Navigation-Dialog")
    
    def _configure_autosave_dialog(self):
        """Autosave konfigurieren."""
        messagebox.showinfo("Autosave", "Autosave-Dialog")
    
    def _configure_ollama(self):
        """Ollama konfigurieren."""
        messagebox.showinfo("Ollama", "Ollama-Konfiguration")
    
    def _ollama_health(self):
        """Ollama Health-Check."""
        messagebox.showinfo("Ollama", "Health-Check")
    
    def _quick_switch_model(self):
        """Modell wechseln."""
        messagebox.showinfo("Ollama", "Modell wechseln")
    
    def _text_to_diagram(self):
        """Text zu Diagramm."""
        messagebox.showinfo("AI", "Text → Diagramm")
    
    def _diagnose_fix(self):
        """Diagnose/Fix."""
        messagebox.showinfo("AI", "Diagnose/Fix")
    
    def _export_png(self):
        """PNG Export."""
        messagebox.showinfo("Export", "PNG Export")
    
    def _export_pdf(self):
        """PDF Export."""
        messagebox.showinfo("Export", "PDF Export")
    
    def _export_svg(self):
        """SVG Export."""
        messagebox.showinfo("Export", "SVG Export")
    
    def _export_ps(self):
        """PostScript Export."""
        messagebox.showinfo("Export", "PostScript Export")
    
    def _edit_metadata(self):
        """Metadaten bearbeiten."""
        messagebox.showinfo("Metadaten", "Metadaten bearbeiten")
    
    def _open_ingestion_wizard(self):
        """Öffnet den AI-Ingestion Wizard.""" 
        messagebox.showinfo("AI Wizard", "AI-Ingestion Wizard")
    
    def _add_connection_dialog(self):
        """Dialog zum Hinzufügen von Verbindungen."""
        messagebox.showinfo("Verbindung", "Verbindung hinzufügen")
    
    def _on_mousewheel_mode_change(self):
        """Handler für Mausrad-Modus-Änderung."""
        try:
            if hasattr(self, "_mousewheel_mode_var"):
                self._mousewheel_behavior = self._mousewheel_mode_var.get()
        except Exception:
            pass
    
    def _toggle_merge_snap(self):
        """Togglet Merge-Snap."""
        try:
            if hasattr(self, "_merge_snap_var"):
                self._merge_snap_enabled = self._merge_snap_var.get()
        except Exception:
            pass
    
    def _set_merge_mode(self):
        """Setzt Merge-Modus."""
        try:
            if hasattr(self, "_merge_mode_var"):
                self._merge_update_mode = self._merge_mode_var.get()
        except Exception:
            pass
    
    def _toggle_auto_rename(self):
        """Togglet Auto-Rename."""
        try:
            if hasattr(self, "_auto_rename_var"):
                self._auto_rename_enabled = self._auto_rename_var.get()
        except Exception:
            pass
    
    def _on_close(self):
        """Schließt die Anwendung."""
        try:
            self.quit()
        except Exception:
            pass


class StatusHolder:
    """Einfacher Status-Container."""
    def __init__(self):
        self._value = ""
    
    def set(self, value: str):
        self._value = str(value)
    
    def get(self) -> str:
        return self._value

        # Initial Code-Ansicht einmal befüllen
        try:
            self._refresh_code_view()
            self._refresh_xml_view(silent=True)
        except Exception:
            pass

        # Geladene View-Einstellungen anwenden (Grid, Snap, Routing)
        try:
            if self._pref_grid_visible is not None:
                self._grid_var.set(bool(self._pref_grid_visible))
                self._toggle_grid()
        except Exception:
            pass
        try:
            if self._pref_snap_to_grid is not None:
                self._snap_var.set(bool(self._pref_snap_to_grid))
                self._toggle_snap()
        except Exception:
            pass
        try:
            if isinstance(self._pref_routing_style, str) and self._pref_routing_style:
                self._route_var.set(self._pref_routing_style)
                self._apply_routing_style()
        except Exception:
            pass
        # Zeitachse: geladene Settings anwenden
        try:
            if self._pref_time_axis_enabled is not None:
                self._time_axis_var.set(bool(self._pref_time_axis_enabled))
                self._toggle_time_axis()
        except Exception:
            pass
        try:
            if isinstance(self._pref_time_axis_interval, (int, float)) and float(self._pref_time_axis_interval) > 0:
                self.canvas.time_axis_interval = float(self._pref_time_axis_interval)
                self.canvas.redraw_all()
        except Exception:
            pass
        # Hierarchie-Kategorien aus Settings anwenden
        try:
            if isinstance(self._pref_hierarchy_categories, list):
                self.canvas.hierarchy_categories = self._pref_hierarchy_categories
                # Hierarchie sofort neu zeichnen
                try:
                    self.hier_canvas.redraw()
                except Exception:
                    pass
        except Exception:
            pass

        # Rechte Seitenleiste mit Tabs (Eigenschaften) im right_pane
        self._properties_controller = PropertiesController(self)

        self._minimap_notebook, self._right_notebook, self.props, self.minimap = create_right_sidebar(
            self._right_pane,
            on_apply=self._apply_properties,
            resolve_member_label=self._properties_controller.resolve_member_label,
            on_member_select=self._properties_controller.select_member,
            on_group_add=self._properties_controller.add_selection_to_group,
            on_group_remove=self._properties_controller.remove_selection_from_group,
        )
        try:
            self.minimap.attach(self.canvas)
        except Exception:
            pass
        _trace_startup("right notebook created")

        # UI-Queue für thread-sichere UI-Updates
        self._ui_queue = queue.Queue()
        def _drain_ui_queue():
            try:
                for _ in range(25):
                    try:
                        cb = self._ui_queue.get_nowait()
                    except Exception:
                        break
                    try:
                        cb()
                    except Exception:
                        traceback.print_exc()
            finally:
                self.after(50, _drain_ui_queue)
        self.after(50, _drain_ui_queue)
        self.post_ui = lambda cb: self._ui_queue.put(cb)

        # Eigenschaften-Tab
        _trace_startup("properties tab added")

        # Chat-Konsole unterhalb des Canvas
        self.chat_controller = ChatController(self)
        self.canvas_controller = CanvasController(self)
        self._configure_arrangement_panel()
        self.task_controller = TaskController(self)
        self._actions = AppActions(self)
        self._shortcuts = AppShortcuts(self)
        self._chat_integration = AppChatIntegration(self)
        self._task_dispatch = AppTaskDispatch(self)
        self._palette_integration = AppPaletteIntegration(self, category_dialog_cls=HierarchyCategoryDialog)
        self._pending_ingestion_request: Optional[IngestionWizardRequest] = None
        self._last_ingestion_dir: Optional[str] = None
        self._latest_ingestion_diff: Optional[dict] = None
        self._latest_ingestion_result: Optional[dict] = None
        self._latest_ingestion_warnings: list[str] = []
        (
            self._chat_container,
            self.chat,
            self.tasks,
        ) = create_chat_console(
            self,
            self._chat_console_wrap,
            on_send=self.chat_controller.handle_send,
            on_stop=self.chat_controller.handle_stop,
            on_attach=self.chat_controller.handle_attach,
        )
        self.chat_controller.bind_ui(self.chat, self.tasks)
        self.task_controller.bind_ui(self.tasks)
        _trace_startup("chat console created")
        self.after(240, lambda: self._ensure_chat_visible())

        # Services & Controller
        self._telemetry_manager = TelemetryManager()
        self._validation_service = ValidationService()
        self._ollama_service = OllamaService()
        self._ingestion_service = IngestionService()
        try:
            self._merge_service = MergeService(telemetry=self._telemetry_manager)
        except Exception:
            self._merge_service = None
        try:
            self._app_controller = AppController(telemetry=self._telemetry_manager)
            self._app_controller.register(
                "validate_process",
                lambda payload, context=None: self._validation_service.validate(payload.get("data") or {}, context=context),
            )
            self._app_controller.register(
                "ollama_chat_stream",
                lambda payload, context=None: self._ollama_service.chat_stream(payload, context=context),
            )
            self._app_controller.register(
                "ai_ingestion",
                lambda payload, context=None: self._ingestion_service.run(payload, context=context),
            )
            if self._merge_service:
                self._app_controller.register("merge_full", lambda payload, context=None: self._merge_service.merge_full(payload, context=context))
                self._app_controller.register("patch_add_only", lambda payload, context=None: self._merge_service.patch_add_only(payload, context=context))

            dispatch = getattr(self, "_task_dispatch", None)
            if dispatch is not None:
                dispatch.start()
        except Exception:
            self._app_controller = None

        # Statusbar: links allgemeiner Status, rechts Ollama-Status
        self.status_bar = create_status_bar(self, self.status, self._ollama_status)

        # Shortcuts
        if hasattr(self, "_shortcuts"):
            self._shortcuts.register()
        _trace_startup("shortcuts bound")

        # Paletten laden
        try:
            self._reload_palettes()
            _trace_startup("palettes loaded")
        except Exception as e:
            _trace_startup(f"palette load error: {e}")

        # Wenn Datei als Argument übergeben wurde, laden
        if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
            self._load_file(sys.argv[1])

        # Aufräum-Handler: Chatverlauf beim Schließen sichern
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        _trace_startup("protocols bound")

        # Initialen Ollama-Status ermitteln
        try:
            self._refresh_ollama_status(async_call=True)
            _trace_startup("ollama status refresh started")
        except Exception as e:
            _trace_startup(f"ollama status error: {e}")

        # Geladene Fenstergeometrie/Window-State zuletzt anwenden (nachdem Widgets existieren)
        try:
            if isinstance(self._pref_geometry, dict):
                g = self._pref_geometry
                w = int(g.get("width", 0) or 0)
                h = int(g.get("height", 0) or 0)
                x = g.get("x")
                y = g.get("y")
                if w > 0 and h > 0:
                    if isinstance(x, int) and isinstance(y, int):
                        self.geometry(f"{w}x{h}+{x}+{y}")
                    else:
                        self.geometry(f"{w}x{h}")
                state = str(g.get("state", "")).lower()
                if state in ("zoomed", "maximized"):
                    try:
                        self.state("zoomed")
                    except Exception:
                        pass
        except Exception as e:
            _trace_startup(f"geometry/state apply error: {e}")

        try:
            self._update_autosave_target()
            self._schedule_autosave()
        except Exception:
            pass
        try:
            self.after(1200, self._check_autosave_recovery)
        except Exception:
            pass
        try:
            self.after(1600, self._maybe_show_pan_onboarding_hint)
        except Exception:
            pass
        _trace_startup("__init__ finished")

    # ----- GROUP Aktionen (App-Wrapper) -----
    def _group_from_selection(self):
        if hasattr(self, "canvas_controller"):
            self.canvas_controller.group_from_selection()

    def _ungroup_selected(self):
        if hasattr(self, "canvas_controller"):
            self.canvas_controller.ungroup_selected()

    def _apply_diagnose_patch(self, diag: dict):
        if hasattr(self, "_chat_integration"):
            self._chat_integration.apply_diagnose_patch(diag)

    def _open_ingestion_wizard(self) -> None:
        initial_dir = self._last_ingestion_dir
        if not initial_dir and self._current_path:
            try:
                initial_dir = os.path.dirname(self._current_path)
            except Exception:
                initial_dir = None
        try:
            dlg = IngestionWizardDialog(
                self,
                initial_dir=initial_dir,
                on_submit=self._handle_ingestion_wizard_submit,
            )
            dlg.show()
        except Exception as exc:
            messagebox.showerror("AI-Ingestion Wizard", f"Fehler beim Öffnen: {exc}")

    def _handle_ingestion_wizard_submit(self, request: IngestionWizardRequest) -> None:
        if request.sources:
            try:
                last_dir = os.path.dirname(request.sources[-1])
                if last_dir:
                    self._last_ingestion_dir = last_dir
            except Exception:
                pass
        elif self._current_path:
            try:
                self._last_ingestion_dir = os.path.dirname(self._current_path)
            except Exception:
                pass

        self._pending_ingestion_request = request
        self._latest_ingestion_diff = None

        summary: list[str] = []
        if request.sources:
            summary.append("Quellen:")
            for path in request.sources:
                summary.append(f"- {path}")
        else:
            summary.append("Quellen: (keine Dateien)")

        if request.inline_text:
            summary.append("Freitext-Vorschau:")
            preview_lines = request.inline_text.splitlines()
            for line in preview_lines[:5]:
                summary.append(f"  {line}")
            if len(preview_lines) > 5:
                summary.append("  …")
        else:
            summary.append("Freitext: (leer)")

        if request.prompt_context:
            summary.append(f"Prompt-Kontext: {request.prompt_context}")
        else:
            summary.append("Prompt-Kontext: (leer)")

        try:
            self.chat_controller.append_block("AI-Ingestion Wizard", summary)
        except Exception:
            pass

        if hasattr(self, "chat"):
            try:
                self.chat.set_progress(None)
                self.chat.clear_dynamic_actions()
                self.chat.add_dynamic_button("AI-Ingestion starten", self._start_ingestion_from_pending)
                self.chat.add_dynamic_button("Quellen bearbeiten…", self._open_ingestion_wizard)
            except Exception:
                pass
            try:
                self._ensure_chat_visible()
            except Exception:
                pass

        self.status.set("AI-Ingestion: Anfrage erfasst (Verarbeitung folgt).")
        try:
            messagebox.showinfo(
                "AI-Ingestion Wizard",
                "Die Ingestion-Anfrage wurde gespeichert. Die AI-Verarbeitung folgt in einem späteren Schritt.",
            )
        except Exception:
            pass

    # ----- Mittel-Notebook: Diagramm/Code Sync -----
    def _start_ingestion_from_pending(self):
        request = getattr(self, "_pending_ingestion_request", None)
        controller = getattr(self, "_app_controller", None)
        if request is None:
            messagebox.showinfo("AI-Ingestion", "Keine gespeicherte Ingestion-Anfrage vorhanden.")
            return
        if controller is None:
            messagebox.showerror("AI-Ingestion", "Hintergrund-Controller nicht verfügbar.")
            return
        if self.task_controller.has_pending("ai_ingestion"):
            self.status.set("AI-Ingestion läuft bereits – bitte warten")
            return

        try:
            current_diagram = self.canvas.to_dict()
        except Exception as exc:
            messagebox.showerror("AI-Ingestion", f"Diagramm konnte nicht gelesen werden: {exc}")
            return

        request_dict = {
            "sources": list(getattr(request, "sources", [])),
            "inline_text": getattr(request, "inline_text", ""),
            "prompt_context": getattr(request, "prompt_context", ""),
            "options": dict(getattr(request, "options", {}) or {}),
        }
        if "include_prompt" not in request_dict["options"]:
            request_dict["options"]["include_prompt"] = True
        if "include_raw" not in request_dict["options"]:
            request_dict["options"]["include_raw"] = False
        payload = {
            "request": request_dict,
            "element_types": list(ELEMENT_STYLES.keys()),
            "connection_types": list(CONNECTION_STYLES.keys()),
            "current_diagram": current_diagram,
            "settings": {
                "endpoint": self._ollama_endpoint,
                "model": self._ollama_model,
                "temperature": self._ollama_temperature,
                "num_predict": self._ollama_num_predict,
            },
        }

        try:
            task_id = controller.submit("ai_ingestion", payload)
        except Exception as exc:
            messagebox.showerror("AI-Ingestion", f"Task konnte nicht gestartet werden: {exc}")
            return

        self.task_controller.register_task_start("ai_ingestion", task_id)
        self._latest_ingestion_diff = None

        if hasattr(self, "chat"):
            try:
                self.chat.set_progress("AI-Ingestion gestartet …", fraction=0.0)
                self.chat.clear_dynamic_actions()
                self.chat.add_dynamic_button("Ingestion abbrechen", self._cancel_ingestion_task)
            except Exception:
                pass
            try:
                self._ensure_chat_visible()
            except Exception:
                pass

        self.status.set("AI-Ingestion läuft…")

    def _cancel_ingestion_task(self):
        controller = getattr(self, "_app_controller", None)
        task_id = self.task_controller.pending_id("ai_ingestion")
        if controller is None or not task_id:
            self.status.set("AI-Ingestion: Kein laufender Task")
            return
        try:
            cancelled = controller.cancel(task_id)
        except Exception as exc:
            messagebox.showerror("AI-Ingestion", f"Abbruch fehlgeschlagen: {exc}")
            return
        if not cancelled:
            self.status.set("AI-Ingestion: Kein laufender Task")
            return
        if hasattr(self, "chat"):
            try:
                self.chat.set_progress("Abbruch wird angefordert …")
            except Exception:
                pass
        self.status.set("AI-Ingestion: Abbruch angefordert")

    def _review_ingestion_diff(self):
        diff = getattr(self, "_latest_ingestion_diff", None)
        if not isinstance(diff, dict) or not (diff.get("elements") or diff.get("connections")):
            messagebox.showinfo("AI-Ingestion", "Kein Diff zur Prüfung vorhanden.")
            return
        try:
            current = self.canvas.to_dict()
        except Exception as exc:
            messagebox.showerror("AI-Ingestion", f"Diagramm konnte nicht gelesen werden: {exc}")
            return
        try:
            element_types = list(ELEMENT_STYLES.keys())
            connection_types = list(CONNECTION_STYLES.keys())
        except Exception:
            element_types = []
            connection_types = []
        self._review_and_apply_diff(current, diff, element_types, connection_types)

    def _show_ingestion_details(self):
        result = getattr(self, "_latest_ingestion_result", None)
        if not isinstance(result, dict):
            messagebox.showinfo("AI-Ingestion", "Keine Details verfügbar – bitte zunächst eine Ingestion ausführen.")
            return

        diff = result.get("diff") if isinstance(result.get("diff"), dict) else {}
        warnings = result.get("warnings") if isinstance(result.get("warnings"), list) else []
        issues = result.get("issues") if isinstance(result.get("issues"), list) else []
        guardrail_issues = result.get("guardrail_issues") if isinstance(result.get("guardrail_issues"), list) else []
        guardrail_summary = result.get("guardrail_summary") if isinstance(result.get("guardrail_summary"), dict) else {}
        prompt_meta = result.get("prompt_meta") if isinstance(result.get("prompt_meta"), dict) else {}
        source_preview = result.get("source_preview") if isinstance(result.get("source_preview"), list) else []
        prompt_text = result.get("prompt") if isinstance(result.get("prompt"), str) else None
        raw_output = result.get("raw_output") if isinstance(result.get("raw_output"), str) else None
        sources_prompt = result.get("sources_prompt") if isinstance(result.get("sources_prompt"), str) else None

        try:
            W = tk.Toplevel(self)
        except Exception:
            return
        W.title("AI-Ingestion Details")
        W.geometry("780x560")

        body = tk.Frame(W)
        body.pack(fill=tk.BOTH, expand=True)
        txt = tk.Text(body, wrap="word", font=("Consolas", 10))
        ysb = tk.Scrollbar(body, orient=tk.VERTICAL, command=txt.yview)
        txt.configure(yscrollcommand=ysb.set)
        txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ysb.pack(side=tk.RIGHT, fill=tk.Y)

        def _write_section(header: str, content: str):
            txt.insert(tk.END, header + "\n", ("header",))
            txt.insert(tk.END, content.strip() + "\n\n")

        txt.tag_configure("header", font=("Segoe UI", 10, "bold"))

        elem_count = len(diff.get("elements", []) if isinstance(diff, dict) else [])
        conn_count = len(diff.get("connections", []) if isinstance(diff, dict) else [])
        summary_lines = [
            f"Neue Elemente: {elem_count}",
            f"Neue Verbindungen: {conn_count}",
            f"Warnungen: {len(warnings)}",
            f"Validierungs-Hinweise: {len(issues)}",
            f"Guardrail-Meldungen: {len(guardrail_issues)}",
        ]
        attempts = result.get("attempts")
        if attempts not in (None, ""):
            summary_lines.append(f"Versuche: {attempts}")
        _write_section("Zusammenfassung", "\n".join(summary_lines))

        if warnings:
            _write_section("Warnungen", "\n".join(str(w) for w in warnings))
        else:
            _write_section("Warnungen", "(keine)")

        if issues:
            try:
                issue_lines = []
                for it in issues:
                    if not isinstance(it, dict):
                        issue_lines.append(str(it))
                        continue
                    sev = it.get("severity", "info")
                    code = it.get("code", "issue")
                    msg = it.get("message", "")
                    issue_lines.append(f"[{sev.upper()}] {code}: {msg}")
                _write_section("Validierungs-Hinweise", "\n".join(issue_lines))
            except Exception:
                _write_section("Validierungs-Hinweise", str(issues))
        else:
            _write_section("Validierungs-Hinweise", "(keine)")

        if guardrail_issues:
            try:
                guard_lines = []
                for it in guardrail_issues:
                    if isinstance(it, dict):
                        code = it.get("code", "guard")
                        msg = it.get("message", "")
                        severity = it.get("severity", "info")
                        scope = it.get("scope")
                        prefix = f"[{severity.upper()}] {code}"
                        if scope:
                            prefix = f"{prefix} ({scope})"
                        guard_lines.append(f"{prefix}: {msg}")
                    else:
                        guard_lines.append(str(it))
                if guardrail_summary:
                    try:
                        summary_bits = []
                        if isinstance(guardrail_summary.get("error"), int):
                            summary_bits.append(f"Fehler: {guardrail_summary['error']}")
                        if isinstance(guardrail_summary.get("warning"), int):
                            summary_bits.append(f"Warnungen: {guardrail_summary['warning']}")
                        if isinstance(guardrail_summary.get("info"), int):
                            summary_bits.append(f"Infos: {guardrail_summary['info']}")
                        if summary_bits:
                            guard_lines.insert(0, " | ".join(summary_bits))
                    except Exception:
                        pass
                _write_section("Guardrail-Ergebnisse", "\n".join(guard_lines))
            except Exception:
                _write_section("Guardrail-Ergebnisse", str(guardrail_issues))
        else:
            _write_section("Guardrail-Ergebnisse", "(keine)")

        if source_preview:
            preview_lines = []
            for src in source_preview:
                if not isinstance(src, dict):
                    preview_lines.append(str(src))
                    continue
                label = src.get("path") or src.get("name") or src.get("type") or "Quelle"
                meta_bits: List[str] = []
                if src.get("type"):
                    meta_bits.append(str(src.get("type")))
                if src.get("characters"):
                    meta_bits.append(f"{src.get('characters')} Zeichen")
                if src.get("rows") and src.get("columns"):
                    meta_bits.append(f"{src.get('rows')}×{src.get('columns')} Zellen")
                if src.get("truncated"):
                    meta_bits.append("gekürzt")
                preview_lines.append(label + (" (" + ", ".join(meta_bits) + ")" if meta_bits else ""))
            _write_section("Quellen", "\n".join(preview_lines))
        else:
            _write_section("Quellen", "(keine Angaben)")

        if prompt_meta:
            try:
                txt.insert(tk.END, "Prompt-Metadaten\n", ("header",))
                txt.insert(tk.END, json.dumps(prompt_meta, ensure_ascii=False, indent=2) + "\n\n")
            except Exception:
                _write_section("Prompt-Metadaten", str(prompt_meta))
        else:
            _write_section("Prompt-Metadaten", "(keine)")

        if sources_prompt:
            _write_section("Quellen Prompt", sources_prompt)

        if prompt_text:
            _write_section("LLM Prompt", prompt_text)

        if raw_output:
            _write_section("Modell-Rohantwort", raw_output)

        btns = tk.Frame(W)
        btns.pack(fill=tk.X, pady=(0, 8))
        tk.Button(btns, text="Schließen", command=W.destroy).pack(side=tk.RIGHT, padx=8)

        txt.configure(state="disabled")
        W.grab_set()
        W.transient(self)

    def _on_mousewheel_mode_change(self):
        try:
            mode = str(self._mousewheel_mode_var.get())
        except Exception:
            mode = self._mousewheel_behavior
        self._set_mousewheel_behavior(mode)
        try:
            if mode == "pan-primary":
                self.status.set("Mausrad: Pannen (Strg=Zoom)")
            else:
                self.status.set("Mausrad: Zoomen (Strg=Pan)")
        except Exception:
            pass
        self._save_settings()


    def _maybe_show_pan_onboarding_hint(self):
        try:
            if getattr(self, "_pan_hint_dismissed", False):
                return
            if getattr(self, "_pan_hint_seen_session", False):
                return
            existing = getattr(self, "_pan_hint_window", None)
            if existing is not None and existing.winfo_exists():
                try:
                    existing.deiconify()
                    existing.lift()
                except Exception:
                    pass
                return

            popup = tk.Toplevel(self)
            popup.title("Navigationstipp")
            popup.transient(self)
            popup.resizable(False, False)
            popup.configure(background="#202428")
            try:
                popup.attributes("-topmost", True)
            except Exception:
                pass
            try:
                popup.attributes("-alpha", 0.96)
            except Exception:
                pass

            width, height = 380, 220
            try:
                self.update_idletasks()
            except Exception:
                pass
            try:
                root_x = int(self.winfo_rootx())
                root_y = int(self.winfo_rooty())
                popup.geometry(f"{width}x{height}+{root_x + 80}+{root_y + 120}")
            except Exception:
                popup.geometry(f"{width}x{height}")

            frame = ttk.Frame(popup, padding=20)
            frame.pack(fill=tk.BOTH, expand=True)

            ttk.Label(frame, text="Tipp: Pannen ohne mittlere Maustaste", font=("Segoe UI", 13, "bold")).pack(anchor="w")
            ttk.Label(
                frame,
                text=(
                    "Halte die Leertaste gedrückt und ziehe mit der linken Maustaste, "
                    "um dich im Diagramm zu bewegen."
                ),
                font=("Segoe UI", 11),
                wraplength=width - 40,
                justify="left",
            ).pack(anchor="w", pady=(8, 4))
            ttk.Label(
                frame,
                text="Alternativ: Alt+Linksklick zieht vertikal, Shift/Alt+Mausrad schiebt horizontal/vertikal.",
                font=("Segoe UI", 10),
                wraplength=width - 40,
                justify="left",
            ).pack(anchor="w")

            ttk.Separator(frame).pack(fill=tk.X, pady=(14, 10))

            permanent_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(frame, text="Diesen Hinweis nicht mehr anzeigen", variable=permanent_var).pack(anchor="w")

            btn_frame = ttk.Frame(frame)
            btn_frame.pack(fill=tk.X, pady=(12, 0))

            def _open_shortcuts():
                try:
                    show_shortcut_overlay(self)
                except Exception:
                    pass

            ttk.Button(btn_frame, text="Shortcut-Übersicht öffnen", command=_open_shortcuts).pack(side=tk.LEFT)

            def _confirm():
                self._dismiss_pan_hint(bool(permanent_var.get()))

            ttk.Button(btn_frame, text="Verstanden", command=_confirm).pack(side=tk.RIGHT)

            def _confirm_event(_event=None):
                _confirm()
                return "break"

            def _cancel_event(_event=None):
                self._dismiss_pan_hint(False)
                return "break"

            popup.bind("<Return>", _confirm_event)
            popup.bind("<Escape>", _cancel_event)
            popup.protocol("WM_DELETE_WINDOW", lambda: self._dismiss_pan_hint(bool(permanent_var.get())))

            self._pan_hint_window = popup
            self._pan_hint_seen_session = True
        except Exception:
            pass

    def _dismiss_pan_hint(self, permanent: bool = False):
        try:
            window = getattr(self, "_pan_hint_window", None)
            if window is not None and window.winfo_exists():
                try:
                    window.destroy()
                except Exception:
                    pass
        except Exception:
            pass
        self._pan_hint_window = None
        self._pan_hint_seen_session = True
        if permanent and not getattr(self, "_pan_hint_dismissed", False):
            self._pan_hint_dismissed = True
            try:
                onboarding = getattr(self._settings_manager.loaded, "onboarding", {})
                if not isinstance(onboarding, dict):
                    onboarding = {}
                onboarding["pan_hint_dismissed"] = True
                self._settings_manager.loaded.onboarding = onboarding
            except Exception:
                pass
            try:
                self._save_settings()
            except Exception:
                pass
        return "break"

    def _on_mid_tab_changed(self, event=None):
        try:
            # Wenn in den Code-Tab gewechselt wird, aktualisieren
            nb = self._mid_notebook
            sel = nb.select()
            current_title = nb.tab(sel, 'text') if sel else ''
            if current_title == 'Code':
                self._refresh_code_view()
            elif current_title == 'XML':
                self._refresh_xml_view()
        except Exception as e:
            try:
                self.status.set(f'Tab-Fehler: {e}')
            except Exception:
                pass

    def _refresh_code_view(self):
        try:
            data = self.canvas.to_dict()
            txt = json.dumps(data, ensure_ascii=False, indent=2)
            self._code_text.configure(state='normal')
            self._code_text.delete('1.0', tk.END)
            self._code_text.insert('1.0', txt)
            self._code_text.configure(state='normal')
            self._clear_code_error_highlight()
            self.status.set('Diagramm → Code aktualisiert')
            self._refresh_xml_view(silent=True)
        except Exception as e:
            self.status.set(f'Code-Ansicht Fehler: {e}')

    def _refresh_xml_view(self, format_code: Optional[str] = None, *, silent: bool = False):
        selected_format = format_code
        if not selected_format:
            try:
                if getattr(self, "_xml_format_var", None):
                    selected_format = self._xml_format_var.get()
            except Exception:
                selected_format = None
        if not selected_format:
            selected_format = EXPORT_CONFIG.default_export_format or "bpmn"
        selected_format = (selected_format or "bpmn").lower().strip()

        # Synchronisiere Auswahl-Variable, falls Refresh mit Override erfolgt.
        try:
            if getattr(self, "_xml_format_var", None) and self._xml_format_var.get() != selected_format:
                self._xml_format_var.set(selected_format)
        except Exception:
            pass

        label_map = getattr(self, "_xml_format_options", [])
        label_lookup = {code: label for code, label in label_map}
        format_label = label_lookup.get(selected_format, selected_format.upper())

        try:
            data = self.canvas.to_dict()
            xml_text = render_vpb_xml(data, format=selected_format, indent=EXPORT_CONFIG.xml_indent)
        except Exception as e:
            xml_text = f"<!-- XML-Ansicht Fehler ({selected_format}): {e} -->\n"
            try:
                if not silent:
                    self.status.set(f'XML-Ansicht Fehler ({selected_format}): {e}')
            except Exception:
                pass
        else:
            if not silent:
                self.status.set(f'Diagramm → XML ({format_label}) aktualisiert')

        try:
            self._xml_text.configure(state='normal')
            self._xml_text.delete('1.0', tk.END)
            self._xml_text.insert('1.0', xml_text)
            self._xml_text.configure(state='normal')
        except Exception:
            pass

    def _apply_code_to_diagram(self):
        try:
            raw = self._code_text.get('1.0', tk.END)
            self._clear_code_error_highlight()
            data = json.loads(raw)
            # einfache Validierung grob
            if not isinstance(data, dict) or 'elements' not in data or 'connections' not in data:
                # Bestmöglich Zeile bestimmen (hier nicht bekannt) → erste Zeile markieren
                self._highlight_code_error(1, 1)
                messagebox.showerror('Code → Diagramm', 'Ungültiges VPB JSON (elements/connections fehlen).')
                return
            # Schema-Validierung, falls verfügbar
            ok, err = self._validate_vpb_data_safe(data)
            if not ok:
                try:
                    # Versuche Zeile aus Fehlermeldung zu extrahieren (falls Zahl vorhanden)
                    import re
                    m = re.search(r"line\s*(\d+)", str(err) or "")
                    if m:
                        self._highlight_code_error(int(m.group(1)), 1)
                except Exception:
                    pass
                messagebox.showerror('Code → Diagramm', f'Schema-Fehler: {err}')
                return
            self.canvas.push_undo()
            self.canvas.load_from_dict(data)
            self.canvas.redraw_all()
            self.status.set('Code → Diagramm übernommen')
            try:
                self._refresh_xml_view(silent=True)
            except Exception:
                pass
            # Bei Wechsel zurück in Diagramm ggf. fitten
            try:
                self._fit_to_diagram()
            except Exception:
                pass
        except json.JSONDecodeError as je:
            try:
                line = getattr(je, 'lineno', 1) or 1
                col = getattr(je, 'colno', 1) or 1
                self._highlight_code_error(int(line), int(col))
            except Exception:
                pass
            messagebox.showerror('Code → Diagramm', f'JSON Fehler: {je}')
        except Exception as e:
            messagebox.showerror('Code → Diagramm', f'Fehler: {e}')

    def _clear_code_error_highlight(self):
        try:
            self._code_text.tag_remove("json_error", "1.0", tk.END)
        except Exception:
            pass

    def _highlight_code_error(self, line: int, col: int):
        try:
            # Markiere von Spalte bis zum Zeilenende; mind. 1 Zeichen
            start = f"{max(1, line)}.{max(0, col-1)}"
            end = f"{max(1, line)}.end"
            self._code_text.tag_add("json_error", start, end)
            self._code_text.see(start)
        except Exception:
            pass

    def _validate_vpb_data_safe(self, data: dict) -> tuple[bool, Optional[str]]:
        """Versucht, via vpb_schema zu validieren; fällt sonst auf OK zurück.
        Rückgabe: (ok, fehlertext|None)
        """
        # Akzeptiere triviale Fälle
        try:
            from vpb_schema import validate_vpb_dict  # type: ignore
        except Exception:
            return True, None
        try:
            elems = list(ELEMENT_STYLES.keys())
            conns = list(CONNECTION_STYLES.keys())
            try:
                res = validate_vpb_dict(data, elems, conns)
            except TypeError:
                # manche Varianten brauchen nur data
                res = validate_vpb_dict(data)
            # bool oder (bool, msg) akzeptieren
            if isinstance(res, tuple) and len(res) >= 1 and isinstance(res[0], bool):
                return bool(res[0]), (str(res[1]) if len(res) > 1 and res[1] is not None else None)
            if isinstance(res, bool):
                return (res, None)
            # unbekanntes Format – als ok behandeln
            return True, None
        except Exception as e:
            # Bei Exceptions: als Fehler zurückgeben
            return False, str(e)

    def _display_validation_result(self, ok: bool, err: Optional[str]):
        if ok:
            messagebox.showinfo("Prozess prüfen", "Keine Schemafehler gefunden.")
            self.status.set("Validierung OK")
        else:
            messagebox.showerror("Prozess prüfen", f"Schema-Fehler: {err or 'Unbekannt'}")
            self.status.set(f"Validierung Fehler: {err or 'Unbekannt'}")

    def _validate_process_dialog(self):
        """Validiert den aktuellen Prozess (Schema) asynchron über den Controller."""
        controller = getattr(self, "_app_controller", None)
        try:
            data = self.canvas.to_dict()
        except Exception as e:
            messagebox.showerror("Prozess prüfen", f"Konnte Diagramm nicht erfassen: {e}")
            return

        if controller is None:
            try:
                ok, err = self._validate_vpb_data_safe(data)
            except Exception as e:
                ok, err = False, f"Validierung-Fehler: {e}"
            self._display_validation_result(ok, err)
            return

        if self.task_controller.has_pending("validate_process"):
            self.status.set("Validierung läuft bereits – bitte warten")
            return

        try:
            task_id = controller.submit("validate_process", {"data": data})
        except Exception as e:
            messagebox.showwarning(
                "Prozess prüfen",
                f"Hintergrund-Validierung nicht möglich ({e}). Führe lokale Prüfung aus.",
            )
            try:
                ok, err = self._validate_vpb_data_safe(data)
            except Exception as ex:
                ok, err = False, f"Validierung-Fehler: {ex}"
            self._display_validation_result(ok, err)
            return

        self.task_controller.register_task_start("validate_process", task_id)
        self.status.set("Validierung läuft…")

    def _toggle_grid(self):
        if hasattr(self, "_actions"):
            self._actions.toggle_grid()

    def _apply_routing_style(self):
        try:
            style = self._route_var.get()
            self.canvas.routing_style = style
            self.canvas.redraw_all()
            self.status.set(f"Routing: {style}")
        except Exception:
            pass

    def _toggle_merge_snap(self):
        """Aktiviert/Deaktiviert Raster-Snap für neu hinzugefügte Elemente im Merge-Pfad."""
        try:
            enabled = bool(self._merge_snap_var.get())
            self._merge_snap_enabled = enabled
            self.status.set("Merge Raster-Snap an" if enabled else "Merge Raster-Snap aus")
        except Exception:
            self._merge_snap_enabled = False

    def _set_merge_mode(self):
        try:
            mode = self._merge_mode_var.get()
            if mode not in ("none", "fill-empty", "overwrite"):
                mode = "none"
            self._merge_update_mode = mode
            self.status.set(f"Merge Modus: {mode}")
        except Exception:
            self._merge_update_mode = "none"

    def _toggle_auto_rename(self):
        """Aktiviert/Deaktiviert das automatische Umbenennen kollidierender IDs.
        Bei deaktiviertem Auto-Rename brechen Merge/Patch bei Konflikten mit Warnung ab."""
        try:
            enabled = bool(self._auto_rename_var.get())
            self._auto_rename_enabled = enabled
            self.status.set("Auto-Rename an" if enabled else "Auto-Rename aus")
        except Exception:
            self._auto_rename_enabled = True

    # ----- Zeitachse: Toggle/Intervall -----
    def _toggle_time_axis(self):
        try:
            enabled = bool(self._time_axis_var.get())
            self.canvas.time_axis_enabled = enabled
            self.canvas.redraw_all()
            self.status.set("Zeitachse sichtbar" if enabled else "Zeitachse verborgen")
        except Exception:
            pass

    def _set_time_interval_dialog(self):
        try:
            cur = float(getattr(self.canvas, 'time_axis_interval', 100.0) or 100.0)
        except Exception:
            cur = 100.0
        val = simpledialog.askstring(
            "Zeitintervall",
            "Intervall in Model-Einheiten (z. B. 100):",
            initialvalue=str(int(cur)),
            parent=self,
        )
        if not val:
            return
        try:
            f = float(val)
            if f <= 0:
                raise ValueError("Intervall muss > 0 sein")
            self.canvas.time_axis_interval = f
            self.canvas.redraw_all()
            self.status.set(f"Zeitintervall gesetzt: {f}")
        except Exception as e:
            messagebox.showerror("Zeitintervall", f"Ungültiger Wert: {e}")

    def _configure_hierarchy_dialog(self):
        """Dialog zum Bearbeiten der Hierarchie-Kategorien als JSON-Liste.
        Format je Eintrag: {"name": str, "y0": float, "y1": float, "color": str}
        """
        import tkinter.scrolledtext as scrolledtext
        T = tk.Toplevel(self)
        T.title("Hierarchie konfigurieren")
        T.geometry("600x500")
        info = tk.Label(T, text="Bearbeite die Kategorien als JSON-Liste. Einträge mit name, y0, y1, color.", anchor='w')
        info.pack(side=tk.TOP, fill=tk.X, padx=8, pady=6)
        txt = scrolledtext.ScrolledText(T, wrap='none', font=("Consolas", 10))
        txt.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0,8))
        # Bestehende Kategorien einfügen (pretty JSON)
        try:
            cur = getattr(self.canvas, 'hierarchy_categories', None) or []
            txt.insert('1.0', json.dumps(cur, ensure_ascii=False, indent=2))
        except Exception:
            txt.insert('1.0', "[]")

        btns = tk.Frame(T)
        btns.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=8)

        def load_demo():
            demo = [
                {"name": "Strategisch", "y0": -1000, "y1": -500, "color": "#f5f5ff"},
                {"name": "Taktisch",   "y0": -500,  "y1": 0,    "color": "#f0fff5"},
                {"name": "Operativ",   "y0": 0,     "y1": 600,  "color": "#fffaf0"},
            ]
            txt.delete('1.0', tk.END)
            txt.insert('1.0', json.dumps(demo, ensure_ascii=False, indent=2))

        def apply_and_close():
            raw = txt.get('1.0', tk.END)
            try:
                data = json.loads(raw)
                if not isinstance(data, list):
                    raise ValueError("JSON ist keine Liste")
                norm = []
                for i, it in enumerate(data):
                    if not isinstance(it, dict):
                        raise ValueError(f"Eintrag {i} ist kein Objekt")
                    name = str(it.get('name', '')).strip()
                    if not name:
                        raise ValueError(f"Eintrag {i}: 'name' fehlt")
                    try:
                        y0 = float(it.get('y0', 0.0))
                        y1 = float(it.get('y1', 0.0))
                    except Exception:
                        raise ValueError(f"Eintrag {i}: y0/y1 müssen Zahlen sein")
                    color = str(it.get('color', '#f2f2f2'))
                    norm.append({"name": name, "y0": y0, "y1": y1, "color": color})
                # Optional sortieren nach y0
                norm.sort(key=lambda e: e.get('y0', 0.0))
                self.canvas.hierarchy_categories = norm
                try:
                    # Sofort neu zeichnen
                    self.hier_canvas.redraw()
                    self.canvas.redraw_all()
                except Exception:
                    pass
                # Persistieren
                try:
                    self._save_settings()
                except Exception:
                    pass
                T.destroy()
                self.status.set("Hierarchie aktualisiert")
            except Exception as e:
                messagebox.showerror("Hierarchie", f"Ungültiges JSON: {e}")

        tk.Button(btns, text="Demo laden", command=load_demo).pack(side=tk.LEFT)
        tk.Button(btns, text="Abbrechen", command=T.destroy).pack(side=tk.RIGHT)
        tk.Button(btns, text="Übernehmen", command=apply_and_close).pack(side=tk.RIGHT, padx=6)

    def _open_hierarchy_manager(self):
        categories = list(getattr(self.canvas, "hierarchy_categories", []) or [])
        dialog = HierarchyManagerDialog(self, categories)
        self.wait_window(dialog)
        result = getattr(dialog, "result", None)
        if result is None:
            return
        selected_index = getattr(dialog, "selected_index", None)
        message = f"{len(result)} Hierarchien gespeichert."
        self._apply_hierarchy_categories(result, select_index=selected_index, push_undo=True, status_message=message)

    def _apply_hierarchy_categories(
        self,
        categories: List[Dict[str, object]],
        *,
        select_index: Optional[int] = None,
        push_undo: bool = True,
        status_message: Optional[str] = None,
    ) -> None:
        if hasattr(self, "_palette_integration"):
            self._palette_integration.apply_hierarchy_categories(
                categories,
                select_index=select_index,
                push_undo=push_undo,
                status_message=status_message,
            )

    def _auto_calculate_hierarchy_ranges(self) -> None:
        """Berechnet die Y-Bereiche der Hierarchiebänder anhand der Elementpositionen und stapelt sie ohne Überlappung."""
        canvas = getattr(self, "canvas", None)
        if canvas is None:
            return
        categories = list(getattr(canvas, "hierarchy_categories", []) or [])
        if not categories:
            try:
                self.status.set("Keine Hierarchien vorhanden.")
            except Exception:
                pass
            return

        elements = list(canvas.elements.values())
        if not elements:
            try:
                self.status.set("Keine Elemente im Diagramm vorhanden.")
            except Exception:
                pass
            return

        try:
            canvas.push_undo()
        except Exception:
            pass

        node_h = int(getattr(canvas, "NODE_H", 60) or 60)
        half_h = max(1, node_h // 2)
        band_padding = max(20, node_h // 2)
        stack_gap = max(10, node_h // 3)
        min_span = max(node_h + 2 * band_padding, node_h * 2)

        updated_cats: List[Dict[str, object]] = []
        current_bottom: Optional[int] = None
        shifted_elements = 0

        for idx, cat in enumerate(categories):
            name = str(cat.get("name", "") or "").strip()
            color = str(cat.get("color", "") or "#f2f2f2").strip() or "#f2f2f2"
            assigned = [el for el in canvas.elements.values() if getattr(el, "hierarchy", None) == name]

            if assigned:
                top_candidates = [int(el.y) - half_h for el in assigned]
                bottom_candidates = [int(el.y) + half_h for el in assigned]
                band_top = min(top_candidates) - band_padding
                band_bottom = max(bottom_candidates) + band_padding
            else:
                band_top = None
                band_bottom = None

            if band_top is None or band_bottom is None:
                existing_top = int(float(cat.get("y0", current_bottom + stack_gap if current_bottom is not None else 0)))
                existing_bottom = int(float(cat.get("y1", existing_top + min_span)))
                band_top = existing_top
                band_bottom = max(existing_bottom, band_top + min_span)
            else:
                span = band_bottom - band_top
                if span < min_span:
                    deficit = min_span - span
                    upper_add = deficit // 2
                    lower_add = deficit - upper_add
                    band_top -= upper_add
                    band_bottom += lower_add

            if current_bottom is not None:
                min_top = current_bottom + stack_gap
                if band_top < min_top:
                    delta = min_top - band_top
                    band_top += delta
                    band_bottom += delta
                    if assigned:
                        for el in assigned:
                            el.y += delta
                        shifted_elements += len(assigned)

            if band_bottom <= band_top:
                band_bottom = band_top + max(min_span, node_h)

            updated_cats.append({
                "name": name,
                "color": color,
                "y0": float(band_top),
                "y1": float(band_bottom),
            })
            current_bottom = band_bottom

        status_msg = "Hierarchie-Bänder automatisch berechnet"
        if shifted_elements:
            status_msg += f" ({shifted_elements} Elemente verschoben)"

        self._apply_hierarchy_categories(
            updated_cats,
            select_index=self._selected_hierarchy_index,
            push_undo=False,
            status_message=status_msg,
        )

    # ----- Dateioperationen -----
    def new_document(self):
        try:
            if hasattr(self, "chat_controller"):
                self.chat_controller.switch_project(None)
        except Exception:
            pass
        self.canvas.clear()
        self._current_path = None
        self.status.set("Neues Dokument")
        self.props.set_element(None)
        try:
            self._bump_autosave_session()
            self._schedule_autosave()
        except Exception:
            pass

    def open_document(self):
        path = filedialog.askopenfilename(
            title="VPB Prozess laden",
            filetypes=[("VPB JSON", "*.json *.vpb.json"), ("Alle Dateien", "*.*")],
            initialdir=os.path.join(os.getcwd(), "processes") if os.path.isdir("processes") else os.getcwd(),
        )
        if not path:
            return
        self._load_file(path)

    def _load_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Tolerant gegenüber Legacy-Strukturen
            if isinstance(data, dict) and "elements" in data and "connections" in data:
                # Basisverzeichnis für SUBPROCESS-Referenzen setzen
                try:
                    self.canvas.base_dir = os.path.dirname(os.path.abspath(path))
                except Exception:
                    self.canvas.base_dir = os.getcwd()
                # Callback zum Öffnen von Referenzen verbinden
                try:
                    self.canvas.set_open_reference_callback(self._load_file)
                except Exception:
                    pass
                self.canvas.load_from_dict(data)
                self._current_path = path
                self.status.set(f"Geladen: {os.path.basename(path)}")
                self.props.set_element(None)
                try:
                    if hasattr(self, "chat_controller"):
                        self.chat_controller.switch_project(path)
                except Exception:
                    pass
                try:
                    self._bump_autosave_session()
                    self._schedule_autosave()
                except Exception:
                    pass
            else:
                messagebox.showerror("Fehler", "Ungültiges VPB JSON-Format")
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte Datei nicht laden:\n{e}")

    def save_document(self):
        if not self._current_path:
            return self.save_document_as()
        try:
            data = self.canvas.to_dict()
            with open(self._current_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.status.set(f"Gespeichert: {os.path.basename(self._current_path)}")
            try:
                self._clear_autosave_snapshot()
                self._update_autosave_target()
                self._schedule_autosave()
            except Exception:
                pass
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte nicht speichern:\n{e}")

    def save_document_as(self):
        path = filedialog.asksaveasfilename(
            title="VPB Prozess speichern",
            defaultextension=".vpb.json",
            filetypes=[("VPB JSON", "*.vpb.json"), ("JSON", "*.json"), ("Alle Dateien", "*.*")],
            initialdir=os.path.join(os.getcwd(), "processes") if os.path.isdir("processes") else os.getcwd(),
        )
        if not path:
            return
        self._current_path = path
        try:
            if hasattr(self, "chat_controller"):
                self.chat_controller.switch_project(path, preserve_current=True)
        except Exception:
            pass
        self.save_document()

    # ----- Einstellungen (optional einfache Persistenz) -----
    def _settings_path(self) -> str:
        # Neuer Standard: settings.json im Projekt-Root
        return os.path.join(os.getcwd(), "settings.json")

    def _load_settings(self):
        """Delegiert an SettingsManager und mapped Werte auf App-Attribute (rückwärtskompatibel)."""
        try:
            L = self._settings_manager.load()
            # Ollama Werte
            self._ollama_endpoint = L.ollama_endpoint
            self._ollama_model = L.ollama_model
            self._ollama_temperature = L.ollama_temperature
            self._ollama_num_predict = L.ollama_num_predict
            # Window prefs
            win = L.window
            if isinstance(win, dict) and win:
                try:
                    self._pref_geometry = {
                        "width": int(win.get("width", 0) or 0),
                        "height": int(win.get("height", 0) or 0),
                        "x": int(win.get("x")) if win.get("x") is not None else None,
                        "y": int(win.get("y")) if win.get("y") is not None else None,
                        "state": str(win.get("state", "")).lower(),
                    }
                except Exception:
                    self._pref_geometry = None
            # Sidebars
            sb = L.sidebars
            try:
                if isinstance(sb, dict) and sb:
                    lw = int(sb.get("left_width", 0) or 0)
                    rw = int(sb.get("right_width", 0) or 0)
                    self._pref_sidebar_left = lw if lw > 0 else None
                    self._pref_sidebar_right = rw if rw > 0 else None
            except Exception:
                pass
            # View
            self._pref_grid_visible = self._settings_manager.get_pref_grid_visible()
            self._pref_snap_to_grid = self._settings_manager.get_pref_snap_to_grid()
            self._pref_routing_style = self._settings_manager.get_pref_routing_style()
            self._pref_time_axis_enabled = self._settings_manager.get_pref_time_axis_enabled()
            self._pref_time_axis_interval = self._settings_manager.get_pref_time_axis_interval()
            # Styles & Hierarchie
            self._pref_element_styles = L.element_styles or {}
            self._pref_hierarchy_categories = L.hierarchy_categories
            nav = getattr(L, "navigation", None)
            if isinstance(nav, dict):
                self._apply_navigation_settings(nav)
            mw_mode = self._settings_manager.get_pref_mousewheel_behavior()
            if mw_mode:
                self._mousewheel_behavior = mw_mode
            self._pan_hint_dismissed = bool(self._settings_manager.get_pref_pan_hint_dismissed())
            pref_autosave = self._settings_manager.get_pref_autosave_enabled()
            if pref_autosave is not None:
                self._autosave_enabled = bool(pref_autosave)
            pref_interval = self._settings_manager.get_pref_autosave_interval()
            if pref_interval is not None:
                try:
                    self._autosave_interval_minutes = max(1, int(pref_interval))
                except Exception:
                    pass
        except Exception:
            pass

    @staticmethod
    def _coerce_positive_int(value: object) -> Optional[int]:
        try:
            if value is None:
                return None
            if isinstance(value, bool):
                return None
            if isinstance(value, str):
                trimmed = value.strip()
                if not trimmed:
                    return None
                value = trimmed
            number = int(float(value))
            if number <= 0:
                return None
            return number
        except Exception:
            return None

    def _apply_navigation_settings(self, data: Dict[str, object]) -> None:
        try:
            mapping = (
                ("nudge_small", "_nudge_step_small"),
                ("nudge_big", "_nudge_step_big"),
                ("pan_small", "_pan_step_small"),
                ("pan_big", "_pan_step_big"),
            )
            for key, attr in mapping:
                value = data.get(key)
                coerced = self._coerce_positive_int(value)
                if coerced is not None:
                    setattr(self, attr, coerced)
            if self._nudge_step_big < self._nudge_step_small:
                self._nudge_step_big = self._nudge_step_small
            if self._pan_step_big < self._pan_step_small:
                self._pan_step_big = self._pan_step_small
            self._sync_canvas_navigation_steps()
            try:
                if hasattr(self, "_settings_manager") and getattr(self._settings_manager, "loaded", None):
                    self._settings_manager.loaded.navigation = {
                        "nudge_small": self._nudge_step_small,
                        "nudge_big": self._nudge_step_big,
                        "pan_small": self._pan_step_small,
                        "pan_big": self._pan_step_big,
                    }
            except Exception:
                pass
        except Exception:
            pass

    def _sync_canvas_navigation_steps(self) -> None:
        try:
            canvas = getattr(self, "canvas", None)
            if canvas is None:
                return
            if hasattr(canvas, "pan_step_small_px"):
                canvas.pan_step_small_px = int(self._pan_step_small)
            else:
                setattr(canvas, "pan_step_small_px", int(self._pan_step_small))
            if hasattr(canvas, "pan_step_big_px"):
                canvas.pan_step_big_px = int(self._pan_step_big)
            else:
                setattr(canvas, "pan_step_big_px", int(self._pan_step_big))
        except Exception:
            pass

    def _set_mousewheel_behavior(self, mode: str) -> None:
        try:
            if mode not in {"zoom-primary", "pan-primary"}:
                mode = "zoom-primary"
            self._mousewheel_behavior = mode
            canvas = getattr(self, "canvas", None)
            if canvas is not None and hasattr(canvas, "set_mousewheel_mode"):
                try:
                    canvas.set_mousewheel_mode(mode)
                except Exception:
                    pass
            if hasattr(self, "_mousewheel_mode_var") and isinstance(self._mousewheel_mode_var, tk.StringVar):
                try:
                    self._mousewheel_mode_var.set(mode)
                except Exception:
                    pass
            if getattr(self, "_settings_manager", None) is not None:
                try:
                    view = getattr(self._settings_manager.loaded, "view", None)
                    if isinstance(view, dict):
                        view["mousewheel_behavior"] = mode
                except Exception:
                    pass
        except Exception:
            pass

    def _save_settings(self):
        try:
            self._settings_manager.save_from_app(self)
        except Exception:
            pass

    # ----- Autosave -----
    def _bump_autosave_session(self) -> None:
        try:
            self._autosave_session_id = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        except Exception:
            self._autosave_session_id = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        self._autosave_last_hash = None
        self._update_autosave_target()

    def _update_autosave_target(self) -> Optional[str]:
        try:
            os.makedirs(self._autosave_dir, exist_ok=True)
        except Exception:
            pass
        try:
            if self._current_path:
                base = os.path.splitext(os.path.basename(self._current_path))[0] or "diagram"
                safe_base = re.sub(r"[^A-Za-z0-9_-]+", "_", base)
                digest = hashlib.sha1(os.path.abspath(self._current_path).encode("utf-8")).hexdigest()[:6]
                if digest:
                    safe_base = f"{safe_base}_{digest}"
            else:
                safe_base = f"untitled_{self._autosave_session_id}"
            if not safe_base:
                safe_base = "untitled"
            path = os.path.join(self._autosave_dir, f"{safe_base}.autosave.vpb.json")
            self._autosave_target_path = path
            return path
        except Exception:
            return None

    def _schedule_autosave(self) -> None:
        try:
            if self._autosave_after_id is not None:
                self.after_cancel(self._autosave_after_id)
        except Exception:
            pass
        finally:
            self._autosave_after_id = None
        if not getattr(self, "_autosave_enabled", True):
            return
        try:
            interval = max(1, int(getattr(self, "_autosave_interval_minutes", 3) or 3)) * 60 * 1000
        except Exception:
            interval = 3 * 60 * 1000
        try:
            self._autosave_after_id = self.after(interval, self._perform_autosave)
        except Exception:
            self._autosave_after_id = None

    def _perform_autosave(self) -> None:
        self._autosave_after_id = None
        if not getattr(self, "_autosave_enabled", True):
            return
        try:
            data = self.canvas.to_dict()
            payload = json.loads(json.dumps(data, ensure_ascii=False)) if isinstance(data, dict) else {}
            now = datetime.datetime.now()
            meta = {
                "timestamp": now.timestamp(),
                "display_name": os.path.basename(self._current_path) if self._current_path else "Unbenannt",
                "source_path": self._current_path,
                "session": self._autosave_session_id,
            }
            if isinstance(payload, dict):
                payload["__autosave_meta"] = meta
            else:
                payload = {"__autosave_meta": meta, "data": data}
            serialized = json.dumps(payload, ensure_ascii=False, indent=2)
            digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
            if digest == self._autosave_last_hash:
                return
            path = self._autosave_target_path or self._update_autosave_target()
            if not path:
                return
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp_path = f"{path}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(serialized)
            os.replace(tmp_path, path)
            self._autosave_last_hash = digest
            self._purge_old_autosaves(limit=20)
        except Exception as e:
            try:
                self.status.set(f"Autosave fehlgeschlagen: {e}")
            except Exception:
                pass
        finally:
            self._schedule_autosave()

    def _clear_autosave_snapshot(self) -> None:
        path = getattr(self, "_autosave_target_path", None)
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
        self._autosave_last_hash = None

    def _purge_old_autosaves(self, limit: int = 20) -> None:
        try:
            if not os.path.isdir(self._autosave_dir):
                return
            entries: List[Tuple[float, str]] = []
            for name in os.listdir(self._autosave_dir):
                if not name.endswith(".autosave.vpb.json"):
                    continue
                path = os.path.join(self._autosave_dir, name)
                try:
                    ts = os.path.getmtime(path)
                except Exception:
                    ts = time.time()
                entries.append((ts, path))
            if len(entries) <= limit:
                return
            entries.sort(key=lambda item: item[0], reverse=True)
            for _, path in entries[limit:]:
                try:
                    os.remove(path)
                except Exception:
                    pass
        except Exception:
            pass

    def _check_autosave_recovery(self) -> None:
        try:
            if not os.path.isdir(self._autosave_dir):
                return
            candidates = []
            for name in os.listdir(self._autosave_dir):
                if not name.endswith(".autosave.vpb.json"):
                    continue
                path = os.path.join(self._autosave_dir, name)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = json.load(f)
                except Exception:
                    continue
                if not isinstance(content, dict):
                    continue
                meta = content.get("__autosave_meta") if isinstance(content.get("__autosave_meta"), dict) else {}
                ts = meta.get("timestamp")
                if not isinstance(ts, (int, float)):
                    try:
                        ts = os.path.getmtime(path)
                    except Exception:
                        ts = time.time()
                candidates.append({
                    "path": path,
                    "meta": meta,
                    "timestamp": ts,
                    "payload": content,
                })
            if not candidates:
                return
            candidates.sort(key=lambda item: item.get("timestamp", 0.0), reverse=True)
            candidate = candidates[0]
            meta = candidate.get("meta", {})
            display_name = meta.get("display_name") or os.path.basename(candidate["path"])
            ts_val = candidate.get("timestamp", time.time())
            ts_fmt = datetime.datetime.fromtimestamp(ts_val).strftime("%d.%m.%Y %H:%M")
            if not messagebox.askyesno("Autosave gefunden", f"Es wurde eine automatische Sicherung von '{display_name}' vom {ts_fmt} gefunden. Möchten Sie sie wiederherstellen?"):
                return
            payload = candidate.get("payload")
            if isinstance(payload, dict):
                payload = dict(payload)
                payload.pop("__autosave_meta", None)
                try:
                    self.canvas.load_from_dict(payload)
                    source_path = meta.get("source_path")
                    self._current_path = source_path if isinstance(source_path, str) and source_path else None
                    self.props.set_element(None)
                    self.status.set(f"Autosave wiederhergestellt: {display_name}")
                except Exception as e:
                    messagebox.showerror("Autosave", f"Wiederherstellung fehlgeschlagen: {e}")
                self._bump_autosave_session()
                if self._current_path:
                    self._update_autosave_target()
            try:
                os.remove(candidate["path"])
            except Exception:
                pass
        except Exception:
            pass

    def _configure_autosave_dialog(self):
        T = tk.Toplevel(self)
        T.title("Autosave Einstellungen")
        T.transient(self)
        try:
            T.grab_set()
        except Exception:
            pass
        frame = ttk.Frame(T, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        enabled_var = tk.BooleanVar(value=bool(getattr(self, "_autosave_enabled", True)))
        interval_var = tk.IntVar(value=int(getattr(self, "_autosave_interval_minutes", 3) or 3))

        ttk.Checkbutton(frame, text="Autosave aktivieren", variable=enabled_var).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Label(frame, text="Intervall (Minuten):").grid(row=1, column=0, sticky="w", pady=(12, 0))
        spin = tk.Spinbox(frame, from_=1, to=60, textvariable=interval_var, width=6)
        spin.grid(row=1, column=1, sticky="w", pady=(12, 0))
        ttk.Label(
            frame,
            text="Speichert automatisch eine Sicherungskopie im Ordner 'autosaves'.",
            foreground="#666",
            wraplength=360,
            justify="left",
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(12, 8))

        btns = ttk.Frame(frame)
        btns.grid(row=3, column=0, columnspan=2, sticky="e", pady=(8, 0))

        def close():
            try:
                T.destroy()
            except Exception:
                pass

        def apply():
            self._autosave_enabled = bool(enabled_var.get())
            try:
                interval = int(interval_var.get())
            except Exception:
                interval = self._autosave_interval_minutes
            self._autosave_interval_minutes = max(1, interval)
            try:
                self._save_settings()
            except Exception:
                pass
            self._schedule_autosave()
            close()

        ttk.Button(btns, text="Abbrechen", command=close).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(btns, text="Übernehmen", command=apply).pack(side=tk.RIGHT)

        try:
            T.bind("<Return>", lambda e: (apply(), "break"))
            T.bind("<Escape>", lambda e: (close(), "break"))
        except Exception:
            pass

    def _configure_ollama(self):
        T = tk.Toplevel(self)
        T.title("Ollama konfigurieren")
        tk.Label(T, text="Endpoint:").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        tk.Label(T, text="Model:").grid(row=1, column=0, padx=6, pady=6, sticky="e")
        tk.Label(T, text="Temperatur (0-1):").grid(row=2, column=0, padx=6, pady=6, sticky="e")
        tk.Label(T, text="Max Tokens:").grid(row=3, column=0, padx=6, pady=6, sticky="e")
        ep_var = tk.StringVar(value=self._ollama_endpoint)
        md_var = tk.StringVar(value=self._ollama_model)
        temp_var = tk.StringVar(value=str(self._ollama_temperature))
        max_var = tk.StringVar(value=str(self._ollama_num_predict))
        tk.Entry(T, textvariable=ep_var, width=40).grid(row=0, column=1, padx=6, pady=6, sticky="we")
        # Modelle: Combobox + Reload
        box_frame = tk.Frame(T)
        box_frame.grid(row=1, column=1, padx=6, pady=6, sticky="we")
        box_frame.columnconfigure(0, weight=1)
        models_cb = ttk.Combobox(box_frame, textvariable=md_var, width=28, state="normal")
        models_cb.grid(row=0, column=0, sticky="we")
        status_lbl = tk.Label(T, text="", fg="#666")
        status_lbl.grid(row=1, column=2, padx=6, pady=6, sticky="w")
        def reload_models():
            # Versuche, Modelle vom Endpoint zu laden
            endpoint = ep_var.get().strip() or self._ollama_endpoint
            try:
                if OllamaClient is None:
                    raise RuntimeError("Ollama-Client nicht verfügbar")
                client = OllamaClient(endpoint=endpoint, model=self._ollama_model)
                tags = client.health()
                models = []
                if isinstance(tags, dict):
                    for m in tags.get("models", []) or []:
                        name = m.get("name") if isinstance(m, dict) else None
                        if isinstance(name, str) and name:
                            models.append(name)
                if not models:
                    status_lbl.configure(text="Keine Modelle gefunden – manueller Eintrag möglich.")
                else:
                    status_lbl.configure(text=f"{len(models)} Modelle geladen")
                models_cb['values'] = models
                # Falls aktuelles Modell nicht in Liste → beibehalten, sonst auswählen
                cur = md_var.get().strip()
                if cur and cur in models:
                    models_cb.set(cur)
                elif models:
                    models_cb.set(models[0])
            except Exception as e:
                status_lbl.configure(text=f"Fehler beim Laden: {e}")
        reload_btn = tk.Button(box_frame, text="Neu laden", command=reload_models)
        reload_btn.grid(row=0, column=1, padx=(6,0))
        tk.Entry(T, textvariable=temp_var, width=8).grid(row=2, column=1, padx=6, pady=6, sticky="w")
        tk.Spinbox(T, from_=32, to=8192, textvariable=max_var, width=8).grid(row=3, column=1, padx=6, pady=6, sticky="w")
        # Initiale Ladung der Modelle beim Öffnen
        try:
            T.after(50, reload_models)
        except Exception:
            pass

        def ok():
            # Sammle Eingaben
            endpoint = ep_var.get().strip() or self._ollama_endpoint
            model = md_var.get().strip() or self._ollama_model or "llama:latest"
            try:
                t = float(temp_var.get().strip())
            except Exception:
                t = self._ollama_temperature
            try:
                n = int(max_var.get().strip())
                if n <= 0:
                    n = self._ollama_num_predict
            except Exception:
                n = self._ollama_num_predict
            # Auf Manager anwenden (auch lokale Attribute synchron halten für bestehenden Code)
            try:
                self._settings_manager.update_ollama(endpoint=endpoint, model=model, temperature=t, num_predict=n)
            except Exception:
                pass
            self._ollama_endpoint = endpoint
            self._ollama_model = model
            self._ollama_temperature = t
            self._ollama_num_predict = n
            # Persistieren
            self._save_settings()
            # Status aktualisieren
            try:
                self._refresh_ollama_status(async_call=True)
            except Exception:
                pass
            T.destroy()

        tk.Button(T, text="OK", command=ok).grid(row=4, column=0, padx=6, pady=8)
        tk.Button(T, text="Abbrechen", command=T.destroy).grid(row=4, column=1, padx=6, pady=8)
        T.grab_set()
        T.transient(self)

    def _configure_navigation_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Navigation Schrittgrößen")
        dlg.transient(self)
        dlg.grab_set()
        try:
            dlg.resizable(False, False)
        except Exception:
            pass

        content = ttk.Frame(dlg, padding=12)
        content.grid(row=0, column=0, sticky="nsew")
        dlg.columnconfigure(0, weight=1)
        dlg.rowconfigure(0, weight=1)

        nudge_frame = ttk.LabelFrame(content, text="Element verschieben (Modell-Einheiten)")
        nudge_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=(0, 10))
        nudge_frame.columnconfigure(1, weight=1)
        nudge_small_var = tk.StringVar(value=str(self._nudge_step_small))
        nudge_big_var = tk.StringVar(value=str(self._nudge_step_big))
        ttk.Label(nudge_frame, text="Feinschritt (Pfeiltasten)").grid(row=0, column=0, sticky="w", padx=(6, 4), pady=4)
        tk.Spinbox(nudge_frame, from_=1, to=200, width=6, textvariable=nudge_small_var).grid(row=0, column=1, sticky="w", padx=6, pady=4)
        ttk.Label(nudge_frame, text="Grobschritt (Shift+Pfeile)").grid(row=1, column=0, sticky="w", padx=(6, 4), pady=4)
        tk.Spinbox(nudge_frame, from_=1, to=400, width=6, textvariable=nudge_big_var).grid(row=1, column=1, sticky="w", padx=6, pady=4)

        pan_frame = ttk.LabelFrame(content, text="Ansicht verschieben (Pixel)")
        pan_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=(0, 10))
        pan_frame.columnconfigure(1, weight=1)
        pan_small_var = tk.StringVar(value=str(self._pan_step_small))
        pan_big_var = tk.StringVar(value=str(self._pan_step_big))
        ttk.Label(pan_frame, text="Feinschritt (Pfeiltasten ohne Auswahl)").grid(row=0, column=0, sticky="w", padx=(6, 4), pady=4)
        tk.Spinbox(pan_frame, from_=5, to=600, increment=5, width=6, textvariable=pan_small_var).grid(row=0, column=1, sticky="w", padx=6, pady=4)
        ttk.Label(pan_frame, text="Grobschritt (Shift+Pfeile ohne Auswahl)").grid(row=1, column=0, sticky="w", padx=(6, 4), pady=4)
        tk.Spinbox(pan_frame, from_=10, to=1200, increment=10, width=6, textvariable=pan_big_var).grid(row=1, column=1, sticky="w", padx=6, pady=4)

        ttk.Label(content, text="Hinweis: Grobschritte werden automatisch auf mindestens den Wert der Feinschritte gesetzt.", wraplength=320).grid(row=2, column=0, sticky="w", pady=(0, 10))

        btn_frame = ttk.Frame(content)
        btn_frame.grid(row=3, column=0, sticky="e")

        def close_dialog(event=None):
            dlg.grab_release()
            dlg.destroy()

        def apply_changes(event=None):
            mapping = [
                ("Feinschritt (Pfeiltasten)", "nudge_small", nudge_small_var.get()),
                ("Grobschritt (Shift+Pfeile)", "nudge_big", nudge_big_var.get()),
                ("Pan Feinschritt", "pan_small", pan_small_var.get()),
                ("Pan Grobschritt", "pan_big", pan_big_var.get()),
            ]
            values: Dict[str, int] = {}
            for label, key, raw in mapping:
                coerced = self._coerce_positive_int(raw)
                if coerced is None:
                    messagebox.showerror("Navigation", f"Ungültiger Wert für {label}. Bitte ganze Zahl > 0 eingeben.")
                    return
                values[key] = coerced
            if values["nudge_big"] < values["nudge_small"]:
                values["nudge_big"] = values["nudge_small"]
            if values["pan_big"] < values["pan_small"]:
                values["pan_big"] = values["pan_small"]
            self._apply_navigation_settings(values)
            self._save_settings()
            try:
                self.status.set("Navigation Schrittgrößen aktualisiert")
            except Exception:
                pass
            close_dialog()

        ttk.Button(btn_frame, text="Übernehmen", command=apply_changes).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="Abbrechen", command=close_dialog).pack(side=tk.RIGHT, padx=(6, 0))

        dlg.bind("<Return>", apply_changes)
        dlg.bind("<Escape>", close_dialog)
        dlg.protocol("WM_DELETE_WINDOW", close_dialog)
        try:
            dlg.focus_set()
        except Exception:
            pass

    def _ollama_health(self):
        if OllamaClient is None:
            messagebox.showwarning("Ollama", "Ollama-Client-Modul nicht gefunden (ollama_client.py).")
            return
        try:
            client = OllamaClient(endpoint=self._ollama_endpoint, model=self._ollama_model)
            tags = client.health()
            # Kurze Zusammenfassung
            models = ", ".join([t.get("name", "?") for t in tags.get("models", [])]) if isinstance(tags, dict) else str(tags)
            messagebox.showinfo("Ollama Health", f"Verbunden zu: {self._ollama_endpoint}\nModel: {self._ollama_model}\nVerfügbare Modelle: {models or 'unbekannt'}")
        except Exception as e:
            messagebox.showerror("Ollama Health", str(e))

    def _refresh_ollama_status(self, async_call: bool = True):
        """Aktualisiert die Anzeige des Ollama-Status (Modell/Reachability)."""
        def _work():
            status = f"Ollama: {self._ollama_model}"
            if OllamaClient is None:
                status = "Ollama: Client fehlt"
            else:
                try:
                    client = OllamaClient(endpoint=self._ollama_endpoint, model=self._ollama_model, timeout=5)
                    _ = client.health()
                    status = f"Ollama ok: {self._ollama_model}"
                except Exception as e:
                    status = f"Ollama Fehler: {e}"
            def _apply():
                try:
                    self._ollama_status.set(status)
                except Exception:
                    pass
            try:
                self.after(0, _apply)
            except Exception:
                _apply()

        if async_call:
            threading.Thread(target=_work, daemon=True).start()
        else:
            _work()

    def _quick_switch_model(self):
        """Öffnet den Einstellungsdialog für schnellen Modellwechsel und refresht den Status."""
        try:
            self._configure_ollama()
            # Der Status wird am Ende von _configure_ollama bereits aktualisiert
        except Exception:
            pass

    # ----- Bearbeiten -----
    def _add_element_dialog(self):
        T = tk.Toplevel(self)
        T.title("Element hinzufügen")
        tk.Label(T, text="Element-Typ:").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        tk.Label(T, text="Name:").grid(row=1, column=0, padx=6, pady=6, sticky="e")

        type_var = tk.StringVar(value="FUNCTION")
        name_var = tk.StringVar(value="Neues Element")
        tk.OptionMenu(T, type_var, *sorted(ELEMENT_STYLES.keys())).grid(row=0, column=1, padx=6, pady=6, sticky="we")
        tk.Entry(T, textvariable=name_var).grid(row=1, column=1, padx=6, pady=6, sticky="we")

        def ok():
            el = self.canvas.add_element(type_var.get(), name_var.get(), at=(300, 200))
            self.canvas.selected_id = el.element_id
            self.canvas.redraw_all()
            self.props.set_element(el)
            T.destroy()

        tk.Button(T, text="OK", command=ok).grid(row=2, column=0, padx=6, pady=8)
        tk.Button(T, text="Abbrechen", command=T.destroy).grid(row=2, column=1, padx=6, pady=8)
        T.grab_set()
        T.transient(self)

    def _add_connection_dialog(self):
        if not self.canvas.elements:
            messagebox.showinfo("Hinweis", "Bitte zuerst Elemente hinzufügen")
            return
        T = tk.Toplevel(self)
        T.title("Verbindung hinzufügen")
        tk.Label(T, text="Quelle (Element-ID):").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        tk.Label(T, text="Ziel (Element-ID):").grid(row=1, column=0, padx=6, pady=6, sticky="e")
        tk.Label(T, text="Typ:").grid(row=2, column=0, padx=6, pady=6, sticky="e")
        tk.Label(T, text="Pfeilstil:").grid(row=3, column=0, padx=6, pady=6, sticky="e")
        tk.Label(T, text="Beschriftung:").grid(row=4, column=0, padx=6, pady=6, sticky="e")

        ids = sorted(self.canvas.elements.keys())
        src_var = tk.StringVar(value=ids[0])
        tgt_var = tk.StringVar(value=ids[-1])
        type_var = tk.StringVar(value="SEQUENCE")
        tk.OptionMenu(T, src_var, *ids).grid(row=0, column=1, padx=6, pady=6, sticky="we")
        tk.OptionMenu(T, tgt_var, *ids).grid(row=1, column=1, padx=6, pady=6, sticky="we")
        tk.OptionMenu(T, type_var, *sorted(CONNECTION_STYLES.keys())).grid(row=2, column=1, padx=6, pady=6, sticky="we")
        arrow_var = tk.StringVar(value="single")
        tk.OptionMenu(T, arrow_var, "none", "single", "double").grid(row=3, column=1, padx=6, pady=6, sticky="we")
        desc_var = tk.StringVar(value="")
        tk.Entry(T, textvariable=desc_var).grid(row=4, column=1, padx=6, pady=6, sticky="we")

        def ok():
            if src_var.get() == tgt_var.get():
                messagebox.showerror("Fehler", "Quelle und Ziel dürfen nicht gleich sein")
                return
            conn = self.canvas.add_connection(src_var.get(), tgt_var.get(), type_var.get())
            if conn:
                conn.arrow_style = arrow_var.get()
                conn.description = desc_var.get().strip()
                self.canvas.redraw_all()
            T.destroy()

        tk.Button(T, text="OK", command=ok).grid(row=5, column=0, padx=6, pady=8)
        tk.Button(T, text="Abbrechen", command=T.destroy).grid(row=5, column=1, padx=6, pady=8)
        T.grab_set()
        T.transient(self)

    def _about(self):
        """Zeigt einen modernen About-Dialog mit VPB-Branding."""
        about_window = tk.Toplevel(self)
        about_window.title("Über VPB Process Designer")
        about_window.geometry("500x400")
        about_window.resizable(False, False)
        about_window.transient(self)
        about_window.grab_set()
        
        # Zentriere das Fenster
        about_window.update_idletasks()
        x = (about_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (about_window.winfo_screenheight() // 2) - (400 // 2)
        about_window.geometry(f"+{x}+{y}")
        
        # Header mit VPB-Logo und Titel
        header_frame = tk.Frame(about_window, bg="#2c3e50", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # VPB Logo/Icon
        logo_label = tk.Label(header_frame, text="🔄", font=("Segoe UI", 32), 
                             bg="#2c3e50", fg="#ecf0f1")
        logo_label.pack(side=tk.LEFT, padx=20, pady=20)
        
        # Titel und Untertitel
        title_frame = tk.Frame(header_frame, bg="#2c3e50")
        title_frame.pack(side=tk.LEFT, padx=10, pady=20, expand=True, fill=tk.BOTH)
        
        title_label = tk.Label(title_frame, text="VPB Process Designer", 
                              font=("Segoe UI", 18, "bold"), 
                              bg="#2c3e50", fg="#ecf0f1")
        title_label.pack(anchor="w")
        
        subtitle_label = tk.Label(title_frame, text="Verwaltungsprozess-Beschreibungssprache Editor", 
                                 font=("Segoe UI", 10), 
                                 bg="#2c3e50", fg="#bdc3c7")
        subtitle_label.pack(anchor="w")
        
        # Inhalt
        content_frame = tk.Frame(about_window, bg="#ecf0f1", padx=30, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Version und Informationen
        version_text = """Version: 1.0 (Minimal)
Entwickelt für die deutsche Verwaltung

VPB (Verwaltungsprozess-Beschreibungssprache) ist eine 
speziell für deutsche Behörden entwickelte Sprache zur 
Modellierung und Dokumentation von Verwaltungsprozessen.

Basierend auf:
• BMI Organisationshandbuch eEPK-Standards  
• UDS3 4D-Geodaten-Integration
• Deutsche Verwaltungsrecht-Spezifika

© 2025 UDS3 Development Team
Lizenz: Behörden-intern"""
        
        info_label = tk.Label(content_frame, text=version_text, 
                             font=("Segoe UI", 10), 
                             bg="#ecf0f1", fg="#2c3e50",
                             justify=tk.LEFT, anchor="nw")
        info_label.pack(fill=tk.BOTH, expand=True)
        
        # Buttons
        button_frame = tk.Frame(about_window, bg="#ecf0f1", pady=10)
        button_frame.pack(fill=tk.X)
        
        ok_button = tk.Button(button_frame, text="OK", 
                             command=about_window.destroy,
                             font=("Segoe UI", 10), 
                             bg="#3498db", fg="white",
                             relief=tk.FLAT, padx=20, pady=8)
        ok_button.pack(side=tk.RIGHT, padx=30)
        
        # ESC-Taste bindet auf Schließen
        about_window.bind("<Escape>", lambda e: about_window.destroy())
        about_window.focus_set()

    def _edit_element_styles(self):
        T = tk.Toplevel(self)
        T.title("Element-Stile bearbeiten")
        T.geometry("700x420")
        # Liste links
        left = tk.Frame(T)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=6)
        tk.Label(left, text="Elementtypen").pack(anchor="w")
        lst = tk.Listbox(left, height=20)
        lst.pack(fill=tk.Y, expand=False)
        # Editor rechts
        right = tk.Frame(T)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=6, pady=6)
        right.columnconfigure(1, weight=1)
        tk.Label(right, text="Shape:").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        tk.Label(right, text="Fill:").grid(row=1, column=0, sticky="e", padx=4, pady=4)
        tk.Label(right, text="Outline:").grid(row=2, column=0, sticky="e", padx=4, pady=4)
        tk.Label(right, text="Dash (z.B. 4,4):").grid(row=3, column=0, sticky="e", padx=4, pady=4)
        shape_var = tk.StringVar(value="rect")
        fill_var = tk.StringVar(value="#EEEEEE")
        outline_var = tk.StringVar(value="#888888")
        dash_var = tk.StringVar(value="")
        shape_cb = ttk.Combobox(right, textvariable=shape_var, values=["rect","rectangle","oval","circle","diamond","hex"], state="readonly")
        shape_cb.grid(row=0, column=1, sticky="we", padx=4, pady=4)
        tk.Entry(right, textvariable=fill_var).grid(row=1, column=1, sticky="we", padx=4, pady=4)
        tk.Entry(right, textvariable=outline_var).grid(row=2, column=1, sticky="we", padx=4, pady=4)
        tk.Entry(right, textvariable=dash_var).grid(row=3, column=1, sticky="we", padx=4, pady=4)
        # Vorschau
        prev = tk.Canvas(right, width=220, height=140, bg="#fff", highlightthickness=1, highlightbackground="#ccc")
        prev.grid(row=0, column=2, rowspan=4, padx=8, pady=4)

        # Datenquelle: vorhandene Typen + existierende Overrides
        types = sorted(ELEMENT_STYLES.keys())
        for t in types:
            lst.insert(tk.END, t)

        def load_type(t: str):
            # Aufgelösten Stil anzeigen (inkl. Overrides)
            style = self.canvas._resolve_element_style(t)
            shape_var.set(style.get("shape", "rect"))
            fill_var.set(style.get("fill", "#EEEEEE"))
            outline_var.set(style.get("outline", "#888888"))
            dv = style.get("dash")
            if isinstance(dv, (tuple, list)):
                dash_var.set(",".join(str(int(x)) for x in dv))
            elif isinstance(dv, str):
                dash_var.set(dv)
            else:
                dash_var.set("")
            draw_preview()

        def draw_preview():
            prev.delete("all")
            w = 180; h = 90; cx = 110; cy = 70
            sh = shape_var.get()
            fill = fill_var.get(); out = outline_var.get()
            dash_s = dash_var.get().strip()
            dash = None
            if dash_s:
                try:
                    dash = tuple(int(x.strip()) for x in dash_s.split(',') if x.strip())
                except Exception:
                    dash = None
            if sh in ("rect","rectangle"):
                prev.create_rectangle(cx - w//2, cy - h//2, cx + w//2, cy + h//2, fill=fill, outline=out, width=2, dash=dash)
            elif sh in ("oval","circle"):
                r = min(w,h)//2
                prev.create_oval(cx - r, cy - r, cx + r, cy + r, fill=fill, outline=out, width=2, dash=dash)
            elif sh == "diamond":
                pts = [cx, cy - h//2, cx + w//2, cy, cx, cy + h//2, cx - w//2, cy]
                prev.create_polygon(pts, fill=fill, outline=out, width=2, dash=dash)
            elif sh == "hex":
                dx = w//2; dy = h//2
                pts = [cx - dx//2, cy - dy, cx + dx//2, cy - dy, cx + dx, cy, cx + dx//2, cy + dy, cx - dx//2, cy + dy, cx - dx, cy]
                prev.create_polygon(pts, fill=fill, outline=out, width=2, dash=dash)
            else:
                prev.create_rectangle(cx - w//2, cy - h//2, cx + w//2, cy + h//2, fill=fill, outline=out, width=2, dash=dash)

        shape_cb.bind('<<ComboboxSelected>>', lambda e: draw_preview())
        for v in (fill_var, outline_var, dash_var):
            v.trace_add('write', lambda *_: draw_preview())

        def on_select(evt=None):
            try:
                idx = lst.curselection()
                if not idx:
                    return
                t = lst.get(idx[0])
                load_type(t)
            except Exception:
                pass
        lst.bind('<<ListboxSelect>>', on_select)

        # Save/Reset Buttons
        btns = tk.Frame(right)
        btns.grid(row=4, column=0, columnspan=3, sticky="we")
        btns.columnconfigure(0, weight=1)
        btns.columnconfigure(1, weight=0)
        btns.columnconfigure(2, weight=0)

        def apply_style():
            idx = lst.curselection()
            if not idx:
                return
            t = lst.get(idx[0])
            s = {"shape": shape_var.get(), "fill": fill_var.get(), "outline": outline_var.get()}
            ds = dash_var.get().strip()
            if ds:
                try:
                    s["dash"] = [int(x.strip()) for x in ds.split(',') if x.strip()]
                except Exception:
                    s["dash"] = None
            # Update Overrides
            current = dict(self.canvas.element_style_overrides)
            current[t] = s
            self.canvas.set_element_style_overrides(current)
            # Einstellungen speichern
            try:
                self._save_settings()
            except Exception:
                pass

        def reset_style():
            idx = lst.curselection()
            if not idx:
                return
            t = lst.get(idx[0])
            current = dict(self.canvas.element_style_overrides)
            if t in current:
                current.pop(t, None)
                self.canvas.set_element_style_overrides(current)
                try:
                    self._save_settings()
                except Exception:
                    pass
            load_type(t)

        tk.Button(btns, text="Übernehmen", command=apply_style).grid(row=0, column=1, padx=4, pady=6)
        tk.Button(btns, text="Zurücksetzen", command=reset_style).grid(row=0, column=2, padx=4, pady=6)

        # Initiale Auswahl
        try:
            lst.selection_set(0)
            load_type(lst.get(0))
        except Exception:
            pass

    # ----- Auswahl/Properties/Shortcuts Hilfsfunktionen -----
    def _on_hierarchy_selected(self, index: Optional[int], category: Optional[Dict[str, object]]):
        self._selected_hierarchy_index = index if isinstance(index, int) else None
        if not category or index is None:
            try:
                self.props.set_hierarchy(None, None)
            except Exception:
                pass
            return
        try:
            self.canvas.selected_conn_id = None
            self.canvas.selected_id = None
            if hasattr(self.canvas, "selected_ids"):
                try:
                    self.canvas.selected_ids.clear()
                except Exception:
                    self.canvas.selected_ids = set()
        except Exception:
            pass
        try:
            self.canvas.redraw_all()
        except Exception:
            pass
        try:
            cat_dict = dict(category) if isinstance(category, dict) else {
                "name": getattr(category, "name", ""),
                "color": getattr(category, "color", ""),
                "y0": getattr(category, "y0", 0.0),
                "y1": getattr(category, "y1", 0.0),
            }
        except Exception:
            cat_dict = {"name": "", "color": "", "y0": 0.0, "y1": 0.0}
        try:
            self.props.set_hierarchy(index, cat_dict)
        except Exception:
            pass
        try:
            name = str(cat_dict.get("name", "") or "")
            if name:
                self.status.set(f"Hierarchie \u201e{name}\u201c ausgewählt.")
            else:
                self.status.set("Hierarchie ausgewählt.")
        except Exception:
            pass

    def _on_hierarchy_double_clicked(self, index: Optional[int], category: Optional[Dict[str, object]]):
        if index is None or not category:
            return
        try:
            cat_dict = dict(category) if isinstance(category, dict) else {
                "name": getattr(category, "name", ""),
                "color": getattr(category, "color", ""),
                "y0": getattr(category, "y0", 0.0),
                "y1": getattr(category, "y1", 0.0),
            }
        except Exception:
            cat_dict = {"name": "", "color": "", "y0": 0.0, "y1": 0.0}
        self._open_hierarchy_dialog(index, cat_dict)

    def _update_hierarchy_category(
        self,
        index: int,
        data: Dict[str, object],
        *,
        refresh_panel: bool = True,
    ) -> bool:
        if not hasattr(self, "_palette_integration"):
            return False
        return self._palette_integration.update_hierarchy_category(index, data, refresh_panel=refresh_panel)

    def _open_hierarchy_dialog(self, index: int, category: Dict[str, object]) -> None:
        if hasattr(self, "_palette_integration"):
            self._palette_integration.open_hierarchy_dialog(index, category)

    def _on_selection_changed(self, el: Optional[VPBElement], conn: Optional[VPBConnection]):
        if hasattr(self, "_properties_bridge"):
            self._properties_bridge.on_selection_changed(el, conn)

    def _apply_properties(self, values: Dict[str, object]):
        if hasattr(self, "_properties_bridge"):
            self._properties_bridge.apply_properties(values)

    # ----- Palette Handling -----
    def _reload_palettes(self):
        if hasattr(self, "_palette_integration"):
            self._palette_integration.reload_palettes()

    def _on_palette_pick(self, item: dict):
        if hasattr(self, "_palette_integration"):
            self._palette_integration.on_palette_pick(item)


    def _delete_selected(self):
        if hasattr(self, "_actions"):
            self._actions.delete_selected()

    def _duplicate_selected(self):
        if hasattr(self, "_actions"):
            self._actions.duplicate_selected()

    def _toggle_snap(self):
        if hasattr(self, "_actions"):
            self._actions.toggle_snap()

    def _toggle_link_mode(self):
        if hasattr(self, "_actions"):
            self._actions.toggle_link_mode()

    def _undo(self):
        if hasattr(self, "_actions"):
            self._actions.undo()

    def _redo(self):
        if hasattr(self, "_actions"):
            self._actions.redo()

    # ----- Ansicht: Handler -----
    def _reset_view(self):
        if hasattr(self, "_actions"):
            self._actions.reset_view()

    def _fit_to_diagram(self):
        if hasattr(self, "_actions"):
            self._actions.fit_to_diagram()

    def _ensure_chat_visible(self, min_height: int = 200):
        if hasattr(self, "_chat_integration"):
            self._chat_integration.ensure_chat_visible(min_height)

    # ----- Chat Seitenleiste -----
    def _focus_chat(self):
        if hasattr(self, "_chat_integration"):
            self._chat_integration.focus_chat()

    # ----- Shortcut-Helfer -----
    def _is_text_input_focus(self) -> bool:
        try:
            w = self.focus_get()
            return isinstance(w, (tk.Entry, tk.Text, tk.Spinbox))
        except Exception:
            return False

    def _select_all(self):
        if hasattr(self, "canvas_controller"):
            self.canvas_controller.select_all()

    def _copy_selection(self):
        if hasattr(self, "canvas_controller"):
            self.canvas_controller.copy_selection()

    def _cut_selection(self):
        if hasattr(self, "canvas_controller"):
            self.canvas_controller.cut_selection()

    def _paste_clipboard(self):
        if hasattr(self, "canvas_controller"):
            self.canvas_controller.paste_clipboard()

    def _handle_arrow(self, sx: int, sy: int, big: bool = False):
        if hasattr(self, "canvas_controller"):
            return self.canvas_controller.handle_arrow(sx, sy, big)

    def _handle_controller_result(self, item):
        dispatch = getattr(self, "_task_dispatch", None)
        if dispatch is not None:
            return dispatch.dispatch_item(item)
        task_controller = getattr(self, "task_controller", None)
        if task_controller is None:
            return False
        try:
            return bool(task_controller.handle_poll_item(item))
        except Exception:
            traceback.print_exc()
            return True

    def _handle_ctrl_enter(self, event=None):
        if hasattr(self, "_chat_integration"):
            return self._chat_integration.handle_ctrl_enter(event)

    # ----- LLM Antwort Post-Processing → Canvas Integration -----
    def _postprocess_chat_result(self):
        if hasattr(self, "_chat_integration"):
            self._chat_integration.postprocess_chat_result()

    def _apply_full_process_json(self, data: dict):
        if hasattr(self, "_chat_integration"):
            self._chat_integration.apply_full_process_json(data)

    def _highlight_merge_changes(
        self,
        prev_element_ids: Iterable[str],
        prev_connection_ids: Iterable[str],
        element_renames: Iterable[str] = (),
        connection_renames: Iterable[str] = (),
    ) -> None:
        try:
            if not hasattr(self, "canvas"):
                return
            current_elements = set(self.canvas.elements.keys())
            current_connections = set(self.canvas.connections.keys())
            prev_elements = set(prev_element_ids or [])
            prev_connections = set(prev_connection_ids or [])

            added_elements = [eid for eid in (current_elements - prev_elements) if eid in self.canvas.elements]
            added_connections = [cid for cid in (current_connections - prev_connections) if cid in self.canvas.connections]
            renamed_elements = [eid for eid in (element_renames or []) if eid in current_elements]
            renamed_connections = [cid for cid in (connection_renames or []) if cid in current_connections]

            self.canvas.highlight_merge_results(
                added_elements=added_elements,
                updated_elements=renamed_elements,
                added_connections=added_connections,
                updated_connections=renamed_connections,
            )
        except Exception:
            pass

    def _prepare_merge_payload(self, data: dict) -> tuple[dict, List[str]]:
        if hasattr(self, "_chat_integration"):
            return self._chat_integration._prepare_merge_payload(data)
        raise ValueError("Merge-Helfer nicht initialisiert")

    def _merge_full_process_json(self, data: dict):
        if hasattr(self, "_chat_integration"):
            self._chat_integration.merge_full_process_json(data)

    def _merge_full_process_json_sync(
        self,
        prepared: dict,
        hints: Optional[List[str]] = None,
        hints_logged: bool = False,
    ):
        if hasattr(self, "_chat_integration"):
            self._chat_integration._merge_full_process_json_sync(
                prepared,
                hints=hints,
                hints_logged=hints_logged,
            )

    def _prepare_patch_payload(self, patch: dict) -> tuple[dict, List[str]]:
        if hasattr(self, "_chat_integration"):
            return self._chat_integration._prepare_patch_payload(patch)
        raise ValueError("Patch-Helfer nicht initialisiert")

    def _apply_add_only_patch(self, patch: dict):
        if hasattr(self, "_chat_integration"):
            self._chat_integration.apply_add_only_patch(patch)

    def _apply_add_only_patch_sync(
        self,
        prepared: dict,
        warnings: Optional[List[str]] = None,
        warnings_logged: bool = False,
    ):
        if hasattr(self, "_chat_integration"):
            self._chat_integration._apply_add_only_patch_sync(
                prepared,
                warnings=warnings,
                warnings_logged=warnings_logged,
            )

    def _apply_diagnose_patch(self, diag: dict):
        try:
            patch = diag.get("patch") or {}
            if not isinstance(patch, dict):
                messagebox.showerror("Diagnose", "Patch fehlt oder ist ungültig")
                return
            # Diagnose/Fix Validierung (diagnose_fix)
            try:
                from vpb_prompt_core import validate_vpb_json  # type: ignore
                existing_ids = set(self.canvas.elements.keys()) | set(self.canvas.connections.keys())
                try:
                    elem_types = set(ELEMENT_STYLES.keys())  # type: ignore
                except Exception:
                    elem_types = None
                try:
                    conn_types = set(CONNECTION_STYLES.keys())  # type: ignore
                except Exception:
                    conn_types = None
                raw = json.dumps({"issues": diag.get("issues") or [], "patch": patch}, ensure_ascii=False)
                vres = validate_vpb_json(
                    raw,
                    mode="diagnose_fix",
                    existing_ids=existing_ids,
                    allow_element_types=elem_types,
                    allow_connection_types=conn_types,
                    tolerance="lenient",
                )
                if getattr(vres, 'fatal', False):
                    errs = [f"- {i.code}: {i.message}" for i in getattr(vres, 'issues', []) if getattr(i, 'severity', '') == 'error']
                    messagebox.showerror("Diagnose – Validierung", "Fataler Validierungsfehler:\n" + ("\n".join(errs) or "Unbekannt"))
                    return
                sanitized = getattr(vres, 'parsed', None)
                if isinstance(sanitized, dict):
                    patch_candidate = sanitized.get("patch")
                    if isinstance(patch_candidate, dict):
                        patch = patch_candidate
                warns = [f"- {i.code}: {i.message}" for i in getattr(vres, 'issues', []) if getattr(i, 'severity', '') in ("warning", "info")]
                repairs = list(getattr(vres, 'repairs', []) or []) if hasattr(vres, 'repairs') else []
                if repairs:
                    warns.extend(f"- Reparatur: {r}" for r in repairs)
                if warns:
                    try:
                        self.chat.append_assistant("\n[Diagnose Validierung]\n" + "\n".join(warns))
                    except Exception:
                        pass
                    self.status.set("Diagnose: Hinweise vorhanden")
            except Exception:
                pass
            self._apply_add_only_patch(patch)
            issues = diag.get("issues") or []
            if issues:
                # Einfacher Report im Chat-Fenster ergänzen
                lines = [f"Issue {i.get('id')}: {i.get('severity')} – {i.get('message')}" for i in issues if isinstance(i, dict)]
                self.chat.append_assistant("\n[Diagnose Zusammenfassung]\n" + "\n".join(lines))
        except Exception as e:
            messagebox.showerror("Diagnose", f"Fehler: {e}")

    # ----- Chat-Verlauf Persistenz -----
    def _on_close(self):
        try:
            dispatch = getattr(self, "_task_dispatch", None)
            if dispatch is not None:
                dispatch.stop()
        except Exception:
            pass
        try:
            if self._autosave_after_id is not None:
                try:
                    self.after_cancel(self._autosave_after_id)
                except Exception:
                    pass
                self._autosave_after_id = None
        except Exception:
            pass
        try:
            if hasattr(self, "chat_controller"):
                self.chat_controller.save_history()
            # Vor dem Speichern Sidebar-Breiten aktualisieren
            try:
                self._sidebar_left_width = int(self._left_pane.winfo_width())
                self._sidebar_right_width = int(self._right_pane.winfo_width())
            except Exception:
                pass
            self._save_settings()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            os._exit(0)

    # ----- AI: Text → Diagramm -----
    def _text_to_diagram(self):
        if hasattr(self, "_chat_integration"):
            self._chat_integration.text_to_diagram()

    def _suggest_next_step(self):
        try:
            from vpb_ai_logic import build_prompt_with_examples_next_steps  # type: ignore
            from vpb_diff import validate_add_only_diff  # type: ignore
        except Exception as e:
            messagebox.showerror("AI", f"Fehlende Module: {e}")
            return
        if OllamaClient is None:
            messagebox.showwarning("AI", "Ollama-Client nicht verfügbar.")
            return
        # Kontext
        current = self.canvas.to_dict()
        import json as _json
        element_types = list(ELEMENT_STYLES.keys())
        connection_types = list(CONNECTION_STYLES.keys())
        selected = self.canvas.selected_id

        # Dialog für Beispielparameter
        T = tk.Toplevel(self)
        T.title("Nächster Schritt vorschlagen…")
        tk.Label(T, text="Beispiel-Tags (optional, komma-getrennt):").grid(row=0, column=0, padx=6, pady=(8,2), sticky="w")
        tags_var = tk.StringVar(value="")
        tk.Entry(T, textvariable=tags_var, width=46).grid(row=0, column=1, padx=6, pady=(8,2), sticky="w")
        tk.Label(T, text="Anzahl Beispiele:").grid(row=1, column=0, padx=6, pady=2, sticky="e")
        max_var = tk.StringVar(value="3")
        tk.Spinbox(T, from_=0, to=5, textvariable=max_var, width=6).grid(row=1, column=1, padx=6, pady=2, sticky="w")

        def run():
            try:
                ex_count = max(0, min(5, int(max_var.get().strip() or "0")))
            except Exception:
                ex_count = 3
            raw_tags = [t.strip() for t in tags_var.get().split(",") if t.strip()]
            prompt = build_prompt_with_examples_next_steps(
                _json.dumps(current, ensure_ascii=False, indent=2),
                selected,
                element_types,
                connection_types,
                example_tags=raw_tags,
                max_examples=ex_count,
            )
            client = OllamaClient(endpoint=self._ollama_endpoint, model=self._ollama_model)
            # Fortschrittsfenster
            PD = tk.Toplevel(T)
            PD.title("Vorschläge werden generiert…")
            tk.Label(PD, text="LLM läuft…").pack(padx=10, pady=(10,4))
            ptxt = tk.Text(PD, width=60, height=4)
            ptxt.pack(padx=10, pady=4)
            ptxt.insert("1.0", prompt[:2000])
            ptxt.configure(state="disabled")
            btnf = tk.Frame(PD)
            btnf.pack(fill=tk.X, padx=10, pady=(4,10))
            cancelled = {"v": False}
            def do_cancel():
                cancelled["v"] = True
                if job and hasattr(job, "cancel"):
                    job.cancel()
            tk.Button(btnf, text="Abbrechen", command=do_cancel).pack(side=tk.RIGHT)

            def target():
                return client.generate_json(
                    prompt,
                    options=OllamaOptions(temperature=self._ollama_temperature, num_predict=self._ollama_num_predict),
                    retries=1,
                    validate=lambda d: validate_add_only_diff(d, [e["element_id"] for e in current.get("elements", [])], element_types, connection_types),
                )

            job = OllamaJob(target).start() if OllamaJob else None

            def poll():
                if cancelled["v"]:
                    try:
                        PD.destroy()
                    except Exception:
                        pass
                    return
                if not job:
                    try:
                        diff = target()
                    except Exception as e:
                        PD.destroy()
                        messagebox.showerror("AI", f"Fehler: {e}")
                        return
                    try:
                        PD.destroy()
                    except Exception:
                        pass
                    self._review_and_apply_diff(current, diff, element_types, connection_types)
                    return
                chunk = job.get_nowait()
                if chunk is None:
                    if not job.is_done():
                        self.after(150, poll)
                        return
                    try:
                        chunk = job.get(timeout=0.1)
                    except Exception:
                        chunk = None
                if isinstance(chunk, Exception):
                    try:
                        PD.destroy()
                    except Exception:
                        pass
                    messagebox.showerror("AI", f"Fehler: {chunk}")
                    return
                if chunk is not None:
                    try:
                        PD.destroy()
                    except Exception:
                        pass
                    self._review_and_apply_diff(current, chunk, element_types, connection_types)
                    return
                self.after(150, poll)

            poll()

        btns = tk.Frame(T)
        btns.grid(row=2, column=0, columnspan=2, padx=6, pady=8, sticky="e")
        tk.Button(btns, text="Generieren", command=run).pack(side=tk.LEFT, padx=4)
        tk.Button(btns, text="Abbrechen", command=T.destroy).pack(side=tk.LEFT, padx=4)
        T.grab_set(); T.transient(self)
        return

    def _diagnose_fix(self):
        try:
            from vpb_ai_logic import build_prompt_with_examples_diagnose_fix  # type: ignore
            from vpb_diff import validate_add_only_diff  # type: ignore
        except Exception as e:
            messagebox.showerror("AI", f"Fehlende Module: {e}")
            return
        if OllamaClient is None:
            messagebox.showwarning("AI", "Ollama-Client nicht verfügbar.")
            return
        current = self.canvas.to_dict()
        import json as _json
        element_types = list(ELEMENT_STYLES.keys())
        connection_types = list(CONNECTION_STYLES.keys())

        # Dialog für Beispielparameter
        T = tk.Toplevel(self)
        T.title("Diagnose/Fix…")
        tk.Label(T, text="Beispiel-Tags (optional, komma-getrennt):").grid(row=0, column=0, padx=6, pady=(8,2), sticky="w")
        tags_var = tk.StringVar(value="standard")
        tk.Entry(T, textvariable=tags_var, width=46).grid(row=0, column=1, padx=6, pady=(8,2), sticky="w")
        tk.Label(T, text="Anzahl Beispiele:").grid(row=1, column=0, padx=6, pady=2, sticky="e")
        max_var = tk.StringVar(value="2")
        tk.Spinbox(T, from_=0, to=5, textvariable=max_var, width=6).grid(row=1, column=1, padx=6, pady=2, sticky="w")

        def run():
            try:
                ex_count = max(0, min(5, int(max_var.get().strip() or "0")))
            except Exception:
                ex_count = 2
            raw_tags = [t.strip() for t in tags_var.get().split(",") if t.strip()]
            prompt = build_prompt_with_examples_diagnose_fix(
                _json.dumps(current, ensure_ascii=False, indent=2),
                element_types,
                connection_types,
                example_tags=raw_tags,
                max_examples=ex_count,
            )
            client = OllamaClient(endpoint=self._ollama_endpoint, model=self._ollama_model)

            PD = tk.Toplevel(T)
            PD.title("Diagnose läuft…")
            tk.Label(PD, text="LLM analysiert das Diagramm…").pack(padx=10, pady=(10,4))
            ptxt = tk.Text(PD, width=60, height=4)
            ptxt.pack(padx=10, pady=4)
            ptxt.insert("1.0", prompt[:2000])
            ptxt.configure(state="disabled")
            btnf = tk.Frame(PD)
            btnf.pack(fill=tk.X, padx=10, pady=(4,10))
            cancelled = {"v": False}
            def do_cancel():
                cancelled["v"] = True
                if job and hasattr(job, "cancel"):
                    job.cancel()
            tk.Button(btnf, text="Abbrechen", command=do_cancel).pack(side=tk.RIGHT)

            def _validate_issues_patch(d: dict) -> tuple[bool, str | None]:
                if not isinstance(d, dict):
                    return False, "Antwort ist kein Objekt"
                issues = d.get("issues", [])
                patch = d.get("patch", {"elements": [], "connections": []})
                if not isinstance(issues, list):
                    return False, "'issues' fehlt oder ist kein Array"
                # optional: grobe Prüfung der Felder
                for it in issues:
                    if not isinstance(it, dict):
                        return False, "Eintrag in 'issues' ist kein Objekt"
                    if "id" not in it or "message" not in it:
                        return False, "Eintrag in 'issues' ohne id/message"
                # Patch validieren (Add-Only)
                try:
                    ok, err = validate_add_only_diff(
                        patch if isinstance(patch, dict) else {},
                        [e["element_id"] for e in current.get("elements", [])],
                        element_types,
                        connection_types,
                    )
                except Exception as ve:
                    return False, f"Patch-Validierung fehlgeschlagen: {ve}"
                if not ok:
                    # Patch invalid ist okay, aber wir signalisieren nur Warnung – nicht abbrechen
                    return True, None
                return True, None

            def target():
                return client.generate_json(
                    prompt,
                    options=OllamaOptions(temperature=self._ollama_temperature, num_predict=self._ollama_num_predict),
                    retries=1,
                    validate=_validate_issues_patch,
                )

            job = OllamaJob(target).start() if OllamaJob else None

            def poll():
                if cancelled["v"]:
                    try:
                        PD.destroy()
                    except Exception:
                        pass
                    return
                if not job:
                    try:
                        res = target()
                    except Exception as e:
                        PD.destroy()
                        messagebox.showerror("AI", f"Fehler: {e}")
                        return
                    try:
                        PD.destroy()
                    except Exception:
                        pass
                    _show_issues_and_patch(res)
                    return
                chunk = job.get_nowait()
                if chunk is None:
                    if not job.is_done():
                        self.after(150, poll)
                        return
                    try:
                        chunk = job.get(timeout=0.1)
                    except Exception:
                        chunk = None
                if isinstance(chunk, Exception):
                    try:
                        PD.destroy()
                    except Exception:
                        pass
                    messagebox.showerror("AI", f"Fehler: {chunk}")
                    return
                if chunk is not None:
                    try:
                        PD.destroy()
                    except Exception:
                        pass
                    _show_issues_and_patch(chunk)
                    return
                self.after(150, poll)

            def _show_issues_and_patch(data: dict):
                issues = data.get("issues", []) if isinstance(data, dict) else []
                patch = data.get("patch", {"elements": [], "connections": []}) if isinstance(data, dict) else {"elements": [], "connections": []}
                W = tk.Toplevel(self)
                W.title("Diagnose-Ergebnisse")
                W.geometry("680x480")
                top = tk.Frame(W)
                top.pack(fill=tk.BOTH, expand=True)
                canvas = tk.Canvas(top)
                ysb = tk.Scrollbar(top, orient=tk.VERTICAL, command=canvas.yview)
                inner = tk.Frame(canvas)
                inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
                canvas.create_window((0,0), window=inner, anchor="nw")
                canvas.configure(yscrollcommand=ysb.set)
                canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                ysb.pack(side=tk.RIGHT, fill=tk.Y)

                tk.Label(inner, text="Gefundene Issues:", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=8, pady=(8,4))
                if not issues:
                    tk.Label(inner, text="Keine Probleme gefunden.", fg="#0a0").pack(anchor="w", padx=12)
                else:
                    for it in issues:
                        sev = str(it.get("severity", "info")).lower()
                        color = {"error": "#b22222", "warning": "#b36b00", "info": "#444"}.get(sev, "#444")
                        loc_el = it.get("location", {}).get("element_id") if isinstance(it.get("location"), dict) else None
                        loc_con = it.get("location", {}).get("connection_id") if isinstance(it.get("location"), dict) else None
                        where = f" (Element: {loc_el})" if loc_el else (f" (Verbindung: {loc_con})" if loc_con else "")
                        msg = f"[{sev.upper()}] {it.get('id','ISS')} – {it.get('message','')}" + where
                        tk.Label(inner, text=msg, fg=color, wraplength=620, justify=tk.LEFT).pack(anchor="w", padx=12, pady=2)

                tk.Label(inner, text="\nPatch-Vorschlag:", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=8, pady=(8,4))
                btns = tk.Frame(inner)
                btns.pack(fill=tk.X, padx=8, pady=(0,8))

                def open_review():
                    if not isinstance(patch, dict) or (not patch.get("elements") and not patch.get("connections")):
                        messagebox.showinfo("AI", "Kein Patch-Vorschlag enthalten.")
                        return
                    self._review_and_apply_diff(current, patch, element_types, connection_types)

                tk.Button(btns, text="Patch prüfen/anwenden…", command=open_review).pack(side=tk.RIGHT)

            poll()

        btns = tk.Frame(T)
        btns.grid(row=2, column=0, columnspan=2, padx=6, pady=8, sticky="e")
        tk.Button(btns, text="Analysieren", command=run).pack(side=tk.LEFT, padx=4)
        tk.Button(btns, text="Abbrechen", command=T.destroy).pack(side=tk.LEFT, padx=4)
        T.grab_set(); T.transient(self)

    def _review_and_apply_diff(self, current: dict, diff: dict, element_types: list[str], connection_types: list[str]):
        """Zeigt ein Review-Fenster für ein Add-only-Diff und erlaubt das Anwenden.
        Validiert vorab mit vpb_diff.validate_add_only_diff.
        """
        try:
            from vpb_diff import validate_add_only_diff  # type: ignore
        except Exception as e:
            messagebox.showerror("AI", f"Fehlende Diff-Module: {e}")
            return

        ok, err = (False, "Unbekannt")
        try:
            existing_ids = [e.get("element_id") for e in current.get("elements", []) if isinstance(e, dict)]
            ok, err = validate_add_only_diff(diff, existing_ids, element_types, connection_types)
        except Exception as ve:
            ok, err = False, f"Validierung fehlgeschlagen: {ve}"

        W = tk.Toplevel(self)
        W.title("Diff prüfen und anwenden…")
        W.geometry("720x520")

        # Kopfzeile mit Validierungsstatus
        head = tk.Frame(W)
        head.pack(side=tk.TOP, fill=tk.X, padx=8, pady=8)
        status_lbl = tk.Label(head, text=("Diff OK" if ok else f"Diff ungültig: {err}"), fg=("#0a0" if ok else "#b22222"))
        status_lbl.pack(side=tk.LEFT)

        # Zahlenübersicht
        try:
            els = diff.get("elements", []) if isinstance(diff, dict) else []
            cons = diff.get("connections", []) if isinstance(diff, dict) else []
            meta = f"Neue Elemente: {len(els)}   Neue Verbindungen: {len(cons)}"
        except Exception:
            meta = ""
        tk.Label(head, text=meta).pack(side=tk.RIGHT)

        # Pretty-JSON Anzeige
        body = tk.Frame(W)
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0,8))
        txt = tk.Text(body, wrap="none", font=("Consolas", 10))
        ysb = tk.Scrollbar(body, orient=tk.VERTICAL, command=txt.yview)
        xsb = tk.Scrollbar(body, orient=tk.HORIZONTAL, command=txt.xview)
        txt.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        txt.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        xsb.grid(row=1, column=0, sticky="we")
        body.rowconfigure(0, weight=1)
        body.columnconfigure(0, weight=1)
        import json as _json
        try:
            txt.insert("1.0", _json.dumps(diff, ensure_ascii=False, indent=2))
        except Exception:
            try:
                txt.insert("1.0", str(diff))
            except Exception:
                pass
        txt.configure(state="disabled")

        # Buttons
        btns = tk.Frame(W)
        btns.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=8)

        def do_apply():
            if not ok:
                if not messagebox.askyesno("Diff anwenden?", f"Die Validierung meldet einen Fehler:\n{err}\n\nTrotzdem anwenden?"):
                    return
            try:
                if not getattr(self, "_merge_manager", None):
                    self._merge_manager = MergeManager(self.canvas)
                from copy import deepcopy

                patch = deepcopy(diff)
                prev_elements = set(self.canvas.elements.keys())
                prev_connections = set(self.canvas.connections.keys())
                result: MergeResult = self._merge_manager.apply_add_only_patch(
                    patch,
                    auto_rename=getattr(self, "_auto_rename_enabled", True),
                )
                added_e = getattr(result, "added_elements", 0)
                added_c = getattr(result, "added_connections", 0)
                summary_lines_raw = result.summary_lines() if hasattr(result, "summary_lines") else []
                summary_lines = list(summary_lines_raw) if isinstance(summary_lines_raw, (list, tuple)) else []
                primary_line = f"AI Diff: {added_e} Elemente, {added_c} Verbindungen hinzugefügt"
                if summary_lines:
                    summary_lines[0] = primary_line
                else:
                    summary_lines = [primary_line]
                status_msg = f"AI-Diff angewendet (+{added_e}/+{added_c})"
                self.status.set(status_msg)
                if getattr(self, "chat_controller", None):
                    try:
                        self.chat_controller.append_merge_feedback(
                            "AI Diff",
                            {
                                "added_elements": result.added_elements,
                                "added_connections": result.added_connections,
                                "element_renames": getattr(result, "element_renames", {}),
                                "connection_renames": getattr(result, "connection_renames", {}),
                                "summary_lines": summary_lines,
                                "warnings": getattr(result, "warnings", []),
                            },
                        )
                    except Exception:
                        pass
                if getattr(result, "warnings", None):
                    try:
                        messagebox.showwarning("AI", "\n".join(str(w) for w in result.warnings))
                    except Exception:
                        pass
                try:
                    self._highlight_merge_changes(
                        prev_elements,
                        prev_connections,
                        element_renames=getattr(result, "element_renames", {}).values(),
                        connection_renames=getattr(result, "connection_renames", {}).values(),
                    )
                except Exception:
                    pass
                try:
                    W.destroy()
                except Exception:
                    pass
            except Exception as e:
                messagebox.showerror("AI", f"Fehler beim Anwenden: {e}")

        tk.Button(btns, text="Anwenden", command=do_apply).pack(side=tk.RIGHT, padx=6)
        tk.Button(btns, text="Schließen", command=W.destroy).pack(side=tk.RIGHT)
        W.grab_set(); W.transient(self)

    # ----- Metadaten & Export -----
    def _edit_metadata(self):
        md = dict(self.canvas.metadata or {})
        T = tk.Toplevel(self)
        T.title("Metadaten bearbeiten")
        tk.Label(T, text="Name:").grid(row=0, column=0, padx=6, pady=6, sticky="e")
        tk.Label(T, text="Beschreibung:").grid(row=1, column=0, padx=6, pady=6, sticky="ne")
        name_var = tk.StringVar(value=str(md.get("name", "VPB Prozess")))
        tk.Entry(T, textvariable=name_var, width=40).grid(row=0, column=1, padx=6, pady=6, sticky="we")
        txt_desc = tk.Text(T, width=40, height=6)
        txt_desc.grid(row=1, column=1, padx=6, pady=6, sticky="we")
        if md.get("description"):
            txt_desc.insert("1.0", str(md.get("description")))

        def ok():
            self.canvas.metadata["name"] = name_var.get()
            self.canvas.metadata["description"] = txt_desc.get("1.0", tk.END).strip()
            T.destroy()

        tk.Button(T, text="OK", command=ok).grid(row=2, column=0, padx=6, pady=8)
        tk.Button(T, text="Abbrechen", command=T.destroy).grid(row=2, column=1, padx=6, pady=8)
        T.grab_set()
        T.transient(self)

    def _export_pdf(self):
        path = filedialog.asksaveasfilename(
            title="Export als PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf"), ("Alle Dateien", "*.*")],
        )
        if not path:
            return

        try:
            bbox = self.canvas.bbox("all")
        except Exception:
            bbox = None

        if bbox and len(bbox) == 4:
            x0, y0, x1, y1 = bbox
            width = max(1, int(x1 - x0))
            height = max(1, int(y1 - y0))
        else:
            x0 = 0
            y0 = 0
            width = max(1, int(self.canvas.winfo_width()))
            height = max(1, int(self.canvas.winfo_height()))

        try:
            ps_data = self.canvas.postscript(
                colormode="color", x=int(x0), y=int(y0), width=int(width), height=int(height)
            )
        except Exception as exc:
            messagebox.showerror("Export-Fehler", f"Canvas konnte nicht exportiert werden: {exc}")
            return

        try:
            from PIL import EpsImagePlugin, Image
        except Exception as exc:
            messagebox.showerror("Export-Fehler", f"Pillow (PIL) ist nicht verfügbar: {exc}")
            return

        def _ensure_ghostscript() -> None:
            try:
                if sys.platform.startswith("win"):
                    if getattr(EpsImagePlugin, "gs_windows_binary", None):
                        return
                else:
                    if getattr(EpsImagePlugin, "gs_binary", None):
                        return
            except Exception:
                pass

            candidates: List[str] = []
            env_override = os.environ.get("GHOSTSCRIPT_BINARY") or os.environ.get("GHOSTSCRIPT_PATH")
            if env_override:
                candidates.append(env_override)
            if sys.platform.startswith("win"):
                candidates.extend(["gswin64c", "gswin32c"])
            else:
                candidates.append("gs")

            for candidate in candidates:
                if not candidate:
                    continue
                resolved = shutil.which(candidate)
                if not resolved and os.path.isfile(candidate):
                    resolved = candidate
                if not resolved:
                    continue
                try:
                    if sys.platform.startswith("win"):
                        EpsImagePlugin.gs_windows_binary = resolved
                    else:
                        EpsImagePlugin.gs_binary = resolved
                except Exception:
                    pass
                return

        def _postscript_to_image(data: str) -> Image.Image:
            buffer = io.BytesIO(data.encode("utf-8"))

            def _load() -> Image.Image:
                buffer.seek(0)
                image = Image.open(buffer)
                image.load()
                converted = image.convert("RGBA")
                image.close()
                return converted

            try:
                return _load()
            except OSError:
                _ensure_ghostscript()
                try:
                    return _load()
                except OSError as err:
                    raise RuntimeError(
                        "Ghostscript wird für den PDF-Export benötigt. Bitte installieren und den Pfad konfigurieren."
                    ) from err

        try:
            pil_image = _postscript_to_image(ps_data)
        except Exception as exc:
            messagebox.showerror("Export-Fehler", f"Grafik-Konvertierung fehlgeschlagen: {exc}")
            return

        try:
            process_data = self.canvas.to_dict()
        except Exception as exc:
            messagebox.showerror("Export-Fehler", f"Prozessdaten konnten nicht gelesen werden: {exc}")
            return

        try:
            render_process_pdf(pil_image, process_data, path, config=EXPORT_CONFIG)
        except Exception as exc:
            messagebox.showerror("Export-Fehler", f"PDF-Erstellung fehlgeschlagen: {exc}")
            return
        finally:
            try:
                pil_image.close()
            except Exception:
                pass

        try:
            self.status.set(f"PDF exportiert: {os.path.basename(path)}")
        except Exception:
            pass

    def _export_png(self):
        path = filedialog.asksaveasfilename(
            title="Export als PNG",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("Alle Dateien", "*.*")],
        )
        if not path:
            return

        try:
            bbox = self.canvas.bbox("all")
        except Exception:
            bbox = None

        if bbox and len(bbox) == 4:
            x0, y0, x1, y1 = bbox
            width = max(1, int(x1 - x0))
            height = max(1, int(y1 - y0))
        else:
            x0 = 0
            y0 = 0
            width = max(1, int(self.canvas.winfo_width()))
            height = max(1, int(self.canvas.winfo_height()))

        try:
            ps_data = self.canvas.postscript(
                colormode="color", x=int(x0), y=int(y0), width=int(width), height=int(height)
            )
        except Exception as exc:
            messagebox.showerror("Export-Fehler", f"Canvas konnte nicht exportiert werden: {exc}")
            return

        try:
            from PIL import EpsImagePlugin, Image
        except Exception as exc:
            messagebox.showerror("Export-Fehler", f"Pillow (PIL) ist nicht verfügbar: {exc}")
            return

        def _ensure_ghostscript() -> None:
            try:
                if sys.platform.startswith("win"):
                    if getattr(EpsImagePlugin, "gs_windows_binary", None):
                        return
                else:
                    if getattr(EpsImagePlugin, "gs_binary", None):
                        return
            except Exception:
                pass

            candidates: List[str] = []
            env_override = os.environ.get("GHOSTSCRIPT_BINARY") or os.environ.get("GHOSTSCRIPT_PATH")
            if env_override:
                candidates.append(env_override)
            if sys.platform.startswith("win"):
                candidates.extend(["gswin64c", "gswin32c"])
            else:
                candidates.append("gs")

            for candidate in candidates:
                if not candidate:
                    continue
                resolved = shutil.which(candidate)
                if not resolved and os.path.isfile(candidate):
                    resolved = candidate
                if not resolved:
                    continue
                try:
                    if sys.platform.startswith("win"):
                        EpsImagePlugin.gs_windows_binary = resolved
                    else:
                        EpsImagePlugin.gs_binary = resolved
                except Exception:
                    pass
                return

        def _postscript_to_image(data: str) -> Image.Image:
            buffer = io.BytesIO(data.encode("utf-8"))

            def _load() -> Image.Image:
                buffer.seek(0)
                image = Image.open(buffer)
                image.load()
                converted = image.convert("RGBA")
                image.close()
                return converted

            try:
                return _load()
            except OSError:
                _ensure_ghostscript()
                try:
                    return _load()
                except OSError as err:
                    raise RuntimeError(
                        "Ghostscript wird für den PNG-Export benötigt. Bitte installieren und den Pfad konfigurieren."
                    ) from err

        try:
            pil_image = _postscript_to_image(ps_data)
        except Exception as exc:
            messagebox.showerror("Export-Fehler", f"Grafik-Konvertierung fehlgeschlagen: {exc}")
            return

        try:
            pil_image.save(path, format="PNG")
        except Exception as exc:
            messagebox.showerror("Export-Fehler", f"PNG konnte nicht gespeichert werden: {exc}")
            return
        finally:
            try:
                pil_image.close()
            except Exception:
                pass

        try:
            self.status.set(f"PNG exportiert: {os.path.basename(path)}")
        except Exception:
            pass

    def _export_svg(self):
        path = filedialog.asksaveasfilename(
            title="Export als SVG",
            defaultextension=".svg",
            filetypes=[("SVG", "*.svg"), ("Alle Dateien", "*.*")],
        )
        if not path:
            return

        try:
            data = self.canvas.to_dict()
        except Exception as exc:
            messagebox.showerror("Export-Fehler", f"Prozessdaten konnten nicht gelesen werden: {exc}")
            return

        try:
            svg_text = render_process_svg(data)
        except Exception as exc:
            messagebox.showerror("Export-Fehler", f"SVG konnte nicht erzeugt werden: {exc}")
            return

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(svg_text)
        except Exception as exc:
            messagebox.showerror("Export-Fehler", f"SVG konnte nicht gespeichert werden: {exc}")
            return

        try:
            self.status.set(f"SVG exportiert: {os.path.basename(path)}")
        except Exception:
            pass

    def _export_ps(self):
        path = filedialog.asksaveasfilename(
            title="Export als PostScript",
            defaultextension=".ps",
            filetypes=[("PostScript", "*.ps"), ("Alle Dateien", "*.*")]
        )
        if not path:
            return
        # Canvas postscript Export
        try:
            # bbox der Inhalte bestimmen
            xs, ys, xe, ye = 0, 0, self.canvas.winfo_width(), self.canvas.winfo_height()
            ps = self.canvas.postscript(colormode='color', x=xs, y=ys, width=xe, height=ye)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(ps)
            self.status.set(f"Exportiert: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Export-Fehler", str(e))


class HierarchyManagerDialog(tk.Toplevel):
    def __init__(self, master: tk.Misc, categories: Iterable[Dict[str, object]]):
        super().__init__(master)
        self.title("Hierarchien verwalten")
        self.transient(master)
        self.resizable(False, False)
        self.configure(padx=12, pady=10)
        self.result: Optional[List[Dict[str, object]]] = None
        self.selected_index: Optional[int] = None
        self._loading_fields: bool = False
        self._selected_index: Optional[int] = None

        def _fmt(value: object) -> str:
            try:
                if isinstance(value, (int, float)):
                    return str(float(value)).rstrip("0").rstrip(".")
                return str(value or "")
            except Exception:
                return str(value or "")

        self._format_value = _fmt  # reuse helper outside of __init__
        self._categories: List[Dict[str, str]] = []
        for cat in categories:
            if not isinstance(cat, dict):
                continue
            self._categories.append(
                {
                    "name": str(cat.get("name", "") or ""),
                    "color": str(cat.get("color", "") or ""),
                    "y0": _fmt(cat.get("y0", 0.0)),
                    "y1": _fmt(cat.get("y1", 0.0)),
                }
            )

        tk.Label(
            self,
            text="Hierarchie-Bänder hinzufügen, bearbeiten, löschen oder sortieren.",
            anchor="w",
        ).pack(fill=tk.X, pady=(0, 10))

        main = tk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True)

        left = tk.Frame(main)
        left.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 12))

        self._listbox = tk.Listbox(left, exportselection=False, height=12)
        self._listbox.pack(fill=tk.BOTH, expand=True)
        self._listbox.bind("<<ListboxSelect>>", self._on_select)

        list_btns = tk.Frame(left)
        list_btns.pack(fill=tk.X, pady=(8, 4))
        tk.Button(list_btns, text="Neu", command=self._add_category).pack(side=tk.LEFT)
        tk.Button(list_btns, text="Duplizieren", command=self._duplicate_category).pack(side=tk.LEFT, padx=(4, 0))
        tk.Button(list_btns, text="Löschen", command=self._delete_category).pack(side=tk.LEFT, padx=(4, 0))

        reorder_btns = tk.Frame(left)
        reorder_btns.pack(fill=tk.X)
        tk.Button(reorder_btns, text="Nach oben", command=lambda: self._move_category(-1)).pack(side=tk.LEFT)
        tk.Button(reorder_btns, text="Nach unten", command=lambda: self._move_category(1)).pack(side=tk.LEFT, padx=(4, 0))

        details = tk.LabelFrame(main, text="Details", padx=10, pady=8)
        details.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        details.columnconfigure(1, weight=1)

        self.var_name = tk.StringVar()
        self.var_color = tk.StringVar()
        self.var_y0 = tk.StringVar()
        self.var_y1 = tk.StringVar()

        self._field_map = {
            "name": self.var_name,
            "color": self.var_color,
            "y0": self.var_y0,
            "y1": self.var_y1,
        }
        for key, var in self._field_map.items():
            var.trace_add("write", lambda *_args, field=key: self._on_field_change(field))

        tk.Label(details, text="Name:").grid(row=0, column=0, sticky="e", pady=3)
        entry_name = tk.Entry(details, textvariable=self.var_name, width=26)
        entry_name.grid(row=0, column=1, sticky="we", pady=3)

        tk.Label(details, text="Farbe (#RRGGBB):").grid(row=1, column=0, sticky="e", pady=3)
        color_row = tk.Frame(details)
        color_row.grid(row=1, column=1, sticky="we", pady=3)
        color_row.columnconfigure(0, weight=1)
        entry_color = tk.Entry(color_row, textvariable=self.var_color)
        entry_color.grid(row=0, column=0, sticky="we")
        btn_color = tk.Button(color_row, text="Wählen", command=self._choose_color)
        btn_color.grid(row=0, column=1, padx=(6, 0))

        tk.Label(details, text="Y-Beginn:").grid(row=2, column=0, sticky="e", pady=3)
        entry_y0 = tk.Entry(details, textvariable=self.var_y0)
        entry_y0.grid(row=2, column=1, sticky="we", pady=3)

        tk.Label(details, text="Y-Ende:").grid(row=3, column=0, sticky="e", pady=3)
        entry_y1 = tk.Entry(details, textvariable=self.var_y1)
        entry_y1.grid(row=3, column=1, sticky="we", pady=3)

        self._detail_widgets = [entry_name, entry_color, btn_color, entry_y0, entry_y1]

        bottom = tk.Frame(self)
        bottom.pack(fill=tk.X, pady=(12, 0))
        tk.Button(bottom, text="Abbrechen", command=self._on_cancel).pack(side=tk.RIGHT, padx=(6, 0))
        tk.Button(bottom, text="OK", command=self._on_ok).pack(side=tk.RIGHT)

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Escape>", self._on_cancel)

        self._refresh_listbox()
        self._set_detail_state(bool(self._categories))
        self.grab_set()
        self.after(80, lambda: self._listbox.focus_set())

    def _set_detail_state(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        for widget in self._detail_widgets:
            try:
                widget.configure(state=state)
            except Exception:
                pass

    def _refresh_listbox(self, select: Optional[int] = None) -> None:
        self._listbox.delete(0, tk.END)
        for cat in self._categories:
            self._listbox.insert(tk.END, self._format_summary(cat))
        if not self._categories:
            self._selected_index = None
            self.selected_index = None
            self._clear_fields()
            self._set_detail_state(False)
            return
        if select is None:
            select = self._selected_index if self._selected_index is not None else 0
        select = max(0, min(select, len(self._categories) - 1))
        self._listbox.selection_set(select)
        self._listbox.activate(select)
        self._listbox.see(select)
        self._selected_index = select
        self.selected_index = select
        self._load_fields(select)
        self._set_detail_state(True)

    def _format_summary(self, cat: Dict[str, str]) -> str:
        name = str(cat.get("name", "") or "–")
        y0 = str(cat.get("y0", "") or "0")
        y1 = str(cat.get("y1", "") or "0")
        return f"{name} ({y0} – {y1})"

    def _clear_fields(self) -> None:
        self._loading_fields = True
        self.var_name.set("")
        self.var_color.set("")
        self.var_y0.set("")
        self.var_y1.set("")
        self._loading_fields = False

    def _load_fields(self, index: int) -> None:
        if index < 0 or index >= len(self._categories):
            self._clear_fields()
            return
        cat = self._categories[index]
        self._loading_fields = True
        self.var_name.set(cat.get("name", ""))
        self.var_color.set(cat.get("color", ""))
        self.var_y0.set(cat.get("y0", ""))
        self.var_y1.set(cat.get("y1", ""))
        self._loading_fields = False
        self.selected_index = index

    def _on_select(self, event) -> None:
        cur = self._listbox.curselection()
        if not cur:
            self._selected_index = None
            self.selected_index = None
            self._clear_fields()
            self._set_detail_state(False)
            return
        idx = int(cur[0])
        self._selected_index = idx
        self._load_fields(idx)
        self._set_detail_state(True)

    def _on_field_change(self, field: str) -> None:
        if self._loading_fields:
            return
        idx = self._selected_index
        if idx is None or idx < 0 or idx >= len(self._categories):
            return
        value = self._field_map[field].get()
        self._categories[idx][field] = value
        self._update_listbox_entry(idx)

    def _update_listbox_entry(self, index: int) -> None:
        if index < 0 or index >= len(self._categories):
            return
        label = self._format_summary(self._categories[index])
        self._listbox.delete(index)
        self._listbox.insert(index, label)
        self._listbox.selection_set(index)
        self._listbox.activate(index)

    def _generate_unique_name(self, base: str) -> str:
        existing = {str(cat.get("name", "")) for cat in self._categories}
        if base not in existing:
            return base
        suffix = 2
        while True:
            candidate = f"{base} {suffix}"
            if candidate not in existing:
                return candidate
            suffix += 1

    def _add_category(self) -> None:
        template = None
        if self._selected_index is not None and 0 <= self._selected_index < len(self._categories):
            template = self._categories[self._selected_index]
        color = template.get("color", "#f2f2f2") if template else "#f2f2f2"
        try:
            base_start = float(str(template.get("y1", 0.0)).replace(",", ".")) if template else None
        except Exception:
            base_start = None
        if base_start is None and self._categories:
            try:
                base_start = float(str(self._categories[-1].get("y1", 0.0)).replace(",", "."))
            except Exception:
                base_start = 0.0
        if base_start is None:
            base_start = 0.0
        y0 = base_start
        y1 = base_start + 200.0
        new_cat = {
            "name": self._generate_unique_name("Neues Band"),
            "color": color,
            "y0": self._format_value(y0),
            "y1": self._format_value(y1),
        }
        insert_at = self._selected_index + 1 if self._selected_index is not None else len(self._categories)
        self._categories.insert(insert_at, new_cat)
        self._refresh_listbox(select=insert_at)

    def _duplicate_category(self) -> None:
        idx = self._selected_index
        if idx is None or idx < 0 or idx >= len(self._categories):
            return
        source = dict(self._categories[idx])
        base_name = (source.get("name") or "Neues Band").strip()
        source["name"] = self._generate_unique_name(f"{base_name} Kopie")
        insert_at = idx + 1
        self._categories.insert(insert_at, source)
        self._refresh_listbox(select=insert_at)

    def _delete_category(self) -> None:
        idx = self._selected_index
        if idx is None or idx < 0 or idx >= len(self._categories):
            return
        if not messagebox.askyesno(
            "Hierarchie löschen",
            "Soll das ausgewählte Hierarchieband entfernt werden?",
            parent=self,
        ):
            return
        del self._categories[idx]
        next_index = min(idx, len(self._categories) - 1) if self._categories else None
        self._refresh_listbox(select=next_index)

    def _move_category(self, offset: int) -> None:
        idx = self._selected_index
        if idx is None:
            return
        target = idx + offset
        if target < 0 or target >= len(self._categories):
            return
        self._categories[idx], self._categories[target] = self._categories[target], self._categories[idx]
        self._refresh_listbox(select=target)

    def _choose_color(self) -> None:
        current = self.var_color.get() or "#ffffff"
        try:
            _, hex_color = colorchooser.askcolor(initialcolor=current, parent=self)
        except Exception:
            hex_color = None
        if hex_color:
            self.var_color.set(str(hex_color))

    def _validate_and_normalize(self) -> List[Dict[str, object]]:
        normalized: List[Dict[str, object]] = []
        seen: set[str] = set()
        for i, cat in enumerate(self._categories):
            name = str(cat.get("name", "")).strip()
            if not name:
                raise ValueError(f"Eintrag {i + 1}: Name fehlt.")
            if name in seen:
                raise ValueError(f"Eintrag {i + 1}: Name {name!r} wird mehrfach verwendet.")
            seen.add(name)
            color = str(cat.get("color", "")).strip() or "#f2f2f2"
            if color and not re.fullmatch(r"#([0-9a-fA-F]{6})", color):
                raise ValueError(f"Eintrag {i + 1}: Ungültige Farbe {color!r}. Erwartet #RRGGBB.")
            try:
                y0 = float(str(cat.get("y0", 0.0)).replace(",", ".") or 0.0)
                y1 = float(str(cat.get("y1", 0.0)).replace(",", ".") or 0.0)
            except Exception:
                raise ValueError(f"Eintrag {i + 1}: Y-Werte müssen numerisch sein.")
            if y1 < y0:
                y0, y1 = y1, y0
            normalized.append({"name": name, "color": color, "y0": y0, "y1": y1})
        return normalized

    def _on_ok(self, event=None) -> None:
        try:
            normalized = self._validate_and_normalize()
        except ValueError as exc:
            messagebox.showerror("Hierarchien", str(exc), parent=self)
            return
        self.result = normalized
        if self._selected_index is not None and 0 <= self._selected_index < len(normalized):
            self.selected_index = self._selected_index
        else:
            self.selected_index = None if not normalized else 0
        self.destroy()

    def _on_cancel(self, event=None) -> None:
        self.result = None
        self.selected_index = None
        self.destroy()


class HierarchyCategoryDialog(tk.Toplevel):
    def __init__(self, master: tk.Misc, category: Dict[str, object]):
        super().__init__(master)
        self.title("Hierarchieband bearbeiten")
        self.transient(master)
        self.resizable(False, False)
        self.configure(padx=12, pady=10)
        self.result: Optional[Dict[str, object]] = None

        def _fmt(value: object) -> str:
            try:
                return str(float(value)).rstrip("0").rstrip(".") if isinstance(value, (int, float)) else str(value or "")
            except Exception:
                return str(value or "")

        name = str(category.get("name", "") or "")
        color = str(category.get("color", "") or "")
        y0 = _fmt(category.get("y0", 0.0) or 0.0)
        y1 = _fmt(category.get("y1", 0.0) or 0.0)

        self.var_name = tk.StringVar(value=name)
        self.var_color = tk.StringVar(value=color)
        self.var_y0 = tk.StringVar(value=y0)
        self.var_y1 = tk.StringVar(value=y1)

        tk.Label(self, text="Name:").grid(row=0, column=0, sticky="e", pady=(0, 6))
        entry_name = tk.Entry(self, textvariable=self.var_name, width=28)
        entry_name.grid(row=0, column=1, sticky="we", pady=(0, 6))

        tk.Label(self, text="Farbe (#RRGGBB):").grid(row=1, column=0, sticky="e", pady=(0, 6))
        color_frame = tk.Frame(self)
        color_frame.grid(row=1, column=1, sticky="we", pady=(0, 6))
        color_frame.columnconfigure(0, weight=1)
        entry_color = tk.Entry(color_frame, textvariable=self.var_color)
        entry_color.grid(row=0, column=0, sticky="we")
        tk.Button(color_frame, text="Wählen", command=self._choose_color).grid(row=0, column=1, padx=(6, 0))

        tk.Label(self, text="Y-Beginn:").grid(row=2, column=0, sticky="e", pady=(0, 6))
        tk.Entry(self, textvariable=self.var_y0).grid(row=2, column=1, sticky="we", pady=(0, 6))

        tk.Label(self, text="Y-Ende:").grid(row=3, column=0, sticky="e", pady=(0, 6))
        tk.Entry(self, textvariable=self.var_y1).grid(row=3, column=1, sticky="we", pady=(0, 6))

        btns = tk.Frame(self)
        btns.grid(row=4, column=0, columnspan=2, pady=(8, 0), sticky="e")
        tk.Button(btns, text="Abbrechen", command=self._on_cancel).pack(side=tk.RIGHT, padx=(6, 0))
        tk.Button(btns, text="OK", command=self._on_ok).pack(side=tk.RIGHT)

        self.columnconfigure(1, weight=1)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.bind("<Return>", self._on_ok)
        self.bind("<Escape>", self._on_cancel)
        self.grab_set()
        self.after(50, lambda: entry_name.focus_set())

    def _choose_color(self) -> None:
        current = self.var_color.get() or "#ffffff"
        try:
            _, hex_color = colorchooser.askcolor(initialcolor=current, parent=self)
        except Exception:
            hex_color = None
        if hex_color:
            self.var_color.set(str(hex_color))

    def _on_ok(self, event=None) -> None:
        name = self.var_name.get().strip()
        if not name:
            messagebox.showerror("Hierarchie", "Bitte einen Namen angeben.", parent=self)
            return
        color = self.var_color.get().strip() or "#f2f2f2"
        if color and not re.fullmatch(r"#([0-9a-fA-F]{6})", color):
            messagebox.showerror("Hierarchie", "Ungültige Farbe. Erwartet wird #RRGGBB.", parent=self)
            return
        try:
            y0 = float(self.var_y0.get().replace(",", ".") or 0.0)
            y1 = float(self.var_y1.get().replace(",", ".") or 0.0)
        except Exception:
            messagebox.showerror("Hierarchie", "Y-Werte müssen numerisch sein.", parent=self)
            return
        self.result = {"name": name, "color": color, "y0": y0, "y1": y1}
        self.destroy()

    def _on_cancel(self, event=None) -> None:
        self.result = None
        self.destroy()

def main():
    import argparse
    # Globaler Exception-Handler für bessere Diagnose (Konsole + Datei)
    def _log_exception(exc_type, exc, tb):
        try:
            err = "\n".join(traceback.format_exception(exc_type, exc, tb))
            sys.stderr.write(err + "\n")
            with open(os.path.join(os.getcwd(), "last_exception.log"), "w", encoding="utf-8") as f:
                f.write(err)
        except Exception:
            pass
    try:
        sys.excepthook = _log_exception
    except Exception:
        pass

    # Argumente parsen
    parser = argparse.ArgumentParser(description="VPB Process Designer")
    parser.add_argument('files', nargs='*', help='VPB JSON-Dateien (*.json, *.vpb.json), erste wird beim Start geladen')
    parser.add_argument('--fit', action='store_true', help='Nach dem Laden auf das Diagramm zoomen (Fit-to-Diagram)')
    parser.add_argument('--grid', dest='grid', action='store_true', help='Grid anzeigen')
    parser.add_argument('--no-grid', dest='grid', action='store_false', help='Grid ausblenden')
    parser.set_defaults(grid=None)
    parser.add_argument('--snap', dest='snap', action='store_true', help='Snap-to-Grid aktivieren')
    parser.add_argument('--no-snap', dest='snap', action='store_false', help='Snap-to-Grid deaktivieren')
    parser.set_defaults(snap=None)
    parser.add_argument('--routing', choices=['straight', 'orthogonal', 'curved', 'smart'], help='Routing-Stil setzen')
    parser.add_argument('--time-axis', choices=['on', 'off'], help='Zeitachse ein-/ausblenden')
    parser.add_argument('--zoom', type=float, help='Zoom-Faktor setzen (z.B. 1.0)')
    parser.add_argument('--pan', type=float, nargs=2, metavar=('X', 'Y'), help='Viewport-Ursprung in Model-Koordinaten setzen (X Y)')
    parser.add_argument('--tab', choices=['diagram', 'code'], help='Start-Tab auswählen')
    args = parser.parse_args()

    try:
        print("[VPB] Starte Anwendung…")
        app = VPBDesignerApp()
        print("[VPB] Hauptfenster erstellt – entering mainloop")
        # Startparameter anwenden
        try:
            # Datei laden (erste)
            if getattr(args, 'files', None):
                first = args.files[0]
                if first and os.path.exists(first):
                    app._load_file(first)
            # Grid
            if args.grid is not None:
                try:
                    app._grid_var.set(bool(args.grid))
                    app._toggle_grid()
                except Exception:
                    pass
            # Snap
            if args.snap is not None:
                try:
                    app._snap_var.set(bool(args.snap))
                    app._toggle_snap()
                except Exception:
                    pass
            # Routing
            if getattr(args, 'routing', None):
                try:
                    app._route_var.set(args.routing)
                    app._apply_routing_style()
                except Exception:
                    pass
            # Zeitachse
            if getattr(args, 'time_axis', None) in ('on', 'off'):
                try:
                    app._time_axis_var.set(args.time_axis == 'on')
                    app._toggle_time_axis()
                except Exception:
                    pass
            # Zoom (relativ auf aktuellen View)
            if isinstance(getattr(args, 'zoom', None), float) and args.zoom > 0:
                try:
                    current = float(app.canvas.view_scale or 1.0)
                    factor = max(0.05, min(20.0, args.zoom)) / max(1e-6, current)
                    if abs(factor - 1.0) > 1e-6:
                        app.canvas.zoom_at_view(factor)
                except Exception:
                    pass
            # Pan (Viewport-Ursprung in Model-Koordinaten)
            if getattr(args, 'pan', None) and len(args.pan) == 2:
                try:
                    app.canvas.set_view_origin_model(float(args.pan[0]), float(args.pan[1]))
                except Exception:
                    pass
            # Fit-to-Diagram (nach evtl. Load)
            if getattr(args, 'fit', False):
                try:
                    app.canvas.fit_to_diagram()
                except Exception:
                    pass
            # Start-Tab
            if getattr(args, 'tab', None) in ('diagram', 'code'):
                try:
                    wanted = 'Diagramm' if args.tab == 'diagram' else 'Code'
                    nb = app._mid_notebook
                    for t in nb.tabs():
                        if nb.tab(t, 'text') == wanted:
                            nb.select(t)
                            break
                except Exception:
                    pass
            # Wenn weder --pan noch --fit angegeben wurde, Zeitachse vertikal zentrieren
            try:
                no_pan = not (getattr(args, 'pan', None) and len(args.pan) == 2)
                no_fit = not bool(getattr(args, 'fit', False))
                if no_pan and no_fit:
                    # nach kurzem Delay, damit Größen feststehen
                    app.after(120, lambda: app.canvas.center_time_axis_vertical())
            except Exception:
                pass
        except Exception:
            pass
        app.mainloop()
        print("[VPB] Anwendung beendet (Exit 0)")
    except Exception:
        _log_exception(*sys.exc_info())
        # Sicherstellen, dass ein Fehlcode zurückgegeben wird
        sys.exit(1)


if __name__ == "__main__":
    main()
else:
    pass

