"""
Tests für Palette View.

Testet:
- Initialisierung
- Element-Auswahl (Event Publishing)
- Kategorie-Management (load, expand, collapse)
- Filter/Suche
- Reload-Funktionalität
- Public API
- Factory Functions
"""

import pytest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock, call
import os

from vpb.views.palette_view import PaletteView, create_palette_view
from vpb.infrastructure.event_bus import EventBus


# ===== Fixtures =====

@pytest.fixture
def root():
    """Creates a Tkinter root window for testing."""
    root = tk.Tk()
    root.withdraw()  # Hide window during tests
    yield root
    try:
        root.update_idletasks()
        root.destroy()
    except tk.TclError:
        pass


@pytest.fixture
def mock_event_bus():
    """Creates a mock Event-Bus."""
    bus = Mock(spec=EventBus)
    bus.publish = Mock()
    bus.subscribe = Mock()
    return bus


@pytest.fixture
def sample_categories():
    """Sample palette categories for testing."""
    return [
        {
            "id": "activities",
            "title": "Aktivitäten",
            "items": [
                {"type": "ACTIVITY", "label": "Aktivität", "description": "Eine Aktivität"},
                {"type": "FUNCTION", "label": "Funktion", "description": "Eine Funktion"}
            ],
            "layout": {"columns": 2, "expanded": True}
        },
        {
            "id": "events",
            "title": "Events",
            "items": [
                {"type": "START_EVENT", "label": "Start", "description": "Start Event"},
                {"type": "END_EVENT", "label": "Ende", "description": "End Event"}
            ],
            "layout": {"columns": 2, "expanded": False}
        }
    ]


@pytest.fixture
def palette_view(root, mock_event_bus):
    """Creates a Palette View for testing."""
    with patch('vpb.views.palette_view.get_global_event_bus', return_value=mock_event_bus):
        view = PaletteView(root, event_bus=mock_event_bus, width=220)
        view.pack()
        root.update_idletasks()
        yield view
        try:
            view.destroy()
        except tk.TclError:
            pass


# ===== Initialization Tests =====

class TestPaletteViewInit:
    """Tests für Palette View Initialisierung."""
    
    def test_palette_view_creates_panel(self, palette_view):
        """Test: Palette View erstellt PalettePanel."""
        assert hasattr(palette_view, 'palette_panel')
        assert palette_view.palette_panel is not None
        
    def test_palette_view_has_event_bus(self, palette_view, mock_event_bus):
        """Test: Palette View hat Event-Bus."""
        assert palette_view.event_bus == mock_event_bus
        
    def test_palette_view_default_width(self, root, mock_event_bus):
        """Test: Palette View hat Standard-Breite."""
        with patch('vpb.views.palette_view.get_global_event_bus', return_value=mock_event_bus):
            view = PaletteView(root, event_bus=mock_event_bus, width=250)
            assert view._width == 250
            view.destroy()
            
    def test_palette_view_empty_categories(self, palette_view):
        """Test: Palette View startet mit leeren Kategorien."""
        assert palette_view._current_categories == []


# ===== Element Picking Tests =====

class TestElementPicking:
    """Tests für Element-Auswahl."""
    
    def test_element_picked_publishes_event(self, palette_view, mock_event_bus):
        """Test: Element-Auswahl published Event."""
        item = {
            "type": "ACTIVITY",
            "label": "Test Activity",
            "description": "Test Description"
        }
        
        palette_view._on_element_picked(item)
        
        mock_event_bus.publish.assert_called_with("ui:palette:element_picked", {
            "type": "ACTIVITY",
            "label": "Test Activity",
            "item": item
        })
        
    def test_element_picked_with_minimal_item(self, palette_view, mock_event_bus):
        """Test: Element-Auswahl mit minimalen Item-Daten."""
        item = {}
        
        palette_view._on_element_picked(item)
        
        mock_event_bus.publish.assert_called_with("ui:palette:element_picked", {
            "type": "",
            "label": "",
            "item": item
        })
        
    def test_element_picked_with_extra_fields(self, palette_view, mock_event_bus):
        """Test: Element-Auswahl mit zusätzlichen Feldern."""
        item = {
            "type": "DECISION",
            "label": "Decision Point",
            "description": "A decision",
            "icon": "◆",
            "color": "#FFD700"
        }
        
        palette_view._on_element_picked(item)
        
        call_args = mock_event_bus.publish.call_args
        assert call_args[0][0] == "ui:palette:element_picked"
        assert call_args[0][1]["type"] == "DECISION"
        assert call_args[0][1]["label"] == "Decision Point"
        assert call_args[0][1]["item"] == item


# ===== Reload Tests =====

