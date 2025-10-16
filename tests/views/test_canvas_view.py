"""
Tests für Canvas View.

Testet:
- Initialisierung
- Widget-Erstellung (Canvas, Scrollbars)
- Event-Publishing (Mouse, Keyboard, Zoom/Pan)
- Public API (load_document, clear, redraw, zoom, pan, grid, selection)
- State Management
- Factory Functions
"""

import pytest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock, call

from vpb.views.canvas_view import CanvasView, create_canvas_view
from vpb.models import VPBElement, VPBConnection
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
def canvas_view(root, mock_event_bus):
    """Creates a Canvas View for testing."""
    with patch('vpb.views.canvas_view.get_global_event_bus', return_value=mock_event_bus):
        view = CanvasView(root, event_bus=mock_event_bus, width=800, height=600)
        view.pack()
        root.update_idletasks()
        yield view
        try:
            view.destroy()
        except tk.TclError:
            pass


# ===== Initialization Tests =====

class TestCanvasViewInit:
    """Tests für Canvas View Initialisierung."""
    
    def test_canvas_view_creates_widgets(self, canvas_view):
        """Test: Canvas View erstellt alle Widgets."""
        assert hasattr(canvas_view, 'canvas')
        assert hasattr(canvas_view, 'v_scrollbar')
        assert hasattr(canvas_view, 'h_scrollbar')
        assert isinstance(canvas_view.canvas, tk.Canvas)
        assert isinstance(canvas_view.v_scrollbar, tk.Scrollbar)
        assert isinstance(canvas_view.h_scrollbar, tk.Scrollbar)
        
    def test_canvas_view_has_event_bus(self, canvas_view, mock_event_bus):
        """Test: Canvas View hat Event-Bus."""
        assert canvas_view.event_bus == mock_event_bus
        
    def test_canvas_view_grid_layout(self, canvas_view, root):
        """Test: Canvas View verwendet Grid-Layout."""
        root.update_idletasks()
        # Canvas sollte in row=0, column=0 sein
        grid_info = canvas_view.canvas.grid_info()
        assert grid_info['row'] == 0
        assert grid_info['column'] == 0
        
    def test_canvas_view_scrollbars_configured(self, canvas_view):
        """Test: Scrollbars sind korrekt konfiguriert."""
        # Vertical scrollbar
        assert canvas_view.v_scrollbar.cget('orient') == 'vertical'
        # Horizontal scrollbar
        assert canvas_view.h_scrollbar.cget('orient') == 'horizontal'
        
    def test_canvas_view_default_dimensions(self, root, mock_event_bus):
        """Test: Canvas View hat Standard-Dimensionen."""
        with patch('vpb.views.canvas_view.get_global_event_bus', return_value=mock_event_bus):
            view = CanvasView(root, event_bus=mock_event_bus, width=1024, height=768)
            assert view._width == 1024
            assert view._height == 768
            view.destroy()


# ===== Event Publishing Tests =====

class TestEventPublishing:
    """Tests für Event-Publishing."""
    
    def test_left_click_publishes_event(self, canvas_view, mock_event_bus):
        """Test: Linksklick published Event."""
        event = Mock()
        event.x = 100
        event.y = 200
        event.widget = canvas_view.canvas
        
        canvas_view._on_left_click(event)
        
        mock_event_bus.publish.assert_called_with("ui:canvas:left_click", {
            "x": 100,
            "y": 200,
            "widget": canvas_view.canvas
        })
        
    def test_right_click_publishes_event(self, canvas_view, mock_event_bus):
        """Test: Rechtsklick published Event."""
        event = Mock()
        event.x = 150
        event.y = 250
        event.widget = canvas_view.canvas
        
        canvas_view._on_right_click(event)
        
        mock_event_bus.publish.assert_called_with("ui:canvas:right_click", {
            "x": 150,
            "y": 250,
            "widget": canvas_view.canvas
        })
        
    def test_double_click_publishes_event(self, canvas_view, mock_event_bus):
        """Test: Doppelklick published Event."""
        event = Mock()
        event.x = 120
        event.y = 220
        event.widget = canvas_view.canvas
        
        canvas_view._on_double_click(event)
        
        mock_event_bus.publish.assert_called_with("ui:canvas:double_click", {
            "x": 120,
            "y": 220,
            "widget": canvas_view.canvas
        })
        
    def test_drag_publishes_event(self, canvas_view, mock_event_bus):
        """Test: Drag published Event."""
        event = Mock()
        event.x = 130
        event.y = 230
        event.widget = canvas_view.canvas
        
        canvas_view._on_drag(event)
        
        mock_event_bus.publish.assert_called_with("ui:canvas:drag", {
            "x": 130,
            "y": 230,
            "widget": canvas_view.canvas
        })
        
    def test_release_publishes_event(self, canvas_view, mock_event_bus):
        """Test: Release published Event."""
        event = Mock()
        event.x = 140
        event.y = 240
        event.widget = canvas_view.canvas
        
        canvas_view._on_release(event)
        
        mock_event_bus.publish.assert_called_with("ui:canvas:release", {
            "x": 140,
            "y": 240,
            "widget": canvas_view.canvas
        })


