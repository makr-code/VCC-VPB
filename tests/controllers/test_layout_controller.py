"""
Tests für LayoutController.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock
import math

from vpb.controllers.layout_controller import LayoutController
from vpb.infrastructure.event_bus import EventBus
from vpb.models import DocumentModel, ElementFactory


# ===== Fixtures =====

@pytest.fixture
def mock_event_bus():
    """Mock Event-Bus."""
    return Mock(spec=EventBus)


@pytest.fixture
def sample_document():
    """Sample DocumentModel mit 4 Elements."""
    doc = DocumentModel()
    for i in range(4):
        elem = ElementFactory.create("ACTIVITY", x=100 + i*50, y=100 + i*50, name=f"Element {i+1}")
        doc.add_element(elem)
    return doc


@pytest.fixture
def layout_controller(mock_event_bus):
    """LayoutController mit Mock Event-Bus."""
    return LayoutController(event_bus=mock_event_bus)


@pytest.fixture
def layout_controller_with_doc(mock_event_bus, sample_document):
    """LayoutController mit Dokument."""
    return LayoutController(event_bus=mock_event_bus, current_document=sample_document)


# ===== Test Initialization =====

class TestLayoutControllerInit:
    """Tests für LayoutController Initialisierung."""
    
    def test_init_creates_controller(self, mock_event_bus):
        """Initialisierung erstellt Controller."""
        controller = LayoutController(mock_event_bus)
        
        assert controller.event_bus is mock_event_bus
        assert controller.current_document is None
        
    def test_init_with_document(self, mock_event_bus, sample_document):
        """Initialisierung mit Dokument."""
        controller = LayoutController(mock_event_bus, sample_document)
        
        assert controller.current_document is sample_document
        
    def test_init_subscribes_to_events(self, mock_event_bus):
        """Initialisierung subscribed zu Events."""
        controller = LayoutController(mock_event_bus)
        
        # Check subscriptions
        subscribe_calls = mock_event_bus.subscribe.call_args_list
        
        # Should subscribe to many events (auto_layout, align, distribute, formation, document)
        assert len(subscribe_calls) >= 10
        
        # Check specific subscriptions
        event_names = [call[0][0] for call in subscribe_calls]
        assert "ui:menu:layout:auto_layout" in event_names
        assert "ui:menu:layout:align:left" in event_names
        assert "ui:menu:layout:distribute:horizontal" in event_names


# ===== Test Auto Layout =====

class TestAutoLayout:
    """Tests für Auto-Layout."""
    
    def test_auto_layout_arranges_elements(self, layout_controller_with_doc, sample_document):
        """Auto-Layout ordnet Elemente an."""
        elements = sample_document.get_all_elements()
        original_positions = [(e.x, e.y) for e in elements]
        
        layout_controller_with_doc._on_auto_layout({})
        
        # Positions should have changed
        new_positions = [(e.x, e.y) for e in elements]
        assert new_positions != original_positions
        
    def test_auto_layout_publishes_event(self, layout_controller_with_doc, mock_event_bus):
        """Auto-Layout publiziert Event."""
        layout_controller_with_doc._on_auto_layout({})
        
        # Should publish layout:applied event
        publish_calls = [call for call in mock_event_bus.publish.call_args_list 
                        if call[0][0] == "layout:applied"]
        assert len(publish_calls) == 1
        
    def test_auto_layout_without_document(self, layout_controller):
        """Auto-Layout ohne Dokument macht nichts."""
        layout_controller._on_auto_layout({})
        
        # Should not crash
        assert True


# ===== Test Align Operations =====

class TestAlignOperations:
    """Tests für Align-Operationen."""
    
    def test_align_left(self, layout_controller_with_doc, sample_document):
        """Align Left richtet aus."""
        elements = sample_document.get_all_elements()
        element_ids = [e.element_id for e in elements]
        
        layout_controller_with_doc._on_align_left({"element_ids": element_ids})
        
        # All elements should have same x coordinate
        x_coords = [e.x for e in elements]
        assert len(set(x_coords)) == 1
        
    def test_align_right(self, layout_controller_with_doc, sample_document):
        """Align Right richtet aus."""
        elements = sample_document.get_all_elements()
        element_ids = [e.element_id for e in elements]
        
        layout_controller_with_doc._on_align_right({"element_ids": element_ids})
        
        # All elements should have same right edge (x + default_width)
        default_width = 120
        right_edges = [e.x + default_width for e in elements]
        assert len(set(right_edges)) == 1
        
    def test_align_top(self, layout_controller_with_doc, sample_document):
        """Align Top richtet aus."""
        elements = sample_document.get_all_elements()
        element_ids = [e.element_id for e in elements]
        
        layout_controller_with_doc._on_align_top({"element_ids": element_ids})
        
        # All elements should have same y coordinate
        y_coords = [e.y for e in elements]
        assert len(set(y_coords)) == 1
        
    def test_align_center_h(self, layout_controller_with_doc, sample_document):
        """Align Center Horizontal zentriert."""
        elements = sample_document.get_all_elements()
        element_ids = [e.element_id for e in elements]
        
        layout_controller_with_doc._on_align_center_h({"element_ids": element_ids})
        
        # All elements should have same center x
        default_width = 120
        center_x = [e.x + default_width / 2 for e in elements]
        # Allow small floating point differences
        assert max(center_x) - min(center_x) < 0.001
        
    def test_align_with_single_element(self, layout_controller_with_doc, sample_document):
        """Align mit nur einem Element macht nichts."""
        elements = sample_document.get_all_elements()
        element_id = elements[0].element_id
        original_x = elements[0].x
        
        layout_controller_with_doc._on_align_left({"element_ids": [element_id]})
        
        # Position should not change
        assert elements[0].x == original_x


# ===== Test Distribute Operations =====

class TestDistributeOperations:
    """Tests für Distribute-Operationen."""
    
    def test_distribute_horizontal(self, layout_controller_with_doc, sample_document):
        """Distribute Horizontal verteilt."""
        elements = sample_document.get_all_elements()
        element_ids = [e.element_id for e in elements]
        
        layout_controller_with_doc._on_distribute_horizontal({"element_ids": element_ids})
        
        # Elements should be evenly spaced
        default_width = 120
        elements_sorted = sorted(elements, key=lambda e: e.x)
        spacings = []
        for i in range(len(elements_sorted) - 1):
            spacing = elements_sorted[i+1].x - (elements_sorted[i].x + default_width)
            spacings.append(spacing)
        
        # All spacings should be approximately equal
        if len(spacings) > 1:
            assert max(spacings) - min(spacings) < 0.001
        
    def test_distribute_vertical(self, layout_controller_with_doc, sample_document):
        """Distribute Vertical verteilt."""
        elements = sample_document.get_all_elements()
        element_ids = [e.element_id for e in elements]
        
        layout_controller_with_doc._on_distribute_vertical({"element_ids": element_ids})
        
        # Elements should be evenly spaced vertically
        default_height = 80
        elements_sorted = sorted(elements, key=lambda e: e.y)
        spacings = []
        for i in range(len(elements_sorted) - 1):
            spacing = elements_sorted[i+1].y - (elements_sorted[i].y + default_height)
            spacings.append(spacing)
        
        # All spacings should be approximately equal
        if len(spacings) > 1:
            assert max(spacings) - min(spacings) < 0.001
        
    def test_distribute_with_two_elements(self, layout_controller_with_doc, sample_document):
        """Distribute mit nur 2 Elementen macht nichts."""
        elements = sample_document.get_all_elements()[:2]
        element_ids = [e.element_id for e in elements]
        original_x = [e.x for e in elements]
        
        layout_controller_with_doc._on_distribute_horizontal({"element_ids": element_ids})
        
        # Positions should not change (need at least 3 elements)
        assert [e.x for e in elements] == original_x


# ===== Test Formation Operations =====

class TestFormationOperations:
    """Tests für Formation-Operationen."""
    
    def test_formation_line(self, layout_controller_with_doc, sample_document):
        """Formation Line ordnet in Linie an."""
        elements = sample_document.get_all_elements()
        element_ids = [e.element_id for e in elements]
        
        layout_controller_with_doc._on_formation_line({"element_ids": element_ids})
        
        # All elements should have same y coordinate
        y_coords = [e.y for e in elements]
        assert len(set(y_coords)) == 1
        
    def test_formation_circle(self, layout_controller_with_doc, sample_document):
        """Formation Circle ordnet im Kreis an."""
        elements = sample_document.get_all_elements()
        element_ids = [e.element_id for e in elements]
        
        layout_controller_with_doc._on_formation_circle({"element_ids": element_ids})
        
        # Elements should be arranged in a circle
        # Check that all elements are approximately same distance from center
        center_x = 400
        center_y = 300
        default_width = 120
        default_height = 80
        distances = []
        for elem in elements:
            elem_center_x = elem.x + default_width / 2
            elem_center_y = elem.y + default_height / 2
            dist = math.sqrt((elem_center_x - center_x)**2 + (elem_center_y - center_y)**2)
            distances.append(dist)
        
        # All distances should be approximately equal
        assert max(distances) - min(distances) < 1.0
        
    def test_formation_grid(self, layout_controller_with_doc, sample_document):
        """Formation Grid ordnet im Gitter an."""
        elements = sample_document.get_all_elements()
        element_ids = [e.element_id for e in elements]
        
        layout_controller_with_doc._on_formation_grid({"element_ids": element_ids})
        
        # Elements should be in grid pattern
        # For 4 elements, should be 2x2 grid
        x_coords = sorted(set(e.x for e in elements))
        y_coords = sorted(set(e.y for e in elements))
        
        # Should have 2 unique x and 2 unique y coordinates
        assert len(x_coords) == 2
        assert len(y_coords) == 2


# ===== Test Document Events =====

class TestDocumentEvents:
    """Tests für Document Events."""
    
    def test_document_changed_updates_document(self, layout_controller):
        """Document Changed aktualisiert Dokument."""
        doc = DocumentModel()
        layout_controller._on_document_changed({"document": doc})
        
        assert layout_controller.current_document is doc
        
    def test_document_closed_clears_document(self, layout_controller_with_doc):
        """Document Closed löscht Dokument."""
        layout_controller_with_doc._on_document_closed({})
        
        assert layout_controller_with_doc.current_document is None


# ===== Test Public API =====

class TestPublicAPI:
    """Tests für Public API."""
    
    def test_set_document(self, layout_controller):
        """set_document setzt Dokument."""
        doc = DocumentModel()
        layout_controller.set_document(doc)
        
        assert layout_controller.current_document is doc
        
    def test_apply_auto_layout(self, layout_controller_with_doc, sample_document):
        """apply_auto_layout wendet Layout an."""
        elements = sample_document.get_all_elements()
        original_positions = [(e.x, e.y) for e in elements]
        
        layout_controller_with_doc.apply_auto_layout()
        
        # Positions should have changed
        new_positions = [(e.x, e.y) for e in elements]
        assert new_positions != original_positions
        
    def test_align_elements(self, layout_controller_with_doc, sample_document):
        """align_elements richtet aus."""
        elements = sample_document.get_all_elements()
        element_ids = [e.element_id for e in elements]
        
        layout_controller_with_doc.align_elements(element_ids, "left")
        
        # All elements should have same x coordinate
        x_coords = [e.x for e in elements]
        assert len(set(x_coords)) == 1


# ===== Test String Representation =====

class TestStringRepresentation:
    """Tests für String-Repräsentation."""
    
    def test_repr_without_document(self, layout_controller):
        """__repr__ ohne Dokument."""
        result = repr(layout_controller)
        
        assert "no document" in result
        assert "elements=0" in result
        
    def test_repr_with_document(self, layout_controller_with_doc):
        """__repr__ mit Dokument."""
        result = repr(layout_controller_with_doc)
        
        assert "with document" in result
        assert "elements=4" in result
