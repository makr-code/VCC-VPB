# Gap Detection - Migration Tool Documentation

**Version:** 1.1.0  
**Component:** `migration/gap_detector.py`  
**Last Updated:** 2025-11-17

---

## Overview

The Gap Detector identifies data inconsistencies between SQLite (source) and UDS3 (target) databases during migration. It detects 7 types of gaps and classifies them by severity and auto-fixability.

**Key Features:**
- 7 gap types detection
- Severity classification (low, medium, high, critical)
- Auto-fixability assessment
- Comprehensive gap reports
- Integration with auto-fix engine

**File:** `migration/gap_detector.py` (400+ lines)

---

## Gap Types

### 1. MISSING_RECORD

**Description:** Record exists in SQLite but not in UDS3

**Detection Logic:**
```python
# Compare process IDs
sqlite_ids = get_all_process_ids_from_sqlite()
uds3_ids = get_all_process_ids_from_uds3()

missing = sqlite_ids - uds3_ids  # Set difference
```

**Example:**
```python
Gap {
  gap_type: "MISSING_RECORD",
  record_id: "abc-123",
  description: "Process 'abc-123' exists in SQLite but not in UDS3",
  severity: "high",
  auto_fixable: True  # Can auto-fix with COPY_FROM_SOURCE
}
```

**Severity:** High (data loss risk)  
**Auto-fixable:** Yes (COPY_FROM_SOURCE strategy)

---

### 2. ORPHANED_RECORD

**Description:** Record exists in UDS3 but not in SQLite

**Detection Logic:**
```python
# Compare process IDs (reverse)
sqlite_ids = get_all_process_ids_from_sqlite()
uds3_ids = get_all_process_ids_from_uds3()

orphaned = uds3_ids - sqlite_ids  # Set difference (reverse)
```

**Example:**
```python
Gap {
  gap_type: "ORPHANED_RECORD",
  record_id: "xyz-789",
  description: "Process 'xyz-789' exists in UDS3 but not in SQLite (source)",
  severity: "medium",
  auto_fixable: True  # Can auto-fix with DELETE_FROM_TARGET
}
```

**Severity:** Medium (orphaned data)  
**Auto-fixable:** Yes (DELETE_FROM_TARGET strategy)

---

### 3. SCHEMA_MISMATCH

**Description:** Record schemas differ between SQLite and UDS3

**Detection Logic:**
```python
# Compare schemas
sqlite_schema = get_schema_from_sqlite(record_id)
uds3_schema = get_schema_from_uds3(record_id)

# Check for missing/extra fields
missing_fields = sqlite_schema.keys() - uds3_schema.keys()
extra_fields = uds3_schema.keys() - sqlite_schema.keys()

if missing_fields or extra_fields:
    # Schema mismatch detected
```

**Example:**
```python
Gap {
  gap_type: "SCHEMA_MISMATCH",
  record_id: "def-456",
  description: "Schema mismatch: SQLite has 'old_field', UDS3 expects 'new_field'",
  source_data: {"old_field": "value"},
  target_data: {"new_field": null},
  severity: "high",
  auto_fixable: False  # Requires manual schema mapping
}
```

**Severity:** High (data structure issue)  
**Auto-fixable:** No (SKIP - manual intervention required)

---

### 4. DATA_CORRUPTION

**Description:** Data is corrupted or malformed

**Detection Logic:**
```python
# Validate data integrity
def is_corrupted(data):
    # Check for null required fields
    if not data.get('name'):
        return True
    
    # Check for invalid JSON
    try:
        json.loads(data.get('process_data', '{}'))
    except:
        return True
    
    # Check for invalid UUIDs
    if not is_valid_uuid(data.get('process_id')):
        return True
    
    return False
```

**Example:**
```python
Gap {
  gap_type: "DATA_CORRUPTION",
  record_id: "ghi-012",
  description: "Process data is malformed (invalid JSON in process_data field)",
  severity: "critical",
  auto_fixable: False  # Requires manual data repair
}
```

**Severity:** Critical (data integrity issue)  
**Auto-fixable:** No (SKIP - manual data repair required)

