"""
Test: Auto-Fix Engine
Tests für automatische Gap-Korrektur
"""

import pytest
import sqlite3
import json
import tempfile
from pathlib import Path

from migration.auto_fix import (
    AutoFixEngine,
    FixStrategy,
    FixStatus,
    auto_fix_all_gaps
)
from migration.gap_detector import GapDetector, DataGap, GapType


@pytest.fixture
def test_db_with_gaps(tmp_path):
    """Erstellt Test-DB mit bekannten Gaps"""
    db_path = tmp_path / "test_gaps.db"
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Schema erstellen
    cursor.execute("""
        CREATE TABLE vpb_processes (
            process_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            process_data TEXT,
            version INTEGER DEFAULT 1
        )
    """)
    
    # Test-Records mit verschiedenen Gap-Szenarien
    test_records = [
        # Normal Record (kein Gap)
        ("process_001", "Normal Process", "Description 1", json.dumps({"elements": []}), 1),
        
        # Missing Record (fehlt in UDS3)
        ("process_002", "Missing Process", "Description 2", json.dumps({"elements": []}), 1),
        
        # Incomplete Migration (teilweise Daten)
        ("process_003", "Incomplete Process", "Description 3", json.dumps({"elements": [{"id": "elem_1"}]}), 1),
    ]
    
    cursor.executemany(
        "INSERT INTO vpb_processes VALUES (?, ?, ?, ?, ?)",
        test_records
    )
    
    conn.commit()
    conn.close()
    
    return str(db_path)


def test_identify_auto_fixable_gaps(test_db_with_gaps):
    """Test: Identifiziere auto-fixable Gaps"""
    print("\n" + "="*80)
    print("TEST: Identify Auto-Fixable Gaps")
    print("="*80)
    
    detector = GapDetector(test_db_with_gaps)
    engine = AutoFixEngine(detector, dry_run=True)
    
    # Create mock gaps
    gaps = [
        DataGap(
            gap_type=GapType.MISSING_RECORD,
            table_name="vpb_processes",
            record_id="process_002",
            description="Missing in UDS3",
            auto_fixable=True,
            severity="medium"
        ),
        DataGap(
            gap_type=GapType.SCHEMA_MISMATCH,
            table_name="vpb_processes",
            record_id="process_003",
            description="Schema mismatch",
            auto_fixable=False,
            severity="high"
        ),
    ]
    
    auto_fixable = engine.identify_auto_fixable_gaps(gaps)
    
    print(f"Total Gaps: {len(gaps)}")
    print(f"Auto-Fixable: {len(auto_fixable)}")
    
    assert len(auto_fixable) == 1, "Should find 1 auto-fixable gap"
    assert auto_fixable[0].gap_type == GapType.MISSING_RECORD
    
    print("✅ Test PASSED")


def test_select_fix_strategy():
    """Test: Wähle korrekte Fix-Strategie"""
    print("\n" + "="*80)
    print("TEST: Select Fix Strategy")
    print("="*80)
    
    detector = GapDetector("dummy.db")
    engine = AutoFixEngine(detector, dry_run=True)
    
    test_cases = [
        (GapType.MISSING_RECORD, FixStrategy.COPY_FROM_SOURCE),
        (GapType.ORPHANED_RECORD, FixStrategy.DELETE_FROM_TARGET),
        (GapType.INCOMPLETE_MIGRATION, FixStrategy.UPDATE_TARGET),
        (GapType.VERSION_CONFLICT, FixStrategy.MERGE_DATA),
        (GapType.SCHEMA_MISMATCH, FixStrategy.SKIP),
    ]
    
    for gap_type, expected_strategy in test_cases:
        gap = DataGap(
            gap_type=gap_type,
            table_name="test_table",
            record_id="test_id",
            description="Test gap"
        )
        
        strategy = engine.select_fix_strategy(gap)
        
        print(f"{gap_type.value:25} → {strategy.value}")
        assert strategy == expected_strategy, f"Wrong strategy for {gap_type.value}"
    
    print("✅ Test PASSED")


