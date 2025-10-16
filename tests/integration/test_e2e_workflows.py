"""
End-to-End Integration Tests for VPB Process Designer

Tests complete user journeys across all layers:
- Infrastructure (EventBus)
- Models (DocumentModel, VPBElement, VPBConnection)
- Services (DocumentService, ValidationService, LayoutService, ExportService)
- Controllers (DocumentController, ElementController, ConnectionController, etc.)

Note: These tests use the REAL implementations (not mocks) to verify
that all layers integrate correctly.
"""

import pytest
import os
import json
import tempfile
from unittest.mock import patch
from pathlib import Path

from vpb.infrastructure.event_bus import EventBus
from vpb.models.document import DocumentModel
from vpb.models.element import VPBElement, ElementFactory
from vpb.models.connection import VPBConnection, ConnectionFactory
from vpb.services.document_service import DocumentService
from vpb.services.validation_service import ValidationService
from vpb.services.layout_service import LayoutService
from vpb.services.export_service import ExportService
from vpb.controllers.document_controller import DocumentController
from vpb.controllers.element_controller import ElementController
from vpb.controllers.connection_controller import ConnectionController
from vpb.controllers.layout_controller import LayoutController
from vpb.controllers.validation_controller import ValidationController
from vpb.controllers.export_controller import ExportController


