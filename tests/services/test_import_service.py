"""
Tests for VPB Import Service
=============================

Test coverage for import functionality, specifically Mermaid import.

Author: VPB Development Team
Date: 2026-01-22
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from vpb.services.import_service import (
    ImportService,
    ImportConfig,
    ImportServiceError,
    MermaidImportError,
    UnsupportedDiagramError,
)
from vpb.models.document import DocumentModel
from vpb.models.element import VPBElement
from vpb.models.connection import VPBConnection


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create temporary directory for import tests."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)


@pytest.fixture
def import_service():
    """Create import service with default configuration."""
    return ImportService()


@pytest.fixture
def simple_mermaid_flowchart(temp_dir):
    """Create a simple Mermaid flowchart file."""
    content = """```mermaid
flowchart LR
    Start([Start]) --> Process[Process Task]
    Process --> End([End])
```
"""
    file_path = temp_dir / "simple.md"
    file_path.write_text(content, encoding='utf-8')
    return file_path


@pytest.fixture
def mermaid_with_metadata(temp_dir):
    """Create Mermaid file with YAML metadata."""
    content = """---
title: Test Process
description: A test process diagram
author: Test User
---

```mermaid
flowchart TB
    A([Start]) --> B[Task]
    B --> C([End])
```
"""
    file_path = temp_dir / "with_metadata.md"
    file_path.write_text(content, encoding='utf-8')
    return file_path


@pytest.fixture
def mermaid_with_decision(temp_dir):
    """Create Mermaid with decision gateway."""
    content = """```mermaid
flowchart TB
    Start([Start]) --> Check{Decision?}
    Check -->|Yes| TaskA[Process A]
    Check -->|No| TaskB[Process B]
    TaskA --> End([End])
    TaskB --> End
```
"""
    file_path = temp_dir / "decision.md"
    file_path.write_text(content, encoding='utf-8')
    return file_path


@pytest.fixture
def mermaid_complex_flow(temp_dir):
    """Create a more complex Mermaid flowchart."""
    content = """```mermaid
flowchart LR
    S([Start]) --> A[Task A]
    A --> B{Check B}
    B -->|Pass| C[Task C]
    B -->|Fail| D[Task D]
    C --> E[Task E]
    D --> E
    E --> F{Final Check}
    F -->|OK| G([Success])
    F -->|Error| H([Failure])
```
"""
    file_path = temp_dir / "complex.md"
    file_path.write_text(content, encoding='utf-8')
    return file_path


@pytest.fixture
def unsupported_mermaid(temp_dir):
    """Create unsupported diagram type (ERD)."""
    content = """```mermaid
erDiagram
    USER ||--o{ ORDER : places
    ORDER ||--|{ LINE-ITEM : contains
```
"""
    file_path = temp_dir / "unsupported.md"
    file_path.write_text(content, encoding='utf-8')
    return file_path


# ============================================================================
# Basic Tests
# ============================================================================

class TestImportServiceInit:
    """Test ImportService initialization."""
    
    def test_initialization(self):
        """Test service initialization."""
        service = ImportService()
        assert isinstance(service.config, ImportConfig)
        assert service.config.mermaid_auto_layout is True
    
    def test_custom_config(self):
        """Test initialization with custom config."""
        config = ImportConfig(
            mermaid_default_spacing_x=300,
            validate_bpmn_compatibility=False
        )
        service = ImportService(config)
        assert service.config.mermaid_default_spacing_x == 300
        assert service.config.validate_bpmn_compatibility is False


class TestMermaidImport:
    """Test Mermaid import functionality."""
    
    def test_import_simple_flowchart(self, import_service, simple_mermaid_flowchart):
        """Test importing a simple Mermaid flowchart."""
        doc = import_service.import_from_mermaid(str(simple_mermaid_flowchart))
        
        assert isinstance(doc, DocumentModel)
        assert doc.metadata.title == "simple"
        
        # Check elements
        elements = doc.get_all_elements()
        assert len(elements) == 3  # Start, Process, End
        
        # Check element types
        element_types = [e.element_type for e in elements]
        assert 'Ereignis' in element_types  # Start/End events
        assert 'Prozess' in element_types  # Process task
        
        # Check connections
        connections = doc.get_all_connections()
        assert len(connections) == 2  # Start->Process, Process->End
    
    def test_import_with_custom_title(self, import_service, simple_mermaid_flowchart):
        """Test importing with custom title."""
        doc = import_service.import_from_mermaid(
            str(simple_mermaid_flowchart),
            title="Custom Process"
        )
        
        assert doc.metadata.title == "Custom Process"
    
    def test_import_with_metadata(self, import_service, mermaid_with_metadata):
        """Test importing Mermaid with YAML metadata."""
        doc = import_service.import_from_mermaid(str(mermaid_with_metadata))
        
        assert doc.metadata.title == "with_metadata"  # Uses filename as title
        # Metadata from YAML is parsed but not directly set in DocumentMetadata
        # (could be enhanced in future)
    
    def test_import_with_decision(self, import_service, mermaid_with_decision):
        """Test importing flowchart with decision gateway."""
        doc = import_service.import_from_mermaid(str(mermaid_with_decision))
        
        elements = doc.get_all_elements()
        
        # Find decision element
        decisions = [e for e in elements if e.element_type == 'Entscheidung']
        assert len(decisions) == 1
        assert decisions[0].name == "Decision?"
        
        # Check connections with labels
        connections = doc.get_all_connections()
        labeled_conns = [c for c in connections if c.description]
        assert len(labeled_conns) >= 2  # Yes and No branches
    
    def test_import_complex_flow(self, import_service, mermaid_complex_flow):
        """Test importing complex flowchart."""
        doc = import_service.import_from_mermaid(str(mermaid_complex_flow))
        
        elements = doc.get_all_elements()
        assert len(elements) == 9  # S, A, B, C, D, E, F, G, H
        
        # Check multiple decision points
        decisions = [e for e in elements if e.element_type == 'Entscheidung']
        assert len(decisions) == 2  # Check B and Final Check
        
        # Check connections
        connections = doc.get_all_connections()
        assert len(connections) == 9  # All arrows in diagram
    
    def test_import_tb_direction(self, import_service, temp_dir):
        """Test importing flowchart with TB (top-bottom) direction."""
        content = """```mermaid
flowchart TB
    A --> B --> C
```
"""
        file_path = temp_dir / "tb.md"
        file_path.write_text(content, encoding='utf-8')
        
        doc = import_service.import_from_mermaid(str(file_path))
        elements = doc.get_all_elements()
        
        # In TB layout, Y coordinates should increase
        a = next(e for e in elements if e.element_id == 'A')
        b = next(e for e in elements if e.element_id == 'B')
        c = next(e for e in elements if e.element_id == 'C')
        
        assert a.y < b.y < c.y or a.y == b.y  # Y increases down
    
    def test_import_lr_direction(self, import_service, temp_dir):
        """Test importing flowchart with LR (left-right) direction."""
        content = """```mermaid
flowchart LR
    A --> B --> C
```
"""
        file_path = temp_dir / "lr.md"
        file_path.write_text(content, encoding='utf-8')
        
        doc = import_service.import_from_mermaid(str(file_path))
        elements = doc.get_all_elements()
        
        # In LR layout, X coordinates should increase
        a = next(e for e in elements if e.element_id == 'A')
        b = next(e for e in elements if e.element_id == 'B')
        c = next(e for e in elements if e.element_id == 'C')
        
        assert a.x < b.x < c.x or a.x == b.x  # X increases right
    
    def test_import_graph_syntax(self, import_service, temp_dir):
        """Test importing using 'graph' syntax (older Mermaid syntax)."""
        content = """```mermaid
graph TD
    Start --> End
```
"""
        file_path = temp_dir / "graph.md"
        file_path.write_text(content, encoding='utf-8')
        
        doc = import_service.import_from_mermaid(str(file_path))
        assert len(doc.get_all_elements()) == 2
    
    def test_import_dotted_connection(self, import_service, temp_dir):
        """Test importing flowchart with dotted connections."""
        content = """```mermaid
flowchart LR
    A --> B
    B -.-> C
```
"""
        file_path = temp_dir / "dotted.md"
        file_path.write_text(content, encoding='utf-8')
        
        doc = import_service.import_from_mermaid(str(file_path))
        connections = doc.get_all_connections()
        
        # One should be SEQUENCE, one should be INFORMATION (dotted)
        conn_types = [c.connection_type for c in connections]
        assert 'SEQUENCE' in conn_types
        assert 'INFORMATION' in conn_types


class TestErrorHandling:
    """Test error handling in import service."""
    
    def test_import_nonexistent_file(self, import_service):
        """Test importing from non-existent file."""
        with pytest.raises(MermaidImportError, match="File not found"):
            import_service.import_from_mermaid("nonexistent.md")
    
    def test_import_unsupported_diagram(self, import_service, unsupported_mermaid):
        """Test importing unsupported diagram type."""
        with pytest.raises(UnsupportedDiagramError, match="cannot be converted to BPMN"):
            import_service.import_from_mermaid(str(unsupported_mermaid))
    
    def test_import_no_diagram(self, import_service, temp_dir):
        """Test importing file with no valid diagram."""
        content = "Just some text, no diagram here"
        file_path = temp_dir / "no_diagram.md"
        file_path.write_text(content, encoding='utf-8')
        
        with pytest.raises(MermaidImportError, match="No valid Mermaid diagram found"):
            import_service.import_from_mermaid(str(file_path))
    
    def test_import_class_diagram(self, import_service, temp_dir):
        """Test that class diagrams are rejected."""
        content = """```mermaid
classDiagram
    Class01 <|-- Class02
```
"""
        file_path = temp_dir / "class.md"
        file_path.write_text(content, encoding='utf-8')
        
        with pytest.raises(UnsupportedDiagramError):
            import_service.import_from_mermaid(str(file_path))
    
    def test_import_sequence_diagram(self, import_service, temp_dir):
        """Test that sequence diagrams are rejected."""
        content = """```mermaid
sequenceDiagram
    Alice->>Bob: Hello
```
"""
        file_path = temp_dir / "sequence.md"
        file_path.write_text(content, encoding='utf-8')
        
        with pytest.raises(UnsupportedDiagramError):
            import_service.import_from_mermaid(str(file_path))


class TestShapeMapping:
    """Test Mermaid shape to VPB element type mapping."""
    
    def test_rectangle_shape(self, import_service, temp_dir):
        """Test rectangle shape maps to Prozess."""
        content = """```mermaid
flowchart LR
    A[Task]
```
"""
        file_path = temp_dir / "rect.md"
        file_path.write_text(content, encoding='utf-8')
        
        doc = import_service.import_from_mermaid(str(file_path))
        element = doc.get_all_elements()[0]
        assert element.element_type == 'Prozess'
    
    def test_stadium_shape(self, import_service, temp_dir):
        """Test stadium shape maps to Ereignis."""
        content = """```mermaid
flowchart LR
    A([Event])
```
"""
        file_path = temp_dir / "stadium.md"
        file_path.write_text(content, encoding='utf-8')
        
        doc = import_service.import_from_mermaid(str(file_path))
        element = doc.get_all_elements()[0]
        assert element.element_type == 'Ereignis'
    
    def test_diamond_shape(self, import_service, temp_dir):
        """Test diamond shape maps to Entscheidung."""
        content = """```mermaid
flowchart LR
    A{Decision}
```
"""
        file_path = temp_dir / "diamond.md"
        file_path.write_text(content, encoding='utf-8')
        
        doc = import_service.import_from_mermaid(str(file_path))
        element = doc.get_all_elements()[0]
        assert element.element_type == 'Entscheidung'
    
    def test_subprocess_shape(self, import_service, temp_dir):
        """Test subprocess shape maps to Container."""
        content = """```mermaid
flowchart LR
    A[[Subprocess]]
```
"""
        file_path = temp_dir / "subprocess.md"
        file_path.write_text(content, encoding='utf-8')
        
        doc = import_service.import_from_mermaid(str(file_path))
        element = doc.get_all_elements()[0]
        assert element.element_type == 'Container'


class TestLayoutCalculation:
    """Test layout calculation for imported diagrams."""
    
    def test_positions_assigned(self, import_service, simple_mermaid_flowchart):
        """Test that all elements get positions assigned."""
        doc = import_service.import_from_mermaid(str(simple_mermaid_flowchart))
        
        for element in doc.get_all_elements():
            assert element.x is not None
            assert element.y is not None
            assert element.x >= 0
            assert element.y >= 0
    
    def test_no_overlapping_positions(self, import_service, simple_mermaid_flowchart):
        """Test that elements don't have identical positions."""
        doc = import_service.import_from_mermaid(str(simple_mermaid_flowchart))
        
        positions = [(e.x, e.y) for e in doc.get_all_elements()]
        # In a simple linear flow, positions should differ
        assert len(positions) == len(set(positions))


