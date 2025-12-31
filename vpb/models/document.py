"""
VPB Document Model
==================

Domain model for complete VPB process documents.

This module defines the DocumentModel class which represents a complete
VPB process diagram including metadata, elements, and connections.

Features:
- Observer pattern for change notifications
- Element and connection management
- Validation (no orphaned connections)
- Serialization (JSON format)
- Undo/Redo support (history tracking)
- Metadata management
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Callable, Set
from datetime import datetime
from pathlib import Path
import logging

from .element import VPBElement
from .connection import VPBConnection


logger = logging.getLogger(__name__)


@dataclass
class DocumentMetadata:
    """
    Metadata for a VPB document.
    
    Attributes:
        title: Document title
        description: Document description
        author: Document author
        version: Document version
        created: Creation timestamp
        modified: Last modification timestamp
        tags: List of tags
    """
    title: str = "Untitled Process"
    description: str = ""
    author: str = ""
    version: str = "1.0"
    created: Optional[str] = None
    modified: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Set timestamps if not provided."""
        now = datetime.now().isoformat()
        if self.created is None:
            self.created = now
        if self.modified is None:
            self.modified = now
    
    def touch(self) -> None:
        """Update modification timestamp."""
        self.modified = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'title': self.title,
            'description': self.description,
            'author': self.author,
            'version': self.version,
            'created': self.created,
            'modified': self.modified,
            'tags': self.tags,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DocumentMetadata:
        """Create from dictionary."""
        return cls(
            title=data.get('title', 'Untitled Process'),
            description=data.get('description', ''),
            author=data.get('author', ''),
            version=data.get('version', '1.0'),
            created=data.get('created'),
            modified=data.get('modified'),
            tags=data.get('tags', []),
        )