def test_create_fix_action():
    """Test: Erstelle Fix-Action"""
    print("\n" + "="*80)
    print("TEST: Create Fix Action")
    print("="*80)
    
    detector = GapDetector("dummy.db")
    engine = AutoFixEngine(detector, dry_run=True)
    
    gap = DataGap(
        gap_type=GapType.MISSING_RECORD,
        table_name="vpb_processes",
        record_id="process_001",
        description="Missing in UDS3",
        auto_fixable=True,
        severity="medium"
    )
    
    action = engine.create_fix_action(gap)
    
    print(f"Gap Type: {gap.gap_type.value}")
    print(f"Strategy: {action.strategy.value}")
    print(f"Description: {action.description}")
    print(f"Requires Confirmation: {action.requires_confirmation}")
    print(f"Status: {action.status.value}")
    
    assert action.strategy == FixStrategy.COPY_FROM_SOURCE
    assert action.gap == gap
    assert action.status == FixStatus.PENDING
    
    print("✅ Test PASSED")


def test_dry_run_mode(test_db_with_gaps):
    """Test: Dry-Run Mode (keine Änderungen)"""
    print("\n" + "="*80)
    print("TEST: Dry-Run Mode")
    print("="*80)
    
    detector = GapDetector(test_db_with_gaps)
    engine = AutoFixEngine(detector, dry_run=True, auto_confirm=True)
    
    # Create mock gap with source data
    gap = DataGap(
        gap_type=GapType.MISSING_RECORD,
        table_name="vpb_processes",
        record_id="process_002",
        description="Missing in UDS3",
        source_data={
            "process_id": "process_002",
            "name": "Test Process",
            "description": "Test",
            "process_data": json.dumps({"elements": []})
        },
        auto_fixable=True,
        severity="medium"
    )
    
    action = engine.create_fix_action(gap)
    success = engine.execute_fix(action)
    
    print(f"Dry-Run: {engine.dry_run}")
    print(f"Action Status: {action.status.value}")
    print(f"Success: {success}")
    
    assert success, "Dry-run should succeed"
    assert action.status == FixStatus.SUCCESS
    assert action.executed_at is not None
    
    print("✅ Test PASSED")


def test_create_backup():
    """Test: Backup-Erstellung"""
    print("\n" + "="*80)
    print("TEST: Create Backup")
    print("="*80)
    
    detector = GapDetector("dummy.db")
    engine = AutoFixEngine(detector, dry_run=True)
    
    gap = DataGap(
        gap_type=GapType.INCOMPLETE_MIGRATION,
        table_name="vpb_processes",
        record_id="process_003",
        description="Incomplete",
        source_data={"name": "Source Name"},
        target_data={"name": "Target Name", "version": 2},
        auto_fixable=True
    )
    
    backup = engine.create_backup(gap)
    
    print(f"Backup Keys: {list(backup.keys())}")
    print(f"Backup: {json.dumps(backup, indent=2)}")
    
    assert 'gap_type' in backup
    assert 'record_id' in backup
    assert 'table_name' in backup
    assert 'timestamp' in backup
    assert 'source_data' in backup
    assert 'target_data' in backup
    
    print("✅ Test PASSED")