# ===== Keyboard Event Tests =====

class TestKeyboardEvents:
    """Tests für Keyboard-Events."""
    
    def test_delete_key_publishes_event(self, canvas_view, mock_event_bus):
        """Test: Delete-Taste published Event."""
        event = Mock()
        result = canvas_view._on_delete_key(event)
        
        mock_event_bus.publish.assert_called_with("ui:action:edit.delete", {})
        assert result == "break"
        
    def test_undo_publishes_event(self, canvas_view, mock_event_bus):
        """Test: Ctrl+Z published Undo-Event."""
        event = Mock()
        result = canvas_view._on_undo(event)
        
        mock_event_bus.publish.assert_called_with("ui:action:edit.undo", {})
        assert result == "break"
        
    def test_redo_publishes_event(self, canvas_view, mock_event_bus):
        """Test: Ctrl+Y published Redo-Event."""
        event = Mock()
        result = canvas_view._on_redo(event)
        
        mock_event_bus.publish.assert_called_with("ui:action:edit.redo", {})
        assert result == "break"
        
    def test_copy_publishes_event(self, canvas_view, mock_event_bus):
        """Test: Ctrl+C published Copy-Event."""
        event = Mock()
        result = canvas_view._on_copy(event)
        
        mock_event_bus.publish.assert_called_with("ui:action:edit.copy", {})
        assert result == "break"
        
    def test_paste_publishes_event(self, canvas_view, mock_event_bus):
        """Test: Ctrl+V published Paste-Event."""
        event = Mock()
        result = canvas_view._on_paste(event)
        
        mock_event_bus.publish.assert_called_with("ui:action:edit.paste", {})
        assert result == "break"
        
    def test_cut_publishes_event(self, canvas_view, mock_event_bus):
        """Test: Ctrl+X published Cut-Event."""
        event = Mock()
        result = canvas_view._on_cut(event)
        
        mock_event_bus.publish.assert_called_with("ui:action:edit.cut", {})
        assert result == "break"
        
    def test_select_all_publishes_event(self, canvas_view, mock_event_bus):
        """Test: Ctrl+A published Select-All-Event."""
        event = Mock()
        result = canvas_view._on_select_all(event)
        
        mock_event_bus.publish.assert_called_with("ui:action:edit.select_all", {})
        assert result == "break"


# ===== Zoom/Pan Event Tests =====

