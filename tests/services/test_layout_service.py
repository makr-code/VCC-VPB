"""
Tests for LayoutService
========================

Tests for layout algorithms and arrangement operations.
"""

import pytest
import math
from vpb.services.layout_service import (
    LayoutService,
    LayoutConfig,
    LayoutResult,
    LayoutServiceError,
    InsufficientElementsError,
)
from vpb.models.document import DocumentModel, DocumentMetadata
from vpb.models.element import VPBElement, ElementFactory
from vpb.models.connection import VPBConnection


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def layout_service():
    """Create layout service with default config."""
    return LayoutService()


@pytest.fixture
def custom_layout_service():
    """Create layout service with custom config."""
    config = LayoutConfig(
        auto_layout_column_spacing=250,
        auto_layout_row_spacing=150,
        circular_min_radius=100.0,
    )
    return LayoutService(config)


@pytest.fixture
def simple_elements():
    """Create simple test elements."""
    return [
        VPBElement(element_id="e1", element_type="Prozess", name="Task 1", x=100, y=100),
        VPBElement(element_id="e2", element_type="Prozess", name="Task 2", x=200, y=150),
        VPBElement(element_id="e3", element_type="Prozess", name="Task 3", x=300, y=200),
    ]


@pytest.fixture
def flow_document():
    """Create document with connected elements forming a flow."""
    doc = DocumentModel()
    doc.metadata.title = "Test Flow"
    
    # Start -> Process1 -> Process2 -> End
    start = VPBElement(element_id="start", element_type="START_EVENT", name="Start", x=0, y=0)
    process1 = ElementFactory.create_prozess(x=100, y=0)
    process2 = ElementFactory.create_prozess(x=200, y=0)
    end = VPBElement(element_id="end", element_type="END_EVENT", name="End", x=300, y=0)
    
    doc.add_element(start)
    doc.add_element(process1)
    doc.add_element(process2)
    doc.add_element(end)
    
    doc.add_connection(VPBConnection(
        connection_id="c1",
        source_element=start.element_id,
        target_element=process1.element_id
    ))
    doc.add_connection(VPBConnection(
        connection_id="c2",
        source_element=process1.element_id,
        target_element=process2.element_id
    ))
    doc.add_connection(VPBConnection(
        connection_id="c3",
        source_element=process2.element_id,
        target_element=end.element_id
    ))
    
    return doc


# ============================================================================
# Initialization Tests
# ============================================================================

class TestLayoutServiceInit:
    """Test layout service initialization."""
    
    def test_init_defaults(self):
        """Test initialization with default config."""
        service = LayoutService()
        assert service.config is not None
        assert isinstance(service.config, LayoutConfig)
        assert service.config.auto_layout_column_spacing == 200
    
    def test_init_custom_config(self):
        """Test initialization with custom config."""
        config = LayoutConfig(auto_layout_column_spacing=300)
        service = LayoutService(config)
        assert service.config.auto_layout_column_spacing == 300
    
    def test_repr(self, layout_service):
        """Test string representation."""
        repr_str = repr(layout_service)
        assert "LayoutService" in repr_str
        assert "config=" in repr_str


# ============================================================================
# Alignment Tests
# ============================================================================

