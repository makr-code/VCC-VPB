"""
Tests für AIController.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock

from vpb.controllers.ai_controller import AIController
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
def ai_controller(mock_event_bus):
    """AIController mit Mock Event-Bus."""
    return AIController(event_bus=mock_event_bus)


@pytest.fixture
def ai_controller_with_doc(mock_event_bus, sample_document):
    """AIController mit Dokument."""
    return AIController(event_bus=mock_event_bus, current_document=sample_document)


# ===== Test Initialization =====

class TestAIControllerInit:
    """Tests für AIController Initialisierung."""
    
    def test_init_creates_controller(self, mock_event_bus):
        """Initialisierung erstellt Controller."""
        controller = AIController(mock_event_bus)
        
        assert controller.event_bus is mock_event_bus
        assert controller.current_document is None
        assert controller.ai_enabled is True
        
    def test_init_with_document(self, mock_event_bus, sample_document):
        """Initialisierung mit Dokument."""
        controller = AIController(mock_event_bus, sample_document)
        
        assert controller.current_document is sample_document
        
    def test_init_subscribes_to_events(self, mock_event_bus):
        """Initialisierung subscribed zu Events."""
        controller = AIController(mock_event_bus)
        
        # Check subscriptions
        subscribe_calls = mock_event_bus.subscribe.call_args_list
        
        # Should subscribe to multiple events
        assert len(subscribe_calls) >= 5
        
        # Check specific subscriptions
        event_names = [call[0][0] for call in subscribe_calls]
        assert "ui:menu:ai:wizard" in event_names
        assert "ui:menu:ai:improve" in event_names


# ===== Test AI Wizard =====

class TestAIWizard:
    """Tests für AI Wizard."""
    
    def test_ai_wizard_publishes_started_event(self, ai_controller, mock_event_bus):
        """AI Wizard publiziert started Event."""
        ai_controller._on_ai_wizard({"prompt": "Test"})
        
        # Should publish ai:wizard:started event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "ai:wizard:started"]
        assert len(publish_calls) == 1
        
    def test_ai_wizard_publishes_completed_event(self, ai_controller, mock_event_bus):
        """AI Wizard publiziert completed Event."""
        ai_controller._on_ai_wizard({"prompt": "Test"})
        
        # Should publish ai:wizard:completed event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "ai:wizard:completed"]
        assert len(publish_calls) == 1
        
    def test_ai_wizard_when_disabled(self, ai_controller, mock_event_bus):
        """AI Wizard wenn deaktiviert."""
        ai_controller.ai_enabled = False
        ai_controller._on_ai_wizard({"prompt": "Test"})
        
        # Should publish ai:failed event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "ai:failed"]
        assert len(publish_calls) == 1


# ===== Test AI Improve =====

class TestAIImprove:
    """Tests für AI Improve."""
    
    def test_ai_improve_generates_suggestions(self, ai_controller_with_doc):
        """AI Improve generiert Vorschläge."""
        ai_controller_with_doc._on_ai_improve({})
        
        suggestions = ai_controller_with_doc.get_last_suggestions()
        assert len(suggestions) > 0
        
    def test_ai_improve_publishes_completed_event(self, ai_controller_with_doc, mock_event_bus):
        """AI Improve publiziert completed Event."""
        ai_controller_with_doc._on_ai_improve({})
        
        # Should publish ai:improvement:completed event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "ai:improvement:completed"]
        assert len(publish_calls) == 1
        
    def test_ai_improve_without_document(self, ai_controller, mock_event_bus):
        """AI Improve ohne Dokument."""
        ai_controller._on_ai_improve({})
        
        # Should publish ai:failed event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "ai:failed"]
        assert len(publish_calls) == 1
        
    def test_ai_improve_when_disabled(self, ai_controller_with_doc, mock_event_bus):
        """AI Improve wenn deaktiviert."""
        ai_controller_with_doc.ai_enabled = False
        ai_controller_with_doc._on_ai_improve({})
        
        # Should publish ai:failed event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "ai:failed"]
        assert len(publish_calls) == 1


# ===== Test Text Extraction =====

class TestTextExtraction:
    """Tests für Text Extraction."""
    
    def test_extract_text_publishes_event(self, ai_controller, mock_event_bus):
        """Text Extraction publiziert Event."""
        ai_controller._on_ai_extract_text({"image_path": "test.png"})
        
        # Should publish ai:text_extracted event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "ai:text_extracted"]
        assert len(publish_calls) == 1
        
    def test_extract_text_without_path(self, ai_controller, mock_event_bus):
        """Text Extraction ohne Pfad."""
        ai_controller._on_ai_extract_text({})
        
        # Should publish ai:failed event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "ai:failed"]
        assert len(publish_calls) == 1


# ===== Test AI Settings =====

class TestAISettings:
    """Tests für AI Settings."""
    
    def test_enable_ai(self, ai_controller):
        """AI aktivieren."""
        ai_controller.enable_ai(True)
        
        assert ai_controller.ai_enabled is True
        
    def test_disable_ai(self, ai_controller):
        """AI deaktivieren."""
        ai_controller.enable_ai(False)
        
        assert ai_controller.ai_enabled is False
        
    def test_ai_settings_event(self, ai_controller, mock_event_bus):
        """AI Settings Event."""
        ai_controller._on_ai_settings({"enabled": False})
        
        assert ai_controller.ai_enabled is False


# ===== Test Document Events =====

class TestDocumentEvents:
    """Tests für Document Events."""
    
    def test_document_changed_updates_document(self, ai_controller, sample_document):
        """Document Changed aktualisiert Dokument."""
        ai_controller._on_document_changed({"document": sample_document})
        
        assert ai_controller.current_document is sample_document
        
    def test_document_changed_clears_suggestions(self, ai_controller_with_doc):
        """Document Changed löscht Suggestions."""
        ai_controller_with_doc.last_suggestions = [{"test": "data"}]
        ai_controller_with_doc._on_document_changed({"document": DocumentModel()})
        
        assert len(ai_controller_with_doc.last_suggestions) == 0
        
    def test_document_closed_clears_document(self, ai_controller_with_doc):
        """Document Closed löscht Dokument."""
        ai_controller_with_doc._on_document_closed({})
        
        assert ai_controller_with_doc.current_document is None


# ===== Test Public API =====

class TestPublicAPI:
    """Tests für Public API."""
    
    def test_set_document(self, ai_controller, sample_document):
        """set_document setzt Dokument."""
        ai_controller.set_document(sample_document)
        
        assert ai_controller.current_document is sample_document
        
    def test_get_last_suggestions(self, ai_controller):
        """get_last_suggestions gibt Suggestions zurück."""
        suggestions = [{"test": "data"}]
        ai_controller.last_suggestions = suggestions
        
        result = ai_controller.get_last_suggestions()
        
        assert result == suggestions


# ===== Test String Representation =====

class TestStringRepresentation:
    """Tests für String-Repräsentation."""
    
    def test_repr_without_document(self, ai_controller):
        """__repr__ ohne Dokument."""
        result = repr(ai_controller)
        
        assert "no document" in result
        assert "enabled" in result
        
    def test_repr_with_document(self, ai_controller_with_doc):
        """__repr__ mit Dokument."""
        result = repr(ai_controller_with_doc)
        
        assert "with document" in result
        
    def test_repr_with_disabled_ai(self, ai_controller):
        """__repr__ mit deaktivierter AI."""
        ai_controller.ai_enabled = False
        result = repr(ai_controller)
        
        assert "disabled" in result
