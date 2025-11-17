# Migration UI Guide - VPB SQLite to UDS3 Migration Wizard

**Version:** 1.1.0  
**Component:** `vpb/ui/migration_dialog.py`  
**Last Updated:** 2025-11-17

---

## Overview

The Migration Dialog provides a user-friendly wizard interface for migrating VPB processes from SQLite to UDS3 polyglot backends (PostgreSQL, Neo4j, ChromaDB).

**Features:**
- 3-tab interface (Config, Progress, Results)
- Real-time progress updates
- Auto-fix integration
- Validation during migration
- Comprehensive migration reports
- Export results to JSON

**File:** `vpb/ui/migration_dialog.py` (575 lines)

---

## Accessing the Migration Dialog

### From VPB Application Menu

```
Tools → SQLite to UDS3 Migration
```

Or press: **Ctrl+Shift+M**

### Programmatic Access

```python
from vpb.ui.migration_dialog import MigrationDialog

# Create dialog
dialog = MigrationDialog(
    parent=app_window,
    on_start_callback=handle_migration_start
)

# Show dialog
dialog.mainloop()
```

---

## Tab 1: Configuration

### Source Database

**Field:** SQLite Database Path

**Description:** Path to source SQLite database

**Default:** `data/vpb.db`

**Actions:**
- **Browse...** button to select file
- Validates file exists
- Shows error if file not found

**Example:**
```
/path/to/vpb_processes.db
```

### Target Configuration

**Field:** UDS3 Backend Mode

**Options:**
- **Mock Mode** (Development)
- **Production Mode** (Real backends)

**Mock Mode:**
- Uses in-memory storage
- No real backends required
- Safe for testing

**Production Mode:**
- Requires PostgreSQL, Neo4j, ChromaDB
- Configure via environment variables:
  ```bash
  export UDS3_POSTGRES_HOST=localhost
  export UDS3_NEO4J_URI=bolt://localhost:7687
  export UDS3_CHROMADB_PATH=./data/chromadb
  ```

### Migration Options

**Batch Size:**
- Number of records per batch
- Default: 100
- Range: 1-1000
- Smaller batches: more frequent updates, slower
- Larger batches: fewer updates, faster

**Auto-Fix Gaps:**
- ☑ Enable: Automatically fix detectable gaps
- ☐ Disable: Only detect gaps, manual fix required

**Validate During Migration:**
- ☑ Enable: Validate each record (slower, safer)
- ☐ Disable: Skip validation (faster, risky)

**Example Configuration:**
```
Source: /home/user/data/vpb.db
Mode: Production
Batch Size: 100
Auto-Fix: Enabled
Validate: Enabled
```

### Start Migration Button

**Action:** Validates configuration and starts migration

**Validation Checks:**
1. SQLite file exists
2. UDS3 backends reachable (Production mode)
3. Batch size in valid range

**On Success:** Switches to Progress tab

**On Failure:** Shows error message

---

## Tab 2: Progress

### Real-time Progress Display

**Progress Bar:**
- Shows migration progress (0-100%)
- Updates after each batch
- Color: Blue (in progress), Green (complete)

**Status Label:**
```
Migrating batch 5/10 (50%)...
```

**Records Processed:**
```
Records: 500 / 1000
```

**Time Elapsed:**
```
Time: 00:02:35
```

### Progress Log

**Scrollable Text Area:**
```
[2025-11-17 06:30:00] Migration started
[2025-11-17 06:30:05] Batch 1/10: 100 records migrated
[2025-11-17 06:30:10] Batch 2/10: 100 records migrated
[2025-11-17 06:30:15] Auto-fix: 5 gaps fixed
[2025-11-17 06:30:20] Batch 3/10: 100 records migrated
...
[2025-11-17 06:32:30] Migration completed successfully
[2025-11-17 06:32:30] Total: 1000 records, 25 gaps detected, 20 fixed
```

### Cancel Migration Button

**Action:** Stops migration gracefully

**Behavior:**
- Completes current batch
- Rolls back incomplete operations
- Shows cancellation summary

---

## Tab 3: Results

### Migration Summary

**Statistics:**
```
Total Records: 1000
Successfully Migrated: 975
Failed: 0
Gaps Detected: 25
Gaps Fixed (Auto): 20
Gaps Requiring Manual Fix: 5
Duration: 00:02:35
```

### Gap Report

**Table showing all detected gaps:**

| Gap ID | Type | Record ID | Severity | Status | Action |
|--------|------|-----------|----------|--------|--------|
| gap-001 | MISSING_RECORD | abc-123 | high | Fixed | COPY_FROM_SOURCE |
| gap-002 | ORPHANED_RECORD | xyz-789 | medium | Fixed | DELETE_FROM_TARGET |
| gap-003 | VERSION_CONFLICT | def-456 | medium | Fixed | MERGE_DATA |
| gap-004 | SCHEMA_MISMATCH | ghi-012 | high | Manual | SKIP |
| gap-005 | DATA_CORRUPTION | jkl-345 | critical | Manual | SKIP |

**Color Coding:**
- Green: Fixed automatically
- Yellow: Requires manual fix
- Red: Critical, requires immediate attention

### Detailed Gap Information

**Select gap to view details:**
```
Gap ID: gap-004
Type: SCHEMA_MISMATCH
Record ID: ghi-012
Severity: high
Status: Manual fix required

Description:
  Process schema differs between SQLite and UDS3.
  SQLite has 'old_field', UDS3 expects 'new_field'.
  
Recommendation:
  Manually map 'old_field' → 'new_field' and re-migrate.
  
Source Data:
  {
    "process_id": "ghi-012",
    "old_field": "value",
    ...
  }
  
Target Data:
  {
    "process_id": "ghi-012",
    "new_field": null,
    ...
  }
```

