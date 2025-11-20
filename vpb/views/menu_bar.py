"""
MenuBar View - Hauptmenü und Toolbar des VPB Process Designers.

Reine View-Komponente für die Menüleiste und Toolbar.
Publiziert alle Benutzeraktionen über den Event-Bus.

Event-Struktur:
    - ui:action:file.*      (Datei-Menü Aktionen)
    - ui:action:edit.*      (Bearbeiten-Menü Aktionen)
    - ui:action:arrange.*   (Anordnen-Menü Aktionen)
    - ui:action:view.*      (Ansicht-Menü Aktionen)
    - ui:action:tools.*     (Werkzeuge-Menü Aktionen)
    - ui:action:settings.*  (Einstellungen-Menü Aktionen)
    - ui:action:ai.*        (AI-Menü Aktionen)
    - ui:action:help.*      (Hilfe-Menü Aktionen)
    - ui:setting:changed    (Setting-Änderungen via Checkbutton/Radiobutton)

Autor: GitHub Copilot (Phase 4: Views Layer)
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, TYPE_CHECKING
from vpb.infrastructure.event_bus import get_global_event_bus
from vpb.ui.theme import get_theme_manager
from vpb.ui.icons import get_icon_manager
from vpb.ui.fonts import get_font_manager

if TYPE_CHECKING:
    from vpb.infrastructure.event_bus import EventBus


class MenuBarView:
    """
    MenuBar View für den VPB Process Designer.
    
    Erstellt die komplette Menüleiste mit allen Menüs und publiziert
    alle Benutzeraktionen über den Event-Bus.
    
    Menüs:
        - Datei: Neu, Öffnen, Speichern, Export, Beenden
        - Bearbeiten: Element/Verbindung hinzufügen, Löschen, Undo/Redo
        - Anordnen: Ausrichten, Verteilen
        - Ansicht: Zoom, Grid, Zeitachse, Hierarchien, Routing
        - Werkzeuge: Prozess prüfen
        - Einstellungen: Element-Stile, Navigation, Autosave
        - AI: Ollama, Text→Diagramm, Diagnose/Fix, Merge-Einstellungen
        - Hilfe: Tastaturkürzel, Über
    
    Attribute:
        menubar: Tkinter Menu-Widget
        event_bus: Event-Bus für Action-Publishing
        
    Beispiel:
        >>> menu_bar = MenuBarView(parent_window)
        >>> menu_bar.set_snap_to_grid(True)
        >>> menu_bar.set_routing_mode("orthogonal")
    """
    
    def __init__(
        self,
        parent: tk.Tk,
        event_bus: Optional["EventBus"] = None
    ):
        """
        Initialisiert die MenuBar View.
        
        Args:
            parent: Parent Tk-Widget (normalerweise Hauptfenster)
            event_bus: Event-Bus Instanz (optional, nutzt global event bus)
        """
        self.parent = parent
        self.event_bus = event_bus or get_global_event_bus()
        
        # UI Managers
        self.theme = get_theme_manager()
        self.icons = get_icon_manager()
        self.fonts = get_font_manager()
        
        # Tkinter-Variablen für Checkbuttons & Radiobuttons
        self._snap_to_grid_var = tk.BooleanVar(value=False)
        self._show_grid_var = tk.BooleanVar(value=True)
        self._show_timeline_var = tk.BooleanVar(value=False)
        self._routing_mode_var = tk.StringVar(value="smart-plus")
        self._mousewheel_mode_var = tk.StringVar(value="zoom-primary")
        self._merge_snap_var = tk.BooleanVar(value=True)
        self._merge_mode_var = tk.StringVar(value="fill-empty")
        self._auto_rename_var = tk.BooleanVar(value=True)
        
        # Menüleiste erstellen
        self.menubar = tk.Menu(parent)
        self._create_menus()
        
        # Menüleiste dem Fenster zuweisen
        parent.config(menu=self.menubar)
    
    def _create_menus(self) -> None:
        """Erstellt alle Menüs der Menüleiste."""
        self._create_file_menu()
        self._create_edit_menu()
        self._create_arrange_menu()
        self._create_view_menu()
        self._create_tools_menu()
        self._create_settings_menu()
        self._create_ai_menu()
        self._create_help_menu()
    
    def _create_file_menu(self) -> None:
        """Erstellt das Datei-Menü mit Icons."""
        file_menu = tk.Menu(self.menubar, tearoff=0)
        
        file_menu.add_command(
            label=f"{self.icons.get('new')} Neu (Strg+N)",
            command=lambda: self._publish_action("file.new")
        )
        file_menu.add_command(
            label=f"{self.icons.get('open')} Öffnen… (Strg+O)",
            command=lambda: self._publish_action("file.open")
        )
        
        # Recent Files Untermenü
        self.recent_files_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(
            label=f"{self.icons.get('recent')} Zuletzt geöffnet",
            menu=self.recent_files_menu
        )
        self._update_recent_files_menu([])  # Initial leer
        
        file_menu.add_command(
            label=f"{self.icons.get('ai')} AI-Ingestion Wizard…",
            command=lambda: self._publish_action("file.ingestion_wizard")
        )
        file_menu.add_separator()
        file_menu.add_command(
            label=f"{self.icons.get('save')} Speichern (Strg+S)",
            command=lambda: self._publish_action("file.save")
        )
        file_menu.add_command(
            label=f"{self.icons.get('save_as')} Speichern unter…",
            command=lambda: self._publish_action("file.save_as")
        )
        file_menu.add_command(
            label=f"{self.icons.get('settings')} Metadaten bearbeiten…",
            command=lambda: self._publish_action("file.edit_metadata")
        )
        file_menu.add_separator()
        
        # Export-Untermenü
        export_menu = tk.Menu(file_menu, tearoff=0)
        export_menu.add_command(
            label=f"{self.icons.get('export')} Als PNG…",
            command=lambda: self._publish_action("file.export", {"format": "png"})
        )
        export_menu.add_command(
            label=f"{self.icons.get('export')} Als PDF…",
            command=lambda: self._publish_action("file.export", {"format": "pdf"})
        )
        export_menu.add_command(
            label=f"{self.icons.get('export')} Als SVG…",
            command=lambda: self._publish_action("file.export", {"format": "svg"})
        )
        export_menu.add_command(
            label=f"{self.icons.get('export')} Als PostScript…",
            command=lambda: self._publish_action("file.export", {"format": "ps"})
        )
        file_menu.add_cascade(
            label=f"{self.icons.get('export')} Exportieren",
            menu=export_menu
        )
        
        file_menu.add_separator()
        file_menu.add_command(
            label=f"{self.icons.get('close')} Beenden",
            command=lambda: self._publish_action("file.quit")
        )
        
        self.menubar.add_cascade(label="Datei", menu=file_menu)
    
    def _create_edit_menu(self) -> None:
        """Erstellt das Bearbeiten-Menü mit Icons."""
        edit_menu = tk.Menu(self.menubar, tearoff=0)
        
        edit_menu.add_command(
            label=f"{self.icons.get('add_element')} Element hinzufügen… (E)",
            command=lambda: self._publish_action("edit.add_element")
        )
        edit_menu.add_command(
            label=f"{self.icons.get('add_connection')} Verbindung hinzufügen (C)",
            command=lambda: self._publish_action("edit.add_connection")
        )
        edit_menu.add_separator()
        edit_menu.add_command(
            label=f"{self.icons.get('delete')} Löschen (Entf)",
            command=lambda: self._publish_action("edit.delete")
        )
        edit_menu.add_command(
            label=f"{self.icons.get('duplicate')} Duplizieren (Strg+D)",
            command=lambda: self._publish_action("edit.duplicate")
        )
        edit_menu.add_separator()
        
        # Snap-to-Grid als Checkbutton
        edit_menu.add_checkbutton(
            label=f"{self.icons.get('grid')} Snap-to-Grid",
            variable=self._snap_to_grid_var,
            command=lambda: self._on_snap_to_grid_changed()
        )
        
        edit_menu.add_command(
            label=f"{self.icons.get('add_connection')} Link-Modus umschalten (L)",
            command=lambda: self._publish_action("edit.toggle_link_mode")
        )
        edit_menu.add_separator()
        edit_menu.add_command(
            label="Palette neu laden (Strg+R)",
            command=lambda: self._publish_action("edit.reload_palette")
        )
        edit_menu.add_command(
            label="Neu zeichnen (F5)",
            command=lambda: self._publish_action("edit.redraw")
        )
        edit_menu.add_command(
            label="Auto-Layout",
            command=lambda: self._publish_action("edit.auto_layout")
        )
        edit_menu.add_separator()
        edit_menu.add_command(
            label="Gruppe aus Auswahl bilden",
            command=lambda: self._publish_action("edit.group")
        )
        edit_menu.add_command(
            label="Zeitschleife aus Auswahl bilden",
            command=lambda: self._publish_action("edit.time_loop")
        )
        edit_menu.add_command(
            label="Gruppe auflösen",
            command=lambda: self._publish_action("edit.ungroup")
        )
        edit_menu.add_separator()
        edit_menu.add_command(
            label="Rückgängig (Strg+Z)",
            command=lambda: self._publish_action("edit.undo")
        )
        edit_menu.add_command(
            label="Wiederherstellen (Strg+Y)",
            command=lambda: self._publish_action("edit.redo")
        )
        
        self.menubar.add_cascade(label="Bearbeiten", menu=edit_menu)
    
    def _create_arrange_menu(self) -> None:
        """Erstellt das Anordnen-Menü."""
        arrange_menu = tk.Menu(self.menubar, tearoff=0)
        
        # Ausrichten-Untermenü
        align_menu = tk.Menu(arrange_menu, tearoff=0)
        align_menu.add_command(
            label="Links",
            command=lambda: self._publish_action("arrange.align", {"mode": "left"})
        )
        align_menu.add_command(
            label="Horizontal zentrieren",
            command=lambda: self._publish_action("arrange.align", {"mode": "center_h"})
        )
        align_menu.add_command(
            label="Rechts",
            command=lambda: self._publish_action("arrange.align", {"mode": "right"})
        )
        align_menu.add_separator()
        align_menu.add_command(
            label="Oben",
            command=lambda: self._publish_action("arrange.align", {"mode": "top"})
        )
        align_menu.add_command(
            label="Vertikal mittig",
            command=lambda: self._publish_action("arrange.align", {"mode": "center_v"})
        )
        align_menu.add_command(
            label="Unten",
            command=lambda: self._publish_action("arrange.align", {"mode": "bottom"})
        )
        arrange_menu.add_cascade(label="Ausrichten", menu=align_menu)
        
        # Verteilen-Untermenü
        distribute_menu = tk.Menu(arrange_menu, tearoff=0)
        distribute_menu.add_command(
            label="Horizontal",
            command=lambda: self._publish_action("arrange.distribute", {"mode": "horizontal"})
        )
        distribute_menu.add_command(
            label="Vertikal",
            command=lambda: self._publish_action("arrange.distribute", {"mode": "vertical"})
        )
        arrange_menu.add_cascade(label="Verteilen", menu=distribute_menu)
        
        self.menubar.add_cascade(label="Anordnen", menu=arrange_menu)
    
    def _create_view_menu(self) -> None:
        """Erstellt das Ansicht-Menü."""
        view_menu = tk.Menu(self.menubar, tearoff=0)
        
        # Zoom-Befehle
        view_menu.add_command(
            label="Zoom zurücksetzen (Strg+0)",
            command=lambda: self._publish_action("view.zoom_reset")
        )
        view_menu.add_command(
            label="Auf Diagramm zoomen (Strg+1)",
            command=lambda: self._publish_action("view.zoom_to_fit")
        )
        view_menu.add_command(
            label="Zoom auf Auswahl (Strg+2)",
            command=lambda: self._publish_action("view.zoom_to_selection")
        )
        view_menu.add_command(
            label="Auswahl zentrieren (Strg+3)",
            command=lambda: self._publish_action("view.center_selection")
        )
        view_menu.add_separator()
        
        # Grid & Zeitachse als Checkbuttons
        view_menu.add_checkbutton(
            label="Grid anzeigen (G)",
            variable=self._show_grid_var,
            command=lambda: self._on_show_grid_changed()
        )
        view_menu.add_checkbutton(
            label="Zeitachse anzeigen (T)",
            variable=self._show_timeline_var,
            command=lambda: self._on_show_timeline_changed()
        )
        view_menu.add_command(
            label="Zeitintervall setzen…",
            command=lambda: self._publish_action("view.set_time_interval")
        )
        view_menu.add_separator()
        
        # Hierarchien-Untermenü
        hierarchy_menu = tk.Menu(view_menu, tearoff=0)
        hierarchy_menu.add_command(
            label="Hierarchien verwalten…",
            command=lambda: self._publish_action("view.manage_hierarchies")
        )
        hierarchy_menu.add_command(
            label="Hierarchie wechseln…",
            command=lambda: self._publish_action("view.switch_hierarchy")
        )
        hierarchy_menu.add_command(
            label="Hierarchie-Panel",
            command=lambda: self._publish_action("view.hierarchy_panel")
        )
        view_menu.add_cascade(label="Hierarchien", menu=hierarchy_menu)
        
        view_menu.add_separator()
        
        # Routing-Modi als Radiobuttons
        routing_menu = tk.Menu(view_menu, tearoff=0)
        routing_menu.add_radiobutton(
            label="Gerade",
            value="straight",
            variable=self._routing_mode_var,
            command=lambda: self._on_routing_mode_changed()
        )
        routing_menu.add_radiobutton(
            label="Orthogonal",
            value="orthogonal",
            variable=self._routing_mode_var,
            command=lambda: self._on_routing_mode_changed()
        )
        routing_menu.add_radiobutton(
            label="Kurvig",
            value="curved",
            variable=self._routing_mode_var,
            command=lambda: self._on_routing_mode_changed()
        )
        routing_menu.add_radiobutton(
            label="Smart",
            value="smart",
            variable=self._routing_mode_var,
            command=lambda: self._on_routing_mode_changed()
        )
        routing_menu.add_radiobutton(
            label="Smart+",
            value="smart-plus",
            variable=self._routing_mode_var,
            command=lambda: self._on_routing_mode_changed()
        )
        view_menu.add_cascade(label="Routing-Modus", menu=routing_menu)
        
        view_menu.add_separator()
        
        # Mausrad-Verhalten als Radiobuttons
        mousewheel_menu = tk.Menu(view_menu, tearoff=0)
        mousewheel_menu.add_radiobutton(
            label="Mausrad: Zoomen (Strg=Pannen)",
            value="zoom-primary",
            variable=self._mousewheel_mode_var,
            command=lambda: self._on_mousewheel_mode_changed()
        )
        mousewheel_menu.add_radiobutton(
            label="Mausrad: Pannen (Strg=Zoomen)",
            value="pan-primary",
            variable=self._mousewheel_mode_var,
            command=lambda: self._on_mousewheel_mode_changed()
        )
        view_menu.add_cascade(label="Mausrad-Verhalten", menu=mousewheel_menu)
        
        self.menubar.add_cascade(label="Ansicht", menu=view_menu)
    
    def _create_tools_menu(self) -> None:
        """Erstellt das Werkzeuge-Menü."""
        tools_menu = tk.Menu(self.menubar, tearoff=0)
        
        tools_menu.add_command(
            label="Prozess prüfen…",
            command=lambda: self._publish_action("tools.validate_process")
        )
        
        tools_menu.add_separator()
        
        # Migration-Untermenü
        migration_menu = tk.Menu(tools_menu, tearoff=0)
        migration_menu.add_command(
            label="Migration starten…",
            command=lambda: self._publish_action("tools.migration.start")
        )
        migration_menu.add_command(
            label="Gap Detection ausführen…",
            command=lambda: self._publish_action("tools.migration.gap_detection")
        )
        migration_menu.add_command(
            label="Validierung durchführen…",
            command=lambda: self._publish_action("tools.migration.validate")
        )
        migration_menu.add_separator()
        migration_menu.add_command(
            label="Migration Konfiguration…",
            command=lambda: self._publish_action("tools.migration.configure")
        )
        migration_menu.add_command(
            label="Letzten Report anzeigen…",
            command=lambda: self._publish_action("tools.migration.show_report")
        )
        tools_menu.add_cascade(label="SQLite → UDS3 Migration", menu=migration_menu)
        
        self.menubar.add_cascade(label="Werkzeuge", menu=tools_menu)
    
    def _create_settings_menu(self) -> None:
        """Erstellt das Einstellungen-Menü."""
        settings_menu = tk.Menu(self.menubar, tearoff=0)
        
        settings_menu.add_command(
            label="Element-Stile bearbeiten...",
            command=lambda: self._publish_action("settings.edit_element_styles")
        )
        settings_menu.add_command(
            label="Navigation Schrittgrößen…",
            command=lambda: self._publish_action("settings.configure_navigation")
        )
        settings_menu.add_command(
            label="Autosave Einstellungen…",
            command=lambda: self._publish_action("settings.configure_autosave")
        )
        
        self.menubar.add_cascade(label="Einstellungen", menu=settings_menu)
    
    def _create_ai_menu(self) -> None:
        """Erstellt das AI-Menü."""
        ai_menu = tk.Menu(self.menubar, tearoff=0)
        
        ai_menu.add_command(
            label="Ollama konfigurieren...",
            command=lambda: self._publish_action("ai.configure_ollama")
        )
        ai_menu.add_command(
            label="Ollama Health-Check",
            command=lambda: self._publish_action("ai.health_check")
        )
        ai_menu.add_command(
            label="Modell wechseln…",
            command=lambda: self._publish_action("ai.quick_switch_model")
        )
        ai_menu.add_separator()
        ai_menu.add_command(
            label="Text → Diagramm…",
            command=lambda: self._publish_action("ai.text_to_diagram")
        )
        ai_menu.add_command(
            label="Nächster Schritt vorschlagen…",
            command=lambda: self._publish_action("ai.suggest_next_step")
        )
        ai_menu.add_command(
            label="Diagnose/Fix…",
            command=lambda: self._publish_action("ai.diagnose_fix")
        )
        ai_menu.add_separator()
        
        # Merge-Einstellungen
        ai_menu.add_checkbutton(
            label="Merge: Raster-Snap (50)",
            variable=self._merge_snap_var,
            command=lambda: self._on_merge_snap_changed()
        )
        
        # Merge-Modus-Untermenü
        merge_mode_menu = tk.Menu(ai_menu, tearoff=0)
        merge_mode_menu.add_radiobutton(
            label="Keine Updates",
            value="none",
            variable=self._merge_mode_var,
            command=lambda: self._on_merge_mode_changed()
        )
        merge_mode_menu.add_radiobutton(
            label="Nur leere Felder füllen",
            value="fill-empty",
            variable=self._merge_mode_var,
            command=lambda: self._on_merge_mode_changed()
        )
        merge_mode_menu.add_radiobutton(
            label="Bestehende überschreiben",
            value="overwrite",
            variable=self._merge_mode_var,
            command=lambda: self._on_merge_mode_changed()
        )
        ai_menu.add_cascade(label="Merge: Update-Modus", menu=merge_mode_menu)
        
        ai_menu.add_checkbutton(
            label="Auto-Rename bei ID-Konflikten",
            variable=self._auto_rename_var,
            command=lambda: self._on_auto_rename_changed()
        )
        
        self.menubar.add_cascade(label="AI", menu=ai_menu)
    
    def _create_help_menu(self) -> None:
        """Erstellt das Hilfe-Menü mit Icons."""
        help_menu = tk.Menu(self.menubar, tearoff=0)
        
        help_menu.add_command(
            label=f"{self.icons.get('help')} Tastaturkürzel (F1)",
            command=lambda: self._publish_action("help.shortcuts")
        )
        help_menu.add_command(
            label=f"{self.icons.get('info')} Über",
            command=lambda: self._publish_action("help.about")
        )
        
        self.menubar.add_cascade(label="Hilfe", menu=help_menu)
    
    # Event Publishing
    # ---------------
    
    def _publish_action(self, action: str, data: Optional[dict] = None) -> None:
        """
        Publiziert eine UI-Action über den Event-Bus.
        
        Args:
            action: Action-Name (z.B. "file.new")
            data: Optionale Daten (z.B. {"format": "png"})
        """
        event_name = f"ui:action:{action}"
        payload = data or {}
        self.event_bus.publish(event_name, payload)
    
    def _publish_setting_changed(self, setting: str, value: any) -> None:
        """
        Publiziert eine Setting-Änderung über den Event-Bus.
        
        Args:
            setting: Setting-Name (z.B. "snap_to_grid")
            value: Neuer Wert
        """
        self.event_bus.publish("ui:setting:changed", {
            "setting": setting,
            "value": value
        })
    
    # Setting Change Handlers
    # ----------------------
    
    def _on_snap_to_grid_changed(self) -> None:
        """Handler für Snap-to-Grid Toggle."""
        value = self._snap_to_grid_var.get()
        self._publish_setting_changed("snap_to_grid", value)
    
    def _on_show_grid_changed(self) -> None:
        """Handler für Grid-Anzeige Toggle."""
        value = self._show_grid_var.get()
        self._publish_setting_changed("show_grid", value)
    
    def _on_show_timeline_changed(self) -> None:
        """Handler für Zeitachse-Anzeige Toggle."""
        value = self._show_timeline_var.get()
        self._publish_setting_changed("show_timeline", value)
    
    def _on_routing_mode_changed(self) -> None:
        """Handler für Routing-Modus Änderung."""
        value = self._routing_mode_var.get()
        self._publish_setting_changed("routing_mode", value)
    
    def _on_mousewheel_mode_changed(self) -> None:
        """Handler für Mausrad-Modus Änderung."""
        value = self._mousewheel_mode_var.get()
        self._publish_setting_changed("mousewheel_mode", value)
    
    def _on_merge_snap_changed(self) -> None:
        """Handler für Merge-Snap Toggle."""
        value = self._merge_snap_var.get()
        self._publish_setting_changed("merge_snap", value)
    
    def _on_merge_mode_changed(self) -> None:
        """Handler für Merge-Modus Änderung."""
        value = self._merge_mode_var.get()
        self._publish_setting_changed("merge_mode", value)
    
    def _on_auto_rename_changed(self) -> None:
        """Handler für Auto-Rename Toggle."""
        value = self._auto_rename_var.get()
        self._publish_setting_changed("auto_rename", value)
    
    # Public API for External Control
    # -------------------------------
    
    def set_snap_to_grid(self, enabled: bool) -> None:
        """
        Setzt den Snap-to-Grid Status.
        
        Args:
            enabled: True = aktiviert, False = deaktiviert
        """
        self._snap_to_grid_var.set(enabled)
    
    def get_snap_to_grid(self) -> bool:
        """
        Gibt den aktuellen Snap-to-Grid Status zurück.
        
        Returns:
            True = aktiviert, False = deaktiviert
        """
        return self._snap_to_grid_var.get()
    
    def set_show_grid(self, show: bool) -> None:
        """
        Setzt die Grid-Anzeige.
        
        Args:
            show: True = anzeigen, False = verstecken
        """
        self._show_grid_var.set(show)
    
    def get_show_grid(self) -> bool:
        """
        Gibt den aktuellen Grid-Anzeige Status zurück.
        
        Returns:
            True = angezeigt, False = versteckt
        """
        return self._show_grid_var.get()
    
    def set_show_timeline(self, show: bool) -> None:
        """
        Setzt die Zeitachsen-Anzeige.
        
        Args:
            show: True = anzeigen, False = verstecken
        """
        self._show_timeline_var.set(show)
    
    def get_show_timeline(self) -> bool:
        """
        Gibt den aktuellen Zeitachsen-Anzeige Status zurück.
        
        Returns:
            True = angezeigt, False = versteckt
        """
        return self._show_timeline_var.get()
    
    def set_routing_mode(self, mode: str) -> None:
        """
        Setzt den Routing-Modus.
        
        Args:
            mode: Routing-Modus ("straight", "orthogonal", "curved", "smart", "smart-plus")
        """
        valid_modes = ["straight", "orthogonal", "curved", "smart", "smart-plus"]
        if mode not in valid_modes:
            raise ValueError(f"Invalid routing mode: {mode}. Must be one of {valid_modes}")
        self._routing_mode_var.set(mode)
    
    def get_routing_mode(self) -> str:
        """
        Gibt den aktuellen Routing-Modus zurück.
        
        Returns:
            Routing-Modus ("straight", "orthogonal", "curved", "smart", "smart-plus")
        """
        return self._routing_mode_var.get()
    
    def set_mousewheel_mode(self, mode: str) -> None:
        """
        Setzt den Mausrad-Modus.
        
        Args:
            mode: Mausrad-Modus ("zoom-primary", "pan-primary")
        """
        valid_modes = ["zoom-primary", "pan-primary"]
        if mode not in valid_modes:
            raise ValueError(f"Invalid mousewheel mode: {mode}. Must be one of {valid_modes}")
        self._mousewheel_mode_var.set(mode)
    
    def get_mousewheel_mode(self) -> str:
        """
        Gibt den aktuellen Mausrad-Modus zurück.
        
        Returns:
            Mausrad-Modus ("zoom-primary", "pan-primary")
        """
        return self._mousewheel_mode_var.get()
    
    def set_merge_snap(self, enabled: bool) -> None:
        """
        Setzt den Merge-Snap Status.
        
        Args:
            enabled: True = aktiviert, False = deaktiviert
        """
        self._merge_snap_var.set(enabled)
    
    def get_merge_snap(self) -> bool:
        """
        Gibt den aktuellen Merge-Snap Status zurück.
        
        Returns:
            True = aktiviert, False = deaktiviert
        """
        return self._merge_snap_var.get()
    
    def set_merge_mode(self, mode: str) -> None:
        """
        Setzt den Merge-Modus.
        
        Args:
            mode: Merge-Modus ("none", "fill-empty", "overwrite")
        """
        valid_modes = ["none", "fill-empty", "overwrite"]
        if mode not in valid_modes:
            raise ValueError(f"Invalid merge mode: {mode}. Must be one of {valid_modes}")
        self._merge_mode_var.set(mode)
    
    def get_merge_mode(self) -> str:
        """
        Gibt den aktuellen Merge-Modus zurück.
        
        Returns:
            Merge-Modus ("none", "fill-empty", "overwrite")
        """
        return self._merge_mode_var.get()
    
    def set_auto_rename(self, enabled: bool) -> None:
        """
        Setzt den Auto-Rename Status.
        
        Args:
            enabled: True = aktiviert, False = deaktiviert
        """
        self._auto_rename_var.set(enabled)
    
    def get_auto_rename(self) -> bool:
        """
        Gibt den aktuellen Auto-Rename Status zurück.
        
        Returns:
            True = aktiviert, False = deaktiviert
        """
        return self._auto_rename_var.get()
    
    def update_recent_files(self, recent_files: list) -> None:
        """
        Aktualisiert das Recent Files Menü.
        
        Args:
            recent_files: Liste der zuletzt geöffneten Dateien
        """
        self._update_recent_files_menu(recent_files)
    
    def _update_recent_files_menu(self, recent_files: list) -> None:
        """
        Aktualisiert das Recent Files Untermenü.
        
        Args:
            recent_files: Liste der Dateipfade
        """
        import os
        
        # Lösche alle bisherigen Einträge
        self.recent_files_menu.delete(0, tk.END)
        
        if not recent_files:
            self.recent_files_menu.add_command(
                label="(Keine zuletzt geöffneten Dateien)",
                state="disabled"
            )
            return
        
        # Füge Dateien hinzu (max 10)
        for i, file_path in enumerate(recent_files[:10]):
            # Zeige nur Dateinamen (nicht vollständigen Pfad)
            file_name = os.path.basename(file_path)
            label = f"{i+1}. {file_name}"
            
            # Command muss file_path als default parameter haben (closure)
            self.recent_files_menu.add_command(
                label=label,
                command=lambda fp=file_path: self._publish_action("file.open", {"file_path": fp})
            )
        
        # Separator und "Clear Recent Files"
        self.recent_files_menu.add_separator()
        self.recent_files_menu.add_command(
            label="Liste leeren",
            command=lambda: self._publish_action("file.clear_recent_files")
        )
    
    def __repr__(self) -> str:
        """String-Repräsentation für Debugging."""
        return (
            f"MenuBarView("
            f"snap_to_grid={self.get_snap_to_grid()}, "
            f"show_grid={self.get_show_grid()}, "
            f"routing_mode={self.get_routing_mode()}"
            f")"
        )


# Factory Functions
# ----------------

def create_menu_bar(
    parent: tk.Tk,
    event_bus: Optional["EventBus"] = None
) -> MenuBarView:
    """
    Factory-Funktion zum Erstellen einer MenuBar View.
    
    Args:
        parent: Parent Tk-Widget
        event_bus: Event-Bus Instanz (optional)
    
    Returns:
        MenuBarView Instanz
    
    Beispiel:
        >>> menu_bar = create_menu_bar(root_window)
        >>> menu_bar.set_routing_mode("orthogonal")
    """
    return MenuBarView(parent, event_bus)


def get_menu_bar_state(menu_bar: MenuBarView) -> dict:
    """
    Gibt den aktuellen Status der MenuBar als Dictionary zurück.
    
    Args:
        menu_bar: MenuBarView Instanz
    
    Returns:
        Dictionary mit allen Setting-Werten
    
    Beispiel:
        >>> state = get_menu_bar_state(menu_bar)
        >>> # state = {"snap_to_grid": False, "show_grid": True, ...}
    """
    return {
        "snap_to_grid": menu_bar.get_snap_to_grid(),
        "show_grid": menu_bar.get_show_grid(),
        "show_timeline": menu_bar.get_show_timeline(),
        "routing_mode": menu_bar.get_routing_mode(),
        "mousewheel_mode": menu_bar.get_mousewheel_mode(),
        "merge_snap": menu_bar.get_merge_snap(),
        "merge_mode": menu_bar.get_merge_mode(),
        "auto_rename": menu_bar.get_auto_rename(),
    }


def restore_menu_bar_state(menu_bar: MenuBarView, state: dict) -> None:
    """
    Stellt den MenuBar-Status aus einem Dictionary wieder her.
    
    Args:
        menu_bar: MenuBarView Instanz
        state: Dictionary mit Setting-Werten
    
    Beispiel:
        >>> state = {"snap_to_grid": True, "routing_mode": "orthogonal"}
        >>> restore_menu_bar_state(menu_bar, state)
    """
    if "snap_to_grid" in state:
        menu_bar.set_snap_to_grid(state["snap_to_grid"])
    if "show_grid" in state:
        menu_bar.set_show_grid(state["show_grid"])
    if "show_timeline" in state:
        menu_bar.set_show_timeline(state["show_timeline"])
    if "routing_mode" in state:
        menu_bar.set_routing_mode(state["routing_mode"])
    if "mousewheel_mode" in state:
        menu_bar.set_mousewheel_mode(state["mousewheel_mode"])
    if "merge_snap" in state:
        menu_bar.set_merge_snap(state["merge_snap"])
    if "merge_mode" in state:
        menu_bar.set_merge_mode(state["merge_mode"])
    if "auto_rename" in state:
        menu_bar.set_auto_rename(state["auto_rename"])