class TestZoomPanEvents:
    """Tests für Zoom/Pan-Events."""
    
    def test_zoom_in_keyboard_publishes_event(self, canvas_view, mock_event_bus):
        """Test: Ctrl++ published Zoom-In-Event."""
        event = Mock()
        result = canvas_view._on_zoom_in(event)
        
        mock_event_bus.publish.assert_called_with("ui:action:view.zoom_in", {})
        assert result == "break"
        
    def test_zoom_out_keyboard_publishes_event(self, canvas_view, mock_event_bus):
        """Test: Ctrl+- published Zoom-Out-Event."""
        event = Mock()
        result = canvas_view._on_zoom_out(event)
        
        mock_event_bus.publish.assert_called_with("ui:action:view.zoom_out", {})
        assert result == "break"
        
    def test_zoom_reset_keyboard_publishes_event(self, canvas_view, mock_event_bus):
        """Test: Ctrl+0 published Zoom-Reset-Event."""
        event = Mock()
        result = canvas_view._on_zoom_reset(event)
        
        mock_event_bus.publish.assert_called_with("ui:action:view.zoom_reset", {})
        assert result == "break"
        
    def test_mousewheel_zoom_in_publishes_event(self, canvas_view, mock_event_bus):
        """Test: Mausrad aufwärts published Zoom-In-Event (bei zoom-primary)."""
        canvas_view.canvas.mousewheel_mode = "zoom-primary"
        event = Mock()
        event.x = 100
        event.y = 200
        event.delta = 120  # Positive = nach oben
        
        canvas_view._on_mousewheel(event)
        
        mock_event_bus.publish.assert_called_with("ui:canvas:zoom_in", {
            "x": 100,
            "y": 200,
            "delta": 120
        })
        
    def test_mousewheel_zoom_out_publishes_event(self, canvas_view, mock_event_bus):
        """Test: Mausrad abwärts published Zoom-Out-Event (bei zoom-primary)."""
        canvas_view.canvas.mousewheel_mode = "zoom-primary"
        event = Mock()
        event.x = 100
        event.y = 200
        event.delta = -120  # Negative = nach unten
        
        canvas_view._on_mousewheel(event)
        
        mock_event_bus.publish.assert_called_with("ui:canvas:zoom_out", {
            "x": 100,
            "y": 200,
            "delta": -120
        })
        
    def test_mousewheel_pan_mode(self, canvas_view, mock_event_bus):
        """Test: Mausrad bei pan-primary published Pan-Event."""
        canvas_view.canvas.mousewheel_mode = "pan-primary"
        event = Mock()
        event.x = 100
        event.y = 200
        event.delta = 120
        
        canvas_view._on_mousewheel(event)
        
        mock_event_bus.publish.assert_called_with("ui:canvas:pan_up", {
            "x": 100,
            "y": 200,
            "delta": 120
        })


# ===== Document API Tests =====

class TestDocumentAPI:
    """Tests für Document API."""
    
    def test_load_document(self, canvas_view):
        """Test: load_document lädt Dokument."""
        elements = [
            VPBElement(element_id="E001", element_type="ACTIVITY", x=100, y=100, name="Test")
        ]
        connections = [
            VPBConnection(connection_id="C001", source_element="E001", target_element="E002")
        ]
        metadata = {"name": "Test Process", "version": "1.0"}
        
        canvas_view.load_document(elements, connections, metadata)
        
        # Canvas sollte Elemente haben
        assert len(canvas_view.canvas.elements) > 0
        
    def test_get_document_data(self, canvas_view):
        """Test: get_document_data gibt Dokument-Daten zurück."""
        data = canvas_view.get_document_data()
        
        assert isinstance(data, dict)
        assert "elements" in data
        assert "connections" in data
        assert "metadata" in data
        
    def test_clear(self, canvas_view):
        """Test: clear löscht alle Elemente."""
        # Add some elements first
        canvas_view.canvas.elements = {"E001": Mock()}
        canvas_view.canvas.connections = {"C001": Mock()}
        
        canvas_view.clear()
        
        assert len(canvas_view.canvas.elements) == 0
        assert len(canvas_view.canvas.connections) == 0
        
    def test_redraw(self, canvas_view):
        """Test: redraw zeichnet Canvas neu."""
        # Mock redraw_all
        canvas_view.canvas.redraw_all = Mock()
        
        canvas_view.redraw()
        
        canvas_view.canvas.redraw_all.assert_called_once()


# ===== Zoom Control Tests =====

