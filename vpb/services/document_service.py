"""
Document Service
================

Service for managing VPB documents (load, save, create, recent files).

This service provides high-level document operations using the DocumentModel:
- Loading documents from JSON files
- Saving documents to JSON files
- Creating new documents with defaults
- Managing recent files list
- Auto-save functionality
- File validation

Example:
    ```python
    from vpb.services.document_service import DocumentService
    from pathlib import Path
    
    service = DocumentService()
    
    # Create new document
    doc = service.create_new_document(title="My Process")
    
    # Save document
    service.save_document(doc, Path("process.vpb.json"))
    
    # Load document
    loaded_doc = service.load_document(Path("process.vpb.json"))
    
    # Get recent files
    recent = service.get_recent_files()
    ```
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import shutil

from vpb.models.document import DocumentModel, DocumentMetadata
from vpb.infrastructure.event_bus import get_global_event_bus

logger = logging.getLogger(__name__)


class DocumentServiceError(Exception):
    """Base exception for DocumentService errors."""
    pass


class DocumentLoadError(DocumentServiceError):
    """Error loading a document."""
    pass


class DocumentSaveError(DocumentServiceError):
    """Error saving a document."""
    pass


class DocumentService:
    """
    Service for document operations.
    
    This service handles all file I/O for VPB documents, including:
    - Loading and saving documents
    - Creating new documents
    - Managing recent files
    - Auto-save and backup
    - File validation
    
    Attributes:
        max_recent_files: Maximum number of recent files to track (default: 10)
        auto_backup: Whether to create backup before saving (default: True)
        event_bus: Event bus for publishing document events
    """
    
    def __init__(
        self,
        max_recent_files: int = 10,
        auto_backup: bool = True,
        recent_files_path: Optional[Path] = None
    ):
        """
        Initialize DocumentService.
        
        Args:
            max_recent_files: Maximum number of recent files to track
            auto_backup: Whether to create backups before saving
            recent_files_path: Path to recent files JSON (default: ./recent_files.json)
        """
        self.max_recent_files = max_recent_files
        self.auto_backup = auto_backup
        self.recent_files_path = recent_files_path or Path("recent_files.json")
        self.event_bus = get_global_event_bus()
        
        logger.info(
            f"DocumentService initialized (max_recent={max_recent_files}, "
            f"auto_backup={auto_backup})"
        )
    
    def create_new_document(
        self,
        title: str = "Untitled Process",
        author: str = "",
        description: str = "",
        tags: Optional[List[str]] = None
    ) -> DocumentModel:
        """
        Create a new empty document with metadata.
        
        Args:
            title: Document title
            author: Document author
            description: Document description
            tags: List of tags
        
        Returns:
            New DocumentModel instance
        
        Example:
            ```python
            doc = service.create_new_document(
                title="Antragsbearbeitung",
                author="Max Mustermann",
                tags=["verwaltung", "digital"]
            )
            ```
        """
        metadata = DocumentMetadata(
            title=title,
            author=author,
            description=description,
            tags=tags or []
        )
        
        doc = DocumentModel()
        doc.metadata = metadata
        doc.set_modified(False)  # New document is not modified yet
        
        logger.info(f"Created new document: {title}")
        self.event_bus.publish("document.created", {"title": title})
        
        return doc
    
    def load_document(self, file_path: Union[str, Path]) -> DocumentModel:
        """
        Load a document from a JSON file.
        
        Args:
            file_path: Path to the VPB document file (string or Path)
        
        Returns:
            Loaded DocumentModel
        
        Raises:
            DocumentLoadError: If file cannot be loaded or parsed
        
        Example:
            ```python
            doc = service.load_document("process.vpb.json")
            doc = service.load_document(Path("process.vpb.json"))
            print(f"Loaded: {doc.metadata.title}")
            ```
        """
        # Convert string to Path if needed
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        if not file_path.exists():
            raise DocumentLoadError(f"File not found: {file_path}")
        
        try:
            logger.info(f"Loading document from: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Deserialize document
            doc = DocumentModel.from_dict(data)
            doc.current_file_path = file_path
            doc.set_modified(False)  # Just loaded, not modified
            
            # Add to recent files
            self._add_to_recent_files(file_path)
            
            logger.info(
                f"Successfully loaded document: {doc.metadata.title} "
                f"({doc.get_element_count()} elements, "
                f"{doc.get_connection_count()} connections)"
            )
            
            self.event_bus.publish("document.loaded", {
                "file_path": str(file_path),
                "title": doc.metadata.title
            })
            
            return doc
            
        except json.JSONDecodeError as e:
            raise DocumentLoadError(f"Invalid JSON in file {file_path}: {e}")
        except Exception as e:
            raise DocumentLoadError(f"Error loading document from {file_path}: {e}")
    
    def save_document(
        self,
        doc: DocumentModel,
        file_path: Union[str, Path],
        create_backup: Optional[bool] = None
    ) -> None:
        """
        Save a document to a JSON file.
        
        Args:
            doc: DocumentModel to save
            file_path: Path where to save the document (string or Path)
            create_backup: Override auto_backup setting for this save
        
        Raises:
            DocumentSaveError: If document cannot be saved
        
        Example:
            ```python
            service.save_document(doc, "process.vpb.json")
            service.save_document(doc, Path("process.vpb.json"))
            ```
        """
        # Convert string to Path if needed
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        try:
            # Determine if backup should be created
            do_backup = create_backup if create_backup is not None else self.auto_backup
            
            # Create backup if file exists and backup is enabled
            if do_backup and file_path.exists():
                self._create_backup(file_path)
            
            # Update metadata
            doc.metadata.touch()  # Update modification timestamp
            
            # Serialize document
            data = doc.to_dict()
            
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to temp file first (atomic write)
            temp_path = file_path.with_suffix(file_path.suffix + '.tmp')
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Move temp file to target (atomic on most systems)
            temp_path.replace(file_path)
            
            # Update document state
            doc.current_file_path = file_path
            doc.set_modified(False)
            
            # Add to recent files
            self._add_to_recent_files(file_path)
            
            logger.info(f"Successfully saved document to: {file_path}")
            
            self.event_bus.publish("document.saved", {
                "file_path": str(file_path),
                "title": doc.metadata.title
            })
            
        except Exception as e:
            raise DocumentSaveError(f"Error saving document to {file_path}: {e}")
    
    def _create_backup(self, file_path: Path) -> Path:
        """
        Create a backup of the file before overwriting.
        
        Args:
            file_path: Path to file to backup
        
        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(f".{timestamp}.backup{file_path.suffix}")
        
        try:
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")
            # Don't fail the save operation if backup fails
            return file_path
    
    def validate_file(self, file_path: Path) -> tuple[bool, List[str]]:
        """
        Validate a VPB document file without fully loading it.
        
        Args:
            file_path: Path to file to validate
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        
        Example:
            ```python
            is_valid, errors = service.validate_file(Path("process.vpb.json"))
            if not is_valid:
                for error in errors:
                    print(f"Error: {error}")
            ```
        """
        errors = []
        
        # Check file exists
        if not file_path.exists():
            errors.append(f"File not found: {file_path}")
            return False, errors
        
        # Check file is readable
        if not file_path.is_file():
            errors.append(f"Not a file: {file_path}")
            return False, errors
        
        try:
            # Try to parse JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check required top-level keys
            required_keys = ['metadata', 'elements', 'connections']
            for key in required_keys:
                if key not in data:
                    errors.append(f"Missing required key: {key}")
            
            # Try to deserialize (validates structure)
            if not errors:
                doc = DocumentModel.from_dict(data)
                
                # Validate document consistency
                validation_errors = doc.validate()
                errors.extend(validation_errors)
            
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {e}")
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def get_recent_files(self) -> List[Path]:
        """
        Get list of recently opened files.
        
        Returns:
            List of Path objects for recent files (newest first)
        
        Example:
            ```python
            recent = service.get_recent_files()
            for path in recent:
                print(f"Recent: {path}")
            ```
        """
        if not self.recent_files_path.exists():
            return []
        
        try:
            with open(self.recent_files_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            paths = [Path(p) for p in data.get('recent_files', [])]
            
            # Filter out non-existent files
            existing_paths = [p for p in paths if p.exists()]
            
            # Update if some files were removed
            if len(existing_paths) != len(paths):
                self._save_recent_files(existing_paths)
            
            return existing_paths
            
        except Exception as e:
            logger.warning(f"Error loading recent files: {e}")
            return []
    
    def _add_to_recent_files(self, file_path: Path) -> None:
        """
        Add a file to the recent files list.
        
        Args:
            file_path: Path to add to recent files
        """
        recent = self.get_recent_files()
        
        # Remove if already in list (will be added to front)
        if file_path in recent:
            recent.remove(file_path)
        
        # Add to front
        recent.insert(0, file_path)
        
        # Limit to max_recent_files
        recent = recent[:self.max_recent_files]
        
        self._save_recent_files(recent)
    
    def _save_recent_files(self, paths: List[Path]) -> None:
        """
        Save recent files list to disk.
        
        Args:
            paths: List of paths to save
        """
        try:
            data = {
                'recent_files': [str(p) for p in paths],
                'updated': datetime.now().isoformat()
            }
            
            with open(self.recent_files_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Error saving recent files: {e}")
    
    def clear_recent_files(self) -> None:
        """
        Clear the recent files list.
        
        Example:
            ```python
            service.clear_recent_files()
            ```
        """
        try:
            if self.recent_files_path.exists():
                self.recent_files_path.unlink()
            logger.info("Cleared recent files")
        except Exception as e:
            logger.warning(f"Error clearing recent files: {e}")
    
    def export_document(
        self,
        doc: DocumentModel,
        output_path: Path,
        format: str = 'json'
    ) -> None:
        """
        Export document to various formats.
        
        Args:
            doc: DocumentModel to export
            output_path: Where to save the export
            format: Export format ('json', 'json-compact')
        
        Raises:
            DocumentSaveError: If export fails
        
        Example:
            ```python
            # Export as compact JSON (no indentation)
            service.export_document(doc, Path("export.json"), format='json-compact')
            ```
        """
        try:
            data = doc.to_dict()
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format == 'json':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            elif format == 'json-compact':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False)
            else:
                raise DocumentSaveError(f"Unknown export format: {format}")
            
            logger.info(f"Exported document to {output_path} (format: {format})")
            
        except Exception as e:
            raise DocumentSaveError(f"Error exporting document: {e}")
    
    def get_document_info(self, file_path: Path) -> Dict[str, Any]:
        """
        Get basic information about a document without fully loading it.
        
        Args:
            file_path: Path to document file
        
        Returns:
            Dictionary with document info (title, author, element_count, etc.)
        
        Example:
            ```python
            info = service.get_document_info(Path("process.vpb.json"))
            print(f"Title: {info['title']}")
            print(f"Elements: {info['element_count']}")
            ```
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            metadata = data.get('metadata', {})
            
            return {
                'title': metadata.get('title', 'Unknown'),
                'author': metadata.get('author', ''),
                'description': metadata.get('description', ''),
                'version': metadata.get('version', '1.0'),
                'created': metadata.get('created', ''),
                'modified': metadata.get('modified', ''),
                'tags': metadata.get('tags', []),
                'element_count': len(data.get('elements', [])),
                'connection_count': len(data.get('connections', [])),
                'file_size': file_path.stat().st_size,
                'file_modified': datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ).isoformat()
            }
            
        except Exception as e:
            logger.warning(f"Error getting document info: {e}")
            return {
                'title': 'Error',
                'error': str(e)
            }
    
    def __repr__(self) -> str:
        """String representation of DocumentService."""
        return (
            f"DocumentService(max_recent={self.max_recent_files}, "
            f"auto_backup={self.auto_backup})"
        )