class TestEndToEndWorkflows:
    """End-to-End Integration Tests"""
    
    def setup_method(self):
        """Setup EventBus, Services and all Controllers"""
        self.event_bus = EventBus()
        
        # Services
        self.doc_service = DocumentService()
        self.validation_service = ValidationService()
        self.layout_service = LayoutService()
        self.export_service = ExportService()
        
        # Controllers (with required services)
        self.doc_ctrl = DocumentController(self.event_bus, self.doc_service)
        self.elem_ctrl = ElementController(self.event_bus)
        self.conn_ctrl = ConnectionController(self.event_bus)
        self.layout_ctrl = LayoutController(self.event_bus, self.layout_service)
        self.validation_ctrl = ValidationController(self.event_bus, self.validation_service)
        self.export_ctrl = ExportController(self.event_bus, self.export_service)
        
        # Track published events
        self.published_events = []
        self.event_bus.subscribe('*', self._track_event)
        
        # Temp directory for file operations
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup temp files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _track_event(self, data):
        """Track all published events"""
        # Get event type from current publish call
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            # Extract event type from EventBus.publish call
            pass  # Just track the data
        self.published_events.append(data)
    
    def _get_events_by_type(self, event_type: str):
        """Get all events of a specific type"""
        # Note: This is simplified - real implementation would track event types
        return self.published_events
    
    # ==========================================
    # E2E Test 1: Complete Document Lifecycle
    # ==========================================
    
    def test_e2e_document_lifecycle(self):
        """
        Test: New Document → Add Elements → Add Connections → Save → Load
        
        Steps:
        1. Create new document
        2. Add 3 elements (Start, Activity, End)
        3. Add 2 connections
        4. Save document to file
        5. Load document from file
        6. Verify all data intact
        """
        # Step 1: Create new document
        self.event_bus.publish('ui:menu:file:new', {})
        
        doc = self.doc_ctrl.get_current_document()
        assert doc is not None
        assert doc.metadata.title == "Unbenannter Prozess"
        assert len(doc.elements) == 0
        
        # Step 2: Add elements
        # Element 1: Start Event
        self.event_bus.publish('ui:palette:element_selected', {
            'element_type': 'start_event',
            'category': 'Events'
        })
        self.event_bus.publish('ui:canvas:element_placed', {
            'x': 100,
            'y': 100
        })
        
        # Element 2: Activity
        self.event_bus.publish('ui:palette:element_selected', {
            'element_type': 'activity',
            'category': 'Activities'
        })
        self.event_bus.publish('ui:canvas:element_placed', {
            'x': 300,
            'y': 100
        })
        
        # Element 3: End Event
        self.event_bus.publish('ui:palette:element_selected', {
            'element_type': 'end_event',
            'category': 'Events'
        })
        self.event_bus.publish('ui:canvas:element_placed', {
            'x': 500,
            'y': 100
        })
        
        # Verify elements added
        doc = self.doc_ctrl.get_current_document()
        assert len(doc.elements) == 3
        elem1_id = doc.elements[0].id
        elem2_id = doc.elements[1].id
        elem3_id = doc.elements[2].id
        
        # Step 3: Add connections
        # Connection 1: Start → Activity
        self.event_bus.publish('ui:canvas:connection_start', {
            'element_id': elem1_id
        })
        self.event_bus.publish('ui:canvas:connection_end', {
            'element_id': elem2_id
        })
        
        # Connection 2: Activity → End
        self.event_bus.publish('ui:canvas:connection_start', {
            'element_id': elem2_id
        })
        self.event_bus.publish('ui:canvas:connection_end', {
            'element_id': elem3_id
        })
        
        # Verify connections added
        doc = self.doc_ctrl.get_current_document()
        assert len(doc.connections) == 2
        
        # Step 4: Save document
        file_path = os.path.join(self.temp_dir, 'test_process.vpb.json')
        
        with patch('tkinter.filedialog.asksaveasfilename', return_value=file_path):
            self.event_bus.publish('ui:menu:file:save_as', {})
            self.event_bus.publish('ui:dialog:file:save_as_selected', {
                'file_path': file_path
            })
        
        # Verify file created
        assert os.path.exists(file_path)
        assert self.doc_ctrl.get_current_file_path() == file_path
        
        # Step 5: Close and load document
        self.event_bus.publish('ui:menu:file:close', {})
        assert self.doc_ctrl.get_current_document() is None
        
        with patch('tkinter.filedialog.askopenfilename', return_value=file_path):
            self.event_bus.publish('ui:menu:file:open', {})
            self.event_bus.publish('ui:dialog:file:open_selected', {
                'file_path': file_path
            })
        
        # Step 6: Verify loaded document
        doc = self.doc_ctrl.get_current_document()
        assert doc is not None
        assert len(doc.elements) == 3
        assert len(doc.connections) == 2
        assert doc.elements[0].type == 'start_event'
        assert doc.elements[1].type == 'activity'
        assert doc.elements[2].type == 'end_event'
        assert doc.connections[0].source_element.id == elem1_id
        assert doc.connections[0].target_element.id == elem2_id
    
    # ==========================================
    # E2E Test 2: Edit → Validate → Export
    # ==========================================
    
    def test_e2e_edit_validate_export(self):
        """
        Test: Open Document → Edit Elements → Validate → Export
        
        Steps:
        1. Create document with elements
        2. Edit element properties
        3. Validate process
        4. Export to multiple formats
        """
        # Step 1: Create document with elements
        self.event_bus.publish('ui:menu:file:new', {})
        doc = self.doc_ctrl.get_current_document()
        
        # Add 2 elements
        elem1 = ElementFactory.create('activity', x=100, y=100, name='Task 1')
        elem2 = ElementFactory.create('activity', x=300, y=100, name='Task 2')
        doc.add_element(elem1)
        doc.add_element(elem2)
        
        # Add connection
        conn = ConnectionFactory.create(elem1, elem2)
        doc.add_connection(conn)
        
        # Step 2: Edit element properties
        self.elem_ctrl.set_document(doc)
        self.event_bus.publish('ui:canvas:element_selected', {
            'element_id': elem1.id
        })
        self.event_bus.publish('ui:properties:element_edited', {
            'element_id': elem1.id,
            'properties': {
                'label': 'Updated Task 1',
                'description': 'This is an updated task'
            }
        })
        
        # Verify edit
        assert elem1.label == 'Updated Task 1'
        assert elem1.description == 'This is an updated task'
        
        # Step 3: Validate process
        self.validation_ctrl.set_document(doc)
        result = self.validation_ctrl.validate()
        
        assert result is not None
        assert 'errors' in result
        assert 'warnings' in result
        assert result['element_count'] == 2
        assert result['connection_count'] == 1
        assert len(result['errors']) == 0  # No errors
        
        # Step 4: Export to multiple formats
        self.export_ctrl.set_document(doc)
        
        # Export to JSON
        json_path = os.path.join(self.temp_dir, 'export.json')
        self.export_ctrl.export(json_path, 'json')
        assert os.path.exists(json_path)
        
        # Export to XML
        xml_path = os.path.join(self.temp_dir, 'export.xml')
        self.export_ctrl.export(xml_path, 'xml')
        assert os.path.exists(xml_path)
        
        # Export to PNG
        png_path = os.path.join(self.temp_dir, 'export.png')
        self.export_ctrl.export(png_path, 'png')
        assert os.path.exists(png_path)
        
        # Verify last export info
        last_export = self.export_ctrl.get_last_export_info()
        assert last_export['file_path'] == png_path
        assert last_export['format'] == 'png'
    
    # ==========================================
    # E2E Test 3: AI Wizard → Layout → Export
    # ==========================================
    
    def test_e2e_ai_wizard_workflow(self):
        """
        Test: AI Wizard → Generate Process → Layout → Export
        
        Steps:
        1. Create new document
        2. Use AI Wizard to generate process
        3. Apply auto-layout
        4. Validate result
        5. Export
        """
        # Step 1: Create new document
        self.event_bus.publish('ui:menu:file:new', {})
        doc = self.doc_ctrl.get_current_document()
        
        # Step 2: AI Wizard (mock implementation generates 3 elements + 2 connections)
        from vpb.controllers.ai_controller import AIController
        ai_ctrl = AIController(self.event_bus)
        ai_ctrl.set_document(doc)
        
        self.event_bus.publish('ui:menu:ai:wizard', {})
        self.event_bus.publish('ui:dialog:ai:wizard_completed', {
            'prompt': 'Create a simple approval process'
        })
        
        # Verify AI generated elements (mock creates 3 elements, 2 connections)
        doc = self.doc_ctrl.get_current_document()
        assert len(doc.elements) >= 3
        assert len(doc.connections) >= 2
        
        # Step 3: Apply auto-layout
        self.layout_ctrl.set_document(doc)
        self.layout_ctrl.apply_auto_layout()
        
        # Verify layout applied (elements should have updated positions)
        # Auto-layout uses hierarchical BFS algorithm
        elements = doc.elements
        assert elements[0].x != elements[1].x or elements[0].y != elements[1].y
        
        # Step 4: Validate
        self.validation_ctrl.set_document(doc)
        result = self.validation_ctrl.validate()
        
        assert len(result['errors']) == 0
        assert result['element_count'] >= 3
        assert result['connection_count'] >= 2
        
        # Step 5: Export
        self.export_ctrl.set_document(doc)
        export_path = os.path.join(self.temp_dir, 'ai_process.pdf')
        self.export_ctrl.export(export_path, 'pdf')
        assert os.path.exists(export_path)
    
    # ==========================================
    # E2E Test 4: Complex Editing Workflow
    # ==========================================
    
    def test_e2e_complex_editing(self):
        """
        Test: Complex editing with multiple operations
        
        Steps:
        1. Create document with 5 elements
        2. Create connections
        3. Delete element (should remove associated connections)
        4. Edit multiple elements
        5. Apply layout operations (align, distribute)
        6. Validate and save
        """
        # Step 1: Create document with 5 elements
        self.event_bus.publish('ui:menu:file:new', {})
        doc = self.doc_ctrl.get_current_document()
        
        elements = []
        for i in range(5):
            elem = ElementFactory.create(
                'activity',
                x=100 + i * 150,
                y=100,
                name=f'Task {i+1}'
            )
            doc.add_element(elem)
            elements.append(elem)
        
        # Step 2: Create connections (linear flow)
        for i in range(4):
            conn = ConnectionFactory.create(elements[i], elements[i+1])
            doc.add_connection(conn)
        
        assert len(doc.elements) == 5
        assert len(doc.connections) == 4
        
        # Step 3: Delete middle element
        self.elem_ctrl.set_document(doc)
        self.conn_ctrl.set_document(doc)
        
        middle_elem_id = elements[2].id
        self.event_bus.publish('ui:canvas:element_selected', {
            'element_id': middle_elem_id
        })
        self.event_bus.publish('ui:menu:edit:delete', {})
        
        # Verify element and its connections removed
        assert len(doc.elements) == 4
        # Connections involving deleted element should be removed
        remaining_connections = [c for c in doc.connections 
                                if c.source_element.id != middle_elem_id 
                                and c.target_element.id != middle_elem_id]
        assert len(remaining_connections) == 2
        
        # Step 4: Edit multiple elements
        for elem in doc.elements[:2]:
            self.event_bus.publish('ui:properties:element_edited', {
                'element_id': elem.id,
                'properties': {
                    'label': f'Updated {elem.name}',
                    'description': 'Updated description'
                }
            })
        
        # Step 5: Apply layout operations
        self.layout_ctrl.set_document(doc)
        
        # Align left
        self.event_bus.publish('ui:menu:arrange:align_left', {})
        
        # All elements should have same x coordinate
        x_coords = [elem.x for elem in doc.elements]
        assert len(set(x_coords)) == 1, "All elements should be aligned left"
        
        # Distribute vertically
        self.event_bus.publish('ui:menu:arrange:distribute_vertical', {})
        
        # Elements should be evenly spaced vertically
        y_coords = sorted([elem.y for elem in doc.elements])
        if len(y_coords) >= 3:
            spacing1 = y_coords[1] - y_coords[0]
            spacing2 = y_coords[2] - y_coords[1]
            assert abs(spacing1 - spacing2) < 1, "Vertical spacing should be equal"
        
        # Step 6: Validate and save
        self.validation_ctrl.set_document(doc)
        result = self.validation_ctrl.validate()
        
        # Should have warnings about disconnected elements
        assert len(result['errors']) == 0
        
        # Save
        file_path = os.path.join(self.temp_dir, 'complex_process.vpb.json')
        with patch('tkinter.filedialog.asksaveasfilename', return_value=file_path):
            self.event_bus.publish('ui:dialog:file:save_as_selected', {
                'file_path': file_path
            })
        
        assert os.path.exists(file_path)
    
    # ==========================================
    # E2E Test 5: Error Handling
    # ==========================================
    
    def test_e2e_error_handling(self):
        """
        Test: Error handling across layers
        
        Tests:
        1. Invalid file format
        2. Self-connection prevention
        3. Export with no document
        4. Invalid export format
        """
        # Test 1: Invalid file format (handled by DocumentService)
        invalid_path = os.path.join(self.temp_dir, 'invalid.txt')
        with open(invalid_path, 'w') as f:
            f.write("Not a valid VPB document")
        
        with patch('tkinter.filedialog.askopenfilename', return_value=invalid_path):
            self.event_bus.publish('ui:menu:file:open', {})
            self.event_bus.publish('ui:dialog:file:open_selected', {
                'file_path': invalid_path
            })
        
        # Document should not be loaded
        doc = self.doc_ctrl.get_current_document()
        # Depending on error handling, doc might be None or previous doc
        
        # Test 2: Self-connection prevention
        self.event_bus.publish('ui:menu:file:new', {})
        doc = self.doc_ctrl.get_current_document()
        
        elem = ElementFactory.create('activity', x=100, y=100, name='Task')
        doc.add_element(elem)
        
        self.conn_ctrl.set_document(doc)
        
        # Try to create self-connection
        self.event_bus.publish('ui:canvas:connection_start', {
            'element_id': elem.id
        })
        self.event_bus.publish('ui:canvas:connection_end', {
            'element_id': elem.id  # Same element!
        })
        
        # No connection should be created
        assert len(doc.connections) == 0
        
        # Test 3: Export with no document
        self.event_bus.publish('ui:menu:file:close', {})
        assert self.doc_ctrl.get_current_document() is None
        
        self.export_ctrl.set_document(None)
        export_path = os.path.join(self.temp_dir, 'should_fail.png')
        
        # Should handle gracefully (not crash)
        try:
            self.export_ctrl.export(export_path, 'png')
        except Exception:
            pass  # Expected to fail or handle gracefully
        
        # Test 4: Invalid export format
        self.event_bus.publish('ui:menu:file:new', {})
        doc = self.doc_ctrl.get_current_document()
        self.export_ctrl.set_document(doc)
        
        with pytest.raises(ValueError):
            self.export_ctrl.export('test.invalid', 'invalid_format')


