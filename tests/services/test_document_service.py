"""Unit tests for DocumentService"""

import pytest
import json
from pathlib import Path
from datetime import datetime

from vpb.services.document_service import (
    DocumentService,
    DocumentServiceError,
    DocumentLoadError,
    DocumentSaveError
)
from vpb.models import DocumentModel, ElementFactory, ConnectionFactory


@pytest.fixture
def service(tmp_path):
    """Create DocumentService with temp directory."""
    recent_files = tmp_path / "recent.json"
    return DocumentService(
        max_recent_files=5,
        auto_backup=True,
        recent_files_path=recent_files
    )


@pytest.fixture
def sample_document():
    """Create a sample document with elements and connections."""
    doc = DocumentModel()
    doc.metadata.title = "Test Process"
    doc.metadata.author = "Test Author"
    doc.metadata.tags = ["test", "sample"]
    
    # Add elements (use create() method with explicit element_id)
    e1 = ElementFactory.create('Prozess', 100, 100, element_id='e1', name='Process 1')
    e2 = ElementFactory.create('Prozess', 300, 300, element_id='e2', name='Process 2')
    doc.add_element(e1)
    doc.add_element(e2)
    
    # Add connection
    conn = ConnectionFactory.create('e1', 'e2')
    doc.add_connection(conn)
    
    return doc


class TestDocumentServiceInit:
    """Tests for DocumentService initialization."""
    
    def test_init_defaults(self, tmp_path):
        """Test default initialization."""
        service = DocumentService()
        
        assert service.max_recent_files == 10
        assert service.auto_backup is True
        assert service.event_bus is not None
    
    def test_init_custom_params(self, tmp_path):
        """Test initialization with custom parameters."""
        recent_path = tmp_path / "custom_recent.json"
        service = DocumentService(
            max_recent_files=20,
            auto_backup=False,
            recent_files_path=recent_path
        )
        
        assert service.max_recent_files == 20
        assert service.auto_backup is False
        assert service.recent_files_path == recent_path
    
    def test_repr(self, service):
        """Test string representation."""
        repr_str = repr(service)
        
        assert "DocumentService" in repr_str
        assert "max_recent=5" in repr_str
        assert "auto_backup=True" in repr_str


class TestCreateNewDocument:
    """Tests for creating new documents."""
    
    def test_create_default_document(self, service):
        """Test creating document with defaults."""
        doc = service.create_new_document()
        
        assert doc.metadata.title == "Untitled Process"
        assert doc.metadata.author == ""
        assert doc.metadata.description == ""
        assert doc.metadata.tags == []
        assert doc.is_empty() is True
        assert doc.is_modified() is False
    
    def test_create_document_with_metadata(self, service):
        """Test creating document with custom metadata."""
        doc = service.create_new_document(
            title="My Process",
            author="John Doe",
            description="Test description",
            tags=["test", "demo"]
        )
        
        assert doc.metadata.title == "My Process"
        assert doc.metadata.author == "John Doe"
        assert doc.metadata.description == "Test description"
        assert doc.metadata.tags == ["test", "demo"]
        assert doc.is_modified() is False
    
    def test_create_publishes_event(self, service):
        """Test that creating document publishes event."""
        events = []
        
        def track_event(data):  # Event-Bus callbacks only get data parameter
            events.append(data)
        
        service.event_bus.subscribe("document.created", track_event)
        
        doc = service.create_new_document(title="Test")
        
        assert len(events) == 1
        assert events[0]["title"] == "Test"


