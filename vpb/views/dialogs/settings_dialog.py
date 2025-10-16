"""
Settings Dialog für VPB Process Designer.

Anwendungs-Einstellungen mit mehreren Tabs:
- General: Allgemeine Einstellungen
- Canvas: Canvas-Einstellungen
- Export: Export-Optionen
- AI: AI-Einstellungen
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict

from vpb.infrastructure.event_bus import EventBus


class SettingsDialog(tk.Toplevel):
    """
    Settings Dialog für VPB Process Designer.
    
    Multi-Tab Dialog für Anwendungs-Einstellungen.
    
    Attributes:
        event_bus (EventBus): Event-Bus für Kommunikation
        settings (Dict): Aktuelle Einstellungen
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        event_bus: Optional[EventBus] = None,
        initial_settings: Optional[Dict] = None,
        **kwargs
    ):
        """
        Initialisiert den Settings Dialog.
        
        Args:
            parent: Parent Widget
            event_bus: Event-Bus für Kommunikation
            initial_settings: Initiale Einstellungen
            **kwargs: Zusätzliche Toplevel-Optionen
        """
        super().__init__(parent, **kwargs)
        
        self.event_bus = event_bus
        self.settings = initial_settings or {}
        self._original_settings = self.settings.copy()
        
        # Window configuration
        self.title("Einstellungen")
        self.resizable(False, False)
        
        # Center on parent
        self._center_on_parent(parent)
        
        # Create widgets
        self._create_widgets()
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
    def _center_on_parent(self, parent: tk.Widget):
        """Zentriert das Fenster über dem Parent."""
        self.update_idletasks()
        
        parent.update_idletasks()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        dialog_width = 600
        dialog_height = 500
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
    def _create_widgets(self):
        """Erstellt die Dialog-Widgets."""
        # Main frame
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Notebook (Tabs)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Create tabs
        self._create_general_tab()
        self._create_canvas_tab()
        self._create_export_tab()
        self._create_ai_tab()
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # Buttons
        ttk.Button(
            button_frame,
            text="OK",
            command=self._on_ok,
            width=12
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Abbrechen",
            command=self._on_cancel,
            width=12
        ).pack(side=tk.RIGHT)
        
        ttk.Button(
            button_frame,
            text="Übernehmen",
            command=self._on_apply,
            width=12
        ).pack(side=tk.RIGHT, padx=5)
        
        # Bind Escape
        self.bind("<Escape>", lambda e: self._on_cancel())
        
    def _create_general_tab(self):
        """Erstellt General-Tab."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Allgemein")
        
        # Auto-save
        self.var_autosave = tk.BooleanVar(value=self.settings.get("autosave", True))
        ttk.Checkbutton(
            frame,
            text="Automatisch speichern",
            variable=self.var_autosave
        ).pack(anchor=tk.W, pady=5)
        
        # Auto-save interval
        interval_frame = ttk.Frame(frame)
        interval_frame.pack(anchor=tk.W, pady=5, fill=tk.X)
        
        ttk.Label(interval_frame, text="Speicher-Intervall (Minuten):").pack(side=tk.LEFT)
        self.var_autosave_interval = tk.IntVar(value=self.settings.get("autosave_interval", 5))
        ttk.Spinbox(
            interval_frame,
            from_=1,
            to=60,
            textvariable=self.var_autosave_interval,
            width=10
        ).pack(side=tk.LEFT, padx=10)
        
        # Theme
        theme_frame = ttk.Frame(frame)
        theme_frame.pack(anchor=tk.W, pady=5, fill=tk.X)
        
        ttk.Label(theme_frame, text="Theme:").pack(side=tk.LEFT)
        self.var_theme = tk.StringVar(value=self.settings.get("theme", "System"))
        ttk.Combobox(
            theme_frame,
            textvariable=self.var_theme,
            values=["System", "Hell", "Dunkel"],
            state="readonly",
            width=15
        ).pack(side=tk.LEFT, padx=10)
        
    def _create_canvas_tab(self):
        """Erstellt Canvas-Tab."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Canvas")
        
        # Grid
        self.var_grid_visible = tk.BooleanVar(value=self.settings.get("grid_visible", True))
        ttk.Checkbutton(
            frame,
            text="Raster anzeigen",
            variable=self.var_grid_visible
        ).pack(anchor=tk.W, pady=5)
        
        # Snap to grid
        self.var_snap_to_grid = tk.BooleanVar(value=self.settings.get("snap_to_grid", True))
        ttk.Checkbutton(
            frame,
            text="An Raster einrasten",
            variable=self.var_snap_to_grid
        ).pack(anchor=tk.W, pady=5)
        
        # Grid size
        grid_size_frame = ttk.Frame(frame)
        grid_size_frame.pack(anchor=tk.W, pady=5, fill=tk.X)
        
        ttk.Label(grid_size_frame, text="Rastergröße (px):").pack(side=tk.LEFT)
        self.var_grid_size = tk.IntVar(value=self.settings.get("grid_size", 20))
        ttk.Spinbox(
            grid_size_frame,
            from_=5,
            to=100,
            textvariable=self.var_grid_size,
            width=10
        ).pack(side=tk.LEFT, padx=10)
        
    def _create_export_tab(self):
        """Erstellt Export-Tab."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="Export")
        
        # Default format
        format_frame = ttk.Frame(frame)
        format_frame.pack(anchor=tk.W, pady=5, fill=tk.X)
        
        ttk.Label(format_frame, text="Standard-Format:").pack(side=tk.LEFT)
        self.var_export_format = tk.StringVar(value=self.settings.get("export_format", "PNG"))
        ttk.Combobox(
            format_frame,
            textvariable=self.var_export_format,
            values=["PNG", "SVG", "PDF", "XML"],
            state="readonly",
            width=15
        ).pack(side=tk.LEFT, padx=10)
        
        # DPI
        dpi_frame = ttk.Frame(frame)
        dpi_frame.pack(anchor=tk.W, pady=5, fill=tk.X)
        
        ttk.Label(dpi_frame, text="DPI (PNG/PDF):").pack(side=tk.LEFT)
        self.var_dpi = tk.IntVar(value=self.settings.get("dpi", 300))
        ttk.Spinbox(
            dpi_frame,
            from_=72,
            to=600,
            textvariable=self.var_dpi,
            increment=50,
            width=10
        ).pack(side=tk.LEFT, padx=10)
        
    def _create_ai_tab(self):
        """Erstellt AI-Tab."""
        frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(frame, text="AI")
        
        # AI enabled
        self.var_ai_enabled = tk.BooleanVar(value=self.settings.get("ai_enabled", True))
        ttk.Checkbutton(
            frame,
            text="AI-Funktionen aktivieren",
            variable=self.var_ai_enabled
        ).pack(anchor=tk.W, pady=5)
        
        # Model
        model_frame = ttk.Frame(frame)
        model_frame.pack(anchor=tk.W, pady=5, fill=tk.X)
        
        ttk.Label(model_frame, text="AI-Modell:").pack(side=tk.LEFT)
        self.var_ai_model = tk.StringVar(value=self.settings.get("ai_model", "llama3.2"))
        ttk.Entry(
            model_frame,
            textvariable=self.var_ai_model,
            width=25
        ).pack(side=tk.LEFT, padx=10)
        
        # Temperature
        temp_frame = ttk.Frame(frame)
        temp_frame.pack(anchor=tk.W, pady=5, fill=tk.X)
        
        ttk.Label(temp_frame, text="Temperature:").pack(side=tk.LEFT)
        self.var_temperature = tk.DoubleVar(value=self.settings.get("temperature", 0.7))
        ttk.Spinbox(
            temp_frame,
            from_=0.0,
            to=2.0,
            increment=0.1,
            textvariable=self.var_temperature,
            width=10,
            format="%.1f"
        ).pack(side=tk.LEFT, padx=10)
        
    def _collect_settings(self) -> Dict:
        """Sammelt alle Einstellungen."""
        return {
            # General
            "autosave": self.var_autosave.get(),
            "autosave_interval": self.var_autosave_interval.get(),
            "theme": self.var_theme.get(),
            # Canvas
            "grid_visible": self.var_grid_visible.get(),
            "snap_to_grid": self.var_snap_to_grid.get(),
            "grid_size": self.var_grid_size.get(),
            # Export
            "export_format": self.var_export_format.get(),
            "dpi": self.var_dpi.get(),
            # AI
            "ai_enabled": self.var_ai_enabled.get(),
            "ai_model": self.var_ai_model.get(),
            "temperature": self.var_temperature.get(),
        }
        
    def _on_ok(self):
        """OK Button - Übernehmen und Schließen."""
        self._on_apply()
        self.destroy()
        
    def _on_apply(self):
        """Apply Button - Einstellungen übernehmen."""
        self.settings = self._collect_settings()
        
        if self.event_bus:
            self.event_bus.publish("ui:dialog:settings:applied", {
                "settings": self.settings
            })
            
    def _on_cancel(self):
        """Cancel Button - Abbrechen."""
        self.settings = self._original_settings.copy()
        
        if self.event_bus:
            self.event_bus.publish("ui:dialog:settings:cancelled", {})
            
        self.destroy()
        
    def get_settings(self) -> Dict:
        """
        Gibt aktuelle Einstellungen zurück.
        
        Returns:
            Dictionary mit Einstellungen
        """
        return self.settings.copy()
        
    def __repr__(self) -> str:
        return f"<SettingsDialog tabs={self.notebook.index('end')}>"


# ===== Factory Function =====

def create_settings_dialog(
    parent: tk.Widget,
    event_bus: Optional[EventBus] = None,
    initial_settings: Optional[Dict] = None,
    **kwargs
) -> SettingsDialog:
    """
    Factory-Funktion zum Erstellen eines Settings Dialogs.
    
    Args:
        parent: Parent Widget
        event_bus: Event-Bus für Kommunikation
        initial_settings: Initiale Einstellungen
        **kwargs: Zusätzliche Toplevel-Optionen
        
    Returns:
        Neue SettingsDialog-Instanz
    """
    return SettingsDialog(parent, event_bus=event_bus, initial_settings=initial_settings, **kwargs)
