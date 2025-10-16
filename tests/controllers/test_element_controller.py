"""
Tests für ElementController.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, MagicMock, patch

from vpb.controllers.element_controller import ElementController
from vpb.infrastructure.event_bus import EventBus
from vpb.models import VPBElement, ElementFactory, DocumentModel


# ===== Fixtures =====

@pytest.fixture
def mock_event_bus():
    """Mock Event-Bus."""
    return Mock(spec=EventBus)


@pytest.fixture
def sample_document():
    """Sample DocumentModel."""
    return DocumentModel()


@pytest.fixture
def element_controller(mock_event_bus):
    """ElementController mit Mock Event-Bus."""
    return ElementController(event_bus=mock_event_bus)


@pytest.fixture
def element_controller_with_doc(mock_event_bus, sample_document):
    """ElementController mit Dokument."""
    return ElementController(event_bus=mock_event_bus, current_document=sample_document)


@pytest.fixture
def sample_element():
    """Sample VPBElement."""
    return ElementFactory.create("ACTIVITY", x=100, y=200, name="Test Element")


# ===== Test Initialization =====

class TestElementControllerInit:
    """Tests für ElementController Initialisierung."""
    
    def test_init_creates_controller(self, mock_event_bus):
        """Initialisierung erstellt Controller."""
        controller = ElementController(mock_event_bus)
        
        assert controller.event_bus is mock_event_bus
        assert controller.current_document is None
        assert controller.selected_palette_item is None
        assert controller.selected_element_id is None
        
    def test_init_with_document(self, mock_event_bus, sample_document):
        """Initialisierung mit Dokument."""
        controller = ElementController(mock_event_bus, sample_document)
        
        assert controller.current_document is sample_document
        
    def test_init_subscribes_to_events(self, mock_event_bus):
        """Initialisierung subscribed zu Events."""
        controller = ElementController(mock_event_bus)
        
        # Check subscriptions
        subscribe_calls = mock_event_bus.subscribe.call_args_list
        
        # Should subscribe to multiple events
        assert len(subscribe_calls) >= 6
        
        # Check specific subscriptions
        event_names = [call[0][0] for call in subscribe_calls]
        assert "ui:palette:element_picked" in event_names
        assert "ui:canvas:left_click" in event_names
        assert "ui:canvas:delete_key" in event_names
        assert "ui:properties:element_changed" in event_names


# ===== Test Palette Element Picked =====

class TestPaletteElementPicked:
    """Tests für Palette Element Picked."""
    
    def test_palette_element_picked_stores_item(self, element_controller, mock_event_bus):
        """Palette Element Picked speichert Item."""
        item_data = {"type": "ACTIVITY", "name": "Aktivität"}
        
        element_controller._on_palette_element_picked({"item_data": item_data})
        
        assert element_controller.selected_palette_item == item_data
        
    def test_palette_element_picked_publishes_status(self, element_controller, mock_event_bus):
        """Palette Element Picked publiziert Status."""
        item_data = {"type": "ACTIVITY", "name": "Aktivität"}
        
        element_controller._on_palette_element_picked({"item_data": item_data})
        
        # Should publish status bar message
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "ui:statusbar:message"]
        assert len(publish_calls) == 1


# ===== Test Canvas Click (Element Creation) =====

class TestCanvasClick:
    """Tests für Canvas Click und Element-Erstellung."""
    
    def test_canvas_click_creates_element(self, element_controller_with_doc, mock_event_bus):
        """Canvas Click erstellt Element."""
        # Setup palette selection
        element_controller_with_doc.selected_palette_item = {
            "type": "ACTIVITY",
            "name": "Neue Aktivität"
        }
        
        element_controller_with_doc._on_canvas_click({"x": 150, "y": 250})
        
        # Element should be added to document
        elements = element_controller_with_doc.current_document.get_all_elements()
        assert len(elements) == 1
        assert elements[0].name == "Neue Aktivität"
        assert elements[0].x == 150
        assert elements[0].y == 250
        
    def test_canvas_click_publishes_event(self, element_controller_with_doc, mock_event_bus):
        """Canvas Click publiziert Event."""
        element_controller_with_doc.selected_palette_item = {
            "type": "ACTIVITY",
            "name": "Test"
        }
        
        element_controller_with_doc._on_canvas_click({"x": 100, "y": 200})
        
        # Should publish element:created event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "element:created"]
        assert len(publish_calls) == 1
        
    def test_canvas_click_without_palette_selection(self, element_controller_with_doc):
        """Canvas Click ohne Palette-Selection macht nichts."""
        element_controller_with_doc.selected_palette_item = None
        
        element_controller_with_doc._on_canvas_click({"x": 100, "y": 200})
        
        # No element should be created
        elements = element_controller_with_doc.current_document.get_all_elements()
        assert len(elements) == 0
        
    def test_canvas_click_without_document(self, element_controller):
        """Canvas Click ohne Dokument macht nichts."""
        element_controller.selected_palette_item = {"type": "ACTIVITY"}
        
        element_controller._on_canvas_click({"x": 100, "y": 200})
        
        # Should not crash
        assert True
        
    def test_canvas_click_clears_palette_selection(self, element_controller_with_doc):
        """Canvas Click löscht Palette-Selection nach Erstellung."""
        element_controller_with_doc.selected_palette_item = {"type": "ACTIVITY"}
        
        element_controller_with_doc._on_canvas_click({"x": 100, "y": 200})
        
        assert element_controller_with_doc.selected_palette_item is None


# ===== Test Delete Element =====

class TestDeleteElement:
    """Tests für Element-Deletion."""
    
    def test_delete_key_removes_element(self, element_controller_with_doc, sample_element):
        """Delete Key entfernt Element."""
        # Add element
        element_controller_with_doc.current_document.add_element(sample_element)
        element_controller_with_doc.selected_element_id = sample_element.element_id
        
        element_controller_with_doc._on_delete_key({})
        
        # Element should be removed
        assert element_controller_with_doc.current_document.get_element(sample_element.element_id) is None
        
    def test_delete_key_publishes_event(self, element_controller_with_doc, mock_event_bus, sample_element):
        """Delete Key publiziert Event."""
        element_controller_with_doc.current_document.add_element(sample_element)
        element_controller_with_doc.selected_element_id = sample_element.element_id
        
        element_controller_with_doc._on_delete_key({})
        
        # Should publish element:deleted event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "element:deleted"]
        assert len(publish_calls) == 1
        
    def test_delete_key_without_selection(self, element_controller_with_doc, sample_element):
        """Delete Key ohne Selection macht nichts."""
        element_controller_with_doc.current_document.add_element(sample_element)
        element_controller_with_doc.selected_element_id = None
        
        element_controller_with_doc._on_delete_key({})
        
        # Element should still exist
        assert element_controller_with_doc.current_document.get_element(sample_element.element_id) is not None
        
    def test_delete_key_clears_selection(self, element_controller_with_doc, sample_element):
        """Delete Key löscht Selection."""
        element_controller_with_doc.current_document.add_element(sample_element)
        element_controller_with_doc.selected_element_id = sample_element.element_id
        
        element_controller_with_doc._on_delete_key({})
        
        assert element_controller_with_doc.selected_element_id is None


# ===== Test Element Selection =====

class TestElementSelection:
    """Tests für Element-Selection."""
    
    def test_element_selected_sets_id(self, element_controller, sample_element):
        """Element Selected setzt ID."""
        element_controller._on_element_selected({"element_id": "E001"})
        
        assert element_controller.selected_element_id == "E001"
        
    def test_element_selected_publishes_event(self, element_controller_with_doc, mock_event_bus, sample_element):
        """Element Selected publiziert Event."""
        element_controller_with_doc.current_document.add_element(sample_element)
        
        element_controller_with_doc._on_element_selected({"element_id": sample_element.element_id})
        
        # Should publish element:selected event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "element:selected"]
        assert len(publish_calls) == 1


# ===== Test Element Properties Changed =====

class TestElementPropertiesChanged:
    """Tests für Element Properties Changed."""
    
    def test_properties_changed_updates_element(self, element_controller_with_doc, sample_element):
        """Properties Changed aktualisiert Element."""
        element_controller_with_doc.current_document.add_element(sample_element)
        
        element_controller_with_doc._on_element_properties_changed({
            "element": sample_element,
            "values": {"name": "Neuer Name", "description": "Neue Beschreibung"}
        })
        
        assert sample_element.name == "Neuer Name"
        assert sample_element.description == "Neue Beschreibung"
        
    def test_properties_changed_publishes_event(self, element_controller_with_doc, mock_event_bus, sample_element):
        """Properties Changed publiziert Event."""
        element_controller_with_doc.current_document.add_element(sample_element)
        
        element_controller_with_doc._on_element_properties_changed({
            "element": sample_element,
            "values": {"name": "Test"}
        })
        
        # Should publish element:modified event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "element:modified"]
        assert len(publish_calls) == 1


# ===== Test Document Events =====

class TestDocumentEvents:
    """Tests für Document Events."""
    
    def test_document_changed_updates_document(self, element_controller, sample_document):
        """Document Changed aktualisiert Dokument."""
        element_controller._on_document_changed({"document": sample_document})
        
        assert element_controller.current_document is sample_document
        
    def test_document_changed_clears_selection(self, element_controller):
        """Document Changed löscht Selection."""
        element_controller.selected_element_id = "E001"
        element_controller.selected_palette_item = {"type": "ACTIVITY"}
        
        element_controller._on_document_changed({"document": DocumentModel()})
        
        assert element_controller.selected_element_id is None
        assert element_controller.selected_palette_item is None
        
    def test_document_closed_clears_all(self, element_controller_with_doc):
        """Document Closed löscht alles."""
        element_controller_with_doc.selected_element_id = "E001"
        
        element_controller_with_doc._on_document_closed({})
        
        assert element_controller_with_doc.current_document is None
        assert element_controller_with_doc.selected_element_id is None


# ===== Test Public API =====

class TestPublicAPI:
    """Tests für Public API."""
    
    def test_set_document(self, element_controller, sample_document):
        """set_document setzt Dokument."""
        element_controller.set_document(sample_document)
        
        assert element_controller.current_document is sample_document
        
    def test_get_selected_element_id(self, element_controller):
        """get_selected_element_id gibt ID zurück."""
        element_controller.selected_element_id = "E001"
        
        assert element_controller.get_selected_element_id() == "E001"
        
    def test_get_selected_element(self, element_controller_with_doc, sample_element):
        """get_selected_element gibt Element zurück."""
        element_controller_with_doc.current_document.add_element(sample_element)
        element_controller_with_doc.selected_element_id = sample_element.element_id
        
        result = element_controller_with_doc.get_selected_element()
        
        assert result is sample_element
        
    def test_get_selected_element_without_selection(self, element_controller_with_doc):
        """get_selected_element ohne Selection gibt None zurück."""
        result = element_controller_with_doc.get_selected_element()
        
        assert result is None
        
    def test_clear_palette_selection(self, element_controller):
        """clear_palette_selection löscht Palette-Selection."""
        element_controller.selected_palette_item = {"type": "ACTIVITY"}
        
        element_controller.clear_palette_selection()
        
        assert element_controller.selected_palette_item is None


# ===== Test String Representation =====

class TestStringRepresentation:
    """Tests für String-Repräsentation."""
    
    def test_repr_without_document(self, element_controller):
        """__repr__ ohne Dokument."""
        result = repr(element_controller)
        
        assert "no document" in result
        assert "no selection" in result
        
    def test_repr_with_document(self, element_controller_with_doc):
        """__repr__ mit Dokument."""
        result = repr(element_controller_with_doc)
        
        assert "with document" in result
        
    def test_repr_with_selection(self, element_controller):
        """__repr__ mit Selection."""
        element_controller.selected_element_id = "E001"
        
        result = repr(element_controller)
        
        assert "selected=E001" in result