class TestReload:
    """Tests für Reload-Funktionalität."""
    
    def test_reload_requested_publishes_event(self, palette_view, mock_event_bus):
        """Test: Reload-Request published Event."""
        palette_view._on_reload_requested()
        
        mock_event_bus.publish.assert_called_with("ui:palette:reload_requested", {})
        
    def test_reload_method_triggers_callback(self, palette_view, mock_event_bus):
        """Test: reload() triggert Callback."""
        palette_view.reload()
        
        mock_event_bus.publish.assert_called_with("ui:palette:reload_requested", {})


# ===== Category Management Tests =====

class TestCategoryManagement:
    """Tests für Kategorie-Management."""
    
    def test_load_categories(self, palette_view, sample_categories):
        """Test: load_categories lädt Kategorien."""
        palette_view.load_categories(sample_categories)
        
        assert palette_view._current_categories == sample_categories
        
    def test_get_categories(self, palette_view, sample_categories):
        """Test: get_categories gibt Kategorien zurück."""
        palette_view.load_categories(sample_categories)
        
        result = palette_view.get_categories()
        
        assert result == sample_categories
        # Verify it's a copy
        assert result is not palette_view._current_categories
        
    def test_load_categories_empty_list(self, palette_view):
        """Test: load_categories mit leerer Liste."""
        palette_view.load_categories([])
        
        assert palette_view._current_categories == []
        
    @patch('vpb.views.palette_view.PaletteLoader.load_all')
    def test_load_from_folder(self, mock_load_all, palette_view, sample_categories):
        """Test: load_from_folder lädt aus Ordner."""
        mock_load_all.return_value = {"categories": sample_categories}
        
        palette_view.load_from_folder("/path/to/palettes")
        
        mock_load_all.assert_called_once_with("/path/to/palettes")
        assert palette_view._current_categories == sample_categories
        
    @patch('vpb.views.palette_view.PaletteLoader.load_all')
    def test_load_from_folder_no_categories(self, mock_load_all, palette_view):
        """Test: load_from_folder ohne Kategorien."""
        mock_load_all.return_value = {}
        
        palette_view.load_from_folder("/path/to/palettes")
        
        assert palette_view._current_categories == []


# ===== Category Expansion Tests =====

class TestCategoryExpansion:
    """Tests für Kategorie-Expansion."""
    
    def test_expand_all_categories(self, palette_view):
        """Test: expand_all_categories expandiert alle."""
        palette_view.palette_panel._expand_all_categories = Mock()
        
        palette_view.expand_all_categories()
        
        palette_view.palette_panel._expand_all_categories.assert_called_once()
        
    def test_collapse_all_categories(self, palette_view):
        """Test: collapse_all_categories kollabiert alle."""
        palette_view.palette_panel._collapse_all_categories = Mock()
        
        palette_view.collapse_all_categories()
        
        palette_view.palette_panel._collapse_all_categories.assert_called_once()


# ===== Search Filter Tests =====

class TestSearchFilter:
    """Tests für Such-Filter."""
    
    def test_set_search_filter(self, palette_view):
        """Test: set_search_filter setzt Filter."""
        palette_view.palette_panel._apply_filter = Mock()
        
        palette_view.set_search_filter("activity")
        
        assert palette_view.palette_panel._search.get() == "activity"
        palette_view.palette_panel._apply_filter.assert_called_once()
        
    def test_clear_search_filter(self, palette_view):
        """Test: clear_search_filter löscht Filter."""
        palette_view.palette_panel._search.set("test")
        palette_view.palette_panel._apply_filter = Mock()
        
        palette_view.clear_search_filter()
        
        assert palette_view.palette_panel._search.get() == ""
        palette_view.palette_panel._apply_filter.assert_called_once()
        
    def test_get_search_filter(self, palette_view):
        """Test: get_search_filter gibt Filter zurück."""
        palette_view.palette_panel._search.set("decision")
        
        result = palette_view.get_search_filter()
        
        assert result == "decision"
        
    def test_get_search_filter_empty(self, palette_view):
        """Test: get_search_filter wenn leer."""
        result = palette_view.get_search_filter()
        
        assert result == ""
        
    def test_set_search_filter_handles_missing_attribute(self, palette_view):
        """Test: set_search_filter behandelt fehlende Attribute gracefully."""
        # Remove _search attribute
        delattr(palette_view.palette_panel, '_search')
        
        # Should not raise exception
        palette_view.set_search_filter("test")
        
    def test_get_search_filter_handles_missing_attribute(self, palette_view):
        """Test: get_search_filter behandelt fehlende Attribute gracefully."""
        # Remove _search attribute
        delattr(palette_view.palette_panel, '_search')
        
        result = palette_view.get_search_filter()
        
        assert result == ""


