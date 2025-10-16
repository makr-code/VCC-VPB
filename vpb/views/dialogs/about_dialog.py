"""
About Dialog für VPB Process Designer.

Zeigt Informationen über die Anwendung:
- VPB Logo/Name
- Versionsinformation
- Copyright
- Lizenz
- Dependencies
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from vpb.infrastructure.event_bus import EventBus


class AboutDialog(tk.Toplevel):
    """
    About Dialog für VPB Process Designer.
    
    Zeigt Informationen über die Anwendung.
    
    Attributes:
        event_bus (EventBus): Event-Bus für Kommunikation (optional)
    """
    
    # Version info
    VERSION = "1.0.0"
    COPYRIGHT = "© 2025 VPB Process Designer"
    LICENSE = "MIT License"
    
    def __init__(
        self,
        parent: tk.Widget,
        event_bus: Optional[EventBus] = None,
        **kwargs
    ):
        """
        Initialisiert den About Dialog.
        
        Args:
            parent: Parent Widget
            event_bus: Event-Bus für Kommunikation (optional)
            **kwargs: Zusätzliche Toplevel-Optionen
        """
        super().__init__(parent, **kwargs)
        
        self.event_bus = event_bus
        
        # Window configuration
        self.title("Über VPB Process Designer")
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
        
        # Get parent geometry
        parent.update_idletasks()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        # Calculate center position
        dialog_width = 500
        dialog_height = 400
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
    def _create_widgets(self):
        """Erstellt die Dialog-Widgets."""
        # Main frame
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Logo/Icon (🔄 VPB)
        logo_label = ttk.Label(
            main_frame,
            text="🔄",
            font=("Segoe UI Emoji", 48)
        )
        logo_label.pack(pady=(0, 10))
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="VPB Process Designer",
            font=("Segoe UI", 16, "bold")
        )
        title_label.pack()
        
        # Version
        version_label = ttk.Label(
            main_frame,
            text=f"Version {self.VERSION}",
            font=("Segoe UI", 10)
        )
        version_label.pack(pady=(5, 20))
        
        # Description
        desc_text = (
            "UDS³ Verwaltungsprozess-Beschreibungssprache\n\n"
            "Ein moderner Prozess-Designer für die Erstellung und\n"
            "Bearbeitung von Verwaltungsprozessen nach UDS³-Standard.\n\n"
            "Features:\n"
            "• Grafischer Prozess-Designer mit Drag & Drop\n"
            "• AI-gestützte Prozess-Erstellung\n"
            "• Compliance-Validierung\n"
            "• Export zu PNG, SVG, PDF, XML\n"
            "• Versionsverwaltung und Collaboration"
        )
        
        desc_label = ttk.Label(
            main_frame,
            text=desc_text,
            justify=tk.LEFT,
            font=("Segoe UI", 9)
        )
        desc_label.pack(pady=10)
        
        # Copyright & License
        copyright_label = ttk.Label(
            main_frame,
            text=f"{self.COPYRIGHT}\n{self.LICENSE}",
            font=("Segoe UI", 8),
            foreground="gray"
        )
        copyright_label.pack(pady=(20, 10))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        # Close button
        close_btn = ttk.Button(
            button_frame,
            text="Schließen",
            command=self._on_close,
            width=15
        )
        close_btn.pack()
        close_btn.focus_set()
        
        # Bind Escape key
        self.bind("<Escape>", lambda e: self._on_close())
        
    def _on_close(self):
        """Schließt den Dialog."""
        if self.event_bus:
            self.event_bus.publish("ui:dialog:about:closed", {})
        self.destroy()
        
    def show(self):
        """Zeigt den Dialog modal an."""
        self.wait_window()
        
    def __repr__(self) -> str:
        return f"<AboutDialog version={self.VERSION}>"


# ===== Factory Function =====

def create_about_dialog(
    parent: tk.Widget,
    event_bus: Optional[EventBus] = None,
    **kwargs
) -> AboutDialog:
    """
    Factory-Funktion zum Erstellen eines About Dialogs.
    
    Args:
        parent: Parent Widget
        event_bus: Event-Bus für Kommunikation
        **kwargs: Zusätzliche Toplevel-Optionen
        
    Returns:
        Neue AboutDialog-Instanz
    """
    return AboutDialog(parent, event_bus=event_bus, **kwargs)
