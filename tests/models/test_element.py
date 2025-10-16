"""Unit tests for VPBElement model"""

import pytest
from vpb.models.element import (
    VPBElement,
    ElementFactory,
    ELEMENT_TYPES,
)


class TestVPBElement:
    """Test suite for VPBElement class."""
    
    def test_create_element(self):
        """Test creating a basic element."""
        element = VPBElement(
            element_id="test1",
            element_type="Prozess",
            name="Test Process",
            x=100,
            y=200
        )
        
        assert element.element_id == "test1"
        assert element.element_type == "Prozess"
        assert element.name == "Test Process"
        assert element.x == 100
        assert element.y == 200
    
    def test_element_defaults(self):
        """Test that optional fields have proper defaults."""
        element = VPBElement(
            element_id="test1",
            element_type="Prozess",
            name="Test",
            x=0,
            y=0
        )
        
        assert element.description == ""
        assert element.responsible_authority == ""
        assert element.legal_basis == ""
        assert element.deadline_days == 0
        assert element.members == []
        assert element.collapsed is False
        assert element.canvas_items == []
    
    def test_validation_empty_id(self):
        """Test that empty element_id raises error."""
        with pytest.raises(ValueError, match="element_id cannot be empty"):
            VPBElement(
                element_id="",
                element_type="Prozess",
                name="Test",
                x=0,
                y=0
            )
    
    def test_validation_empty_type(self):
        """Test that empty element_type raises error."""
        with pytest.raises(ValueError, match="element_type cannot be empty"):
            VPBElement(
                element_id="test1",
                element_type="",
                name="Test",
                x=0,
                y=0
            )
    
    def test_validation_negative_deadline(self):
        """Test that negative deadline raises error."""
        with pytest.raises(ValueError, match="deadline_days cannot be negative"):
            VPBElement(
                element_id="test1",
                element_type="Prozess",
                name="Test",
                x=0,
                y=0,
                deadline_days=-5
            )
    
    def test_center(self):
        """Test center() method."""
        element = VPBElement(
            element_id="test1",
            element_type="Prozess",
            name="Test",
            x=150,
            y=250
        )
        
        center = element.center()
        assert center == (150, 250)
    
    def test_move_to(self):
        """Test move_to() creates new element at new position."""
        element = VPBElement(
            element_id="test1",
            element_type="Prozess",
            name="Test",
            x=100,
            y=100,
            description="Original"
        )
        
        moved = element.move_to(200, 300)
        
        # New position
        assert moved.x == 200
        assert moved.y == 300
        
        # Other properties preserved
        assert moved.element_id == "test1"
        assert moved.element_type == "Prozess"
        assert moved.description == "Original"
        
        # Original unchanged
        assert element.x == 100
        assert element.y == 100
    
    def test_clone(self):
        """Test clone() creates deep copy."""
        element = VPBElement(
            element_id="original",
            element_type="Prozess",
            name="Original",
            x=100,
            y=100,
            description="Description",
            members=["member1", "member2"]
        )
        
        cloned = element.clone()
        
        # Different ID
        assert cloned.element_id == "original_copy"
        
        # Modified name
        assert cloned.name == "Original (copy)"
        
        # Offset position
        assert cloned.x == 120
        assert cloned.y == 120
        
        # Properties preserved
        assert cloned.element_type == "Prozess"
        assert cloned.description == "Description"
        assert cloned.members == ["member1", "member2"]
        
        # Canvas items not copied
        assert cloned.canvas_items == []
        
        # Deep copy of lists
        cloned.members.append("member3")
        assert len(element.members) == 2
    
    def test_clone_with_new_id(self):
        """Test clone() with custom ID."""
        element = VPBElement(
            element_id="original",
            element_type="Prozess",
            name="Test",
            x=0,
            y=0
        )
        
        cloned = element.clone(new_id="custom_id")
        
        assert cloned.element_id == "custom_id"
        assert cloned.name == "Test"  # Name not modified
    
    def test_is_container(self):
        """Test is_container() method."""
        container = VPBElement(
            element_id="c1",
            element_type="Container",
            name="Container",
            x=0,
            y=0
        )
        
        prozess = VPBElement(
            element_id="p1",
            element_type="Prozess",
            name="Prozess",
            x=0,
            y=0
        )
        
        assert container.is_container() is True
        assert prozess.is_container() is False
    
    def test_is_gateway(self):
        """Test is_gateway() method."""
        and_gate = VPBElement(
            element_id="g1",
            element_type="AND",
            name="AND",
            x=0,
            y=0
        )
        
        or_gate = VPBElement(
            element_id="g2",
            element_type="OR",
            name="OR",
            x=0,
            y=0
        )
        
        xor_gate = VPBElement(
            element_id="g3",
            element_type="XOR",
            name="XOR",
            x=0,
            y=0
        )
        
        prozess = VPBElement(
            element_id="p1",
            element_type="Prozess",
            name="Prozess",
            x=0,
            y=0
        )
        
        assert and_gate.is_gateway() is True
        assert or_gate.is_gateway() is True
        assert xor_gate.is_gateway() is True
        assert prozess.is_gateway() is False
    
    def test_to_dict(self):
        """Test serialization to dictionary."""
        element = VPBElement(
            element_id="test1",
            element_type="Prozess",
            name="Test",
            x=100,
            y=200,
            description="Test description",
            deadline_days=30,
            members=["m1", "m2"]
        )
        
        data = element.to_dict()
        
        assert isinstance(data, dict)
        assert data['element_id'] == "test1"
        assert data['element_type'] == "Prozess"
        assert data['name'] == "Test"
        assert data['x'] == 100
        assert data['y'] == 200
        assert data['description'] == "Test description"
        assert data['deadline_days'] == 30
        assert data['members'] == ["m1", "m2"]
    
    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            'element_id': 'test1',
            'element_type': 'Prozess',
            'name': 'Test',
            'x': 100,
            'y': 200,
            'description': 'Test description',
            'deadline_days': 30,
            'members': ['m1', 'm2']
        }
        
        element = VPBElement.from_dict(data)
        
        assert element.element_id == "test1"
        assert element.element_type == "Prozess"
        assert element.name == "Test"
        assert element.x == 100
        assert element.y == 200
        assert element.description == "Test description"
        assert element.deadline_days == 30
        assert element.members == ["m1", "m2"]
    
    def test_round_trip_serialization(self):
        """Test that to_dict/from_dict preserves all data."""
        original = VPBElement(
            element_id="test1",
            element_type="Entscheidung",
            name="Decision",
            x=150,
            y=250,
            description="Important decision",
            responsible_authority="Dept A",
            legal_basis="§42",
            deadline_days=14,
            geo_reference="Berlin",
            ref_file="doc.pdf",
            members=["child1"],
            collapsed=True
        )
        
        data = original.to_dict()
        restored = VPBElement.from_dict(data)
        
        assert restored.element_id == original.element_id
        assert restored.element_type == original.element_type
        assert restored.name == original.name
        assert restored.x == original.x
        assert restored.y == original.y
        assert restored.description == original.description
        assert restored.responsible_authority == original.responsible_authority
        assert restored.legal_basis == original.legal_basis
        assert restored.deadline_days == original.deadline_days
        assert restored.geo_reference == original.geo_reference
        assert restored.ref_file == original.ref_file
        assert restored.members == original.members
        assert restored.collapsed == original.collapsed
    
    def test_repr(self):
        """Test string representation."""
        element = VPBElement(
            element_id="test1",
            element_type="Prozess",
            name="Test Process",
            x=100,
            y=200
        )
        
        repr_str = repr(element)
        
        assert "VPBElement" in repr_str
        assert "test1" in repr_str
        assert "Prozess" in repr_str
        assert "Test Process" in repr_str


