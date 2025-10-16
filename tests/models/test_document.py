"""Unit tests for DocumentModel"""

import pytest
from vpb.models.document import DocumentModel, DocumentMetadata
from vpb.models.element import ElementFactory
from vpb.models.connection import ConnectionFactory


class TestDocumentMetadata:
    """Test suite for DocumentMetadata."""
    
    def test_create_metadata(self):
        """Test creating metadata with defaults."""
        meta = DocumentMetadata()
        
        assert meta.title == "Untitled Process"
        assert meta.description == ""
        assert meta.author == ""
        assert meta.version == "1.0"
        assert meta.created is not None
        assert meta.modified is not None
        assert meta.tags == []
    
    def test_create_metadata_with_values(self):
        """Test creating metadata with custom values."""
        meta = DocumentMetadata(
            title="My Process",
            description="Test process",
            author="John Doe",
            version="2.0",
            tags=["tag1", "tag2"]
        )
        
        assert meta.title == "My Process"
        assert meta.description == "Test process"
        assert meta.author == "John Doe"
        assert meta.version == "2.0"
        assert meta.tags == ["tag1", "tag2"]
    
    def test_touch_updates_modified(self):
        """Test that touch() updates modification time."""
        meta = DocumentMetadata()
        original_modified = meta.modified
        
        import time
        time.sleep(0.01)  # Small delay
        
        meta.touch()
        
        assert meta.modified != original_modified
    
    def test_to_dict(self):
        """Test metadata serialization."""
        meta = DocumentMetadata(
            title="Test",
            author="Author",
            tags=["tag1"]
        )
        
        data = meta.to_dict()
        
        assert data['title'] == "Test"
        assert data['author'] == "Author"
        assert data['tags'] == ["tag1"]
    
    def test_from_dict(self):
        """Test metadata deserialization."""
        data = {
            'title': 'Test Process',
            'description': 'Description',
            'author': 'Jane Doe',
            'version': '3.0',
            'created': '2025-01-01T12:00:00',
            'modified': '2025-01-02T12:00:00',
            'tags': ['important']
        }
        
        meta = DocumentMetadata.from_dict(data)
        
        assert meta.title == 'Test Process'
        assert meta.description == 'Description'
        assert meta.author == 'Jane Doe'
        assert meta.version == '3.0'
        assert meta.tags == ['important']


