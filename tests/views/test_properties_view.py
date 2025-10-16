"""
Tests für PropertiesView.
"""

from __future__ import annotations

import pytest
import tkinter as tk
from unittest.mock import Mock, MagicMock, patch

from vpb.views.properties_view import PropertiesView, create_properties_view
from vpb.models import VPBElement, VPBConnection
from vpb.infrastructure.event_bus import EventBus


# ===== Fixtures =====

@pytest.fixture
def root():
    """Tkinter root window."""
    root = tk.Tk()
    yield root
    root.destroy()


@pytest.fixture
def mock_event_bus():
    """Mock Event-Bus."""
    return Mock(spec=EventBus)


@pytest.fixture
def properties_view(root, mock_event_bus):
    """Properties View mit Mock Event-Bus."""
    return PropertiesView(root, event_bus=mock_event_bus)


@pytest.fixture
def sample_element():
    """Sample VPBElement."""
    return VPBElement(
        element_id="E001",
        name="Test Element",
        element_type="ACTIVITY",
        x=100,
        y=100,
        description="Test description"
    )


@pytest.fixture
def sample_connection():
    """Sample VPBConnection."""
    return VPBConnection(
        connection_id="C001",
        source_element="E001",
        target_element="E002",
        connection_type="SEQUENTIAL"
    )


# ===== Test Initialization =====

class TestPropertiesViewInit:
    """Tests für PropertiesView Initialisierung."""
    
    def test_init_creates_properties_panel(self, root, mock_event_bus):
        """Initialisierung erstellt PropertiesPanel."""
        view = PropertiesView(root, event_bus=mock_event_bus)
        
        assert view.properties_panel is not None
        assert view.event_bus is mock_event_bus
        
    def test_init_without_event_bus(self, root):
        """Initialisierung ohne Event-Bus verwendet globalen Bus."""
        view = PropertiesView(root)
        
        assert view.event_bus is not None
        
    def test_init_with_custom_width(self, root, mock_event_bus):
        """Initialisierung mit custom width."""
        view = PropertiesView(root, event_bus=mock_event_bus, width=500)
        
        assert view._width == 500
        
    def test_initial_state_empty(self, properties_view):
        """Initial state ist leer."""
        assert properties_view.get_current_element() is None
        assert properties_view.get_current_connection() is None


# ===== Test Element Mode =====

class TestElementMode:
    """Tests für Element-Modus."""
    
    @patch('vpb.views.properties_view.PropertiesPanel')
    def test_set_element(self, mock_panel_class, root, mock_event_bus, sample_element):
        """set_element setzt Element."""
        view = PropertiesView(root, event_bus=mock_event_bus)
        
        view.set_element(sample_element)
        
        assert view.get_current_element() == sample_element
        assert view.get_current_connection() is None
        view.properties_panel.set_element.assert_called_once_with(sample_element)
        
    @patch('vpb.views.properties_view.PropertiesPanel')
    def test_set_element_clears_connection(self, mock_panel_class, root, mock_event_bus, sample_element):
        """set_element löscht Connection."""
        view = PropertiesView(root, event_bus=mock_event_bus)
        view._current_connection = Mock()
        
        view.set_element(sample_element)
        
        assert view.get_current_connection() is None
        
    @patch('vpb.views.properties_view.PropertiesPanel')
    def test_set_element_none(self, mock_panel_class, root, mock_event_bus):
        """set_element mit None."""
        view = PropertiesView(root, event_bus=mock_event_bus)
        
        view.set_element(None)
        
        assert view.get_current_element() is None
        view.properties_panel.set_element.assert_called_once_with(None)


# ===== Test Connection Mode =====

class TestConnectionMode:
    """Tests für Connection-Modus."""
    
    @patch('vpb.views.properties_view.PropertiesPanel')
    def test_set_connection(self, mock_panel_class, root, mock_event_bus, sample_connection):
        """set_connection setzt Connection."""
        view = PropertiesView(root, event_bus=mock_event_bus)
        
        view.set_connection(sample_connection)
        
        assert view.get_current_connection() == sample_connection
        assert view.get_current_element() is None
        view.properties_panel.set_element.assert_called_once_with(None, sample_connection)
        
    @patch('vpb.views.properties_view.PropertiesPanel')
    def test_set_connection_clears_element(self, mock_panel_class, root, mock_event_bus, sample_connection):
        """set_connection löscht Element."""
        view = PropertiesView(root, event_bus=mock_event_bus)
        view._current_element = Mock()
        
        view.set_connection(sample_connection)
        
        assert view.get_current_element() is None
        
    @patch('vpb.views.properties_view.PropertiesPanel')
    def test_set_connection_none(self, mock_panel_class, root, mock_event_bus):
        """set_connection mit None."""
        view = PropertiesView(root, event_bus=mock_event_bus)
        
        view.set_connection(None)
        
        assert view.get_current_connection() is None
        view.properties_panel.set_element.assert_called_once_with(None, None)


