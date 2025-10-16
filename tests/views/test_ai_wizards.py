"""
Tests für AI Wizards Dialogs
=============================

Grundlegende Tests für AIProcessGenerationDialog und AIIngestionWizard.
"""

import pytest
import tkinter as tk
from pathlib import Path
from vpb.views.dialogs.ai_wizards import (
    AIProcessGenerationDialog,
    AIIngestionWizard,
    show_ai_process_generation_dialog,
    show_ai_ingestion_wizard
)


@pytest.fixture
def root():
    """Erstellt Tkinter Root Window."""
    root = tk.Tk()
    root.withdraw()  # Verstecken
    yield root
    try:
        root.destroy()
    except tk.TclError:
        pass


class TestAIProcessGenerationDialog:
    """Tests für AIProcessGenerationDialog."""
    
    def test_create_dialog(self, root):
        """Test: Dialog erstellen."""
        dialog = AIProcessGenerationDialog(root)
        
        assert dialog.dialog is not None
        assert dialog.result is None
        
        dialog.dialog.destroy()
    
    def test_dialog_has_text_input(self, root):
        """Test: Dialog hat Text-Eingabefeld."""
        dialog = AIProcessGenerationDialog(root)
        
        assert hasattr(dialog, 'text_input')
        assert dialog.text_input is not None
        
        # Prüfe Beispiel-Text
        text = dialog.text_input.get("1.0", tk.END)
        assert len(text) > 0
        assert "Beispiel" in text or "Baugenehmigung" in text
        
        dialog.dialog.destroy()
    
    def test_dialog_has_model_selector(self, root):
        """Test: Dialog hat Model-Auswahl."""
        dialog = AIProcessGenerationDialog(root)
        
        assert hasattr(dialog, 'model_var')
        assert dialog.model_var.get() in ["llama3.2:latest", "mistral:latest", "phi3:latest"]
        
        dialog.dialog.destroy()
    
    def test_dialog_has_temperature_setting(self, root):
        """Test: Dialog hat Temperature-Einstellung."""
        dialog = AIProcessGenerationDialog(root)
        
        assert hasattr(dialog, 'temperature_var')
        temp = dialog.temperature_var.get()
        assert 0.0 <= temp <= 1.0
        
        dialog.dialog.destroy()
    
    def test_dialog_callback(self, root):
        """Test: Dialog Callback funktioniert."""
        callback_called = []
        
        def on_generate(prompt, settings):
            callback_called.append((prompt, settings))
        
        dialog = AIProcessGenerationDialog(root, on_generate)
        
        # Setze Text
        dialog.text_input.delete("1.0", tk.END)
        dialog.text_input.insert("1.0", "Test Process")
        
        # Simuliere Generate-Click
        dialog._on_generate()
        
        assert len(callback_called) == 1
        assert callback_called[0][0] == "Test Process"
        assert "model" in callback_called[0][1]
        assert "temperature" in callback_called[0][1]
    
    def test_factory_function(self, root):
        """Test: Factory Function show_ai_process_generation_dialog."""
        # Kann nicht vollständig getestet werden ohne Modal-Dialog
        # aber wir können prüfen dass Function existiert
        assert callable(show_ai_process_generation_dialog)


class TestAIIngestionWizard:
    """Tests für AIIngestionWizard."""
    
    def test_create_wizard(self, root):
        """Test: Wizard erstellen."""
        wizard = AIIngestionWizard(root)
        
        assert wizard.dialog is not None
        assert wizard.selected_file is None
        assert wizard.result is None
        
        wizard.dialog.destroy()
    
    def test_wizard_has_file_selection(self, root):
        """Test: Wizard hat Datei-Auswahl."""
        wizard = AIIngestionWizard(root)
        
        assert hasattr(wizard, 'file_path_var')
        assert wizard.file_path_var.get() == "Keine Datei ausgewählt"
        
        wizard.dialog.destroy()
    
    def test_wizard_has_source_type_selector(self, root):
        """Test: Wizard hat Source-Type-Auswahl."""
        wizard = AIIngestionWizard(root)
        
        assert hasattr(wizard, 'source_type_var')
        assert wizard.source_type_var.get() in ["text", "image", "structured"]
        
        wizard.dialog.destroy()
    
    def test_wizard_has_model_selector(self, root):
        """Test: Wizard hat Model-Auswahl."""
        wizard = AIIngestionWizard(root)
        
        assert hasattr(wizard, 'model_var')
        assert wizard.model_var.get() in ["llama3.2:latest", "mistral:latest", "phi3:latest"]
        
        wizard.dialog.destroy()
    
    def test_wizard_has_confidence_threshold(self, root):
        """Test: Wizard hat Confidence-Einstellung."""
        wizard = AIIngestionWizard(root)
        
        assert hasattr(wizard, 'confidence_var')
        conf = wizard.confidence_var.get()
        assert 0.0 <= conf <= 1.0
        
        wizard.dialog.destroy()
    
    def test_wizard_callback(self, root, tmp_path):
        """Test: Wizard Callback funktioniert."""
        callback_called = []
        
        def on_ingest(file_path, settings):
            callback_called.append((file_path, settings))
        
        wizard = AIIngestionWizard(root, on_ingest)
        
        # Erstelle Test-Datei
        test_file = tmp_path / "test.pdf"
        test_file.write_text("Test content")
        
        wizard.selected_file = test_file
        wizard.file_path_var.set(str(test_file))
        
        # Simuliere Ingest-Click
        wizard._on_ingest()
        
        assert len(callback_called) == 1
        assert callback_called[0][0] == test_file
        assert "source_type" in callback_called[0][1]
        assert "model" in callback_called[0][1]
        assert "confidence_threshold" in callback_called[0][1]
    
    def test_factory_function(self, root):
        """Test: Factory Function show_ai_ingestion_wizard."""
        # Kann nicht vollständig getestet werden ohne Modal-Dialog
        # aber wir können prüfen dass Function existiert
        assert callable(show_ai_ingestion_wizard)


class TestIntegration:
    """Integrations-Tests für beide Dialoge."""
    
    def test_both_dialogs_can_coexist(self, root):
        """Test: Beide Dialoge können gleichzeitig existieren."""
        dialog1 = AIProcessGenerationDialog(root)
        dialog2 = AIIngestionWizard(root)
        
        assert dialog1.dialog is not None
        assert dialog2.dialog is not None
        
        dialog1.dialog.destroy()
        dialog2.dialog.destroy()
    
    def test_dialogs_are_transient(self, root):
        """Test: Dialoge sind transient über Parent."""
        dialog = AIProcessGenerationDialog(root)
        
        # Tkinter transient Verhalten schwer zu testen
        # aber wir können prüfen dass Dialog existiert
        assert dialog.dialog.winfo_exists()
        
        dialog.dialog.destroy()
