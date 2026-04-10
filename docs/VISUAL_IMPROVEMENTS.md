# Visual Improvements: Mermaid and Blender Inspired

## Overview

This document describes visual improvements to VPB's diagram representation inspired by:
1. **Mermaid Diagrams**: Clean, modern visual style with optimal readability
2. **Blender Node Editor**: Intuitive node-based visual programming interface

## Implemented Features

### 1. Mermaid Export (✅ Complete)

VPB now exports diagrams to Mermaid format, enabling:
- Text-based diagram representation
- Version control friendly format
- Wide platform support (GitHub, GitLab, wikis, documentation)
- Automatic shape mapping for different element types
- Clean, modern visual style

See [MERMAID_EXPORT.md](MERMAID_EXPORT.md) for full documentation.

## Planned Improvements

### 2. Enhanced Connection Rendering

#### Current State
- Basic straight-line connections
- Limited routing options (auto, straight, orthogonal, curved)

#### Mermaid-Inspired Improvements
- **Smoother Curves**: Implement Bezier curves for more natural connection flow
- **Smart Routing**: Auto-avoid overlapping elements
- **Arrow Styles**: Multiple arrow head styles (single, double, hollow, filled)
- **Connection Labels**: Better label positioning and background

#### Implementation Approach
```python
# In vpb/ui/canvas.py - Connection rendering
def _draw_connection_bezier(self, conn: VPBConnection):
    """Draw connection with smooth Bezier curve."""
    source = self.elements.get(conn.source_element)
    target = self.elements.get(conn.target_element)
    
    if not source or not target:
        return
    
    # Calculate control points for smooth curve
    sx, sy = source.center()
    tx, ty = target.center()
    
    # Horizontal offset for control points
    dx = abs(tx - sx)
    offset = min(dx * 0.5, 100)
    
    # Bezier control points
    cp1_x = sx + offset
    cp1_y = sy
    cp2_x = tx - offset
    cp2_y = ty
    
    # Draw smooth curve
    self.create_line(
        sx, sy, cp1_x, cp1_y, cp2_x, cp2_y, tx, ty,
        smooth=True,
        splinesteps=20,
        arrow=tk.LAST,
        tags=f"conn:{conn.connection_id}"
    )
```

### 3. Node Grouping and Hierarchy (Blender-Inspired)

#### Concept
Blender's node editor uses frames to group related nodes. VPB can adopt this for:
- Subprocess visualization
- Organizational grouping
- Visual hierarchy

#### Features
- **Frame Elements**: Collapsible containers that group related elements
- **Color-Coded Groups**: Different colors for different subprocess types
- **Nesting**: Support for nested frames
- **Auto-Layout**: Automatically arrange elements within groups

#### Visual Design
```
┌─ Subprocess: Document Review ─────────────────┐
│  ┌──────────┐      ┌──────────┐              │
│  │ Receive  │─────▶│  Check   │              │
│  │ Document │      │Completeness              │
│  └──────────┘      └──────────┘              │
│                          │                    │
│                          ▼                    │
│                    ┌──────────┐              │
│                    │  Review  │              │
│                    │ Content  │              │
│                    └──────────┘              │
└───────────────────────────────────────────────┘
```

### 4. Improved Color Coding

#### Mermaid Color Scheme
Adopt Mermaid's clean, accessible color palette:

| Element Type | Current Color | Mermaid-Inspired |
|--------------|---------------|------------------|
| Start/End Events | Light Green | #90EE90 (✅ In Mermaid export) |
| Process Steps | Light Blue | #ADD8E6 (✅ In Mermaid export) |
| Decisions | Wheat | #F5DEB3 (✅ In Mermaid export) |
| Containers | Light Yellow | #FFFFE0 (✅ In Mermaid export) |
| Selected | Blue | #2D7FF9 |
| Error State | Light Red | #FFB6C1 |
| Warning State | Light Orange | #FFE4B5 |

#### Status Indicators
- **Processing**: Animated pulse effect
- **Completed**: Green checkmark badge
- **Error**: Red X badge
- **Warning**: Yellow ! badge

### 5. Grid and Alignment Helpers

#### Blender-Inspired Grid
- **Snap to Grid**: Configurable grid size (default: 20px)
- **Grid Lines**: Subtle background grid
- **Smart Guides**: Show alignment lines when dragging
- **Distribute**: Evenly space selected elements

