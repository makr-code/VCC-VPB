"""
VPB Connection Model
====================

Domain model for connections between VPB process elements.

This module defines the VPBConnection class representing arrows/connections
between process elements.

Features:
- Type-safe connection representation
- Validation of source/target references
- Multiple connection types (SEQUENCE, DEPENDENCY, etc.)
- Routing modes (auto, straight, orthogonal)
- Serialization support
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
from uuid import uuid4
import logging


logger = logging.getLogger(__name__)


# Connection type constants
CONNECTION_TYPES = {
    'SEQUENCE': 'Ablauf-Sequenz',
    'DEPENDENCY': 'Abhängigkeit',
    'INFORMATION': 'Informationsfluss',
    'DATA': 'Datenfluss',
    'ASSOCIATION': 'Assoziation',
}

# Arrow style constants
ARROW_STYLES = {
    'single': 'Einfacher Pfeil',
    'double': 'Doppelpfeil',
    'none': 'Keine Pfeilspitze',
}

# Routing mode constants
ROUTING_MODES = {
    'auto': 'Automatisch',
    'straight': 'Gerade Linie',
    'orthogonal': 'Orthogonal',
    'curved': 'Gebogen',
}


@dataclass
class VPBConnection:
    """
    VPB Process Connection.
    
    Represents a connection/arrow between two elements in a VPB process diagram.
    
    Attributes:
        connection_id: Unique identifier
        source_element: ID of source element
        target_element: ID of target element
        connection_type: Type of connection (SEQUENCE, DEPENDENCY, etc.)
        description: Optional description/label
        arrow_style: Arrow style (single, double, none)
        routing_mode: How the connection should be routed
        canvas_item: Canvas item ID (transient)
        waypoints: Optional manual waypoints for routing
    """
    
    # Core properties
    connection_id: str
    source_element: str
    target_element: str
    
    # Optional properties with defaults
    connection_type: str = "SEQUENCE"
    description: str = ""
    arrow_style: str = "single"
    routing_mode: str = "auto"
    
    # Canvas integration (transient)
    canvas_item: Optional[int] = None
    
    # Manual routing
    waypoints: List[Tuple[int, int]] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate connection after creation."""
        self.validate()
    
    def validate(self) -> None:
        """
        Validate connection properties.
        
        Raises:
            ValueError: If validation fails
        """
        if not self.connection_id:
            raise ValueError("connection_id cannot be empty")
        
        if not self.source_element:
            raise ValueError("source_element cannot be empty")
        
        if not self.target_element:
            raise ValueError("target_element cannot be empty")
        
        if self.source_element == self.target_element:
            raise ValueError("Cannot connect element to itself")
        
        if self.connection_type not in CONNECTION_TYPES:
            logger.warning(f"Unknown connection type: {self.connection_type}")
        
        if self.arrow_style not in ARROW_STYLES:
            logger.warning(f"Unknown arrow style: {self.arrow_style}")
        
        if self.routing_mode not in ROUTING_MODES:
            logger.warning(f"Unknown routing mode: {self.routing_mode}")
    
    def is_sequence(self) -> bool:
        """Check if this is a sequence connection."""
        return self.connection_type == 'SEQUENCE'
    
    def is_dependency(self) -> bool:
        """Check if this is a dependency connection."""
        return self.connection_type == 'DEPENDENCY'
    
    def is_information_flow(self) -> bool:
        """Check if this is an information flow connection."""
        return self.connection_type == 'INFORMATION'
    
    def has_waypoints(self) -> bool:
        """Check if connection has manual waypoints."""
        return len(self.waypoints) > 0
    
    def add_waypoint(self, x: int, y: int) -> None:
        """
        Add a waypoint for manual routing.
        
        Args:
            x: X-coordinate
            y: Y-coordinate
        """
        self.waypoints.append((x, y))
    
    def clear_waypoints(self) -> None:
        """Remove all waypoints."""
        self.waypoints.clear()
    
    def reverse(self) -> VPBConnection:
        """
        Create a reversed connection (swap source and target).
        
        Returns:
            New VPBConnection with reversed direction
        """
        return VPBConnection(
            connection_id=f"{self.connection_id}_reversed",
            source_element=self.target_element,
            target_element=self.source_element,
            connection_type=self.connection_type,
            description=self.description,
            arrow_style=self.arrow_style,
            routing_mode=self.routing_mode,
            waypoints=list(reversed(self.waypoints)),
        )
    
    def clone(self, new_id: Optional[str] = None) -> VPBConnection:
        """
        Create a copy of this connection.
        
        Args:
            new_id: Optional new ID for the clone
            
        Returns:
            New VPBConnection instance
        """
        return VPBConnection(
            connection_id=new_id or f"{self.connection_id}_copy",
            source_element=self.source_element,
            target_element=self.target_element,
            connection_type=self.connection_type,
            description=self.description,
            arrow_style=self.arrow_style,
            routing_mode=self.routing_mode,
            waypoints=self.waypoints.copy(),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert connection to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            'connection_id': self.connection_id,
            'source_element': self.source_element,
            'target_element': self.target_element,
            'connection_type': self.connection_type,
            'description': self.description,
            'arrow_style': self.arrow_style,
            'routing_mode': self.routing_mode,
            'waypoints': self.waypoints,
            # Note: canvas_item is transient and not serialized
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> VPBConnection:
        """
        Create connection from dictionary.
        
        Args:
            data: Dictionary with connection data
            
        Returns:
            New VPBConnection instance
        """
        return cls(
            connection_id=data['connection_id'],
            source_element=data['source_element'],
            target_element=data['target_element'],
            connection_type=data.get('connection_type', 'SEQUENCE'),
            description=data.get('description', ''),
            arrow_style=data.get('arrow_style', 'single'),
            routing_mode=data.get('routing_mode', 'auto'),
            waypoints=data.get('waypoints', []),
        )
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"VPBConnection(id='{self.connection_id}', "
            f"from='{self.source_element}', "
            f"to='{self.target_element}', "
            f"type='{self.connection_type}')"
        )


