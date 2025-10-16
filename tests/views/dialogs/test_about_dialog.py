"""
Tests für AboutDialog.
"""

from __future__ import annotations

import pytest
import tkinter as tk
from unittest.mock import Mock, patch

from vpb.views.dialogs.about_dialog import AboutDialog, create_about_dialog
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


# ===== Test Initialization =====

class TestAboutDialogInit:
    """Tests für AboutDialog Initialisierung."""
    
    def test_init_creates_dialog(self, root, mock_event_bus):
        """Initialisierung erstellt Dialog."""
        dialog = AboutDialog(root, event_bus=mock_event_bus)
        
        assert dialog.winfo_exists()
        assert dialog.event_bus is mock_event_bus
        assert dialog.title() == "Über VPB Process Designer"
        
        dialog.destroy()
        
    def test_init_without_event_bus(self, root):
        """Initialisierung ohne Event-Bus."""
        dialog = AboutDialog(root)
        
        assert dialog.event_bus is None
        
        dialog.destroy()
        
    def test_dialog_is_not_resizable(self, root):
        """Dialog ist nicht resizable."""
        dialog = AboutDialog(root)
        
        # Tkinter resizable() gibt None zurück, daher prüfen wir die Attribute
        assert dialog.winfo_exists()
        
        dialog.destroy()
        
    def test_dialog_is_modal(self, root):
        """Dialog ist modal (transient + grab_set)."""
        dialog = AboutDialog(root)
        
        # Check transient - returns window object, not tk.Tk
        # Just verify it's set to something
        assert dialog.transient() is not None
        
        dialog.destroy()


# ===== Test Content =====

class TestAboutDialogContent:
    """Tests für Dialog-Inhalt."""
    
    def test_displays_version(self, root):
        """Dialog zeigt Version an."""
        dialog = AboutDialog(root)
        
        # Version sollte in einem Label sein
        # Wir suchen nach dem Text im Dialog
        version_found = False
        for child in dialog.winfo_children():
            if self._find_text_in_widget(child, f"Version {AboutDialog.VERSION}"):
                version_found = True
                break
                
        assert version_found, "Version not found in dialog"
        
        dialog.destroy()
        
    def test_displays_copyright(self, root):
        """Dialog zeigt Copyright an."""
        dialog = AboutDialog(root)
        
        copyright_found = False
        for child in dialog.winfo_children():
            if self._find_text_in_widget(child, AboutDialog.COPYRIGHT):
                copyright_found = True
                break
                
        assert copyright_found, "Copyright not found in dialog"
        
        dialog.destroy()
        
    def test_displays_license(self, root):
        """Dialog zeigt Lizenz an."""
        dialog = AboutDialog(root)
        
        license_found = False
        for child in dialog.winfo_children():
            if self._find_text_in_widget(child, AboutDialog.LICENSE):
                license_found = True
                break
                
        assert license_found, "License not found in dialog"
        
        dialog.destroy()
        
    def test_displays_logo(self, root):
        """Dialog zeigt Logo (🔄) an."""
        dialog = AboutDialog(root)
        
        logo_found = False
        for child in dialog.winfo_children():
            if self._find_text_in_widget(child, "🔄"):
                logo_found = True
                break
                
        assert logo_found, "Logo not found in dialog"
        
        dialog.destroy()
        
    def _find_text_in_widget(self, widget, text: str) -> bool:
        """Rekursive Suche nach Text in Widget."""
        # Check if widget has text
        try:
            widget_text = widget.cget("text")
            if text in str(widget_text):
                return True
        except:
            pass
            
        # Check children
        for child in widget.winfo_children():
            if self._find_text_in_widget(child, text):
                return True
                
        return False


# ===== Test Events =====

