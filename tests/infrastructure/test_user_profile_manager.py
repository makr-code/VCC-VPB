"""
Unit Tests for User Profile Manager

Tests the user profile system including:
- Profile creation and loading
- Saving and persistence
- Canvas view updates
- UI preferences updates
- Recent files management
- Chat history management
- Migration

Autor: GitHub Copilot
Datum: 17. Oktober 2025
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

from vpb.infrastructure.user_profile_manager import (
    UserProfileManager,
    UserProfile,
    CanvasViewState,
    UIPreferences,
    WorkspaceState,
    ToolPreferences,
    UIPanelState
)


class TestUserProfileManager:
    """Tests für UserProfileManager."""
    
    @pytest.fixture
    def temp_profile_dir(self):
        """Temporäres Verzeichnis für Profile."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def manager(self, temp_profile_dir):
        """Manager-Instanz mit temporärem Verzeichnis."""
        return UserProfileManager(profile_dir=temp_profile_dir)
    
    def test_initialization(self, manager, temp_profile_dir):
        """Test: Manager-Initialisierung."""
        assert manager.profile_dir == Path(temp_profile_dir)
        assert manager.username is not None
        assert manager.hostname is not None
        assert manager.profile_path.exists() or not manager.profile_path.exists()
    
    def test_load_new_profile(self, manager):
        """Test: Neues Profil laden."""
        profile = manager.load()
        
        assert profile is not None
        assert profile.username == manager.username
        assert profile.hostname == manager.hostname
        assert profile.profile_version == "1.0"
        assert profile.canvas_view.zoom_level == 1.0
        assert profile.ui_preferences.left_sidebar_width == 250
        assert profile.workspace.recent_files == []
    
    def test_save_and_load(self, manager):
        """Test: Profil speichern und laden."""
        # Erstelle Profil
        profile = manager.load()
        profile.canvas_view.zoom_level = 1.5
        profile.ui_preferences.left_sidebar_width = 300
        
        # Speichern
        success = manager.save(profile)
        assert success is True
        assert manager.profile_path.exists()
        
        # Neu laden
        manager2 = UserProfileManager(profile_dir=manager.profile_dir)
        loaded_profile = manager2.load()
        
        assert loaded_profile.canvas_view.zoom_level == 1.5
        assert loaded_profile.ui_preferences.left_sidebar_width == 300
    
    def test_update_canvas_view(self, manager):
        """Test: Canvas-Ansicht aktualisieren."""
        profile = manager.load()
        
        manager.update_canvas_view(
            zoom=2.0,
            pan_x=100.0,
            pan_y=50.0,
            grid_visible=False
        )
        
        # Neu laden und prüfen
        manager2 = UserProfileManager(profile_dir=manager.profile_dir)
        loaded_profile = manager2.load()
        
        assert loaded_profile.canvas_view.zoom_level == 2.0
        assert loaded_profile.canvas_view.pan_x == 100.0
        assert loaded_profile.canvas_view.pan_y == 50.0
        assert loaded_profile.canvas_view.grid_visible is False
    
    def test_update_ui_preferences(self, manager):
        """Test: UI-Präferenzen aktualisieren."""
        profile = manager.load()
        
        manager.update_ui_preferences(
            left_sidebar_width=400,
            right_sidebar_width=350
        )
        
        # Neu laden und prüfen
        manager2 = UserProfileManager(profile_dir=manager.profile_dir)
        loaded_profile = manager2.load()
        
        assert loaded_profile.ui_preferences.left_sidebar_width == 400
        assert loaded_profile.ui_preferences.right_sidebar_width == 350
    
    def test_add_recent_file(self, manager):
        """Test: Recent File hinzufügen."""
        profile = manager.load()
        
        # Temporäre Dateien erstellen
        temp_file1 = tempfile.NamedTemporaryFile(delete=False, suffix=".vpb.json")
        temp_file2 = tempfile.NamedTemporaryFile(delete=False, suffix=".vpb.json")
        
        try:
            # Dateien hinzufügen
            manager.add_recent_file(temp_file1.name)
            manager.add_recent_file(temp_file2.name)
            
            # Neu laden und prüfen
            manager2 = UserProfileManager(profile_dir=manager.profile_dir)
            loaded_profile = manager2.load()
            
            assert len(loaded_profile.workspace.recent_files) == 2
            assert loaded_profile.workspace.recent_files[0] == os.path.abspath(temp_file2.name)
            assert loaded_profile.workspace.recent_files[1] == os.path.abspath(temp_file1.name)
            assert loaded_profile.workspace.last_opened_file == os.path.abspath(temp_file2.name)
        
        finally:
            # Cleanup
            os.unlink(temp_file1.name)
            os.unlink(temp_file2.name)
    
    def test_get_recent_files_validation(self, manager):
        """Test: Recent Files mit Validierung."""
        profile = manager.load()
        
        # Füge existierende und nicht-existierende Dateien hinzu
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".vpb.json")
        fake_file = "/fake/path/file.vpb.json"
        
        try:
            profile.workspace.recent_files = [temp_file.name, fake_file]
            manager.save(profile)
            
            # Mit Validierung
            valid_files = manager.get_recent_files(validate=True)
            assert len(valid_files) == 1
            assert valid_files[0] == temp_file.name
            
            # Ohne Validierung
            all_files = manager.get_recent_files(validate=False)
            assert len(all_files) == 2
        
        finally:
            os.unlink(temp_file.name)
    
    def test_chat_history(self, manager):
        """Test: Chat-Historie verwalten."""
        profile = manager.load()
        
        messages = [
            {"role": "user", "content": "Hallo"},
            {"role": "assistant", "content": "Hallo! Wie kann ich helfen?"}
        ]
        
        manager.update_chat_history("test-project-123", messages)
        
        # Neu laden und prüfen
        manager2 = UserProfileManager(profile_dir=manager.profile_dir)
        loaded_messages = manager2.get_chat_history("test-project-123")
        
        assert len(loaded_messages) == 2
        assert loaded_messages[0]["role"] == "user"
        assert loaded_messages[1]["role"] == "assistant"
    
    def test_max_recent_files(self, manager):
        """Test: Maximale Anzahl Recent Files."""
        profile = manager.load()
        
        # Erstelle 15 temporäre Dateien (max ist 10)
        temp_files = []
        for i in range(15):
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{i}.vpb.json")
            temp_files.append(temp_file.name)
            manager.add_recent_file(temp_file.name)
        
        try:
            # Neu laden und prüfen
            manager2 = UserProfileManager(profile_dir=manager.profile_dir)
            recent_files = manager2.get_recent_files(validate=False)
            
            assert len(recent_files) == 10  # Maximal 10
            assert recent_files[0] == os.path.abspath(temp_files[-1])  # Neueste zuerst
        
        finally:
            for temp_file in temp_files:
                os.unlink(temp_file)


