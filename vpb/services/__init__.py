"""
VPB Services Layer
==================

Business logic and operations for VPB Process Designer.

This package contains:
- DocumentService: Document load/save operations, recent files management
- ValidationService: Process validation (flow, naming, completeness)
- ExportService: Export to PDF/SVG/PNG/BPMN formats
- LayoutService: Auto-layout algorithms, element alignment, arrangement
- AIService: AI-powered process generation, suggestions, diagnostics
"""

from .document_service import (
    DocumentService,
    DocumentServiceError,
    DocumentLoadError,
    DocumentSaveError,
)
from .validation_service import (
    ValidationService,
    ValidationResult,
    ValidationIssue,
    IssueSeverity,
)
from .export_service import (
    ExportService,
    ExportConfig,
    ExportServiceError,
    PDFExportError,
    SVGExportError,
    PNGExportError,
    BPMNExportError,
)
from .layout_service import (
    LayoutService,
    LayoutConfig,
    LayoutResult,
    LayoutServiceError,
    InsufficientElementsError,
)
from .ai_service import (
    AIService,
    AIConfig,
    AIResult,
    AIServiceError,
    OllamaConnectionError,
    ValidationError,
)

__all__ = [
    # Document Service
    'DocumentService',
    'DocumentServiceError',
    'DocumentLoadError',
    'DocumentSaveError',
    # Validation Service
    'ValidationService',
    'ValidationResult',
    'ValidationIssue',
    'IssueSeverity',
    # Export Service
    'ExportService',
    'ExportConfig',
    'ExportServiceError',
    'PDFExportError',
    'SVGExportError',
    'PNGExportError',
    'BPMNExportError',
    # Layout Service
    'LayoutService',
    'LayoutConfig',
    'LayoutResult',
    'LayoutServiceError',
    'InsufficientElementsError',
    # AI Service
    'AIService',
    'AIConfig',
    'AIResult',
    'AIServiceError',
    'OllamaConnectionError',
    'ValidationError',
]