class TestAlignment:
    """Test element alignment operations."""
    
    def test_align_left(self, layout_service, simple_elements):
        """Test left alignment."""
        result = layout_service.align_elements(simple_elements, "left")
        
        assert isinstance(result, LayoutResult)
        assert result.elements_moved > 0
        
        # All elements should have same left edge
        positions = result.element_positions
        x_coords = [positions[el.element_id][0] for el in simple_elements]
        
        # Calculate expected x (accounting for element width)
        bounds = [layout_service._get_element_bounds(el) for el in simple_elements]
        min_left = min(b[0] for b in bounds)
        width = 120  # Prozess width
        expected_x = min_left + width // 2
        
        assert all(abs(x - expected_x) < 2 for x in x_coords)
    
    def test_align_right(self, layout_service, simple_elements):
        """Test right alignment."""
        result = layout_service.align_elements(simple_elements, "right")
        
        assert result.elements_moved > 0
        positions = result.element_positions
        
        # All elements should have same right edge (adjusted for width)
        bounds = [layout_service._get_element_bounds(el) for el in simple_elements]
        max_right = max(b[2] for b in bounds)
        width = 120
        expected_x = max_right - width // 2
        
        x_coords = [positions[el.element_id][0] for el in simple_elements]
        assert all(abs(x - expected_x) < 2 for x in x_coords)
    
    def test_align_center(self, layout_service, simple_elements):
        """Test center alignment."""
        result = layout_service.align_elements(simple_elements, "center")
        
        assert result.elements_moved > 0
        positions = result.element_positions
        
        # All elements should have same center x
        x_coords = [positions[el.element_id][0] for el in simple_elements]
        avg_x = sum(el.x for el in simple_elements) / len(simple_elements)
        
        assert all(abs(x - avg_x) < 2 for x in x_coords)
    
    def test_align_top(self, layout_service, simple_elements):
        """Test top alignment."""
        result = layout_service.align_elements(simple_elements, "top")
        
        assert result.elements_moved > 0
        positions = result.element_positions
        
        # All elements should have same top edge
        bounds = [layout_service._get_element_bounds(el) for el in simple_elements]
        min_top = min(b[1] for b in bounds)
        height = 80
        expected_y = min_top + height // 2
        
        y_coords = [positions[el.element_id][1] for el in simple_elements]
        assert all(abs(y - expected_y) < 2 for y in y_coords)
    
    def test_align_bottom(self, layout_service, simple_elements):
        """Test bottom alignment."""
        result = layout_service.align_elements(simple_elements, "bottom")
        
        assert result.elements_moved > 0
        positions = result.element_positions
        
        bounds = [layout_service._get_element_bounds(el) for el in simple_elements]
        max_bottom = max(b[3] for b in bounds)
        height = 80
        expected_y = max_bottom - height // 2
        
        y_coords = [positions[el.element_id][1] for el in simple_elements]
        assert all(abs(y - expected_y) < 2 for y in y_coords)
    
    def test_align_middle(self, layout_service, simple_elements):
        """Test middle/vertical alignment."""
        result = layout_service.align_elements(simple_elements, "middle")
        
        assert result.elements_moved > 0
        positions = result.element_positions
        
        # All elements should have same center y
        y_coords = [positions[el.element_id][1] for el in simple_elements]
        avg_y = sum(el.y for el in simple_elements) / len(simple_elements)
        
        assert all(abs(y - avg_y) < 2 for y in y_coords)
    
    def test_align_insufficient_elements(self, layout_service):
        """Test alignment with insufficient elements."""
        single_element = [VPBElement(element_id="e1", element_type="Prozess", name="Task", x=100, y=100)]
        
        with pytest.raises(InsufficientElementsError):
            layout_service.align_elements(single_element, "left")
    
    def test_align_invalid_mode(self, layout_service, simple_elements):
        """Test alignment with invalid mode."""
        with pytest.raises(ValueError, match="Invalid alignment mode"):
            layout_service.align_elements(simple_elements, "invalid")
    
    def test_align_no_movement_needed(self, layout_service):
        """Test alignment when elements already aligned."""
        # All elements at same x
        elements = [
            VPBElement(element_id="e1", element_type="Prozess", name="T1", x=100, y=100),
            VPBElement(element_id="e2", element_type="Prozess", name="T2", x=100, y=200),
        ]
        
        result = layout_service.align_elements(elements, "center")
        # Should still return result, but may have 0 moved
        assert isinstance(result, LayoutResult)


# ============================================================================
# Circular Arrangement Tests
# ============================================================================

