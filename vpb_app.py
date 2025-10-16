#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VPB Process Designer 0.2.0-alpha - Refactored"""

import sys
import os
import json
import argparse
import tkinter as tk
from tkinter import ttk
from vpb.infrastructure.event_bus import EventBus
from vpb.infrastructure.settings_manager import SettingsManager
from vpb.services.document_service import DocumentService
from vpb.services.validation_service import ValidationService
from vpb.services.export_service import ExportService
from vpb.services.layout_service import LayoutService
from vpb.services.ai_service import AIService
from vpb.views.main_window import create_main_window
from vpb.views.menu_bar import create_menu_bar
from vpb.views.toolbar import create_toolbar
from vpb.views.status_bar import create_status_bar
from vpb.views.canvas_view import create_canvas_view
from vpb.views.palette_view import create_palette_view
from vpb.views.properties_view import create_properties_view
from vpb.views.dialogs.about_dialog import create_about_dialog
from vpb.views.dialogs.settings_dialog import create_settings_dialog
from vpb.controllers.document_controller import DocumentController
from vpb.controllers.element_controller import ElementController
from vpb.controllers.connection_controller import ConnectionController
from vpb.controllers.layout_controller import LayoutController
from vpb.controllers.validation_controller import ValidationController
from vpb.controllers.ai_controller import AIController
from vpb.controllers.export_controller import ExportController
from vpb.services.code_sync_service import CodeSyncService