class TestZoomControl:
    """Tests für Zoom-Control."""
    
    def test_zoom_in(self, canvas_view):
        """Test: zoom_in vergrößert."""
        canvas_view.canvas.zoom_at_view = Mock()
        
        canvas_view.zoom_in(center_x=400, center_y=300)
        
        canvas_view.canvas.zoom_at_view.assert_called_once()
        args = canvas_view.canvas.zoom_at_view.call_args[0]
        assert args[0] == 1.2  # Zoom-Faktor
        assert args[1] == 400  # center_x
        assert args[2] == 300  # center_y
        
    def test_zoom_out(self, canvas_view):
        """Test: zoom_out verkleinert."""
        canvas_view.canvas.zoom_at_view = Mock()
        
        canvas_view.zoom_out(center_x=400, center_y=300)
        
        canvas_view.canvas.zoom_at_view.assert_called_once()
        args = canvas_view.canvas.zoom_at_view.call_args[0]
        assert abs(args[0] - (1.0 / 1.2)) < 0.01  # Zoom-Faktor
        
    def test_zoom_reset(self, canvas_view):
        """Test: zoom_reset setzt Zoom auf 100%."""
        canvas_view.canvas.view_scale = 2.0
        canvas_view.canvas.view_tx = 100.0
        canvas_view.canvas.view_ty = 200.0
        canvas_view.canvas.redraw_all = Mock()
        
        canvas_view.zoom_reset()
        
        assert canvas_view.canvas.view_scale == 1.0
        assert canvas_view.canvas.view_tx == 0.0
        assert canvas_view.canvas.view_ty == 0.0
        canvas_view.canvas.redraw_all.assert_called_once()
        
    def test_zoom_to_fit(self, canvas_view):
        """Test: zoom_to_fit zoomt auf alle Elemente."""
        canvas_view.canvas.fit_to_diagram = Mock()
        
        canvas_view.zoom_to_fit()
        
        canvas_view.canvas.fit_to_diagram.assert_called_once()
        
    def test_get_zoom_level(self, canvas_view):
        """Test: get_zoom_level gibt Zoom-Level zurück."""
        canvas_view.canvas.view_scale = 1.5
        
        level = canvas_view.get_zoom_level()
        
        assert level == 1.5
        
    def test_set_zoom_level(self, canvas_view):
        """Test: set_zoom_level setzt Zoom-Level."""
        canvas_view.canvas.redraw_all = Mock()
        
        canvas_view.set_zoom_level(2.0)
        
        assert canvas_view.canvas.view_scale == 2.0
        canvas_view.canvas.redraw_all.assert_called_once()
        
    def test_set_zoom_level_clamps_to_limits(self, canvas_view):
        """Test: set_zoom_level clampt auf Min/Max."""
        canvas_view.canvas._min_zoom = 0.1
        canvas_view.canvas._max_zoom = 5.0
        canvas_view.canvas.redraw_all = Mock()
        
        # Try to set below minimum
        canvas_view.set_zoom_level(0.05)
        assert canvas_view.canvas.view_scale == 0.1
        
        # Try to set above maximum
        canvas_view.set_zoom_level(10.0)
        assert canvas_view.canvas.view_scale == 5.0


# ===== Pan Control Tests =====

class TestPanControl:
    """Tests für Pan-Control."""
    
    def test_pan(self, canvas_view):
        """Test: pan verschiebt Ansicht."""
        canvas_view.canvas.pan_pixels = Mock()
        
        canvas_view.pan(100, 50)
        
        canvas_view.canvas.pan_pixels.assert_called_once_with(100, 50)
        
    def test_center_on_point(self, canvas_view):
        """Test: center_on_point zentriert auf Punkt."""
        canvas_view.canvas.to_view = Mock(return_value=(200, 150))
        canvas_view.canvas.pan_pixels = Mock()
        canvas_view.canvas.winfo_width = Mock(return_value=800)
        canvas_view.canvas.winfo_height = Mock(return_value=600)
        
        canvas_view.center_on_point(1000, 500)
        
        # Should calculate center and pan
        canvas_view.canvas.pan_pixels.assert_called_once()


# ===== Grid Control Tests =====

class TestGridControl:
    """Tests für Grid-Control."""
    
    def test_set_grid_visible(self, canvas_view):
        """Test: set_grid_visible setzt Grid-Sichtbarkeit."""
        canvas_view.canvas.redraw_all = Mock()
        
        canvas_view.set_grid_visible(True)
        
        assert canvas_view.canvas.grid_visible is True
        canvas_view.canvas.redraw_all.assert_called_once()
        
    def test_is_grid_visible(self, canvas_view):
        """Test: is_grid_visible gibt Grid-Sichtbarkeit zurück."""
        canvas_view.canvas.grid_visible = True
        assert canvas_view.is_grid_visible() is True
        
        canvas_view.canvas.grid_visible = False
        assert canvas_view.is_grid_visible() is False
        
    def test_set_snap_to_grid(self, canvas_view):
        """Test: set_snap_to_grid setzt Snap-to-Grid."""
        canvas_view.set_snap_to_grid(True)
        assert canvas_view.canvas.snap_to_grid is True
        
        canvas_view.set_snap_to_grid(False)
        assert canvas_view.canvas.snap_to_grid is False
        
    def test_is_snap_to_grid(self, canvas_view):
        """Test: is_snap_to_grid gibt Snap-to-Grid zurück."""
        canvas_view.canvas.snap_to_grid = True
        assert canvas_view.is_snap_to_grid() is True
        
        canvas_view.canvas.snap_to_grid = False
        assert canvas_view.is_snap_to_grid() is False
        
    def test_set_grid_size(self, canvas_view):
        """Test: set_grid_size setzt Grid-Größe."""
        canvas_view.canvas.redraw_all = Mock()
        
        canvas_view.set_grid_size(30)
        
        assert canvas_view.canvas.grid_size == 30
        canvas_view.canvas.redraw_all.assert_called_once()
        
    def test_set_grid_size_clamps_to_limits(self, canvas_view):
        """Test: set_grid_size clampt auf 5-100."""
        canvas_view.canvas.redraw_all = Mock()
        
        canvas_view.set_grid_size(3)  # Too small
        assert canvas_view.canvas.grid_size == 5
        
        canvas_view.set_grid_size(150)  # Too large
        assert canvas_view.canvas.grid_size == 100
        
    def test_get_grid_size(self, canvas_view):
        """Test: get_grid_size gibt Grid-Größe zurück."""
        canvas_view.canvas.grid_size = 25
        assert canvas_view.get_grid_size() == 25