---

### 5. INTEGRITY_VIOLATION

**Description:** Foreign key or referential integrity violations

**Detection Logic:**
```python
# Check foreign key constraints
def check_integrity(process):
    # Check if referenced elements exist
    for element_id in process.get('element_ids', []):
        if not element_exists(element_id):
            return IntegrityViolation(
                type="missing_element",
                record_id=process['process_id'],
                referenced_id=element_id
            )
    
    # Check if referenced connections exist
    for conn_id in process.get('connection_ids', []):
        if not connection_exists(conn_id):
            return IntegrityViolation(
                type="missing_connection",
                record_id=process['process_id'],
                referenced_id=conn_id
            )
```

**Example:**
```python
Gap {
  gap_type: "INTEGRITY_VIOLATION",
  record_id: "jkl-345",
  description: "Process references element 'elem-999' which does not exist",
  severity: "high",
  auto_fixable: False  # Requires manual resolution
}
```

**Severity:** High (referential integrity issue)  
**Auto-fixable:** No (SKIP - manual resolution required)

---

### 6. INCOMPLETE_MIGRATION

**Description:** Record partially migrated (some fields missing)

**Detection Logic:**
```python
# Compare field completeness
sqlite_data = get_from_sqlite(record_id)
uds3_data = get_from_uds3(record_id)

missing_fields = []
for field in sqlite_data.keys():
    if field not in uds3_data or uds3_data[field] is None:
        missing_fields.append(field)

if missing_fields:
    # Incomplete migration detected
```

**Example:**
```python
Gap {
  gap_type: "INCOMPLETE_MIGRATION",
  record_id: "mno-678",
  description: "Process missing fields: elements, connections, metadata",
  source_data: {
    "process_id": "mno-678",
    "name": "Test",
    "elements": [...],
    "connections": [...],
    "metadata": {...}
  },
  target_data: {
    "process_id": "mno-678",
    "name": "Test"
    # Missing: elements, connections, metadata
  },
  severity: "medium",
  auto_fixable: True  # Can auto-fix with UPDATE_TARGET
}
```

**Severity:** Medium (partial data loss)  
**Auto-fixable:** Yes (UPDATE_TARGET strategy)

---

### 7. VERSION_CONFLICT

**Description:** Different versions exist in SQLite and UDS3

**Detection Logic:**
```python
# Compare timestamps and versions
sqlite_data = get_from_sqlite(record_id)
uds3_data = get_from_uds3(record_id)

sqlite_updated = sqlite_data.get('updated_at')
uds3_updated = uds3_data.get('updated_at')

if sqlite_updated != uds3_updated:
    # Check if data differs
    if data_differs(sqlite_data, uds3_data):
        # Version conflict detected
```

**Example:**
```python
Gap {
  gap_type: "VERSION_CONFLICT",
  record_id: "pqr-901",
  description: "Conflicting versions: SQLite updated 2025-11-17 10:00, UDS3 updated 2025-11-17 09:00",
  source_data: {
    "name": "Process A",
    "updated_at": "2025-11-17T10:00:00Z"
  },
  target_data: {
    "name": "Process B",
    "updated_at": "2025-11-17T09:00:00Z"
  },
  severity: "medium",
  auto_fixable: True  # Can auto-fix with MERGE_DATA
}
```

**Severity:** Medium (sync issue)  
**Auto-fixable:** Yes (MERGE_DATA strategy)

---

## Detection Algorithm

### Complete Detection Workflow

```python
def detect_all_gaps() -> List[DataGap]:
    """Comprehensive gap detection"""
    gaps = []
    
    # 1. Missing Records
    gaps.extend(detect_missing_records())
    
    # 2. Orphaned Records
    gaps.extend(detect_orphaned_records())
    
    # 3. Schema Mismatches
    gaps.extend(detect_schema_mismatches())
    
    # 4. Data Corruption
    gaps.extend(detect_data_corruption())
    
    # 5. Integrity Violations
    gaps.extend(detect_integrity_violations())
    
    # 6. Incomplete Migrations
    gaps.extend(detect_incomplete_migrations())
    
    # 7. Version Conflicts (for common records)
    common_ids = sqlite_ids & uds3_ids
    for record_id in common_ids:
        gap = detect_version_conflict(record_id)
        if gap:
            gaps.append(gap)
    
    return gaps
```