class VPBApplication:
    def __init__(self, args=None):
        """
        Initialisiert die VPB Application.
        
        Args:
            args: Argparse Namespace mit CLI-Argumenten
        """
        self.args = args or argparse.Namespace()
        self.event_bus = EventBus()
        self.settings_manager = SettingsManager("settings.json")
        
        # Ollama Settings (für Chat)
        self._ollama_endpoint = "http://localhost:11434"
        self._ollama_model = "llama3.2"
        self._ollama_temperature = 0.7
        self._ollama_num_predict = 2048
        
        self._init_services()
        self.root = create_main_window(self.event_bus)
        self.root.title("VPB Process Designer 0.2.0-alpha")
        self.root.geometry("1400x900")
        self._init_views()
        self._init_controllers()
        self._subscribe_to_events()
        
        # Debug: Auto-load file wenn angegeben
        if hasattr(self.args, 'load') and self.args.load:
            self._debug_load_file(self.args.load)
        else:
            self.event_bus.publish("document:new")
        
        print("✅ VPB Process Designer 0.2.0-alpha gestartet")
        
        # Debug: Auto-actions nach GUI-Initialisierung
        if hasattr(self.args, 'debug') and self.args.debug:
            self.root.after(500, self._run_debug_actions)
    
    def _debug_load_file(self, file_path):
        """Debug: Lädt eine Datei beim Start."""
        print(f"🔧 DEBUG: Auto-loading file: {file_path}")
        if os.path.exists(file_path):
            self.event_bus.publish("ui:menu:file:open", {"file_path": file_path})
        else:
            print(f"❌ DEBUG: File not found: {file_path}")
    
    def _run_debug_actions(self):
        """Führt Debug-Actions aus (nach GUI-Init)."""
        print("🔧 DEBUG MODE: Aktiv")
        
        # Koordinatenursprung vertikal mittig setzen (y=0 in Mitte)
        # WICHTIG: Nach GUI-Init aufrufen, damit Canvas-Dimensionen bekannt sind
        if hasattr(self, 'canvas'):
            self.root.update_idletasks()  # GUI updaten
            self.canvas.center_time_axis_vertical()
        
        if hasattr(self.args, 'validate') and self.args.validate:
            print("🔧 DEBUG: Running validation...")
            self.event_bus.publish("ui:menu:tools:validate", {})
        
        if hasattr(self.args, 'export') and self.args.export:
            print(f"🔧 DEBUG: Exporting to {self.args.export}...")
            format_type = self.args.export.split('.')[-1].lower()
            self.event_bus.publish("ui:menu:file:export", {"format": format_type})
        
        if hasattr(self.args, 'info') and self.args.info:
            self._debug_print_canvas_info()
    
    def _init_services(self):
        self.document_service = DocumentService()
        self.validation_service = ValidationService()
        self.export_service = ExportService()
        self.layout_service = LayoutService()
        self.code_sync_service = CodeSyncService()
        try:
            self.ai_service = AIService()
        except:
            self.ai_service = None
    
    def _init_views(self):
        # Menu Bar
        self.menu_bar = create_menu_bar(self.root, self.event_bus)
        self.root.config(menu=self.menu_bar.menubar)
        
        # Main Container
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Toolbar (packt sich selbst)
        self.toolbar = create_toolbar(main_container, self.event_bus)
        
        # Vertical Split: Content Area (oben) + Chat Terminal (unten)
        self.vertical_paned = tk.PanedWindow(main_container, orient=tk.VERTICAL, sashwidth=5)
        self.vertical_paned.pack(fill=tk.BOTH, expand=True)
        
        # Oberer Bereich: 3-Spalten Layout
        content_area = tk.Frame(self.vertical_paned)
        self.vertical_paned.add(content_area, minsize=400)
        
        # PanedWindow für 3 Spalten
        self.paned_window = tk.PanedWindow(content_area, orient=tk.HORIZONTAL, sashwidth=5)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Linke Spalte: Palette (Sidebar mit fester Mindestbreite)
        self.palette_view = create_palette_view(self.paned_window, self.event_bus)
        self.palette_view.pack(fill=tk.BOTH, expand=True)
        self.paned_window.add(self.palette_view, minsize=250, width=250, stretch='never')
        
        # Palette-Daten laden
        self._load_palette_data()
        
        # Mittlere Spalte: Notebook mit Canvas/Code/XML Tabs (expandiert beim Fenster vergrößern)
        self.mid_notebook = ttk.Notebook(self.paned_window)
        self.paned_window.add(self.mid_notebook, minsize=400, stretch='always')
        
        # Rechte Spalte: Vertikales PanedWindow für Properties und MiniMap (Sidebar mit fester Mindestbreite)
        self.right_paned = tk.PanedWindow(self.paned_window, orient=tk.VERTICAL, sashwidth=5)
        self.paned_window.add(self.right_paned, minsize=250, width=300, stretch='never')
        
        # oberes Notebook: MiniMap  
        self.minimap_notebook = ttk.Notebook(self.right_paned)
        self.right_paned.add(self.minimap_notebook, minsize=150)
        
        self.minimap_frame = tk.Frame(self.minimap_notebook, bg="#fafafa")
        self.minimap_notebook.add(self.minimap_frame, text="Übersicht")
       
        # unteres Notebook: Properties
        self.properties_notebook = ttk.Notebook(self.right_paned)
        self.right_paned.add(self.properties_notebook, minsize=200)
        
        self.properties_view = create_properties_view(self.properties_notebook, self.event_bus)
        self.properties_notebook.add(self.properties_view, text="Eigenschaften")
        
        # JETZT Mittlere Spalte Tabs erstellen (nachdem minimap_frame existiert)
        # Tab 1: Canvas (Diagramm) - mit Linealen und Hierarchie
        self._create_diagram_tab()
        
        # Tab 2: JSON Code
        self.json_frame = tk.Frame(self.mid_notebook)
        self.mid_notebook.add(self.json_frame, text="JSON Code")
        self._create_code_tab(self.json_frame, "json")
        
        # Tab 3: XML Code
        self.xml_frame = tk.Frame(self.mid_notebook)
        self.mid_notebook.add(self.xml_frame, text="XML Code")
        self._create_code_tab(self.xml_frame, "xml")
        
        # Unterer Bereich: AI Chat Terminal
        self._init_chat_terminal(self.vertical_paned)
        
        # Status Bar (packt sich selbst, braucht KEINEN event_bus)
        self.status_bar = create_status_bar(main_container)
    
    def _init_chat_terminal(self, parent):
        """Initialisiert den AI Chat Terminal."""
        from vpb.ui.chat_console import create_chat_console
        from vpb.ui.chat_controller import ChatController
        
        # Chat Terminal Container
        chat_frame = tk.Frame(parent)
        parent.add(chat_frame, minsize=150, height=200)
        
        # Chat Controller erstellen (mit self statt self.root)
        self.chat_controller = ChatController(self)
        
        # Chat Console erstellen
        self.chat_container, self.chat_panel, self.task_manager = create_chat_console(
            self.root,
            chat_frame,
            on_send=self.chat_controller.handle_send,
            on_stop=self.chat_controller.handle_stop,
            on_attach=self.chat_controller.handle_attach,
        )
        
        # Controller mit UI verbinden
        self.chat_controller.bind_ui(self.chat_panel, self.task_manager)
    
    def _create_diagram_tab(self):
        """Erstellt den Diagramm-Tab mit Canvas, Linealen und Hierarchie."""
        from vpb.ui.diagram_tab import add_diagram_tab
        from vpb.ui.canvas_interactions import configure_canvas_interactions
        from vpb.ui.canvas import MiniMapCanvas
        
        # Diagramm-Tab mit vollständigem Canvas-Setup erstellen
        components = add_diagram_tab(self.mid_notebook)
        
        # Komponenten extrahieren
        self.diagram_frame = components[0]  # Frame
        self.canvas = components[1]         # VPBCanvas
        self.ruler_x = components[2]        # Horizontales Lineal
        self.ruler_y = components[3]        # Vertikales Lineal
        self.hier_canvas = components[4]    # Hierarchie-Canvas
        self.x_scroll = components[5]       # Horizontale Scrollbar
        self.y_scroll = components[6]       # Vertikale Scrollbar
        
        # Lineale mit Canvas verbinden
        self.ruler_x.attach(self.canvas)
        self.ruler_y.attach(self.canvas)
        
        # MiniMap im rechten Notebook-Tab erstellen
        self.minimap = MiniMapCanvas(self.minimap_frame, height=400)
        self.minimap.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.minimap.attach(self.canvas)
        
        # Canvas-Interaktionen konfigurieren (WICHTIG: self, nicht self.root!)
        configure_canvas_interactions(self, self.canvas, self.x_scroll, self.y_scroll)
        
        # Canvas Status-Callback setzen
        self.canvas.set_status_callback(self._on_canvas_status)
        
        # Canvas Selection-Callback für Properties Panel setzen
        self.canvas.on_selection_changed = self._on_canvas_selection
        
        # Grid anzeigen und Canvas initial zeichnen
        self.canvas.grid_visible = True
        
        # Canvas initial zeichnen
        self.canvas.redraw_all()
        
        # Lineale initial zeichnen
        self.ruler_x.redraw()
        self.ruler_y.redraw()
        
        # Koordinatenursprung vertikal mittig setzen (y=0 in Mitte)
        # WICHTIG: Nach GUI-Initialisierung aufrufen, damit Canvas-Größe bekannt ist
        # Wird in run() nach mainloop-Start aufgerufen
        
        print("✅ Canvas mit Linealen und Hierarchie erstellt")
    
    def _load_palette_data(self):
        """Lädt Palette-Daten aus default_palette.json."""
        try:
            palette_path = os.path.join(os.getcwd(), "palettes", "default_palette.json")
            if os.path.exists(palette_path):
                with open(palette_path, "r", encoding="utf-8") as f:
                    palette_data = json.load(f)
                    categories = palette_data.get("categories", [])
                    self.palette_view.load_categories(categories)
                    print(f"✅ Palette geladen: {len(categories)} Kategorien")
            else:
                print(f"⚠️ Palette nicht gefunden: {palette_path}")
        except Exception as e:
            print(f"❌ Fehler beim Laden der Palette: {e}")
    
    def _create_code_tab(self, parent, code_type):
        """Erstellt einen Code-Viewer Tab mit Syntax-Highlighting und Sync."""
        from vpb.ui.rich_code_editor import RichCodeEditor
        
        # Erstelle Rich Code Editor mit Callbacks
        if code_type == "json":
            on_refresh = lambda: self._refresh_json_from_canvas()
            on_apply = lambda: self._apply_json_to_canvas()
        else:  # xml
            on_refresh = lambda: self._refresh_xml_from_canvas()
            on_apply = lambda: self._apply_xml_to_canvas()
        
        editor = RichCodeEditor(
            parent, 
            language=code_type.lower(),
            on_refresh=on_refresh,
            on_apply=on_apply
        )
        editor.pack(fill=tk.BOTH, expand=True)
        
        # Speichere Referenz
        if code_type == "json":
            self.json_editor = editor
            self.json_text = editor.text  # Kompatibilität mit bestehendem Code
        else:
            self.xml_editor = editor
            self.xml_text = editor.text  # Kompatibilität mit bestehendem Code
        
        # Initial Content
        editor.set_text(f"# {code_type.upper()} Code wird hier angezeigt\n# Klicken Sie 🔄 Refresh um Canvas-Daten zu laden...")

    
    def _init_controllers(self):
        self.document_controller = DocumentController(self.event_bus, self.document_service)
        self.element_controller = ElementController(self.event_bus)
        self.connection_controller = ConnectionController(self.event_bus)
        self.layout_controller = LayoutController(self.event_bus, self.layout_service)
        self.validation_controller = ValidationController(self.event_bus, self.validation_service)
        self.export_controller = ExportController(self.event_bus, self.export_service)
        if self.ai_service:
            self.ai_controller = AIController(self.event_bus, self.ai_service)
        
        # Canvas-Referenz an Controller übergeben
        if hasattr(self, 'canvas'):
            self.element_controller.set_canvas(self.canvas)
            self.document_controller.set_canvas(self.canvas)  # Für Legacy-Kompatibilität
    
    def _subscribe_to_events(self):
        self.event_bus.subscribe("app:exit", self._on_exit)
        self.event_bus.subscribe("ui:help:about", self._on_show_about)
        self.event_bus.subscribe("ui:settings:show", self._on_show_settings)
        self.event_bus.subscribe("ui:request:file_path", self._on_file_dialog_requested)
        self.event_bus.subscribe("ui:error", self._on_show_error)
        self.event_bus.subscribe("ui:info", self._on_show_info)
        
        # Event-Bridge: ui:action:* → Legacy Events
        # MenuBar/Toolbar publizieren ui:action:*, Controller erwarten ui:menu:*
        self._setup_action_bridge()
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)
    
    def _setup_action_bridge(self):
        """
        Event-Bridge: Übersetzt ui:action:* Events zu Legacy-Events.
        MenuBar und Toolbar publizieren ui:action:*, aber Controller erwarten ui:menu:*.
        """
        # File Actions → ui:menu:file:* UND ui:toolbar:*
        self.event_bus.subscribe("ui:action:file.new", lambda d: self._bridge_file_action("new", d))
        self.event_bus.subscribe("ui:action:file.open", lambda d: self._bridge_file_action("open", d))
        self.event_bus.subscribe("ui:action:file.save", lambda d: self._bridge_file_action("save", d))
        self.event_bus.subscribe("ui:action:file.save_as", lambda d: self._bridge_file_action("save_as", d))
        self.event_bus.subscribe("ui:action:file.export", lambda d: self.event_bus.publish("ui:menu:file:export", d))
        self.event_bus.subscribe("ui:action:file.close", lambda d: self.event_bus.publish("ui:menu:file:close", d))
        
        # Edit Actions
        self.event_bus.subscribe("ui:action:edit.undo", lambda d: self.event_bus.publish("ui:menu:edit:undo", d))
        self.event_bus.subscribe("ui:action:edit.redo", lambda d: self.event_bus.publish("ui:menu:edit:redo", d))
        self.event_bus.subscribe("ui:action:edit.delete", lambda d: self.event_bus.publish("ui:menu:edit:delete", d))
        
        # Arrange Actions
        self.event_bus.subscribe("ui:action:arrange.align", lambda d: self._handle_arrange_align(d))
        self.event_bus.subscribe("ui:action:arrange.distribute", lambda d: self._handle_arrange_distribute(d))
        self.event_bus.subscribe("ui:action:arrange.formation", lambda d: self._handle_arrange_formation(d))
        
        # Layout Actions
        self.event_bus.subscribe("ui:action:edit.auto_layout", lambda d: self.event_bus.publish("ui:menu:layout:auto_layout", d))
        
        # Tools Actions
        self.event_bus.subscribe("ui:action:tools.validate", lambda d: self.event_bus.publish("ui:menu:tools:validate", d))
        
        # Help Actions
        self.event_bus.subscribe("ui:action:help.about", lambda d: self._on_show_about(d))
    
    def _bridge_file_action(self, action, data):
        """Bridged File-Actions zu ui:menu:file:* UND ui:toolbar:* für Kompatibilität."""
        self.event_bus.publish(f"ui:menu:file:{action}", data)
        self.event_bus.publish(f"ui:toolbar:{action}", data)
    
    def _handle_arrange_align(self, data):
        """Übersetzt arrange.align Action zu ui:menu:layout:align:* Event."""
        mode = data.get("mode", "left")
        self.event_bus.publish(f"ui:menu:layout:align:{mode}", data)
    
    def _handle_arrange_distribute(self, data):
        """Übersetzt arrange.distribute Action zu ui:menu:layout:distribute:* Event."""
        mode = data.get("mode", "horizontal")
        self.event_bus.publish(f"ui:menu:layout:distribute:{mode}", data)
    
    def _handle_arrange_formation(self, data):
        """Übersetzt arrange.formation Action zu ui:menu:layout:formation:* Event."""
        mode = data.get("mode", "line")
        self.event_bus.publish(f"ui:menu:layout:formation:{mode}", data)
    
    def _on_exit(self, data=None):
        if self.document_controller.is_document_modified():
            from tkinter import messagebox
            result = messagebox.askyesnocancel("Ungespeicherte Änderungen", "Möchten Sie die Änderungen speichern?")
            if result is None:
                return
            elif result:
                self.event_bus.publish("document:save")
        self.root.quit()
        self.root.destroy()
    
    def _on_window_close(self):
        self.event_bus.publish("app:exit")
    
    def _on_show_about(self, data=None):
        create_about_dialog(self.root, self.event_bus)
    
    def _on_show_settings(self, data=None):
        create_settings_dialog(self.root, self.event_bus)
        if settings:
            self.event_bus.publish("settings:changed", settings)
    
    def _on_file_dialog_requested(self, data):
        """Zeigt File-Dialog und publiziert Ergebnis."""
        from tkinter import filedialog
        mode = data.get("mode", "open")
        callback_event = data.get("callback")
        
        if mode == "open":
            file_path = filedialog.askopenfilename(
                title="VPB-Datei öffnen",
                filetypes=[
                    ("VPB Files", "*.vpb.json"),
                    ("JSON Files", "*.json"),
                    ("All Files", "*.*")
                ]
            )
        else:  # save
            file_path = filedialog.asksaveasfilename(
                title="VPB-Datei speichern",
                defaultextension=".vpb.json",
                filetypes=[
                    ("VPB Files", "*.vpb.json"),
                    ("JSON Files", "*.json")
                ]
            )
        
        if file_path and callback_event:
            self.event_bus.publish(callback_event, {"file_path": file_path})
    
    def _on_show_error(self, data):
        """Zeigt Error-Messagebox."""
        from tkinter import messagebox
        message = data.get("message", "Ein Fehler ist aufgetreten")
        messagebox.showerror("Fehler", message)
    
    def _on_show_info(self, data):
        """Zeigt Info-Messagebox."""
        from tkinter import messagebox
        message = data.get("message", "Information")
        messagebox.showinfo("Information", message)
    
    def _on_canvas_status(self, message):
        """Callback für Canvas-Statusmeldungen."""
        if self.status_bar and hasattr(self.status_bar, 'set_message'):
            self.status_bar.set_message(message)
        else:
            print(f"Canvas: {message}")
    
    def _on_canvas_selection(self, element, connection):
        """Callback für Canvas-Selection-Changes - aktualisiert Properties Panel."""
        if connection:
            self.properties_view.set_connection(connection)
        elif element:
            self.properties_view.set_element(element)
        else:
            self.properties_view.clear()
    
    # Legacy App Compatibility - für canvas_interactions.py
    @property
    def status(self):
        """Legacy-Kompatibilität für status.set()"""
        class StatusProxy:
            def __init__(self, status_bar):
                self._status_bar = status_bar
            
            def set(self, message):
                if self._status_bar and hasattr(self._status_bar, 'set_message'):
                    self._status_bar.set_message(message)
        
        return StatusProxy(self.status_bar)
    
    def _handle_arrow(self, dx, dy, big=False):
        """Legacy-Kompatibilität: Pfeiltasten-Navigation."""
        if not hasattr(self, 'canvas'):
            return
        
        # Wenn Element selektiert: Element verschieben
        if self.canvas.selected_id:
            step = 10 if big else 1
            try:
                el = self.canvas.elements.get(self.canvas.selected_id)
                if el:
                    el.x += dx * step
                    el.y += dy * step
                    self.canvas.redraw_all()
                    return "break"
            except:
                pass
        
        # Sonst: Canvas pannen
        step_px = self.canvas.pan_step_big_px if big else self.canvas.pan_step_small_px
        scale = max(self.canvas.view_scale, 1e-6)
        delta_model_x = (dx * step_px) / scale
        delta_model_y = (dy * step_px) / scale
        x0, y0 = self.canvas.get_view_origin_model()
        self.canvas.set_view_origin_model(x0 - delta_model_x, y0 - delta_model_y)
        return "break"
    
    def _debug_print_canvas_info(self):
        """Debug: Gibt Canvas-Informationen aus."""
        print("\n" + "="*60)
        print("🔧 DEBUG: Canvas Information")
        print("="*60)
        
        if not hasattr(self, 'canvas'):
            print("❌ Canvas nicht initialisiert")
            return
        
        print(f"📊 Elemente: {len(self.canvas.elements)}")
        print(f"🔗 Verbindungen: {len(self.canvas.connections)}")
        print(f"📏 View Scale: {self.canvas.view_scale:.2f}")
        print(f"📍 View Position: ({self.canvas.view_tx:.1f}, {self.canvas.view_ty:.1f})")
        print(f"🎯 Grid Visible: {self.canvas.grid_visible}")
        print(f"🧲 Snap to Grid: {self.canvas.snap_to_grid}")
        
        if self.canvas.elements:
            print("\n📦 Elemente:")
            for el_id, el in list(self.canvas.elements.items())[:10]:
                print(f"  - {el_id}: {el.element_type} '{el.name}' @ ({el.x}, {el.y})")
            if len(self.canvas.elements) > 10:
                print(f"  ... und {len(self.canvas.elements) - 10} weitere")
        
        if self.canvas.connections:
            print("\n🔗 Verbindungen:")
            for conn_id, conn in list(self.canvas.connections.items())[:10]:
                print(f"  - {conn_id}: {conn.source_element} → {conn.target_element}")
            if len(self.canvas.connections) > 10:
                print(f"  ... und {len(self.canvas.connections) - 10} weitere")
        
        print("="*60 + "\n")
    
    # ============================================================================
    # Code Sync Methods (Canvas ↔ JSON/XML)
    # ============================================================================
    
    def _refresh_json_from_canvas(self):
        """Aktualisiert JSON-Editor mit Canvas-Daten."""
        try:
            if hasattr(self, 'canvas'):
                canvas_data = self.canvas.to_dict()
                json_text = self.code_sync_service.canvas_to_json(canvas_data, pretty=True)
                self.json_editor.set_text(json_text)
                print("✅ JSON aktualisiert vom Canvas")
        except Exception as e:
            print(f"❌ JSON Refresh Fehler: {e}")
    
    def _refresh_xml_from_canvas(self):
        """Aktualisiert XML-Editor mit Canvas-Daten."""
        try:
            if hasattr(self, 'canvas'):
                canvas_data = self.canvas.to_dict()
                xml_text = self.code_sync_service.canvas_to_xml(canvas_data, pretty=True)
                self.xml_editor.set_text(xml_text)
                print("✅ XML aktualisiert vom Canvas")
        except Exception as e:
            print(f"❌ XML Refresh Fehler: {e}")
    
    def _apply_json_to_canvas(self):
        """Wendet JSON-Änderungen auf Canvas an."""
        try:
            json_text = self.json_editor.get_text()
            
            # Validierung
            valid, error = self.code_sync_service.validate_json(json_text)
            if not valid:
                print(f"❌ JSON Validierung fehlgeschlagen: {error}")
                return
            
            # Konvertierung
            canvas_data = self.code_sync_service.json_to_canvas(json_text)
            if canvas_data:
                # Canvas neu laden
                if hasattr(self, 'canvas'):
                    self.canvas.load_from_dict(canvas_data)
                    self.canvas.redraw_all()
                    print("✅ Canvas aktualisiert von JSON")
        except Exception as e:
            print(f"❌ JSON Apply Fehler: {e}")
    
    def _apply_xml_to_canvas(self):
        """Wendet XML-Änderungen auf Canvas an."""
        try:
            xml_text = self.xml_editor.get_text()
            
            # Validierung
            valid, error = self.code_sync_service.validate_xml(xml_text)
            if not valid:
                print(f"❌ XML Validierung fehlgeschlagen: {error}")
                return
            
            # Konvertierung
            canvas_data = self.code_sync_service.xml_to_canvas(xml_text)
            if canvas_data:
                # Canvas neu laden
                if hasattr(self, 'canvas'):
                    self.canvas.load_from_dict(canvas_data)
                    self.canvas.redraw_all()
                    print("✅ Canvas aktualisiert von XML")
        except Exception as e:
            print(f"❌ XML Apply Fehler: {e}")
    
    # ============================================================================
    # Chat Terminal Methods (Legacy-Kompatibilität)
    # ============================================================================
    
    def _ensure_chat_visible(self):
        """Stellt sicher, dass der Chat-Terminal sichtbar ist."""
        # TODO: Implementierung wenn Chat minimiert/versteckt werden kann
        pass
    
    def _apply_full_process_json(self, parsed_data):
        """Wendet vollständigen Prozess-JSON an (Replace)."""
        try:
            if hasattr(self, 'canvas') and isinstance(parsed_data, dict):
                self.canvas.load_from_dict(parsed_data)
                self.canvas.redraw_all()
                self.status.set("✅ Prozess vollständig ersetzt")
                print("✅ Prozess vollständig ersetzt via Chat")
        except Exception as e:
            self.status.set(f"❌ Fehler beim Ersetzen: {e}")
            print(f"❌ _apply_full_process_json Fehler: {e}")
    
    def _merge_full_process_json(self, parsed_data):
        """Merged Prozess-JSON mit existierendem Canvas (Merge)."""
        try:
            if hasattr(self, 'canvas') and isinstance(parsed_data, dict):
                # Aktuellen Zustand speichern
                current_data = self.canvas.to_dict()
                
                # Neue Elemente hinzufügen
                for elem in parsed_data.get('elements', []):
                    elem_id = elem.get('element_id')
                    # Nur hinzufügen wenn ID noch nicht existiert
                    if elem_id and elem_id not in self.canvas.elements:
                        from vpb.models.element import VPBElement
                        new_elem = VPBElement.from_dict(elem)
                        self.canvas.elements[elem_id] = new_elem
                
                # Neue Connections hinzufügen
                for conn in parsed_data.get('connections', []):
                    conn_id = conn.get('connection_id')
                    if conn_id and conn_id not in self.canvas.connections:
                        from vpb.models.connection import VPBConnection
                        new_conn = VPBConnection.from_dict(conn)
                        self.canvas.connections[conn_id] = new_conn
                
                self.canvas.redraw_all()
                self.status.set("✅ Prozess gemerged")
                print("✅ Prozess gemerged via Chat")
        except Exception as e:
            self.status.set(f"❌ Fehler beim Mergen: {e}")
            print(f"❌ _merge_full_process_json Fehler: {e}")
    
    def _apply_add_only_patch(self, parsed_data):
        """Wendet Add-Only Patch an (nur neue Elemente)."""
        try:
            if hasattr(self, 'canvas') and isinstance(parsed_data, dict):
                added_count = 0
                
                # Nur neue Elemente hinzufügen
                for elem in parsed_data.get('elements', []):
                    elem_id = elem.get('element_id')
                    if elem_id and elem_id not in self.canvas.elements:
                        from vpb.models.element import VPBElement
                        new_elem = VPBElement.from_dict(elem)
                        self.canvas.elements[elem_id] = new_elem
                        added_count += 1
                
                # Nur neue Connections hinzufügen
                for conn in parsed_data.get('connections', []):
                    conn_id = conn.get('connection_id')
                    if conn_id and conn_id not in self.canvas.connections:
                        from vpb.models.connection import VPBConnection
                        new_conn = VPBConnection.from_dict(conn)
                        self.canvas.connections[conn_id] = new_conn
                        added_count += 1
                
                self.canvas.redraw_all()
                self.status.set(f"✅ {added_count} neue Elemente hinzugefügt")
                print(f"✅ {added_count} neue Elemente hinzugefügt via Chat")
        except Exception as e:
            self.status.set(f"❌ Fehler beim Patchen: {e}")
            print(f"❌ _apply_add_only_patch Fehler: {e}")
    
    def _apply_diagnose_patch(self, parsed_data):
        """Wendet Diagnose-Patch an (Fehlerbehebungen)."""
        try:
            if hasattr(self, 'canvas') and isinstance(parsed_data, dict):
                fixes = parsed_data.get('fixes', [])
                fixed_count = 0
                
                for fix in fixes:
                    elem_id = fix.get('element_id')
                    if elem_id and elem_id in self.canvas.elements:
                        elem = self.canvas.elements[elem_id]
                        
                        # Wende Fixes an
                        for key, value in fix.items():
                            if key != 'element_id' and hasattr(elem, key):
                                setattr(elem, key, value)
                                fixed_count += 1
                
                self.canvas.redraw_all()
                self.status.set(f"✅ {fixed_count} Korrekturen angewendet")
                print(f"✅ {fixed_count} Korrekturen angewendet via Chat")
        except Exception as e:
            self.status.set(f"❌ Fehler bei Diagnose: {e}")
            print(f"❌ _apply_diagnose_patch Fehler: {e}")
    
    # ============================================================================
    # Main Loop
    # ============================================================================
    
    def run(self):
        """Startet die Hauptschleife der Anwendung."""
        # GUI updaten damit alle Größen bekannt sind
        self.root.update_idletasks()
        
        # Koordinatenursprung vertikal mittig setzen (y=0 in Mitte)
        # Jetzt sind die Canvas-Dimensionen bekannt
        if hasattr(self, 'canvas'):
            self.canvas.center_time_axis_vertical()
            print(f"✅ Koordinatenursprung zentriert: view_ty = {self.canvas.view_ty:.1f}")
        
        # Mainloop starten
        self.root.mainloop()

