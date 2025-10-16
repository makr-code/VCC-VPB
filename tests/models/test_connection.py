"""Unit tests for VPBConnection model"""

import pytest
from vpb.models.connection import (
    VPBConnection,
    ConnectionFactory,
    CONNECTION_TYPES,
    ARROW_STYLES,
    ROUTING_MODES,
)


class TestVPBConnection:
    """Test suite for VPBConnection class."""
    
    def test_create_connection(self):
        """Test creating a basic connection."""
        conn = VPBConnection(
            connection_id="conn1",
            source_element="elem1",
            target_element="elem2"
        )
        
        assert conn.connection_id == "conn1"
        assert conn.source_element == "elem1"
        assert conn.target_element == "elem2"
        assert conn.connection_type == "SEQUENCE"  # default
    
    def test_connection_defaults(self):
        """Test that optional fields have proper defaults."""
        conn = VPBConnection(
            connection_id="conn1",
            source_element="elem1",
            target_element="elem2"
        )
        
        assert conn.description == ""
        assert conn.arrow_style == "single"
        assert conn.routing_mode == "auto"
        assert conn.canvas_item is None
        assert conn.waypoints == []
    
    def test_validation_empty_id(self):
        """Test that empty connection_id raises error."""
        with pytest.raises(ValueError, match="connection_id cannot be empty"):
            VPBConnection(
                connection_id="",
                source_element="elem1",
                target_element="elem2"
            )
    
    def test_validation_empty_source(self):
        """Test that empty source_element raises error."""
        with pytest.raises(ValueError, match="source_element cannot be empty"):
            VPBConnection(
                connection_id="conn1",
                source_element="",
                target_element="elem2"
            )
    
    def test_validation_empty_target(self):
        """Test that empty target_element raises error."""
        with pytest.raises(ValueError, match="target_element cannot be empty"):
            VPBConnection(
                connection_id="conn1",
                source_element="elem1",
                target_element=""
            )
    
    def test_validation_self_connection(self):
        """Test that self-connection raises error."""
        with pytest.raises(ValueError, match="Cannot connect element to itself"):
            VPBConnection(
                connection_id="conn1",
                source_element="elem1",
                target_element="elem1"
            )
    
    def test_is_sequence(self):
        """Test is_sequence() method."""
        conn = VPBConnection(
            connection_id="conn1",
            source_element="elem1",
            target_element="elem2",
            connection_type="SEQUENCE"
        )
        
        assert conn.is_sequence() is True
    
    def test_is_dependency(self):
        """Test is_dependency() method."""
        conn = VPBConnection(
            connection_id="conn1",
            source_element="elem1",
            target_element="elem2",
            connection_type="DEPENDENCY"
        )
        
        assert conn.is_dependency() is True
    
    def test_is_information_flow(self):
        """Test is_information_flow() method."""
        conn = VPBConnection(
            connection_id="conn1",
            source_element="elem1",
            target_element="elem2",
            connection_type="INFORMATION"
        )
        
        assert conn.is_information_flow() is True
    
    def test_has_waypoints(self):
        """Test has_waypoints() method."""
        conn = VPBConnection(
            connection_id="conn1",
            source_element="elem1",
            target_element="elem2"
        )
        
        assert conn.has_waypoints() is False
        
        conn.add_waypoint(100, 100)
        assert conn.has_waypoints() is True
    
    def test_add_waypoint(self):
        """Test adding waypoints."""
        conn = VPBConnection(
            connection_id="conn1",
            source_element="elem1",
            target_element="elem2"
        )
        
        conn.add_waypoint(100, 100)
        conn.add_waypoint(200, 150)
        
        assert len(conn.waypoints) == 2
        assert conn.waypoints[0] == (100, 100)
        assert conn.waypoints[1] == (200, 150)
    
    def test_clear_waypoints(self):
        """Test clearing waypoints."""
        conn = VPBConnection(
            connection_id="conn1",
            source_element="elem1",
            target_element="elem2",
            waypoints=[(100, 100), (200, 200)]
        )
        
        assert len(conn.waypoints) == 2
        
        conn.clear_waypoints()
        assert len(conn.waypoints) == 0
    
    def test_reverse(self):
        """Test reverse() creates reversed connection."""
        conn = VPBConnection(
            connection_id="conn1",
            source_element="elem1",
            target_element="elem2",
            description="Test",
            waypoints=[(100, 100), (200, 200)]
        )
        
        reversed_conn = conn.reverse()
        
        # ID changed
        assert reversed_conn.connection_id == "conn1_reversed"
        
        # Source and target swapped
        assert reversed_conn.source_element == "elem2"
        assert reversed_conn.target_element == "elem1"
        
        # Properties preserved
        assert reversed_conn.description == "Test"
        
        # Waypoints reversed
        assert reversed_conn.waypoints == [(200, 200), (100, 100)]
        
        # Original unchanged
        assert conn.source_element == "elem1"
        assert conn.target_element == "elem2"
    
    def test_clone(self):
        """Test clone() creates deep copy."""
        conn = VPBConnection(
            connection_id="original",
            source_element="elem1",
            target_element="elem2",
            description="Test",
            waypoints=[(100, 100)]
        )
        
        cloned = conn.clone()
        
        # Different ID
        assert cloned.connection_id == "original_copy"
        
        # Properties preserved
        assert cloned.source_element == "elem1"
        assert cloned.target_element == "elem2"
        assert cloned.description == "Test"
        assert cloned.waypoints == [(100, 100)]
        
        # Deep copy of waypoints
        cloned.waypoints.append((200, 200))
        assert len(conn.waypoints) == 1
    
    def test_clone_with_new_id(self):
        """Test clone() with custom ID."""
        conn = VPBConnection(
            connection_id="original",
            source_element="elem1",
            target_element="elem2"
        )
        
        cloned = conn.clone(new_id="custom_id")
        
        assert cloned.connection_id == "custom_id"
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        conn = VPBConnection(
            connection_id="conn1",
            source_element="elem1",
            target_element="elem2",
            connection_type="DEPENDENCY",
            description="Test connection",
            arrow_style="double",
            routing_mode="straight",
            waypoints=[(100, 100), (200, 200)]
        )
        
        data = conn.to_dict()
        
        assert isinstance(data, dict)
        assert data['connection_id'] == "conn1"
        assert data['source_element'] == "elem1"
        assert data['target_element'] == "elem2"
        assert data['connection_type'] == "DEPENDENCY"
        assert data['description'] == "Test connection"
        assert data['arrow_style'] == "double"
        assert data['routing_mode'] == "straight"
        assert data['waypoints'] == [(100, 100), (200, 200)]
    
    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            'connection_id': 'conn1',
            'source_element': 'elem1',
            'target_element': 'elem2',
            'connection_type': 'DEPENDENCY',
            'description': 'Test connection',
            'arrow_style': 'double',
            'routing_mode': 'straight',
            'waypoints': [(100, 100), (200, 200)]
        }
        
        conn = VPBConnection.from_dict(data)
        
        assert conn.connection_id == "conn1"
        assert conn.source_element == "elem1"
        assert conn.target_element == "elem2"
        assert conn.connection_type == "DEPENDENCY"
        assert conn.description == "Test connection"
        assert conn.arrow_style == "double"
        assert conn.routing_mode == "straight"
        assert conn.waypoints == [(100, 100), (200, 200)]
    
    def test_round_trip_serialization(self):
        """Test that to_dict/from_dict preserves all data."""
        original = VPBConnection(
            connection_id="conn1",
            source_element="elem1",
            target_element="elem2",
            connection_type="INFORMATION",
            description="Info flow",
            arrow_style="single",
            routing_mode="curved",
            waypoints=[(100, 100), (150, 150), (200, 200)]
        )
        
        data = original.to_dict()
        restored = VPBConnection.from_dict(data)
        
        assert restored.connection_id == original.connection_id
        assert restored.source_element == original.source_element
        assert restored.target_element == original.target_element
        assert restored.connection_type == original.connection_type
        assert restored.description == original.description
        assert restored.arrow_style == original.arrow_style
        assert restored.routing_mode == original.routing_mode
        assert restored.waypoints == original.waypoints
    
    def test_repr(self):
        """Test string representation."""
        conn = VPBConnection(
            connection_id="conn1",
            source_element="elem1",
            target_element="elem2",
            connection_type="SEQUENCE"
        )
        
        repr_str = repr(conn)
        
        assert "VPBConnection" in repr_str
        assert "conn1" in repr_str
        assert "elem1" in repr_str
        assert "elem2" in repr_str
        assert "SEQUENCE" in repr_str


