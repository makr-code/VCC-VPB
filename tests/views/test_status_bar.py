"""
Tests für StatusBarView (vpb/views/status_bar.py).

Testet die StatusBar-Komponente des VPB Process Designers.

Test-Kategorien:
    - Initialization: StatusBar-Erstellung
    - Message Management: set/get/clear
    - Info Management: center & right
    - Visibility: hide/show
    - Styling: Background, Font
    - Convenience: Coordinates, Zoom, Selection, Error, Success
    - State Management: Save/Restore
    - Factory Functions: create_status_bar

Autor: GitHub Copilot (Phase 4: Views Layer)
"""

import pytest
import tkinter as tk
from vpb.views.status_bar import (
    StatusBarView,
    create_status_bar,
    get_status_bar_state,
    restore_status_bar_state,
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
def statusbar(root):
    """Fixture für StatusBarView."""
    return StatusBarView(root)


# ============================================================================
# Initialization Tests
# ============================================================================

class TestStatusBarInit:
    """Tests für StatusBarView Initialisierung."""
    
    def test_init_creates_statusbar_frame(self, root):
        """Test: __init__ erstellt StatusBar Frame."""
        statusbar = StatusBarView(root)
        
        assert statusbar.statusbar is not None
        assert isinstance(statusbar.statusbar, tk.Frame)
    
    def test_init_packs_statusbar(self, root):
        """Test: __init__ packt StatusBar an BOTTOM."""
        statusbar = StatusBarView(root)
        
        # StatusBar sollte gepackt sein
        assert statusbar.statusbar.winfo_manager() == 'pack'
    
    def test_init_sets_default_background(self, root):
        """Test: __init__ setzt Standard-Hintergrundfarbe."""
        statusbar = StatusBarView(root)
        
        assert statusbar.get_background_color() == "#eeeeee"
    
    def test_init_with_custom_background(self, root):
        """Test: __init__ akzeptiert Custom-Hintergrundfarbe."""
        statusbar = StatusBarView(root, background_color="#ff0000")
        
        assert statusbar.get_background_color() == "#ff0000"
    
    def test_init_creates_three_labels(self, root):
        """Test: __init__ erstellt 3 Labels (left, center, right)."""
        statusbar = StatusBarView(root)
        
        assert statusbar.left_label is not None
        assert statusbar.center_label is not None
        assert statusbar.right_label is not None
    
    def test_init_sets_default_message(self, root):
        """Test: __init__ setzt Default-Message auf 'Bereit'."""
        statusbar = StatusBarView(root)
        
        assert statusbar.get_message() == "Bereit"


# ============================================================================
# Message Management Tests
# ============================================================================

class TestMessageManagement:
    """Tests für Message-Management (links)."""
    
    def test_set_message(self, statusbar):
        """Test: set_message setzt Status-Nachricht."""
        statusbar.set_message("Test-Nachricht")
        
        assert statusbar.get_message() == "Test-Nachricht"
    
    def test_get_message_returns_current(self, statusbar):
        """Test: get_message gibt aktuelle Nachricht zurück."""
        statusbar.set_message("Dokument gespeichert")
        
        assert statusbar.get_message() == "Dokument gespeichert"
    
    def test_clear_message_resets_to_bereit(self, statusbar):
        """Test: clear_message setzt auf 'Bereit' zurück."""
        statusbar.set_message("Test")
        statusbar.clear_message()
        
        assert statusbar.get_message() == "Bereit"
    
    def test_set_message_updates_label(self, statusbar):
        """Test: set_message aktualisiert Label-Text."""
        statusbar.set_message("Neuer Status")
        
        # StringVar sollte aktualisiert sein
        assert statusbar._left_var.get() == "Neuer Status"


# ============================================================================
# Info Management Tests
# ============================================================================

class TestInfoManagement:
    """Tests für Info-Management (center & right)."""
    
    def test_set_center_info(self, statusbar):
        """Test: set_center_info setzt Zusatzinfo."""
        statusbar.set_center_info("X: 100, Y: 200")
        
        assert statusbar.get_center_info() == "X: 100, Y: 200"
    
    def test_get_center_info_returns_current(self, statusbar):
        """Test: get_center_info gibt aktuelle Info zurück."""
        statusbar.set_center_info("Koordinaten")
        
        assert statusbar.get_center_info() == "Koordinaten"
    
    def test_clear_center_info(self, statusbar):
        """Test: clear_center_info löscht Zusatzinfo."""
        statusbar.set_center_info("Test")
        statusbar.clear_center_info()
        
        assert statusbar.get_center_info() == ""
    
    def test_set_right_info(self, statusbar):
        """Test: set_right_info setzt permanente Info."""
        statusbar.set_right_info("Zoom: 150%")
        
        assert statusbar.get_right_info() == "Zoom: 150%"
    
    def test_get_right_info_returns_current(self, statusbar):
        """Test: get_right_info gibt aktuelle Info zurück."""
        statusbar.set_right_info("Ollama: Online")
        
        assert statusbar.get_right_info() == "Ollama: Online"
    
    def test_clear_right_info(self, statusbar):
        """Test: clear_right_info löscht permanente Info."""
        statusbar.set_right_info("Test")
        statusbar.clear_right_info()
        
        assert statusbar.get_right_info() == ""
    
    def test_set_all(self, statusbar):
        """Test: set_all setzt mehrere Felder gleichzeitig."""
        statusbar.set_all(
            message="Status",
            center="Mitte",
            right="Rechts"
        )
        
        assert statusbar.get_message() == "Status"
        assert statusbar.get_center_info() == "Mitte"
        assert statusbar.get_right_info() == "Rechts"
    
    def test_set_all_partial(self, statusbar):
        """Test: set_all funktioniert mit partiellen Argumenten."""
        statusbar.set_message("Alt")
        statusbar.set_all(message="Neu")
        
        assert statusbar.get_message() == "Neu"
    
    def test_clear_all(self, statusbar):
        """Test: clear_all löscht alle Felder."""
        statusbar.set_all(
            message="Test1",
            center="Test2",
            right="Test3"
        )
        statusbar.clear_all()
        
        assert statusbar.get_message() == "Bereit"
        assert statusbar.get_center_info() == ""
        assert statusbar.get_right_info() == ""


# ============================================================================
# Visibility Tests
# ============================================================================

class TestVisibility:
    """Tests für Visibility-Management."""
    
    def test_hide_removes_statusbar(self, statusbar):
        """Test: hide() versteckt StatusBar."""
        statusbar.hide()
        
        assert not statusbar.is_visible()
    
    def test_show_displays_statusbar(self, statusbar):
        """Test: show() zeigt StatusBar wieder."""
        statusbar.hide()
        statusbar.show()
        
        # Nach show() sollte StatusBar wieder im Pack-Manager sein
        assert statusbar.statusbar.winfo_manager() == 'pack'
    
    def test_is_visible_initially_packed(self, statusbar):
        """Test: is_visible() prüft Pack-Status nach Initialisierung."""
        # StatusBar sollte gepackt sein
        assert statusbar.statusbar.winfo_manager() == 'pack'
    
    def test_is_visible_returns_false_after_hide(self, statusbar):
        """Test: is_visible() gibt False zurück nach hide()."""
        statusbar.hide()
        
        assert statusbar.is_visible() is False


# ============================================================================
# Styling Tests
# ============================================================================

class TestStyling:
    """Tests für Styling (Background, Font)."""
    
    def test_set_background_color(self, statusbar):
        """Test: set_background_color setzt Hintergrundfarbe."""
        statusbar.set_background_color("#123456")
        
        assert statusbar.get_background_color() == "#123456"
    
    def test_get_background_color_returns_default(self, statusbar):
        """Test: get_background_color gibt Standard-Farbe zurück."""
        color = statusbar.get_background_color()
        
        assert color == "#eeeeee"
    
    def test_set_background_color_updates_all_labels(self, statusbar):
        """Test: set_background_color aktualisiert alle Labels."""
        statusbar.set_background_color("#abcdef")
        
        assert statusbar.left_label.cget("bg") == "#abcdef"
        assert statusbar.center_label.cget("bg") == "#abcdef"
        assert statusbar.right_label.cget("bg") == "#abcdef"
    
    def test_set_font(self, statusbar):
        """Test: set_font setzt Schriftart für alle Labels."""
        font = ("Arial", 12, "bold")
        statusbar.set_font(font)
        
        # Prüfe, dass Font gesetzt wurde (Tkinter gibt tuple zurück)
        left_font = statusbar.left_label.cget("font")
        assert "Arial" in str(left_font)


# ============================================================================
# Convenience Methods Tests
# ============================================================================

class TestConvenienceMethods:
    """Tests für Convenience-Methoden."""
    
    def test_show_coordinates(self, statusbar):
        """Test: show_coordinates zeigt Koordinaten an."""
        statusbar.show_coordinates(100.5, 200.7)
        
        assert statusbar.get_center_info() == "X: 100, Y: 201"
    
    def test_show_zoom(self, statusbar):
        """Test: show_zoom zeigt Zoom-Level an."""
        statusbar.show_zoom(150.0)
        
        assert statusbar.get_right_info() == "Zoom: 150%"
    
    def test_show_selection_count_zero(self, statusbar):
        """Test: show_selection_count löscht bei 0."""
        statusbar.set_message("Alt")
        statusbar.show_selection_count(0)
        
        assert statusbar.get_message() == "Bereit"
    
    def test_show_selection_count_one(self, statusbar):
        """Test: show_selection_count zeigt '1 Element'."""
        statusbar.show_selection_count(1)
        
        assert statusbar.get_message() == "1 Element ausgewählt"
    
    def test_show_selection_count_multiple(self, statusbar):
        """Test: show_selection_count zeigt 'X Elemente'."""
        statusbar.show_selection_count(5)
        
        assert statusbar.get_message() == "5 Elemente ausgewählt"
    
    def test_show_error_adds_warning_icon(self, statusbar):
        """Test: show_error fügt Warning-Icon hinzu."""
        statusbar.show_error("Fehler aufgetreten")
        
        message = statusbar.get_message()
        assert "⚠️" in message
        assert "Fehler aufgetreten" in message
    
    def test_show_success_adds_checkmark(self, statusbar):
        """Test: show_success fügt Checkmark hinzu."""
        statusbar.show_success("Erfolgreich gespeichert")
        
        message = statusbar.get_message()
        assert "✓" in message
        assert "Erfolgreich gespeichert" in message


# ============================================================================
# State Management Tests
# ============================================================================

class TestStateManagement:
    """Tests für State-Management (Save/Restore)."""
    
    def test_get_status_bar_state(self, statusbar):
        """Test: get_status_bar_state gibt vollständigen State zurück."""
        statusbar.set_message("Test-Status")
        statusbar.set_center_info("Mitte")
        statusbar.set_right_info("Rechts")
        
        state = get_status_bar_state(statusbar)
        
        assert state["message"] == "Test-Status"
        assert state["center"] == "Mitte"
        assert state["right"] == "Rechts"
        assert "visible" in state
        assert "background" in state
    
    def test_restore_status_bar_state_full(self, statusbar):
        """Test: restore_status_bar_state stellt vollständigen State wieder her."""
        state = {
            "message": "Wiederhergestellt",
            "center": "X: 50",
            "right": "Zoom: 200%",
            "background": "#abcdef",
            "visible": True,
        }
        
        restore_status_bar_state(statusbar, state)
        
        assert statusbar.get_message() == "Wiederhergestellt"
        assert statusbar.get_center_info() == "X: 50"
        assert statusbar.get_right_info() == "Zoom: 200%"
        assert statusbar.get_background_color() == "#abcdef"
    
    def test_restore_status_bar_state_partial(self, statusbar):
        """Test: restore_status_bar_state funktioniert mit partiellem State."""
        statusbar.set_message("Alt")
        statusbar.set_right_info("Alt")
        
        state = {"message": "Neu"}
        restore_status_bar_state(statusbar, state)
        
        assert statusbar.get_message() == "Neu"
        assert statusbar.get_right_info() == "Alt"  # Unverändert
    
    def test_restore_status_bar_state_visibility(self, statusbar):
        """Test: restore_status_bar_state stellt Visibility wieder her."""
        state = {"visible": False}
        restore_status_bar_state(statusbar, state)
        
        assert statusbar.is_visible() is False


# ============================================================================
# Factory Function Tests
# ============================================================================

class TestFactoryFunctions:
    """Tests für Factory-Funktionen."""
    
    def test_create_status_bar_returns_instance(self, root):
        """Test: create_status_bar gibt StatusBarView-Instanz zurück."""
        statusbar = create_status_bar(root)
        
        assert isinstance(statusbar, StatusBarView)
        assert statusbar.parent == root
    
    def test_create_status_bar_with_custom_background(self, root):
        """Test: create_status_bar akzeptiert Background-Parameter."""
        statusbar = create_status_bar(root, background_color="#123456")
        
        assert statusbar.get_background_color() == "#123456"
    
    def test_create_status_bar_auto_packs(self, root):
        """Test: create_status_bar packt StatusBar automatisch."""
        statusbar = create_status_bar(root)
        
        assert statusbar.statusbar.winfo_manager() == 'pack'
    
    def test_get_and_restore_state_roundtrip(self, statusbar):
        """Test: get_status_bar_state → restore_status_bar_state Roundtrip."""
        # Setze spezifische Werte
        statusbar.set_message("Original")
        statusbar.set_center_info("Koordinaten")
        statusbar.set_right_info("Zoom: 100%")
        
        # State speichern
        state = get_status_bar_state(statusbar)
        
        # Werte ändern
        statusbar.clear_all()
        
        # State wiederherstellen
        restore_status_bar_state(statusbar, state)
        
        # Prüfe, ob ursprüngliche Werte wiederhergestellt
        assert statusbar.get_message() == "Original"
        assert statusbar.get_center_info() == "Koordinaten"
        assert statusbar.get_right_info() == "Zoom: 100%"


# ============================================================================
# String Representation Tests
# ============================================================================

class TestStringRepresentation:
    """Tests für String-Repräsentation."""
    
    def test_repr(self, statusbar):
        """Test: __repr__ gibt nützliche String-Repräsentation."""
        statusbar.set_message("Test-Status")
        repr_str = repr(statusbar)
        
        assert "StatusBarView" in repr_str
        assert "visible=" in repr_str
        assert "message=" in repr_str
        assert "bg=" in repr_str
    
    def test_repr_shows_message(self, statusbar):
        """Test: __repr__ zeigt aktuelle Message."""
        statusbar.set_message("Dokument gespeichert")
        repr_str = repr(statusbar)
        
        assert "Dokument gespeichert" in repr_str
    
    def test_repr_shows_background(self, statusbar):
        """Test: __repr__ zeigt Background-Color."""
        statusbar.set_background_color("#123456")
        repr_str = repr(statusbar)
        
        assert "bg=#123456" in repr_str