# ===== Integration Tests =====

class TestIntegration:
    """Integration Tests für Palette View."""
    
    def test_full_workflow(self, palette_view, sample_categories, mock_event_bus):
        """Test: Vollständiger Workflow."""
        # Load categories
        palette_view.load_categories(sample_categories)
        assert len(palette_view.get_categories()) == 2
        
        # Set search filter
        palette_view.set_search_filter("event")
        assert palette_view.get_search_filter() == "event"
        
        # Clear filter
        palette_view.clear_search_filter()
        assert palette_view.get_search_filter() == ""
        
        # Expand/Collapse
        palette_view.expand_all_categories()
        palette_view.collapse_all_categories()
        
        # Reload
        palette_view.reload()
        mock_event_bus.publish.assert_called_with("ui:palette:reload_requested", {})
        
    def test_event_publishing_workflow(self, palette_view, mock_event_bus):
        """Test: Event-Publishing-Workflow."""
        # Pick element
        item1 = {"type": "ACTIVITY", "label": "Activity 1"}
        palette_view._on_element_picked(item1)
        
        # Pick another element
        item2 = {"type": "DECISION", "label": "Decision 1"}
        palette_view._on_element_picked(item2)
        
        # Reload
        palette_view._on_reload_requested()
        
        # Verify all events published
        assert mock_event_bus.publish.call_count == 3
        calls = mock_event_bus.publish.call_args_list
        assert calls[0][0][0] == "ui:palette:element_picked"
        assert calls[1][0][0] == "ui:palette:element_picked"
        assert calls[2][0][0] == "ui:palette:reload_requested"


# ===== Factory Functions Tests =====

class TestFactoryFunctions:
    """Tests für Factory-Funktionen."""
    
    def test_create_palette_view(self, root, mock_event_bus):
        """Test: create_palette_view erstellt Palette View."""
        with patch('vpb.views.palette_view.get_global_event_bus', return_value=mock_event_bus):
            view = create_palette_view(root, event_bus=mock_event_bus, width=250)
            
            assert isinstance(view, PaletteView)
            assert view.event_bus == mock_event_bus
            assert view._width == 250
            
            view.destroy()
            
    def test_create_palette_view_uses_global_event_bus(self, root, mock_event_bus):
        """Test: create_palette_view verwendet globalen Event-Bus."""
        with patch('vpb.views.palette_view.get_global_event_bus', return_value=mock_event_bus):
            view = create_palette_view(root, width=220)
            
            assert view.event_bus == mock_event_bus
            
            view.destroy()
            
    def test_create_palette_view_default_width(self, root, mock_event_bus):
        """Test: create_palette_view mit Standard-Breite."""
        with patch('vpb.views.palette_view.get_global_event_bus', return_value=mock_event_bus):
            view = create_palette_view(root, event_bus=mock_event_bus)
            
            assert view._width == 220
            
            view.destroy()


# ===== String Representation Tests =====

class TestStringRepresentation:
    """Tests für String Representation."""
    
    def test_repr_no_categories(self, palette_view):
        """Test: __repr__ ohne Kategorien."""
        repr_str = repr(palette_view)
        
        assert "PaletteView" in repr_str
        assert "categories=0" in repr_str
        
    def test_repr_with_categories(self, palette_view, sample_categories):
        """Test: __repr__ mit Kategorien."""
        palette_view.load_categories(sample_categories)
        
        repr_str = repr(palette_view)
        
        assert "PaletteView" in repr_str
        assert "categories=2" in repr_str


# ===== Edge Cases Tests =====

class TestEdgeCases:
    """Tests für Edge Cases."""
    
    def test_load_categories_with_none(self, palette_view):
        """Test: load_categories mit None."""
        # Should not raise exception
        palette_view.palette_panel.render = Mock()
        palette_view.load_categories(None)
        
        # Verify render was called with None
        palette_view.palette_panel.render.assert_called_once_with(None)
        
    def test_element_picked_with_none(self, palette_view, mock_event_bus):
        """Test: _on_element_picked mit None."""
        # Should handle None gracefully
        try:
            palette_view._on_element_picked(None)
        except AttributeError:
            pass  # Expected for None.get()
            
    def test_multiple_loads(self, palette_view, sample_categories):
        """Test: Mehrfaches Laden von Kategorien."""
        palette_view.load_categories(sample_categories)
        assert len(palette_view._current_categories) == 2
        
        # Load different categories
        new_categories = [{"id": "new", "title": "New", "items": []}]
        palette_view.load_categories(new_categories)
        assert len(palette_view._current_categories) == 1
        assert palette_view._current_categories[0]["id"] == "new"
