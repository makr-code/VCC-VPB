"""
Tests für MenuBarView (vpb/views/menu_bar.py).

Testet die Menüleisten-Komponente des VPB Process Designers.

Test-Kategorien:
    - Initialization: MenuBar-Erstellung
    - Menu Creation: Menü-Struktur
    - Event Publishing: Action-Events
    - Setting Changes: Checkbutton/Radiobutton-Events
    - Public API: Getter/Setter
    - State Management: Save/Restore
    - Factory Functions: Hilfsfunktionen

Autor: GitHub Copilot (Phase 4: Views Layer)
"""

import pytest
import tkinter as tk
from unittest.mock import Mock, patch, call
from vpb.views.menu_bar import (
    MenuBarView,
    create_menu_bar,
    get_menu_bar_state,
    restore_menu_bar_state,
)


@pytest.fixture
def root():
    """Fixture für Tkinter Root-Widget."""
    root = tk.Tk()
    root.withdraw()  # Fenster verstecken
    yield root
    try:
        root.destroy()
    except tk.TclError:
        pass


@pytest.fixture
def mock_event_bus():
    """Fixture für Mock Event-Bus."""
    return Mock()


@pytest.fixture
def menu_bar(root, mock_event_bus):
    """Fixture für MenuBarView mit Mock Event-Bus."""
    return MenuBarView(root, mock_event_bus)


# ============================================================================
# Initialization Tests
# ============================================================================

class TestMenuBarInit:
    """Tests für MenuBarView Initialisierung."""
    
    def test_init_creates_menubar(self, root, mock_event_bus):
        """Test: __init__ erstellt MenuBar-Widget."""
        menu_bar = MenuBarView(root, mock_event_bus)
        
        assert menu_bar.menubar is not None
        assert isinstance(menu_bar.menubar, tk.Menu)
        assert menu_bar.event_bus == mock_event_bus
    
    def test_init_configures_parent_menu(self, root, mock_event_bus):
        """Test: __init__ konfiguriert Parent-Fenster mit MenuBar."""
        MenuBarView(root, mock_event_bus)
        
        # Parent sollte MenuBar zugewiesen haben
        assert root.cget('menu') != ''
    
    def test_init_uses_global_event_bus_if_none(self, root):
        """Test: __init__ nutzt globalen Event-Bus wenn keiner übergeben."""
        with patch('vpb.views.menu_bar.get_global_event_bus') as mock_get_bus:
            mock_bus = Mock()
            mock_get_bus.return_value = mock_bus
            
            menu_bar = MenuBarView(root)
            
            assert menu_bar.event_bus == mock_bus
            mock_get_bus.assert_called_once()
    
    def test_init_creates_all_menus(self, root, mock_event_bus):
        """Test: __init__ erstellt alle 8 Menüs."""
        menu_bar = MenuBarView(root, mock_event_bus)
        
        # MenuBar sollte 8 Top-Level-Menüs haben
        # (Datei, Bearbeiten, Anordnen, Ansicht, Werkzeuge, Einstellungen, AI, Hilfe)
        num_menus = menu_bar.menubar.index('end')
        assert num_menus >= 7  # Mindestens 8 Menüs (0-based index, also >= 7)


# ============================================================================
# Menu Structure Tests
# ============================================================================

