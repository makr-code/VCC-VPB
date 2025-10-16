"""
VPB Models Layer
================

Data models and business entities for VPB Process Designer.

This package contains:
- DocumentModel: Complete process document structure with metadata
- VPBElement: Individual process elements
- VPBConnection: Connections between elements
- PaletteModel: Element palette definitions
"""

from .element import VPBElement, ElementFactory, ELEMENT_TYPES
from .connection import (
    VPBConnection,
    ConnectionFactory,
    CONNECTION_TYPES,
    ARROW_STYLES,
    ROUTING_MODES,
)
from .document import DocumentModel, DocumentMetadata
from .palette import PaletteModel, PaletteCategory, PaletteItem

__all__ = [
    # Element
    'VPBElement',
    'ElementFactory',
    'ELEMENT_TYPES',
    # Connection
    'VPBConnection',
    'ConnectionFactory',
    'CONNECTION_TYPES',
    'ARROW_STYLES',
    'ROUTING_MODES',
    # Document
    'DocumentModel',
    'DocumentMetadata',
    # Palette
    'PaletteModel',
    'PaletteCategory',
    'PaletteItem',
]