#### Implementation
```python
class VPBCanvas:
    def draw_grid(self, spacing=20):
        """Draw background grid for alignment."""
        width = self.winfo_width()
        height = self.winfo_height()
        
        # Vertical lines
        for x in range(0, width, spacing):
            self.create_line(
                x, 0, x, height,
                fill="#E0E0E0",
                tags="grid"
            )
        
        # Horizontal lines
        for y in range(0, height, spacing):
            self.create_line(
                0, y, width, y,
                fill="#E0E0E0",
                tags="grid"
            )
        
        # Send grid to back
        self.tag_lower("grid")
```

### 6. Enhanced Element Rendering

#### Shadow Effects
Add subtle shadows for depth perception (Mermaid-like):
```python
def _draw_element_with_shadow(self, element):
    """Draw element with shadow effect."""
    x, y = element.x, element.y
    
    # Shadow (offset by 2px)
    shadow = self.create_rectangle(
        x + 2, y + 2,
        x + self.NODE_W + 2, y + self.NODE_H + 2,
        fill="#CCCCCC",
        outline="",
        tags=f"shadow:{element.element_id}"
    )
    
    # Actual element
    rect = self.create_rectangle(
        x, y,
        x + self.NODE_W, y + self.NODE_H,
        fill=self._get_element_color(element),
        outline="#333333",
        width=2,
        tags=f"node:{element.element_id}"
    )
```

#### Icon Support
Add icons to element types (similar to Mermaid's font-awesome support):
- Start: ▶️ Play icon
- End: ⏹️ Stop icon
- Process: ⚙️ Gear icon
- Decision: ❓ Question mark
- Document: 📄 Document icon

### 7. Minimap (Blender-Inspired)

Add a minimap in the corner showing overview of entire diagram:
```
┌─────────────────────────────────────┐
│ Main Canvas                         │
│                                     │
│  [Process Flow]                     │
│                                     │
│                    ┌──────────┐    │
│                    │ Minimap  │    │
│                    │ ▪▪▪▪▪▪▪  │    │
│                    │ ▪▪▪▪▪▪▪  │    │
│                    │ ▪▪[View] │    │
│                    └──────────┘    │
└─────────────────────────────────────┘
```

### 8. Animation and Feedback

#### Hover Effects
- **Element Hover**: Slight glow/highlight
- **Connection Hover**: Thicker line, highlighted path
- **Button Hover**: Scale up slightly (1.05x)

#### Transitions
- **Smooth Zoom**: Animated zoom with easing
- **Element Movement**: Smooth animation when auto-arranging
- **Fade In**: New elements fade in smoothly

## Implementation Roadmap

### Phase 1: Foundation (✅ Complete)
- [x] Mermaid export functionality
- [x] Basic shape mapping
- [x] Metadata support

### Phase 2: Enhanced Connections (Priority)
- [ ] Implement Bezier curve rendering
- [ ] Add smart routing algorithm
- [ ] Improve label positioning
- [ ] Add more arrow styles

### Phase 3: Visual Hierarchy
- [ ] Implement frame/group elements
- [ ] Add collapsible containers
- [ ] Color-coded grouping
- [ ] Auto-layout for groups

### Phase 4: Polish
- [ ] Grid and snap-to-grid
- [ ] Smart alignment guides
- [ ] Shadow effects
- [ ] Icon support
- [ ] Minimap
- [ ] Hover effects and animations

## Configuration

Visual improvements should be configurable via settings:

```python
class VisualConfig:
    # Connections
    connection_style: str = "bezier"  # straight, bezier, orthogonal
    connection_smoothness: float = 0.7
    show_connection_labels: bool = True
    
    # Grid
    show_grid: bool = True
    grid_spacing: int = 20
    snap_to_grid: bool = True
    
    # Effects
    show_shadows: bool = True
    shadow_offset: int = 2
    show_icons: bool = True
    animate_transitions: bool = True
    
    # Minimap
    show_minimap: bool = True
    minimap_size: int = 150
    minimap_position: str = "bottom-right"
```

## Benefits

1. **Better Readability**: Cleaner visual style inspired by Mermaid
2. **Improved Organization**: Grouping and hierarchy from Blender concepts
3. **Enhanced UX**: Modern visual feedback and animations
4. **Professional Look**: Polished appearance suitable for presentations
5. **Accessibility**: Better color contrast and visual indicators

## References

- [Mermaid.js Documentation](https://mermaid.js.org/)
- [Blender Node Editor](https://docs.blender.org/manual/en/latest/interface/controls/nodes/)
- [Material Design Motion](https://material.io/design/motion/)
- [Graph Visualization Best Practices](https://www.cambridge.org/core/books/abs/handbook-of-graph-drawing-and-visualization/graph-drawing-aesthetics/6C42E5AE60C2B62E0F47BD34341C5EA7)

## Changelog

### 2025-12-31
- Initial document created
- Mermaid export implemented
- Roadmap defined for visual improvements