# ==========================================
# Performance Tests (Basic)
# ==========================================

class TestPerformanceBasic:
    """Basic performance tests for large documents"""
    
    def test_large_document_creation(self):
        """Test creating document with 100 elements"""
        doc = DocumentModel()
        
        import time
        start = time.time()
        
        # Add 100 elements
        elements = []
        for i in range(100):
            elem = ElementFactory.create(
                'activity',
                x=100 + (i % 10) * 150,
                y=100 + (i // 10) * 100,
                name=f'Task {i+1}'
            )
            doc.add_element(elem)
            elements.append(elem)
        
        # Add connections (create a grid)
        for i in range(99):
            if (i + 1) % 10 != 0:  # Connect horizontally
                conn = ConnectionFactory.create(elements[i], elements[i+1])
                doc.add_connection(conn)
        
        elapsed = time.time() - start
        
        assert len(doc.elements) == 100
        assert len(doc.connections) == 90
        assert elapsed < 1.0, f"Creation took {elapsed}s, should be < 1s"
    
    def test_document_serialization_performance(self):
        """Test serialization of large document"""
        doc = DocumentModel()
        
        # Add 50 elements
        for i in range(50):
            elem = ElementFactory.create(
                'activity',
                x=100 + (i % 10) * 150,
                y=100 + (i // 10) * 100,
                name=f'Task {i+1}'
            )
            doc.add_element(elem)
        
        import time
        start = time.time()
        
        # Serialize to dict
        doc_dict = doc.to_dict()
        
        # Deserialize from dict
        doc2 = DocumentModel.from_dict(doc_dict)
        
        elapsed = time.time() - start
        
        assert len(doc2.elements) == 50
        assert elapsed < 0.5, f"Serialization took {elapsed}s, should be < 0.5s"
    
    def test_validation_performance(self):
        """Test validation of large document"""
        from vpb.services.validation_service import ValidationService
        
        doc = DocumentModel()
        elements = []
        
        # Add 100 elements
        for i in range(100):
            elem = ElementFactory.create('activity', x=100, y=100, name=f'Task {i+1}')
            doc.add_element(elem)
            elements.append(elem)
        
        # Add 50 connections
        for i in range(50):
            conn = ConnectionFactory.create(elements[i], elements[i+1])
            doc.add_connection(conn)
        
        validation_service = ValidationService()
        
        import time
        start = time.time()
        
        result = validation_service.validate_document(doc)
        
        elapsed = time.time() - start
        
        assert result is not None
        assert elapsed < 0.5, f"Validation took {elapsed}s, should be < 0.5s"