### Severity Classification

```python
def classify_severity(gap: DataGap) -> str:
    """Classify gap severity"""
    
    # Critical: Data corruption or integrity violations
    if gap.gap_type in [GapType.DATA_CORRUPTION, GapType.INTEGRITY_VIOLATION]:
        return "critical"
    
    # High: Missing records or schema mismatches
    elif gap.gap_type in [GapType.MISSING_RECORD, GapType.SCHEMA_MISMATCH]:
        return "high"
    
    # Medium: Orphaned, incomplete, or version conflicts
    elif gap.gap_type in [GapType.ORPHANED_RECORD, GapType.INCOMPLETE_MIGRATION, GapType.VERSION_CONFLICT]:
        return "medium"
    
    # Default
    else:
        return "low"
```

### Auto-fixability Assessment

```python
def is_auto_fixable(gap: DataGap) -> bool:
    """Determine if gap can be auto-fixed"""
    
    # Auto-fixable gaps
    auto_fixable_types = [
        GapType.MISSING_RECORD,        # COPY_FROM_SOURCE
        GapType.ORPHANED_RECORD,       # DELETE_FROM_TARGET
        GapType.INCOMPLETE_MIGRATION,  # UPDATE_TARGET
        GapType.VERSION_CONFLICT       # MERGE_DATA
    ]
    
    return gap.gap_type in auto_fixable_types
```

---

## Usage Examples

### Example 1: Basic Gap Detection

```python
from migration.gap_detector import GapDetector

# Initialize detector
detector = GapDetector(
    sqlite_path="data/vpb.db",
    uds3_config={
        "use_mock": False  # Use real backends
    }
)

# Detect all gaps
gaps = detector.detect_all_gaps()

# Print summary
print(f"Total gaps: {len(gaps)}")
for gap_type in GapType:
    count = sum(1 for g in gaps if g.gap_type == gap_type)
    print(f"  {gap_type.value}: {count}")
```

**Output:**
```
Total gaps: 25
  missing_record: 10
  orphaned_record: 3
  schema_mismatch: 2
  data_corruption: 1
  integrity_violation: 1
  incomplete_migration: 5
  version_conflict: 3
```

### Example 2: Filter by Severity

```python
# Get critical gaps only
critical_gaps = [g for g in gaps if g.severity == "critical"]

print(f"Critical gaps: {len(critical_gaps)}")
for gap in critical_gaps:
    print(f"  {gap.record_id}: {gap.description}")
```

### Example 3: Auto-fixable Gaps

```python
# Separate auto-fixable and manual gaps
auto_fixable = [g for g in gaps if g.auto_fixable]
manual = [g for g in gaps if not g.auto_fixable]

print(f"Auto-fixable: {len(auto_fixable)}")
print(f"Manual required: {len(manual)}")

# Review manual gaps
for gap in manual:
    print(f"\nManual fix required:")
    print(f"  Type: {gap.gap_type.value}")
    print(f"  Record: {gap.record_id}")
    print(f"  Reason: {gap.description}")
```

### Example 4: Generate Gap Report

```python
# Generate detailed report
report = {
    "detection_date": datetime.now().isoformat(),
    "total_gaps": len(gaps),
    "by_type": {},
    "by_severity": {},
    "auto_fixable": len([g for g in gaps if g.auto_fixable]),
    "gaps": [g.to_dict() for g in gaps]
}

# Count by type
for gap_type in GapType:
    report["by_type"][gap_type.value] = sum(
        1 for g in gaps if g.gap_type == gap_type
    )

# Count by severity
for severity in ["low", "medium", "high", "critical"]:
    report["by_severity"][severity] = sum(
        1 for g in gaps if g.severity == severity
    )

# Save report
with open("gap_report.json", "w") as f:
    json.dump(report, f, indent=2)
```

---

