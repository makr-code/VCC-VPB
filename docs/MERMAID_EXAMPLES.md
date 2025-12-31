# Mermaid Export Examples

This document shows real examples of VPB processes exported to Mermaid format.

## Example 1: Simple Linear Process

### Source (VPB JSON)
```json
{
  "metadata": {
    "title": "Document Approval",
    "description": "Simple document approval process"
  },
  "elements": [
    {"element_id": "e1", "element_type": "Ereignis", "name": "Start", "x": 0, "y": 0},
    {"element_id": "e2", "element_type": "Prozess", "name": "Review", "x": 100, "y": 0},
    {"element_id": "e3", "element_type": "Prozess", "name": "Approve", "x": 200, "y": 0},
    {"element_id": "e4", "element_type": "Ereignis", "name": "End", "x": 300, "y": 0}
  ],
  "connections": [
    {"source_element": "e1", "target_element": "e2"},
    {"source_element": "e2", "target_element": "e3"},
    {"source_element": "e3", "target_element": "e4"}
  ]
}
```

### Exported Mermaid (LR - Left to Right)
```mermaid
---
title: Document Approval
description: Simple document approval process
---

flowchart LR
    node0["Start"]
    node1["Review"]
    node2["Approve"]
    node3["End"]
    
    node0 --> node1
    node1 --> node2
    node2 --> node3
    
    style node0 fill:#90EE90,stroke:#333,stroke-width:2px
    style node1 fill:#ADD8E6,stroke:#333,stroke-width:2px
    style node2 fill:#ADD8E6,stroke:#333,stroke-width:2px
    style node3 fill:#90EE90,stroke:#333,stroke-width:2px
```

## Example 2: Decision Process

### Exported Mermaid (TB - Top to Bottom)
```mermaid
---
title: Application Review
description: Review application with approval decision
---

flowchart TB
    node0["Receive Application"]
    node1["Check Completeness"]
    node2{"Complete?"}
    node3["Request Additional Info"]
    node4["Review Content"]
    node5{"Approved?"}
    node6["Send Approval"]
    node7["Send Rejection"]
    
    node0 --> node1
    node1 --> node2
    node2 -->|No| node3
    node3 --> node0
    node2 -->|Yes| node4
    node4 --> node5
    node5 -->|Yes| node6
    node5 -->|No| node7
    
    style node0 fill:#ADD8E6,stroke:#333,stroke-width:2px
    style node1 fill:#ADD8E6,stroke:#333,stroke-width:2px
    style node2 fill:#F5DEB3,stroke:#333,stroke-width:2px
    style node3 fill:#ADD8E6,stroke:#333,stroke-width:2px
    style node4 fill:#ADD8E6,stroke:#333,stroke-width:2px
    style node5 fill:#F5DEB3,stroke:#333,stroke-width:2px
    style node6 fill:#90EE90,stroke:#333,stroke-width:2px
    style node7 fill:#FFB6C1,stroke:#333,stroke-width:2px
```

## Example 3: Parallel Process

### Exported Mermaid
```mermaid
---
title: Document Processing
description: Parallel document review by multiple departments
---

flowchart TB
    node0["Receive Document"]
    node1{"Split"}
    node2["Legal Review"]
    node3["Technical Review"]
    node4["Financial Review"]
    node5{"Join"}
    node6["Final Decision"]
    
    node0 --> node1
    node1 --> node2
    node1 --> node3
    node1 --> node4
    node2 --> node5
    node3 --> node5
    node4 --> node5
    node5 --> node6
    
    style node0 fill:#ADD8E6,stroke:#333,stroke-width:2px
    style node1 fill:#F5DEB3,stroke:#333,stroke-width:2px
    style node2 fill:#ADD8E6,stroke:#333,stroke-width:2px
    style node3 fill:#ADD8E6,stroke:#333,stroke-width:2px
    style node4 fill:#ADD8E6,stroke:#333,stroke-width:2px
    style node5 fill:#F5DEB3,stroke:#333,stroke-width:2px
    style node6 fill:#90EE90,stroke:#333,stroke-width:2px
```

## Example 4: Container/Subprocess

### Exported Mermaid
```mermaid
---
title: Order Processing
description: E-commerce order processing with subprocesses
---

flowchart LR
    node0["New Order"]
    node1[["Validate Order"]]
    node2[["Process Payment"]]
    node3[["Ship Order"]]
    node4["Order Complete"]
    
    node0 --> node1
    node1 --> node2
    node2 --> node3
    node3 --> node4
    
    style node0 fill:#90EE90,stroke:#333,stroke-width:2px
    style node1 fill:#FFFFE0,stroke:#333,stroke-width:2px
    style node2 fill:#FFFFE0,stroke:#333,stroke-width:2px
    style node3 fill:#FFFFE0,stroke:#333,stroke-width:2px
    style node4 fill:#90EE90,stroke:#333,stroke-width:2px
```