# ===== Selection Tests =====

class TestSelection:
    """Tests für Selection API."""
    
    def test_get_selected_element(self, canvas_view):
        """Test: get_selected_element gibt ausgewähltes Element zurück."""
        element = VPBElement(element_id="E001", element_type="ACTIVITY", x=100, y=100, name="Test Activity")
        canvas_view.canvas.elements = {"E001": element}
        canvas_view.canvas.selected_id = "E001"
        
        selected = canvas_view.get_selected_element()
        
        assert selected == element
        
    def test_get_selected_element_none(self, canvas_view):
        """Test: get_selected_element gibt None wenn keine Auswahl."""
        canvas_view.canvas.selected_id = None
        
        selected = canvas_view.get_selected_element()
        
        assert selected is None
        
    def test_get_selected_elements(self, canvas_view):
        """Test: get_selected_elements gibt alle ausgewählten Elemente zurück."""
        el1 = VPBElement(element_id="E001", element_type="ACTIVITY", x=100, y=100, name="Activity 1")
        el2 = VPBElement(element_id="E002", element_type="DECISION", x=200, y=200, name="Decision 1")
        canvas_view.canvas.elements = {"E001": el1, "E002": el2}
        canvas_view.canvas.selected_ids = {"E001", "E002"}
        
        selected = canvas_view.get_selected_elements()
        
        assert len(selected) == 2
        assert el1 in selected
        assert el2 in selected
        
    def test_get_selected_connection(self, canvas_view):
        """Test: get_selected_connection gibt ausgewählte Verbindung zurück."""
        conn = VPBConnection(connection_id="C001", source_element="E001", target_element="E002")
        canvas_view.canvas.connections = {"C001": conn}
        canvas_view.canvas.selected_conn_id = "C001"
        
        selected = canvas_view.get_selected_connection()
        
        assert selected == conn
        
    def test_select_element(self, canvas_view):
        """Test: select_element wählt Element aus."""
        element = VPBElement(element_id="E001", element_type="ACTIVITY", x=100, y=100, name="Test Activity")
        canvas_view.canvas.elements = {"E001": element}
        canvas_view.canvas.redraw_all = Mock()
        
        canvas_view.select_element("E001")
        
        assert canvas_view.canvas.selected_id == "E001"
        assert "E001" in canvas_view.canvas.selected_ids
        assert canvas_view.canvas.selected_conn_id is None
        canvas_view.canvas.redraw_all.assert_called_once()
        
    def test_clear_selection(self, canvas_view):
        """Test: clear_selection löscht Auswahl."""
        canvas_view.canvas.selected_id = "E001"
        canvas_view.canvas.selected_ids = {"E001", "E002"}
        canvas_view.canvas.selected_conn_id = "C001"
        canvas_view.canvas.redraw_all = Mock()
        
        canvas_view.clear_selection()
        
        assert canvas_view.canvas.selected_id is None
        assert len(canvas_view.canvas.selected_ids) == 0
        assert canvas_view.canvas.selected_conn_id is None
        canvas_view.canvas.redraw_all.assert_called_once()


# ===== State Management Tests =====