class TestMenuStructure:
    """Tests für Menü-Struktur."""
    
    def test_file_menu_exists(self, menu_bar):
        """Test: Datei-Menü existiert."""
        menubar = menu_bar.menubar
        
        # Menüs haben Index >= 0 und Type 'cascade'
        # (Index 0 kann 'tearoff' sein auf manchen Systemen)
        num_menus = menubar.index('end')
        assert num_menus >= 7  # Mindestens 8 Menüs (0-based)
    
    def test_edit_menu_exists(self, menu_bar):
        """Test: Bearbeiten-Menü existiert."""
        menubar = menu_bar.menubar
        
        # Bearbeiten sollte das 2. Menü sein
        menu_type = menubar.type(1)
        assert menu_type == 'cascade'
    
    def test_arrange_menu_exists(self, menu_bar):
        """Test: Anordnen-Menü existiert."""
        menubar = menu_bar.menubar
        
        # Anordnen sollte das 3. Menü sein
        menu_type = menubar.type(2)
        assert menu_type == 'cascade'
    
    def test_view_menu_exists(self, menu_bar):
        """Test: Ansicht-Menü existiert."""
        menubar = menu_bar.menubar
        
        # Ansicht sollte das 4. Menü sein
        menu_type = menubar.type(3)
        assert menu_type == 'cascade'
    
    def test_tools_menu_exists(self, menu_bar):
        """Test: Werkzeuge-Menü existiert."""
        menubar = menu_bar.menubar
        
        # Werkzeuge sollte das 5. Menü sein
        menu_type = menubar.type(4)
        assert menu_type == 'cascade'
    
    def test_settings_menu_exists(self, menu_bar):
        """Test: Einstellungen-Menü existiert."""
        menubar = menu_bar.menubar
        
        # Einstellungen sollte das 6. Menü sein
        menu_type = menubar.type(5)
        assert menu_type == 'cascade'
    
    def test_ai_menu_exists(self, menu_bar):
        """Test: AI-Menü existiert."""
        menubar = menu_bar.menubar
        
        # AI sollte das 7. Menü sein
        menu_type = menubar.type(6)
        assert menu_type == 'cascade'
    
    def test_help_menu_exists(self, menu_bar):
        """Test: Hilfe-Menü existiert."""
        menubar = menu_bar.menubar
        
        # Hilfe sollte das 8. Menü sein (letztes)
        last_index = menubar.index('end')
        menu_type = menubar.type(last_index)
        assert menu_type == 'cascade'


# ============================================================================
# Event Publishing Tests
# ============================================================================

class TestEventPublishing:
    """Tests für Event-Publishing."""
    
    def test_publish_action_publishes_correct_event(self, menu_bar, mock_event_bus):
        """Test: _publish_action publiziert korrektes Event."""
        menu_bar._publish_action("file.new")
        
        mock_event_bus.publish.assert_called_once_with("ui:action:file.new", {})
    
    def test_publish_action_with_data(self, menu_bar, mock_event_bus):
        """Test: _publish_action übergibt Daten korrekt."""
        data = {"format": "png"}
        menu_bar._publish_action("file.export", data)
        
        mock_event_bus.publish.assert_called_once_with("ui:action:file.export", data)
    
    def test_publish_setting_changed(self, menu_bar, mock_event_bus):
        """Test: _publish_setting_changed publiziert Setting-Event."""
        menu_bar._publish_setting_changed("snap_to_grid", True)
        
        mock_event_bus.publish.assert_called_once_with(
            "ui:setting:changed",
            {"setting": "snap_to_grid", "value": True}
        )


# ============================================================================
# Setting Change Handler Tests
# ============================================================================

class TestSettingChangeHandlers:
    """Tests für Setting-Change-Handler."""
    
    def test_snap_to_grid_handler_publishes_event(self, menu_bar, mock_event_bus):
        """Test: Snap-to-Grid Handler publiziert Event."""
        menu_bar._snap_to_grid_var.set(True)
        menu_bar._on_snap_to_grid_changed()
        
        mock_event_bus.publish.assert_called_with(
            "ui:setting:changed",
            {"setting": "snap_to_grid", "value": True}
        )
    
    def test_show_grid_handler_publishes_event(self, menu_bar, mock_event_bus):
        """Test: Show-Grid Handler publiziert Event."""
        menu_bar._show_grid_var.set(False)
        menu_bar._on_show_grid_changed()
        
        mock_event_bus.publish.assert_called_with(
            "ui:setting:changed",
            {"setting": "show_grid", "value": False}
        )
    
    def test_routing_mode_handler_publishes_event(self, menu_bar, mock_event_bus):
        """Test: Routing-Mode Handler publiziert Event."""
        menu_bar._routing_mode_var.set("orthogonal")
        menu_bar._on_routing_mode_changed()
        
        mock_event_bus.publish.assert_called_with(
            "ui:setting:changed",
            {"setting": "routing_mode", "value": "orthogonal"}
        )
    
    def test_merge_snap_handler_publishes_event(self, menu_bar, mock_event_bus):
        """Test: Merge-Snap Handler publiziert Event."""
        menu_bar._merge_snap_var.set(False)
        menu_bar._on_merge_snap_changed()
        
        mock_event_bus.publish.assert_called_with(
            "ui:setting:changed",
            {"setting": "merge_snap", "value": False}
        )