class TestElementFactory:
    """Test suite for ElementFactory."""
    
    def test_create_basic(self):
        """Test basic element creation."""
        element = ElementFactory.create('Prozess', 100, 200)
        
        assert element.element_type == "Prozess"
        assert element.x == 100
        assert element.y == 200
        assert element.element_id.startswith("elem_")
        assert element.name == "Prozess"
    
    def test_create_with_custom_id(self):
        """Test creation with custom ID."""
        element = ElementFactory.create(
            'Prozess',
            100, 200,
            element_id="custom_id"
        )
        
        assert element.element_id == "custom_id"
    
    def test_create_with_custom_name(self):
        """Test creation with custom name."""
        element = ElementFactory.create(
            'Prozess',
            100, 200,
            name="Custom Name"
        )
        
        assert element.name == "Custom Name"
    
    def test_create_with_kwargs(self):
        """Test creation with additional properties."""
        element = ElementFactory.create(
            'Prozess',
            100, 200,
            description="Test description",
            deadline_days=30
        )
        
        assert element.description == "Test description"
        assert element.deadline_days == 30
    
    def test_create_prozess(self):
        """Test convenience method for Prozess."""
        element = ElementFactory.create_prozess(100, 200, "My Process")
        
        assert element.element_type == "Prozess"
        assert element.name == "My Process"
        assert element.x == 100
        assert element.y == 200
    
    def test_create_vorprozess(self):
        """Test convenience method for VorProzess."""
        element = ElementFactory.create_vorprozess(100, 200)
        
        assert element.element_type == "VorProzess"
        assert element.name == "Vor-Prozess"
    
    def test_create_nachprozess(self):
        """Test convenience method for NachProzess."""
        element = ElementFactory.create_nachprozess(100, 200)
        
        assert element.element_type == "NachProzess"
        assert element.name == "Nach-Prozess"
    
    def test_create_entscheidung(self):
        """Test convenience method for Entscheidung."""
        element = ElementFactory.create_entscheidung(100, 200)
        
        assert element.element_type == "Entscheidung"
        assert element.name == "Entscheidung"
    
    def test_create_gateway_and(self):
        """Test AND gateway creation."""
        element = ElementFactory.create_gateway('AND', 100, 200)
        
        assert element.element_type == "AND"
        assert element.name == "AND-Gateway"
        assert element.is_gateway() is True
    
    def test_create_gateway_or(self):
        """Test OR gateway creation."""
        element = ElementFactory.create_gateway('OR', 100, 200)
        
        assert element.element_type == "OR"
        assert element.name == "OR-Gateway"
    
    def test_create_gateway_xor(self):
        """Test XOR gateway creation."""
        element = ElementFactory.create_gateway('XOR', 100, 200)
        
        assert element.element_type == "XOR"
        assert element.name == "XOR-Gateway"
    
    def test_create_gateway_invalid_type(self):
        """Test that invalid gateway type raises error."""
        with pytest.raises(ValueError, match="Invalid gateway type"):
            ElementFactory.create_gateway('INVALID', 100, 200)
    
    def test_create_gateway_custom_name(self):
        """Test gateway creation with custom name."""
        element = ElementFactory.create_gateway('AND', 100, 200, "Custom Gateway")
        
        assert element.name == "Custom Gateway"
    
    def test_create_container(self):
        """Test container creation."""
        element = ElementFactory.create_container(
            100, 200,
            "My Container",
            members=["child1", "child2"]
        )
        
        assert element.element_type == "Container"
        assert element.name == "My Container"
        assert element.members == ["child1", "child2"]
        assert element.is_container() is True
    
    def test_create_container_empty(self):
        """Test container creation without members."""
        element = ElementFactory.create_container(100, 200)
        
        assert element.members == []


class TestElementTypes:
    """Test ELEMENT_TYPES constant."""
    
    def test_element_types_defined(self):
        """Test that all element types are defined."""
        assert 'VorProzess' in ELEMENT_TYPES
        assert 'Prozess' in ELEMENT_TYPES
        assert 'NachProzess' in ELEMENT_TYPES
        assert 'Entscheidung' in ELEMENT_TYPES
        assert 'Container' in ELEMENT_TYPES
        assert 'AND' in ELEMENT_TYPES
        assert 'OR' in ELEMENT_TYPES
        assert 'XOR' in ELEMENT_TYPES
    
    def test_element_types_values(self):
        """Test element type display names."""
        assert ELEMENT_TYPES['Prozess'] == 'Prozess'
        assert ELEMENT_TYPES['AND'] == 'AND-Gateway'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
