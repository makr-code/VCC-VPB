"""
Settings Manager for VPB Process Designer
==========================================

Manages loading and saving of application settings (settings.json).
Provides structured access to all configuration values.

Features:
- Robust loading with defaults
- Type-safe property access
- Migration from legacy vpb_settings.json
- No direct UI dependencies
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, Optional, Union
import json
import logging


logger = logging.getLogger(__name__)


@dataclass
class OllamaSettings:
    """Ollama AI configuration."""
    endpoint: str = "http://localhost:11434"
    model: str = "llama:latest"
    temperature: float = 0.2
    num_predict: int = 600
    
    def validate(self) -> None:
        """Validate and clamp values."""
        self.temperature = max(0.0, min(1.0, self.temperature))
        self.num_predict = max(1, self.num_predict)


@dataclass
class WindowSettings:
    """Window geometry and state."""
    width: int = 1200
    height: int = 800
    x: Optional[int] = None
    y: Optional[int] = None
    state: str = ""  # "normal", "zoomed", "iconic"


@dataclass
class SidebarSettings:
    """Sidebar widths."""
    left_width: int = 250
    right_width: int = 250


@dataclass
class ViewSettings:
    """Canvas view preferences."""
    grid_visible: bool = True
    snap_to_grid: bool = False
    routing_style: str = "smart"
    time_axis_enabled: bool = True
    time_axis_interval: float = 100.0
    mousewheel_behavior: str = "zoom-primary"  # or "pan-primary"


@dataclass
class NavigationSettings:
    """Keyboard navigation step sizes."""
    nudge_small: int = 2
    nudge_big: int = 10
    pan_small: int = 30
    pan_big: int = 60


@dataclass
class OnboardingSettings:
    """User onboarding state."""
    pan_hint_dismissed: bool = False


@dataclass
class AutosaveSettings:
    """Autosave configuration."""
    enabled: bool = True
    interval_minutes: int = 3


@dataclass
class AppSettings:
    """Complete application settings."""
    ollama: OllamaSettings = field(default_factory=OllamaSettings)
    window: WindowSettings = field(default_factory=WindowSettings)
    sidebars: SidebarSettings = field(default_factory=SidebarSettings)
    view: ViewSettings = field(default_factory=ViewSettings)
    navigation: NavigationSettings = field(default_factory=NavigationSettings)
    onboarding: OnboardingSettings = field(default_factory=OnboardingSettings)
    autosave: AutosaveSettings = field(default_factory=AutosaveSettings)
    element_styles: Dict[str, Any] = field(default_factory=dict)
    hierarchy_categories: list = field(default_factory=list)


class SettingsManager:
    """
    Manages application settings persistence.
    
    Example:
        ```python
        manager = SettingsManager("settings.json")
        settings = manager.load()
        
        # Access settings
        print(settings.ollama.endpoint)
        print(settings.view.grid_visible)
        
        # Modify and save
        settings.view.grid_visible = False
        manager.save(settings)
        ```
    """
    
    def __init__(self, settings_path: Union[str, Path]):
        """
        Initialize settings manager.
        
        Args:
            settings_path: Path to settings.json file
        """
        self.settings_path = Path(settings_path)
        
        # Legacy settings path (for migration)
        base_dir = self.settings_path.parent
        self.legacy_path = base_dir / "vpb_settings.json"
        
        self._current_settings: Optional[AppSettings] = None
    
    def load(self) -> AppSettings:
        """
        Load settings from file or create defaults.
        
        Returns:
            AppSettings instance with loaded or default values
        """
        data: Dict[str, Any] = {}
        
        # Try to load from primary path
        if self.settings_path.exists():
            try:
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
                    if isinstance(raw, dict):
                        data = raw
                logger.info(f"Loaded settings from {self.settings_path}")
            except Exception as e:
                logger.error(f"Failed to load settings from {self.settings_path}: {e}")
        
        # Fallback to legacy path
        elif self.legacy_path.exists():
            try:
                with open(self.legacy_path, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
                    if isinstance(raw, dict):
                        data = raw
                logger.info(f"Migrated settings from legacy {self.legacy_path}")
            except Exception as e:
                logger.error(f"Failed to load legacy settings: {e}")
        
        # Parse into structured settings
        settings = self._parse_settings(data)
        self._current_settings = settings
        
        return settings
    
    def save(self, settings: Optional[AppSettings] = None) -> bool:
        """
        Save settings to file.
        
        Args:
            settings: Settings to save (uses last loaded if None)
            
        Returns:
            True if save succeeded, False otherwise
        """
        if settings is None:
            settings = self._current_settings
        
        if settings is None:
            logger.warning("No settings to save")
            return False
        
        try:
            # Convert to dict
            data = self._settings_to_dict(settings)
            
            # Ensure directory exists
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to file
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Settings saved to {self.settings_path}")
            self._current_settings = settings
            return True
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False
    
    def get_current(self) -> Optional[AppSettings]:
        """Get currently loaded settings."""
        return self._current_settings
    
    def _parse_settings(self, data: Dict[str, Any]) -> AppSettings:
        """Parse dictionary into AppSettings structure."""
        settings = AppSettings()
        
        # Ollama settings
        if 'ollama_endpoint' in data or 'ollama_model' in data:
            # Legacy flat structure
            settings.ollama = OllamaSettings(
                endpoint=data.get('ollama_endpoint', settings.ollama.endpoint),
                model=data.get('ollama_model', settings.ollama.model),
                temperature=float(data.get('ollama_temperature', settings.ollama.temperature)),
                num_predict=int(data.get('ollama_num_predict', settings.ollama.num_predict))
            )
        elif 'ollama' in data and isinstance(data['ollama'], dict):
            # New nested structure
            ollama_data = data['ollama']
            settings.ollama = OllamaSettings(
                endpoint=ollama_data.get('endpoint', settings.ollama.endpoint),
                model=ollama_data.get('model', settings.ollama.model),
                temperature=float(ollama_data.get('temperature', settings.ollama.temperature)),
                num_predict=int(ollama_data.get('num_predict', settings.ollama.num_predict))
            )
        settings.ollama.validate()
        
        # Window settings
        if 'window' in data and isinstance(data['window'], dict):
            win = data['window']
            settings.window = WindowSettings(
                width=int(win.get('width', settings.window.width)),
                height=int(win.get('height', settings.window.height)),
                x=win.get('x'),
                y=win.get('y'),
                state=str(win.get('state', ''))
            )
        
        # Sidebar settings
        if 'sidebars' in data and isinstance(data['sidebars'], dict):
            sb = data['sidebars']
            settings.sidebars = SidebarSettings(
                left_width=int(sb.get('left_width', settings.sidebars.left_width)),
                right_width=int(sb.get('right_width', settings.sidebars.right_width))
            )
        
        # View settings
        if 'view' in data and isinstance(data['view'], dict):
            view = data['view']
            settings.view = ViewSettings(
                grid_visible=bool(view.get('grid_visible', settings.view.grid_visible)),
                snap_to_grid=bool(view.get('snap_to_grid', settings.view.snap_to_grid)),
                routing_style=str(view.get('routing_style', settings.view.routing_style)),
                time_axis_enabled=bool(view.get('time_axis_enabled', settings.view.time_axis_enabled)),
                time_axis_interval=float(view.get('time_axis_interval', settings.view.time_axis_interval)),
                mousewheel_behavior=str(view.get('mousewheel_behavior', settings.view.mousewheel_behavior))
            )
        
        # Navigation settings
        if 'navigation' in data and isinstance(data['navigation'], dict):
            nav = data['navigation']
            settings.navigation = NavigationSettings(
                nudge_small=int(nav.get('nudge_small', settings.navigation.nudge_small)),
                nudge_big=int(nav.get('nudge_big', settings.navigation.nudge_big)),
                pan_small=int(nav.get('pan_small', settings.navigation.pan_small)),
                pan_big=int(nav.get('pan_big', settings.navigation.pan_big))
            )
        
        # Onboarding settings
        if 'onboarding' in data and isinstance(data['onboarding'], dict):
            ob = data['onboarding']
            settings.onboarding = OnboardingSettings(
                pan_hint_dismissed=bool(ob.get('pan_hint_dismissed', False))
            )
        
        # Autosave settings
        if 'autosave' in data and isinstance(data['autosave'], dict):
            aus = data['autosave']
            settings.autosave = AutosaveSettings(
                enabled=bool(aus.get('enabled', settings.autosave.enabled)),
                interval_minutes=int(aus.get('interval_minutes', settings.autosave.interval_minutes))
            )
        
        # Element styles and hierarchy
        if 'element_styles' in data and isinstance(data['element_styles'], dict):
            settings.element_styles = data['element_styles']
        
        if 'hierarchy_categories' in data and isinstance(data['hierarchy_categories'], list):
            settings.hierarchy_categories = data['hierarchy_categories']
        
        return settings
    
    def _settings_to_dict(self, settings: AppSettings) -> Dict[str, Any]:
        """Convert AppSettings to dictionary for JSON serialization."""
        return {
            'ollama': {
                'endpoint': settings.ollama.endpoint,
                'model': settings.ollama.model,
                'temperature': settings.ollama.temperature,
                'num_predict': settings.ollama.num_predict,
            },
            'window': {
                'width': settings.window.width,
                'height': settings.window.height,
                'x': settings.window.x,
                'y': settings.window.y,
                'state': settings.window.state,
            },
            'sidebars': {
                'left_width': settings.sidebars.left_width,
                'right_width': settings.sidebars.right_width,
            },
            'view': {
                'grid_visible': settings.view.grid_visible,
                'snap_to_grid': settings.view.snap_to_grid,
                'routing_style': settings.view.routing_style,
                'time_axis_enabled': settings.view.time_axis_enabled,
                'time_axis_interval': settings.view.time_axis_interval,
                'mousewheel_behavior': settings.view.mousewheel_behavior,
            },
            'navigation': {
                'nudge_small': settings.navigation.nudge_small,
                'nudge_big': settings.navigation.nudge_big,
                'pan_small': settings.navigation.pan_small,
                'pan_big': settings.navigation.pan_big,
            },
            'onboarding': {
                'pan_hint_dismissed': settings.onboarding.pan_hint_dismissed,
            },
            'autosave': {
                'enabled': settings.autosave.enabled,
                'interval_minutes': settings.autosave.interval_minutes,
            },
            'element_styles': settings.element_styles,
            'hierarchy_categories': settings.hierarchy_categories,
        }
