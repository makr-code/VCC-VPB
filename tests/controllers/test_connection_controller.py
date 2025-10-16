"""
Tests für ConnectionController.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock

from vpb.controllers.connection_controller import ConnectionController
from vpb.infrastructure.event_bus import EventBus
from vpb.models import VPBConnection, ConnectionFactory, DocumentModel, ElementFactory


# ===== Fixtures =====

@pytest.fixture
def mock_event_bus():
    """Mock Event-Bus."""
    return Mock(spec=EventBus)


@pytest.fixture
def sample_document():
    """Sample DocumentModel mit 2 Elements."""
    doc = DocumentModel()
    elem1 = ElementFactory.create("ACTIVITY", x=100, y=100, name="Start")
    elem2 = ElementFactory.create("ACTIVITY", x=300, y=100, name="End")
    doc.add_element(elem1)
    doc.add_element(elem2)
    return doc, elem1.element_id, elem2.element_id


@pytest.fixture
def connection_controller(mock_event_bus):
    """ConnectionController mit Mock Event-Bus."""
    return ConnectionController(event_bus=mock_event_bus)


@pytest.fixture
def connection_controller_with_doc(mock_event_bus, sample_document):
    """ConnectionController mit Dokument."""
    doc, _, _ = sample_document
    return ConnectionController(event_bus=mock_event_bus, current_document=doc)


@pytest.fixture
def sample_connection(sample_document):
    """Sample VPBConnection."""
    _, elem1_id, elem2_id = sample_document
    return ConnectionFactory.create(source_element=elem1_id, target_element=elem2_id)


# ===== Test Initialization =====

class TestConnectionControllerInit:
    """Tests für ConnectionController Initialisierung."""
    
    def test_init_creates_controller(self, mock_event_bus):
        """Initialisierung erstellt Controller."""
        controller = ConnectionController(mock_event_bus)
        
        assert controller.event_bus is mock_event_bus
        assert controller.current_document is None
        assert controller.connection_start_element_id is None
        assert controller.selected_connection_id is None
        
    def test_init_with_document(self, mock_event_bus, sample_document):
        """Initialisierung mit Dokument."""
        doc, _, _ = sample_document
        controller = ConnectionController(mock_event_bus, doc)
        
        assert controller.current_document is doc
        
    def test_init_subscribes_to_events(self, mock_event_bus):
        """Initialisierung subscribed zu Events."""
        controller = ConnectionController(mock_event_bus)
        
        # Check subscriptions
        subscribe_calls = mock_event_bus.subscribe.call_args_list
        
        # Should subscribe to multiple events
        assert len(subscribe_calls) >= 6
        
        # Check specific subscriptions
        event_names = [call[0][0] for call in subscribe_calls]
        assert "ui:canvas:connection_start" in event_names
        assert "ui:canvas:connection_end" in event_names
        assert "ui:properties:connection_changed" in event_names


# ===== Test Connection Creation =====

class TestConnectionCreation:
    """Tests für Connection-Creation."""
    
    def test_connection_start_stores_element_id(self, connection_controller):
        """Connection Start speichert Element ID."""
        connection_controller._on_connection_start({"start_element_id": "E001"})
        
        assert connection_controller.connection_start_element_id == "E001"
        
    def test_connection_start_publishes_status(self, connection_controller, mock_event_bus):
        """Connection Start publiziert Status."""
        connection_controller._on_connection_start({"start_element_id": "E001"})
        
        # Should publish status bar message
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "ui:statusbar:message"]
        assert len(publish_calls) == 1
        
    def test_connection_end_creates_connection(self, connection_controller_with_doc, sample_document):
        """Connection End erstellt Connection."""
        doc, elem1_id, elem2_id = sample_document
        connection_controller_with_doc.connection_start_element_id = elem1_id
        
        connection_controller_with_doc._on_connection_end({"end_element_id": elem2_id})
        
        # Connection should be added to document
        connections = doc.get_all_connections()
        assert len(connections) == 1
        assert connections[0].source_element == elem1_id
        assert connections[0].target_element == elem2_id
        
    def test_connection_end_publishes_event(self, connection_controller_with_doc, mock_event_bus, sample_document):
        """Connection End publiziert Event."""
        _, elem1_id, elem2_id = sample_document
        connection_controller_with_doc.connection_start_element_id = elem1_id
        
        connection_controller_with_doc._on_connection_end({"end_element_id": elem2_id})
        
        # Should publish connection:created event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "connection:created"]
        assert len(publish_calls) == 1
        
    def test_connection_end_prevents_self_connection(self, connection_controller_with_doc, sample_document):
        """Connection End verhindert Self-Connection."""
        doc, elem1_id, _ = sample_document
        connection_controller_with_doc.connection_start_element_id = elem1_id
        
        connection_controller_with_doc._on_connection_end({"end_element_id": elem1_id})
        
        # No connection should be created
        connections = doc.get_all_connections()
        assert len(connections) == 0
        
    def test_connection_end_without_start(self, connection_controller_with_doc):
        """Connection End ohne Start macht nichts."""
        connection_controller_with_doc._on_connection_end({"end_element_id": "E002"})
        
        # Should not crash
        assert True


# ===== Test Connection Deletion =====

class TestConnectionDeletion:
    """Tests für Connection-Deletion."""
    
    def test_delete_key_removes_connection(self, connection_controller_with_doc, sample_document, sample_connection):
        """Delete Key entfernt Connection."""
        doc, _, _ = sample_document
        doc.add_connection(sample_connection)
        connection_controller_with_doc.selected_connection_id = sample_connection.connection_id
        
        connection_controller_with_doc._on_delete_key({})
        
        # Connection should be removed
        assert doc.get_connection(sample_connection.connection_id) is None
        
    def test_delete_key_publishes_event(self, connection_controller_with_doc, mock_event_bus, sample_document, sample_connection):
        """Delete Key publiziert Event."""
        doc, _, _ = sample_document
        doc.add_connection(sample_connection)
        connection_controller_with_doc.selected_connection_id = sample_connection.connection_id
        
        connection_controller_with_doc._on_delete_key({})
        
        # Should publish connection:deleted event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "connection:deleted"]
        assert len(publish_calls) == 1
        
    def test_delete_key_without_selection(self, connection_controller_with_doc, sample_document, sample_connection):
        """Delete Key ohne Selection macht nichts."""
        doc, _, _ = sample_document
        doc.add_connection(sample_connection)
        
        connection_controller_with_doc._on_delete_key({})
        
        # Connection should still exist
        assert doc.get_connection(sample_connection.connection_id) is not None


# ===== Test Connection Selection =====

class TestConnectionSelection:
    """Tests für Connection-Selection."""
    
    def test_connection_selected_sets_id(self, connection_controller):
        """Connection Selected setzt ID."""
        connection_controller._on_connection_selected({"connection_id": "C001"})
        
        assert connection_controller.selected_connection_id == "C001"
        
    def test_connection_selected_publishes_event(self, connection_controller_with_doc, mock_event_bus, sample_document, sample_connection):
        """Connection Selected publiziert Event."""
        doc, _, _ = sample_document
        doc.add_connection(sample_connection)
        
        connection_controller_with_doc._on_connection_selected({"connection_id": sample_connection.connection_id})
        
        # Should publish connection:selected event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "connection:selected"]
        assert len(publish_calls) == 1


# ===== Test Connection Properties =====

class TestConnectionProperties:
    """Tests für Connection Properties."""
    
    def test_properties_changed_updates_connection(self, sample_connection):
        """Properties Changed aktualisiert Connection."""
        controller = ConnectionController(Mock())
        
        controller._on_connection_properties_changed({
            "connection": sample_connection,
            "values": {
                "description": "Neue Beschreibung",
                "routing_mode": "orthogonal"
            }
        })
        
        assert sample_connection.description == "Neue Beschreibung"
        assert sample_connection.routing_mode == "orthogonal"
        
    def test_properties_changed_publishes_event(self, mock_event_bus, sample_connection):
        """Properties Changed publiziert Event."""
        controller = ConnectionController(mock_event_bus)
        
        controller._on_connection_properties_changed({
            "connection": sample_connection,
            "values": {"description": "Test"}
        })
        
        # Should publish connection:modified event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "connection:modified"]
        assert len(publish_calls) == 1


# ===== Test Document Events =====

class TestDocumentEvents:
    """Tests für Document Events."""
    
    def test_document_changed_updates_document(self, connection_controller):
        """Document Changed aktualisiert Dokument."""
        doc = DocumentModel()
        connection_controller._on_document_changed({"document": doc})
        
        assert connection_controller.current_document is doc
        
    def test_document_changed_clears_state(self, connection_controller):
        """Document Changed löscht State."""
        connection_controller.connection_start_element_id = "E001"
        connection_controller.selected_connection_id = "C001"
        
        connection_controller._on_document_changed({"document": DocumentModel()})
        
        assert connection_controller.connection_start_element_id is None
        assert connection_controller.selected_connection_id is None
        
    def test_document_closed_clears_all(self, connection_controller_with_doc):
        """Document Closed löscht alles."""
        connection_controller_with_doc.selected_connection_id = "C001"
        
        connection_controller_with_doc._on_document_closed({})
        
        assert connection_controller_with_doc.current_document is None
        assert connection_controller_with_doc.selected_connection_id is None


# ===== Test Public API =====

class TestPublicAPI:
    """Tests für Public API."""
    
    def test_set_document(self, connection_controller):
        """set_document setzt Dokument."""
        doc = DocumentModel()
        connection_controller.set_document(doc)
        
        assert connection_controller.current_document is doc
        
    def test_get_selected_connection_id(self, connection_controller):
        """get_selected_connection_id gibt ID zurück."""
        connection_controller.selected_connection_id = "C001"
        
        assert connection_controller.get_selected_connection_id() == "C001"
        
    def test_get_selected_connection(self, connection_controller_with_doc, sample_document, sample_connection):
        """get_selected_connection gibt Connection zurück."""
        doc, _, _ = sample_document
        doc.add_connection(sample_connection)
        connection_controller_with_doc.selected_connection_id = sample_connection.connection_id
        
        result = connection_controller_with_doc.get_selected_connection()
        
        assert result is sample_connection
        
    def test_get_selected_connection_without_selection(self, connection_controller_with_doc):
        """get_selected_connection ohne Selection gibt None zurück."""
        result = connection_controller_with_doc.get_selected_connection()
        
        assert result is None
        
    def test_cancel_connection_creation(self, connection_controller):
        """cancel_connection_creation löscht Start-Element."""
        connection_controller.connection_start_element_id = "E001"
        
        connection_controller.cancel_connection_creation()
        
        assert connection_controller.connection_start_element_id is None


# ===== Test String Representation =====

class TestStringRepresentation:
    """Tests für String-Repräsentation."""
    
    def test_repr_without_document(self, connection_controller):
        """__repr__ ohne Dokument."""
        result = repr(connection_controller)
        
        assert "no document" in result
        assert "no selection" in result
        assert "no start" in result
        
    def test_repr_with_document(self, connection_controller_with_doc):
        """__repr__ mit Dokument."""
        result = repr(connection_controller_with_doc)
        
        assert "with document" in result
        
    def test_repr_with_selection(self, connection_controller):
        """__repr__ mit Selection."""
        connection_controller.selected_connection_id = "C001"
        
        result = repr(connection_controller)
        
        assert "selected=C001" in result
        
    def test_repr_with_start(self, connection_controller):
        """__repr__ mit Start-Element."""
        connection_controller.connection_start_element_id = "E001"
        
        result = repr(connection_controller)
        
        assert "start=E001" in result