# ===== Test Hierarchy Mode =====

class TestHierarchyMode:
    """Tests für Hierarchie-Modus."""
    
    @patch('vpb.views.properties_view.PropertiesPanel')
    def test_set_hierarchy(self, mock_panel_class, root, mock_event_bus):
        """set_hierarchy setzt Hierarchie."""
        view = PropertiesView(root, event_bus=mock_event_bus)
        hierarchy_data = {"name": "Category 1", "color": "#FF0000"}
        
        view.set_hierarchy(0, hierarchy_data)
        
        assert view.get_current_element() is None
        assert view.get_current_connection() is None
        view.properties_panel.set_hierarchy.assert_called_once_with(0, hierarchy_data)
        
    @patch('vpb.views.properties_view.PropertiesPanel')
    def test_set_hierarchy_clears_element_and_connection(self, mock_panel_class, root, mock_event_bus):
        """set_hierarchy löscht Element und Connection."""
        view = PropertiesView(root, event_bus=mock_event_bus)
        view._current_element = Mock()
        view._current_connection = Mock()
        
        view.set_hierarchy(0, {})
        
        assert view.get_current_element() is None
        assert view.get_current_connection() is None


# ===== Test Clear =====

class TestClear:
    """Tests für Clear-Funktionalität."""
    
    @patch('vpb.views.properties_view.PropertiesPanel')
    def test_clear(self, mock_panel_class, root, mock_event_bus, sample_element):
        """clear löscht alle Anzeigen."""
        view = PropertiesView(root, event_bus=mock_event_bus)
        view._current_element = sample_element
        
        view.clear()
        
        assert view.get_current_element() is None
        assert view.get_current_connection() is None
        view.properties_panel.set_element.assert_called_with(None)


# ===== Test Callback Events =====

class TestCallbackEvents:
    """Tests für Callback-Events."""
    
    @patch('vpb.views.properties_view.PropertiesPanel')
    def test_on_apply_element(self, mock_panel_class, root, mock_event_bus, sample_element):
        """_on_apply publiziert element_changed Event."""
        view = PropertiesView(root, event_bus=mock_event_bus)
        view._current_element = sample_element
        
        values = {
            "kind": "element",
            "name": "New Name",
            "description": "New Description"
        }
        view._on_apply(values)
        
        mock_event_bus.publish.assert_called_once_with("ui:properties:element_changed", {
            "element": sample_element,
            "values": values
        })
        
    @patch('vpb.views.properties_view.PropertiesPanel')
    def test_on_apply_connection(self, mock_panel_class, root, mock_event_bus, sample_connection):
        """_on_apply publiziert connection_changed Event."""
        view = PropertiesView(root, event_bus=mock_event_bus)
        view._current_connection = sample_connection
        
        values = {
            "kind": "connection",
            "connection_type": "CONDITIONAL"
        }
        view._on_apply(values)
        
        mock_event_bus.publish.assert_called_once_with("ui:properties:connection_changed", {
            "connection": sample_connection,
            "values": values
        })
        
    @patch('vpb.views.properties_view.PropertiesPanel')
    def test_on_apply_hierarchy(self, mock_panel_class, root, mock_event_bus):
        """_on_apply publiziert hierarchy_changed Event."""
        view = PropertiesView(root, event_bus=mock_event_bus)
        
        values = {
            "kind": "hierarchy",
            "name": "Category 1",
            "color": "#FF0000"
        }
        view._on_apply(values)
        
        mock_event_bus.publish.assert_called_once_with("ui:properties:hierarchy_changed", {
            "values": values
        })
        
    @patch('vpb.views.properties_view.PropertiesPanel')
    def test_on_member_select(self, mock_panel_class, root, mock_event_bus):
        """_on_member_select publiziert member_selected Event."""
        view = PropertiesView(root, event_bus=mock_event_bus)
        
        view._on_member_select("E002")
        
        mock_event_bus.publish.assert_called_once_with("ui:properties:member_selected", {
            "element_id": "E002"
        })
        
    @patch('vpb.views.properties_view.PropertiesPanel')
    def test_on_group_add(self, mock_panel_class, root, mock_event_bus):
        """_on_group_add publiziert group_add_requested Event."""
        view = PropertiesView(root, event_bus=mock_event_bus)
        
        view._on_group_add("G001")
        
        mock_event_bus.publish.assert_called_once_with("ui:properties:group_add_requested", {
            "group_id": "G001"
        })
        
    @patch('vpb.views.properties_view.PropertiesPanel')
    def test_on_group_remove(self, mock_panel_class, root, mock_event_bus):
        """_on_group_remove publiziert group_remove_requested Event."""
        view = PropertiesView(root, event_bus=mock_event_bus)
        
        view._on_group_remove("G001")
        
        mock_event_bus.publish.assert_called_once_with("ui:properties:group_remove_requested", {
            "group_id": "G001"
        })
        
    @patch('vpb.views.properties_view.PropertiesPanel')
    def test_resolve_member_label(self, mock_panel_class, root, mock_event_bus):
        """_resolve_member_label gibt Element-ID als Fallback zurück."""
        view = PropertiesView(root, event_bus=mock_event_bus)
        
        label = view._resolve_member_label("E002")
        
        assert label == "E002"


