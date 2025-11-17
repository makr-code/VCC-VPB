# Auto-Fix Strategies - Migration Tool Documentation

**Version:** 1.1.0  
**Component:** `migration/auto_fix.py`  
**Last Updated:** 2025-11-17

---

## Overview

The Auto-Fix Engine automatically corrects data gaps detected during SQLite to UDS3 migration. It provides 5 fix strategies to handle different gap types, with support for dry-run mode, user confirmation, and rollback.

**Key Features:**
- Automatic gap detection and correction
- 5 distinct fix strategies
- Dry-run mode for safe testing
- User confirmation for critical changes
- Backup before fixes
- Rollback support on failure

---

## Fix Strategies

### 1. COPY_FROM_SOURCE

**Purpose:** Copy missing records from SQLite to UDS3

**When Used:**
- Gap Type: `MISSING_RECORD`
- Scenario: Record exists in SQLite but not in UDS3
- Action: Copy complete record from source to target

**Example:**
```python
# Process exists in SQLite but missing in PostgreSQL/Neo4j/ChromaDB
Gap: process_id="abc-123" exists in SQLite, missing in UDS3
Strategy: COPY_FROM_SOURCE
Action: Copy process "abc-123" to PostgreSQL → Neo4j → ChromaDB
```

**Implementation:**
```python
def _execute_copy_from_source(self, action: FixAction) -> bool:
    """Copy record from SQLite to UDS3 backends"""
    gap = action.gap
    process_id = gap.record_id
    
    # 1. Load from SQLite
    source_data = self.sqlite_db.get_process(process_id)
    
    # 2. Copy to UDS3 (with SAGA)
    success = self.uds3_manager.save_process(
        process_data=source_data,
        domain="vpb"
    )
    
    return success
```

**Requires Confirmation:** Yes (creates new data)

---

### 2. DELETE_FROM_TARGET

**Purpose:** Delete orphaned records from UDS3

**When Used:**
- Gap Type: `ORPHANED_RECORD`
- Scenario: Record exists in UDS3 but not in SQLite (source of truth)
- Action: Delete record from UDS3 backends

**Example:**
```python
# Process exists in UDS3 but not in SQLite (was deleted from source)
Gap: process_id="xyz-789" exists in UDS3, missing in SQLite
Strategy: DELETE_FROM_TARGET
Action: Delete process "xyz-789" from PostgreSQL → Neo4j → ChromaDB
```

**Implementation:**
```python
def _execute_delete_from_target(self, action: FixAction) -> bool:
    """Delete orphaned record from UDS3"""
    gap = action.gap
    process_id = gap.record_id
    
    # Backup before delete
    action.backup_data = self.uds3_manager.get_process(process_id)
    
    # Delete from UDS3 (with SAGA)
    success = self.uds3_manager.delete_process(
        process_id=process_id,
        hard_delete=False  # Soft delete by default
    )
    
    return success
```

**Requires Confirmation:** Yes (deletes data)

---

### 3. UPDATE_TARGET

**Purpose:** Update incomplete UDS3 records with complete SQLite data

**When Used:**
- Gap Type: `INCOMPLETE_MIGRATION`
- Scenario: Record partially migrated (some fields missing)
- Action: Update UDS3 with complete data from SQLite

**Example:**
```python
# Process migrated but missing fields
Gap: process_id="def-456" has incomplete data in UDS3
  SQLite: {name, description, elements, connections, metadata}
  UDS3:   {name, description} # Missing elements, connections, metadata
Strategy: UPDATE_TARGET
Action: Update process "def-456" with complete data
```

**Implementation:**
```python
def _execute_update_target(self, action: FixAction) -> bool:
    """Update UDS3 with complete SQLite data"""
    gap = action.gap
    process_id = gap.record_id
    
    # 1. Load complete data from SQLite
    source_data = self.sqlite_db.get_process(process_id)
    
    # 2. Backup current UDS3 data
    action.backup_data = self.uds3_manager.get_process(process_id)
    
    # 3. Update UDS3 (with SAGA)
    success = self.uds3_manager.update_process(
        process_id=process_id,
        process_data=source_data
    )
    
    return success
```

**Requires Confirmation:** No (safe update)

---

### 4. MERGE_DATA

**Purpose:** Merge conflicting versions from SQLite and UDS3

**When Used:**
- Gap Type: `VERSION_CONFLICT`
- Scenario: Both SQLite and UDS3 have different versions
- Action: Merge both versions, keeping newer data

**Example:**
```python
# Process modified in both SQLite and UDS3
Gap: process_id="ghi-012" has version conflict
  SQLite: {name: "Process A", updated_at: "2025-11-17 10:00"}
  UDS3:   {name: "Process B", updated_at: "2025-11-17 09:00"}
Strategy: MERGE_DATA
Action: Keep newer version from SQLite, merge metadata
```