class TestConnectionFactory:
    """Test suite for ConnectionFactory."""
    
    def test_create_basic(self):
        """Test basic connection creation."""
        conn = ConnectionFactory.create("elem1", "elem2")
        
        assert conn.source_element == "elem1"
        assert conn.target_element == "elem2"
        assert conn.connection_type == "SEQUENCE"
        assert conn.connection_id.startswith("conn_")
    
    def test_create_with_custom_id(self):
        """Test creation with custom ID."""
        conn = ConnectionFactory.create(
            "elem1",
            "elem2",
            connection_id="custom_id"
        )
        
        assert conn.connection_id == "custom_id"
    
    def test_create_with_type(self):
        """Test creation with specific type."""
        conn = ConnectionFactory.create(
            "elem1",
            "elem2",
            connection_type="DEPENDENCY"
        )
        
        assert conn.connection_type == "DEPENDENCY"
    
    def test_create_with_kwargs(self):
        """Test creation with additional properties."""
        conn = ConnectionFactory.create(
            "elem1",
            "elem2",
            description="Test",
            arrow_style="double"
        )
        
        assert conn.description == "Test"
        assert conn.arrow_style == "double"
    
    def test_create_sequence(self):
        """Test convenience method for sequence connection."""
        conn = ConnectionFactory.create_sequence(
            "elem1",
            "elem2",
            "Sequential flow"
        )
        
        assert conn.connection_type == "SEQUENCE"
        assert conn.description == "Sequential flow"
    
    def test_create_dependency(self):
        """Test convenience method for dependency connection."""
        conn = ConnectionFactory.create_dependency(
            "elem1",
            "elem2",
            "Depends on"
        )
        
        assert conn.connection_type == "DEPENDENCY"
        assert conn.description == "Depends on"
        assert conn.arrow_style == "double"
    
    def test_create_information_flow(self):
        """Test convenience method for information flow."""
        conn = ConnectionFactory.create_information_flow(
            "elem1",
            "elem2",
            "Info"
        )
        
        assert conn.connection_type == "INFORMATION"
        assert conn.description == "Info"
    
    def test_create_data_flow(self):
        """Test convenience method for data flow."""
        conn = ConnectionFactory.create_data_flow(
            "elem1",
            "elem2",
            "Data"
        )
        
        assert conn.connection_type == "DATA"
        assert conn.description == "Data"


class TestConnectionConstants:
    """Test connection constants."""
    
    def test_connection_types_defined(self):
        """Test that connection types are defined."""
        assert 'SEQUENCE' in CONNECTION_TYPES
        assert 'DEPENDENCY' in CONNECTION_TYPES
        assert 'INFORMATION' in CONNECTION_TYPES
        assert 'DATA' in CONNECTION_TYPES
    
    def test_arrow_styles_defined(self):
        """Test that arrow styles are defined."""
        assert 'single' in ARROW_STYLES
        assert 'double' in ARROW_STYLES
        assert 'none' in ARROW_STYLES
    
    def test_routing_modes_defined(self):
        """Test that routing modes are defined."""
        assert 'auto' in ROUTING_MODES
        assert 'straight' in ROUTING_MODES
        assert 'orthogonal' in ROUTING_MODES
        assert 'curved' in ROUTING_MODES


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
