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


class TestMermaidERDExport:
    """Test Mermaid ERD export."""
    
    def test_export_erd_basic(self, export_service, temp_dir):
        """Test basic ERD export."""
        from vpb.models.document import DocumentModel
        from vpb.models.element import VPBElement
        from vpb.models.connection import VPBConnection
        
        # Create a database schema document
        doc = DocumentModel()
        doc.metadata.title = "Database Schema"
        doc.metadata.description = "Example database schema"
        
        # Create entities (tables)
        user = VPBElement(
            element_id='user',
            element_type='Prozess',
            name='User',
            x=0, y=0,
            description='id int PK\nname string\nemail string'
        )
        
        post = VPBElement(
            element_id='post',
            element_type='Prozess',
            name='Post',
            x=100, y=0,
            description='id int PK\ntitle string\ncontent text\nuser_id int FK'
        )
        
        doc.add_element(user)
        doc.add_element(post)
        
        # Add relationship
        rel = VPBConnection(
            connection_id='user_posts',
            source_element='user',
            target_element='post',
            description='1:N'
        )
        doc.add_connection(rel)
        
        # Export as ERD
        output_path = temp_dir / "schema.md"
        result = export_service.export_to_mermaid(
            doc,
            str(output_path),
            diagram_type='erDiagram'
        )
        
        assert result.exists()
        content = result.read_text(encoding='utf-8')
        assert 'erDiagram' in content
        assert 'User' in content
        assert 'Post' in content
        assert '||--o{' in content or '}o--' in content  # Relationship syntax
    
    def test_export_erd_relationships(self, export_service, temp_dir):
        """Test ERD with different relationship types."""
        from vpb.models.document import DocumentModel
        from vpb.models.element import VPBElement
        from vpb.models.connection import VPBConnection
        
        doc = DocumentModel()
        doc.metadata.title = "Relationship Test"
        
        # Create entities
        e1 = VPBElement(element_id='e1', element_type='Prozess', name='Entity1', x=0, y=0)
        e2 = VPBElement(element_id='e2', element_type='Prozess', name='Entity2', x=100, y=0)
        
        doc.add_element(e1)
        doc.add_element(e2)
        
        # Test one-to-many relationship
        rel = VPBConnection(
            connection_id='rel1',
            source_element='e1',
            target_element='e2',
            description='one-to-many'
        )
        doc.add_connection(rel)
        
        output_path = temp_dir / "relationships.md"
        result = export_service.export_to_mermaid(
            doc,
            str(output_path),
            diagram_type='erDiagram'
        )
        
        content = result.read_text(encoding='utf-8')
        assert 'erDiagram' in content
        assert 'Entity1' in content
        assert 'Entity2' in content


