"""
Simplified Tests for VPB Export Service
========================================

Basic test coverage for export functionality with real VPB element types.

Author: VPB Development Team
Date: 2025-10-14
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from xml.etree import ElementTree as ET

from vpb.services.export_service import (
    ExportService,
    ExportConfig,
    ExportServiceError,
    PDFExportError,
    SVGExportError,
    PNGExportError,
    BPMNExportError,
    MermaidExportError,
)
from vpb.models.document import DocumentModel
from vpb.models.element import VPBElement, ELEMENT_TYPES
from vpb.models.connection import VPBConnection, CONNECTION_TYPES


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create temporary directory for export tests."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def export_service():
    """Create export service with default configuration."""
    return ExportService()


@pytest.fixture
def simple_document():
    """Create a simple VPB document."""
    doc = DocumentModel()
    doc.metadata.title = "Simple Process"
    doc.metadata.description = "Test process"
    doc.metadata.author = "Test User"
    
    # Add elements with VPB types (no width/height needed - service provides defaults)
    ereignis = VPBElement(
        element_id="ereignis_1",
        element_type="Ereignis",
        name="Start",
        x=100, y=100
    )
    
    prozess = VPBElement(
        element_id="prozess_1",
        element_type="Prozess",
        name="Process Task",
        x=200, y=100
    )
    
    doc.add_element(ereignis)
    doc.add_element(prozess)
    
    # Add connection
    conn = VPBConnection(
        connection_id="conn_1",
        connection_type="SEQUENCE",
        source_element="ereignis_1",
        target_element="prozess_1"
    )
    
    doc.add_connection(conn)
    
    return doc


# ============================================================================
# Basic Tests
# ============================================================================

class TestExportServiceInit:
    """Test ExportService initialization."""
    
    def test_initialization(self):
        """Test service initialization."""
        service = ExportService()
        assert isinstance(service.config, ExportConfig)
        assert service.config.pdf_page_size == 'A4'


class TestPDFExport:
    """Test PDF export."""
    
    def test_export_simple_pdf(self, export_service, simple_document, temp_dir):
        """Test basic PDF export."""
        output_path = temp_dir / "test.pdf"
        
        result = export_service.export_to_pdf(simple_document, str(output_path))
        
        assert result.exists()
        assert result.suffix == '.pdf'
        assert result.stat().st_size > 0


class TestSVGExport:
    """Test SVG export."""
    
    def test_export_simple_svg(self, export_service, simple_document, temp_dir):
        """Test basic SVG export."""
        output_path = temp_dir / "test.svg"
        
        result = export_service.export_to_svg(simple_document, str(output_path))
        
        assert result.exists()
        assert result.suffix == '.svg'
        
        # Verify SVG structure
        tree = ET.parse(result)
        root = tree.getroot()
        assert 'svg' in root.tag


class TestPNGExport:
    """Test PNG export."""
    
    def test_export_simple_png(self, export_service, simple_document, temp_dir):
        """Test basic PNG export."""
        output_path = temp_dir / "test.png"
        
        result = export_service.export_to_png(simple_document, str(output_path))
        
        assert result.exists()
        assert result.suffix == '.png'
        assert result.stat().st_size > 0


class TestBPMNExport:
    """Test BPMN export."""
    
    def test_export_simple_bpmn(self, export_service, simple_document, temp_dir):
        """Test basic BPMN export."""
        output_path = temp_dir / "test.bpmn"
        
        result = export_service.export_to_bpmn(simple_document, str(output_path))
        
        assert result.exists()
        assert result.suffix == '.bpmn'
        
        # Verify BPMN structure
        tree = ET.parse(result)
        root = tree.getroot()
        assert 'definitions' in root.tag


class TestMermaidExport:
    """Test Mermaid export."""
    
    def test_export_simple_mermaid(self, export_service, simple_document, temp_dir):
        """Test basic Mermaid export."""
        output_path = temp_dir / "test.md"
        
        result = export_service.export_to_mermaid(simple_document, str(output_path))
        
        assert result.exists()
        assert result.suffix == '.md'
        
        # Verify Mermaid content
        content = result.read_text(encoding='utf-8')
        assert 'flowchart' in content
        assert 'node0' in content
        assert 'node1' in content
        assert '-->' in content
    
    def test_mermaid_with_different_direction(self, export_service, simple_document, temp_dir):
        """Test Mermaid export with left-to-right direction."""
        output_path = temp_dir / "test_lr.md"
        
        result = export_service.export_to_mermaid(
            simple_document, 
            str(output_path),
            direction="LR"
        )
        
        content = result.read_text(encoding='utf-8')
        assert 'flowchart LR' in content
    
    def test_mermaid_includes_metadata(self, export_service, simple_document, temp_dir):
        """Test that Mermaid export includes metadata."""
        output_path = temp_dir / "test_meta.md"
        
        result = export_service.export_to_mermaid(simple_document, str(output_path))
        
        content = result.read_text(encoding='utf-8')
        assert 'title: Simple Process' in content
        assert 'author: Test User' in content

