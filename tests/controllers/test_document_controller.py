"""
Tests für DocumentController.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path

from vpb.controllers.document_controller import DocumentController
from vpb.infrastructure.event_bus import EventBus
from vpb.services.document_service import DocumentService
from vpb.models import DocumentModel


# ===== Fixtures =====

@pytest.fixture
def mock_event_bus():
    """Mock Event-Bus."""
    return Mock(spec=EventBus)


@pytest.fixture
def mock_document_service():
    """Mock DocumentService."""
    service = Mock(spec=DocumentService)
    
    # Default return values
    doc = DocumentModel()
    doc.metadata.title = "Neues Dokument"
    service.create_new_document.return_value = doc
    
    return service


@pytest.fixture
def document_controller(mock_event_bus, mock_document_service):
    """DocumentController mit Mocks."""
    return DocumentController(
        event_bus=mock_event_bus,
        document_service=mock_document_service
    )


@pytest.fixture
def sample_document():
    """Sample DocumentModel."""
    doc = DocumentModel()
    doc.metadata.title = "Test Dokument"
    return doc


# ===== Test Initialization =====

class TestDocumentControllerInit:
    """Tests für DocumentController Initialisierung."""
    
    def test_init_creates_controller(self, mock_event_bus, mock_document_service):
        """Initialisierung erstellt Controller."""
        controller = DocumentController(mock_event_bus, mock_document_service)
        
        assert controller.event_bus is mock_event_bus
        assert controller.document_service is mock_document_service
        assert controller.current_document is None
        assert controller.current_file_path is None
        assert controller.is_modified is False
        
    def test_init_subscribes_to_events(self, mock_event_bus, mock_document_service):
        """Initialisierung subscribed zu Events."""
        controller = DocumentController(mock_event_bus, mock_document_service)
        
        # Check subscriptions
        subscribe_calls = mock_event_bus.subscribe.call_args_list
        
        # Should subscribe to multiple events
        assert len(subscribe_calls) >= 10
        
        # Check specific subscriptions
        event_names = [call[0][0] for call in subscribe_calls]
        assert "ui:menu:file:new" in event_names
        assert "ui:menu:file:open" in event_names
        assert "ui:menu:file:save" in event_names
        assert "ui:toolbar:new" in event_names
        assert "ui:window:closing" in event_names


# ===== Test New Document =====

class TestNewDocument:
    """Tests für New Document Funktionalität."""
    
    def test_new_document_creates_document(self, document_controller, mock_document_service):
        """New Document erstellt neues Dokument."""
        document_controller._on_new_document({})
        
        # Should create new document
        mock_document_service.create_new_document.assert_called_once()
        assert document_controller.current_document is not None
        assert document_controller.is_modified is False
        
    def test_new_document_publishes_event(self, document_controller, mock_event_bus):
        """New Document publiziert Event."""
        document_controller._on_new_document({})
        
        # Should publish document:created event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "document:created"]
        assert len(publish_calls) == 1
        
    def test_new_document_clears_file_path(self, document_controller):
        """New Document löscht Dateipfad."""
        document_controller.current_file_path = "/path/to/file.vpb"
        
        document_controller._on_new_document({})
        
        assert document_controller.current_file_path is None
        
    def test_new_document_with_unsaved_changes(self, document_controller):
        """New Document mit ungespeicherten Änderungen."""
        document_controller.is_modified = True
        
        with patch.object(document_controller, '_confirm_discard_changes', return_value=False):
            document_controller._on_new_document({})
            
        # Should not create new document
        assert document_controller.is_modified is True


# ===== Test Open Document =====

class TestOpenDocument:
    """Tests für Open Document Funktionalität."""
    
    def test_open_document_with_file_path(self, document_controller, mock_document_service, sample_document):
        """Open Document mit Dateipfad."""
        mock_document_service.load_document.return_value = sample_document
        
        document_controller._on_open_document({"file_path": "/path/to/doc.vpb"})
        
        # Should load document
        mock_document_service.load_document.assert_called_once_with("/path/to/doc.vpb")
        assert document_controller.current_document is sample_document
        assert document_controller.current_file_path == "/path/to/doc.vpb"
        assert document_controller.is_modified is False
        
    def test_open_document_publishes_event(self, document_controller, mock_event_bus, mock_document_service, sample_document):
        """Open Document publiziert Event."""
        mock_document_service.load_document.return_value = sample_document
        
        document_controller._on_open_document({"file_path": "/path/to/doc.vpb"})
        
        # Should publish document:loaded event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "document:loaded"]
        assert len(publish_calls) == 1
        
    def test_open_document_without_file_path(self, document_controller, mock_event_bus):
        """Open Document ohne Dateipfad fordert Dialog an."""
        document_controller._on_open_document({})
        
        # Should request file path
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "ui:request:file_path"]
        assert len(publish_calls) == 1
        
    def test_open_document_with_error(self, document_controller, mock_event_bus, mock_document_service):
        """Open Document mit Fehler publiziert Error Event."""
        mock_document_service.load_document.side_effect = Exception("Load error")
        
        document_controller._on_open_document({"file_path": "/path/to/doc.vpb"})
        
        # Should publish error event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "ui:error"]
        assert len(publish_calls) == 1


# ===== Test Save Document =====

class TestSaveDocument:
    """Tests für Save Document Funktionalität."""
    
    def test_save_document_with_file_path(self, document_controller, mock_document_service, sample_document):
        """Save Document mit Dateipfad."""
        document_controller.current_document = sample_document
        document_controller.current_file_path = "/path/to/doc.vpb"
        document_controller.is_modified = True
        
        document_controller._on_save_document({})
        
        # Should save document
        mock_document_service.save_document.assert_called_once_with(
            sample_document,
            "/path/to/doc.vpb"
        )
        assert document_controller.is_modified is False
        
    def test_save_document_without_file_path(self, document_controller, sample_document):
        """Save Document ohne Dateipfad ruft Save As auf."""
        document_controller.current_document = sample_document
        document_controller.current_file_path = None
        
        with patch.object(document_controller, '_on_save_document_as') as mock_save_as:
            document_controller._on_save_document({})
            
            # Should call Save As
            mock_save_as.assert_called_once()
            
    def test_save_document_without_current_document(self, document_controller, mock_document_service):
        """Save Document ohne aktuelles Dokument macht nichts."""
        document_controller.current_document = None
        
        document_controller._on_save_document({})
        
        # Should not save
        mock_document_service.save_document.assert_not_called()
        
    def test_save_document_publishes_event(self, document_controller, mock_event_bus, sample_document):
        """Save Document publiziert Event."""
        document_controller.current_document = sample_document
        document_controller.current_file_path = "/path/to/doc.vpb"
        
        document_controller._on_save_document({})
        
        # Should publish document:saved event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "document:saved"]
        assert len(publish_calls) == 1


# ===== Test Save Document As =====

class TestSaveDocumentAs:
    """Tests für Save Document As Funktionalität."""
    
    def test_save_as_with_file_path(self, document_controller, mock_document_service, sample_document):
        """Save As mit Dateipfad."""
        document_controller.current_document = sample_document
        
        document_controller._on_save_document_as({"file_path": "/new/path.vpb"})
        
        # Should save document
        mock_document_service.save_document.assert_called_once_with(
            sample_document,
            "/new/path.vpb"
        )
        assert document_controller.current_file_path == "/new/path.vpb"
        assert document_controller.is_modified is False
        
    def test_save_as_without_file_path(self, document_controller, mock_event_bus, sample_document):
        """Save As ohne Dateipfad fordert Dialog an."""
        document_controller.current_document = sample_document
        
        document_controller._on_save_document_as({})
        
        # Should request file path
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "ui:request:file_path"]
        assert len(publish_calls) == 1


# ===== Test Close Document =====

class TestCloseDocument:
    """Tests für Close Document Funktionalität."""
    
    def test_close_document(self, document_controller, sample_document):
        """Close Document löscht aktuelles Dokument."""
        document_controller.current_document = sample_document
        document_controller.current_file_path = "/path/to/doc.vpb"
        
        document_controller._on_close_document({})
        
        assert document_controller.current_document is None
        assert document_controller.current_file_path is None
        assert document_controller.is_modified is False
        
    def test_close_document_publishes_event(self, document_controller, mock_event_bus, sample_document):
        """Close Document publiziert Event."""
        document_controller.current_document = sample_document
        
        document_controller._on_close_document({})
        
        # Should publish document:closed event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "document:closed"]
        assert len(publish_calls) == 1


# ===== Test Document Modified =====

class TestDocumentModified:
    """Tests für Document Modified Funktionalität."""
    
    def test_document_modified_sets_flag(self, document_controller, sample_document):
        """Document Modified setzt is_modified Flag."""
        document_controller.current_document = sample_document
        document_controller.is_modified = False
        
        document_controller._on_document_modified({})
        
        assert document_controller.is_modified is True
        
    def test_document_modified_publishes_event(self, document_controller, mock_event_bus, sample_document):
        """Document Modified publiziert Event."""
        document_controller.current_document = sample_document
        
        document_controller._on_document_modified({})
        
        # Should publish document:modified event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "document:modified"]
        assert len(publish_calls) == 1


# ===== Test Public API =====

class TestPublicAPI:
    """Tests für Public API."""
    
    def test_get_current_document(self, document_controller, sample_document):
        """get_current_document gibt aktuelles Dokument zurück."""
        document_controller.current_document = sample_document
        
        assert document_controller.get_current_document() is sample_document
        
    def test_get_current_file_path(self, document_controller):
        """get_current_file_path gibt Dateipfad zurück."""
        document_controller.current_file_path = "/path/to/doc.vpb"
        
        assert document_controller.get_current_file_path() == "/path/to/doc.vpb"
        
    def test_is_document_modified(self, document_controller):
        """is_document_modified gibt Modified-Flag zurück."""
        document_controller.is_modified = True
        
        assert document_controller.is_document_modified() is True


# ===== Test String Representation =====

class TestStringRepresentation:
    """Tests für String-Repräsentation."""
    
    def test_repr_without_document(self, document_controller):
        """__repr__ ohne Dokument."""
        result = repr(document_controller)
        
        assert "Unbenannt" in result
        
    def test_repr_with_file_path(self, document_controller, sample_document):
        """__repr__ mit Dateipfad."""
        document_controller.current_document = sample_document
        document_controller.current_file_path = "/path/to/mydoc.vpb"
        
        result = repr(document_controller)
        
        assert "mydoc.vpb" in result
        
    def test_repr_with_modified_flag(self, document_controller, sample_document):
        """__repr__ mit Modified-Flag."""
        document_controller.current_document = sample_document
        document_controller.current_file_path = "/path/to/doc.vpb"
        document_controller.is_modified = True
        
        result = repr(document_controller)
        
        assert "*" in result