**Implementation:**
```python
def _execute_merge_data(self, action: FixAction) -> bool:
    """Merge SQLite and UDS3 data (newer wins)"""
    gap = action.gap
    process_id = gap.record_id
    
    # 1. Load both versions
    source_data = self.sqlite_db.get_process(process_id)
    target_data = self.uds3_manager.get_process(process_id)
    
    # 2. Backup current UDS3 data
    action.backup_data = target_data
    
    # 3. Merge: newer version wins, combine metadata
    merged_data = self._merge_process_data(source_data, target_data)
    
    # 4. Update UDS3 (with SAGA)
    success = self.uds3_manager.update_process(
        process_id=process_id,
        process_data=merged_data
    )
    
    return success

def _merge_process_data(self, source: Dict, target: Dict) -> Dict:
    """Merge two process versions"""
    # Compare timestamps
    source_time = source.get('updated_at', source.get('created_at'))
    target_time = target.get('updated_at', target.get('created_at'))
    
    # Newer version wins for most fields
    if source_time >= target_time:
        base = source.copy()
        # Merge metadata/tags from both
        base['metadata'] = {**target.get('metadata', {}), **source.get('metadata', {})}
    else:
        base = target.copy()
        base['metadata'] = {**source.get('metadata', {}), **target.get('metadata', {})}
    
    return base
```

**Requires Confirmation:** Yes (modifies data)

---

### 5. SKIP

**Purpose:** Skip gaps that require manual intervention

**When Used:**
- Gap Type: Any unhandled type or complex scenario
- Scenario: Gap cannot be auto-fixed safely
- Action: Log gap, require manual fix

**Example:**
```python
# Complex data inconsistency
Gap: process_id="jkl-345" has complex schema mismatch
Strategy: SKIP
Action: Log gap for manual review
```

**Implementation:**
```python
def _execute_skip(self, action: FixAction) -> bool:
    """Skip gap - log for manual fix"""
    gap = action.gap
    
    logger.warning(f"Gap {gap.gap_id} skipped (manual fix required)")
    logger.warning(f"  Type: {gap.gap_type}")
    logger.warning(f"  Record: {gap.record_id}")
    logger.warning(f"  Details: {gap.details}")
    
    action.status = FixStatus.SKIPPED
    return True  # Skipping is "successful"
```

**Requires Confirmation:** No (no changes made)

---

## Strategy Selection Algorithm

The Auto-Fix Engine automatically selects the optimal strategy based on gap type:

```python
def select_fix_strategy(gap: DataGap) -> FixStrategy:
    """Select optimal fix strategy for gap"""
    
    if gap.gap_type == GapType.MISSING_RECORD:
        # Record missing in UDS3 → Copy from SQLite
        return FixStrategy.COPY_FROM_SOURCE
        
    elif gap.gap_type == GapType.ORPHANED_RECORD:
        # Record orphaned in UDS3 → Delete
        return FixStrategy.DELETE_FROM_TARGET
        
    elif gap.gap_type == GapType.INCOMPLETE_MIGRATION:
        # Partial migration → Update with complete data
        return FixStrategy.UPDATE_TARGET
        
    elif gap.gap_type == GapType.VERSION_CONFLICT:
        # Version conflict → Merge
        return FixStrategy.MERGE_DATA
        
    else:
        # Unknown/complex → Skip (manual fix)
        return FixStrategy.SKIP
```

---

## Fix Workflow

### 1. Detection Phase
```python
# Detect gaps
detector = GapDetector(sqlite_db, uds3_manager)
gaps = detector.detect_all_gaps()

# Analyze gaps
auto_fixable = [g for g in gaps if g.auto_fixable]
manual_required = [g for g in gaps if not g.auto_fixable]
```

### 2. Strategy Selection
```python
# Create fix actions
fixer = AutoFixer(sqlite_db, uds3_manager)
actions = []

for gap in auto_fixable:
    action = fixer.create_fix_action(gap)
    actions.append(action)
```

### 3. User Confirmation
```python
# Show fix plan
print(f"Total gaps: {len(gaps)}")
print(f"Auto-fixable: {len(auto_fixable)}")
print(f"Manual required: {len(manual_required)}")
print("\nFix Plan:")

for action in actions:
    print(f"  [{action.strategy.value}] {action.description}")
    
# Request confirmation
if input("Proceed with fixes? (yes/no): ").lower() != 'yes':
    print("Aborted")
    return
```

### 4. Execution (with Backup)
```python
# Execute fixes
report = fixer.execute_fixes(
    actions=actions,
    dry_run=False,  # Set True for testing
    require_confirmation=True
)

print(f"\nFixed: {report.fixed}")
print(f"Failed: {report.failed}")
print(f"Skipped: {report.skipped}")
```

### 5. Rollback on Failure
```python
# Automatic rollback if any step fails
for action in failed_actions:
    if action.backup_data:
        # Restore from backup
        fixer.rollback_fix(action)
        print(f"Rolled back: {action.gap.record_id}")
```

---

## Usage Examples

### Example 1: Dry Run (Safe Testing)

```bash
# Run auto-fix in dry-run mode (no changes made)
python -m migration.auto_fix \
  --source sqlite:///data/vpb.db \
  --dry-run \
  --verbose
```