class TestCircularArrangement:
    """Test circular arrangement."""
    
    def test_arrange_circular_basic(self, layout_service, simple_elements):
        """Test basic circular arrangement."""
        result = layout_service.arrange_circular(simple_elements)
        
        assert isinstance(result, LayoutResult)
        assert result.elements_moved > 0
        assert len(result.element_positions) == 3
    
    def test_arrange_circular_with_center(self, layout_service, simple_elements):
        """Test circular arrangement with specified center."""
        center = (500.0, 500.0)
        result = layout_service.arrange_circular(simple_elements, center=center)
        
        assert result.elements_moved > 0
        positions = result.element_positions
        
        # Verify elements are roughly equidistant from center
        distances = []
        for el in simple_elements:
            x, y = positions[el.element_id]
            dist = math.hypot(x - center[0], y - center[1])
            distances.append(dist)
        
        # All distances should be similar (within tolerance)
        avg_dist = sum(distances) / len(distances)
        assert all(abs(d - avg_dist) < 5 for d in distances)
    
    def test_arrange_circular_with_radius(self, layout_service, simple_elements):
        """Test circular arrangement with specified radius."""
        radius = 150.0
        result = layout_service.arrange_circular(simple_elements, radius=radius)
        
        assert result.elements_moved > 0
        
        # Calculate center from result
        positions = result.element_positions
        cx = sum(positions[el.element_id][0] for el in simple_elements) / len(simple_elements)
        cy = sum(positions[el.element_id][1] for el in simple_elements) / len(simple_elements)
        
        # Verify distances match radius
        for el in simple_elements:
            x, y = positions[el.element_id]
            dist = math.hypot(x - cx, y - cy)
            assert abs(dist - radius) < 2
    
    def test_arrange_circular_insufficient_elements(self, layout_service):
        """Test circular arrangement with insufficient elements."""
        single = [VPBElement(element_id="e1", element_type="Prozess", name="T", x=100, y=100)]
        
        with pytest.raises(InsufficientElementsError):
            layout_service.arrange_circular(single)
    
    def test_arrange_circular_preserves_relative_order(self, layout_service):
        """Test that circular arrangement preserves angular order."""
        # Create elements in a line
        elements = [
            VPBElement(element_id="e1", element_type="Prozess", name="T1", x=0, y=0),
            VPBElement(element_id="e2", element_type="Prozess", name="T2", x=100, y=0),
            VPBElement(element_id="e3", element_type="Prozess", name="T3", x=200, y=0),
        ]
        
        result = layout_service.arrange_circular(elements)
        
        # Elements should maintain their relative angular order
        positions = result.element_positions
        cx = sum(positions[el.element_id][0] for el in elements) / len(elements)
        cy = sum(positions[el.element_id][1] for el in elements) / len(elements)
        
        angles = []
        for el in elements:
            x, y = positions[el.element_id]
            angle = math.atan2(y - cy, x - cx)
            angles.append(angle)
        
        # Check angles are distributed
        assert len(set(angles)) == len(angles)  # All unique


# ============================================================================
# Auto Layout Tests
# ============================================================================

class TestAutoLayout:
    """Test automatic hierarchical layout."""
    
    def test_auto_layout_simple_flow(self, layout_service, flow_document):
        """Test auto-layout on simple linear flow."""
        result = layout_service.auto_layout(flow_document)
        
        assert isinstance(result, LayoutResult)
        assert result.elements_moved >= 0  # May be 0 if already laid out
        assert len(result.element_positions) == 4
    
    def test_auto_layout_creates_layers(self, layout_service, flow_document):
        """Test that auto-layout creates hierarchical layers."""
        result = layout_service.auto_layout(flow_document)
        
        positions = result.element_positions
        elements = flow_document.get_all_elements()
        
        # Get x coordinates (layer positions)
        x_coords = [positions[el.element_id][0] for el in elements]
        
        # Should have increasing x for sequential elements
        # (allowing for some tolerance)
        assert len(set(x_coords)) >= 2  # At least 2 different layers
    
    def test_auto_layout_empty_document(self, layout_service):
        """Test auto-layout on empty document."""
        doc = DocumentModel()
        doc.metadata.title = "Empty"
        result = layout_service.auto_layout(doc)
        
        assert result.elements_moved == 0
        assert len(result.element_positions) == 0
        assert "No elements" in result.message
    
    def test_auto_layout_disconnected_elements(self, layout_service):
        """Test auto-layout with disconnected elements."""
        doc = DocumentModel()
        doc.metadata.title = "Disconnected"
        
        e1 = ElementFactory.create_prozess(x=0, y=0)
        e2 = ElementFactory.create_prozess(x=100, y=100)
        e3 = ElementFactory.create_prozess(x=200, y=200)
        
        doc.add_element(e1)
        doc.add_element(e2)
        doc.add_element(e3)
        
        result = layout_service.auto_layout(doc)
        
        # Should still create layout even without connections
        assert len(result.element_positions) == 3
    
    def test_auto_layout_with_custom_spacing(self, custom_layout_service, flow_document):
        """Test auto-layout with custom spacing."""
        result = custom_layout_service.auto_layout(flow_document)
        
        assert result.elements_moved >= 0
        positions = result.element_positions
        
        # Check that spacing matches custom config (250)
        elements = flow_document.get_all_elements()
        x_coords = sorted(set(positions[el.element_id][0] for el in elements))
        
        if len(x_coords) > 1:
            # Spacing between layers should be ~250
            spacing = x_coords[1] - x_coords[0]
            assert abs(spacing - 250) < 10


