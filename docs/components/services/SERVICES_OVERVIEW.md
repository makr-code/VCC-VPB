# VPB Services Documentation Overview

**Version:** 1.1.0  
**Last Updated:** 2025-11-17

---

## Documented Services

### Core Business Logic (5 services - Fully Documented)

1. **[DocumentService](../../PHASE_3_DOCUMENTSERVICE_COMPLETE.md)** ✅
   - CRUD operations for documents
   - Event-driven architecture
   - File I/O management

2. **[ValidationService](../../PHASE_3_VALIDATIONSERVICE_COMPLETE.md)** ✅
   - Process validation rules
   - Element validation
   - Connection validation

3. **[ExportService](../../PHASE_3_EXPORTSERVICE_COMPLETE.md)** ✅
   - Multiple export formats (JSON, XML, PNG, SVG, PDF, BPMN)
   - Template-based export
   - Format conversion

4. **[LayoutService](../../PHASE_3_LAYOUTSERVICE_COMPLETE.md)** ✅
   - Auto-layout algorithms
   - Grid, hierarchical, circular layouts
   - Manual layout support

5. **[AIService](../../PHASE_3_AISERVICE_COMPLETE.md)** ✅
   - AI-powered process generation
   - Ollama integration
   - Intelligent suggestions

### Supporting Services (4 services - NEW DOCUMENTATION)

6. **[AutosaveService](AUTOSAVE_SERVICE.md)** ✅ NEW
   - **Purpose:** Timer-based automatic saving
   - **Interval:** Configurable (default 5 minutes)
   - **Features:** Change detection, background operation
   - **File:** vpb/services/autosave_service.py (130 lines)

7. **BackupService** ⏳ Coming Soon
   - **Purpose:** Automated backup creation
   - **Features:** Timestamp backups, retention policy, auto-cleanup
   - **File:** vpb/services/backup_service.py (200 lines)
   - **Details:** Creates backups in autosaves/ directory, limits per file

8. **CodeSyncService** ⏳ Coming Soon
   - **Purpose:** Bidirectional Canvas ↔ Code sync
   - **Features:** JSON/XML conversion, real-time sync, conflict detection
   - **File:** vpb/services/code_sync_service.py (400 lines)
   - **Details:** Syncs visual canvas with code editors

9. **RecentFilesService** ⏳ Coming Soon
   - **Purpose:** Recent files tracking
   - **Features:** File history, quick access, persistence
   - **File:** vpb/services/recent_files_service.py (150 lines)
   - **Details:** Manages MRU (Most Recently Used) file list

---

## Service Architecture

### Event-Driven Pattern

All services use the event bus for loose coupling:

```python
# Services publish events
event_bus.publish('document.saved', {'file_path': path})

# Services subscribe to events
event_bus.subscribe('document.opened', self.on_document_opened)
```

### Service Responsibilities

**DocumentService:**
- File operations (load, save, new)
- Document lifecycle management

**ValidationService:**
- Process validation
- Real-time validation feedback

**ExportService:**
- Format conversion
- Export to various formats

**LayoutService:**
- Element positioning
- Auto-layout algorithms

**AIService:**
- AI-powered features
- Process generation

**AutosaveService:**
- Automatic saving
- Change detection

**BackupService:**
- Backup creation
- Backup management

**CodeSyncService:**
- Canvas ↔ Code synchronization
- Format conversion

**RecentFilesService:**
- File history tracking
- Quick file access

---

## Quick Reference

### AutosaveService

```python
from vpb.services.autosave_service import AutoSaveService

# Create and configure
autosave = AutoSaveService(interval_seconds=300)
autosave.set_save_callback(document.save)
autosave.set_is_modified_callback(document.is_modified)
autosave.start()
```

**Key Methods:**
- `start()` - Start auto-save timer
- `stop()` - Stop auto-save timer
- `set_interval(seconds)` - Change interval
- `enable()` / `disable()` - Toggle auto-save

**Configuration:**
- Default interval: 300 seconds (5 minutes)
- Change detection: Only saves if modified
- Background operation: Uses timer thread

---

### BackupService (Summary)

```python
from vpb.services.backup_service import BackupService

# Create backups
backup = BackupService(backup_dir="autosaves", max_backups_per_file=5)
backup_path = backup.create_backup("myfile.vpb.json")
```

**Features:**
- Timestamp-based backup names
- Auto-cleanup of old backups
- Configurable retention (max backups per file)

---

