"""
VPB Element Model
=================

Domain model for VPB process elements.

This module defines the VPBElement class representing individual process elements
like VorProzess, Prozess, NachProzess, Entscheidung, etc.

Features:
- Immutable data structure (frozen dataclass)
- Type validation
- Serialization (to_dict/from_dict)
- Geometry calculations
- Factory pattern for creation
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple, Dict, Any
from uuid import uuid4
import logging


logger = logging.getLogger(__name__)


# Element type constants
ELEMENT_TYPES = {
    'VorProzess': 'Vor-Prozess',
    'Prozess': 'Prozess',
    'NachProzess': 'Nach-Prozess',
    'Entscheidung': 'Entscheidung',
    'Datenobjekt': 'Datenobjekt',
    'Ereignis': 'Ereignis',
    'Schnittstelle': 'Schnittstelle',
    'Container': 'Container',
    'AND': 'AND-Gateway',
    'OR': 'OR-Gateway',
    'XOR': 'XOR-Gateway',
}


@dataclass
class VPBElement:
    """
    VPB Process Element.
    
    Represents a single element in a VPB process diagram.
    
    Attributes:
        element_id: Unique identifier
        element_type: Type of element (VorProzess, Prozess, etc.)
        name: Display name/label
        x: X-coordinate on canvas
        y: Y-coordinate on canvas
        description: Detailed description
        responsible_authority: Responsible authority/department
        legal_basis: Legal basis reference
        deadline_days: Deadline in days
        geo_reference: Geographic reference
        ref_file: Reference to external file
        ref_inline_content: Inline content reference
        ref_inline_path: Path to inline content
        ref_inline_error: Error loading inline content
        ref_inline_truncated: Whether inline content was truncated
        ref_source_mtime: Modification time of source file
        original_element_type: Original type before transformation
        members: List of member element IDs (for containers)
        collapsed: Whether container is collapsed
        canvas_items: List of canvas item IDs
    """
    
    # Core properties
    element_id: str
    element_type: str
    name: str
    x: int
    y: int
    
    # Optional properties with defaults
    description: str = ""
    responsible_authority: str = ""
    legal_basis: str = ""
    deadline_days: int = 0
    geo_reference: str = ""
    
    # File references
    ref_file: str = ""
    ref_inline_content: Optional[str] = None
    ref_inline_path: Optional[str] = None
    ref_inline_error: Optional[str] = None
    ref_inline_truncated: bool = False
    ref_source_mtime: Optional[float] = None
    
    # Type transformation
    original_element_type: Optional[str] = None
    
    # Container properties
    members: List[str] = field(default_factory=list)
    collapsed: bool = False
    
    # Canvas integration
    canvas_items: List[int] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate element after creation."""
        self.validate()
    
    def validate(self) -> None:
        """
        Validate element properties.
        
        Raises:
            ValueError: If validation fails
        """
        if not self.element_id:
            raise ValueError("element_id cannot be empty")
        
        if not self.element_type:
            raise ValueError("element_type cannot be empty")
        
        if self.element_type not in ELEMENT_TYPES:
            logger.warning(f"Unknown element type: {self.element_type}")
        
        if not self.name:
            logger.warning(f"Element {self.element_id} has no name")
        
        if self.deadline_days < 0:
            raise ValueError("deadline_days cannot be negative")
    
    def center(self) -> Tuple[int, int]:
        """
        Get center coordinates of element.
        
        Returns:
            Tuple of (x, y) coordinates
        """
        return (self.x, self.y)
    
    def move_to(self, x: int, y: int) -> VPBElement:
        """
        Create a new element at different position.
        
        Args:
            x: New x-coordinate
            y: New y-coordinate
            
        Returns:
            New VPBElement instance at new position
        """
        return VPBElement(
            element_id=self.element_id,
            element_type=self.element_type,
            name=self.name,
            x=x,
            y=y,
            description=self.description,
            responsible_authority=self.responsible_authority,
            legal_basis=self.legal_basis,
            deadline_days=self.deadline_days,
            geo_reference=self.geo_reference,
            ref_file=self.ref_file,
            ref_inline_content=self.ref_inline_content,
            ref_inline_path=self.ref_inline_path,
            ref_inline_error=self.ref_inline_error,
            ref_inline_truncated=self.ref_inline_truncated,
            ref_source_mtime=self.ref_source_mtime,
            original_element_type=self.original_element_type,
            members=self.members.copy(),
            collapsed=self.collapsed,
            canvas_items=self.canvas_items.copy(),
        )
    
    def clone(self, new_id: Optional[str] = None) -> VPBElement:
        """
        Create a deep copy of this element.
        
        Args:
            new_id: Optional new ID for the clone
            
        Returns:
            New VPBElement instance
        """
        return VPBElement(
            element_id=new_id or f"{self.element_id}_copy",
            element_type=self.element_type,
            name=f"{self.name} (copy)" if not new_id else self.name,
            x=self.x + 20,  # Offset slightly
            y=self.y + 20,
            description=self.description,
            responsible_authority=self.responsible_authority,
            legal_basis=self.legal_basis,
            deadline_days=self.deadline_days,
            geo_reference=self.geo_reference,
            ref_file=self.ref_file,
            ref_inline_content=self.ref_inline_content,
            ref_inline_path=self.ref_inline_path,
            ref_inline_error=self.ref_inline_error,
            ref_inline_truncated=self.ref_inline_truncated,
            ref_source_mtime=self.ref_source_mtime,
            original_element_type=self.original_element_type,
            members=self.members.copy(),
            collapsed=self.collapsed,
            canvas_items=[],  # Don't copy canvas items
        )
    
    def is_container(self) -> bool:
        """Check if this element is a container."""
        return self.element_type == 'Container'
    
    def is_gateway(self) -> bool:
        """Check if this element is a gateway (AND/OR/XOR)."""
        return self.element_type in ('AND', 'OR', 'XOR')
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert element to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            'element_id': self.element_id,
            'element_type': self.element_type,
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'description': self.description,
            'responsible_authority': self.responsible_authority,
            'legal_basis': self.legal_basis,
            'deadline_days': self.deadline_days,
            'geo_reference': self.geo_reference,
            'ref_file': self.ref_file,
            'ref_inline_content': self.ref_inline_content,
            'ref_inline_path': self.ref_inline_path,
            'ref_inline_error': self.ref_inline_error,
            'ref_inline_truncated': self.ref_inline_truncated,
            'ref_source_mtime': self.ref_source_mtime,
            'original_element_type': self.original_element_type,
            'members': self.members,
            'collapsed': self.collapsed,
            # Note: canvas_items are transient and not serialized
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> VPBElement:
        """
        Create element from dictionary.
        
        Args:
            data: Dictionary with element data
            
        Returns:
            New VPBElement instance
        """
        return cls(
            element_id=data['element_id'],
            element_type=data['element_type'],
            name=data['name'],
            x=int(data['x']),
            y=int(data['y']),
            description=data.get('description', ''),
            responsible_authority=data.get('responsible_authority', ''),
            legal_basis=data.get('legal_basis', ''),
            deadline_days=int(data.get('deadline_days', 0)),
            geo_reference=data.get('geo_reference', ''),
            ref_file=data.get('ref_file', ''),
            ref_inline_content=data.get('ref_inline_content'),
            ref_inline_path=data.get('ref_inline_path'),
            ref_inline_error=data.get('ref_inline_error'),
            ref_inline_truncated=bool(data.get('ref_inline_truncated', False)),
            ref_source_mtime=data.get('ref_source_mtime'),
            original_element_type=data.get('original_element_type'),
            members=data.get('members', []),
            collapsed=bool(data.get('collapsed', False)),
            canvas_items=[],  # Don't restore canvas items
        )
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"VPBElement(id='{self.element_id}', "
            f"type='{self.element_type}', "
            f"name='{self.name}', "
            f"pos=({self.x}, {self.y}))"
        )