## Integration with Auto-Fix

### Workflow: Detect → Fix

```python
from migration.gap_detector import GapDetector
from migration.auto_fix import AutoFixer

# 1. Detect gaps
detector = GapDetector("data/vpb.db")
gaps = detector.detect_all_gaps()

# 2. Filter auto-fixable
auto_fixable = [g for g in gaps if g.auto_fixable]

# 3. Create fix actions
fixer = AutoFixer("data/vpb.db")
actions = [fixer.create_fix_action(g) for g in auto_fixable]

# 4. Execute fixes
report = fixer.execute_fixes(actions, dry_run=False)

print(f"Fixed: {report.fixed}/{len(auto_fixable)}")
```

---

## Configuration

Configure detection behavior:

```python
DETECTION_CONFIG = {
    'sqlite_path': 'data/vpb.db',
    'uds3_config': {
        'use_mock': False,
        'postgres_host': 'localhost',
        'neo4j_uri': 'bolt://localhost:7687',
        'chromadb_path': './data/chromadb'
    },
    'detection_options': {
        'check_schema': True,          # Detect schema mismatches
        'check_corruption': True,      # Detect data corruption
        'check_integrity': True,       # Detect integrity violations
        'check_versions': True,        # Detect version conflicts
        'strict_mode': False           # Strict validation (slower)
    }
}
```

---

## Performance

### Detection Speed

Typical performance on various dataset sizes:

| Records | Detection Time | Gaps Found | Rate |
|---------|---------------|------------|------|
| 100 | 2 seconds | 5-10 | 50 rec/sec |
| 1,000 | 15 seconds | 20-50 | 67 rec/sec |
| 10,000 | 2 minutes | 100-200 | 83 rec/sec |
| 100,000 | 20 minutes | 500-1000 | 83 rec/sec |

**Optimization Tips:**
1. Use batch queries for comparison
2. Index SQLite database
3. Enable caching for UDS3 queries
4. Disable strict mode for faster detection
5. Run in parallel for multiple tables

---

## Best Practices

### 1. Run Detection Before Migration

```python
# Always detect gaps before migration
gaps = detector.detect_all_gaps()

if gaps:
    print(f"WARNING: {len(gaps)} gaps detected")
    print("Review gaps before proceeding with migration")
    # Show gap summary
else:
    print("No gaps detected - safe to migrate")
```

### 2. Regular Gap Checks

```python
# Schedule periodic gap checks
import schedule

def check_gaps():
    gaps = detector.detect_all_gaps()
    if gaps:
        send_alert(f"{len(gaps)} gaps detected")

# Check daily
schedule.every().day.at("02:00").do(check_gaps)
```

### 3. Log All Gaps

```python
# Always log gaps for audit trail
for gap in gaps:
    logger.warning(
        f"Gap detected: {gap.gap_type.value} - "
        f"{gap.record_id} - {gap.description}"
    )
```

---

## Troubleshooting

### High Gap Count

**Problem:** Too many gaps detected

**Causes:**
- First migration (expected)
- Schema changes
- Data corruption in source

**Solutions:**
- Review gap types distribution
- Check for patterns
- Verify SQLite data quality

### False Positives

**Problem:** Gaps detected but data is actually correct

**Causes:**
- Timing issues (data changed during detection)
- Cache issues
- Schema version differences

**Solutions:**
- Re-run detection
- Clear caches
- Update schema mappings

### Slow Detection

**Problem:** Detection takes too long

**Causes:**
- Large dataset
- Slow database queries
- Network latency (UDS3)

**Solutions:**
- Increase batch size
- Add database indexes
- Use local UDS3 for testing

---

## Related Documentation

- [Auto-Fix Strategies](AUTO_FIX_STRATEGIES.md) - How to fix detected gaps
- [Migration UI](MIGRATION_UI_GUIDE.md) - Using the migration wizard
- [Migration CLI](../DOCUMENTATION_GAP_ANALYSIS.md) - Command-line migration

---

**Last Updated:** 2025-11-17  
**Version:** 1.1.0  
**Status:** ✅ Production Ready