**Output:**
```
Detecting gaps...
Found 25 gaps
  - 10 MISSING_RECORD (auto-fixable)
  - 3 ORPHANED_RECORD (auto-fixable)
  - 5 INCOMPLETE_MIGRATION (auto-fixable)
  - 2 VERSION_CONFLICT (auto-fixable)
  - 5 OTHER (manual required)

Fix Plan (DRY RUN):
  [copy_from_source] Copy process abc-123 to UDS3
  [copy_from_source] Copy process def-456 to UDS3
  [delete_from_target] Delete orphaned process xyz-789
  [update_target] Update incomplete process ghi-012
  [merge_data] Merge conflicting process jkl-345

DRY RUN - No changes made
```

### Example 2: Auto-Fix with Confirmation

```python
from migration.auto_fix import AutoFixer
from migration.gap_detector import GapDetector

# Initialize
detector = GapDetector(sqlite_db, uds3_manager)
fixer = AutoFixer(sqlite_db, uds3_manager)

# Detect and fix
gaps = detector.detect_all_gaps()
actions = [fixer.create_fix_action(g) for g in gaps if g.auto_fixable]

# Execute with confirmation
report = fixer.execute_fixes(
    actions=actions,
    dry_run=False,
    require_confirmation=True
)

# Print report
print(f"Total: {report.total_gaps}")
print(f"Fixed: {report.fixed}")
print(f"Failed: {report.failed}")

# Save report
with open('fix_report.json', 'w') as f:
    json.dump(report.to_dict(), f, indent=2)
```

### Example 3: Batch Fix (No Confirmation)

```python
# Fix all auto-fixable gaps without confirmation
# USE WITH CAUTION!
report = fixer.execute_fixes(
    actions=actions,
    dry_run=False,
    require_confirmation=False  # Automatic fixes
)
```

---

## Fix Reports

Each fix generates a comprehensive report:

```json
{
  "total_gaps": 25,
  "auto_fixable": 20,
  "fixed": 18,
  "failed": 2,
  "skipped": 5,
  "rolled_back": 1,
  "started_at": "2025-11-17T06:30:00Z",
  "completed_at": "2025-11-17T06:35:00Z",
  "duration_seconds": 300.5,
  "dry_run": false,
  "actions": [
    {
      "gap": {
        "gap_id": "gap-001",
        "gap_type": "MISSING_RECORD",
        "record_id": "abc-123",
        "severity": "high"
      },
      "strategy": "copy_from_source",
      "description": "Copy process abc-123 to UDS3",
      "status": "success",
      "executed_at": "2025-11-17T06:30:15Z"
    }
  ]
}
```

---

## Error Handling

### Rollback on Failure

```python
# Automatic rollback
try:
    success = fixer._execute_copy_from_source(action)
    if not success:
        raise Exception("Copy failed")
except Exception as e:
    # Rollback
    if action.backup_data:
        fixer.rollback_fix(action)
    action.status = FixStatus.ROLLED_BACK
    action.error = str(e)
```

### Partial Success Handling

```python
# Some fixes succeed, some fail
if report.failed > 0:
    print(f"WARNING: {report.failed} fixes failed")
    print("Failed actions:")
    for action in report.actions:
        if action.status == FixStatus.FAILED:
            print(f"  - {action.gap.record_id}: {action.error}")
```

---

## Best Practices

### 1. Always Dry Run First
```bash
# Test fixes before applying
python -m migration.auto_fix --dry-run
```

### 2. Backup Before Fixes
```python
# Automatic backup
fixer.create_backup()  # Called automatically before fixes
```

### 3. Review Fix Plan
```python
# Review before confirmation
for action in actions:
    if action.requires_confirmation:
        print(f"REVIEW: {action.description}")
```

### 4. Monitor Fix Progress
```python
# Enable verbose logging
logging.basicConfig(level=logging.INFO)
fixer.execute_fixes(actions, verbose=True)
```

### 5. Save Fix Reports
```python
# Always save reports for audit trail
report.save_to_file(f"fix_report_{datetime.now():%Y%m%d_%H%M%S}.json")
```

---

## Configuration

Configure auto-fix behavior in `migration_config.py`:

```python
AUTO_FIX_CONFIG = {
    'require_confirmation': True,  # Ask before fixing
    'backup_enabled': True,         # Backup before fixes
    'dry_run_default': False,       # Default mode
    'max_retries': 3,               # Retry failed fixes
    'rollback_on_failure': True,    # Auto-rollback
    'log_level': 'INFO'             # Logging verbosity
}
```

---

## Related Documentation

- [Gap Detection](GAP_DETECTION.md) - How gaps are detected
- [Migration Guide](MIGRATION_GUIDE.md) - Complete migration workflow
- [Migration UI](MIGRATION_UI_GUIDE.md) - Using the GUI wizard

---

**Last Updated:** 2025-11-17  
**Version:** 1.1.0  
**Status:** ✅ Production Ready
