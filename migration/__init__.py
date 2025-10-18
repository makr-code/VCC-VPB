"""
Migration Infrastructure for VPB SQLite → UDS3 Polyglot
Version: 1.0.0
"""

from .migration_tool import VPBMigrationTool, MigrationConfig, MigrationResult
from .gap_detector import GapDetector, DataGap, GapType
from .validation import DataValidator, ValidationResult

__all__ = [
    'VPBMigrationTool',
    'MigrationConfig',
    'MigrationResult',
    'GapDetector',
    'DataGap',
    'GapType',
    'DataValidator',
    'ValidationResult'
]

__version__ = '1.0.0'