### Export Results

**Export Report Button:**
- Exports complete migration report to JSON
- Includes:
  - Migration statistics
  - All gaps with details
  - Timestamps
  - Configuration used

**Example Export:**
```json
{
  "migration_id": "mig-20251117-063000",
  "started_at": "2025-11-17T06:30:00Z",
  "completed_at": "2025-11-17T06:32:35Z",
  "duration_seconds": 155,
  "config": {
    "source": "/home/user/data/vpb.db",
    "mode": "production",
    "batch_size": 100,
    "auto_fix": true,
    "validate": true
  },
  "summary": {
    "total_records": 1000,
    "migrated": 975,
    "failed": 0,
    "gaps_detected": 25,
    "gaps_fixed": 20,
    "gaps_manual": 5
  },
  "gaps": [...]
}
```

**File Name:** `migration_report_20251117_063000.json`

---

## Workflow Example

### Complete Migration Workflow

**Step 1: Open Migration Dialog**
```
VPB Menu → Tools → SQLite to UDS3 Migration
```

**Step 2: Configure (Tab 1)**
1. Browse for SQLite file: `/data/vpb_processes.db`
2. Select mode: Production
3. Set batch size: 100
4. Enable auto-fix: ☑
5. Enable validation: ☑
6. Click "Start Migration"

**Step 3: Monitor Progress (Tab 2)**
```
Migration started...
Batch 1/10: 100 records [10%] ████░░░░░░
Batch 2/10: 100 records [20%] ████████░░
...
Auto-fix: 20 gaps fixed
...
Batch 10/10: 100 records [100%] ██████████
Migration completed!
```

**Step 4: Review Results (Tab 3)**
1. Check summary statistics
2. Review gap report
3. Click on manual gaps for details
4. Export report for documentation

**Step 5: Fix Manual Gaps (if any)**
1. Note gap IDs requiring manual fix
2. Close dialog
3. Fix gaps manually in VPB or via script
4. Re-run migration for those records

---

## Error Handling

### Connection Errors

**Scenario:** Cannot connect to PostgreSQL

**Display:**
```
ERROR: Failed to connect to PostgreSQL
Host: localhost:5432
Error: Connection refused

Recommendation:
  - Start PostgreSQL service
  - Check connection settings
  - Verify firewall rules
```

**Action:** Fix connection, retry migration

### Validation Errors

**Scenario:** Invalid process schema

**Display:**
```
VALIDATION ERROR: Batch 5/10
Record: abc-123
Error: Missing required field 'name'

Action: Skipped (not migrated)
```

**Action:** Fix source data, retry migration

### Auto-Fix Failures

**Scenario:** Gap cannot be auto-fixed

**Display:**
```
AUTO-FIX FAILED: Gap gap-015
Type: VERSION_CONFLICT
Record: def-456
Error: Cannot determine newer version

Status: Marked for manual fix
```

**Action:** Review in Results tab, fix manually

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+Shift+M | Open migration dialog |
| Ctrl+S | Start migration |
| Ctrl+X | Cancel migration |
| Ctrl+E | Export results |
| Ctrl+W | Close dialog |
| Ctrl+Tab | Next tab |
| Ctrl+Shift+Tab | Previous tab |

---

## Tips & Best Practices

### Before Migration

1. **Backup SQLite database**
   ```bash
   cp vpb.db vpb.db.backup
   ```

2. **Test with mock mode first**
   - Verify migration logic
   - Check for gaps
   - Estimate duration

3. **Start backends (Production mode)**
   ```bash
   # PostgreSQL
   sudo service postgresql start
   
   # Neo4j
   neo4j start
   
   # ChromaDB (auto-started)
   ```

### During Migration

1. **Monitor progress log**
   - Watch for errors
   - Note gap patterns
   - Check batch timing

2. **Don't close application**
   - Migration runs in background
   - Closing cancels migration

3. **Use appropriate batch size**
   - Small datasets (<1000): batch 50-100
   - Medium datasets (1000-10000): batch 100-500
   - Large datasets (>10000): batch 500-1000

### After Migration

1. **Review gap report**
   - Check all manual gaps
   - Understand why gaps occurred
   - Plan fixes

2. **Export results**
   - Save for audit trail
   - Document manual fixes
   - Track migration history

3. **Verify data**
   ```python
   # Check migrated data
   from core.polyglot_manager import create_uds3_manager
   
   manager = create_uds3_manager()
   processes = manager.list_processes()
   print(f"Migrated: {len(processes)} processes")
   ```

---

## Troubleshooting

### Migration Hangs

**Symptom:** Progress bar stuck

**Causes:**
- Large batch size
- Slow network
- Backend timeout

**Solution:**
- Reduce batch size
- Check network connection
- Increase backend timeout settings

### High Gap Count

**Symptom:** Many gaps detected

**Causes:**
- Schema mismatch
- Data corruption
- Incomplete SQLite data

**Solution:**
- Review SQLite schema
- Run data validation
- Fix source data before migration

### Auto-Fix Failures

**Symptom:** Many gaps not auto-fixed

**Causes:**
- Complex gaps (SCHEMA_MISMATCH, DATA_CORRUPTION)
- Ambiguous version conflicts

**Solution:**
- Review gap details
- Fix manually
- Update auto-fix logic if pattern recurring

---

## Related Documentation

- [Auto-Fix Strategies](AUTO_FIX_STRATEGIES.md) - Fix strategy details
- [Gap Detection](GAP_DETECTION.md) - How gaps are detected
- [Migration CLI](MIGRATION_CLI_GUIDE.md) - Command-line migration

---

**Last Updated:** 2025-11-17  
**Version:** 1.1.0  
**Status:** ✅ Production Ready