# ===== Test Public API =====

class TestPublicAPI:
    """Tests für Public API."""
    
    @patch('vpb.views.properties_view.PropertiesPanel')
    def test_refresh_hierarchy_options(self, mock_panel_class, root, mock_event_bus):
        """refresh_hierarchy_options ruft PropertiesPanel-Methode auf."""
        view = PropertiesView(root, event_bus=mock_event_bus)
        names = ["Category 1", "Category 2", "Category 3"]
        
        view.refresh_hierarchy_options(names)
        
        view.properties_panel.refresh_hierarchy_options.assert_called_once_with(names)


# ===== Test String Representation =====

class TestStringRepresentation:
    """Tests für String-Repräsentation."""
    
    @patch('vpb.views.properties_view.PropertiesPanel')
    def test_repr_empty(self, mock_panel_class, root, mock_event_bus):
        """__repr__ für leeren Zustand."""
        view = PropertiesView(root, event_bus=mock_event_bus)
        
        result = repr(view)
        
        assert result == "<PropertiesView mode=empty>"
        
    @patch('vpb.views.properties_view.PropertiesPanel')
    def test_repr_with_element(self, mock_panel_class, root, mock_event_bus, sample_element):
        """__repr__ mit Element."""
        view = PropertiesView(root, event_bus=mock_event_bus)
        view._current_element = sample_element
        
        result = repr(view)
        
        assert result == "<PropertiesView mode=element element_id=E001>"
        
    @patch('vpb.views.properties_view.PropertiesPanel')
    def test_repr_with_connection(self, mock_panel_class, root, mock_event_bus, sample_connection):
        """__repr__ mit Connection."""
        view = PropertiesView(root, event_bus=mock_event_bus)
        view._current_connection = sample_connection
        
        result = repr(view)
        
        assert result == "<PropertiesView mode=connection connection_id=C001>"


# ===== Test Factory Functions =====

class TestFactoryFunctions:
    """Tests für Factory-Funktionen."""
    
    def test_create_properties_view(self, root, mock_event_bus):
        """create_properties_view erstellt PropertiesView."""
        view = create_properties_view(root, event_bus=mock_event_bus)
        
        assert isinstance(view, PropertiesView)
        assert view.event_bus is mock_event_bus
        
    def test_create_properties_view_with_width(self, root, mock_event_bus):
        """create_properties_view mit width."""
        view = create_properties_view(root, event_bus=mock_event_bus, width=500)
        
        assert view._width == 500
        
    def test_create_properties_view_without_event_bus(self, root):
        """create_properties_view ohne Event-Bus verwendet globalen Bus."""
        view = create_properties_view(root)
        
        assert view.event_bus is not None


# ===== Test Edge Cases =====

class TestEdgeCases:
    """Tests für Edge Cases."""
    
    @patch('vpb.views.properties_view.PropertiesPanel')
    def test_multiple_set_element_calls(self, mock_panel_class, root, mock_event_bus, sample_element):
        """Mehrfaches set_element überschreibt."""
        view = PropertiesView(root, event_bus=mock_event_bus)
        
        element2 = VPBElement(
            element_id="E002",
            name="Element 2",
            element_type="DECISION",
            x=200,
            y=200
        )
        
        view.set_element(sample_element)
        view.set_element(element2)
        
        assert view.get_current_element() == element2
        
    @patch('vpb.views.properties_view.PropertiesPanel')
    def test_multiple_set_connection_calls(self, mock_panel_class, root, mock_event_bus, sample_connection):
        """Mehrfaches set_connection überschreibt."""
        view = PropertiesView(root, event_bus=mock_event_bus)
        
        connection2 = VPBConnection(
            connection_id="C002",
            source_element="E003",
            target_element="E004",
            connection_type="CONDITIONAL"
        )
        
        view.set_connection(sample_connection)
        view.set_connection(connection2)
        
        assert view.get_current_connection() == connection2
        
    @patch('vpb.views.properties_view.PropertiesPanel')
    def test_on_apply_with_empty_kind(self, mock_panel_class, root, mock_event_bus):
        """_on_apply ohne kind verwendet 'element' als Default."""
        view = PropertiesView(root, event_bus=mock_event_bus)
        
        values = {"name": "Test"}  # kein 'kind' key
        view._on_apply(values)
        
        # Sollte element_changed publishen (da "element" der Default ist)
        mock_event_bus.publish.assert_called_once_with("ui:properties:element_changed", {
            "element": None,
            "values": values
        })