def parse_arguments():
    """Parst Command-Line Argumente."""
    parser = argparse.ArgumentParser(
        description='VPB Process Designer 0.2.0-alpha',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python vpb_app.py                              # Normal starten
  python vpb_app.py --load test_process.vpb.json # Datei beim Start laden
  python vpb_app.py --load file.vpb.json --debug # Mit Debug-Modus
  python vpb_app.py --load file.vpb.json --info  # Canvas-Info anzeigen
  python vpb_app.py --load file.vpb.json --validate # Auto-Validierung
  python vpb_app.py --version                    # Version anzeigen
        """
    )
    
    # File Operations
    parser.add_argument(
        '--load', '-l',
        metavar='FILE',
        help='VPB-Datei beim Start laden (.vpb.json)'
    )
    
    parser.add_argument(
        '--export', '-e',
        metavar='FILE',
        help='Nach dem Laden exportieren (z.B. output.pdf, output.svg, output.png)'
    )
    
    # Debug Options
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='Debug-Modus aktivieren (mehr Logging)'
    )
    
    parser.add_argument(
        '--info', '-i',
        action='store_true',
        help='Canvas-Informationen nach dem Laden ausgeben'
    )
    
    parser.add_argument(
        '--validate', '-v',
        action='store_true',
        help='Automatische Validierung nach dem Laden durchführen'
    )
    
    # Canvas Options
    parser.add_argument(
        '--grid',
        action='store_true',
        help='Grid beim Start anzeigen (Standard: an)'
    )
    
    parser.add_argument(
        '--no-grid',
        action='store_true',
        help='Grid beim Start ausblenden'
    )
    
    parser.add_argument(
        '--snap',
        action='store_true',
        help='Snap-to-Grid beim Start aktivieren'
    )
    
    # Window Options
    parser.add_argument(
        '--geometry',
        metavar='WIDTHxHEIGHT',
        default='1400x900',
        help='Fenster-Größe (z.B. 1920x1080, default: 1400x900)'
    )
    
    parser.add_argument(
        '--fullscreen',
        action='store_true',
        help='Im Vollbild-Modus starten'
    )
    
    # Version
    parser.add_argument(
        '--version',
        action='version',
        version='VPB Process Designer 0.2.0-alpha'
    )
    
    return parser.parse_args()

def main():
    """Main Entry Point mit ArgumentParser."""
    args = parse_arguments()
    
    print("="*60)
    print("VPB Process Designer 0.2.0-alpha")
    print("="*60)
    
    # Debug-Info ausgeben
    if args.debug:
        print("🔧 DEBUG MODE: Aktiviert")
        if args.load:
            print(f"📂 Auto-Load: {args.load}")
        if args.export:
            print(f"💾 Auto-Export: {args.export}")
        if args.validate:
            print("✅ Auto-Validate: Aktiviert")
        if args.info:
            print("ℹ️  Canvas-Info: Aktiviert")
        print("-"*60)
    
    # Python-Version prüfen
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ erforderlich!")
        sys.exit(1)
    
    try:
        app = VPBApplication(args)
        
        # Window-Optionen anwenden
        if args.geometry and args.geometry != '1400x900':
            app.root.geometry(args.geometry)
            print(f"🖼️  Fenster-Größe: {args.geometry}")
        
        if args.fullscreen:
            app.root.attributes('-fullscreen', True)
            print("🖼️  Vollbild-Modus: Aktiviert")
        
        # Canvas-Optionen anwenden (nach Canvas-Init)
        if hasattr(app, 'canvas'):
            if args.no_grid:
                app.canvas.grid_visible = False
                app.canvas.redraw_all()
                print("📏 Grid: Ausgeblendet")
            elif args.grid:
                app.canvas.grid_visible = True
                app.canvas.redraw_all()
                print("📏 Grid: Angezeigt")
            
            if args.snap:
                app.canvas.snap_to_grid = True
                print("🧲 Snap-to-Grid: Aktiviert")
        
        # App starten
        app.run()
        
    except KeyboardInterrupt:
        print("\n⚠️  Beendet durch Benutzer (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
