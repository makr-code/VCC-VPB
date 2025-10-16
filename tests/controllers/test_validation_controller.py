"""
Tests für ValidationController.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock

from vpb.controllers.validation_controller import ValidationController
from vpb.infrastructure.event_bus import EventBus
from vpb.models import DocumentModel, ElementFactory, ConnectionFactory


# ===== Fixtures =====

@pytest.fixture
def mock_event_bus():
    """Mock Event-Bus."""
    return Mock(spec=EventBus)


@pytest.fixture
def empty_document():
    """Leeres DocumentModel."""
    return DocumentModel()


@pytest.fixture
def valid_document():
    """Valides DocumentModel mit 2 Elements und 1 Connection."""
    doc = DocumentModel()
    elem1 = ElementFactory.create("ACTIVITY", x=100, y=100, name="Start")
    elem2 = ElementFactory.create("ACTIVITY", x=300, y=100, name="End")
    doc.add_element(elem1)
    doc.add_element(elem2)
    conn = ConnectionFactory.create(source_element=elem1.element_id, target_element=elem2.element_id)
    doc.add_connection(conn)
    return doc


@pytest.fixture
def document_with_warnings():
    """DocumentModel mit Warnungen (keine Namen, keine Connections)."""
    doc = DocumentModel()
    elem1 = ElementFactory.create("ACTIVITY", x=100, y=100, name="")
    elem2 = ElementFactory.create("ACTIVITY", x=300, y=100, name="")
    doc.add_element(elem1)
    doc.add_element(elem2)
    return doc


@pytest.fixture
def validation_controller(mock_event_bus):
    """ValidationController mit Mock Event-Bus."""
    return ValidationController(event_bus=mock_event_bus)


@pytest.fixture
def validation_controller_with_doc(mock_event_bus, valid_document):
    """ValidationController mit validem Dokument."""
    return ValidationController(event_bus=mock_event_bus, current_document=valid_document)


# ===== Test Initialization =====

class TestValidationControllerInit:
    """Tests für ValidationController Initialisierung."""
    
    def test_init_creates_controller(self, mock_event_bus):
        """Initialisierung erstellt Controller."""
        controller = ValidationController(mock_event_bus)
        
        assert controller.event_bus is mock_event_bus
        assert controller.current_document is None
        
    def test_init_with_document(self, mock_event_bus, valid_document):
        """Initialisierung mit Dokument."""
        controller = ValidationController(mock_event_bus, current_document=valid_document)
        
        assert controller.current_document is valid_document
        
    def test_init_subscribes_to_events(self, mock_event_bus):
        """Initialisierung subscribed zu Events."""
        controller = ValidationController(mock_event_bus)
        
        # Check subscriptions
        subscribe_calls = mock_event_bus.subscribe.call_args_list
        
        # Should subscribe to multiple events
        assert len(subscribe_calls) >= 3
        
        # Check specific subscriptions
        event_names = [call[0][0] for call in subscribe_calls]
        assert "ui:menu:tools:validate" in event_names
        assert "document:created" in event_names


# ===== Test Validation =====

class TestValidation:
    """Tests für Validierung."""
    
    def test_validate_empty_document_has_errors(self, validation_controller, empty_document):
        """Validierung eines leeren Dokuments hat Fehler."""
        validation_controller.current_document = empty_document
        
        results = validation_controller.validate()
        
        assert len(results["errors"]) > 0
        assert results["element_count"] == 0
        
    def test_validate_valid_document_has_no_errors(self, validation_controller_with_doc):
        """Validierung eines validen Dokuments hat keine Fehler."""
        results = validation_controller_with_doc.validate()
        
        assert len(results["errors"]) == 0
        
    def test_validate_document_with_warnings(self, validation_controller, document_with_warnings):
        """Validierung mit Warnungen."""
        validation_controller.current_document = document_with_warnings
        
        results = validation_controller.validate()
        
        assert len(results["warnings"]) > 0
        
    def test_validate_publishes_started_event(self, validation_controller_with_doc, mock_event_bus):
        """Validierung publiziert started Event."""
        validation_controller_with_doc._on_validate({})
        
        # Should publish validation:started event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "validation:started"]
        assert len(publish_calls) == 1
        
    def test_validate_publishes_completed_event(self, validation_controller_with_doc, mock_event_bus):
        """Validierung publiziert completed Event."""
        validation_controller_with_doc._on_validate({})
        
        # Should publish validation:completed event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "validation:completed"]
        assert len(publish_calls) == 1
        
    def test_validate_without_document_publishes_failed(self, validation_controller, mock_event_bus):
        """Validierung ohne Dokument publiziert failed Event."""
        validation_controller._on_validate({})
        
        # Should publish validation:failed event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "validation:failed"]
        assert len(publish_calls) == 1


# ===== Test Validation Rules =====

class TestValidationRules:
    """Tests für Validierungs-Regeln."""
    
    def test_no_elements_is_error(self, validation_controller, empty_document):
        """Keine Elemente ist Fehler."""
        validation_controller.current_document = empty_document
        results = validation_controller.validate()
        
        assert any(err["type"] == "NO_ELEMENTS" for err in results["errors"])
        
    def test_no_connections_is_warning(self, validation_controller, document_with_warnings):
        """Keine Connections (bei mehreren Elementen) ist Warnung."""
        validation_controller.current_document = document_with_warnings
        results = validation_controller.validate()
        
        assert any(warn["type"] == "NO_CONNECTIONS" for warn in results["warnings"])
        
    def test_empty_name_is_warning(self, validation_controller, document_with_warnings):
        """Leerer Name ist Warnung."""
        validation_controller.current_document = document_with_warnings
        results = validation_controller.validate()
        
        assert any(warn["type"] == "EMPTY_NAME" for warn in results["warnings"])
        
    def test_duplicate_names_is_warning(self, validation_controller):
        """Doppelte Namen sind Warnung."""
        doc = DocumentModel()
        elem1 = ElementFactory.create("ACTIVITY", x=100, y=100, name="Test")
        elem2 = ElementFactory.create("ACTIVITY", x=300, y=100, name="Test")
        doc.add_element(elem1)
        doc.add_element(elem2)
        validation_controller.current_document = doc
        
        results = validation_controller.validate()
        
        assert any(warn["type"] == "DUPLICATE_NAME" for warn in results["warnings"])


# ===== Test Validation Status =====

class TestValidationStatus:
    """Tests für Validierungs-Status."""
    
    def test_get_validation_status_valid(self, validation_controller_with_doc):
        """Status für valides Dokument."""
        status = validation_controller_with_doc.get_validation_status()
        
        assert status == "valid"
        
    def test_get_validation_status_warnings(self, validation_controller, document_with_warnings):
        """Status für Dokument mit Warnungen."""
        validation_controller.current_document = document_with_warnings
        status = validation_controller.get_validation_status()
        
        assert status == "warnings"
        
    def test_get_validation_status_errors(self, validation_controller, empty_document):
        """Status für Dokument mit Fehlern."""
        validation_controller.current_document = empty_document
        status = validation_controller.get_validation_status()
        
        assert status == "errors"
        
    def test_get_validation_status_no_document(self, validation_controller):
        """Status ohne Dokument."""
        status = validation_controller.get_validation_status()
        
        assert status == "no_document"


# ===== Test Document Events =====

class TestDocumentEvents:
    """Tests für Document Events."""
    
    def test_document_changed_updates_document(self, validation_controller, valid_document):
        """Document Changed aktualisiert Dokument."""
        validation_controller._on_document_changed({"document": valid_document})
        
        assert validation_controller.current_document is valid_document
        
    def test_document_closed_clears_document(self, validation_controller_with_doc):
        """Document Closed löscht Dokument."""
        validation_controller_with_doc._on_document_closed({})
        
        assert validation_controller_with_doc.current_document is None


# ===== Test Public API =====

class TestPublicAPI:
    """Tests für Public API."""
    
    def test_set_document(self, validation_controller, valid_document):
        """set_document setzt Dokument."""
        validation_controller.set_document(valid_document)
        
        assert validation_controller.current_document is valid_document
        
    def test_validate_returns_results(self, validation_controller_with_doc):
        """validate gibt Ergebnisse zurück."""
        results = validation_controller_with_doc.validate()
        
        assert "errors" in results
        assert "warnings" in results
        assert "info" in results
        assert "element_count" in results
        assert "connection_count" in results


# ===== Test String Representation =====

class TestStringRepresentation:
    """Tests für String-Repräsentation."""
    
    def test_repr_without_document(self, validation_controller):
        """__repr__ ohne Dokument."""
        result = repr(validation_controller)
        
        assert "no document" in result
        
    def test_repr_with_document(self, validation_controller_with_doc):
        """__repr__ mit Dokument."""
        result = repr(validation_controller_with_doc)
        
        assert "with document" in result
        assert "status=" in result