class TestStateManagement:
    """Tests für State Management."""
    
    def test_get_canvas_state(self, canvas_view):
        """Test: get_canvas_state gibt Canvas-Zustand zurück."""
        canvas_view.canvas.view_scale = 1.5
        canvas_view.canvas.view_tx = 100.0
        canvas_view.canvas.view_ty = 200.0
        canvas_view.canvas.grid_visible = True
        canvas_view.canvas.snap_to_grid = True
        canvas_view.canvas.grid_size = 30
        canvas_view.canvas.mousewheel_mode = "pan-primary"
        canvas_view.canvas.routing_style = "orthogonal"
        
        state = canvas_view.get_canvas_state()
        
        assert state["zoom_level"] == 1.5
        assert state["view_tx"] == 100.0
        assert state["view_ty"] == 200.0
        assert state["grid_visible"] is True
        assert state["snap_to_grid"] is True
        assert state["grid_size"] == 30
        assert state["mousewheel_mode"] == "pan-primary"
        assert state["routing_style"] == "orthogonal"
        
    def test_restore_canvas_state(self, canvas_view):
        """Test: restore_canvas_state stellt Canvas-Zustand wieder her."""
        canvas_view.canvas.redraw_all = Mock()
        
        state = {
            "zoom_level": 2.0,
            "view_tx": 150.0,
            "view_ty": 250.0,
            "grid_visible": False,
            "snap_to_grid": False,
            "grid_size": 40,
            "mousewheel_mode": "zoom-primary",
            "routing_style": "curved"
        }
        
        canvas_view.restore_canvas_state(state)
        
        assert canvas_view.canvas.view_scale == 2.0
        assert canvas_view.canvas.view_tx == 150.0
        assert canvas_view.canvas.view_ty == 250.0
        assert canvas_view.canvas.grid_visible is False
        assert canvas_view.canvas.snap_to_grid is False
        assert canvas_view.canvas.grid_size == 40
        assert canvas_view.canvas.mousewheel_mode == "zoom-primary"
        assert canvas_view.canvas.routing_style == "curved"
        canvas_view.canvas.redraw_all.assert_called_once()
        
    def test_restore_canvas_state_partial(self, canvas_view):
        """Test: restore_canvas_state mit partiellem State."""
        canvas_view.canvas.redraw_all = Mock()
        
        state = {
            "zoom_level": 1.8,
            "grid_visible": False
        }
        
        canvas_view.restore_canvas_state(state)
        
        assert canvas_view.canvas.view_scale == 1.8
        assert canvas_view.canvas.grid_visible is False
        canvas_view.canvas.redraw_all.assert_called_once()


# ===== Focus Tests =====

class TestFocus:
    """Tests für Focus."""
    
    def test_focus(self, canvas_view):
        """Test: focus gibt Canvas Fokus."""
        canvas_view.canvas.focus_set = Mock()
        
        canvas_view.focus()
        
        canvas_view.canvas.focus_set.assert_called_once()


# ===== Factory Functions Tests =====

class TestFactoryFunctions:
    """Tests für Factory-Funktionen."""
    
    def test_create_canvas_view(self, root, mock_event_bus):
        """Test: create_canvas_view erstellt Canvas View."""
        with patch('vpb.views.canvas_view.get_global_event_bus', return_value=mock_event_bus):
            view = create_canvas_view(root, event_bus=mock_event_bus, width=1024, height=768)
            
            assert isinstance(view, CanvasView)
            assert view.event_bus == mock_event_bus
            assert view._width == 1024
            assert view._height == 768
            
            view.destroy()
            
    def test_create_canvas_view_uses_global_event_bus(self, root, mock_event_bus):
        """Test: create_canvas_view verwendet globalen Event-Bus."""
        with patch('vpb.views.canvas_view.get_global_event_bus', return_value=mock_event_bus):
            view = create_canvas_view(root, width=800, height=600)
            
            assert view.event_bus == mock_event_bus
            
            view.destroy()


# ===== String Representation Tests =====

class TestStringRepresentation:
    """Tests für String Representation."""
    
    def test_repr(self, canvas_view):
        """Test: __repr__ gibt sinnvolle Repräsentation zurück."""
        canvas_view.canvas.view_scale = 1.5
        canvas_view.canvas.elements = {"E001": Mock(), "E002": Mock()}
        canvas_view.canvas.connections = {"C001": Mock()}
        
        repr_str = repr(canvas_view)
        
        assert "CanvasView" in repr_str
        assert "1.50" in repr_str
        assert "elements=2" in repr_str
        assert "connections=1" in repr_str