class ConnectionFactory:
    """
    Factory for creating VPB connections.
    
    Provides convenient methods to create connections with proper defaults.
    """
    
    @staticmethod
    def create(
        source_element: str,
        target_element: str,
        connection_type: str = "SEQUENCE",
        connection_id: Optional[str] = None,
        **kwargs
    ) -> VPBConnection:
        """
        Create a new VPB connection.
        
        Args:
            source_element: Source element ID
            target_element: Target element ID
            connection_type: Type of connection
            connection_id: Connection ID (auto-generated if None)
            **kwargs: Additional properties
            
        Returns:
            New VPBConnection instance
        """
        if connection_id is None:
            connection_id = f"conn_{uuid4().hex[:8]}"
        
        return VPBConnection(
            connection_id=connection_id,
            source_element=source_element,
            target_element=target_element,
            connection_type=connection_type,
            **kwargs
        )
    
    @staticmethod
    def create_sequence(
        source_element: str,
        target_element: str,
        description: str = ""
    ) -> VPBConnection:
        """
        Create a sequence connection.
        
        Args:
            source_element: Source element ID
            target_element: Target element ID
            description: Optional description
            
        Returns:
            New sequence connection
        """
        return ConnectionFactory.create(
            source_element,
            target_element,
            connection_type="SEQUENCE",
            description=description
        )
    
    @staticmethod
    def create_dependency(
        source_element: str,
        target_element: str,
        description: str = ""
    ) -> VPBConnection:
        """
        Create a dependency connection.
        
        Args:
            source_element: Source element ID
            target_element: Target element ID
            description: Optional description
            
        Returns:
            New dependency connection
        """
        return ConnectionFactory.create(
            source_element,
            target_element,
            connection_type="DEPENDENCY",
            description=description,
            arrow_style="double"
        )
    
    @staticmethod
    def create_information_flow(
        source_element: str,
        target_element: str,
        description: str = ""
    ) -> VPBConnection:
        """
        Create an information flow connection.
        
        Args:
            source_element: Source element ID
            target_element: Target element ID
            description: Optional description
            
        Returns:
            New information flow connection
        """
        return ConnectionFactory.create(
            source_element,
            target_element,
            connection_type="INFORMATION",
            description=description
        )
    
    @staticmethod
    def create_data_flow(
        source_element: str,
        target_element: str,
        description: str = ""
    ) -> VPBConnection:
        """
        Create a data flow connection.
        
        Args:
            source_element: Source element ID
            target_element: Target element ID
            description: Optional description
            
        Returns:
            New data flow connection
        """
        return ConnectionFactory.create(
            source_element,
            target_element,
            connection_type="DATA",
            description=description
        )


__all__ = [
    'VPBConnection',
    'ConnectionFactory',
    'CONNECTION_TYPES',
    'ARROW_STYLES',
    'ROUTING_MODES',
]