## Visual Guide: Element Shapes

### Rectangles `[...]` - Standard Process Steps
```mermaid
flowchart LR
    A["Process Step"]
    B["Another Step"]
    A --> B
```

### Diamonds `{...}` - Decisions
```mermaid
flowchart LR
    A{"Decision?"}
    B["Option A"]
    C["Option B"]
    A -->|Yes| B
    A -->|No| C
```

### Stadiums `([...])` - Start/End Events
```mermaid
flowchart LR
    A(["Start"])
    B["Process"]
    C(["End"])
    A --> B --> C
```

### Subprocesses `[[...]]` - Containers
```mermaid
flowchart LR
    A[["Subprocess 1"]]
    B[["Subprocess 2"]]
    A --> B
```

## Color Scheme

| Element Type | Color | Hex Code | Usage |
|-------------|-------|----------|-------|
| Events | Light Green | #90EE90 | Start/End events |
| Processes | Light Blue | #ADD8E6 | Standard tasks |
| Decisions | Wheat | #F5DEB3 | Decision points |
| Containers | Light Yellow | #FFFFE0 | Subprocesses |
| Error | Light Red | #FFB6C1 | Error states |

## Integration Examples

### GitHub README.md
````markdown
# Project Documentation

## Process Overview

```mermaid
flowchart LR
    Start["Start"] --> Review["Review"] --> End["End"]
```
````

### GitLab Wiki
Same as GitHub - native Mermaid support

### MkDocs
Add to `mkdocs.yml`:
```yaml
markdown_extensions:
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
```

### VS Code
1. Install "Markdown Preview Mermaid Support" extension
2. Open markdown file
3. Use preview (Ctrl+Shift+V)

### Online Editor
Visit [mermaid.live](https://mermaid.live/) and paste the code

## Tips and Tricks

### 1. Long Labels
Use line breaks with `<br>`:
```mermaid
flowchart LR
    A["Step 1:<br>Very Long<br>Description"]
```

### 2. Custom Styling
Add custom styles:
```mermaid
flowchart LR
    A["Important"]:::highlight
    B["Normal"]
    A --> B
    classDef highlight fill:#f9f,stroke:#333,stroke-width:4px
```

### 3. Subgraphs
Group related nodes:
```mermaid
flowchart TB
    subgraph "Department A"
        A1["Task 1"]
        A2["Task 2"]
    end
    subgraph "Department B"
        B1["Task 3"]
    end
    A2 --> B1
```

### 4. Comments
Use `%%` for comments:
```mermaid
flowchart LR
    %% This is a comment
    A --> B
```

## Conversion to Images

Use mermaid-cli for image export:

```bash
# Install
npm install -g @mermaid-js/mermaid-cli

# Convert to PNG
mmdc -i process.md -o process.png

# Convert to SVG (vector)
mmdc -i process.md -o process.svg

# Convert to PDF
mmdc -i process.md -o process.pdf

# With custom theme
mmdc -i process.md -o process.png -t dark

# With custom background
mmdc -i process.md -o process.png -b transparent
```

## Best Practices

1. **Keep It Simple**
   - Limit to 10-15 nodes per diagram
   - Break complex processes into multiple diagrams

2. **Use Clear Names**
   - Short, descriptive labels
   - Avoid technical jargon when possible

3. **Consistent Direction**
   - LR for wide processes
   - TB for hierarchical processes
   - Stick to one direction per diagram

4. **Color Consistency**
   - Use colors consistently across diagrams
   - Match VPB color scheme for familiarity

5. **Version Control**
   - Commit `.md` files, not rendered images
   - Easy to see changes in git diff
   - Team can edit without special tools

## Troubleshooting

### Diagram Not Rendering
- Check syntax (proper arrows `-->`, braces, etc.)
- Ensure platform supports Mermaid
- Try copying to mermaid.live for validation

### Labels Overlapping
- Shorten labels
- Change diagram direction
- Use line breaks `<br>`

### Complex Layouts
- Break into multiple diagrams
- Use subgraphs for organization
- Consider using TB direction

## Further Reading

- [Official Mermaid Documentation](https://mermaid.js.org/)
- [Mermaid Flowchart Syntax](https://mermaid.js.org/syntax/flowchart.html)
- [GitHub Mermaid Support](https://github.blog/2022-02-14-include-diagrams-markdown-files-mermaid/)
- [VPB Mermaid Export Documentation](MERMAID_EXPORT.md)

---

**Generated by VPB Process Designer**  
**Version:** 0.5.0  
**Date:** 2025-12-31
