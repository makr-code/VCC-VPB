"""
Migration Script: Settings to User Profile
===========================================

Migriert bestehende Einstellungen und Daten in das neue User Profile System.

Migrierte Daten:
- Settings (settings.json) → UI Preferences
- Recent Files (recent_files.json) → Workspace
- Chat History (chats/) → Chat History

Autor: GitHub Copilot
Datum: 17. Oktober 2025
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List
import logging

from vpb.infrastructure.user_profile_manager import (
    UserProfileManager,
    UserProfile,
    CanvasViewState,
    UIPreferences,
    WorkspaceState,
    ToolPreferences,
    UIPanelState
)


logger = logging.getLogger(__name__)


class ProfileMigration:
    """Migriert bestehende Daten in das User Profile System."""
    
    def __init__(self):
        self.profile_manager = UserProfileManager()
    
    def migrate_all(self) -> UserProfile:
        """
        Führt die vollständige Migration durch.
        
        Returns:
            Migriertes UserProfile
        """
        logger.info("=" * 60)
        logger.info("Starte Migration zu User Profile System")
        logger.info("=" * 60)
        
        # Lade oder erstelle Profil
        profile = self.profile_manager.load()
        
        # Migriere Settings
        self._migrate_settings(profile)
        
        # Migriere Recent Files
        self._migrate_recent_files(profile)
        
        # Migriere Chat History
        self._migrate_chat_history(profile)
        
        # Speichere migriertes Profil
        self.profile_manager.save(profile)
        
        logger.info("=" * 60)
        logger.info("✅ Migration abgeschlossen")
        logger.info("=" * 60)
        
        return profile
    
    def _migrate_settings(self, profile: UserProfile) -> None:
        """Migriert settings.json in UI Preferences."""
        settings_path = Path("settings.json")
        
        if not settings_path.exists():
            logger.info("⏭️  Keine settings.json gefunden, überspringe Migration")
            return
        
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            logger.info(f"📁 Migriere settings.json...")
            
            # UI Preferences
            prefs = profile.ui_preferences
            
            # Sidebar-Breiten
            if "sidebars" in settings:
                sidebars = settings["sidebars"]
                prefs.left_sidebar_width = sidebars.get("left_width", 250)
                prefs.right_sidebar_width = sidebars.get("right_width", 250)
                logger.info(f"  ✓ Sidebar-Breiten: {prefs.left_sidebar_width}px / {prefs.right_sidebar_width}px")
            
            # Canvas View
            view = profile.canvas_view
            if "view" in settings:
                view_settings = settings["view"]
                view.grid_visible = view_settings.get("grid_visible", True)
                view.snap_to_grid = view_settings.get("snap_to_grid", False)
                logger.info(f"  ✓ Grid: {view.grid_visible}, Snap: {view.snap_to_grid}")
            
            logger.info("✅ Settings migriert")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Settings-Migration: {e}")
    
    def _migrate_recent_files(self, profile: UserProfile) -> None:
        """Migriert recent_files.json in Workspace."""
        recent_files_path = Path("recent_files.json")
        
        if not recent_files_path.exists():
            logger.info("⏭️  Keine recent_files.json gefunden, überspringe Migration")
            return
        
        try:
            with open(recent_files_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            recent_files = data.get("recent_files", [])
            
            if not recent_files:
                logger.info("⏭️  Keine Recent Files zum Migrieren")
                return
            
            logger.info(f"📁 Migriere {len(recent_files)} Recent Files...")
            
            # Validiere Dateien
            valid_files = [f for f in recent_files if os.path.exists(f)]
            
            profile.workspace.recent_files = valid_files[:profile.workspace.max_recent_files]
            
            if valid_files:
                profile.workspace.last_opened_file = valid_files[0]
            
            logger.info(f"✅ {len(valid_files)} Recent Files migriert")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Recent Files Migration: {e}")
    
    def _migrate_chat_history(self, profile: UserProfile) -> None:
        """Migriert Chat-Historie aus chats/ Verzeichnis."""
        chats_dir = Path("chats")
        
        if not chats_dir.exists():
            logger.info("⏭️  Kein chats/ Verzeichnis gefunden, überspringe Migration")
            return
        
        try:
            # Finde alle chat.json Dateien
            chat_files = list(chats_dir.rglob("chat.json"))
            
            if not chat_files:
                logger.info("⏭️  Keine Chat-Historie zum Migrieren")
                return
            
            logger.info(f"📁 Migriere Chat-Historie aus {len(chat_files)} Projekten...")
            
            migrated_count = 0
            
            for chat_file in chat_files:
                try:
                    # Projekt-ID aus Pfad extrahieren
                    # Format: chats/<user>@<host>/<model>/<project_id>/chat.json
                    parts = chat_file.parts
                    if len(parts) >= 3:
                        project_id = parts[-2]  # Vorletzter Teil ist die Projekt-ID
                        
                        # Lade Chat-Nachrichten
                        with open(chat_file, 'r', encoding='utf-8') as f:
                            messages = json.load(f)
                        
                        if isinstance(messages, list) and messages:
                            profile.chat_history[project_id] = messages
                            migrated_count += 1
                            logger.info(f"  ✓ {project_id}: {len(messages)} Nachrichten")
                
                except Exception as e:
                    logger.warning(f"  ⚠️  Fehler bei {chat_file}: {e}")
            
            logger.info(f"✅ Chat-Historie migriert ({migrated_count} Projekte)")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Chat-Historie Migration: {e}")


def main():
    """Führt die Migration aus."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )
    
    migration = ProfileMigration()
    profile = migration.migrate_all()
    
    # Zeige Zusammenfassung
    print("\n" + "=" * 60)
    print("Migration Zusammenfassung")
    print("=" * 60)
    print(f"Benutzer: {profile.username}@{profile.hostname}")
    print(f"Recent Files: {len(profile.workspace.recent_files)}")
    print(f"Chat-Historie: {len(profile.chat_history)} Projekte")
    print(f"Sidebar Links: {profile.ui_preferences.left_sidebar_width}px")
    print(f"Sidebar Rechts: {profile.ui_preferences.right_sidebar_width}px")
    print(f"Grid sichtbar: {profile.canvas_view.grid_visible}")
    print("=" * 60)


if __name__ == "__main__":
    main()
