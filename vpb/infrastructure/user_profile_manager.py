"""
User Profile Manager for VPB Process Designer
==============================================

Zentrales System für benutzerspezifische Einstellungen und Daten.
Speichert alle Benutzer-Präferenzen in einer JSON-Datei und stellt
sie beim nächsten Start wieder her.

Features:
- Benutzername und Hostname basierte Profile
- Canvas-Ansicht (Zoom, Position, Grid)
- UI-Präferenzen (Sidebar-Breiten, Panel-Zustände)
- Werkzeug-Einstellungen (Letzte Auswahl, Favoriten)
- Kürzlich verwendete Dateien
- Chat-Historie (pro Projekt)
- Letzte geöffnete Dateien und Positionen
- Automatisches Speichern bei Änderungen

Autor: GitHub Copilot
Datum: 17. Oktober 2025
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json
import logging
import getpass
import socket
import os


logger = logging.getLogger(__name__)


@dataclass
class CanvasViewState:
    """Canvas-Ansichtszustand."""
    zoom_level: float = 1.0
    pan_x: float = 0.0
    pan_y: float = 0.0
    grid_visible: bool = True
    snap_to_grid: bool = False
    ruler_visible: bool = True
    minimap_visible: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "CanvasViewState":
        return CanvasViewState(
            zoom_level=float(data.get("zoom_level", 1.0)),
            pan_x=float(data.get("pan_x", 0.0)),
            pan_y=float(data.get("pan_y", 0.0)),
            grid_visible=bool(data.get("grid_visible", True)),
            snap_to_grid=bool(data.get("snap_to_grid", False)),
            ruler_visible=bool(data.get("ruler_visible", True)),
            minimap_visible=bool(data.get("minimap_visible", True))
        )


@dataclass
class UIPanelState:
    """UI-Panel-Zustand."""
    visible: bool = True
    width: int = 250
    height: int = 200
    collapsed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "UIPanelState":
        return UIPanelState(
            visible=bool(data.get("visible", True)),
            width=int(data.get("width", 250)),
            height=int(data.get("height", 200)),
            collapsed=bool(data.get("collapsed", False))
        )


@dataclass
class UIPreferences:
    """UI-Präferenzen des Benutzers."""
    # Panel-Zustände
    palette_panel: UIPanelState = field(default_factory=UIPanelState)
    properties_panel: UIPanelState = field(default_factory=UIPanelState)
    minimap_panel: UIPanelState = field(default_factory=UIPanelState)
    chat_panel: UIPanelState = field(default_factory=UIPanelState)
    
    # Sidebar-Breiten
    left_sidebar_width: int = 250
    right_sidebar_width: int = 250
    
    # Toolbar-Einstellungen
    toolbar_icon_size: str = "medium"  # small, medium, large
    show_toolbar_labels: bool = False
    
    # Theme
    theme: str = "default"
    color_scheme: str = "light"  # light, dark, auto
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "palette_panel": self.palette_panel.to_dict(),
            "properties_panel": self.properties_panel.to_dict(),
            "minimap_panel": self.minimap_panel.to_dict(),
            "chat_panel": self.chat_panel.to_dict(),
            "left_sidebar_width": self.left_sidebar_width,
            "right_sidebar_width": self.right_sidebar_width,
            "toolbar_icon_size": self.toolbar_icon_size,
            "show_toolbar_labels": self.show_toolbar_labels,
            "theme": self.theme,
            "color_scheme": self.color_scheme
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "UIPreferences":
        prefs = UIPreferences()
        
        # Panel-Zustände
        if "palette_panel" in data:
            prefs.palette_panel = UIPanelState.from_dict(data["palette_panel"])
        if "properties_panel" in data:
            prefs.properties_panel = UIPanelState.from_dict(data["properties_panel"])
        if "minimap_panel" in data:
            prefs.minimap_panel = UIPanelState.from_dict(data["minimap_panel"])
        if "chat_panel" in data:
            prefs.chat_panel = UIPanelState.from_dict(data["chat_panel"])
        
        # Sidebar-Breiten
        prefs.left_sidebar_width = int(data.get("left_sidebar_width", 250))
        prefs.right_sidebar_width = int(data.get("right_sidebar_width", 250))
        
        # Toolbar
        prefs.toolbar_icon_size = str(data.get("toolbar_icon_size", "medium"))
        prefs.show_toolbar_labels = bool(data.get("show_toolbar_labels", False))
        
        # Theme
        prefs.theme = str(data.get("theme", "default"))
        prefs.color_scheme = str(data.get("color_scheme", "light"))
        
        return prefs


@dataclass
class WorkspaceState:
    """Workspace-Zustand (letzte geöffnete Dateien, Positionen)."""
    last_opened_file: Optional[str] = None
    recent_files: List[str] = field(default_factory=list)
    max_recent_files: int = 10
    
    # Pro-Datei-Zustände
    file_states: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "last_opened_file": self.last_opened_file,
            "recent_files": self.recent_files[:self.max_recent_files],
            "file_states": self.file_states
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "WorkspaceState":
        return WorkspaceState(
            last_opened_file=data.get("last_opened_file"),
            recent_files=list(data.get("recent_files", [])),
            file_states=dict(data.get("file_states", {}))
        )


@dataclass
class ToolPreferences:
    """Werkzeug-Präferenzen."""
    last_selected_element: Optional[str] = None
    favorite_elements: List[str] = field(default_factory=list)
    last_connection_type: str = "arrow"
    
    # Tastenkombinationen (Custom Keybindings)
    custom_keybindings: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ToolPreferences":
        return ToolPreferences(
            last_selected_element=data.get("last_selected_element"),
            favorite_elements=list(data.get("favorite_elements", [])),
            last_connection_type=str(data.get("last_connection_type", "arrow")),
            custom_keybindings=dict(data.get("custom_keybindings", {}))
        )


@dataclass
class UserProfile:
    """Komplettes Benutzerprofil."""
    # Metadaten
    username: str = ""
    hostname: str = ""
    profile_version: str = "1.0"
    last_updated: Optional[str] = None
    
    # Einstellungen
    canvas_view: CanvasViewState = field(default_factory=CanvasViewState)
    ui_preferences: UIPreferences = field(default_factory=UIPreferences)
    workspace: WorkspaceState = field(default_factory=WorkspaceState)
    tools: ToolPreferences = field(default_factory=ToolPreferences)
    
    # Chat-Historie (pro Projekt)
    chat_history: Dict[str, List[Dict[str, str]]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "username": self.username,
            "hostname": self.hostname,
            "profile_version": self.profile_version,
            "last_updated": self.last_updated,
            "canvas_view": self.canvas_view.to_dict(),
            "ui_preferences": self.ui_preferences.to_dict(),
            "workspace": self.workspace.to_dict(),
            "tools": self.tools.to_dict(),
            "chat_history": self.chat_history
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "UserProfile":
        profile = UserProfile()
        
        # Metadaten
        profile.username = str(data.get("username", ""))
        profile.hostname = str(data.get("hostname", ""))
        profile.profile_version = str(data.get("profile_version", "1.0"))
        profile.last_updated = data.get("last_updated")
        
        # Einstellungen
        if "canvas_view" in data:
            profile.canvas_view = CanvasViewState.from_dict(data["canvas_view"])
        if "ui_preferences" in data:
            profile.ui_preferences = UIPreferences.from_dict(data["ui_preferences"])
        if "workspace" in data:
            profile.workspace = WorkspaceState.from_dict(data["workspace"])
        if "tools" in data:
            profile.tools = ToolPreferences.from_dict(data["tools"])
        
        # Chat-Historie
        profile.chat_history = dict(data.get("chat_history", {}))
        
        return profile


class UserProfileManager:
    """
    Verwaltet Benutzerprofile und deren Persistenz.
    
    Speichert benutzerspezifische Einstellungen in einer JSON-Datei.
    Standardpfad: user_profiles/<username>@<hostname>.json
    
    Example:
        ```python
        # Initialisierung
        manager = UserProfileManager()
        profile = manager.load()
        
        # Einstellungen ändern
        profile.canvas_view.zoom_level = 1.5
        profile.ui_preferences.left_sidebar_width = 300
        
        # Automatisch speichern
        manager.save(profile)
        
        # Oder explizit
        manager.save()
        ```
    """
    
    def __init__(self, profile_dir: Union[str, Path] = "user_profiles"):
        """
        Initialisiert den User Profile Manager.
        
        Args:
            profile_dir: Verzeichnis für Benutzerprofile
        """
        self.profile_dir = Path(profile_dir)
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        
        # Aktueller Benutzer
        self.username = self._get_username()
        self.hostname = self._get_hostname()
        
        # Profilpfad
        profile_filename = f"{self.username}@{self.hostname}.json"
        self.profile_path = self.profile_dir / profile_filename
        
        # Aktuelles Profil
        self._current_profile: Optional[UserProfile] = None
        
        logger.info(f"User Profile Manager initialisiert für {self.username}@{self.hostname}")
        logger.info(f"Profilpfad: {self.profile_path}")
    
    def load(self) -> UserProfile:
        """
        Lädt das Benutzerprofil von Disk oder erstellt ein neues.
        
        Returns:
            UserProfile mit geladenen oder Default-Werten
        """
        profile = UserProfile()
        profile.username = self.username
        profile.hostname = self.hostname
        
        if self.profile_path.exists():
            try:
                with open(self.profile_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    profile = UserProfile.from_dict(data)
                    # Aktualisiere Metadaten
                    profile.username = self.username
                    profile.hostname = self.hostname
                    logger.info(f"✅ Benutzerprofil geladen: {self.profile_path}")
            except Exception as e:
                logger.error(f"❌ Fehler beim Laden des Benutzerprofils: {e}")
                logger.info("Verwende Default-Profil")
        else:
            logger.info("Kein gespeichertes Profil gefunden, erstelle neues Profil")
        
        self._current_profile = profile
        return profile
    
    def save(self, profile: Optional[UserProfile] = None) -> bool:
        """
        Speichert das Benutzerprofil auf Disk.
        
        Args:
            profile: Zu speicherndes Profil (verwendet aktuelles wenn None)
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        if profile is None:
            profile = self._current_profile
        
        if profile is None:
            logger.warning("Kein Profil zum Speichern vorhanden")
            return False
        
        try:
            # Aktualisiere Zeitstempel
            from datetime import datetime
            profile.last_updated = datetime.now().isoformat()
            
            # Konvertiere zu Dict
            data = profile.to_dict()
            
            # Speichere in JSON-Datei
            with open(self.profile_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Benutzerprofil gespeichert: {self.profile_path}")
            self._current_profile = profile
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern des Benutzerprofils: {e}")
            return False
    
    def get_current(self) -> Optional[UserProfile]:
        """Gibt das aktuell geladene Profil zurück."""
        return self._current_profile
    
    def update_canvas_view(
        self,
        zoom: Optional[float] = None,
        pan_x: Optional[float] = None,
        pan_y: Optional[float] = None,
        grid_visible: Optional[bool] = None,
        snap_to_grid: Optional[bool] = None
    ) -> None:
        """
        Aktualisiert Canvas-Ansicht und speichert automatisch.
        
        Args:
            zoom: Zoom-Level
            pan_x: Horizontale Pan-Position
            pan_y: Vertikale Pan-Position
            grid_visible: Grid-Sichtbarkeit
            snap_to_grid: Snap-to-Grid aktiviert
        """
        if self._current_profile is None:
            logger.warning("Kein Profil geladen")
            return
        
        view = self._current_profile.canvas_view
        
        if zoom is not None:
            view.zoom_level = zoom
        if pan_x is not None:
            view.pan_x = pan_x
        if pan_y is not None:
            view.pan_y = pan_y
        if grid_visible is not None:
            view.grid_visible = grid_visible
        if snap_to_grid is not None:
            view.snap_to_grid = snap_to_grid
        
        self.save()
    
    def update_ui_preferences(
        self,
        left_sidebar_width: Optional[int] = None,
        right_sidebar_width: Optional[int] = None,
        **kwargs
    ) -> None:
        """
        Aktualisiert UI-Präferenzen und speichert automatisch.
        
        Args:
            left_sidebar_width: Breite der linken Sidebar
            right_sidebar_width: Breite der rechten Sidebar
            **kwargs: Weitere UI-Präferenzen
        """
        if self._current_profile is None:
            logger.warning("Kein Profil geladen")
            return
        
        prefs = self._current_profile.ui_preferences
        
        if left_sidebar_width is not None:
            prefs.left_sidebar_width = left_sidebar_width
        if right_sidebar_width is not None:
            prefs.right_sidebar_width = right_sidebar_width
        
        for key, value in kwargs.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)
        
        self.save()
    
    def add_recent_file(self, file_path: str) -> None:
        """
        Fügt eine Datei zur Recent Files Liste hinzu.
        
        Args:
            file_path: Absoluter Pfad zur Datei
        """
        if self._current_profile is None:
            logger.warning("Kein Profil geladen")
            return
        
        workspace = self._current_profile.workspace
        file_path = os.path.abspath(file_path)
        
        # Entferne Duplikate
        if file_path in workspace.recent_files:
            workspace.recent_files.remove(file_path)
        
        # Füge am Anfang hinzu
        workspace.recent_files.insert(0, file_path)
        
        # Beschränke auf max_recent_files
        workspace.recent_files = workspace.recent_files[:workspace.max_recent_files]
        
        # Setze als letzte geöffnete Datei
        workspace.last_opened_file = file_path
        
        self.save()
    
    def get_recent_files(self, validate: bool = True) -> List[str]:
        """
        Gibt die Liste der Recent Files zurück.
        
        Args:
            validate: Nur existierende Dateien zurückgeben
        
        Returns:
            Liste der Dateipfade
        """
        if self._current_profile is None:
            return []
        
        files = self._current_profile.workspace.recent_files
        
        if validate:
            files = [f for f in files if os.path.exists(f)]
        
        return files
    
    def update_chat_history(self, project_id: str, messages: List[Dict[str, str]]) -> None:
        """
        Aktualisiert Chat-Historie für ein Projekt.
        
        Args:
            project_id: Projekt-Identifier
            messages: Liste der Chat-Nachrichten
        """
        if self._current_profile is None:
            logger.warning("Kein Profil geladen")
            return
        
        self._current_profile.chat_history[project_id] = messages
        self.save()
    
    def get_chat_history(self, project_id: str) -> List[Dict[str, str]]:
        """
        Gibt Chat-Historie für ein Projekt zurück.
        
        Args:
            project_id: Projekt-Identifier
        
        Returns:
            Liste der Chat-Nachrichten
        """
        if self._current_profile is None:
            return []
        
        return self._current_profile.chat_history.get(project_id, [])
    
    def _get_username(self) -> str:
        """Ermittelt den Benutzernamen."""
        try:
            return getpass.getuser() or "user"
        except Exception:
            return "user"
    
    def _get_hostname(self) -> str:
        """Ermittelt den Hostnamen."""
        try:
            return socket.gethostname() or "host"
        except Exception:
            return "host"
    
    def __repr__(self) -> str:
        return f"<UserProfileManager user={self.username}@{self.hostname}>"
