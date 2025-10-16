#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MainWindow View - Hauptfenster der VPB-Anwendung.

Diese View ist verantwortlich für:
- Fenster-Setup (Titel, Geometrie, Icon)
- Hauptlayout mit PanedWindow
- Koordination der Sub-Views (Canvas, Palette, Properties, etc.)

WICHTIG: Nur GUI-Code, keine Business-Logik!
Alle Aktionen werden über Event-Bus an Controller weitergegeben.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any, Callable
from pathlib import Path

from vpb.infrastructure.event_bus import get_global_event_bus


class MainWindow(tk.Tk):
    """
    Hauptfenster der VPB Process Designer Anwendung.
    
    Diese Klasse ist nur für das GUI-Layout verantwortlich.
    Alle Business-Logik wird über Events an Controller delegiert.
    
    Attributes:
        event_bus: Globaler Event-Bus für View-Controller Kommunikation
        paned: Haupt-PanedWindow (3-Spalten Layout)
        left_pane: Linke Sidebar (Palette)
        mid_pane: Mittlerer Bereich (Canvas, Chat)
        right_pane: Rechte Sidebar (Properties)
    """
    
    def __init__(
        self,
        title: str = "VPB Process Designer",
        geometry: str = "1200x800",
        icon_path: Optional[Path] = None
    ):
        """
        Initialisiert das Hauptfenster.
        
        Args:
            title: Fenster-Titel
            geometry: Initial-Geometrie (WIDTHxHEIGHT oder WIDTHxHEIGHT+X+Y)
            icon_path: Pfad zum Icon (optional)
        """
        super().__init__()
        
        self.event_bus = get_global_event_bus()
        
        # Fenster konfigurieren
        self._setup_window(title, geometry, icon_path)
        
        # Layout erstellen
        self._create_layout()
        
        # Event-Handler registrieren
        self._bind_events()
        
        # Window-Status tracken
        self._is_maximized = False
        self._last_geometry = geometry
    
    def _setup_window(
        self,
        title: str,
        geometry: str,
        icon_path: Optional[Path]
    ):
        """
        Konfiguriert Fenster-Properties.
        
        Args:
            title: Fenster-Titel
            geometry: Geometrie-String
            icon_path: Icon-Pfad
        """
        self.title(title)
        self.geometry(geometry)
        
        # Icon setzen (wenn vorhanden)
        if icon_path and icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                # Fallback: kein Icon
                pass
        
        # Minimum-Größe
        self.minsize(800, 600)
        
        # Window-Manager Protokolle
        self.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_layout(self):
        """
        Erstellt das Haupt-Layout.
        
        Layout-Struktur:
        ┌─────────────────────────────────────┐
        │ MenuBar                             │
        ├─────────────────────────────────────┤
        │ Toolbar                             │
        ├────────┬─────────────────┬──────────┤
        │ Left   │ Middle          │ Right    │
        │ Pane   │ Pane            │ Pane     │
        │        │                 │          │
        │ Palette│ ┌─────────────┐ │Properties│
        │        │ │   Canvas    │ │          │
        │        │ └─────────────┘ │          │
        │        │ ┌─────────────┐ │          │
        │        │ │   Chat      │ │          │
        │        │ └─────────────┘ │          │
        ├────────┴─────────────────┴──────────┤
        │ StatusBar                           │
        └─────────────────────────────────────┘
        """
        # Haupt-PanedWindow (3-Spalten)
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)
        
        # Linke Sidebar (Palette)
        self.left_pane = ttk.Frame(self.paned)
        self.paned.add(self.left_pane, weight=0)
        
        # Mittlerer Bereich (Canvas + Chat)
        self.mid_pane = ttk.Frame(self.paned)
        self.paned.add(self.mid_pane, weight=1)
        
        # Rechte Sidebar (Properties)
        self.right_pane = ttk.Frame(self.paned)
        self.paned.add(self.right_pane, weight=0)
        
        # Initial-Breiten setzen (werden später über Settings überschrieben)
        self._set_sidebar_widths(250, 300)
    
    def _bind_events(self):
        """Bindet Window-Events an Event-Bus."""
        # Window State Changes
        self.bind("<Configure>", self._on_configure)
        
        # Keyboard Shortcuts (werden an Event-Bus weitergeleitet)
        self.bind("<Control-n>", lambda e: self._publish_action("file.new"))
        self.bind("<Control-o>", lambda e: self._publish_action("file.open"))
        self.bind("<Control-s>", lambda e: self._publish_action("file.save"))
        self.bind("<Control-Shift-S>", lambda e: self._publish_action("file.save_as"))
        self.bind("<Control-z>", lambda e: self._publish_action("edit.undo"))
        self.bind("<Control-y>", lambda e: self._publish_action("edit.redo"))
        self.bind("<Control-c>", lambda e: self._publish_action("edit.copy"))
        self.bind("<Control-v>", lambda e: self._publish_action("edit.paste"))
        self.bind("<Delete>", lambda e: self._publish_action("edit.delete"))
        self.bind("<Control-a>", lambda e: self._publish_action("edit.select_all"))
        self.bind("<Control-f>", lambda e: self._publish_action("edit.find"))
        self.bind("<F5>", lambda e: self._publish_action("view.refresh"))
        self.bind("<F11>", lambda e: self._toggle_fullscreen())
    
    def _publish_action(self, action: str):
        """
        Publiziert eine Action über Event-Bus.
        
        Args:
            action: Action-Name (z.B. "file.new", "edit.undo")
        """
        self.event_bus.publish(f'ui:action:{action}', {
            'source': 'keyboard'
        })
    
    def _on_configure(self, event):
        """
        Handler für Configure-Events (Größenänderungen).
        
        Publiziert Geometrie-Änderungen über Event-Bus.
        """
        if event.widget == self:
            # Nur Main-Window Events (nicht Sub-Widgets)
            self.event_bus.publish('ui:window:resized', {
                'width': event.width,
                'height': event.height,
                'x': self.winfo_x(),
                'y': self.winfo_y()
            })
    
    def _on_close(self):
        """
        Handler für Window-Close Event.
        
        Publiziert Close-Event über Event-Bus und wartet auf Bestätigung.
        Der Controller entscheidet ob/wie geschlossen wird.
        """
        self.event_bus.publish('ui:window:close_requested', {})
    
    def _toggle_fullscreen(self):
        """Togglet Fullscreen-Modus."""
        self._is_maximized = not self._is_maximized
        self.attributes('-fullscreen', self._is_maximized)
        
        self.event_bus.publish('ui:window:fullscreen_changed', {
            'fullscreen': self._is_maximized
        })
    
    # ============================
    # Public API für Controller
    # ============================
    
    def close(self):
        """
        Schließt das Fenster.
        
        Wird vom Controller aufgerufen nach Bestätigung durch User.
        """
        self.destroy()
    
    def set_title(self, title: str):
        """
        Setzt den Fenster-Titel.
        
        Args:
            title: Neuer Titel (z.B. "VPB - process.vpb *")
        """
        self.title(title)
    
    def set_geometry(self, geometry: str):
        """
        Setzt Fenster-Geometrie.
        
        Args:
            geometry: Geometrie-String (WIDTHxHEIGHT+X+Y)
        """
        self.geometry(geometry)
        self._last_geometry = geometry
    
    def get_geometry(self) -> Dict[str, int]:
        """
        Liefert aktuelle Fenster-Geometrie.
        
        Returns:
            Dict mit width, height, x, y
        """
        return {
            'width': self.winfo_width(),
            'height': self.winfo_height(),
            'x': self.winfo_x(),
            'y': self.winfo_y()
        }
    
    def set_maximized(self, maximized: bool):
        """
        Setzt Maximized-Status.
        
        Args:
            maximized: True für maximiert, False für normal
        """
        if maximized:
            self.state('zoomed')
        else:
            self.state('normal')
        
        self._is_maximized = maximized
    
    def is_maximized(self) -> bool:
        """
        Prüft ob Fenster maximiert ist.
        
        Returns:
            True wenn maximiert
        """
        return self.state() == 'zoomed'
    
    def _set_sidebar_widths(self, left: int, right: int):
        """
        Setzt Breiten der Sidebars.
        
        Args:
            left: Breite linke Sidebar (Pixel)
            right: Breite rechte Sidebar (Pixel)
        """
        # PanedWindow Sash-Positionen
        try:
            # Nach erstem pack sind Positionen verfügbar
            self.after(10, lambda: self._apply_sash_positions(left, right))
        except Exception:
            pass
    
    def _apply_sash_positions(self, left: int, right: int):
        """Wendet Sash-Positionen an (delayed)."""
        try:
            total_width = self.winfo_width()
            # Linker Sash
            self.paned.sashpos(0, left)
            # Rechter Sash
            self.paned.sashpos(1, total_width - right)
        except Exception:
            pass
    
    def set_sidebar_widths(self, left: Optional[int] = None, right: Optional[int] = None):
        """
        Setzt Sidebar-Breiten (Public API).
        
        Args:
            left: Breite linke Sidebar (None = nicht ändern)
            right: Breite rechte Sidebar (None = nicht ändern)
        """
        if left is not None or right is not None:
            current_left = self.paned.sashpos(0) if left is None else left
            total = self.winfo_width()
            current_right = total - self.paned.sashpos(1) if right is None else right
            
            self._set_sidebar_widths(current_left, current_right)
    
    def get_sidebar_widths(self) -> Dict[str, int]:
        """
        Liefert aktuelle Sidebar-Breiten.
        
        Returns:
            Dict mit left, right
        """
        try:
            left = self.paned.sashpos(0)
            total = self.winfo_width()
            right = total - self.paned.sashpos(1)
            return {'left': left, 'right': right}
        except Exception:
            return {'left': 250, 'right': 300}
    
    def show_left_sidebar(self, visible: bool = True):
        """
        Zeigt/versteckt linke Sidebar.
        
        Args:
            visible: True zum Anzeigen, False zum Verstecken
        """
        panes = self.paned.panes()
        
        if visible:
            if self.left_pane._w not in [str(p) for p in panes]:
                self.paned.insert(0, self.left_pane)
        else:
            if self.left_pane._w in [str(p) for p in panes]:
                self.paned.remove(self.left_pane)
        
        self.event_bus.publish('ui:sidebar:left:toggled', {'visible': visible})
    
    def show_right_sidebar(self, visible: bool = True):
        """
        Zeigt/versteckt rechte Sidebar.
        
        Args:
            visible: True zum Anzeigen, False zum Verstecken
        """
        panes = self.paned.panes()
        
        if visible:
            if self.right_pane._w not in [str(p) for p in panes]:
                self.paned.add(self.right_pane)
        else:
            if self.right_pane._w in [str(p) for p in panes]:
                self.paned.remove(self.right_pane)
        
        self.event_bus.publish('ui:sidebar:right:toggled', {'visible': visible})
    
    def is_left_sidebar_visible(self) -> bool:
        """Prüft ob linke Sidebar sichtbar ist."""
        panes = self.paned.panes()
        return self.left_pane._w in [str(p) for p in panes]
    
    def is_right_sidebar_visible(self) -> bool:
        """Prüft ob rechte Sidebar sichtbar ist."""
        panes = self.paned.panes()
        return self.right_pane._w in [str(p) for p in panes]
    
    # ============================
    # Container-Zugriff für Sub-Views
    # ============================
    
    def get_left_container(self) -> tk.Widget:
        """Liefert Container für linke Sidebar (Palette)."""
        return self.left_pane
    
    def get_mid_container(self) -> tk.Widget:
        """Liefert Container für mittleren Bereich (Canvas)."""
        return self.mid_pane
    
    def get_right_container(self) -> tk.Widget:
        """Liefert Container für rechte Sidebar (Properties)."""
        return self.right_pane
    
    def __repr__(self) -> str:
        """String-Repräsentation."""
        geometry = self.get_geometry()
        return (
            f"MainWindow(title='{self.title()}', "
            f"size={geometry['width']}x{geometry['height']}, "
            f"maximized={self.is_maximized()})"
        )


