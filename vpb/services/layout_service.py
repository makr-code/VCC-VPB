"""
VPB Layout Service
==================

Service for automatic layout and arrangement of process diagram elements.

This service provides layout algorithms including:
- Element alignment (left, right, center, top, bottom, middle)
- Circular arrangement
- Auto-layout (hierarchical BFS-based)
- Distribution (horizontal, vertical)
- Grid arrangement

The service operates on DocumentModel and returns updated element positions
without directly modifying the document.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Set
from collections import deque
import math
import logging

from vpb.models.document import DocumentModel
from vpb.models.element import VPBElement
from vpb.models.connection import VPBConnection
from vpb.infrastructure.event_bus import get_global_event_bus


logger = logging.getLogger(__name__)


# ============================================================================
# Exceptions
# ============================================================================

class LayoutServiceError(Exception):
    """Base exception for layout service errors."""
    pass


class InsufficientElementsError(LayoutServiceError):
    """Raised when not enough elements for layout operation."""
    pass


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class LayoutConfig:
    """Configuration for layout service."""
    
    # Default element sizes (used for bounds calculation)
    default_element_sizes: Dict[str, Tuple[int, int]] = None
    
    # Auto-layout settings
    auto_layout_column_spacing: int = 200
    auto_layout_row_spacing: int = 120
    
    # Circular arrangement settings
    circular_min_radius: float = 80.0
    circular_spacing_factor: float = 1.15
    
    # Grid arrangement settings
    grid_spacing_x: int = 150
    grid_spacing_y: int = 100
    
    def __post_init__(self):
        if self.default_element_sizes is None:
            self.default_element_sizes = {
                'Ereignis': (60, 60),
                'START_EVENT': (60, 60),
                'END_EVENT': (60, 60),
                'Prozess': (120, 80),
                'Vorprozess': (120, 80),
                'Nachprozess': (120, 80),
                'Entscheidung': (80, 80),
                'Gateway': (80, 80),
                'AND_Gateway': (80, 80),
                'OR_Gateway': (80, 80),
                'XOR_Gateway': (80, 80),
                'Konnektor': (40, 40),
                'AND_CONNECTOR': (40, 40),
                'OR_CONNECTOR': (40, 40),
                'XOR_CONNECTOR': (40, 40),
                'Container': (200, 150),
            }


# ============================================================================
# Layout Result
# ============================================================================

@dataclass
class LayoutResult:
    """Result of a layout operation."""
    
    # Updated element positions {element_id: (x, y)}
    element_positions: Dict[str, Tuple[int, int]]
    
    # Number of elements affected
    elements_moved: int
    
    # Optional message
    message: Optional[str] = None
    
    def __bool__(self) -> bool:
        """Layout result is truthy if elements were moved."""
        return self.elements_moved > 0


# ============================================================================
# Layout Service
# ============================================================================

class LayoutService:
    """
    Service for layout operations on process diagrams.
    
    Provides various layout algorithms that can be applied to documents.
    All operations return LayoutResult with new positions without modifying
    the document directly.
    """
    
    def __init__(self, config: Optional[LayoutConfig] = None):
        """
        Initialize layout service.
        
        Args:
            config: Layout configuration, uses defaults if None
        """
        self.config = config or LayoutConfig()
        self.event_bus = get_global_event_bus()
        logger.info(f"LayoutService initialized with config: {self.config}")
    
    def _get_element_bounds(self, element: VPBElement) -> Tuple[int, int, int, int]:
        """
        Get element bounds (x1, y1, x2, y2).
        
        Args:
            element: Element to get bounds for
            
        Returns:
            Tuple of (x1, y1, x2, y2) coordinates
        """
        width, height = self.config.default_element_sizes.get(
            element.element_type, 
            (100, 80)
        )
        x1 = element.x - width // 2
        y1 = element.y - height // 2
        x2 = element.x + width // 2
        y2 = element.y + height // 2
        return (x1, y1, x2, y2)
    
    def _get_element_center(self, element: VPBElement) -> Tuple[float, float]:
        """Get element center point."""
        return (float(element.x), float(element.y))
    
    # ========================================================================
    # Alignment Operations
    # ========================================================================
    
    def align_elements(
        self,
        elements: List[VPBElement],
        mode: str
    ) -> LayoutResult:
        """
        Align elements according to mode.
        
        Args:
            elements: Elements to align
            mode: Alignment mode (left, right, center, top, bottom, middle)
            
        Returns:
            LayoutResult with new positions
            
        Raises:
            InsufficientElementsError: If less than 2 elements
            ValueError: If invalid alignment mode
        """
        if len(elements) < 2:
            raise InsufficientElementsError("Need at least 2 elements to align")
        
        self.event_bus.publish('layout:align:started', {
            'element_count': len(elements),
            'mode': mode
        })
        
        try:
            # Calculate bounds and centers
            bounds = {el.element_id: self._get_element_bounds(el) for el in elements}
            centers = {
                el.element_id: self._get_element_center(el) 
                for el in elements
            }
            
            mode = mode.lower()
            target_x = None
            target_y = None
            
            # Determine target coordinate
            if mode == "left":
                target_x = min(b[0] for b in bounds.values())
            elif mode == "right":
                target_x = max(b[2] for b in bounds.values())
            elif mode in {"center", "centre"}:
                target_x = sum(c[0] for c in centers.values()) / len(centers)
            elif mode == "top":
                target_y = min(b[1] for b in bounds.values())
            elif mode == "bottom":
                target_y = max(b[3] for b in bounds.values())
            elif mode in {"middle", "vertical", "middle_vertical"}:
                target_y = sum(c[1] for c in centers.values()) / len(centers)
            else:
                raise ValueError(f"Invalid alignment mode: {mode}")
            
            # Calculate new positions
            new_positions = {}
            for el in elements:
                b = bounds[el.element_id]
                new_x = float(el.x)
                new_y = float(el.y)
                
                if target_x is not None:
                    width = max(1.0, b[2] - b[0])
                    if mode == "left":
                        new_x = target_x + width / 2.0
                    elif mode == "right":
                        new_x = target_x - width / 2.0
                    else:  # center
                        new_x = target_x
                
                if target_y is not None:
                    height = max(1.0, b[3] - b[1])
                    if mode == "top":
                        new_y = target_y + height / 2.0
                    elif mode == "bottom":
                        new_y = target_y - height / 2.0
                    else:  # middle
                        new_y = target_y
                
                new_positions[el.element_id] = (int(round(new_x)), int(round(new_y)))
            
            # Count how many actually moved
            moved = sum(
                1 for el in elements
                if new_positions[el.element_id] != (el.x, el.y)
            )
            
            result = LayoutResult(
                element_positions=new_positions,
                elements_moved=moved,
                message=f"Aligned {moved} elements {mode}"
            )
            
            self.event_bus.publish('layout:align:completed', {
                'element_count': len(elements),
                'mode': mode,
                'moved': moved
            })
            
            return result
            
        except Exception as e:
            self.event_bus.publish('layout:align:failed', {
                'error': str(e),
                'mode': mode
            })
            raise
    
    # ========================================================================
    # Circular Arrangement
    # ========================================================================
    
    def arrange_circular(
        self,
        elements: List[VPBElement],
        center: Optional[Tuple[float, float]] = None,
        radius: Optional[float] = None
    ) -> LayoutResult:
        """
        Arrange elements in a circle.
        
        Args:
            elements: Elements to arrange
            center: Center point (x, y), calculated from elements if None
            radius: Circle radius, calculated if None
            
        Returns:
            LayoutResult with new positions
            
        Raises:
            InsufficientElementsError: If less than 2 elements
        """
        if len(elements) < 2:
            raise InsufficientElementsError("Need at least 2 elements for circular arrangement")
        
        self.event_bus.publish('layout:circular:started', {
            'element_count': len(elements)
        })
        
        try:
            # Calculate center if not provided
            if center is None:
                cx = sum(el.x for el in elements) / len(elements)
                cy = sum(el.y for el in elements) / len(elements)
            else:
                cx, cy = center
            
            # Get maximum element extent
            bounds = [self._get_element_bounds(el) for el in elements]
            max_extent = max(
                max(b[2] - b[0], b[3] - b[1])
                for b in bounds
            )
            
            # Calculate radius if not provided
            if radius is None:
                # Calculate based on circumference needed
                circumference_needed = len(elements) * max_extent * self.config.circular_spacing_factor
                radius_min = circumference_needed / (2.0 * math.pi) if circumference_needed > 0 else 0.0
                
                # Also consider current max distance
                max_distance = max(
                    math.hypot(el.x - cx, el.y - cy) 
                    for el in elements
                )
                
                radius = max(
                    radius_min, 
                    max_distance, 
                    max_extent * 0.75, 
                    self.config.circular_min_radius
                )
            
            # Calculate current angles to preserve relative positions
            angle_pairs = []
            for el in elements:
                angle = math.atan2(el.y - cy, el.x - cx)
                angle_pairs.append((el, angle))
            
            # Sort by angle
            angle_pairs.sort(key=lambda item: (item[1], item[0].element_id))
            
            # Calculate new positions
            step = (2.0 * math.pi) / len(angle_pairs)
            start_angle = angle_pairs[0][1] if angle_pairs else 0.0
            
            new_positions = {}
            for index, (el, _) in enumerate(angle_pairs):
                angle = start_angle + index * step
                nx = cx + radius * math.cos(angle)
                ny = cy + radius * math.sin(angle)
                new_positions[el.element_id] = (int(round(nx)), int(round(ny)))
            
            # Count moved elements
            moved = sum(
                1 for el in elements
                if new_positions[el.element_id] != (el.x, el.y)
            )
            
            result = LayoutResult(
                element_positions=new_positions,
                elements_moved=moved,
                message=f"Arranged {moved} elements in circle (radius={radius:.0f})"
            )
            
            self.event_bus.publish('layout:circular:completed', {
                'element_count': len(elements),
                'moved': moved,
                'radius': radius
            })
            
            return result
            
        except Exception as e:
            self.event_bus.publish('layout:circular:failed', {
                'error': str(e)
            })
            raise
    
    # ========================================================================
    # Auto Layout (Hierarchical)
    # ========================================================================
    
    def auto_layout(
        self,
        document: DocumentModel
    ) -> LayoutResult:
        """
        Apply automatic hierarchical layout based on process flow.
        
        Uses BFS from start events to create layers, then arranges
        elements in columns based on their layer.
        
        Args:
            document: Document to layout
            
        Returns:
            LayoutResult with new positions
        """
        elements = document.get_all_elements()
        connections = document.get_all_connections()
        
        if not elements:
            return LayoutResult(
                element_positions={},
                elements_moved=0,
                message="No elements to layout"
            )
        
        self.event_bus.publish('layout:auto:started', {
            'element_count': len(elements),
            'connection_count': len(connections)
        })
        
        try:
            # Build graph structure
            outgoing: Dict[str, List[str]] = {}
            incoming_count: Dict[str, int] = {el.element_id: 0 for el in elements}
            
            for conn in connections:
                s, t = conn.source_element, conn.target_element
                element_ids = {el.element_id for el in elements}
                if s in element_ids and t in element_ids:
                    outgoing.setdefault(s, []).append(t)
                    incoming_count[t] = incoming_count.get(t, 0) + 1
            
            # Find start nodes (START_EVENT or in-degree 0)
            starts = [
                el.element_id for el in elements 
                if el.element_type in ("START_EVENT", "Ereignis")
            ]
            if not starts:
                starts = [eid for eid, deg in incoming_count.items() if deg == 0]
            if not starts and elements:
                starts = [elements[0].element_id]
            
            # BFS to assign layers
            level: Dict[str, int] = {}
            queue = deque()
            for s in starts:
                level[s] = 0
                queue.append(s)
            
            while queue:
                u = queue.popleft()
                for v in outgoing.get(u, []):
                    if v not in level:
                        level[v] = level[u] + 1
                        queue.append(v)
            
            # Assign unvisited to last layer
            max_level = max(level.values()) if level else 0
            for el in elements:
                if el.element_id not in level:
                    level[el.element_id] = max_level + 1
            
            # Group elements by layer
            layers: Dict[int, List[VPBElement]] = {}
            for el in elements:
                lv = level[el.element_id]
                layers.setdefault(lv, []).append(el)
            
            # Sort within layers (connectors in middle)
            def type_weight(element_type: str) -> int:
                t = (element_type or "").upper()
                if "CONNECTOR" in t or "GATEWAY" in t:
                    return 1
                if "END" in t:
                    return 3
                return 2
            
            for lv in layers:
                layers[lv].sort(key=lambda el: (
                    type_weight(el.element_type),
                    el.element_id
                ))
            
            # Calculate positions
            new_positions = {}
            for lv, layer_elements in sorted(layers.items()):
                x = lv * self.config.auto_layout_column_spacing
                count = len(layer_elements)
                total_height = count * self.config.auto_layout_row_spacing
                start_y = -total_height // 2
                
                for idx, el in enumerate(layer_elements):
                    y = start_y + idx * self.config.auto_layout_row_spacing
                    new_positions[el.element_id] = (x, y)
            
            # Count moved elements
            moved = sum(
                1 for el in elements
                if new_positions[el.element_id] != (el.x, el.y)
            )
            
            result = LayoutResult(
                element_positions=new_positions,
                elements_moved=moved,
                message=f"Auto-layout applied to {moved} elements in {len(layers)} layers"
            )
            
            self.event_bus.publish('layout:auto:completed', {
                'element_count': len(elements),
                'moved': moved,
                'layers': len(layers)
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Auto-layout failed: {e}", exc_info=True)
            self.event_bus.publish('layout:auto:failed', {
                'error': str(e)
            })
            raise LayoutServiceError(f"Auto-layout failed: {e}") from e
    
    # ========================================================================
    # Distribution
    # ========================================================================
    
    def distribute_elements(
        self,
        elements: List[VPBElement],
        mode: str
    ) -> LayoutResult:
        """
        Distribute elements evenly.
        
        Args:
            elements: Elements to distribute
            mode: Distribution mode (horizontal, vertical)
            
        Returns:
            LayoutResult with new positions
            
        Raises:
            InsufficientElementsError: If less than 3 elements
            ValueError: If invalid mode
        """
        if len(elements) < 3:
            raise InsufficientElementsError("Need at least 3 elements to distribute")
        
        mode = mode.lower()
        if mode not in ("horizontal", "vertical"):
            raise ValueError(f"Invalid distribution mode: {mode}")
        
        self.event_bus.publish('layout:distribute:started', {
            'element_count': len(elements),
            'mode': mode
        })
        
        try:
            if mode == "horizontal":
                # Sort by x position
                sorted_elements = sorted(elements, key=lambda el: el.x)
                min_x = sorted_elements[0].x
                max_x = sorted_elements[-1].x
                spacing = (max_x - min_x) / (len(elements) - 1) if len(elements) > 1 else 0
                
                new_positions = {}
                for idx, el in enumerate(sorted_elements):
                    new_x = int(round(min_x + idx * spacing))
                    new_positions[el.element_id] = (new_x, el.y)
            
            else:  # vertical
                # Sort by y position
                sorted_elements = sorted(elements, key=lambda el: el.y)
                min_y = sorted_elements[0].y
                max_y = sorted_elements[-1].y
                spacing = (max_y - min_y) / (len(elements) - 1) if len(elements) > 1 else 0
                
                new_positions = {}
                for idx, el in enumerate(sorted_elements):
                    new_y = int(round(min_y + idx * spacing))
                    new_positions[el.element_id] = (el.x, new_y)
            
            # Count moved
            moved = sum(
                1 for el in elements
                if new_positions[el.element_id] != (el.x, el.y)
            )
            
            result = LayoutResult(
                element_positions=new_positions,
                elements_moved=moved,
                message=f"Distributed {moved} elements {mode}ly"
            )
            
            self.event_bus.publish('layout:distribute:completed', {
                'element_count': len(elements),
                'mode': mode,
                'moved': moved
            })
            
            return result
            
        except Exception as e:
            self.event_bus.publish('layout:distribute:failed', {
                'error': str(e),
                'mode': mode
            })
            raise
    
    # ========================================================================
    # Grid Arrangement
    # ========================================================================
    
    def arrange_grid(
        self,
        elements: List[VPBElement],
        columns: Optional[int] = None
    ) -> LayoutResult:
        """
        Arrange elements in a grid.
        
        Args:
            elements: Elements to arrange
            columns: Number of columns, calculated if None
            
        Returns:
            LayoutResult with new positions
        """
        if not elements:
            return LayoutResult(
                element_positions={},
                elements_moved=0,
                message="No elements to arrange"
            )
        
        self.event_bus.publish('layout:grid:started', {
            'element_count': len(elements)
        })
        
        try:
            # Calculate columns if not specified
            if columns is None:
                columns = math.ceil(math.sqrt(len(elements)))
            
            # Calculate center point of current elements
            cx = sum(el.x for el in elements) / len(elements)
            cy = sum(el.y for el in elements) / len(elements)
            
            # Calculate grid dimensions
            rows = math.ceil(len(elements) / columns)
            grid_width = (columns - 1) * self.config.grid_spacing_x
            grid_height = (rows - 1) * self.config.grid_spacing_y
            
            # Starting position (top-left of grid, centered around cx, cy)
            start_x = int(cx - grid_width / 2)
            start_y = int(cy - grid_height / 2)
            
            # Arrange elements
            new_positions = {}
            for idx, el in enumerate(elements):
                col = idx % columns
                row = idx // columns
                x = start_x + col * self.config.grid_spacing_x
                y = start_y + row * self.config.grid_spacing_y
                new_positions[el.element_id] = (x, y)
            
            # Count moved
            moved = sum(
                1 for el in elements
                if new_positions[el.element_id] != (el.x, el.y)
            )
            
            result = LayoutResult(
                element_positions=new_positions,
                elements_moved=moved,
                message=f"Arranged {moved} elements in {rows}x{columns} grid"
            )
            
            self.event_bus.publish('layout:grid:completed', {
                'element_count': len(elements),
                'moved': moved,
                'rows': rows,
                'columns': columns
            })
            
            return result
            
        except Exception as e:
            self.event_bus.publish('layout:grid:failed', {
                'error': str(e)
            })
            raise
    
    def __repr__(self) -> str:
        return f"LayoutService(config={self.config})"