### CodeSyncService (Summary)

```python
from vpb.services.code_sync_service import CodeSyncService

# Sync Canvas → Code
sync = CodeSyncService()
json_code = sync.canvas_to_json(canvas.to_dict())
xml_code = sync.canvas_to_xml(canvas.to_dict())

# Sync Code → Canvas
canvas_data = sync.json_to_canvas(json_code)
```

**Features:**
- Canvas ↔ JSON conversion
- Canvas ↔ XML conversion
- Bidirectional sync
- Validation on import

---

### RecentFilesService (Summary)

```python
from vpb.services.recent_files_service import RecentFilesService

# Track recent files
recent = RecentFilesService(max_files=10)
recent.add_file("/path/to/file.vpb.json")
files = recent.get_recent_files()
```

**Features:**
- MRU (Most Recently Used) tracking
- Persistence across sessions
- Configurable history size

---

## Service Dependencies

```
                    Event Bus
                        ↓
        ┌───────────────┼───────────────┐
        ↓               ↓               ↓
 DocumentService  ValidationService  AIService
        ↓               ↓               ↓
    ┌───┴───┬───────────┴───┬───────────┴────┐
    ↓       ↓               ↓                ↓
Autosave  Backup      ExportService    LayoutService
           ↓                ↓
       CodeSync        RecentFiles
```

---

## Integration Example

### Complete Service Integration

```python
class VPBApplication:
    def __init__(self):
        # Core services
        self.document_service = DocumentService()
        self.validation_service = ValidationService()
        self.export_service = ExportService()
        
        # Supporting services
        self.autosave_service = AutoSaveService(interval_seconds=300)
        self.backup_service = BackupService()
        self.code_sync_service = CodeSyncService()
        self.recent_files_service = RecentFilesService()
        
        # Configure autosave
        self.autosave_service.set_save_callback(self.save_document)
        self.autosave_service.set_is_modified_callback(
            lambda: self.document_service.current_document.is_modified()
        )
        self.autosave_service.start()
        
        # Subscribe to events
        event_bus.subscribe('document.opened', self.on_document_opened)
        event_bus.subscribe('document.saved', self.on_document_saved)
    
    def on_document_opened(self, data):
        """Handle document opened"""
        file_path = data['file_path']
        
        # Add to recent files
        self.recent_files_service.add_file(file_path)
        
        # Create backup
        self.backup_service.create_backup(file_path)
        
        # Sync to code editors
        canvas_data = self.document_service.current_document.to_dict()
        json_code = self.code_sync_service.canvas_to_json(canvas_data)
        self.json_editor.set_text(json_code)
    
    def save_document(self):
        """Save with services"""
        # Validate before save
        errors = self.validation_service.validate_document(
            self.document_service.current_document
        )
        
        if errors:
            show_validation_errors(errors)
            return
        
        # Save document
        self.document_service.save_current_document()
        
        # Create backup
        self.backup_service.create_backup(self.current_file_path)
```

---

## Service Status

### Documentation Status

| Service | Status | Documentation | Lines | Tests |
|---------|--------|--------------|-------|-------|
| DocumentService | ✅ Complete | PHASE_3_DOCUMENTSERVICE_COMPLETE.md | - | Yes |
| ValidationService | ✅ Complete | PHASE_3_VALIDATIONSERVICE_COMPLETE.md | - | Yes |
| ExportService | ✅ Complete | PHASE_3_EXPORTSERVICE_COMPLETE.md | - | Yes |
| LayoutService | ✅ Complete | PHASE_3_LAYOUTSERVICE_COMPLETE.md | - | Yes |
| AIService | ✅ Complete | PHASE_3_AISERVICE_COMPLETE.md | - | Yes |
| **AutosaveService** | ✅ **NEW** | **AUTOSAVE_SERVICE.md** | **505** | Partial |
| BackupService | ⏳ Pending | Summary in overview | - | Partial |
| CodeSyncService | ⏳ Pending | Summary in overview | - | Partial |
| RecentFilesService | ⏳ Pending | Summary in overview | - | Partial |

**Overall Service Documentation:** 6 of 9 complete (67%)

---

## Next Steps

1. Complete BackupService documentation
2. Complete CodeSyncService documentation
3. Complete RecentFilesService documentation
4. Add integration tests for all services
5. Create service architecture diagram

---

**Last Updated:** 2025-11-17  
**Version:** 1.1.0  
**Coverage:** 6/9 services (67%)