def test_auto_fix_with_confirmation():
    """Test: Auto-Fix mit User-Confirmation"""
    print("\n" + "="*80)
    print("TEST: Auto-Fix mit Confirmation")
    print("="*80)
    
    detector = GapDetector("dummy.db")
    engine = AutoFixEngine(detector, dry_run=True, auto_confirm=False)
    
    # Mock gaps
    gaps = [
        DataGap(
            gap_type=GapType.MISSING_RECORD,
            table_name="vpb_processes",
            record_id="process_001",
            description="Test 1",
            source_data={"process_id": "process_001", "name": "Test", "process_data": "{}"},
            auto_fixable=True,
            severity="medium"
        ),
        DataGap(
            gap_type=GapType.MISSING_RECORD,
            table_name="vpb_processes",
            record_id="process_002",
            description="Test 2 (critical)",
            source_data={"process_id": "process_002", "name": "Test", "process_data": "{}"},
            auto_fixable=True,
            severity="critical"  # Requires confirmation
        ),
    ]
    
    # Confirmation callback: Reject critical gaps
    def confirmation_callback(action):
        # Only confirm medium severity, reject critical
        result = action.gap.severity != "critical"
        print(f"Confirmation for {action.gap.record_id} ({action.gap.severity}): {result}")
        return result
    
    report = engine.auto_fix_gaps(gaps=gaps, confirmation_callback=confirmation_callback)
    
    print(f"\n📊 Report:")
    print(f"Total Gaps: {report.total_gaps}")
    print(f"Auto-Fixable: {report.auto_fixable}")
    print(f"Fixed: {report.fixed}")
    print(f"Skipped: {report.skipped}")
    
    assert report.total_gaps == 2
    assert report.auto_fixable == 2
    # Medium severity (process_001) doesn't require confirmation, gets fixed
    # Critical severity (process_002) requires confirmation, gets rejected → skipped
    assert report.fixed == 1, f"Should fix 1 (medium severity), got {report.fixed}"
    assert report.skipped == 1, f"Should skip 1 (rejected critical), got {report.skipped}"
    
    print("✅ Test PASSED")


def test_fix_report_to_dict():
    """Test: Fix Report to Dictionary"""
    print("\n" + "="*80)
    print("TEST: Fix Report to Dict")
    print("="*80)
    
    from migration.auto_fix import FixReport, FixAction
    from datetime import datetime
    
    gap = DataGap(
        gap_type=GapType.MISSING_RECORD,
        table_name="test",
        record_id="test_id",
        description="Test"
    )
    
    action = FixAction(
        gap=gap,
        strategy=FixStrategy.COPY_FROM_SOURCE,
        description="Test action",
        status=FixStatus.SUCCESS,
        executed_at=datetime.now()
    )
    
    report = FixReport(
        total_gaps=10,
        auto_fixable=5,
        fixed=4,
        failed=1,
        skipped=0,
        rolled_back=0,
        actions=[action],
        started_at=datetime.now(),
        completed_at=datetime.now(),
        duration_seconds=1.5,
        dry_run=True
    )
    
    report_dict = report.to_dict()
    
    print(f"Report Dict Keys: {list(report_dict.keys())}")
    print(f"Success Rate: {report_dict['success_rate']:.1f}%")
    
    assert 'total_gaps' in report_dict
    assert 'auto_fixable' in report_dict
    assert 'fixed' in report_dict
    assert 'success_rate' in report_dict
    assert 'actions' in report_dict
    assert report_dict['success_rate'] == 80.0  # 4/5 * 100
    
    print("✅ Test PASSED")


def test_auto_fix_all_gaps_convenience():
    """Test: Convenience Function auto_fix_all_gaps()"""
    print("\n" + "="*80)
    print("TEST: auto_fix_all_gaps() Convenience Function")
    print("="*80)
    
    # Create temp DB
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Create test DB
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE vpb_processes (
                process_id TEXT PRIMARY KEY,
                name TEXT,
                process_data TEXT
            )
        """)
        cursor.execute(
            "INSERT INTO vpb_processes VALUES (?, ?, ?)",
            ("test_001", "Test", "{}")
        )
        conn.commit()
        conn.close()
        
        # Run auto-fix
        report = auto_fix_all_gaps(
            db_path,
            dry_run=True,
            auto_confirm=True
        )
        
        print(f"Report Type: {type(report)}")
        print(f"Total Gaps: {report.total_gaps}")
        print(f"Dry-Run: {report.dry_run}")
        
        assert report.dry_run == True
        print("✅ Test PASSED")
        
    finally:
        # Windows-kompatible DB-Löschung
        try:
            Path(db_path).unlink()
        except (PermissionError, FileNotFoundError):
            pass  # Ignore cleanup errors on Windows


# Run all tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
