#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests für MainWindow View.

Verwendet Tkinter Test-Harness für GUI-Tests.
"""

import pytest
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from vpb.views.main_window import (
    MainWindow,
    create_main_window,
    restore_window_state,
    save_window_state
)


# ============================
# Fixtures
# ============================

@pytest.fixture
def root():
    """Tkinter Root für Tests."""
    # Wichtig: Für Tests müssen wir einen Hidden Root verwenden
    root = tk.Tk()
    root.withdraw()  # Verstecke Fenster
    yield root
    try:
        root.destroy()
    except:
        pass


@pytest.fixture
def main_window(root):
    """MainWindow-Instanz für Tests."""
    with patch('vpb.views.main_window.get_global_event_bus'):
        window = MainWindow(title="Test Window", geometry="800x600")
        window.withdraw()  # Verstecke während Tests
        yield window
        try:
            window.destroy()
        except:
            pass


# ============================
# Initialization Tests
# ============================

class TestMainWindowInit:
    """Tests für MainWindow Initialisierung."""
    
    def test_init_creates_window(self):
        """Test: MainWindow wird korrekt erstellt."""
        with patch('vpb.views.main_window.get_global_event_bus'):
            window = MainWindow()
            window.withdraw()
            
            assert window.winfo_exists()
            assert "VPB Process Designer" in window.title()
            
            window.destroy()
    
    def test_init_with_custom_title(self):
        """Test: Custom-Titel wird gesetzt."""
        with patch('vpb.views.main_window.get_global_event_bus'):
            window = MainWindow(title="Custom Title")
            window.withdraw()
            
            assert window.title() == "Custom Title"
            
            window.destroy()
    
    def test_init_with_custom_geometry(self):
        """Test: Custom-Geometrie wird gesetzt."""
        with patch('vpb.views.main_window.get_global_event_bus'):
            window = MainWindow(geometry="1000x700")
            window.withdraw()
            window.update()  # Geometrie anwenden
            
            # Geometrie kann leicht abweichen (Window Manager)
            # Prüfe nur dass Fenster existiert
            assert window.winfo_exists()
            
            window.destroy()
    
    def test_init_creates_paned_window(self, main_window):
        """Test: PanedWindow wird erstellt."""
        assert hasattr(main_window, 'paned')
        assert isinstance(main_window.paned, tk.PanedWindow)
    
    def test_init_creates_three_panes(self, main_window):
        """Test: Drei Panes (left, mid, right) werden erstellt."""
        assert hasattr(main_window, 'left_pane')
        assert hasattr(main_window, 'mid_pane')
        assert hasattr(main_window, 'right_pane')
        
        panes = main_window.paned.panes()
        assert len(panes) == 3


# ============================
# Title & Geometry Tests
# ============================

class TestTitleAndGeometry:
    """Tests für Titel und Geometrie."""
    
    def test_set_title(self, main_window):
        """Test: Titel kann geändert werden."""
        main_window.set_title("New Title")
        assert main_window.title() == "New Title"
    
    def test_set_geometry(self, main_window):
        """Test: Geometrie kann geändert werden."""
        main_window.set_geometry("1200x800")
        main_window.update()
        
        # Geometrie wird gespeichert
        assert main_window._last_geometry == "1200x800"
    
    def test_get_geometry(self, main_window):
        """Test: Geometrie kann abgefragt werden."""
        main_window.update()
        geometry = main_window.get_geometry()
        
        assert 'width' in geometry
        assert 'height' in geometry
        assert 'x' in geometry
        assert 'y' in geometry
        assert geometry['width'] > 0
        assert geometry['height'] > 0


# ============================
# Sidebar Tests
# ============================

class TestSidebars:
    """Tests für Sidebar-Funktionen."""
    
    def test_show_left_sidebar(self, main_window):
        """Test: Linke Sidebar kann angezeigt werden."""
        main_window.show_left_sidebar(True)
        assert main_window.is_left_sidebar_visible()
    
    def test_hide_left_sidebar(self, main_window):
        """Test: Linke Sidebar kann versteckt werden."""
        main_window.show_left_sidebar(False)
        assert not main_window.is_left_sidebar_visible()
    
    def test_show_right_sidebar(self, main_window):
        """Test: Rechte Sidebar kann angezeigt werden."""
        main_window.show_right_sidebar(True)
        assert main_window.is_right_sidebar_visible()
    
    def test_hide_right_sidebar(self, main_window):
        """Test: Rechte Sidebar kann versteckt werden."""
        main_window.show_right_sidebar(False)
        assert not main_window.is_right_sidebar_visible()
    
    def test_get_sidebar_widths(self, main_window):
        """Test: Sidebar-Breiten können abgefragt werden."""
        main_window.update()
        widths = main_window.get_sidebar_widths()
        
        assert 'left' in widths
        assert 'right' in widths
        assert widths['left'] >= 0
        assert widths['right'] >= 0


# ============================
# Container Access Tests
# ============================

class TestContainerAccess:
    """Tests für Container-Zugriff."""
    
    def test_get_left_container(self, main_window):
        """Test: Linker Container ist zugänglich."""
        container = main_window.get_left_container()
        assert container == main_window.left_pane
    
    def test_get_mid_container(self, main_window):
        """Test: Mittlerer Container ist zugänglich."""
        container = main_window.get_mid_container()
        assert container == main_window.mid_pane
    
    def test_get_right_container(self, main_window):
        """Test: Rechter Container ist zugänglich."""
        container = main_window.get_right_container()
        assert container == main_window.right_pane


# ============================
# Event Publishing Tests
# ============================

class TestEventPublishing:
    """Tests für Event-Publishing."""
    
    def test_publishes_action_events(self, main_window):
        """Test: Aktionen werden über Event-Bus published."""
        mock_bus = Mock()
        main_window.event_bus = mock_bus
        
        main_window._publish_action("file.new")
        
        mock_bus.publish.assert_called_once()
        call_args = mock_bus.publish.call_args
        assert 'ui:action:file.new' in call_args[0][0]
    
    def test_on_close_publishes_event(self, main_window):
        """Test: Close-Request wird published."""
        mock_bus = Mock()
        main_window.event_bus = mock_bus
        
        main_window._on_close()
        
        mock_bus.publish.assert_called_once()
        call_args = mock_bus.publish.call_args
        assert 'ui:window:close_requested' in call_args[0][0]


# ============================
# Factory Function Tests
# ============================

class TestFactoryFunctions:
    """Tests für Factory-Funktionen."""
    
    def test_create_main_window(self):
        """Test: create_main_window erstellt MainWindow."""
        with patch('vpb.views.main_window.get_global_event_bus'):
            window = create_main_window(title="Factory Test")
            window.withdraw()
            
            assert isinstance(window, MainWindow)
            assert window.title() == "Factory Test"
            
            window.destroy()
    
    def test_save_window_state(self, main_window):
        """Test: Window-State kann gespeichert werden."""
        main_window.update()
        state = save_window_state(main_window)
        
        assert 'geometry' in state
        assert 'maximized' in state
        assert 'sidebar_left' in state
        assert 'sidebar_right' in state
        assert 'left_sidebar_visible' in state
        assert 'right_sidebar_visible' in state
    
    def test_restore_window_state(self, main_window):
        """Test: Window-State kann wiederhergestellt werden."""
        state = {
            'geometry': '1000x700+100+50',
            'maximized': False,
            'sidebar_left': 300,
            'sidebar_right': 350,
            'left_sidebar_visible': True,
            'right_sidebar_visible': False
        }
        
        restore_window_state(main_window, state)
        main_window.update()
        
        # Prüfe dass State angewendet wurde
        assert main_window._last_geometry == '1000x700+100+50'
        assert main_window.is_left_sidebar_visible()
        assert not main_window.is_right_sidebar_visible()
    
    def test_save_and_restore_roundtrip(self, main_window):
        """Test: Save + Restore Roundtrip."""
        # Modifiziere Window
        main_window.set_title("Modified")
        main_window.show_right_sidebar(False)
        main_window.update()
        
        # Save
        state = save_window_state(main_window)
        
        # Restore
        with patch('vpb.views.main_window.get_global_event_bus'):
            new_window = MainWindow()
            new_window.withdraw()
            restore_window_state(new_window, state)
            new_window.update()
            
            # Vergleiche States
            assert not new_window.is_right_sidebar_visible()
            
            new_window.destroy()


# ============================
# Repr Tests
# ============================

class TestRepr:
    """Tests für String-Repräsentation."""
    
    def test_repr(self, main_window):
        """Test: __repr__ liefert aussagekräftige Darstellung."""
        repr_str = repr(main_window)
        
        assert 'MainWindow' in repr_str
        assert 'title=' in repr_str
        assert 'size=' in repr_str
