"""
Canvas View für Prozessdiagramm-Darstellung.

Diese View ist verantwortlich für:
- Rendering von VPB-Elementen und Verbindungen
- Zoom/Pan-Funktionalität
- Grid-Anzeige
- Mouse-Event-Erfassung (kein Handling!)
- Selection-Visualisierung

Alle Events werden über den Event-Bus publiziert.
Business-Logik bleibt in Services.
"""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Dict, List, Optional, Tuple, Any

from vpb.models import VPBElement, VPBConnection
from vpb.infrastructure.event_bus import get_global_event_bus, EventBus
from vpb.ui.canvas import VPBCanvas


class CanvasView(tk.Frame):
    """
    Canvas View für Prozessdiagramm-Darstellung mit Zoom/Pan/Grid.
    
    Diese View ist eine schlanke Wrapper um die bestehende VPBCanvas-Klasse,
    die für Event-Bus-Integration sorgt und die View-Verantwortlichkeiten
    von Business-Logik trennt.
    
    Attributes:
        canvas (VPBCanvas): Das eigentliche Canvas-Widget
        event_bus (EventBus): Event-Bus für Kommunikation
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        event_bus: Optional[EventBus] = None,
        width: int = 800,
        height: int = 600,
        **kwargs
    ):
        """
        Initialisiert die Canvas View.
        
        Args:
            parent: Parent Widget
            event_bus: Event-Bus für Kommunikation (optional)
            width: Initiale Breite
            height: Initiale Höhe
            **kwargs: Zusätzliche Frame-Optionen
        """
        super().__init__(parent, **kwargs)
        
        self.event_bus = event_bus or get_global_event_bus()
        self._width = width
        self._height = height
        
        # Create scrollbars and canvas
        self._create_widgets()
        self._setup_event_publishing()
        
    def _create_widgets(self):
        """Erstellt Canvas mit Scrollbars."""
        # Scrollbars
        self.v_scrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.h_scrollbar = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        
        # VPBCanvas (wiederverwendet bestehende Implementierung)
        self.canvas = VPBCanvas(
            self,
            width=self._width,
            height=self._height,
            scrollregion=(0, 0, 2000, 2000),
            yscrollcommand=self.v_scrollbar.set,
            xscrollcommand=self.h_scrollbar.set
        )
        
        # Configure scrollbars
        self.v_scrollbar.config(command=self.canvas.yview)
        self.h_scrollbar.config(command=self.canvas.xview)
        
        # Grid layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Configure grid weights
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
    def _setup_event_publishing(self):
        """Setzt Event-Publishing für Canvas-Events auf."""
        # Override selection callback to publish events
        original_selection_cb = self.canvas.on_selection_changed
        
        def _publish_selection(element: Optional[VPBElement], connection: Optional[VPBConnection]):
            """Publishes selection changed event."""
            if element:
                self.event_bus.publish("ui:canvas:element_selected", {
                    "element_id": element.element_id,
                    "element": element
                })
            elif connection:
                self.event_bus.publish("ui:canvas:connection_selected", {
                    "connection_id": connection.connection_id,
                    "connection": connection
                })
            else:
                self.event_bus.publish("ui:canvas:selection_cleared", {})
            
            # Call original callback if exists
            if original_selection_cb:
                original_selection_cb(element, connection)
        
        self.canvas.on_selection_changed = _publish_selection
        
        # Bind mouse events for publishing
        self.canvas.bind("<Button-1>", self._on_left_click, add="+")
        self.canvas.bind("<Button-3>", self._on_right_click, add="+")
        self.canvas.bind("<Double-Button-1>", self._on_double_click, add="+")
        self.canvas.bind("<B1-Motion>", self._on_drag, add="+")
        self.canvas.bind("<ButtonRelease-1>", self._on_release, add="+")
        
        # Bind keyboard events
        self.canvas.bind("<Delete>", self._on_delete_key, add="+")
        self.canvas.bind("<Control-z>", self._on_undo, add="+")
        self.canvas.bind("<Control-y>", self._on_redo, add="+")
        self.canvas.bind("<Control-c>", self._on_copy, add="+")
        self.canvas.bind("<Control-v>", self._on_paste, add="+")
        self.canvas.bind("<Control-x>", self._on_cut, add="+")
        self.canvas.bind("<Control-a>", self._on_select_all, add="+")
        
        # Zoom/Pan events
        self.canvas.bind("<MouseWheel>", self._on_mousewheel, add="+")
        self.canvas.bind("<Control-plus>", self._on_zoom_in, add="+")
        self.canvas.bind("<Control-minus>", self._on_zoom_out, add="+")
        self.canvas.bind("<Control-0>", self._on_zoom_reset, add="+")
        
    # ===== Mouse Event Handlers (Publish Events) =====
    
    def _on_left_click(self, event: tk.Event):
        """Publishes left click event."""
        self.event_bus.publish("ui:canvas:left_click", {
            "x": event.x,
            "y": event.y,
            "widget": event.widget
        })
        
    def _on_right_click(self, event: tk.Event):
        """Publishes right click event."""
        self.event_bus.publish("ui:canvas:right_click", {
            "x": event.x,
            "y": event.y,
            "widget": event.widget
        })
        
    def _on_double_click(self, event: tk.Event):
        """Publishes double click event."""
        self.event_bus.publish("ui:canvas:double_click", {
            "x": event.x,
            "y": event.y,
            "widget": event.widget
        })
        
    def _on_drag(self, event: tk.Event):
        """Publishes drag event."""
        self.event_bus.publish("ui:canvas:drag", {
            "x": event.x,
            "y": event.y,
            "widget": event.widget
        })
        
    def _on_release(self, event: tk.Event):
        """Publishes release event."""
        self.event_bus.publish("ui:canvas:release", {
            "x": event.x,
            "y": event.y,
            "widget": event.widget
        })
        
    # ===== Keyboard Event Handlers (Publish Events) =====
    
    def _on_delete_key(self, event: tk.Event):
        """Publishes delete key event."""
        self.event_bus.publish("ui:action:edit.delete", {})
        return "break"  # Prevent default behavior
        
    def _on_undo(self, event: tk.Event):
        """Publishes undo event."""
        self.event_bus.publish("ui:action:edit.undo", {})
        return "break"
        
    def _on_redo(self, event: tk.Event):
        """Publishes redo event."""
        self.event_bus.publish("ui:action:edit.redo", {})
        return "break"
        
    def _on_copy(self, event: tk.Event):
        """Publishes copy event."""
        self.event_bus.publish("ui:action:edit.copy", {})
        return "break"
        
    def _on_paste(self, event: tk.Event):
        """Publishes paste event."""
        self.event_bus.publish("ui:action:edit.paste", {})
        return "break"
        
    def _on_cut(self, event: tk.Event):
        """Publishes cut event."""
        self.event_bus.publish("ui:action:edit.cut", {})
        return "break"
        
    def _on_select_all(self, event: tk.Event):
        """Publishes select all event."""
        self.event_bus.publish("ui:action:edit.select_all", {})
        return "break"
        
    # ===== Zoom/Pan Event Handlers =====
    
    def _on_mousewheel(self, event: tk.Event):
        """Publishes mousewheel event."""
        # Determine direction
        delta = event.delta
        if delta > 0:
            action = "zoom_in" if self.canvas.mousewheel_mode == "zoom-primary" else "pan_up"
        else:
            action = "zoom_out" if self.canvas.mousewheel_mode == "zoom-primary" else "pan_down"
            
        self.event_bus.publish(f"ui:canvas:{action}", {
            "x": event.x,
            "y": event.y,
            "delta": delta
        })
        
    def _on_zoom_in(self, event: tk.Event):
        """Publishes zoom in event."""
        self.event_bus.publish("ui:action:view.zoom_in", {})
        return "break"
        
    def _on_zoom_out(self, event: tk.Event):
        """Publishes zoom out event."""
        self.event_bus.publish("ui:action:view.zoom_out", {})
        return "break"
        
    def _on_zoom_reset(self, event: tk.Event):
        """Publishes zoom reset event."""
        self.event_bus.publish("ui:action:view.zoom_reset", {})
        return "break"
        
    # ===== Public API =====
    
    def load_document(self, elements: List[VPBElement], connections: List[VPBConnection], metadata: Dict):
        """
        Lädt ein Dokument in das Canvas.
        
        Args:
            elements: Liste von VPBElement-Objekten
            connections: Liste von VPBConnection-Objekten
            metadata: Dokument-Metadaten
        """
        data = {
            "elements": [el.to_dict() for el in elements],
            "connections": [conn.to_dict() for conn in connections],
            "metadata": metadata
        }
        self.canvas.load_from_dict(data)
        self.canvas.redraw_all()
        
    def get_document_data(self) -> Dict:
        """
        Gibt die aktuellen Canvas-Daten zurück.
        
        Returns:
            Dictionary mit elements, connections, metadata
        """
        return self.canvas.to_dict()
        
    def clear(self):
        """Löscht alle Elemente vom Canvas."""
        self.canvas.clear()
        
    def redraw(self):
        """Zeichnet das Canvas neu."""
        self.canvas.redraw_all()
        
    # ===== Zoom Control =====
    
    def zoom_in(self, center_x: Optional[int] = None, center_y: Optional[int] = None):
        """
        Zoomt hinein.
        
        Args:
            center_x: Optionales Zoom-Zentrum X
            center_y: Optionales Zoom-Zentrum Y
        """
        factor = 1.2
        self.canvas.zoom_at_view(factor, center_x, center_y)
        
    def zoom_out(self, center_x: Optional[int] = None, center_y: Optional[int] = None):
        """
        Zoomt heraus.
        
        Args:
            center_x: Optionales Zoom-Zentrum X
            center_y: Optionales Zoom-Zentrum Y
        """
        factor = 1.0 / 1.2
        self.canvas.zoom_at_view(factor, center_x, center_y)
        
    def zoom_reset(self):
        """Setzt Zoom auf 100% zurück."""
        self.canvas.view_scale = 1.0
        self.canvas.view_tx = 0.0
        self.canvas.view_ty = 0.0
        self.canvas.redraw_all()
        
    def zoom_to_fit(self):
        """Zoomt so dass alle Elemente sichtbar sind."""
        self.canvas.fit_to_diagram()
        
    def get_zoom_level(self) -> float:
        """
        Gibt den aktuellen Zoom-Level zurück.
        
        Returns:
            Zoom-Level (1.0 = 100%)
        """
        return self.canvas.view_scale
        
    def set_zoom_level(self, level: float):
        """
        Setzt den Zoom-Level.
        
        Args:
            level: Zoom-Level (1.0 = 100%)
        """
        level = max(self.canvas._min_zoom, min(self.canvas._max_zoom, level))
        self.canvas.view_scale = level
        self.canvas.redraw_all()
        
    # ===== Pan Control =====
    
    def pan(self, dx: int, dy: int):
        """
        Verschiebt die Ansicht.
        
        Args:
            dx: Verschiebung in X-Richtung (Pixel)
            dy: Verschiebung in Y-Richtung (Pixel)
        """
        self.canvas.pan_pixels(dx, dy)
        
    def center_on_point(self, x: float, y: float):
        """
        Zentriert die Ansicht auf einen Punkt.
        
        Args:
            x: X-Koordinate (Model-Koordinaten)
            y: Y-Koordinate (Model-Koordinaten)
        """
        # Calculate canvas center
        canvas_width = self.canvas.winfo_width() or 800
        canvas_height = self.canvas.winfo_height() or 600
        center_x = canvas_width / 2
        center_y = canvas_height / 2
        
        # Transform model coords to view coords
        vx, vy = self.canvas.to_view(x, y)
        
        # Calculate required pan
        dx = center_x - vx
        dy = center_y - vy
        
        self.canvas.pan_pixels(dx, dy)
        
    # ===== Grid Control =====
    
    def set_grid_visible(self, visible: bool):
        """
        Setzt Grid-Sichtbarkeit.
        
        Args:
            visible: True für sichtbar, False für unsichtbar
        """
        self.canvas.grid_visible = visible
        self.canvas.redraw_all()
        
    def is_grid_visible(self) -> bool:
        """
        Gibt zurück ob Grid sichtbar ist.
        
        Returns:
            True wenn sichtbar
        """
        return self.canvas.grid_visible
        
    def set_snap_to_grid(self, snap: bool):
        """
        Setzt Snap-to-Grid.
        
        Args:
            snap: True für Snap-to-Grid aktiviert
        """
        self.canvas.snap_to_grid = snap
        
    def is_snap_to_grid(self) -> bool:
        """
        Gibt zurück ob Snap-to-Grid aktiviert ist.
        
        Returns:
            True wenn aktiviert
        """
        return self.canvas.snap_to_grid
        
    def set_grid_size(self, size: int):
        """
        Setzt Grid-Größe.
        
        Args:
            size: Grid-Größe in Pixeln
        """
        self.canvas.grid_size = max(5, min(100, size))
        self.canvas.redraw_all()
        
    def get_grid_size(self) -> int:
        """
        Gibt Grid-Größe zurück.
        
        Returns:
            Grid-Größe in Pixeln
        """
        return self.canvas.grid_size
        
    # ===== Selection =====
    
    def get_selected_element(self) -> Optional[VPBElement]:
        """
        Gibt das aktuell ausgewählte Element zurück.
        
        Returns:
            Ausgewähltes Element oder None
        """
        if self.canvas.selected_id and self.canvas.selected_id in self.canvas.elements:
            return self.canvas.elements[self.canvas.selected_id]
        return None
        
    def get_selected_elements(self) -> List[VPBElement]:
        """
        Gibt alle ausgewählten Elemente zurück.
        
        Returns:
            Liste von ausgewählten Elementen
        """
        result = []
        for eid in self.canvas.selected_ids:
            if eid in self.canvas.elements:
                result.append(self.canvas.elements[eid])
        return result
        
    def get_selected_connection(self) -> Optional[VPBConnection]:
        """
        Gibt die aktuell ausgewählte Verbindung zurück.
        
        Returns:
            Ausgewählte Verbindung oder None
        """
        if self.canvas.selected_conn_id and self.canvas.selected_conn_id in self.canvas.connections:
            return self.canvas.connections[self.canvas.selected_conn_id]
        return None
        
    def select_element(self, element_id: str):
        """
        Wählt ein Element aus.
        
        Args:
            element_id: Element-ID
        """
        if element_id in self.canvas.elements:
            self.canvas.selected_id = element_id
            self.canvas.selected_ids = {element_id}
            self.canvas.selected_conn_id = None
            self.canvas.redraw_all()
            
    def clear_selection(self):
        """Löscht die aktuelle Auswahl."""
        self.canvas.selected_id = None
        self.canvas.selected_ids.clear()
        self.canvas.selected_conn_id = None
        self.canvas.redraw_all()
        
    # ===== Canvas State =====
    
    def get_canvas_state(self) -> Dict[str, Any]:
        """
        Gibt den aktuellen Canvas-Zustand zurück.
        
        Returns:
            Dictionary mit Canvas-Zustand
        """
        return {
            "zoom_level": self.canvas.view_scale,
            "view_tx": self.canvas.view_tx,
            "view_ty": self.canvas.view_ty,
            "grid_visible": self.canvas.grid_visible,
            "snap_to_grid": self.canvas.snap_to_grid,
            "grid_size": self.canvas.grid_size,
            "mousewheel_mode": self.canvas.mousewheel_mode,
            "routing_style": self.canvas.routing_style
        }
        
    def restore_canvas_state(self, state: Dict[str, Any]):
        """
        Stellt Canvas-Zustand wieder her.
        
        Args:
            state: Dictionary mit Canvas-Zustand
        """
        if "zoom_level" in state:
            self.canvas.view_scale = state["zoom_level"]
        if "view_tx" in state:
            self.canvas.view_tx = state["view_tx"]
        if "view_ty" in state:
            self.canvas.view_ty = state["view_ty"]
        if "grid_visible" in state:
            self.canvas.grid_visible = state["grid_visible"]
        if "snap_to_grid" in state:
            self.canvas.snap_to_grid = state["snap_to_grid"]
        if "grid_size" in state:
            self.canvas.grid_size = state["grid_size"]
        if "mousewheel_mode" in state:
            self.canvas.mousewheel_mode = state["mousewheel_mode"]
        if "routing_style" in state:
            self.canvas.routing_style = state["routing_style"]
        self.canvas.redraw_all()
        
    # ===== Focus =====
    
    def focus(self):
        """Gibt dem Canvas den Fokus."""
        self.canvas.focus_set()
        
    def __repr__(self) -> str:
        return f"<CanvasView zoom={self.canvas.view_scale:.2f} elements={len(self.canvas.elements)} connections={len(self.canvas.connections)}>"


# ===== Factory Function =====

def create_canvas_view(
    parent: tk.Widget,
    event_bus: Optional[EventBus] = None,
    width: int = 800,
    height: int = 600,
    **kwargs
) -> CanvasView:
    """
    Factory-Funktion zum Erstellen einer Canvas View.
    
    Args:
        parent: Parent Widget
        event_bus: Event-Bus für Kommunikation
        width: Initiale Breite
        height: Initiale Höhe
        **kwargs: Zusätzliche Frame-Optionen
        
    Returns:
        Neue CanvasView-Instanz
    """
    return CanvasView(parent, event_bus=event_bus, width=width, height=height, **kwargs)