# ============================================================================
# Public API Tests - Getters & Setters
# ============================================================================

class TestPublicAPI:
    """Tests für Public API (Getter/Setter)."""
    
    def test_set_snap_to_grid(self, menu_bar):
        """Test: set_snap_to_grid setzt Wert korrekt."""
        menu_bar.set_snap_to_grid(True)
        assert menu_bar.get_snap_to_grid() is True
        
        menu_bar.set_snap_to_grid(False)
        assert menu_bar.get_snap_to_grid() is False
    
    def test_set_show_grid(self, menu_bar):
        """Test: set_show_grid setzt Wert korrekt."""
        menu_bar.set_show_grid(True)
        assert menu_bar.get_show_grid() is True
        
        menu_bar.set_show_grid(False)
        assert menu_bar.get_show_grid() is False
    
    def test_set_show_timeline(self, menu_bar):
        """Test: set_show_timeline setzt Wert korrekt."""
        menu_bar.set_show_timeline(True)
        assert menu_bar.get_show_timeline() is True
        
        menu_bar.set_show_timeline(False)
        assert menu_bar.get_show_timeline() is False
    
    def test_set_routing_mode_valid(self, menu_bar):
        """Test: set_routing_mode setzt gültige Modi."""
        valid_modes = ["straight", "orthogonal", "curved", "smart", "smart-plus"]
        
        for mode in valid_modes:
            menu_bar.set_routing_mode(mode)
            assert menu_bar.get_routing_mode() == mode
    
    def test_set_routing_mode_invalid(self, menu_bar):
        """Test: set_routing_mode wirft Fehler bei ungültigem Modus."""
        with pytest.raises(ValueError, match="Invalid routing mode"):
            menu_bar.set_routing_mode("invalid-mode")
    
    def test_set_mousewheel_mode_valid(self, menu_bar):
        """Test: set_mousewheel_mode setzt gültige Modi."""
        menu_bar.set_mousewheel_mode("zoom-primary")
        assert menu_bar.get_mousewheel_mode() == "zoom-primary"
        
        menu_bar.set_mousewheel_mode("pan-primary")
        assert menu_bar.get_mousewheel_mode() == "pan-primary"
    
    def test_set_mousewheel_mode_invalid(self, menu_bar):
        """Test: set_mousewheel_mode wirft Fehler bei ungültigem Modus."""
        with pytest.raises(ValueError, match="Invalid mousewheel mode"):
            menu_bar.set_mousewheel_mode("invalid-mode")
    
    def test_set_merge_snap(self, menu_bar):
        """Test: set_merge_snap setzt Wert korrekt."""
        menu_bar.set_merge_snap(True)
        assert menu_bar.get_merge_snap() is True
        
        menu_bar.set_merge_snap(False)
        assert menu_bar.get_merge_snap() is False
    
    def test_set_merge_mode_valid(self, menu_bar):
        """Test: set_merge_mode setzt gültige Modi."""
        valid_modes = ["none", "fill-empty", "overwrite"]
        
        for mode in valid_modes:
            menu_bar.set_merge_mode(mode)
            assert menu_bar.get_merge_mode() == mode
    
    def test_set_merge_mode_invalid(self, menu_bar):
        """Test: set_merge_mode wirft Fehler bei ungültigem Modus."""
        with pytest.raises(ValueError, match="Invalid merge mode"):
            menu_bar.set_merge_mode("invalid-mode")
    
    def test_set_auto_rename(self, menu_bar):
        """Test: set_auto_rename setzt Wert korrekt."""
        menu_bar.set_auto_rename(True)
        assert menu_bar.get_auto_rename() is True
        
        menu_bar.set_auto_rename(False)
        assert menu_bar.get_auto_rename() is False


# ============================================================================
# State Management Tests
# ============================================================================