class ElementFactory:
    """
    Factory for creating VPB elements.
    
    Provides convenient methods to create elements with proper defaults.
    """
    
    @staticmethod
    def create(
        element_type: str,
        x: int,
        y: int,
        name: Optional[str] = None,
        element_id: Optional[str] = None,
        **kwargs
    ) -> VPBElement:
        """
        Create a new VPB element.
        
        Args:
            element_type: Type of element
            x: X-coordinate
            y: Y-coordinate
            name: Element name (auto-generated if None)
            element_id: Element ID (auto-generated if None)
            **kwargs: Additional properties
            
        Returns:
            New VPBElement instance
        """
        if element_id is None:
            element_id = f"elem_{uuid4().hex[:8]}"
        
        if name is None:
            name = ELEMENT_TYPES.get(element_type, element_type)
        
        return VPBElement(
            element_id=element_id,
            element_type=element_type,
            name=name,
            x=x,
            y=y,
            **kwargs
        )
    
    @staticmethod
    def create_prozess(x: int, y: int, name: str = "Prozess") -> VPBElement:
        """Create a Prozess element."""
        return ElementFactory.create('Prozess', x, y, name)
    
    @staticmethod
    def create_vorprozess(x: int, y: int, name: str = "Vor-Prozess") -> VPBElement:
        """Create a VorProzess element."""
        return ElementFactory.create('VorProzess', x, y, name)
    
    @staticmethod
    def create_nachprozess(x: int, y: int, name: str = "Nach-Prozess") -> VPBElement:
        """Create a NachProzess element."""
        return ElementFactory.create('NachProzess', x, y, name)
    
    @staticmethod
    def create_entscheidung(x: int, y: int, name: str = "Entscheidung") -> VPBElement:
        """Create an Entscheidung element."""
        return ElementFactory.create('Entscheidung', x, y, name)
    
    @staticmethod
    def create_gateway(
        gateway_type: str,
        x: int,
        y: int,
        name: Optional[str] = None
    ) -> VPBElement:
        """
        Create a gateway element.
        
        Args:
            gateway_type: 'AND', 'OR', or 'XOR'
            x: X-coordinate
            y: Y-coordinate
            name: Gateway name
            
        Returns:
            New gateway element
        """
        if gateway_type not in ('AND', 'OR', 'XOR'):
            raise ValueError(f"Invalid gateway type: {gateway_type}")
        
        if name is None:
            name = f"{gateway_type}-Gateway"
        
        return ElementFactory.create(gateway_type, x, y, name)
    
    @staticmethod
    def create_container(
        x: int,
        y: int,
        name: str = "Container",
        members: Optional[List[str]] = None
    ) -> VPBElement:
        """Create a Container element."""
        return ElementFactory.create(
            'Container',
            x, y,
            name,
            members=members or []
        )


__all__ = ['VPBElement', 'ElementFactory', 'ELEMENT_TYPES']