class TestSaveDocument:
    """Tests for saving documents."""
    
    def test_save_new_document(self, service, sample_document, tmp_path):
        """Test saving a document to a new file."""
        file_path = tmp_path / "test_process.vpb.json"
        
        service.save_document(sample_document, file_path)
        
        assert file_path.exists()
        assert sample_document.current_file_path == file_path
        assert sample_document.is_modified() is False
    
    def test_save_document_content(self, service, sample_document, tmp_path):
        """Test that saved document has correct content."""
        file_path = tmp_path / "test_process.vpb.json"
        
        service.save_document(sample_document, file_path)
        
        # Read and verify content
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data['metadata']['title'] == "Test Process"
        assert data['metadata']['author'] == "Test Author"
        assert len(data['elements']) == 2
        assert len(data['connections']) == 1
    
    def test_save_creates_parent_directory(self, service, sample_document, tmp_path):
        """Test that save creates parent directories."""
        file_path = tmp_path / "subdir" / "nested" / "test.vpb.json"
        
        service.save_document(sample_document, file_path)
        
        assert file_path.exists()
        assert file_path.parent.exists()
    
    def test_save_creates_backup(self, service, sample_document, tmp_path):
        """Test that save creates backup of existing file."""
        file_path = tmp_path / "test.vpb.json"
        
        # Save first time
        service.save_document(sample_document, file_path)
        
        # Wait a bit to ensure different timestamp in backup filename
        import time
        time.sleep(1.1)  # Wait more than 1 second for different timestamp
        
        # Modify document
        sample_document.metadata.title = "Modified"
        sample_document.set_modified(True)
        
        # Save again (should create backup)
        service.save_document(sample_document, file_path)
        
        # Check for backup file
        all_files = list(tmp_path.iterdir())
        backup_files = [f for f in all_files if 'backup' in f.name]
        
        assert len(backup_files) >= 1, f"No backup found. Files: {[f.name for f in all_files]}"
    
    def test_save_without_backup(self, service, sample_document, tmp_path):
        """Test saving without creating backup."""
        file_path = tmp_path / "test.vpb.json"
        
        # Save first time
        service.save_document(sample_document, file_path)
        
        # Save again with backup disabled
        service.save_document(sample_document, file_path, create_backup=False)
        
        # No backup should exist
        backup_files = list(tmp_path.glob("test.*.backup.vpb.json"))
        assert len(backup_files) == 0
    
    def test_save_updates_modified_timestamp(self, service, sample_document, tmp_path):
        """Test that save updates modification timestamp."""
        file_path = tmp_path / "test.vpb.json"
        
        original_modified = sample_document.metadata.modified
        
        import time
        time.sleep(0.01)
        
        service.save_document(sample_document, file_path)
        
        assert sample_document.metadata.modified != original_modified
    
    def test_save_publishes_event(self, service, sample_document, tmp_path):
        """Test that saving publishes event."""
        events = []
        
        def track_event(data):  # Event-Bus callbacks only get data parameter
            events.append(data)
        
        service.event_bus.subscribe("document.saved", track_event)
        
        file_path = tmp_path / "test.vpb.json"
        service.save_document(sample_document, file_path)
        
        assert len(events) == 1
        assert "test.vpb.json" in events[0]["file_path"]


class TestLoadDocument:
    """Tests for loading documents."""
    
    def test_load_document(self, service, sample_document, tmp_path):
        """Test loading a document."""
        file_path = tmp_path / "test.vpb.json"
        service.save_document(sample_document, file_path)
        
        loaded_doc = service.load_document(file_path)
        
        assert loaded_doc.metadata.title == sample_document.metadata.title
        assert loaded_doc.get_element_count() == sample_document.get_element_count()
        assert loaded_doc.get_connection_count() == sample_document.get_connection_count()
        assert loaded_doc.is_modified() is False
    
    def test_load_nonexistent_file(self, service, tmp_path):
        """Test loading non-existent file raises error."""
        file_path = tmp_path / "nonexistent.vpb.json"
        
        with pytest.raises(DocumentLoadError, match="File not found"):
            service.load_document(file_path)
    
    def test_load_invalid_json(self, service, tmp_path):
        """Test loading invalid JSON raises error."""
        file_path = tmp_path / "invalid.vpb.json"
        
        with open(file_path, 'w') as f:
            f.write("{ invalid json }")
        
        with pytest.raises(DocumentLoadError, match="Invalid JSON"):
            service.load_document(file_path)
    
    def test_load_sets_current_file_path(self, service, sample_document, tmp_path):
        """Test that load sets current_file_path."""
        file_path = tmp_path / "test.vpb.json"
        service.save_document(sample_document, file_path)
        
        loaded_doc = service.load_document(file_path)
        
        assert loaded_doc.current_file_path == file_path
    
    def test_load_publishes_event(self, service, sample_document, tmp_path):
        """Test that loading publishes event."""
        events = []
        
        def track_event(data):  # Event-Bus callbacks only get data parameter
            events.append(data)
        
        service.event_bus.subscribe("document.loaded", track_event)
        
        file_path = tmp_path / "test.vpb.json"
        service.save_document(sample_document, file_path)
        service.load_document(file_path)
        
        assert len(events) == 1
        # Note: save also publishes event, but we only subscribed after that