class TestRoundTripCompatibility:
    """Test that imported diagrams can be exported."""
    
    def test_import_then_export_mermaid(
        self,
        import_service,
        simple_mermaid_flowchart,
        temp_dir
    ):
        """Test importing Mermaid and exporting back to Mermaid."""
        from vpb.services.export_service import ExportService
        
        # Import
        doc = import_service.import_from_mermaid(str(simple_mermaid_flowchart))
        
        # Export
        export_service = ExportService()
        output_path = temp_dir / "exported.md"
        export_service.export_to_mermaid(doc, str(output_path))
        
        assert output_path.exists()
        content = output_path.read_text(encoding='utf-8')
        assert 'flowchart' in content
    
    def test_import_then_export_bpmn(
        self,
        import_service,
        simple_mermaid_flowchart,
        temp_dir
    ):
        """Test importing Mermaid and exporting to BPMN."""
        from vpb.services.export_service import ExportService
        
        # Import
        doc = import_service.import_from_mermaid(str(simple_mermaid_flowchart))
        
        # Export to BPMN
        export_service = ExportService()
        output_path = temp_dir / "exported.bpmn"
        export_service.export_to_bpmn(doc, str(output_path))
        
        assert output_path.exists()
        # Verify BPMN structure
        from xml.etree import ElementTree as ET
        tree = ET.parse(output_path)
        root = tree.getroot()
        assert 'definitions' in root.tag