class TestStateManagement:
    """Tests für State-Management (Save/Restore)."""
    
    def test_get_menu_bar_state(self, menu_bar):
        """Test: get_menu_bar_state gibt vollständigen State zurück."""
        menu_bar.set_snap_to_grid(True)
        menu_bar.set_show_grid(False)
        menu_bar.set_routing_mode("orthogonal")
        
        state = get_menu_bar_state(menu_bar)
        
        assert state["snap_to_grid"] is True
        assert state["show_grid"] is False
        assert state["routing_mode"] == "orthogonal"
        assert "mousewheel_mode" in state
        assert "merge_snap" in state
        assert "merge_mode" in state
        assert "auto_rename" in state
    
    def test_restore_menu_bar_state_full(self, menu_bar):
        """Test: restore_menu_bar_state stellt vollständigen State wieder her."""
        state = {
            "snap_to_grid": True,
            "show_grid": False,
            "show_timeline": True,
            "routing_mode": "curved",
            "mousewheel_mode": "pan-primary",
            "merge_snap": False,
            "merge_mode": "overwrite",
            "auto_rename": False,
        }
        
        restore_menu_bar_state(menu_bar, state)
        
        assert menu_bar.get_snap_to_grid() is True
        assert menu_bar.get_show_grid() is False
        assert menu_bar.get_show_timeline() is True
        assert menu_bar.get_routing_mode() == "curved"
        assert menu_bar.get_mousewheel_mode() == "pan-primary"
        assert menu_bar.get_merge_snap() is False
        assert menu_bar.get_merge_mode() == "overwrite"
        assert menu_bar.get_auto_rename() is False
    
    def test_restore_menu_bar_state_partial(self, menu_bar):
        """Test: restore_menu_bar_state funktioniert mit partiellem State."""
        # Setze Defaults
        menu_bar.set_snap_to_grid(False)
        menu_bar.set_routing_mode("smart-plus")
        
        # Restore nur snap_to_grid
        state = {"snap_to_grid": True}
        restore_menu_bar_state(menu_bar, state)
        
        assert menu_bar.get_snap_to_grid() is True
        assert menu_bar.get_routing_mode() == "smart-plus"  # Unverändert


# ============================================================================
# Factory Function Tests
# ============================================================================

class TestFactoryFunctions:
    """Tests für Factory-Funktionen."""
    
    def test_create_menu_bar_returns_instance(self, root):
        """Test: create_menu_bar gibt MenuBarView-Instanz zurück."""
        with patch('vpb.views.menu_bar.get_global_event_bus') as mock_get_bus:
            mock_bus = Mock()
            mock_get_bus.return_value = mock_bus
            
            menu_bar = create_menu_bar(root)
            
            assert isinstance(menu_bar, MenuBarView)
            assert menu_bar.parent == root
    
    def test_create_menu_bar_with_event_bus(self, root, mock_event_bus):
        """Test: create_menu_bar akzeptiert Event-Bus Parameter."""
        menu_bar = create_menu_bar(root, mock_event_bus)
        
        assert menu_bar.event_bus == mock_event_bus
    
    def test_get_and_restore_state_roundtrip(self, menu_bar):
        """Test: get_menu_bar_state → restore_menu_bar_state Roundtrip."""
        # Setze spezifische Werte
        menu_bar.set_snap_to_grid(True)
        menu_bar.set_routing_mode("orthogonal")
        menu_bar.set_merge_mode("overwrite")
        
        # State speichern
        state = get_menu_bar_state(menu_bar)
        
        # Werte ändern
        menu_bar.set_snap_to_grid(False)
        menu_bar.set_routing_mode("straight")
        menu_bar.set_merge_mode("none")
        
        # State wiederherstellen
        restore_menu_bar_state(menu_bar, state)
        
        # Prüfe, ob ursprüngliche Werte wiederhergestellt
        assert menu_bar.get_snap_to_grid() is True
        assert menu_bar.get_routing_mode() == "orthogonal"
        assert menu_bar.get_merge_mode() == "overwrite"


# ============================================================================
# String Representation Tests
# ============================================================================

class TestStringRepresentation:
    """Tests für String-Repräsentation."""
    
    def test_repr(self, menu_bar):
        """Test: __repr__ gibt nützliche String-Repräsentation."""
        menu_bar.set_snap_to_grid(True)
        menu_bar.set_show_grid(False)
        menu_bar.set_routing_mode("orthogonal")
        
        repr_str = repr(menu_bar)
        
        assert "MenuBarView" in repr_str
        assert "snap_to_grid=True" in repr_str
        assert "show_grid=False" in repr_str
        assert "routing_mode=orthogonal" in repr_str
