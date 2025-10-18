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
from vpb.infrastructure.user_profile_manager import UserProfileManager
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
from vpb.controllers.background_task_controller import BackgroundTaskController
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
        
        # User Profile Manager - Zentrales Benutzerprofil-System
        self.user_profile_manager = UserProfileManager()
        self.user_profile = self.user_profile_manager.load()
        
        print(f"👤 Benutzerprofil geladen: {self.user_profile.username}@{self.user_profile.hostname}")
        
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
        
        # Recent Files Service
        from vpb.services.recent_files_service import RecentFilesService
        self.recent_files_service = RecentFilesService()
        
        # Backup Service
        from vpb.services.backup_service import BackupService
        self.backup_service = BackupService()
        
        # AutoSave Service (5 Minuten Intervall)
        from vpb.services.autosave_service import AutoSaveService
        settings = self.settings_manager.get_current()
        if settings and hasattr(settings, 'autosave'):
            autosave_interval = settings.autosave.interval_minutes * 60  # Minuten -> Sekunden
            autosave_enabled = settings.autosave.enabled
        else:
            autosave_interval = 300  # Default: 5 Minuten
            autosave_enabled = True
        
        self.autosave_service = AutoSaveService(
            interval_seconds=autosave_interval,
            enabled=autosave_enabled
        )
        
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
        
        # Linke Spalte: Notebook mit Tabs (Sidebar mit fester Mindestbreite)
        # Container-Frame für linke Sidebar, damit Scrollbar nicht vom Sash verdeckt wird
        left_container = tk.Frame(self.paned_window)
        self.left_notebook = ttk.Notebook(left_container)
        self.left_notebook.pack(fill=tk.BOTH, expand=True, padx=(0, 3))
        self.paned_window.add(left_container, minsize=250, width=250, stretch='never')
        
        # Tab 1: Palette
        self.palette_view = create_palette_view(self.left_notebook, self.event_bus)
        self.left_notebook.add(self.palette_view, text="Palette")
        
        # Palette-Daten laden
        self._load_palette_data()
        
        # Dynamische Anpassung der Palette-Breite beim Resize
        self.left_notebook.bind('<Configure>', self._on_left_sidebar_resize)
        
        # Mittlere Spalte: Notebook mit Canvas/Code/XML Tabs (expandiert beim Fenster vergrößern)
        self.mid_notebook = ttk.Notebook(self.paned_window)
        self.paned_window.add(self.mid_notebook, minsize=400, stretch='always')
        
        # Rechte Spalte: Vertikales PanedWindow für Properties und MiniMap (Sidebar mit fester Mindestbreite)
        # Container-Frame für rechte Sidebar, damit Scrollbar nicht vom Sash verdeckt wird
        right_container = tk.Frame(self.paned_window)
        self.right_paned = tk.PanedWindow(right_container, orient=tk.VERTICAL, sashwidth=5)
        self.right_paned.pack(fill=tk.BOTH, expand=True, padx=(3, 0))
        self.paned_window.add(right_container, minsize=250, width=300, stretch='never')
        
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
        
        # Hierarchie mit Canvas verbinden (Anzeige und Sync aktivieren)
        try:
            self.hier_canvas.attach(
                self.canvas,
                on_select=self._on_hierarchy_select,
                on_double_click=self._on_hierarchy_double_click,
            )
        except Exception as e:
            print(f"⚠️ Hierarchie konnte nicht verbunden werden: {e}")
        
        # MiniMap im rechten Notebook-Tab erstellen (4:3 Seitenverhältnis)
        self.minimap = MiniMapCanvas(self.minimap_frame)
        self.minimap.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.minimap.attach(self.canvas)
        
        # 4:3 Seitenverhältnis für MiniMap erzwingen
        self._setup_minimap_aspect_ratio()
        
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
    
    def _setup_minimap_aspect_ratio(self):
        """Richtet das 4:3 Seitenverhältnis für die MiniMap ein."""
        def on_minimap_resize(event):
            # Berechne Höhe für 4:3 Seitenverhältnis (Breite : Höhe = 4 : 3)
            # Höhe = Breite * 3/4
            width = event.width
            target_height = int(width * 3 / 4)
            
            # Setze neue Höhe, falls sie sich geändert hat
            current_height = self.minimap.winfo_height()
            if abs(current_height - target_height) > 5:  # Toleranz von 5px
                self.minimap.configure(height=target_height)
        
        # Binde Resize-Event an MiniMap-Frame
        self.minimap_frame.bind("<Configure>", on_minimap_resize)
        
        print("✅ Canvas mit Linealen und Hierarchie erstellt")
    
    def _on_left_sidebar_resize(self, event):
        """
        Wird aufgerufen, wenn die linke Sidebar ihre Größe ändert.
        Passt die Palette dynamisch an die neue Breite an.
        """
        # Die Palette passt sich automatisch an durch fill=BOTH, expand=True
        # Hier könnten zusätzliche Anpassungen erfolgen, z.B. für Reflow
        pass
    
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
        self.document_controller = DocumentController(
            self.event_bus, 
            self.document_service,
            self.recent_files_service,
            self.backup_service
        )
        self.element_controller = ElementController(self.event_bus)
        self.connection_controller = ConnectionController(self.event_bus)
        self.layout_controller = LayoutController(self.event_bus, self.layout_service)
        self.validation_controller = ValidationController(self.event_bus, self.validation_service)
        self.export_controller = ExportController(self.event_bus, self.export_service)
        
        # Background Task Controller (für Ollama Chat Streams)
        self.background_task_controller = BackgroundTaskController(self.event_bus)
        
        if self.ai_service:
            self.ai_controller = AIController(self.event_bus, self.ai_service)
        
        # ChatController benötigt Zugriff auf _app_controller für submit/cancel
        self._app_controller = self.background_task_controller
        
        # Canvas-Referenz an Controller übergeben
        if hasattr(self, 'canvas'):
            self.element_controller.set_canvas(self.canvas)
            self.connection_controller.set_canvas(self.canvas)  # NEU: Connection-Controller braucht Canvas
            self.document_controller.set_canvas(self.canvas)  # Für Legacy-Kompatibilität
            self.layout_controller.set_canvas(self.canvas)  # Layout-Controller braucht Canvas
        
        # AutoSave Callbacks konfigurieren
        self._setup_autosave()
    
    def _setup_autosave(self):
        """Konfiguriert AutoSave-Service mit Callbacks."""
        if not hasattr(self, 'autosave_service'):
            return
        
        # Callback für Speichern
        def auto_save_callback():
            if self.document_controller.current_file_path:
                # Speichere in existierende Datei
                self.event_bus.publish("ui:menu:file:save", {})
            else:
                # Erstelle Auto-Backup für ungespeicherte Projekte
                if self.canvas and hasattr(self.canvas, 'to_dict'):
                    canvas_data = self.canvas.to_dict()
                    self.backup_service.create_auto_backup(None, canvas_data)
        
        # Callback für "ist modifiziert?"
        def is_modified_callback():
            return self.document_controller.is_document_modified()
        
        self.autosave_service.set_save_callback(auto_save_callback)
        self.autosave_service.set_is_modified_callback(is_modified_callback)
        
        # Starte AutoSave
        self.autosave_service.start()
    
    def _subscribe_to_events(self):
        self.event_bus.subscribe("app:exit", self._on_exit)
        self.event_bus.subscribe("ui:help:about", self._on_show_about)
        self.event_bus.subscribe("ui:settings:show", self._on_show_settings)
        self.event_bus.subscribe("ui:request:file_path", self._on_file_dialog_requested)
        self.event_bus.subscribe("ui:error", self._on_show_error)
        self.event_bus.subscribe("ui:info", self._on_show_info)
        
        # Window Events
        self.event_bus.subscribe("ui:window:title", self._on_window_title_changed)
        
        # Recent Files Event
        self.event_bus.subscribe("document:recent_files_changed", self._on_recent_files_changed)
        
        # Toolbar Update Events
        self.event_bus.subscribe("toolbar:zoom_changed", self._on_toolbar_zoom_changed)
        self.event_bus.subscribe("toolbar:grid_state_changed", self._on_toolbar_grid_changed)
        
        # Canvas View Changed Events (Auto-Save Profile)
        self.event_bus.subscribe("canvas:zoom_changed", self._on_canvas_view_changed)
        self.event_bus.subscribe("canvas:pan_changed", self._on_canvas_view_changed)
        self.event_bus.subscribe("canvas:grid_toggled", self._on_canvas_view_changed)
        
        # Element/Connection Events (Canvas Redraw)
        self.event_bus.subscribe("element:created", self._on_element_changed)
        self.event_bus.subscribe("element:modified", self._on_element_changed)
        self.event_bus.subscribe("element:deleted", self._on_element_changed)
        self.event_bus.subscribe("connection:created", self._on_connection_changed)
        self.event_bus.subscribe("connection:modified", self._on_connection_changed)
        self.event_bus.subscribe("connection:deleted", self._on_connection_changed)
        
        # Background Task Events (für Chat-Controller)
        self.event_bus.subscribe("task:stream_chunk", self._on_task_stream_chunk)
        self.event_bus.subscribe("task:completed", self._on_task_completed)
        self.event_bus.subscribe("task:failed", self._on_task_failed)
        self.event_bus.subscribe("task:cancelled", self._on_task_cancelled)
        
        # Event-Bridge: ui:action:* → Legacy Events
        # MenuBar/Toolbar publizieren ui:action:*, Controller erwarten ui:menu:*
        self._setup_action_bridge()
        
        # Initial Recent Files laden
        self.root.after(100, self._load_initial_recent_files)
        
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
        self.event_bus.subscribe("ui:action:file.clear_recent_files", lambda d: self._on_clear_recent_files(d))
        
        # Edit Actions
        self.event_bus.subscribe("ui:action:edit.undo", lambda d: self.event_bus.publish("ui:menu:edit:undo", d))
        self.event_bus.subscribe("ui:action:edit.redo", lambda d: self.event_bus.publish("ui:menu:edit:redo", d))
        self.event_bus.subscribe("ui:action:edit.delete", lambda d: self.event_bus.publish("ui:menu:edit:delete", d))
        self.event_bus.subscribe("ui:action:edit.group", lambda d: self._handle_group_from_selection(d))
        self.event_bus.subscribe("ui:action:edit.time_loop", lambda d: self._handle_time_loop_from_selection(d))
        self.event_bus.subscribe("ui:action:edit.ungroup", lambda d: self._handle_ungroup_selected(d))
        
        # Arrange Actions
        self.event_bus.subscribe("ui:action:arrange.align", lambda d: self._handle_arrange_align(d))
        self.event_bus.subscribe("ui:action:arrange.distribute", lambda d: self._handle_arrange_distribute(d))
        self.event_bus.subscribe("ui:action:arrange.formation", lambda d: self._handle_arrange_formation(d))
        
        # Layout Actions
        self.event_bus.subscribe("ui:action:edit.auto_layout", lambda d: self.event_bus.publish("ui:menu:layout:auto_layout", d))
        
        # Tools Actions
        self.event_bus.subscribe("ui:action:tools.validate", lambda d: self.event_bus.publish("ui:menu:tools:validate", d))
        
        # Migration Actions
        self.event_bus.subscribe("ui:action:tools.migration.start", lambda d: self._on_migration_start(d))
        self.event_bus.subscribe("ui:action:tools.migration.gap_detection", lambda d: self._on_migration_gap_detection(d))
        self.event_bus.subscribe("ui:action:tools.migration.validate", lambda d: self._on_migration_validate(d))
        self.event_bus.subscribe("ui:action:tools.migration.configure", lambda d: self._on_migration_configure(d))
        self.event_bus.subscribe("ui:action:tools.migration.show_report", lambda d: self._on_migration_show_report(d))
        
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
    
    def _handle_group_from_selection(self, data):
        """Erstellt eine Gruppe aus der Auswahl."""
        if hasattr(self, 'canvas') and hasattr(self.canvas, '_group_from_selection'):
            self.canvas._group_from_selection()
    
    def _handle_time_loop_from_selection(self, data):
        """Erstellt eine Zeitschleife aus der Auswahl."""
        if hasattr(self, 'canvas') and hasattr(self.canvas, '_time_loop_from_selection'):
            self.canvas._time_loop_from_selection()
    
    def _handle_ungroup_selected(self, data):
        """Löst die ausgewählte Gruppe auf."""
        if hasattr(self, 'canvas') and hasattr(self.canvas, '_ungroup_selected'):
            self.canvas._ungroup_selected()
    
    def _on_exit(self, data=None):
        if self.document_controller.is_document_modified():
            from tkinter import messagebox
            result = messagebox.askyesnocancel("Ungespeicherte Änderungen", "Möchten Sie die Änderungen speichern?")
            if result is None:
                return
            elif result:
                self.event_bus.publish("document:save")
        
        # AutoSave beenden
        if hasattr(self, 'autosave_service'):
            try:
                self.autosave_service.stop()
            except Exception as e:
                print(f"⚠️ Error stopping autosave: {e}")
        
        # Benutzerprofil speichern vor dem Beenden
        self._save_user_profile()
        
        # Background Tasks beenden
        if hasattr(self, 'background_task_controller'):
            try:
                self.background_task_controller.shutdown()
            except Exception as e:
                print(f"⚠️ Error shutting down background tasks: {e}")
        
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
        import os
        
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
            # Ermittle aktuellen Dateinamen für Vorschlag
            current_file = self.document_controller.get_current_file_path()
            initial_file = ""
            initial_dir = os.getcwd()
            
            if current_file:
                initial_file = os.path.basename(current_file)
                initial_dir = os.path.dirname(current_file)
            else:
                # Vorschlag für neue Datei
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                initial_file = f"prozess_{timestamp}.vpb.json"
            
            file_path = filedialog.asksaveasfilename(
                title="VPB-Datei speichern",
                initialfile=initial_file,
                initialdir=initial_dir,
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
    
    def _on_recent_files_changed(self, data):
        """Aktualisiert das Recent Files Menü."""
        recent_files = data.get("recent_files", [])
        if hasattr(self, 'menu_bar') and hasattr(self.menu_bar, 'update_recent_files'):
            self.menu_bar.update_recent_files(recent_files)
    
    def _load_initial_recent_files(self):
        """Lädt initial die Recent Files in das Menü."""
        if hasattr(self, 'recent_files_service'):
            recent_files = self.recent_files_service.get_recent_files()
            if hasattr(self, 'menu_bar') and hasattr(self.menu_bar, 'update_recent_files'):
                self.menu_bar.update_recent_files(recent_files)
    
    def _on_clear_recent_files(self, data):
        """Leert die Recent Files Liste."""
        if hasattr(self, 'recent_files_service'):
            self.recent_files_service.clear_recent_files()
            self.event_bus.publish("document:recent_files_changed", {"recent_files": []})
    
    def _on_window_title_changed(self, data):
        """Aktualisiert den Fenstertitel."""
        title = data.get("title", "VPB Process Designer")
        self.root.title(title)
    
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
    
    def _on_canvas_view_changed(self, data):
        """Speichert Canvas-Ansicht im Benutzerprofil."""
        try:
            if hasattr(self, 'canvas') and hasattr(self, 'user_profile_manager'):
                canvas = self.canvas
                self.user_profile_manager.update_canvas_view(
                    zoom=canvas.view_scale,
                    pan_x=canvas.view_tx,
                    pan_y=canvas.view_ty,
                    grid_visible=canvas.grid_visible,
                    snap_to_grid=canvas.snap_to_grid
                )
        except Exception as e:
            # Stille Fehlerbehandlung, um UI nicht zu stören
            pass
    
    def _on_element_changed(self, data):
        """Synchronisiert Canvas mit Dokument, wenn Element erstellt/geändert/gelöscht wird."""
        try:
            if hasattr(self, 'canvas') and hasattr(self, 'document_controller'):
                # Synchronisiere Canvas mit aktuellem Dokument
                self._sync_canvas_with_document()
        except Exception as e:
            print(f"⚠️ Fehler beim Canvas-Sync nach Element-Änderung: {e}")
    
    def _on_connection_changed(self, data):
        """Synchronisiert Canvas mit Dokument, wenn Verbindung erstellt/geändert/gelöscht wird."""
        try:
            if hasattr(self, 'canvas') and hasattr(self, 'document_controller'):
                # Synchronisiere Canvas mit aktuellem Dokument
                self._sync_canvas_with_document()
        except Exception as e:
            print(f"⚠️ Fehler beim Canvas-Sync nach Verbindungs-Änderung: {e}")
    
    def _sync_canvas_with_document(self):
        """Synchronisiert Canvas-Elemente mit dem aktuellen Dokument."""
        try:
            if not hasattr(self, 'canvas') or not hasattr(self, 'document_controller'):
                return
            
            document = self.document_controller.get_current_document()
            if not document:
                return
            
            # Aktualisiere Canvas-Elemente aus Dokument
            self.canvas.elements.clear()
            for element in document.elements:
                self.canvas.elements[element.element_id] = element
            
            # Aktualisiere Canvas-Verbindungen aus Dokument
            self.canvas.connections.clear()
            for connection in document.connections:
                self.canvas.connections[connection.connection_id] = connection
            
            # Jetzt neu zeichnen
            self.canvas.redraw_all()
            
        except Exception as e:
            print(f"⚠️ Fehler beim Sync von Canvas mit Dokument: {e}")

    # =============================
    # Toolbar Update Events
    # =============================
    def _on_toolbar_zoom_changed(self, data):
        """Aktualisiert Zoom-Anzeige in Toolbar."""
        try:
            zoom = data.get("zoom", 1.0)
            if hasattr(self, 'toolbar_view'):
                self.toolbar_view.update_zoom_level(zoom)
        except Exception as e:
            print(f"⚠️ Error updating toolbar zoom: {e}")
    
    def _on_toolbar_grid_changed(self, data):
        """Aktualisiert Grid-Button in Toolbar."""
        try:
            active = data.get("active", False)
            if hasattr(self, 'toolbar_view'):
                self.toolbar_view.set_grid_active(active)
        except Exception as e:
            print(f"⚠️ Error updating toolbar grid: {e}")

    # =============================
    # Background Task Events (Chat)
    # =============================
    def _on_task_stream_chunk(self, data):
        """Wird aufgerufen, wenn ein Stream-Chunk empfangen wird."""
        try:
            task_id = data.get("task_id")
            chunk = data.get("chunk", "")
            # Weiterleiten an ChatController (im Haupt-Thread)
            if hasattr(self, 'chat_controller') and hasattr(self, 'root'):
                self.root.after_idle(lambda: self._handle_chunk_in_main_thread(chunk))
        except Exception as e:
            print(f"⚠️ Error handling stream chunk: {e}")
    
    def _handle_chunk_in_main_thread(self, chunk):
        """Verarbeitet Chunk im Haupt-Thread (Tkinter-sicher)."""
        try:
            if chunk and hasattr(self.args, 'debug') and self.args.debug:
                print(f"🔧 DEBUG: Chunk empfangen: {chunk[:50]}...")
            if hasattr(self, 'chat_controller'):
                self.chat_controller.handle_stream_event("chunk", chunk)
        except Exception as e:
            print(f"⚠️ Error in chunk handler: {e}")
    
    def _on_task_completed(self, data):
        """Wird aufgerufen, wenn ein Task abgeschlossen ist."""
        try:
            task_id = data.get("task_id")
            result = data.get("result", "")
            # Weiterleiten an ChatController (im Haupt-Thread)
            if hasattr(self, 'chat_controller') and hasattr(self, 'root'):
                self.root.after_idle(lambda: self._handle_completion_in_main_thread(result))
        except Exception as e:
            print(f"⚠️ Error handling task completion: {e}")
    
    def _handle_completion_in_main_thread(self, result):
        """Verarbeitet Completion im Haupt-Thread."""
        try:
            if hasattr(self, 'chat_controller'):
                self.chat_controller.handle_stream_event("stream_end", result)
        except Exception as e:
            print(f"⚠️ Error in completion handler: {e}")
    
    def _on_task_failed(self, data):
        """Wird aufgerufen, wenn ein Task fehlschlägt."""
        try:
            task_id = data.get("task_id")
            error = data.get("error", "Unbekannter Fehler")
            # Weiterleiten an ChatController (im Haupt-Thread)
            if hasattr(self, 'chat_controller') and hasattr(self, 'root'):
                self.root.after_idle(lambda: self._handle_error_in_main_thread(error))
        except Exception as e:
            print(f"⚠️ Error handling task failure: {e}")
    
    def _handle_error_in_main_thread(self, error):
        """Verarbeitet Fehler im Haupt-Thread."""
        try:
            if hasattr(self, 'chat_controller'):
                self.chat_controller.handle_stream_event("error", error)
        except Exception as e:
            print(f"⚠️ Error in error handler: {e}")
    
    def _on_task_cancelled(self, data):
        """Wird aufgerufen, wenn ein Task abgebrochen wird."""
        try:
            task_id = data.get("task_id")
            # Weiterleiten an ChatController (im Haupt-Thread)
            if hasattr(self, 'chat_controller') and hasattr(self, 'root'):
                self.root.after_idle(lambda: self._handle_cancel_in_main_thread())
        except Exception as e:
            print(f"⚠️ Error handling task cancellation: {e}")
    
    def _handle_cancel_in_main_thread(self):
        """Verarbeitet Cancellation im Haupt-Thread."""
        try:
            if hasattr(self, 'chat_controller'):
                self.chat_controller.handle_stream_event("cancelled", None)
        except Exception as e:
            print(f"⚠️ Error in cancel handler: {e}")

    # =============================
    # Hierarchie-Events
    # =============================
    def _on_hierarchy_select(self, index, category):
        """Wird aufgerufen, wenn in der Hierarchie eine Kategorie selektiert wird."""
        try:
            name = category.get('name') if isinstance(category, dict) else str(category)
            if hasattr(self, 'status'):
                self.status.set(f"Hierarchie: {name if name else '—'}")
        except Exception:
            pass

    def _on_hierarchy_double_click(self, index, category):
        """Doppelklick: Canvas-Viewport auf die Kategorie zentrieren."""
        try:
            if not category or not hasattr(self, 'canvas'):
                return
            y0 = float(category.get('y0', 0.0)) if isinstance(category, dict) else 0.0
            y1 = float(category.get('y1', 0.0)) if isinstance(category, dict) else 0.0
            # Mitte der Kategorie in Model-Koordinaten
            cy = (y0 + y1) / 2.0
            # Aktuelle View-Breite/Höhe in Model-Einheiten
            vw_m, vh_m = self.canvas.get_viewport_model_size()
            # X beibehalten, Y so setzen, dass cy mittig ist
            x0, y0 = self.canvas.get_view_origin_model()
            self.canvas.set_view_origin_model(x0, cy - vh_m / 2.0)
            self.canvas.redraw_all()
        except Exception as e:
            print(f"⚠️ Hierarchie-Navigation fehlgeschlagen: {e}")
    
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
            print(f"\n🔧 _apply_full_process_json aufgerufen")
            print(f"   Typ: {type(parsed_data)}")
            
            if not hasattr(self, 'canvas'):
                print(f"❌ Kein Canvas verfügbar")
                return
            
            if not isinstance(parsed_data, dict):
                print(f"❌ parsed_data ist kein Dict: {type(parsed_data)}")
                return
            
            # Zeige Struktur
            elem_count = len(parsed_data.get('elements', []))
            conn_count = len(parsed_data.get('connections', []))
            print(f"   Struktur: {elem_count} Elemente, {conn_count} Verbindungen")
            
            # Lade in Canvas
            self.canvas.load_from_dict(parsed_data)
            self.canvas.redraw_all()
            
            # Erfolgsmeldung
            self.status.set(f"✅ Prozess ersetzt: {elem_count} Elemente, {conn_count} Verbindungen")
            print(f"✅ Prozess vollständig ersetzt: {elem_count} Elemente, {conn_count} Verbindungen")
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.status.set(f"❌ Fehler beim Ersetzen: {e}")
            print(f"❌ _apply_full_process_json Fehler: {e}")
            print(f"   Traceback:\n{error_details}")
    
    def _merge_full_process_json(self, parsed_data):
        """Merged Prozess-JSON mit existierendem Canvas (Merge)."""
        try:
            print(f"\n🔧 _merge_full_process_json aufgerufen")
            print(f"   Typ: {type(parsed_data)}")
            
            if not hasattr(self, 'canvas'):
                print(f"❌ Kein Canvas verfügbar")
                return
            
            if not isinstance(parsed_data, dict):
                print(f"❌ parsed_data ist kein Dict: {type(parsed_data)}")
                return
            
            # Zeige Struktur
            elem_count_new = len(parsed_data.get('elements', []))
            conn_count_new = len(parsed_data.get('connections', []))
            elem_count_existing = len(self.canvas.elements)
            conn_count_existing = len(self.canvas.connections)
            
            print(f"   Neu: {elem_count_new} Elemente, {conn_count_new} Verbindungen")
            print(f"   Existierend: {elem_count_existing} Elemente, {conn_count_existing} Verbindungen")
            
            added_elements = 0
            added_connections = 0
            
            # Neue Elemente hinzufügen
            for elem in parsed_data.get('elements', []):
                elem_id = elem.get('element_id')
                # Nur hinzufügen wenn ID noch nicht existiert
                if elem_id and elem_id not in self.canvas.elements:
                    from vpb.models.element import VPBElement
                    new_elem = VPBElement.from_dict(elem)
                    self.canvas.elements[elem_id] = new_elem
                    added_elements += 1
                    print(f"   ➕ Element hinzugefügt: {elem_id} ({new_elem.element_type})")
                else:
                    print(f"   ⏭️  Element übersprungen (existiert): {elem_id}")
            
            # Neue Connections hinzufügen
            for conn in parsed_data.get('connections', []):
                conn_id = conn.get('connection_id')
                if conn_id and conn_id not in self.canvas.connections:
                    from vpb.models.connection import VPBConnection
                    new_conn = VPBConnection.from_dict(conn)
                    self.canvas.connections[conn_id] = new_conn
                    added_connections += 1
                    print(f"   ➕ Verbindung hinzugefügt: {conn_id}")
                else:
                    print(f"   ⏭️  Verbindung übersprungen (existiert): {conn_id}")
            
            self.canvas.redraw_all()
            self.status.set(f"✅ Gemerged: +{added_elements} Elemente, +{added_connections} Verbindungen")
            print(f"✅ Prozess gemerged: {added_elements} neue Elemente, {added_connections} neue Verbindungen")
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.status.set(f"❌ Fehler beim Mergen: {e}")
            print(f"❌ _merge_full_process_json Fehler: {e}")
            print(f"   Traceback:\n{error_details}")
    
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
    # Migration Event Handlers
    # ============================================================================
    
    def _on_migration_start(self, data=None):
        """Öffnet Migration Dialog."""
        from vpb.ui.migration_dialog import MigrationDialog
        
        dialog = MigrationDialog(
            self.root,
            on_start_callback=self._run_migration
        )
    
    def _run_migration(self, config: dict, dialog):
        """
        Führt Migration aus.
        
        Args:
            config: Migration Configuration
            dialog: MigrationDialog Instance
        """
        import time
        from pathlib import Path
        
        try:
            # Import Migration Tools
            from migration.migration_tool import VPBMigrationTool, MigrationConfig
            from migration.gap_detector import GapDetector
            from migration.validation import DataValidator
            
            start_time = time.time()
            
            # Create MigrationConfig
            migration_config = MigrationConfig(
                source_config={
                    "type": "sqlite",
                    "db_path": config["source"]["db_path"]
                },
                target_config={
                    "type": "uds3_polyglot",
                    "backend_config": config["target"].get("backend_config")
                },
                batch_size=config["options"]["batch_size"],
                continue_on_error=config["options"]["continue_on_error"]
            )
            
            # Progress Callback
            total_records = 0
            processed_records = 0
            
            def progress_callback(batch_num, batch_size, table_name):
                nonlocal processed_records
                processed_records += batch_size
                speed = processed_records / (time.time() - start_time) if time.time() > start_time else 0
                dialog.update_progress(
                    processed_records,
                    total_records,
                    status=f"Migriere {table_name} (Batch {batch_num})...",
                    speed=speed
                )
                dialog._log_message(f"✓ Batch {batch_num} ({batch_size} records) verarbeitet", "info")
            
            # Gap Detection (optional)
            gap_results = None
            if config["options"]["gap_detection"]:
                dialog._log_message("🔍 Gap Detection gestartet...", "info")
                gap_detector = GapDetector(config["source"]["db_path"])
                gap_results = gap_detector.detect_all_gaps()
                
                total_gaps = sum(len(gaps) for gaps in gap_results.values())
                dialog._log_message(f"✓ Gap Detection abgeschlossen: {total_gaps} Gaps gefunden", 
                                  "warning" if total_gaps > 0 else "success")
            
            # Zähle Datensätze
            import sqlite3
            conn = sqlite3.connect(config["source"]["db_path"])
            cursor = conn.cursor()
            
            for table in config["options"]["tables"]:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                total_records += count
                dialog._log_message(f"📊 {table}: {count} Datensätze", "info")
            
            conn.close()
            
            dialog._log_message(f"📦 Gesamt: {total_records} Datensätze", "info")
            dialog.update_progress(0, total_records, status="Starte Migration...")
            
            # Migration Tool erstellen
            migration_tool = VPBMigrationTool(migration_config)
            
            # Migration durchführen
            dialog._log_message("🚀 Migration gestartet...", "info")
            
            migration_results = {}
            for table in config["options"]["tables"]:
                dialog._log_message(f"📋 Migriere Tabelle: {table}", "info")
                
                result = migration_tool.migrate_table(
                    table_name=table,
                    progress_callback=progress_callback
                )
                
                migration_results[table] = result
                
                if result["success"]:
                    dialog._log_message(
                        f"✅ {table}: {result['successful_records']}/{result['total_records']} erfolgreich",
                        "success"
                    )
                else:
                    dialog._log_message(
                        f"❌ {table}: Fehler - {result.get('error', 'Unknown')}",
                        "error"
                    )
            
            # Validation (optional)
            validation_results = None
            if config["options"]["validation"]:
                dialog._log_message("✓ Validierung gestartet...", "info")
                
                validator = DataValidator(migration_config)
                validation_results = {}
                
                for table in config["options"]["tables"]:
                    val_result = validator.validate_migration(table)
                    validation_results[table] = val_result
                    
                    if val_result["valid"]:
                        dialog._log_message(
                            f"✅ {table} Validierung: PASS (Match Rate: {val_result['details']['id_match_rate']:.1%})",
                            "success"
                        )
                    else:
                        dialog._log_message(
                            f"❌ {table} Validierung: FAIL",
                            "error"
                        )
            
            # Ergebnisse zusammenfassen
            duration = time.time() - start_time
            total_successful = sum(r["successful_records"] for r in migration_results.values())
            total_failed = sum(r["failed_records"] for r in migration_results.values())
            
            result = {
                "success": total_failed == 0,
                "duration": duration,
                "total_records": total_records,
                "successful_records": total_successful,
                "failed_records": total_failed,
                "records_per_second": total_records / duration if duration > 0 else 0,
                "migration_results": migration_results,
                "gap_detection": gap_results,
                "validation": validation_results
            }
            
            dialog.show_results(result)
            
        except Exception as e:
            import traceback
            error_msg = f"Migration Fehler: {str(e)}\n{traceback.format_exc()}"
            dialog._log_message(f"❌ {error_msg}", "error")
            
            result = {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            dialog.show_results(result)
    
    def _on_migration_gap_detection(self, data=None):
        """Führt Gap Detection aus."""
        from tkinter import filedialog, messagebox
        from migration.gap_detector import GapDetector
        import json
        
        # SQLite DB auswählen
        db_path = filedialog.askopenfilename(
            title="SQLite Datenbank auswählen",
            filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")]
        )
        
        if not db_path:
            return
        
        try:
            detector = GapDetector(db_path)
            gaps = detector.detect_all_gaps()
            
            total_gaps = sum(len(gap_list) for gap_list in gaps.values())
            
            # Ergebnisse anzeigen
            msg = f"Gap Detection abgeschlossen!\n\n"
            msg += f"Datenbank: {db_path}\n\n"
            
            for gap_type, gap_list in gaps.items():
                msg += f"{gap_type}: {len(gap_list)} Gaps\n"
            
            msg += f"\nGesamt: {total_gaps} Gaps gefunden"
            
            messagebox.showinfo("Gap Detection", msg)
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Gap Detection Fehler:\n{str(e)}")
    
    def _on_migration_validate(self, data=None):
        """Führt Validierung aus."""
        from tkinter import filedialog, messagebox
        from migration.validation import DataValidator
        from migration.migration_tool import MigrationConfig
        
        # SQLite DB auswählen
        db_path = filedialog.askopenfilename(
            title="SQLite Datenbank auswählen",
            filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")]
        )
        
        if not db_path:
            return
        
        try:
            config = MigrationConfig(
                source_config={"type": "sqlite", "db_path": db_path},
                target_config={"type": "uds3_polyglot"}
            )
            
            validator = DataValidator(config)
            result = validator.validate_migration("vpb_processes")
            
            # Ergebnisse anzeigen
            msg = f"Validierung abgeschlossen!\n\n"
            msg += f"Status: {'✅ VALID' if result['valid'] else '❌ INVALID'}\n"
            msg += f"Datensätze: {result['details']['record_count']}\n"
            msg += f"ID Match Rate: {result['details']['id_match_rate']:.1%}\n"
            msg += f"Checksum Match Rate: {result['details'].get('checksum_match_rate', 0):.1%}\n"
            
            if result.get('errors'):
                msg += f"\nFehler: {len(result['errors'])}"
            
            messagebox.showinfo("Validierung", msg)
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Validierung Fehler:\n{str(e)}")
    
    def _on_migration_configure(self, data=None):
        """Öffnet Migration Configuration Dialog."""
        self._on_migration_start(data)
    
    def _on_migration_show_report(self, data=None):
        """Zeigt letzten Migration Report."""
        from tkinter import filedialog, messagebox
        import json
        
        # Report-Datei auswählen
        report_path = filedialog.askopenfilename(
            title="Migration Report auswählen",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            initialdir="."
        )
        
        if not report_path:
            return
        
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
            
            # Ergebnisse formatieren
            msg = f"Migration Report\n\n"
            msg += f"Status: {'✅ ERFOLG' if report.get('success') else '❌ FEHLER'}\n"
            msg += f"Dauer: {report.get('duration', 0):.2f}s\n"
            msg += f"Datensätze: {report.get('total_records', 0)}\n"
            msg += f"Erfolgreich: {report.get('successful_records', 0)}\n"
            msg += f"Fehler: {report.get('failed_records', 0)}\n"
            msg += f"Durchsatz: {report.get('records_per_second', 0):.1f} rec/s\n"
            
            messagebox.showinfo("Migration Report", msg)
            
        except Exception as e:
            messagebox.showerror("Fehler", f"Report laden Fehler:\n{str(e)}")
    
    # ============================================================================
    # Main Loop
    # ============================================================================
    
    def run(self):
        """Startet die Hauptschleife der Anwendung."""
        # GUI updaten damit alle Größen bekannt sind
        self.root.update_idletasks()
        
        # Benutzerprofil wiederherstellen (UI-Zustand)
        self._restore_user_profile()
        
        # Koordinatenursprung vertikal mittig setzen (y=0 in Mitte)
        # Verzögert aufrufen, wenn das Canvas gerendert wurde
        if hasattr(self, 'canvas'):
            def center_after_render():
                canvas_h = self.canvas.winfo_height()
                if canvas_h > 1:  # Canvas ist gerendert
                    self.canvas.center_time_axis_vertical()
                    print(f"✅ Koordinatenursprung zentriert: Canvas-Höhe={canvas_h}px, view_ty={self.canvas.view_ty:.1f}")
                else:  # Noch nicht gerendert, nochmal versuchen
                    self.root.after(50, center_after_render)
            self.root.after(100, center_after_render)
        
        # Mainloop starten
        self.root.mainloop()
    
    def _restore_user_profile(self):
        """Stellt Benutzereinstellungen aus dem Profil wieder her."""
        try:
            profile = self.user_profile
            
            # Canvas-Ansicht wiederherstellen
            if hasattr(self, 'canvas'):
                canvas = self.canvas
                view = profile.canvas_view
                
                # Zoom-Level
                if view.zoom_level != 1.0:
                    canvas.view_scale = view.zoom_level
                
                # Pan-Position
                if view.pan_x != 0.0 or view.pan_y != 0.0:
                    canvas.view_tx = view.pan_x
                    canvas.view_ty = view.pan_y
                
                # Grid-Sichtbarkeit
                canvas.grid_visible = view.grid_visible
                canvas.snap_to_grid = view.snap_to_grid
                
                # Rulers und Minimap
                # TODO: Implementiere ruler_visible und minimap_visible Steuerung
                
                canvas.redraw_all()
                print(f"✅ Canvas-Ansicht wiederhergestellt: Zoom={view.zoom_level:.1f}x, Grid={'an' if view.grid_visible else 'aus'}")
            
            # Sidebar-Breiten wiederherstellen
            if hasattr(self, 'paned_window'):
                prefs = profile.ui_preferences
                
                # Linke Sidebar
                if prefs.left_sidebar_width > 0:
                    try:
                        self.paned_window.sashpos(0, prefs.left_sidebar_width)
                    except:
                        pass
                
                # Rechte Sidebar
                if prefs.right_sidebar_width > 0:
                    try:
                        # Position vom rechten Rand
                        total_width = self.root.winfo_width()
                        right_sash_pos = total_width - prefs.right_sidebar_width
                        self.paned_window.sashpos(1, right_sash_pos)
                    except:
                        pass
                
                print(f"✅ Sidebar-Breiten wiederhergestellt: {prefs.left_sidebar_width}px / {prefs.right_sidebar_width}px")
            
            # Recent Files in Menü laden
            recent_files = profile.workspace.recent_files
            if recent_files and hasattr(self, 'menu_bar'):
                self.menu_bar.update_recent_files(recent_files)
                print(f"✅ {len(recent_files)} Recent Files wiederhergestellt")
            
            # Letzte Datei öffnen (optional, nur wenn --restore Flag)
            if hasattr(self.args, 'restore') and self.args.restore:
                last_file = profile.workspace.last_opened_file
                if last_file and os.path.exists(last_file):
                    self.root.after(200, lambda: self.event_bus.publish("ui:menu:file:open", {"file_path": last_file}))
                    print(f"✅ Letzte Datei wird geöffnet: {last_file}")
        
        except Exception as e:
            print(f"⚠️ Fehler beim Wiederherstellen des Benutzerprofils: {e}")
    
    def _save_user_profile(self):
        """Speichert aktuelle Benutzereinstellungen im Profil."""
        try:
            profile = self.user_profile
            
            # Canvas-Ansicht speichern
            if hasattr(self, 'canvas'):
                canvas = self.canvas
                view = profile.canvas_view
                
                view.zoom_level = float(canvas.view_scale)
                view.pan_x = float(canvas.view_tx)
                view.pan_y = float(canvas.view_ty)
                view.grid_visible = bool(canvas.grid_visible)
                view.snap_to_grid = bool(canvas.snap_to_grid)
            
            # Sidebar-Breiten speichern
            if hasattr(self, 'paned_window'):
                prefs = profile.ui_preferences
                
                try:
                    # Linke Sidebar
                    left_width = self.paned_window.sashpos(0)
                    if left_width > 0:
                        prefs.left_sidebar_width = left_width
                    
                    # Rechte Sidebar (berechne aus Gesamt-Breite)
                    total_width = self.root.winfo_width()
                    right_sash_pos = self.paned_window.sashpos(1)
                    right_width = total_width - right_sash_pos
                    if right_width > 0:
                        prefs.right_sidebar_width = right_width
                except:
                    pass
            
            # Aktuell geöffnete Datei speichern
            if hasattr(self, 'document_controller'):
                current_file = self.document_controller.current_file_path
                if current_file:
                    self.user_profile_manager.add_recent_file(current_file)
            
            # Profil speichern
            success = self.user_profile_manager.save(profile)
            if success:
                print("✅ Benutzerprofil gespeichert")
            
        except Exception as e:
            print(f"⚠️ Fehler beim Speichern des Benutzerprofils: {e}")

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
