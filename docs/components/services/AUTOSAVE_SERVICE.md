# AutoSave Service Documentation

**Version:** 1.1.0  
**Component:** `vpb/services/autosave_service.py`  
**Last Updated:** 2025-11-17

---

## Overview

The AutoSave Service provides automatic, timer-based saving of VPB projects at configurable intervals. It only saves when changes are detected, preventing unnecessary file writes.

**Key Features:**
- Timer-based automatic saving
- Change detection (only saves if modified)
- Configurable save intervals
- Background thread operation
- Start/stop control
- Callback-based integration

**File:** `vpb/services/autosave_service.py` (130 lines)

---

## Configuration

### Default Settings

```python
interval_seconds = 300      # 5 minutes
enabled = True              # Auto-save enabled by default
```

### Custom Configuration

```python
from vpb.services.autosave_service import AutoSaveService

# Create with custom interval
autosave = AutoSaveService(
    interval_seconds=180,   # 3 minutes
    enabled=True
)
```

---

## Usage

### Basic Setup

```python
from vpb.services.autosave_service import AutoSaveService

# 1. Create service
autosave_service = AutoSaveService(interval_seconds=300)

# 2. Set save callback
def save_project():
    """Called when auto-save triggers"""
    # Your save logic here
    document.save()
    print("Project auto-saved")

autosave_service.set_save_callback(save_project)

# 3. Set modification check callback
def is_modified():
    """Returns True if project has unsaved changes"""
    return document.is_modified()

autosave_service.set_is_modified_callback(is_modified)

# 4. Start auto-save
autosave_service.start()
```

### Integration with VPB Application

```python
class VPBApplication:
    def __init__(self):
        # Initialize auto-save service
        self.autosave_service = AutoSaveService(
            interval_seconds=300,  # 5 minutes
            enabled=True
        )
        
        # Connect to document save
        self.autosave_service.set_save_callback(self.save_current_document)
        self.autosave_service.set_is_modified_callback(
            lambda: self.current_document.is_modified()
        )
        
        # Start on application startup
        self.autosave_service.start()
    
    def save_current_document(self):
        """Auto-save callback"""
        if self.current_document:
            self.current_document.save()
            self.status_bar.show_message("Auto-saved", 2000)
```

---

## API Reference

### Constructor

```python
AutoSaveService(interval_seconds=300, enabled=True)
```

**Parameters:**
- `interval_seconds` (int): Save interval in seconds (default: 300 = 5 minutes)
- `enabled` (bool): Whether auto-save is enabled (default: True)

**Example:**
```python
# 3-minute intervals
autosave = AutoSaveService(interval_seconds=180)

# 10-minute intervals, disabled by default
autosave = AutoSaveService(interval_seconds=600, enabled=False)
```

---

### Methods

#### `set_save_callback(callback: Callable) -> None`

Sets the function to call when auto-save triggers.

**Parameters:**
- `callback`: Function with no parameters that performs the save operation

**Example:**
```python
def my_save_function():
    document.save()
    print("Saved!")

autosave.set_save_callback(my_save_function)
```

---

#### `set_is_modified_callback(callback: Callable) -> None`

Sets the function to check if there are unsaved changes.

**Parameters:**
- `callback`: Function that returns `True` if there are unsaved changes

**Example:**
```python
def check_modified():
    return document.has_unsaved_changes()

autosave.set_is_modified_callback(check_modified)
```

---

#### `start() -> None`

Starts the auto-save timer.

**Behavior:**
- Does nothing if `enabled=False`
- Does nothing if already running
- Schedules first save after `interval_seconds`

**Example:**
```python
autosave.start()
# Output: ✅ Auto-Save gestartet (Intervall: 300s)
```

---

#### `stop() -> None`

Stops the auto-save timer.

**Behavior:**
- Cancels any pending save
- Clears the timer
- Can be restarted with `start()`

**Example:**
```python
autosave.stop()
# Output: ⏸️ Auto-Save gestoppt
```

---

#### `enable() -> None`

Enables auto-save and starts the timer.

**Example:**
```python
autosave.enable()
# Auto-save is now enabled and running
```

---

#### `disable() -> None`

Disables auto-save and stops the timer.

**Example:**
```python
autosave.disable()
# Auto-save is now disabled
```

---

#### `set_interval(seconds: int) -> None`

Changes the save interval.

**Parameters:**
- `seconds` (int): New interval in seconds

**Behavior:**
- Stops current timer
- Updates interval
- Restarts timer if was running

**Example:**
```python
# Change to 10 minutes
autosave.set_interval(600)
```

---

## Auto-Save Workflow

### Timer-Based Execution

```
Application Start
       ↓
  Start Timer
       ↓
  Wait (interval_seconds)
       ↓
  Check: is_modified()?
       ↓
   Yes → Call save_callback()
   No  → Skip save
       ↓
  Schedule Next Save
       ↓
  (Repeat)
```

### Modification Detection

The service only saves if `is_modified_callback()` returns `True`:

```python
def _auto_save():
    """Internal auto-save logic"""
    if not self.is_modified_callback:
        print("⚠️ No modification check callback set")
        return
    
    if not self.is_modified_callback():
        print("ℹ️ No changes - skipping auto-save")
        return
    
    if not self.save_callback:
        print("⚠️ No save callback set")
        return
    
    # Perform save
    self.save_callback()
    print("✅ Auto-saved")
```

---

## Best Practices

### 1. Always Set Both Callbacks

```python
# ✅ GOOD - Both callbacks set
autosave.set_save_callback(save_document)
autosave.set_is_modified_callback(check_modified)
autosave.start()

# ❌ BAD - Missing modification check
autosave.set_save_callback(save_document)
autosave.start()  # Will try to save every interval
```

### 2. Choose Appropriate Interval

```python
# For active editing (frequent changes)
autosave = AutoSaveService(interval_seconds=120)  # 2 minutes

# For normal work
autosave = AutoSaveService(interval_seconds=300)  # 5 minutes (default)

# For large files (slow saves)
autosave = AutoSaveService(interval_seconds=600)  # 10 minutes
```

### 3. Handle Save Errors

```python
def safe_save():
    """Save with error handling"""
    try:
        document.save()
        status_bar.show_message("Auto-saved", 2000)
    except Exception as e:
        logger.error(f"Auto-save failed: {e}")
        status_bar.show_error(f"Auto-save failed: {e}")

autosave.set_save_callback(safe_save)
```

### 4. Stop on Application Exit

```python
class Application:
    def close(self):
        """Clean shutdown"""
        # Stop auto-save
        self.autosave_service.stop()
        
        # Perform final save if needed
        if self.document.is_modified():
            self.document.save()
        
        # Continue shutdown...
```

---

## User Preferences

### Saving User Configuration

```python
import json

class Settings:
    def __init__(self):
        self.autosave_enabled = True
        self.autosave_interval = 300
    
    def load(self):
        """Load from config file"""
        try:
            with open('settings.json', 'r') as f:
                data = json.load(f)
                self.autosave_enabled = data.get('autosave_enabled', True)
                self.autosave_interval = data.get('autosave_interval', 300)
        except:
            pass  # Use defaults
    
    def save(self):
        """Save to config file"""
        with open('settings.json', 'w') as f:
            json.dump({
                'autosave_enabled': self.autosave_enabled,
                'autosave_interval': self.autosave_interval
            }, f)

# Apply settings to autosave
settings = Settings()
settings.load()

autosave = AutoSaveService(
    interval_seconds=settings.autosave_interval,
    enabled=settings.autosave_enabled
)
```

---

## Troubleshooting

### Auto-Save Not Working

**Symptom:** Timer started but no saves happening

**Causes:**
1. `is_modified_callback` not set
2. `is_modified_callback` always returns False
3. `save_callback` not set
4. `enabled=False`

**Solutions:**
```python
# Check callbacks are set
if not autosave.save_callback:
    print("ERROR: Save callback not set!")

if not autosave.is_modified_callback:
    print("ERROR: Modification check callback not set!")

# Check enabled status
if not autosave.enabled:
    autosave.enable()

# Test modification detection
print(f"Modified: {autosave.is_modified_callback()}")
```

### Timer Not Stopping

**Symptom:** Auto-save continues after calling `stop()`

**Cause:** Multiple service instances

**Solution:**
```python
# Use single instance
class Application:
    def __init__(self):
        # Create once
        self.autosave = AutoSaveService()
    
    # Don't create new instances!
```

---

## Performance Considerations

### Memory Usage

- **Low:** Single timer thread
- **Negligible:** ~1KB RAM overhead

### CPU Usage

- **Idle:** No CPU when waiting
- **Active:** Minimal CPU during check/save

### Disk I/O

- **Depends on:** File size and save frequency
- **Optimization:** Only saves when modified

**Recommended Intervals:**
- Small files (<1MB): 120-300 seconds
- Medium files (1-10MB): 300-600 seconds
- Large files (>10MB): 600+ seconds

---

## Related Services

- [BackupService](BACKUP_SERVICE.md) - Creates backup copies
- [DocumentService](../../PHASE_3_DOCUMENTSERVICE_COMPLETE.md) - Document management
- [RecentFilesService](RECENT_FILES_SERVICE.md) - Recent files tracking

---

## Testing

### Unit Test Example

```python
import unittest
from vpb.services.autosave_service import AutoSaveService
import time

class TestAutoSaveService(unittest.TestCase):
    def test_autosave_trigger(self):
        """Test that auto-save triggers after interval"""
        saved = []
        
        autosave = AutoSaveService(interval_seconds=1, enabled=True)
        autosave.set_save_callback(lambda: saved.append(1))
        autosave.set_is_modified_callback(lambda: True)
        
        autosave.start()
        time.sleep(1.5)  # Wait for trigger
        
        self.assertGreater(len(saved), 0, "Auto-save should have triggered")
        
        autosave.stop()
```

---

**Last Updated:** 2025-11-17  
**Version:** 1.1.0  
**Status:** ✅ Production Ready