class TestValidateFile:
    """Tests for file validation."""
    
    def test_validate_valid_file(self, service, sample_document, tmp_path):
        """Test validating a valid file."""
        file_path = tmp_path / "test.vpb.json"
        service.save_document(sample_document, file_path)
        
        is_valid, errors = service.validate_file(file_path)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_nonexistent_file(self, service, tmp_path):
        """Test validating non-existent file."""
        file_path = tmp_path / "nonexistent.vpb.json"
        
        is_valid, errors = service.validate_file(file_path)
        
        assert is_valid is False
        assert "File not found" in errors[0]
    
    def test_validate_invalid_json(self, service, tmp_path):
        """Test validating invalid JSON."""
        file_path = tmp_path / "invalid.vpb.json"
        
        with open(file_path, 'w') as f:
            f.write("{ invalid }")
        
        is_valid, errors = service.validate_file(file_path)
        
        assert is_valid is False
        assert any("Invalid JSON" in e for e in errors)
    
    def test_validate_missing_required_keys(self, service, tmp_path):
        """Test validating file with missing required keys."""
        file_path = tmp_path / "incomplete.vpb.json"
        
        with open(file_path, 'w') as f:
            json.dump({'metadata': {}}, f)  # Missing 'elements' and 'connections'
        
        is_valid, errors = service.validate_file(file_path)
        
        assert is_valid is False
        assert any("Missing required key" in e for e in errors)


class TestRecentFiles:
    """Tests for recent files management."""
    
    def test_get_recent_files_empty(self, service):
        """Test getting recent files when none exist."""
        recent = service.get_recent_files()
        
        assert recent == []
    
    def test_add_to_recent_files(self, service, sample_document, tmp_path):
        """Test adding files to recent list."""
        file1 = tmp_path / "file1.vpb.json"
        file2 = tmp_path / "file2.vpb.json"
        
        service.save_document(sample_document, file1)
        service.save_document(sample_document, file2)
        
        recent = service.get_recent_files()
        
        assert len(recent) == 2
        assert recent[0] == file2  # Most recent first
        assert recent[1] == file1
    
    def test_recent_files_max_limit(self, service, sample_document, tmp_path):
        """Test that recent files respects max limit."""
        # Service has max_recent_files=5
        for i in range(10):
            file_path = tmp_path / f"file{i}.vpb.json"
            service.save_document(sample_document, file_path)
        
        recent = service.get_recent_files()
        
        assert len(recent) <= service.max_recent_files
    
    def test_recent_files_no_duplicates(self, service, sample_document, tmp_path):
        """Test that saving same file doesn't create duplicates."""
        file_path = tmp_path / "test.vpb.json"
        
        service.save_document(sample_document, file_path)
        service.save_document(sample_document, file_path)
        service.save_document(sample_document, file_path)
        
        recent = service.get_recent_files()
        
        assert len(recent) == 1
        assert recent[0] == file_path
    
    def test_clear_recent_files(self, service, sample_document, tmp_path):
        """Test clearing recent files."""
        file_path = tmp_path / "test.vpb.json"
        service.save_document(sample_document, file_path)
        
        assert len(service.get_recent_files()) == 1
        
        service.clear_recent_files()
        
        assert len(service.get_recent_files()) == 0


class TestExportDocument:
    """Tests for document export."""
    
    def test_export_json(self, service, sample_document, tmp_path):
        """Test exporting as JSON."""
        output_path = tmp_path / "export.json"
        
        service.export_document(sample_document, output_path, format='json')
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data['metadata']['title'] == "Test Process"
    
    def test_export_json_compact(self, service, sample_document, tmp_path):
        """Test exporting as compact JSON."""
        output_path = tmp_path / "export_compact.json"
        
        service.export_document(sample_document, output_path, format='json-compact')
        
        assert output_path.exists()
        
        # Compact should be smaller (no indentation)
        with open(output_path, 'r') as f:
            content = f.read()
        
        assert '\n  ' not in content  # No indentation
    
    def test_export_unknown_format(self, service, sample_document, tmp_path):
        """Test exporting with unknown format raises error."""
        output_path = tmp_path / "export.unknown"
        
        with pytest.raises(DocumentSaveError, match="Unknown export format"):
            service.export_document(sample_document, output_path, format='unknown')


class TestGetDocumentInfo:
    """Tests for getting document info."""
    
    def test_get_document_info(self, service, sample_document, tmp_path):
        """Test getting document info."""
        file_path = tmp_path / "test.vpb.json"
        service.save_document(sample_document, file_path)
        
        info = service.get_document_info(file_path)
        
        assert info['title'] == "Test Process"
        assert info['author'] == "Test Author"
        assert info['element_count'] == 2
        assert info['connection_count'] == 1
        assert info['file_size'] > 0
        assert 'tags' in info
    
    def test_get_info_nonexistent_file(self, service, tmp_path):
        """Test getting info for non-existent file."""
        file_path = tmp_path / "nonexistent.vpb.json"
        
        info = service.get_document_info(file_path)
        
        assert 'error' in info


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