class TestDocumentModel:
    """Test suite for DocumentModel."""
    
    def test_create_empty_document(self):
        """Test creating an empty document."""
        doc = DocumentModel()
        
        assert doc.is_empty() is True
        assert doc.get_element_count() == 0
        assert doc.get_connection_count() == 0
        assert doc.is_modified() is False
    
    def test_add_element(self):
        """Test adding an element."""
        doc = DocumentModel()
        element = ElementFactory.create_prozess(100, 200)
        
        doc.add_element(element)
        
        assert doc.get_element_count() == 1
        assert doc.has_element(element.element_id) is True
        assert doc.is_modified() is True
    
    def test_add_duplicate_element_raises_error(self):
        """Test that adding duplicate element ID raises error."""
        doc = DocumentModel()
        element = ElementFactory.create('Prozess', 100, 200, element_id='test1')
        
        doc.add_element(element)
        
        with pytest.raises(ValueError, match="already exists"):
            doc.add_element(element)
    
    def test_remove_element(self):
        """Test removing an element."""
        doc = DocumentModel()
        element = ElementFactory.create_prozess(100, 200)
        
        doc.add_element(element)
        removed = doc.remove_element(element.element_id)
        
        assert removed is not None
        assert removed.element_id == element.element_id
        assert doc.get_element_count() == 0
        assert doc.has_element(element.element_id) is False
    
    def test_remove_nonexistent_element(self):
        """Test removing non-existent element returns None."""
        doc = DocumentModel()
        
        removed = doc.remove_element('nonexistent')
        
        assert removed is None
    
    def test_remove_element_removes_connections(self):
        """Test that removing element also removes its connections."""
        doc = DocumentModel()
        
        elem1 = ElementFactory.create('Prozess', 100, 100, element_id='e1')
        elem2 = ElementFactory.create('Prozess', 200, 200, element_id='e2')
        doc.add_element(elem1)
        doc.add_element(elem2)
        
        conn = ConnectionFactory.create('e1', 'e2', connection_id='c1')
        doc.add_connection(conn)
        
        assert doc.get_connection_count() == 1
        
        doc.remove_element('e1')
        
        assert doc.get_connection_count() == 0
    
    def test_get_element(self):
        """Test retrieving an element."""
        doc = DocumentModel()
        element = ElementFactory.create('Prozess', 100, 200, element_id='test1')
        
        doc.add_element(element)
        retrieved = doc.get_element('test1')
        
        assert retrieved is not None
        assert retrieved.element_id == 'test1'
    
    def test_get_all_elements(self):
        """Test getting all elements."""
        doc = DocumentModel()
        
        elem1 = ElementFactory.create_prozess(100, 100)
        elem2 = ElementFactory.create_prozess(200, 200)
        doc.add_element(elem1)
        doc.add_element(elem2)
        
        elements = doc.get_all_elements()
        
        assert len(elements) == 2
        assert elem1 in elements
        assert elem2 in elements
    
    def test_update_element(self):
        """Test updating an element."""
        doc = DocumentModel()
        element = ElementFactory.create('Prozess', 100, 200, element_id='test1', name='Original')
        
        doc.add_element(element)
        
        # Modify element
        updated = element.move_to(300, 400)
        doc.update_element(updated)
        
        retrieved = doc.get_element('test1')
        assert retrieved.x == 300
        assert retrieved.y == 400
    
    def test_update_nonexistent_element_raises_error(self):
        """Test updating non-existent element raises error."""
        doc = DocumentModel()
        element = ElementFactory.create('Prozess', 100, 200, element_id='test1')
        
        with pytest.raises(ValueError, match="not found"):
            doc.update_element(element)
    
    def test_add_connection(self):
        """Test adding a connection."""
        doc = DocumentModel()
        
        elem1 = ElementFactory.create('Prozess', 100, 100, element_id='e1')
        elem2 = ElementFactory.create('Prozess', 200, 200, element_id='e2')
        doc.add_element(elem1)
        doc.add_element(elem2)
        
        conn = ConnectionFactory.create('e1', 'e2')
        doc.add_connection(conn)
        
        assert doc.get_connection_count() == 1
        assert doc.has_connection(conn.connection_id) is True
    
    def test_add_connection_invalid_source_raises_error(self):
        """Test that connection with invalid source raises error."""
        doc = DocumentModel()
        
        elem = ElementFactory.create('Prozess', 100, 100, element_id='e1')
        doc.add_element(elem)
        
        conn = ConnectionFactory.create('nonexistent', 'e1')
        
        with pytest.raises(ValueError, match="Source element .* not found"):
            doc.add_connection(conn)
    
    def test_add_connection_invalid_target_raises_error(self):
        """Test that connection with invalid target raises error."""
        doc = DocumentModel()
        
        elem = ElementFactory.create('Prozess', 100, 100, element_id='e1')
        doc.add_element(elem)
        
        conn = ConnectionFactory.create('e1', 'nonexistent')
        
        with pytest.raises(ValueError, match="Target element .* not found"):
            doc.add_connection(conn)
    
    def test_remove_connection(self):
        """Test removing a connection."""
        doc = DocumentModel()
        
        elem1 = ElementFactory.create('Prozess', 100, 100, element_id='e1')
        elem2 = ElementFactory.create('Prozess', 200, 200, element_id='e2')
        doc.add_element(elem1)
        doc.add_element(elem2)
        
        conn = ConnectionFactory.create('e1', 'e2', connection_id='c1')
        doc.add_connection(conn)
        
        removed = doc.remove_connection('c1')
        
        assert removed is not None
        assert removed.connection_id == 'c1'
        assert doc.get_connection_count() == 0
    
    def test_get_connections_for_element(self):
        """Test getting all connections for an element."""
        doc = DocumentModel()
        
        elem1 = ElementFactory.create('Prozess', 100, 100, element_id='e1')
        elem2 = ElementFactory.create('Prozess', 200, 200, element_id='e2')
        elem3 = ElementFactory.create('Prozess', 300, 300, element_id='e3')
        doc.add_element(elem1)
        doc.add_element(elem2)
        doc.add_element(elem3)
        
        conn1 = ConnectionFactory.create('e1', 'e2', connection_id='c1')
        conn2 = ConnectionFactory.create('e2', 'e3', connection_id='c2')
        doc.add_connection(conn1)
        doc.add_connection(conn2)
        
        # e2 has 2 connections (1 in, 1 out)
        connections = doc.get_connections_for_element('e2')
        assert len(connections) == 2
        
        # e1 has 1 connection (outgoing)
        connections = doc.get_connections_for_element('e1')
        assert len(connections) == 1
    
    def test_get_outgoing_connections(self):
        """Test getting outgoing connections."""
        doc = DocumentModel()
        
        elem1 = ElementFactory.create('Prozess', 100, 100, element_id='e1')
        elem2 = ElementFactory.create('Prozess', 200, 200, element_id='e2')
        elem3 = ElementFactory.create('Prozess', 300, 300, element_id='e3')
        doc.add_element(elem1)
        doc.add_element(elem2)
        doc.add_element(elem3)
        
        conn1 = ConnectionFactory.create('e1', 'e2', connection_id='c1')
        conn2 = ConnectionFactory.create('e1', 'e3', connection_id='c2')
        doc.add_connection(conn1)
        doc.add_connection(conn2)
        
        outgoing = doc.get_outgoing_connections('e1')
        assert len(outgoing) == 2
    
    def test_get_incoming_connections(self):
        """Test getting incoming connections."""
        doc = DocumentModel()
        
        elem1 = ElementFactory.create('Prozess', 100, 100, element_id='e1')
        elem2 = ElementFactory.create('Prozess', 200, 200, element_id='e2')
        elem3 = ElementFactory.create('Prozess', 300, 300, element_id='e3')
        doc.add_element(elem1)
        doc.add_element(elem2)
        doc.add_element(elem3)
        
        conn1 = ConnectionFactory.create('e1', 'e3', connection_id='c1')
        conn2 = ConnectionFactory.create('e2', 'e3', connection_id='c2')
        doc.add_connection(conn1)
        doc.add_connection(conn2)
        
        incoming = doc.get_incoming_connections('e3')
        assert len(incoming) == 2
    
    def test_clear(self):
        """Test clearing document."""
        doc = DocumentModel()
        
        elem = ElementFactory.create_prozess(100, 200)
        doc.add_element(elem)
        doc.metadata.title = "Test"
        
        doc.clear()
        
        assert doc.is_empty() is True
        assert doc.metadata.title == "Untitled Process"
        assert doc.is_modified() is False
    
    def test_is_empty(self):
        """Test is_empty check."""
        doc = DocumentModel()
        
        assert doc.is_empty() is True
        
        elem = ElementFactory.create_prozess(100, 200)
        doc.add_element(elem)
        
        assert doc.is_empty() is False
    
    def test_modified_flag(self):
        """Test modified flag."""
        doc = DocumentModel()
        
        assert doc.is_modified() is False
        
        elem = ElementFactory.create_prozess(100, 200)
        doc.add_element(elem)
        
        assert doc.is_modified() is True
        
        doc.set_modified(False)
        assert doc.is_modified() is False
    
    def test_validate_valid_document(self):
        """Test validation of valid document."""
        doc = DocumentModel()
        
        elem1 = ElementFactory.create('Prozess', 100, 100, element_id='e1')
        elem2 = ElementFactory.create('Prozess', 200, 200, element_id='e2')
        doc.add_element(elem1)
        doc.add_element(elem2)
        
        conn = ConnectionFactory.create('e1', 'e2')
        doc.add_connection(conn)
        
        errors = doc.validate()
        assert len(errors) == 0
        assert doc.is_valid() is True
    
    def test_to_dict(self):
        """Test document serialization."""
        doc = DocumentModel()
        doc.metadata.title = "Test Process"
        
        elem = ElementFactory.create('Prozess', 100, 200, element_id='e1', name='Process 1')
        doc.add_element(elem)
        
        data = doc.to_dict()
        
        assert 'metadata' in data
        assert 'elements' in data
        assert 'connections' in data
        assert 'version' in data
        assert data['metadata']['title'] == "Test Process"
        assert len(data['elements']) == 1
        assert data['elements'][0]['element_id'] == 'e1'
    
    def test_from_dict(self):
        """Test document deserialization."""
        data = {
            'metadata': {
                'title': 'Loaded Process',
                'author': 'Author',
            },
            'elements': [
                {
                    'element_id': 'e1',
                    'element_type': 'Prozess',
                    'name': 'Process 1',
                    'x': 100,
                    'y': 200,
                }
            ],
            'connections': [],
            'version': '2.0'
        }
        
        doc = DocumentModel.from_dict(data)
        
        assert doc.metadata.title == 'Loaded Process'
        assert doc.get_element_count() == 1
        assert doc.has_element('e1') is True
        assert doc.is_modified() is False
    
    def test_round_trip_serialization(self):
        """Test that to_dict/from_dict preserves all data."""
        original = DocumentModel()
        original.metadata.title = "Round Trip Test"
        original.metadata.author = "Tester"
        
        elem1 = ElementFactory.create('Prozess', 100, 100, element_id='e1')
        elem2 = ElementFactory.create('Prozess', 200, 200, element_id='e2')
        original.add_element(elem1)
        original.add_element(elem2)
        
        conn = ConnectionFactory.create('e1', 'e2', connection_id='c1')
        original.add_connection(conn)
        
        data = original.to_dict()
        restored = DocumentModel.from_dict(data)
        
        assert restored.metadata.title == original.metadata.title
        assert restored.metadata.author == original.metadata.author
        assert restored.get_element_count() == original.get_element_count()
        assert restored.get_connection_count() == original.get_connection_count()
        assert restored.has_element('e1') is True
        assert restored.has_element('e2') is True
        assert restored.has_connection('c1') is True
    
    def test_observer_pattern(self):
        """Test observer notifications."""
        doc = DocumentModel()
        events = []
        
        def observer(event, data):
            events.append((event, data))
        
        doc.attach_observer(observer)
        
        # Add element
        elem = ElementFactory.create_prozess(100, 200)
        doc.add_element(elem)
        
        assert len(events) == 1
        assert events[0][0] == 'element.added'
        
        # Remove element
        doc.remove_element(elem.element_id)
        
        assert len(events) == 2
        assert events[1][0] == 'element.removed'
    
    def test_detach_observer(self):
        """Test detaching an observer."""
        doc = DocumentModel()
        events = []
        
        def observer(event, data):
            events.append(event)
        
        doc.attach_observer(observer)
        
        elem = ElementFactory.create_prozess(100, 200)
        doc.add_element(elem)
        
        assert len(events) == 1
        
        # Detach
        result = doc.detach_observer(observer)
        assert result is True
        
        # Add another element (should not trigger)
        elem2 = ElementFactory.create_prozess(300, 400)
        doc.add_element(elem2)
        
        assert len(events) == 1  # Still 1
    
    def test_repr(self):
        """Test string representation."""
        doc = DocumentModel()
        doc.metadata.title = "Test"
        
        elem = ElementFactory.create_prozess(100, 200)
        doc.add_element(elem)
        
        repr_str = repr(doc)
        
        assert "DocumentModel" in repr_str
        assert "Test" in repr_str
        assert "elements=1" in repr_str


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