# ============================================================================
# Distribution Tests
# ============================================================================

class TestDistribution:
    """Test element distribution."""
    
    def test_distribute_horizontal(self, layout_service):
        """Test horizontal distribution."""
        # Create elements with uneven spacing
        elements = [
            VPBElement(element_id="e1", element_type="Prozess", name="Task 1", x=50, y=100),
            VPBElement(element_id="e2", element_type="Prozess", name="Task 2", x=150, y=100),
            VPBElement(element_id="e3", element_type="Prozess", name="Task 3", x=400, y=100),
        ]
        
        result = layout_service.distribute_elements(elements, "horizontal")
        
        assert result.elements_moved > 0
        positions = result.element_positions
        
        # Check even spacing
        x_coords = sorted(positions[el.element_id][0] for el in elements)
        spacings = [x_coords[i+1] - x_coords[i] for i in range(len(x_coords)-1)]
        
        # All spacings should be equal
        avg_spacing = sum(spacings) / len(spacings)
        assert all(abs(s - avg_spacing) < 2 for s in spacings)
    
    def test_distribute_vertical(self, layout_service):
        """Test vertical distribution."""
        # Create elements with uneven spacing
        elements = [
            VPBElement(element_id="e1", element_type="Prozess", name="Task 1", x=100, y=50),
            VPBElement(element_id="e2", element_type="Prozess", name="Task 2", x=100, y=100),
            VPBElement(element_id="e3", element_type="Prozess", name="Task 3", x=100, y=300),
        ]
        
        result = layout_service.distribute_elements(elements, "vertical")
        
        assert result.elements_moved > 0
        positions = result.element_positions
        
        # Check even spacing
        y_coords = sorted(positions[el.element_id][1] for el in elements)
        spacings = [y_coords[i+1] - y_coords[i] for i in range(len(y_coords)-1)]
        
        avg_spacing = sum(spacings) / len(spacings)
        assert all(abs(s - avg_spacing) < 2 for s in spacings)
    
    def test_distribute_insufficient_elements(self, layout_service):
        """Test distribution with insufficient elements."""
        two_elements = [
            VPBElement(element_id="e1", element_type="Prozess", name="T1", x=100, y=100),
            VPBElement(element_id="e2", element_type="Prozess", name="T2", x=200, y=200),
        ]
        
        with pytest.raises(InsufficientElementsError):
            layout_service.distribute_elements(two_elements, "horizontal")
    
    def test_distribute_invalid_mode(self, layout_service, simple_elements):
        """Test distribution with invalid mode."""
        with pytest.raises(ValueError, match="Invalid distribution mode"):
            layout_service.distribute_elements(simple_elements, "diagonal")


# ============================================================================
# Grid Arrangement Tests
# ============================================================================

