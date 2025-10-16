"""
Tests für ExportController.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock

from vpb.controllers.export_controller import ExportController
from vpb.infrastructure.event_bus import EventBus
from vpb.models import DocumentModel, ElementFactory


# ===== Fixtures =====

@pytest.fixture
def mock_event_bus():
    """Mock Event-Bus."""
    return Mock(spec=EventBus)


@pytest.fixture
def sample_document():
    """Sample DocumentModel."""
    doc = DocumentModel()
    elem1 = ElementFactory.create("ACTIVITY", x=100, y=100, name="Test")
    doc.add_element(elem1)
    return doc


@pytest.fixture
def export_controller(mock_event_bus):
    """ExportController mit Mock Event-Bus."""
    return ExportController(event_bus=mock_event_bus)


@pytest.fixture
def export_controller_with_doc(mock_event_bus, sample_document):
    """ExportController mit Dokument."""
    return ExportController(event_bus=mock_event_bus, current_document=sample_document)


# ===== Test Initialization =====

class TestExportControllerInit:
    """Tests für ExportController Initialisierung."""
    
    def test_init_creates_controller(self, mock_event_bus):
        """Initialisierung erstellt Controller."""
        controller = ExportController(mock_event_bus)
        
        assert controller.event_bus is mock_event_bus
        assert controller.current_document is None
        assert controller.last_export_path is None
        assert controller.last_export_format is None
        
    def test_init_with_document(self, mock_event_bus, sample_document):
        """Initialisierung mit Dokument."""
        controller = ExportController(mock_event_bus, sample_document)
        
        assert controller.current_document is sample_document
        
    def test_init_subscribes_to_events(self, mock_event_bus):
        """Initialisierung subscribed zu Events."""
        controller = ExportController(mock_event_bus)
        
        # Check subscriptions
        subscribe_calls = mock_event_bus.subscribe.call_args_list
        
        # Should subscribe to multiple events
        assert len(subscribe_calls) >= 4
        
        # Check specific subscriptions
        event_names = [call[0][0] for call in subscribe_calls]
        assert "ui:menu:file:export" in event_names
        assert "ui:dialog:export:confirmed" in event_names


# ===== Test Export Menu =====

class TestExportMenu:
    """Tests für Export Menu."""
    
    def test_export_menu_opens_dialog(self, export_controller_with_doc, mock_event_bus):
        """Export Menu öffnet Dialog."""
        export_controller_with_doc._on_export_menu({})
        
        # Should publish ui:dialog:export:open event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "ui:dialog:export:open"]
        assert len(publish_calls) == 1
        
    def test_export_menu_without_document(self, export_controller, mock_event_bus):
        """Export Menu ohne Dokument."""
        export_controller._on_export_menu({})
        
        # Should publish export:failed event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "export:failed"]
        assert len(publish_calls) == 1


# ===== Test Export Confirmed =====

class TestExportConfirmed:
    """Tests für Export Confirmed."""
    
    def test_export_confirmed_publishes_started(self, export_controller_with_doc, mock_event_bus):
        """Export Confirmed publiziert started Event."""
        export_controller_with_doc._on_export_confirmed({
            "format": "PNG",
            "path": "test.png",
            "options": {}
        })
        
        # Should publish export:started event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "export:started"]
        assert len(publish_calls) == 1
        
    def test_export_confirmed_publishes_completed(self, export_controller_with_doc, mock_event_bus):
        """Export Confirmed publiziert completed Event."""
        export_controller_with_doc._on_export_confirmed({
            "format": "PNG",
            "path": "test.png",
            "options": {}
        })
        
        # Should publish export:completed event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "export:completed"]
        assert len(publish_calls) == 1
        
    def test_export_confirmed_remembers_settings(self, export_controller_with_doc):
        """Export Confirmed speichert Einstellungen."""
        export_controller_with_doc._on_export_confirmed({
            "format": "SVG",
            "path": "output.svg",
            "options": {}
        })
        
        assert export_controller_with_doc.last_export_format == "SVG"
        assert export_controller_with_doc.last_export_path == "output.svg"
        
    def test_export_confirmed_without_path(self, export_controller_with_doc, mock_event_bus):
        """Export Confirmed ohne Pfad."""
        export_controller_with_doc._on_export_confirmed({
            "format": "PNG",
            "path": "",
            "options": {}
        })
        
        # Should publish export:failed event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "export:failed"]
        assert len(publish_calls) == 1


# ===== Test Export Document =====

class TestExportDocument:
    """Tests für Export Document."""
    
    def test_export_to_png(self, export_controller_with_doc):
        """Export zu PNG."""
        # Should not raise exception
        export_controller_with_doc._export_document("PNG", "test.png", {})
        
    def test_export_to_svg(self, export_controller_with_doc):
        """Export zu SVG."""
        export_controller_with_doc._export_document("SVG", "test.svg", {})
        
    def test_export_to_pdf(self, export_controller_with_doc):
        """Export zu PDF."""
        export_controller_with_doc._export_document("PDF", "test.pdf", {})
        
    def test_export_to_xml(self, export_controller_with_doc):
        """Export zu XML."""
        export_controller_with_doc._export_document("XML", "test.xml", {})
        
    def test_export_to_json(self, export_controller_with_doc):
        """Export zu JSON."""
        export_controller_with_doc._export_document("JSON", "test.json", {})
        
    def test_export_invalid_format_raises_error(self, export_controller_with_doc):
        """Export mit ungültigem Format wirft Fehler."""
        with pytest.raises(ValueError, match="Ungültiges Export-Format"):
            export_controller_with_doc._export_document("INVALID", "test.txt", {})
        
    def test_export_without_document_raises_error(self, export_controller):
        """Export ohne Dokument wirft Fehler."""
        with pytest.raises(ValueError, match="Kein Dokument geladen"):
            export_controller._export_document("PNG", "test.png", {})


# ===== Test Document Events =====

class TestDocumentEvents:
    """Tests für Document Events."""
    
    def test_document_changed_updates_document(self, export_controller, sample_document):
        """Document Changed aktualisiert Dokument."""
        export_controller._on_document_changed({"document": sample_document})
        
        assert export_controller.current_document is sample_document
        
    def test_document_closed_clears_document(self, export_controller_with_doc):
        """Document Closed löscht Dokument."""
        export_controller_with_doc._on_document_closed({})
        
        assert export_controller_with_doc.current_document is None


# ===== Test Public API =====

class TestPublicAPI:
    """Tests für Public API."""
    
    def test_set_document(self, export_controller, sample_document):
        """set_document setzt Dokument."""
        export_controller.set_document(sample_document)
        
        assert export_controller.current_document is sample_document
        
    def test_export(self, export_controller_with_doc):
        """export führt Export durch."""
        # Should not raise exception
        export_controller_with_doc.export("PNG", "test.png")
        
    def test_get_last_export_info(self, export_controller_with_doc):
        """get_last_export_info gibt Informationen zurück."""
        export_controller_with_doc.last_export_format = "PNG"
        export_controller_with_doc.last_export_path = "test.png"
        
        info = export_controller_with_doc.get_last_export_info()
        
        assert info["format"] == "PNG"
        assert info["path"] == "test.png"
        
    def test_get_last_export_info_when_empty(self, export_controller):
        """get_last_export_info wenn leer."""
        info = export_controller.get_last_export_info()
        
        assert info["format"] is None
        assert info["path"] is None


# ===== Test String Representation =====

class TestStringRepresentation:
    """Tests für String-Repräsentation."""
    
    def test_repr_without_document(self, export_controller):
        """__repr__ ohne Dokument."""
        result = repr(export_controller)
        
        assert "no document" in result
        
    def test_repr_with_document(self, export_controller_with_doc):
        """__repr__ mit Dokument."""
        result = repr(export_controller_with_doc)
        
        assert "with document" in result
        
    def test_repr_with_last_export(self, export_controller_with_doc):
        """__repr__ mit letztem Export."""
        export_controller_with_doc.last_export_format = "PNG"
        result = repr(export_controller_with_doc)
        
        assert "last=PNG" in result
