# VPB Models

Data models for VPB Process Designer.

## Overview

This package contains the core data structures and business entities:

- **DocumentModel**: Complete process document with metadata, elements, and connections
- **VPBElement**: Individual process elements (VorProzess, Prozess, etc.)
- **VPBConnection**: Connections/arrows between elements  
- **PaletteModel**: Element palette definitions

## Architecture

Models follow these principles:

- **No Business Logic**: Pure data structures
- **Immutability**: Use dataclasses with frozen=True where appropriate
- **Validation**: Input validation in setters/constructors
- **Serialization**: to_dict() and from_dict() for persistence
- **Observer Pattern**: Notify observers when data changes

## Usage

```python
from vpb.models import DocumentModel, VPBElement

# Create document
doc = DocumentModel()

# Add element
element = VPBElement(
    element_type="Prozess",
    x=100, y=100,
    width=120, height=60,
    label="Example Process"
)
doc.add_element(element)

# Serialize
data = doc.to_dict()
```

## Testing

All models have comprehensive unit tests in `tests/models/`.