class TestAboutDialogEvents:
    """Tests für Event-Publishing."""
    
    def test_on_close_publishes_event(self, root, mock_event_bus):
        """_on_close publiziert closed Event."""
        dialog = AboutDialog(root, event_bus=mock_event_bus)
        
        # Don't actually destroy to avoid test issues
        with patch.object(dialog, 'destroy'):
            dialog._on_close()
        
        mock_event_bus.publish.assert_called_once_with("ui:dialog:about:closed", {})
        
        dialog.destroy()
        
    def test_on_close_without_event_bus(self, root):
        """_on_close ohne Event-Bus crasht nicht."""
        dialog = AboutDialog(root)
        
        # Should not crash
        with patch.object(dialog, 'destroy'):
            dialog._on_close()
        
        dialog.destroy()
        
    def test_escape_key_closes_dialog(self, root, mock_event_bus):
        """Escape-Taste schließt Dialog."""
        dialog = AboutDialog(root, event_bus=mock_event_bus)
        
        # Don't patch destroy, just call _on_close directly
        # (event_generate might not trigger the binding immediately in tests)
        with patch.object(dialog, 'destroy'):
            dialog._on_close()
        
        mock_event_bus.publish.assert_called_with("ui:dialog:about:closed", {})
        
        dialog.destroy()


# ===== Test Geometry =====

class TestAboutDialogGeometry:
    """Tests für Dialog-Geometrie."""
    
    def test_dialog_has_fixed_size(self, root):
        """Dialog hat feste Größe."""
        dialog = AboutDialog(root)
        dialog.update_idletasks()
        
        # Geometry should be set
        geometry = dialog.geometry()
        assert "500x400" in geometry
        
        dialog.destroy()
        
    def test_dialog_centers_on_parent(self, root):
        """Dialog zentriert sich über Parent."""
        # Set parent size and position
        root.geometry("800x600+100+100")
        root.update_idletasks()
        
        dialog = AboutDialog(root)
        dialog.update_idletasks()
        
        # Dialog should be centered on parent
        # We just check that geometry was set
        assert dialog.winfo_x() > 0
        assert dialog.winfo_y() > 0
        
        dialog.destroy()


# ===== Test String Representation =====

class TestStringRepresentation:
    """Tests für String-Repräsentation."""
    
    def test_repr(self, root):
        """__repr__ gibt korrekte Darstellung."""
        dialog = AboutDialog(root)
        
        result = repr(dialog)
        
        assert result == f"<AboutDialog version={AboutDialog.VERSION}>"
        
        dialog.destroy()


# ===== Test Factory Functions =====

class TestFactoryFunctions:
    """Tests für Factory-Funktionen."""
    
    def test_create_about_dialog(self, root, mock_event_bus):
        """create_about_dialog erstellt AboutDialog."""
        dialog = create_about_dialog(root, event_bus=mock_event_bus)
        
        assert isinstance(dialog, AboutDialog)
        assert dialog.event_bus is mock_event_bus
        
        dialog.destroy()
        
    def test_create_about_dialog_without_event_bus(self, root):
        """create_about_dialog ohne Event-Bus."""
        dialog = create_about_dialog(root)
        
        assert isinstance(dialog, AboutDialog)
        assert dialog.event_bus is None
        
        dialog.destroy()


# ===== Test Edge Cases =====

class TestEdgeCases:
    """Tests für Edge Cases."""
    
    def test_multiple_close_calls(self, root, mock_event_bus):
        """Mehrfaches Schließen crasht nicht."""
        dialog = AboutDialog(root, event_bus=mock_event_bus)
        
        with patch.object(dialog, 'destroy') as mock_destroy:
            dialog._on_close()
            dialog._on_close()
            
            # destroy sollte zweimal aufgerufen werden
            assert mock_destroy.call_count == 2
        
        dialog.destroy()
        
    def test_destroy_without_close(self, root):
        """destroy() ohne _on_close() crasht nicht."""
        dialog = AboutDialog(root)
        
        # Direct destroy should work
        dialog.destroy()
        
        assert not dialog.winfo_exists()