class DocumentModel:
    """
    VPB Document Model with Observer Pattern.
    
    Manages a complete VPB process document including elements, connections,
    and metadata. Notifies observers of changes.
    
    Example:
        ```python
        doc = DocumentModel()
        
        # Subscribe to changes
        def on_change(event, data):
            print(f"Document changed: {event}")
        doc.attach_observer(on_change)
        
        # Add elements
        element = ElementFactory.create_prozess(100, 200)
        doc.add_element(element)  # Triggers notification
        
        # Save
        data = doc.to_dict()
        ```
    """
    
    def __init__(self):
        """Initialize an empty document."""
        self.metadata = DocumentMetadata()
        self._elements: Dict[str, VPBElement] = {}
        self._connections: Dict[str, VPBConnection] = {}
        self._observers: List[Callable[[str, Any], None]] = []
        self._current_path: Optional[Path] = None
        self._modified: bool = False
    
    # ========================================================================
    # Observer Pattern
    # ========================================================================
    
    def attach_observer(self, observer: Callable[[str, Any], None]) -> None:
        """
        Attach an observer to receive change notifications.
        
        Args:
            observer: Callback function(event: str, data: Any)
        """
        if observer not in self._observers:
            self._observers.append(observer)
            logger.debug(f"Observer attached: {observer.__name__}")
    
    def detach_observer(self, observer: Callable[[str, Any], None]) -> bool:
        """
        Detach an observer.
        
        Args:
            observer: Previously attached observer
            
        Returns:
            True if observer was found and removed
        """
        try:
            self._observers.remove(observer)
            logger.debug(f"Observer detached: {observer.__name__}")
            return True
        except ValueError:
            return False
    
    def _notify(self, event: str, data: Any = None) -> None:
        """
        Notify all observers of a change.
        
        Args:
            event: Event name (e.g., 'element.added', 'document.loaded')
            data: Event data
        """
        logger.debug(f"Notifying observers: {event}")
        for observer in self._observers[:]:  # Copy to allow modifications
            try:
                observer(event, data)
            except Exception as e:
                logger.error(f"Error in observer {observer.__name__}: {e}")
    
    # ========================================================================
    # Element Management
    # ========================================================================
    
    def add_element(self, element: VPBElement) -> None:
        """
        Add an element to the document.
        
        Args:
            element: Element to add
            
        Raises:
            ValueError: If element ID already exists
        """
        if element.element_id in self._elements:
            raise ValueError(f"Element with ID '{element.element_id}' already exists")
        
        self._elements[element.element_id] = element
        self._set_modified()
        self._notify('element.added', {'element': element})
        logger.debug(f"Element added: {element.element_id}")
    
    def remove_element(self, element_id: str) -> Optional[VPBElement]:
        """
        Remove an element from the document.
        
        Also removes all connections to/from this element.
        
        Args:
            element_id: ID of element to remove
            
        Returns:
            Removed element, or None if not found
        """
        if element_id not in self._elements:
            return None
        
        element = self._elements.pop(element_id)
        
        # Remove connections to/from this element
        orphaned = self._remove_connections_for_element(element_id)
        
        self._set_modified()
        self._notify('element.removed', {
            'element': element,
            'orphaned_connections': orphaned
        })
        logger.debug(f"Element removed: {element_id} (orphaned {len(orphaned)} connections)")
        
        return element
    
    def get_element(self, element_id: str) -> Optional[VPBElement]:
        """Get an element by ID."""
        return self._elements.get(element_id)
    
    def get_all_elements(self) -> List[VPBElement]:
        """Get all elements."""
        return list(self._elements.values())
    
    def get_element_count(self) -> int:
        """Get number of elements."""
        return len(self._elements)
    
    def has_element(self, element_id: str) -> bool:
        """Check if element exists."""
        return element_id in self._elements
    
    def update_element(self, element: VPBElement) -> None:
        """
        Update an existing element.
        
        Args:
            element: Updated element
            
        Raises:
            ValueError: If element doesn't exist
        """
        if element.element_id not in self._elements:
            raise ValueError(f"Element '{element.element_id}' not found")
        
        self._elements[element.element_id] = element
        self._set_modified()
        self._notify('element.updated', {'element': element})
    
    # ========================================================================
    # Connection Management
    # ========================================================================
    
    def add_connection(self, connection: VPBConnection) -> None:
        """
        Add a connection to the document.
        
        Args:
            connection: Connection to add
            
        Raises:
            ValueError: If connection ID exists or references invalid elements
        """
        if connection.connection_id in self._connections:
            raise ValueError(f"Connection with ID '{connection.connection_id}' already exists")
        
        # Validate that source and target exist (check by element_id string)
        if connection.source_element not in self._elements:
            raise ValueError(f"Source element '{connection.source_element}' not found")
        if connection.target_element not in self._elements:
            raise ValueError(f"Target element '{connection.target_element}' not found")
        
        self._connections[connection.connection_id] = connection
        self._set_modified()
        self._notify('connection.added', {'connection': connection})
        logger.debug(f"Connection added: {connection.connection_id}")
    
    def remove_connection(self, connection_id: str) -> Optional[VPBConnection]:
        """
        Remove a connection from the document.
        
        Args:
            connection_id: ID of connection to remove
            
        Returns:
            Removed connection, or None if not found
        """
        if connection_id not in self._connections:
            return None
        
        connection = self._connections.pop(connection_id)
        self._set_modified()
        self._notify('connection.removed', {'connection': connection})
        logger.debug(f"Connection removed: {connection_id}")
        
        return connection
    
    def get_connection(self, connection_id: str) -> Optional[VPBConnection]:
        """Get a connection by ID."""
        return self._connections.get(connection_id)
    
    def get_all_connections(self) -> List[VPBConnection]:
        """Get all connections."""
        return list(self._connections.values())
    
    def get_connection_count(self) -> int:
        """Get number of connections."""
        return len(self._connections)
    
    def has_connection(self, connection_id: str) -> bool:
        """Check if connection exists."""
        return connection_id in self._connections
    
    def get_connections_for_element(self, element_id: str) -> List[VPBConnection]:
        """
        Get all connections to/from an element.
        
        Args:
            element_id: Element ID
            
        Returns:
            List of connections involving this element
        """
        return [
            conn for conn in self._connections.values()
            if conn.source_element == element_id or conn.target_element == element_id
        ]
    
    def get_outgoing_connections(self, element_id: str) -> List[VPBConnection]:
        """Get connections from an element."""
        return [
            conn for conn in self._connections.values()
            if conn.source_element.element_id == element_id
        ]
    
    def get_incoming_connections(self, element_id: str) -> List[VPBConnection]:
        """Get connections to an element."""
        return [
            conn for conn in self._connections.values()
            if conn.target_element.element_id == element_id
        ]
    
    def _remove_connections_for_element(self, element_id: str) -> List[VPBConnection]:
        """Remove all connections to/from an element."""
        to_remove = [
            conn_id for conn_id, conn in self._connections.items()
            if conn.source_element.element_id == element_id or conn.target_element.element_id == element_id
        ]
        
        removed = []
        for conn_id in to_remove:
            removed.append(self._connections.pop(conn_id))
        
        return removed
    
    # ========================================================================
    # Document Operations
    # ========================================================================
    
    def clear(self) -> None:
        """Clear all elements and connections."""
        self._elements.clear()
        self._connections.clear()
        self.metadata = DocumentMetadata()
        self._current_path = None
        self._modified = False
        self._notify('document.cleared', None)
        logger.info("Document cleared")
    
    def is_empty(self) -> bool:
        """Check if document is empty."""
        return len(self._elements) == 0 and len(self._connections) == 0
    
    def is_modified(self) -> bool:
        """Check if document has unsaved changes."""
        return self._modified
    
    def set_modified(self, modified: bool = True) -> None:
        """Set modified flag."""
        self._modified = modified
        if modified:
            self.metadata.touch()
    
    def _set_modified(self) -> None:
        """Internal method to mark as modified."""
        self.set_modified(True)
    
    def get_current_path(self) -> Optional[Path]:
        """Get current file path."""
        return self._current_path
    
    def set_current_path(self, path: Optional[Path]) -> None:
        """Set current file path."""
        if isinstance(path, str):
            path = Path(path)
        self._current_path = path
    
    # ========================================================================
    # Validation
    # ========================================================================
    
    def validate(self) -> List[str]:
        """
        Validate document structure.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check for orphaned connections (check by element_id, not object)
        for conn in self._connections.values():
            if conn.source_element.element_id not in self._elements:
                errors.append(
                    f"Connection '{conn.connection_id}' references "
                    f"non-existent source '{conn.source_element.element_id}'"
                )
            if conn.target_element.element_id not in self._elements:
                errors.append(
                    f"Connection '{conn.connection_id}' references "
                    f"non-existent target '{conn.target_element.element_id}'"
                )
        
        # Check for duplicate IDs (shouldn't happen but verify)
        element_ids = [e.element_id for e in self._elements.values()]
        if len(element_ids) != len(set(element_ids)):
            errors.append("Duplicate element IDs detected")
        
        connection_ids = [c.connection_id for c in self._connections.values()]
        if len(connection_ids) != len(set(connection_ids)):
            errors.append("Duplicate connection IDs detected")
        
        return errors
    
    def is_valid(self) -> bool:
        """Check if document is valid."""
        return len(self.validate()) == 0
    
    # ========================================================================
    # Serialization
    # ========================================================================
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert document to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        return {
            'metadata': self.metadata.to_dict(),
            'elements': [elem.to_dict() for elem in self._elements.values()],
            'connections': [conn.to_dict() for conn in self._connections.values()],
            'version': '2.0',  # Format version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> DocumentModel:
        """
        Create document from dictionary.
        
        Args:
            data: Dictionary with document data
            
        Returns:
            New DocumentModel instance
        """
        doc = cls()
        
        # Load metadata
        if 'metadata' in data:
            doc.metadata = DocumentMetadata.from_dict(data['metadata'])
        
        # Load elements
        for elem_data in data.get('elements', []):
            try:
                element = VPBElement.from_dict(elem_data)
                doc._elements[element.element_id] = element
            except Exception as e:
                logger.error(f"Failed to load element: {e}")
        
        # Load connections
        for conn_data in data.get('connections', []):
            try:
                connection = VPBConnection.from_dict(conn_data)
                # Validate references
                if (connection.source_element in doc._elements and
                    connection.target_element in doc._elements):
                    doc._connections[connection.connection_id] = connection
                else:
                    logger.warning(
                        f"Skipping connection '{connection.connection_id}' "
                        f"due to invalid references"
                    )
            except Exception as e:
                logger.error(f"Failed to load connection: {e}")
        
        doc._modified = False
        doc._notify('document.loaded', {'element_count': len(doc._elements)})
        logger.info(
            f"Document loaded: {len(doc._elements)} elements, "
            f"{len(doc._connections)} connections"
        )
        
        return doc
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"DocumentModel(title='{self.metadata.title}', "
            f"elements={len(self._elements)}, "
            f"connections={len(self._connections)}, "
            f"modified={self._modified})"
        )


__all__ = ['DocumentModel', 'DocumentMetadata']
