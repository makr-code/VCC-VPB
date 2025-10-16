"""
VPB Infrastructure Layer
========================

Core infrastructure components for the VPB Process Designer.

This package contains:
- Event-Bus System for loose coupling
- Settings Manager for configuration
- Legacy Bridge for migration compatibility
"""

from .event_bus import EventBus, get_global_event_bus
from .settings_manager import (
    SettingsManager,
    AppSettings,
    OllamaSettings,
    WindowSettings,
    SidebarSettings,
    ViewSettings,
    NavigationSettings,
    OnboardingSettings,
    AutosaveSettings,
)

__all__ = [
    'EventBus',
    'get_global_event_bus',
    'SettingsManager',
    'AppSettings',
    'OllamaSettings',
    'WindowSettings',
    'SidebarSettings',
    'ViewSettings',
    'NavigationSettings',
    'OnboardingSettings',
    'AutosaveSettings',
]