class TestGridArrangement:
    """Test grid arrangement."""
    
    def test_arrange_grid_basic(self, layout_service, simple_elements):
        """Test basic grid arrangement."""
        result = layout_service.arrange_grid(simple_elements)
        
        assert isinstance(result, LayoutResult)
        assert len(result.element_positions) == 3
    
    def test_arrange_grid_with_columns(self, layout_service):
        """Test grid arrangement with specified columns."""
        elements = [
            VPBElement(element_id=f"e{i}", element_type="Prozess", name=f"T{i}", x=0, y=0)
            for i in range(6)
        ]
        
        result = layout_service.arrange_grid(elements, columns=3)
        
        assert result.elements_moved >= 0
        assert "2x3" in result.message or "grid" in result.message
    
    def test_arrange_grid_empty_elements(self, layout_service):
        """Test grid arrangement with empty list."""
        result = layout_service.arrange_grid([])
        
        assert result.elements_moved == 0
        assert len(result.element_positions) == 0
    
    def test_arrange_grid_single_element(self, layout_service):
        """Test grid arrangement with single element."""
        element = [VPBElement(element_id="e1", element_type="Prozess", name="T", x=100, y=100)]
        
        result = layout_service.arrange_grid(element)
        
        assert len(result.element_positions) == 1
    
    def test_arrange_grid_calculates_columns(self, layout_service):
        """Test that grid calculates columns automatically."""
        # 9 elements should result in 3x3 grid
        elements = [
            VPBElement(element_id=f"e{i}", element_type="Prozess", name=f"T{i}", x=0, y=0)
            for i in range(9)
        ]
        
        result = layout_service.arrange_grid(elements)
        
        assert len(result.element_positions) == 9
        # Should arrange in roughly square grid
        positions = result.element_positions
        x_coords = set(pos[0] for pos in positions.values())
        y_coords = set(pos[1] for pos in positions.values())
        
        # Should have 3 unique x and y positions
        assert len(x_coords) == 3
        assert len(y_coords) == 3


# ============================================================================
# Layout Result Tests
# ============================================================================

class TestLayoutResult:
    """Test LayoutResult class."""
    
    def test_layout_result_truthy_with_moves(self):
        """Test that result with moves is truthy."""
        result = LayoutResult(
            element_positions={"e1": (100, 100)},
            elements_moved=1
        )
        assert bool(result) is True
    
    def test_layout_result_falsy_without_moves(self):
        """Test that result without moves is falsy."""
        result = LayoutResult(
            element_positions={},
            elements_moved=0
        )
        assert bool(result) is False
    
    def test_layout_result_with_message(self):
        """Test layout result with message."""
        result = LayoutResult(
            element_positions={"e1": (100, 100)},
            elements_moved=1,
            message="Test message"
        )
        assert result.message == "Test message"


# ============================================================================
# Integration Tests
# ============================================================================

class TestLayoutIntegration:
    """Integration tests combining multiple layout operations."""
    
    def test_align_then_distribute(self, layout_service):
        """Test aligning then distributing elements."""
        # Create elements with uneven spacing
        elements = [
            VPBElement(element_id="e1", element_type="Prozess", name="Task 1", x=50, y=100),
            VPBElement(element_id="e2", element_type="Prozess", name="Task 2", x=150, y=150),
            VPBElement(element_id="e3", element_type="Prozess", name="Task 3", x=400, y=200),
        ]
        
        # First align
        align_result = layout_service.align_elements(elements, "middle")
        
        # Apply positions
        for el in elements:
            el.x, el.y = align_result.element_positions[el.element_id]
        
        # Then distribute
        dist_result = layout_service.distribute_elements(elements, "horizontal")
        
        assert dist_result.elements_moved > 0
    
    def test_grid_then_circular(self, layout_service):
        """Test grid arrangement followed by circular."""
        elements = [
            VPBElement(element_id=f"e{i}", element_type="Prozess", name=f"T{i}", x=0, y=0)
            for i in range(4)
        ]
        
        # Grid arrangement
        grid_result = layout_service.arrange_grid(elements, columns=2)
        
        # Apply positions
        for el in elements:
            el.x, el.y = grid_result.element_positions[el.element_id]
        
        # Circular arrangement
        circ_result = layout_service.arrange_circular(elements)
        
        assert circ_result.elements_moved > 0
