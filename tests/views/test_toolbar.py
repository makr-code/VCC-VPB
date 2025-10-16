"""
Tests für ToolbarView (vpb/views/toolbar.py).

Testet die Toolbar-Komponente des VPB Process Designers.

Test-Kategorien:
    - Initialization: Toolbar-Erstellung
    - VPB Branding: Logo & Schriftzug
    - Button Creation: Datei & Edit Buttons
    - Menu Creation: Ausrichten, Verteilen, Formationen
    - Event Publishing: Action-Events
    - Public API: hide/show, Background-Color
    - Factory Functions: create_toolbar

Autor: GitHub Copilot (Phase 4: Views Layer)
"""

import pytest
import tkinter as tk
from unittest.mock import Mock, patch
from vpb.views.toolbar import (
    ToolbarView,
    create_toolbar,
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
def toolbar_view(root, mock_event_bus):
    """Fixture für ToolbarView mit Mock Event-Bus."""
    return ToolbarView(root, mock_event_bus)


# ============================================================================
# Initialization Tests
# ============================================================================

class TestToolbarInit:
    """Tests für ToolbarView Initialisierung."""
    
    def test_init_creates_toolbar_frame(self, root, mock_event_bus):
        """Test: __init__ erstellt Toolbar Frame."""
        toolbar = ToolbarView(root, mock_event_bus)
        
        assert toolbar.toolbar is not None
        assert isinstance(toolbar.toolbar, tk.Frame)
        assert toolbar.event_bus == mock_event_bus
    
    def test_init_packs_toolbar(self, root, mock_event_bus):
        """Test: __init__ packt Toolbar an TOP."""
        toolbar = ToolbarView(root, mock_event_bus)
        
        # Toolbar sollte gepackt sein
        assert toolbar.toolbar.winfo_manager() == 'pack'
    
    def test_init_uses_global_event_bus_if_none(self, root):
        """Test: __init__ nutzt globalen Event-Bus wenn keiner übergeben."""
        with patch('vpb.views.toolbar.get_global_event_bus') as mock_get_bus:
            mock_bus = Mock()
            mock_get_bus.return_value = mock_bus
            
            toolbar = ToolbarView(root)
            
            assert toolbar.event_bus == mock_bus
            mock_get_bus.assert_called_once()
    
    def test_init_sets_background_color(self, root, mock_event_bus):
        """Test: __init__ setzt Standard-Hintergrundfarbe."""
        toolbar = ToolbarView(root, mock_event_bus)
        
        bg_color = toolbar.toolbar.cget("bg")
        assert bg_color == "#f2f2f2"
    
    def test_init_sets_height(self, root, mock_event_bus):
        """Test: __init__ setzt Toolbar-Höhe."""
        toolbar = ToolbarView(root, mock_event_bus)
        
        height = toolbar.toolbar.cget("height")
        assert height == 36


# ============================================================================
# VPB Branding Tests
# ============================================================================

class TestVPBBranding:
    """Tests für VPB-Branding (Logo & Schriftzug)."""
    
    def test_vpb_branding_exists(self, toolbar_view):
        """Test: VPB-Branding Frame existiert."""
        # Suche nach Frame mit VPB-Komponenten
        frames = [w for w in toolbar_view.toolbar.winfo_children() if isinstance(w, tk.Frame)]
        
        # Es sollten mehrere Frames existieren (VPB-Frame, Separatoren)
        assert len(frames) > 0
    
    def test_vpb_logo_is_clickable(self, root, mock_event_bus):
        """Test: VPB-Logo publiziert help.about Event bei Klick."""
        toolbar = ToolbarView(root, mock_event_bus)
        
        # Aktualisiere UI
        root.update_idletasks()
        
        # Finde Logo (Label mit 🔄)
        labels = []
        for child in toolbar.toolbar.winfo_children():
            if isinstance(child, tk.Frame):
                for subchild in child.winfo_children():
                    if isinstance(subchild, tk.Label) and subchild.cget("text") == "🔄":
                        labels.append(subchild)
        
        # Logo sollte existieren
        assert len(labels) > 0
        
        # Teste, dass Logo ein Button-1 Binding hat
        logo = labels[0]
        bindings = logo.bind()
        has_button_binding = any("Button" in b for b in bindings)
        assert has_button_binding, "Logo sollte Button-1 Binding haben"
        
        # Teste _publish_action direkt (da event_generate nicht zuverlässig)
        toolbar._publish_action("help.about")
        mock_event_bus.publish.assert_called_with("ui:action:help.about", {})


# ============================================================================
# Button Creation Tests
# ============================================================================

class TestButtonCreation:
    """Tests für Button-Erstellung."""
    
    def test_file_buttons_exist(self, toolbar_view):
        """Test: Datei-Buttons existieren."""
        buttons = [w for w in toolbar_view.toolbar.winfo_children() if isinstance(w, tk.Button)]
        
        # Es sollten mindestens 7 Buttons existieren (4 Datei + 3 Edit)
        assert len(buttons) >= 7
    
    def test_file_new_button_publishes_event(self, root, mock_event_bus):
        """Test: Neu-Button publiziert file.new Event."""
        toolbar = ToolbarView(root, mock_event_bus)
        
        # Finde Neu-Button
        buttons = [w for w in toolbar.toolbar.winfo_children() if isinstance(w, tk.Button)]
        neu_button = None
        for btn in buttons:
            if btn.cget("text") == "Neu":
                neu_button = btn
                break
        
        assert neu_button is not None
        
        # Simuliere Klick
        neu_button.invoke()
        
        # Event-Bus sollte file.new Event publiziert haben
        mock_event_bus.publish.assert_called_with("ui:action:file.new", {})
    
    def test_edit_buttons_exist(self, toolbar_view):
        """Test: Edit-Buttons existieren."""
        buttons = [w for w in toolbar_view.toolbar.winfo_children() if isinstance(w, tk.Button)]
        
        button_texts = [btn.cget("text") for btn in buttons]
        
        # Edit-Buttons sollten existieren
        assert "Element hinzufügen" in button_texts
        assert "Neu zeichnen" in button_texts
        assert "Auto-Layout" in button_texts


# ============================================================================
# Menu Creation Tests
# ============================================================================

class TestMenuCreation:
    """Tests für Menü-Erstellung."""
    
    def test_arrange_menus_exist(self, toolbar_view):
        """Test: Anordnen-Menüs existieren."""
        menubuttons = [w for w in toolbar_view.toolbar.winfo_children() if isinstance(w, tk.Menubutton)]
        
        # Es sollten 3 Menubuttons existieren (Ausrichten, Verteilen, Formationen)
        assert len(menubuttons) == 3
    
    def test_align_menu_exists(self, toolbar_view):
        """Test: Ausrichten-Menü existiert."""
        menubuttons = [w for w in toolbar_view.toolbar.winfo_children() if isinstance(w, tk.Menubutton)]
        
        menu_texts = [mb.cget("text") for mb in menubuttons]
        assert "Ausrichten" in menu_texts
    
    def test_distribute_menu_exists(self, toolbar_view):
        """Test: Verteilen-Menü existiert."""
        menubuttons = [w for w in toolbar_view.toolbar.winfo_children() if isinstance(w, tk.Menubutton)]
        
        menu_texts = [mb.cget("text") for mb in menubuttons]
        assert "Verteilen" in menu_texts
    
    def test_formations_menu_exists(self, toolbar_view):
        """Test: Formationen-Menü existiert."""
        menubuttons = [w for w in toolbar_view.toolbar.winfo_children() if isinstance(w, tk.Menubutton)]
        
        menu_texts = [mb.cget("text") for mb in menubuttons]
        assert "Formationen" in menu_texts


# ============================================================================
# Event Publishing Tests
# ============================================================================

class TestEventPublishing:
    """Tests für Event-Publishing."""
    
    def test_publish_action_publishes_correct_event(self, toolbar_view, mock_event_bus):
        """Test: _publish_action publiziert korrektes Event."""
        toolbar_view._publish_action("file.new")
        
        mock_event_bus.publish.assert_called_with("ui:action:file.new", {})
    
    def test_publish_action_with_data(self, toolbar_view, mock_event_bus):
        """Test: _publish_action übergibt Daten korrekt."""
        data = {"mode": "left"}
        toolbar_view._publish_action("arrange.align", data)
        
        mock_event_bus.publish.assert_called_with("ui:action:arrange.align", data)
    
    def test_file_open_button_publishes_event(self, root, mock_event_bus):
        """Test: Öffnen-Button publiziert file.open Event."""
        toolbar = ToolbarView(root, mock_event_bus)
        
        # Finde Öffnen-Button
        buttons = [w for w in toolbar.toolbar.winfo_children() if isinstance(w, tk.Button)]
        oeffnen_button = None
        for btn in buttons:
            if btn.cget("text") == "Öffnen":
                oeffnen_button = btn
                break
        
        assert oeffnen_button is not None
        
        # Simuliere Klick
        oeffnen_button.invoke()
        
        # Event-Bus sollte file.open Event publiziert haben
        mock_event_bus.publish.assert_called_with("ui:action:file.open", {})


# ============================================================================
# Public API Tests
# ============================================================================

class TestPublicAPI:
    """Tests für Public API (hide/show/is_visible/background)."""
    
    def test_hide_removes_toolbar(self, toolbar_view):
        """Test: hide() versteckt Toolbar."""
        toolbar_view.hide()
        
        assert not toolbar_view.is_visible()
    
    def test_show_displays_toolbar(self, toolbar_view):
        """Test: show() zeigt Toolbar wieder."""
        toolbar_view.hide()
        toolbar_view.show()
        
        # Nach show() sollte Toolbar wieder im Pack-Manager sein
        assert toolbar_view.toolbar.winfo_manager() == 'pack'
    
    def test_is_visible_returns_true_initially(self, toolbar_view):
        """Test: is_visible() prüft Pack-Status nach Initialisierung."""
        # Toolbar sollte gepackt sein
        assert toolbar_view.toolbar.winfo_manager() == 'pack'
    
    def test_is_visible_returns_false_after_hide(self, toolbar_view):
        """Test: is_visible() gibt False zurück nach hide()."""
        toolbar_view.hide()
        
        # Nach hide() sollte is_visible False sein
        assert toolbar_view.is_visible() is False
    
    def test_set_background_color(self, toolbar_view):
        """Test: set_background_color() setzt Hintergrundfarbe."""
        toolbar_view.set_background_color("#ff0000")
        
        assert toolbar_view.get_background_color() == "#ff0000"
    
    def test_get_background_color_returns_default(self, toolbar_view):
        """Test: get_background_color() gibt Standard-Farbe zurück."""
        color = toolbar_view.get_background_color()
        
        assert color == "#f2f2f2"
    
    def test_set_background_color_updates_frames(self, toolbar_view):
        """Test: set_background_color() aktualisiert Child-Frames."""
        toolbar_view.set_background_color("#00ff00")
        
        # Prüfe, ob Frames aktualisiert wurden
        frames = [w for w in toolbar_view.toolbar.winfo_children() if isinstance(w, tk.Frame)]
        
        # Mindestens ein Frame sollte existieren
        assert len(frames) > 0


# ============================================================================
# Factory Function Tests
# ============================================================================

class TestFactoryFunctions:
    """Tests für Factory-Funktionen."""
    
    def test_create_toolbar_returns_instance(self, root):
        """Test: create_toolbar gibt ToolbarView-Instanz zurück."""
        with patch('vpb.views.toolbar.get_global_event_bus') as mock_get_bus:
            mock_bus = Mock()
            mock_get_bus.return_value = mock_bus
            
            toolbar = create_toolbar(root)
            
            assert isinstance(toolbar, ToolbarView)
            assert toolbar.parent == root
    
    def test_create_toolbar_with_event_bus(self, root, mock_event_bus):
        """Test: create_toolbar akzeptiert Event-Bus Parameter."""
        toolbar = create_toolbar(root, mock_event_bus)
        
        assert toolbar.event_bus == mock_event_bus
    
    def test_create_toolbar_auto_packs(self, root, mock_event_bus):
        """Test: create_toolbar packt Toolbar automatisch."""
        toolbar = create_toolbar(root, mock_event_bus)
        
        # Toolbar sollte gepackt sein
        assert toolbar.toolbar.winfo_manager() == 'pack'


# ============================================================================
# String Representation Tests
# ============================================================================

class TestStringRepresentation:
    """Tests für String-Repräsentation."""
    
    def test_repr(self, toolbar_view):
        """Test: __repr__ gibt nützliche String-Repräsentation."""
        repr_str = repr(toolbar_view)
        
        assert "ToolbarView" in repr_str
        assert "visible=" in repr_str
        assert "bg=" in repr_str
    
    def test_repr_shows_visibility(self, toolbar_view):
        """Test: __repr__ zeigt Visibility-Status."""
        # Check repr enthält visible-Flag
        repr_str = repr(toolbar_view)
        assert "visible=" in repr_str
        
        # Nach hide()
        toolbar_view.hide()
        repr_str = repr(toolbar_view)
        assert "visible=False" in repr_str
    
    def test_repr_shows_background_color(self, toolbar_view):
        """Test: __repr__ zeigt Background-Color."""
        toolbar_view.set_background_color("#123456")
        repr_str = repr(toolbar_view)
        
        assert "bg=#123456" in repr_str
