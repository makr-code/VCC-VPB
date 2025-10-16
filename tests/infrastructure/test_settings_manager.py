"""Unit tests for Settings Manager"""

import pytest
import json
import tempfile
from pathlib import Path

from vpb.infrastructure.settings_manager import (
    SettingsManager,
    AppSettings,
    OllamaSettings,
    WindowSettings,
    ViewSettings,
)


class TestSettingsManager:
    """Test suite for SettingsManager."""
    
    def test_load_defaults(self, tmp_path):
        """Test loading with no existing settings file."""
        settings_file = tmp_path / "settings.json"
        manager = SettingsManager(settings_file)
        
        settings = manager.load()
        
        # Should return defaults
        assert isinstance(settings, AppSettings)
        assert settings.ollama.endpoint == "http://localhost:11434"
        assert settings.window.width == 1200
        assert settings.view.grid_visible is True
    
    def test_save_and_load(self, tmp_path):
        """Test save and load round-trip."""
        settings_file = tmp_path / "settings.json"
        manager = SettingsManager(settings_file)
        
        # Create custom settings
        settings = AppSettings()
        settings.ollama.endpoint = "http://custom:11434"
        settings.window.width = 1600
        settings.view.grid_visible = False
        
        # Save
        result = manager.save(settings)
        assert result is True
        assert settings_file.exists()
        
        # Load in new manager
        manager2 = SettingsManager(settings_file)
        loaded = manager2.load()
        
        # Verify
        assert loaded.ollama.endpoint == "http://custom:11434"
        assert loaded.window.width == 1600
        assert loaded.view.grid_visible is False
    
    def test_legacy_migration(self, tmp_path):
        """Test migration from legacy vpb_settings.json."""
        legacy_file = tmp_path / "vpb_settings.json"
        settings_file = tmp_path / "settings.json"
        
        # Create legacy file
        legacy_data = {
            "ollama_endpoint": "http://legacy:11434",
            "ollama_model": "custom-model",
            "window": {"width": 1400, "height": 900}
        }
        with open(legacy_file, 'w') as f:
            json.dump(legacy_data, f)
        
        # Load (should migrate)
        manager = SettingsManager(settings_file)
        settings = manager.load()
        
        assert settings.ollama.endpoint == "http://legacy:11434"
        assert settings.ollama.model == "custom-model"
        assert settings.window.width == 1400
    
    def test_ollama_validation(self):
        """Test Ollama settings validation."""
        ollama = OllamaSettings()
        
        # Temperature should be clamped
        ollama.temperature = 1.5
        ollama.validate()
        assert ollama.temperature == 1.0
        
        ollama.temperature = -0.5
        ollama.validate()
        assert ollama.temperature == 0.0
        
        # Num predict should be >= 1
        ollama.num_predict = -10
        ollama.validate()
        assert ollama.num_predict == 1
    
    def test_nested_ollama_structure(self, tmp_path):
        """Test loading new nested ollama structure."""
        settings_file = tmp_path / "settings.json"
        
        # Create file with nested structure
        data = {
            "ollama": {
                "endpoint": "http://nested:11434",
                "model": "nested-model",
                "temperature": 0.5,
                "num_predict": 800
            }
        }
        with open(settings_file, 'w') as f:
            json.dump(data, f)
        
        manager = SettingsManager(settings_file)
        settings = manager.load()
        
        assert settings.ollama.endpoint == "http://nested:11434"
        assert settings.ollama.model == "nested-model"
        assert settings.ollama.temperature == 0.5
        assert settings.ollama.num_predict == 800
    
    def test_element_styles_preservation(self, tmp_path):
        """Test that element styles are preserved."""
        settings_file = tmp_path / "settings.json"
        manager = SettingsManager(settings_file)
        
        settings = AppSettings()
        settings.element_styles = {
            "VorProzess": {"fill": "#FF0000"},
            "Prozess": {"fill": "#00FF00"}
        }
        
        manager.save(settings)
        
        loaded = manager.load()
        assert "VorProzess" in loaded.element_styles
        assert loaded.element_styles["VorProzess"]["fill"] == "#FF0000"
    
    def test_hierarchy_categories(self, tmp_path):
        """Test hierarchy categories list."""
        settings_file = tmp_path / "settings.json"
        manager = SettingsManager(settings_file)
        
        settings = AppSettings()
        settings.hierarchy_categories = ["Category1", "Category2", "Category3"]
        
        manager.save(settings)
        loaded = manager.load()
        
        assert len(loaded.hierarchy_categories) == 3
        assert "Category1" in loaded.hierarchy_categories
    
    def test_get_current(self, tmp_path):
        """Test get_current returns last loaded settings."""
        settings_file = tmp_path / "settings.json"
        manager = SettingsManager(settings_file)
        
        assert manager.get_current() is None
        
        settings = manager.load()
        current = manager.get_current()
        
        assert current is not None
        assert current is settings
    
    def test_save_without_load(self, tmp_path):
        """Test saving without loading first."""
        settings_file = tmp_path / "settings.json"
        manager = SettingsManager(settings_file)
        
        # Try to save without settings
        result = manager.save()
        assert result is False  # Should fail gracefully
    
    def test_invalid_json_handling(self, tmp_path):
        """Test handling of corrupted JSON file."""
        settings_file = tmp_path / "settings.json"
        
        # Write invalid JSON
        with open(settings_file, 'w') as f:
            f.write("{ invalid json }")
        
        manager = SettingsManager(settings_file)
        settings = manager.load()
        
        # Should fall back to defaults
        assert settings.ollama.endpoint == "http://localhost:11434"
    
    def test_partial_settings(self, tmp_path):
        """Test loading file with partial settings."""
        settings_file = tmp_path / "settings.json"
        
        # Only some settings present
        data = {
            "window": {"width": 1500},
            "view": {"grid_visible": False}
        }
        with open(settings_file, 'w') as f:
            json.dump(data, f)
        
        manager = SettingsManager(settings_file)
        settings = manager.load()
        
        # Should use provided values
        assert settings.window.width == 1500
        assert settings.view.grid_visible is False
        
        # Should use defaults for missing values
        assert settings.window.height == 800  # default
        assert settings.ollama.endpoint == "http://localhost:11434"  # default


class TestAppSettings:
    """Test AppSettings dataclass."""
    
    def test_default_initialization(self):
        """Test creating settings with defaults."""
        settings = AppSettings()
        
        assert isinstance(settings.ollama, OllamaSettings)
        assert isinstance(settings.window, WindowSettings)
        assert isinstance(settings.view, ViewSettings)
        assert settings.element_styles == {}
        assert settings.hierarchy_categories == []
    
    def test_nested_modification(self):
        """Test modifying nested settings."""
        settings = AppSettings()
        
        settings.ollama.endpoint = "http://modified:11434"
        settings.window.width = 2000
        settings.view.grid_visible = False
        
        assert settings.ollama.endpoint == "http://modified:11434"
        assert settings.window.width == 2000
        assert settings.view.grid_visible is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
