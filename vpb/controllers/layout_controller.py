"""
LayoutController
================

Controller für Layout und Alignment Operationen.

Responsibilities:
- Auto-Layout Algorithmen (Hierarchical, Force-Directed, etc.)
- Align Operationen (Left, Right, Top, Bottom, Center-H, Center-V)
- Distribute Operationen (Horizontal, Vertical)
- Formation Operationen (Line, Circle, Grid, Tree)

Event Subscriptions:
- ui:menu:layout:auto_layout
- ui:menu:layout:align:* (left, right, top, bottom, center_h, center_v)
- ui:menu:layout:distribute:* (horizontal, vertical)
- ui:menu:layout:formation:* (line, circle, grid, tree)
- document:created, document:loaded, document:closed

Event Publications:
- layout:applied (layout_type, element_ids)
- layout:failed (error)
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Dict, Any, List
import math

if TYPE_CHECKING:
    from vpb.infrastructure.event_bus import EventBus
    from vpb.models import DocumentModel, VPBElement


class LayoutController:
    """
    Controller für Layout und Alignment.
    
    Koordiniert Layout-Algorithmen und Positionierung von Elementen.
    """
    
    def __init__(
        self,
        event_bus: EventBus,
        layout_service: Optional[Any] = None
    ):
        """
        Initialisiert LayoutController.
        
        Args:
            event_bus: Event-Bus für Kommunikation
            layout_service: Layout-Service (optional, derzeit nicht verwendet)
        """
        self.event_bus = event_bus
        self.layout_service = layout_service
        self.canvas = None  # Wird über set_canvas gesetzt
        
        # Subscribe to Events
        self._subscribe_to_events()
    
    def set_canvas(self, canvas) -> None:
        """Setzt die Canvas-Referenz für Layout-Operationen."""
        self.canvas = canvas
        
    def _subscribe_to_events(self) -> None:
        """Subscribe zu relevanten Events."""
        # Layout Events
        self.event_bus.subscribe("ui:menu:layout:auto_layout", self._on_auto_layout)
        
        # Align Events
        self.event_bus.subscribe("ui:menu:layout:align:left", self._on_align_left)
        self.event_bus.subscribe("ui:menu:layout:align:right", self._on_align_right)
        self.event_bus.subscribe("ui:menu:layout:align:top", self._on_align_top)
        self.event_bus.subscribe("ui:menu:layout:align:bottom", self._on_align_bottom)
        self.event_bus.subscribe("ui:menu:layout:align:center_h", self._on_align_center_h)
        self.event_bus.subscribe("ui:menu:layout:align:center_v", self._on_align_center_v)
        
        # Distribute Events
        self.event_bus.subscribe("ui:menu:layout:distribute:horizontal", self._on_distribute_horizontal)
        self.event_bus.subscribe("ui:menu:layout:distribute:vertical", self._on_distribute_vertical)
        
        # Formation Events
        self.event_bus.subscribe("ui:menu:layout:formation:line", self._on_formation_line)
        self.event_bus.subscribe("ui:menu:layout:formation:circle", self._on_formation_circle)
        self.event_bus.subscribe("ui:menu:layout:formation:grid", self._on_formation_grid)
        
        # Document Events
        self.event_bus.subscribe("document:created", self._on_document_changed)
        self.event_bus.subscribe("document:loaded", self._on_document_changed)
        self.event_bus.subscribe("document:closed", self._on_document_closed)
        
        # Canvas Control Events (Zoom, Pan, etc.)
        self.event_bus.subscribe("ui:action:canvas.zoom", self._on_canvas_zoom)
        self.event_bus.subscribe("ui:action:canvas.zoom_reset", self._on_canvas_zoom_reset)
        self.event_bus.subscribe("ui:action:canvas.fit_to_window", self._on_canvas_fit_to_window)
        self.event_bus.subscribe("ui:action:canvas.zoom_to_selection", self._on_canvas_zoom_to_selection)
        self.event_bus.subscribe("ui:action:canvas.toggle_grid", self._on_canvas_toggle_grid)
        
    # ===== Canvas Controls =====
    
    def _on_canvas_zoom(self, data: Dict[str, Any]) -> None:
        """Zoom In/Out."""
        if not self.canvas:
            return
        
        direction = data.get("direction", "in")
        factor = 1.2 if direction == "in" else 1 / 1.2
        
        try:
            # Zoom am Mittelpunkt
            self.canvas.zoom_at_view(factor)
            
            # Update Toolbar
            self._update_toolbar_zoom()
            
            self.event_bus.publish("canvas:zoom_changed", {
                "zoom": self.canvas.view_scale
            })
        except Exception as e:
            self.event_bus.publish("ui:statusbar:update", {
                "text": f"Zoom fehlgeschlagen: {e}"
            })
    
    def _on_canvas_zoom_reset(self, data: Dict[str, Any]) -> None:
        """Setzt Zoom auf 100% zurück."""
        if not self.canvas:
            return
        
        try:
            # Setze Scale auf 1.0
            self.canvas.view_scale = 1.0
            self.canvas.redraw_all()
            
            # Update Toolbar
            self._update_toolbar_zoom()
            
            self.event_bus.publish("canvas:zoom_changed", {
                "zoom": 1.0
            })
            self.event_bus.publish("ui:statusbar:update", {
                "text": "Zoom auf 100% zurückgesetzt"
            })
        except Exception as e:
            self.event_bus.publish("ui:statusbar:update", {
                "text": f"Zoom Reset fehlgeschlagen: {e}"
            })
    
    def _on_canvas_fit_to_window(self, data: Dict[str, Any]) -> None:
        """Passt Ansicht an Fenster an (Fit to Window)."""
        if not self.canvas:
            return
        
        try:
            # Hole Content Bounds
            min_x, min_y, max_x, max_y = self.canvas.get_content_bounds(include_connections=True)
            
            if min_x >= max_x or min_y >= max_y:
                self.event_bus.publish("ui:statusbar:update", {
                    "text": "Keine Elemente zum Anpassen"
                })
                return
            
            # Berechne benötigten Zoom
            content_w = max_x - min_x
            content_h = max_y - min_y
            canvas_w = self.canvas.winfo_width() or 800
            canvas_h = self.canvas.winfo_height() or 600
            
            # Padding (20% auf jeder Seite)
            padding = 0.8
            scale_x = (canvas_w * padding) / content_w
            scale_y = (canvas_h * padding) / content_h
            new_scale = min(scale_x, scale_y)
            
            # Clamp to min/max zoom
            new_scale = max(self.canvas._min_zoom, min(self.canvas._max_zoom, new_scale))
            
            # Setze Zoom und Position
            self.canvas.view_scale = new_scale
            
            # Zentriere Content
            center_x = (min_x + max_x) / 2
            center_y = (min_y + max_y) / 2
            self.canvas.view_tx = canvas_w / 2 - center_x * new_scale
            self.canvas.view_ty = canvas_h / 2 - center_y * new_scale
            
            self.canvas.redraw_all()
            
            # Update Toolbar
            self._update_toolbar_zoom()
            
            self.event_bus.publish("canvas:zoom_changed", {
                "zoom": new_scale
            })
            self.event_bus.publish("ui:statusbar:update", {
                "text": f"Fit to Window: {int(new_scale * 100)}%"
            })
        except Exception as e:
            self.event_bus.publish("ui:statusbar:update", {
                "text": f"Fit to Window fehlgeschlagen: {e}"
            })
    
    def _on_canvas_zoom_to_selection(self, data: Dict[str, Any]) -> None:
        """Zoomt auf die Selektion."""
        if not self.canvas:
            return
        
        try:
            success = self.canvas.zoom_to_selection(padding=40.0)
            
            if success:
                # Update Toolbar
                self._update_toolbar_zoom()
                
                self.event_bus.publish("canvas:zoom_changed", {
                    "zoom": self.canvas.view_scale
                })
                self.event_bus.publish("ui:statusbar:update", {
                    "text": "Zoom to Selection"
                })
            else:
                self.event_bus.publish("ui:statusbar:update", {
                    "text": "Keine Elemente ausgewählt"
                })
        except Exception as e:
            self.event_bus.publish("ui:statusbar:update", {
                "text": f"Zoom to Selection fehlgeschlagen: {e}"
            })
    
    def _on_canvas_toggle_grid(self, data: Dict[str, Any]) -> None:
        """Schaltet Grid ein/aus."""
        if not self.canvas:
            return
        
        try:
            # Toggle Grid
            current_state = getattr(self.canvas, 'show_grid', False)
            new_state = not current_state
            self.canvas.show_grid = new_state
            self.canvas.redraw_all()
            
            # Update Toolbar Grid-Button
            self.event_bus.publish("toolbar:grid_state_changed", {
                "active": new_state
            })
            
            self.event_bus.publish("ui:statusbar:update", {
                "text": f"Grid {'aktiviert' if new_state else 'deaktiviert'}"
            })
        except Exception as e:
            self.event_bus.publish("ui:statusbar:update", {
                "text": f"Grid Toggle fehlgeschlagen: {e}"
            })
    
    def _update_toolbar_zoom(self) -> None:
        """Aktualisiert die Zoom-Anzeige in der Toolbar."""
        if self.canvas:
            self.event_bus.publish("toolbar:zoom_changed", {
                "zoom": self.canvas.view_scale
            })
        
    # ===== Auto Layout =====
    
    def _on_auto_layout(self, data: Dict[str, Any]) -> None:
        """
        Automatisches Layout anwenden.
        
        Args:
            data: {"algorithm": str} (optional, default: "hierarchical")
        """
        if not self.canvas:
            return
        
        algorithm = data.get("algorithm", "hierarchical")
        elements = list(self.canvas.elements.values())
        
        if not elements:
            return
            
        # Simple hierarchical layout (top to bottom)
        if algorithm == "hierarchical":
            self._apply_hierarchical_layout(elements)
        
        # Canvas neu zeichnen
        self.canvas.redraw_all()
        
        # Publish Event
        element_ids = [elem.element_id for elem in elements]
        self.event_bus.publish("layout:applied", {
            "layout_type": f"auto_{algorithm}",
            "element_ids": element_ids
        })
        
        # Status-Feedback
        self.event_bus.publish("ui:statusbar:message", {
            "text": f"Auto-Layout angewendet ({algorithm})",
            "timeout": 3000
        })
        
    def _apply_hierarchical_layout(self, elements: List[VPBElement]) -> None:
        """Hierarchisches Layout (Top-Down)."""
        x_start = 100
        y_start = 100
        x_spacing = 200
        y_spacing = 150
        
        cols = math.ceil(math.sqrt(len(elements)))
        
        for idx, elem in enumerate(elements):
            row = idx // cols
            col = idx % cols
            elem.x = x_start + col * x_spacing
            elem.y = y_start + row * y_spacing
    
    # ===== Align Operations =====
    
    def _on_align_left(self, data: Dict[str, Any]) -> None:
        """Links ausrichten."""
        self._align_elements(data, align_type="left")
        
    def _on_align_right(self, data: Dict[str, Any]) -> None:
        """Rechts ausrichten."""
        self._align_elements(data, align_type="right")
        
    def _on_align_top(self, data: Dict[str, Any]) -> None:
        """Oben ausrichten."""
        self._align_elements(data, align_type="top")
        
    def _on_align_bottom(self, data: Dict[str, Any]) -> None:
        """Unten ausrichten."""
        self._align_elements(data, align_type="bottom")
        
    def _on_align_center_h(self, data: Dict[str, Any]) -> None:
        """Horizontal zentrieren."""
        self._align_elements(data, align_type="center_h")
        
    def _on_align_center_v(self, data: Dict[str, Any]) -> None:
        """Vertikal zentrieren."""
        self._align_elements(data, align_type="center_v")
        
    def _align_elements(self, data: Dict[str, Any], align_type: str) -> None:
        """
        Elemente ausrichten.
        
        Args:
            data: {"element_ids": List[str]}
            align_type: Art der Ausrichtung
        """
        if not self.canvas:
            return
            
        element_ids = data.get("element_ids", [])
        
        if len(element_ids) < 2:
            # Keine Element-IDs übergeben, nutze Selektion
            if hasattr(self.canvas, 'selected_ids'):
                element_ids = list(self.canvas.selected_ids)
        
        if len(element_ids) < 2:
            return
            
        elements = [self.canvas.elements.get(eid) for eid in element_ids]
        elements = [e for e in elements if e is not None]
        
        if len(elements) < 2:
            return
        
        # Default element dimensions (VPBElement doesn't have width/height)
        default_width = 120
        default_height = 80
        
        # Calculate alignment reference
        if align_type == "left":
            ref = min(e.x for e in elements)
            for elem in elements:
                elem.x = ref
        elif align_type == "right":
            ref = max(e.x + default_width for e in elements)
            for elem in elements:
                elem.x = ref - default_width
        elif align_type == "top":
            ref = min(e.y for e in elements)
            for elem in elements:
                elem.y = ref
        elif align_type == "bottom":
            ref = max(e.y + default_height for e in elements)
            for elem in elements:
                elem.y = ref - default_height
        elif align_type == "center_h":
            ref = sum(e.x + default_width / 2 for e in elements) / len(elements)
            for elem in elements:
                elem.x = ref - default_width / 2
        elif align_type == "center_v":
            ref = sum(e.y + default_height / 2 for e in elements) / len(elements)
            for elem in elements:
                elem.y = ref - default_height / 2
        
        # Canvas neu zeichnen
        self.canvas.redraw_all()
        
        # Publish Event
        self.event_bus.publish("layout:applied", {
            "layout_type": f"align_{align_type}",
            "element_ids": element_ids
        })
        
        # Status-Feedback
        self.event_bus.publish("ui:statusbar:message", {
            "text": f"{len(elements)} Elemente ausgerichtet ({align_type})",
            "timeout": 3000
        })
    
    # ===== Distribute Operations =====
    
    def _on_distribute_horizontal(self, data: Dict[str, Any]) -> None:
        """Horizontal verteilen."""
        self._distribute_elements(data, direction="horizontal")
        
    def _on_distribute_vertical(self, data: Dict[str, Any]) -> None:
        """Vertikal verteilen."""
        self._distribute_elements(data, direction="vertical")
        
    def _distribute_elements(self, data: Dict[str, Any], direction: str) -> None:
        """
        Elemente gleichmäßig verteilen.
        
        Args:
            data: {"element_ids": List[str]}
            direction: "horizontal" oder "vertical"
        """
        if not self.canvas:
            return
            
        element_ids = data.get("element_ids", [])
        
        if len(element_ids) < 3:
            # Keine Element-IDs übergeben, nutze Selektion
            if hasattr(self.canvas, 'selected_ids'):
                element_ids = list(self.canvas.selected_ids)
        
        if len(element_ids) < 3:
            return
            
        elements = [self.canvas.elements.get(eid) for eid in element_ids]
        elements = [e for e in elements if e is not None]
        
        if len(elements) < 3:
            return
        
        # Default element dimensions
        default_width = 120
        default_height = 80
        
        # Sort elements
        if direction == "horizontal":
            elements.sort(key=lambda e: e.x)
            first = elements[0].x
            last = elements[-1].x + default_width
            total_width = sum(default_width for e in elements)
            spacing = (last - first - total_width) / (len(elements) - 1)
            
            current_x = first
            for elem in elements:
                elem.x = current_x
                current_x += default_width + spacing
        else:  # vertical
            elements.sort(key=lambda e: e.y)
            first = elements[0].y
            last = elements[-1].y + default_height
            total_height = sum(default_height for e in elements)
            spacing = (last - first - total_height) / (len(elements) - 1)
            
            current_y = first
            for elem in elements:
                elem.y = current_y
                current_y += default_height + spacing
        
        # Canvas neu zeichnen
        self.canvas.redraw_all()
        
        # Publish Event
        self.event_bus.publish("layout:applied", {
            "layout_type": f"distribute_{direction}",
            "element_ids": element_ids
        })
        
        # Status-Feedback
        self.event_bus.publish("ui:statusbar:message", {
            "text": f"{len(elements)} Elemente verteilt ({direction})",
            "timeout": 3000
        })
    
    # ===== Formation Operations =====
    
    def _on_formation_line(self, data: Dict[str, Any]) -> None:
        """In Linie anordnen."""
        self._formation_elements(data, formation_type="line")
        
    def _on_formation_circle(self, data: Dict[str, Any]) -> None:
        """Im Kreis anordnen."""
        self._formation_elements(data, formation_type="circle")
        
    def _on_formation_grid(self, data: Dict[str, Any]) -> None:
        """Im Gitter anordnen."""
        self._formation_elements(data, formation_type="grid")
        
    def _formation_elements(self, data: Dict[str, Any], formation_type: str) -> None:
        """
        Elemente in Formation anordnen.
        
        Args:
            data: {"element_ids": List[str]}
            formation_type: "line", "circle", "grid"
        """
        if not self.canvas:
            return
            
        element_ids = data.get("element_ids", [])
        
        if len(element_ids) < 2:
            # Keine Element-IDs übergeben, nutze Selektion
            if hasattr(self.canvas, 'selected_ids'):
                element_ids = list(self.canvas.selected_ids)
        
        if len(element_ids) < 2:
            return
            
        elements = [self.canvas.elements.get(eid) for eid in element_ids]
        elements = [e for e in elements if e is not None]
        
        if len(elements) < 2:
            return
        
        if formation_type == "line":
            # Horizontal line
            x_start = 100
            y_pos = 200
            x_spacing = 200
            for idx, elem in enumerate(elements):
                elem.x = x_start + idx * x_spacing
                elem.y = y_pos
                
        elif formation_type == "circle":
            # Circle formation
            center_x = 400
            center_y = 300
            radius = 200
            angle_step = 2 * math.pi / len(elements)
            
            default_width = 120
            default_height = 80
            
            for idx, elem in enumerate(elements):
                angle = idx * angle_step
                elem.x = center_x + radius * math.cos(angle) - default_width / 2
                elem.y = center_y + radius * math.sin(angle) - default_height / 2
                
        elif formation_type == "grid":
            # Grid formation
            x_start = 100
            y_start = 100
            x_spacing = 200
            y_spacing = 150
            cols = math.ceil(math.sqrt(len(elements)))
            
            for idx, elem in enumerate(elements):
                row = idx // cols
                col = idx % cols
                elem.x = x_start + col * x_spacing
                elem.y = y_start + row * y_spacing
        
        # Canvas neu zeichnen
        self.canvas.redraw_all()
        
        # Publish Event
        self.event_bus.publish("layout:applied", {
            "layout_type": f"formation_{formation_type}",
            "element_ids": element_ids
        })
        
        # Status-Feedback
        self.event_bus.publish("ui:statusbar:message", {
            "text": f"{len(elements)} Elemente in {formation_type} angeordnet",
            "timeout": 3000
        })
    
    # ===== Document Lifecycle =====
    
    def _on_document_changed(self, data: Dict[str, Any]) -> None:
        """
        Neues Dokument erstellt oder geladen.
        
        Args:
            data: {"document": DocumentModel}
        """
        # Nicht mehr benötigt, da wir direkt mit Canvas arbeiten
        pass
        
    def _on_document_closed(self, data: Dict[str, Any]) -> None:
        """
        Dokument geschlossen.
        
        Args:
            data: Event-Daten (leer)
        """
        # Nicht mehr benötigt, da wir direkt mit Canvas arbeiten
        pass
        
    # ===== Public API =====
    
    def set_document(self, document: Optional[Any]) -> None:
        """
        Setzt das aktuelle Dokument (Legacy-Kompatibilität).
        
        Args:
            document: DocumentModel oder None (nicht mehr verwendet)
        """
        # Nicht mehr benötigt, da wir direkt mit Canvas arbeiten
        pass
        
    def apply_auto_layout(self, algorithm: str = "hierarchical") -> None:
        """
        Wendet Auto-Layout an.
        
        Args:
            algorithm: Layout-Algorithmus (default: "hierarchical")
        """
        self._on_auto_layout({"algorithm": algorithm})
        
    def align_elements(self, element_ids: List[str], align_type: str) -> None:
        """
        Richtet Elemente aus.
        
        Args:
            element_ids: Liste von Element-IDs
            align_type: Art der Ausrichtung
        """
        self._align_elements({"element_ids": element_ids}, align_type)
        
    def __repr__(self) -> str:
        """String-Repräsentation."""
        canvas_status = "with canvas" if self.canvas else "no canvas"
        elem_count = len(self.canvas.elements) if self.canvas else 0
        return f"<LayoutController({canvas_status}, elements={elem_count})>"