class TestCanvasViewState:
    """Tests für CanvasViewState."""
    
    def test_to_dict(self):
        """Test: Konvertierung zu Dictionary."""
        view = CanvasViewState(
            zoom_level=1.5,
            pan_x=100.0,
            grid_visible=False
        )
        
        data = view.to_dict()
        
        assert data["zoom_level"] == 1.5
        assert data["pan_x"] == 100.0
        assert data["grid_visible"] is False
    
    def test_from_dict(self):
        """Test: Aus Dictionary erstellen."""
        data = {
            "zoom_level": 2.0,
            "pan_x": 50.0,
            "grid_visible": True
        }
        
        view = CanvasViewState.from_dict(data)
        
        assert view.zoom_level == 2.0
        assert view.pan_x == 50.0
        assert view.grid_visible is True


class TestUIPreferences:
    """Tests für UIPreferences."""
    
    def test_to_dict(self):
        """Test: Konvertierung zu Dictionary."""
        prefs = UIPreferences(
            left_sidebar_width=300,
            right_sidebar_width=350
        )
        
        data = prefs.to_dict()
        
        assert data["left_sidebar_width"] == 300
        assert data["right_sidebar_width"] == 350
    
    def test_from_dict(self):
        """Test: Aus Dictionary erstellen."""
        data = {
            "left_sidebar_width": 400,
            "right_sidebar_width": 450,
            "theme": "dark"
        }
        
        prefs = UIPreferences.from_dict(data)
        
        assert prefs.left_sidebar_width == 400
        assert prefs.right_sidebar_width == 450
        assert prefs.theme == "dark"


class TestUserProfile:
    """Tests für UserProfile."""
    
    def test_to_dict(self):
        """Test: Komplettes Profil zu Dictionary."""
        profile = UserProfile()
        profile.username = "testuser"
        profile.hostname = "testhost"
        profile.canvas_view.zoom_level = 1.5
        
        data = profile.to_dict()
        
        assert data["username"] == "testuser"
        assert data["hostname"] == "testhost"
        assert data["canvas_view"]["zoom_level"] == 1.5
    
    def test_from_dict(self):
        """Test: Profil aus Dictionary."""
        data = {
            "username": "testuser",
            "hostname": "testhost",
            "profile_version": "1.0",
            "canvas_view": {
                "zoom_level": 2.0,
                "grid_visible": False
            },
            "ui_preferences": {
                "left_sidebar_width": 300
            }
        }
        
        profile = UserProfile.from_dict(data)
        
        assert profile.username == "testuser"
        assert profile.hostname == "testhost"
        assert profile.canvas_view.zoom_level == 2.0
        assert profile.canvas_view.grid_visible is False
        assert profile.ui_preferences.left_sidebar_width == 300


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
