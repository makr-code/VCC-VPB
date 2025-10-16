# VPB Services

Business logic layer for VPB Process Designer.

## Overview

Services contain all business operations:

- **DocumentService**: Load/save documents
- **ExportService**: Export to PDF/SVG/PNG
- **ValidationService**: Validate processes
- **LayoutService**: Auto-layout algorithms
- **AIService**: AI-powered process generation

## Architecture

Services follow these principles:

- **Pure Business Logic**: No UI dependencies
- **Stateless**: Operate on Models passed as parameters
- **Testable**: Can be fully unit tested
- **Reusable**: Can be used from CLI, API, or GUI
- **Error Handling**: Return Result objects or raise exceptions

## Usage

```python
from vpb.services import DocumentService
from vpb.models import DocumentModel

model = DocumentModel()
service = DocumentService()

# Load document
service.load("example.vpb", model)

# Modify model
model.add_element(...)

# Save document
service.save("example.vpb", model)
```

## Service Guidelines

- **Input Validation**: Validate all inputs
- **Error Messages**: Provide clear error messages
- **Logging**: Log operations for debugging
- **Progress Callbacks**: For long operations
- **Transaction Safety**: Atomic operations where possible

## Testing

Services have comprehensive unit tests in `tests/services/`.
