"""
VPB Dialog Views
================

Dialog windows for VPB Process Designer.

This package contains:
- AboutDialog: About/Info dialog
- SettingsDialog: Application settings
- ExportDialog: Export to PNG/SVG/PDF
- ElementEditorDialog: Advanced element editing
- ValidationResultsDialog: Validation results display
"""

from .about_dialog import AboutDialog, create_about_dialog

__all__ = [
    'AboutDialog',
    'create_about_dialog',
]