# ============================
# Factory Functions
# ============================

def create_main_window(
    title: str = "VPB Process Designer",
    geometry: str = "1200x800",
    icon_path: Optional[Path] = None,
    **kwargs
) -> MainWindow:
    """
    Factory-Funktion zum Erstellen des Hauptfensters.
    
    Args:
        title: Fenster-Titel
        geometry: Initial-Geometrie
        icon_path: Icon-Pfad
        **kwargs: Weitere Argumente für MainWindow
    
    Returns:
        Konfiguriertes MainWindow
    
    Example:
        >>> window = create_main_window(
        ...     title="VPB Process Designer v2.0",
        ...     geometry="1400x900"
        ... )
        >>> window.mainloop()
    """
    return MainWindow(title, geometry, icon_path)


def restore_window_state(
    window: MainWindow,
    state: Dict[str, Any]
):
    """
    Stellt Window-State aus gespeicherten Settings wieder her.
    
    Args:
        window: MainWindow-Instanz
        state: Gespeicherter State (aus Settings)
    
    Example:
        >>> state = {
        ...     'geometry': '1400x900+100+50',
        ...     'maximized': False,
        ...     'sidebar_left': 300,
        ...     'sidebar_right': 350
        ... }
        >>> restore_window_state(window, state)
    """
    if 'geometry' in state:
        window.set_geometry(state['geometry'])
    
    if 'maximized' in state:
        window.set_maximized(state['maximized'])
    
    if 'sidebar_left' in state or 'sidebar_right' in state:
        window.set_sidebar_widths(
            state.get('sidebar_left'),
            state.get('sidebar_right')
        )
    
    if 'left_sidebar_visible' in state:
        window.show_left_sidebar(state['left_sidebar_visible'])
    
    if 'right_sidebar_visible' in state:
        window.show_right_sidebar(state['right_sidebar_visible'])


def save_window_state(window: MainWindow) -> Dict[str, Any]:
    """
    Speichert aktuellen Window-State.
    
    Args:
        window: MainWindow-Instanz
    
    Returns:
        State-Dict zum Speichern in Settings
    
    Example:
        >>> state = save_window_state(window)
        >>> # {'geometry': '1400x900+100+50', 'maximized': False, ...}
    """
    geometry = window.get_geometry()
    sidebars = window.get_sidebar_widths()
    
    return {
        'geometry': f"{geometry['width']}x{geometry['height']}+{geometry['x']}+{geometry['y']}",
        'maximized': window.is_maximized(),
        'sidebar_left': sidebars['left'],
        'sidebar_right': sidebars['right'],
        'left_sidebar_visible': window.is_left_sidebar_visible(),
        'right_sidebar_visible': window.is_right_sidebar_visible()
    }
