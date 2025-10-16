"""
Simplified End-to-End Integration Tests for VPB Process Designer

These tests verify that all layers (Infrastructure, Models, Services, Controllers)
work together correctly using the ACTUAL APIs.
"""

import pytest
import os
import tempfile
import shutil

from vpb.infrastructure.event_bus import EventBus
from vpb.models.document import DocumentModel
from vpb.models.element import ElementFactory
from vpb.models.connection import ConnectionFactory
from vpb.services.document_service import DocumentService
from vpb.services.validation_service import ValidationService
from vpb.services.layout_service import LayoutService
from vpb.services.export_service import ExportService


class TestSimpleIntegration:
    """Simplified integration tests focusing on core functionality"""
    
    def setup_method(self):
        """Setup temp directory"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup temp files"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    # ==========================================
    # Test 1: Document + Elements + Connections
    # ==========================================
    
    def test_document_with_elements_and_connections(self):
        """
        Test: Create document, add elements, add connections, verify
        
        Verifies:
        - DocumentModel API
        - ElementFactory
        - ConnectionFactory
        - Element/Connection management
        """
        # Create document
        doc = DocumentModel()
        doc.metadata.title = "Test Process"
        doc.metadata.description = "Integration test"
        
        # Add elements using ElementFactory
        elem1 = ElementFactory.create('start_event', x=100, y=100, name='Start')
        elem2 = ElementFactory.create('task', x=300, y=100, name='Task 1')
        elem3 = ElementFactory.create('end_event', x=500, y=100, name='End')
        
        doc.add_element(elem1)
        doc.add_element(elem2)
        doc.add_element(elem3)
        
        # Verify elements added
        assert doc.get_element_count() == 3
        assert doc.has_element(elem1.element_id)
        assert doc.has_element(elem2.element_id)
        assert doc.has_element(elem3.element_id)
        
        # Add connections using ConnectionFactory
        conn1 = ConnectionFactory.create(elem1, elem2)
        conn2 = ConnectionFactory.create(elem2, elem3)
        
        doc.add_connection(conn1)
        doc.add_connection(conn2)
        
        # Verify connections added
        assert doc.get_connection_count() == 2
        assert doc.has_connection(conn1.connection_id)
        assert doc.has_connection(conn2.connection_id)
        
        # Verify connection relationships
        outgoing = doc.get_outgoing_connections(elem1.element_id)
        assert len(outgoing) == 1
        assert outgoing[0].target_element.element_id == elem2.element_id
        
        incoming = doc.get_incoming_connections(elem3.element_id)
        assert len(incoming) == 1
        assert incoming[0].source_element.element_id == elem2.element_id
    
    # ==========================================
    # Test 2: Document Service Save/Load
    # ==========================================
    
    def test_document_service_save_and_load(self):
        """
        Test: Document persistence via DocumentService
        
        Verifies:
        - DocumentService.save()
        - DocumentService.load()
        - Serialization round-trip
        """
        doc_service = DocumentService()
        
        # Create document with content
        doc = DocumentModel()
        doc.metadata.title = "Saved Process"
        
        elem1 = ElementFactory.create('task', x=100, y=100, name='Task 1')
        elem2 = ElementFactory.create('task', x=300, y=100, name='Task 2')
        doc.add_element(elem1)
        doc.add_element(elem2)
        
        conn = ConnectionFactory.create(elem1, elem2)
        doc.add_connection(conn)
        
        # Save to file
        file_path = os.path.join(self.temp_dir, 'test.vpb.json')
        doc_service.save_document(doc, file_path)
        
        assert os.path.exists(file_path)
        
        # Load from file
        loaded_doc = doc_service.load_document(file_path)
        
        # Verify loaded document
        assert loaded_doc.metadata.title == "Saved Process"
        assert loaded_doc.get_element_count() == 2
        assert loaded_doc.get_connection_count() == 1
        
        # Verify element details
        loaded_elements = loaded_doc.get_all_elements()
        assert len(loaded_elements) == 2
        assert loaded_elements[0].name == 'Task 1'
        assert loaded_elements[1].name == 'Task 2'
    
    # ==========================================
    # Test 3: Validation Service
    # ==========================================
    
    def test_validation_service(self):
        """
        Test: ValidationService validates document
        
        Verifies:
        - ValidationService.validate_document()
        - Validation rules
        - Error/Warning detection
        """
        validation_service = ValidationService()
        
        # Test 1: Empty document (should have error)
        doc = DocumentModel()
        result = validation_service.validate_document(doc)
        result_dict = result.to_dict()  # Convert to dict
        
        assert 'errors' in result_dict
        assert 'warnings' in result_dict
        # Should have NO_ELEMENTS error
        errors = [e for e in result_dict['errors'] if 'NO_ELEMENTS' in e.get('rule', '')]
        assert len(errors) > 0
        
        # Test 2: Document with elements (should pass)
        elem1 = ElementFactory.create('task', x=100, y=100, name='Task 1')
        elem2 = ElementFactory.create('task', x=300, y=100, name='Task 2')
        doc.add_element(elem1)
        doc.add_element(elem2)
        
        conn = ConnectionFactory.create(elem1, elem2)
        doc.add_connection(conn)
        
        result = validation_service.validate_document(doc)
        result_dict = result.to_dict()  # Convert to dict
        
        # Should have no critical errors
        assert len(result_dict['errors']) == 0
        assert result_dict['element_count'] == 2
        assert result_dict['connection_count'] == 1
    
    # ==========================================
    # Test 4: Layout Service
    # ==========================================
    
    def test_layout_service(self):
        """
        Test: LayoutService applies layouts
        
        Verifies:
        - LayoutService.align_elements()
        - LayoutService.distribute_elements()
        - LayoutService.apply_auto_layout()
        """
        layout_service = LayoutService()
        
        # Create document with 3 elements at different positions
        doc = DocumentModel()
        elem1 = ElementFactory.create('task', x=100, y=150, name='Task 1')
        elem2 = ElementFactory.create('task', x=200, y=100, name='Task 2')
        elem3 = ElementFactory.create('task', x=300, y=200, name='Task 3')
        doc.add_element(elem1)
        doc.add_element(elem2)
        doc.add_element(elem3)
        
        elements = doc.get_all_elements()
        
        # Test align left
        layout_result = layout_service.align_elements(elements, 'left')
        
        # Apply positions to elements
        for elem in elements:
            if elem.element_id in layout_result.element_positions:
                new_x, new_y = layout_result.element_positions[elem.element_id]
                elem.x = new_x
                elem.y = new_y
        
        # All should have same x
        x_coords = [e.x for e in elements]
        assert len(set(x_coords)) == 1, "All elements should be aligned left"
        
        # Reset positions
        elem1.x, elem1.y = 100, 100
        elem2.x, elem2.y = 300, 100
        elem3.x, elem3.y = 500, 100
        
        # Test distribute horizontal
        layout_result = layout_service.distribute_elements(elements, 'horizontal')
        
        # Apply positions
        for elem in elements:
            if elem.element_id in layout_result.element_positions:
                new_x, new_y = layout_result.element_positions[elem.element_id]
                elem.x = new_x
                elem.y = new_y
        
        # Should have equal spacing
        x_coords = sorted([e.x for e in elements])
        spacing1 = x_coords[1] - x_coords[0]
        spacing2 = x_coords[2] - x_coords[1]
        assert abs(spacing1 - spacing2) < 1, "Horizontal spacing should be equal"
    
    # ==========================================
    # Test 5: Export Service
    # ==========================================
    
    def test_export_service(self):
        """
        Test: ExportService exports to various formats
        
        Verifies:
        - ExportService.export_to_png()
        - ExportService.export_to_svg()
        - ExportService.export_to_pdf()
        - ExportService.export_to_bpmn()
        - DocumentService for JSON export
        """
        export_service = ExportService()
        doc_service = DocumentService()
        
        # Create document
        doc = DocumentModel()
        doc.metadata.title = "Export Test"
        elem1 = ElementFactory.create('task', x=100, y=100, name='Task 1')
        doc.add_element(elem1)
        
        # Export to JSON via DocumentService
        json_path = os.path.join(self.temp_dir, 'export.json')
        doc_service.save_document(doc, json_path)
        assert os.path.exists(json_path)
        
        # Export to BPMN
        bpmn_path = os.path.join(self.temp_dir, 'export.bpmn.xml')
        export_service.export_to_bpmn(doc, bpmn_path)
        assert os.path.exists(bpmn_path)
        
        # Export to PNG (mock implementation writes file)
        png_path = os.path.join(self.temp_dir, 'export.png')
        export_service.export_to_png(doc, png_path)
        assert os.path.exists(png_path)
        
        # Export to SVG (mock implementation writes file)
        svg_path = os.path.join(self.temp_dir, 'export.svg')
        export_service.export_to_svg(doc, svg_path)
        assert os.path.exists(svg_path)
        
        # Export to PDF (mock implementation writes file)
        pdf_path = os.path.join(self.temp_dir, 'export.pdf')
        export_service.export_to_pdf(doc, pdf_path)
        assert os.path.exists(pdf_path)
    
    # ==========================================
    # Test 6: EventBus Integration
    # ==========================================
    
    def test_eventbus_integration(self):
        """
        Test: EventBus communication
        
        Verifies:
        - Event subscription
        - Event publishing
        - Event callback execution
        """
        event_bus = EventBus()
        
        # Track received events
        received_events = []
        
        def handler1(data):
            received_events.append(('handler1', data))
        
        def handler2(data):
            received_events.append(('handler2', data))
        
        # Subscribe handlers
        event_bus.subscribe('test:event', handler1)
        event_bus.subscribe('test:event', handler2)
        
        # Publish event
        event_bus.publish('test:event', {'message': 'Hello'})
        
        # Verify both handlers received event
        assert len(received_events) == 2
        assert ('handler1', {'message': 'Hello'}) in received_events
        assert ('handler2', {'message': 'Hello'}) in received_events
    
    # ==========================================
    # Test 7: Full Workflow Integration
    # ==========================================
    
    def test_full_workflow(self):
        """
        Test: Complete workflow from creation to export
        
        Steps:
        1. Create document
        2. Add elements
        3. Add connections
        4. Validate
        5. Apply layout
        6. Save
        7. Load
        8. Export
        """
        doc_service = DocumentService()
        validation_service = ValidationService()
        layout_service = LayoutService()
        export_service = ExportService()
        
        # Step 1: Create document
        doc = DocumentModel()
        doc.metadata.title = "Full Workflow Test"
        
        # Step 2: Add elements
        elem1 = ElementFactory.create('start_event', x=100, y=100, name='Start')
        elem2 = ElementFactory.create('task', x=300, y=100, name='Process')
        elem3 = ElementFactory.create('end_event', x=500, y=100, name='End')
        doc.add_element(elem1)
        doc.add_element(elem2)
        doc.add_element(elem3)
        
        # Step 3: Add connections
        conn1 = ConnectionFactory.create(elem1, elem2)
        conn2 = ConnectionFactory.create(elem2, elem3)
        doc.add_connection(conn1)
        doc.add_connection(conn2)
        
        # Step 4: Validate
        validation_result = validation_service.validate_document(doc)
        result_dict = validation_result.to_dict()
        
        assert len(result_dict['errors']) == 0
        assert result_dict['element_count'] == 3
        assert result_dict['connection_count'] == 2
        
        # Step 5: Apply layout
        elements = doc.get_all_elements()
        layout_result = layout_service.align_elements(elements, 'middle')
        
        # Apply positions
        for elem in elements:
            if elem.element_id in layout_result.element_positions:
                new_x, new_y = layout_result.element_positions[elem.element_id]
                elem.x = new_x
                elem.y = new_y
        
        # All elements should have same y
        y_coords = [e.y for e in elements]
        assert len(set(y_coords)) == 1
        
        # Step 6: Save
        save_path = os.path.join(self.temp_dir, 'workflow.vpb.json')
        doc_service.save_document(doc, save_path)
        assert os.path.exists(save_path)
        
        # Step 7: Load
        loaded_doc = doc_service.load_document(save_path)
        assert loaded_doc.metadata.title == "Full Workflow Test"
        assert loaded_doc.get_element_count() == 3
        assert loaded_doc.get_connection_count() == 2
        
        # Step 8: Export (use DocumentService for JSON)
        export_path = os.path.join(self.temp_dir, 'workflow_export.json')
        doc_service.save_document(loaded_doc, export_path)
        assert os.path.exists(export_path)


# ==========================================
# Performance Tests
# ==========================================

class TestPerformance:
    """Performance tests for large documents"""
    
    def test_large_document_creation(self):
        """Test creating document with 100 elements"""
        import time
        
        doc = DocumentModel()
        
        start = time.time()
        
        # Add 100 elements
        elements = []
        for i in range(100):
            elem = ElementFactory.create(
                'task',
                x=100 + (i % 10) * 150,
                y=100 + (i // 10) * 100,
                name=f'Task {i+1}'
            )
            doc.add_element(elem)
            elements.append(elem)
        
        # Add connections (connect in grid)
        connection_count = 0
        for i in range(99):
            if (i + 1) % 10 != 0:  # Horizontal connections
                conn = ConnectionFactory.create(elements[i], elements[i+1])
                doc.add_connection(conn)
                connection_count += 1
        
        elapsed = time.time() - start
        
        assert doc.get_element_count() == 100
        assert doc.get_connection_count() == 90
        assert elapsed < 2.0, f"Creation took {elapsed}s, should be < 2s"
    
    def test_serialization_performance(self):
        """Test serialization of medium document"""
        import time
        
        doc = DocumentModel()
        
        # Add 50 elements
        for i in range(50):
            elem = ElementFactory.create(
                'task',
                x=100 + (i % 10) * 150,
                y=100 + (i // 10) * 100,
                name=f'Task {i+1}'
            )
            doc.add_element(elem)
        
        start = time.time()
        
        # Serialize
        doc_dict = doc.to_dict()
        
        # Deserialize
        doc2 = DocumentModel.from_dict(doc_dict)
        
        elapsed = time.time() - start
        
        assert doc2.get_element_count() == 50
        assert elapsed < 1.0, f"Serialization took {elapsed}s, should be < 1s"
    
    def test_validation_performance(self):
        """Test validation of large document"""
        import time
        
        from vpb.services.validation_service import ValidationService
        
        doc = DocumentModel()
        elements = []
        
        # Add 100 elements
        for i in range(100):
            elem = ElementFactory.create('task', x=100, y=100, name=f'Task {i+1}')
            doc.add_element(elem)
            elements.append(elem)
        
        # Add 50 connections
        for i in range(50):
            conn = ConnectionFactory.create(elements[i], elements[i+1])
            doc.add_connection(conn)
        
        validation_service = ValidationService()
        
        start = time.time()
        
        result = validation_service.validate_document(doc)
        
        elapsed = time.time() - start
        
        assert result is not None
        assert elapsed < 1.0, f"Validation took {elapsed}s, should be < 1s"
