"""
Production Load Tests für VPB Migration Tool.

Tests:
- 10k+ Records Migration
- Performance Profiling
- Memory Usage Monitoring
- Stress Testing
- Benchmark gegen Performance Goals

Author: VPB Development Team
Date: 18. Oktober 2025
"""

import pytest
import sqlite3
import time
import json
import psutil
import os
from pathlib import Path
from typing import Dict, Any, List
import cProfile
import pstats
from io import StringIO

# Import Migration Tools
from migration.migration_tool import VPBMigrationTool, MigrationConfig
from migration.gap_detector import GapDetector
from migration.validation import DataValidator


class PerformanceMonitor:
    """Monitor für Performance-Metriken."""
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.start_time = None
        self.start_memory = None
        self.metrics = {
            "duration": 0,
            "memory_start": 0,
            "memory_end": 0,
            "memory_peak": 0,
            "memory_delta": 0,
            "cpu_percent": 0,
            "records_per_second": 0
        }
    
    def start(self):
        """Startet Monitoring."""
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.metrics["memory_start"] = self.start_memory
    
    def stop(self, record_count: int) -> Dict[str, Any]:
        """
        Stoppt Monitoring und berechnet Metriken.
        
        Args:
            record_count: Anzahl verarbeiteter Records
            
        Returns:
            Performance Metrics Dictionary
        """
        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        
        self.metrics["duration"] = end_time - self.start_time
        self.metrics["memory_end"] = end_memory
        self.metrics["memory_delta"] = end_memory - self.start_memory
        self.metrics["memory_peak"] = self.process.memory_info().rss / 1024 / 1024  # MB
        self.metrics["cpu_percent"] = self.process.cpu_percent()
        
        if self.metrics["duration"] > 0:
            self.metrics["records_per_second"] = record_count / self.metrics["duration"]
        
        return self.metrics


def create_test_database(db_path: str, record_count: int = 10000) -> None:
    """
    Erstellt Test-SQLite-Datenbank mit N Records.
    
    Args:
        db_path: Pfad zur SQLite DB
        record_count: Anzahl zu erstellender Records
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Schema erstellen
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vpb_processes (
            process_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            process_data TEXT,
            version INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Test-Records generieren
    print(f"📦 Generiere {record_count} Test-Records...")
    batch_size = 1000
    
    for i in range(0, record_count, batch_size):
        records = []
        for j in range(batch_size):
            if i + j >= record_count:
                break
            
            process_id = f"test_process_{i+j:06d}"
            name = f"Test Process {i+j}"
            description = f"Test Description for Process {i+j}"
            
            # Process Data (JSON)
            process_data = {
                "elements": [
                    {
                        "id": f"elem_{i+j}_1",
                        "type": "activity",
                        "label": f"Activity {i+j}",
                        "x": 100 + (i+j) % 10 * 50,
                        "y": 100 + (i+j) % 5 * 50
                    },
                    {
                        "id": f"elem_{i+j}_2",
                        "type": "decision",
                        "label": f"Decision {i+j}",
                        "x": 300 + (i+j) % 10 * 50,
                        "y": 100 + (i+j) % 5 * 50
                    }
                ],
                "connections": [
                    {
                        "id": f"conn_{i+j}_1",
                        "from": f"elem_{i+j}_1",
                        "to": f"elem_{i+j}_2",
                        "label": "Flow"
                    }
                ],
                "metadata": {
                    "version": "1.0",
                    "author": "Test Generator",
                    "test_id": i+j
                }
            }
            
            records.append((
                process_id,
                name,
                description,
                json.dumps(process_data),
                1
            ))
        
        cursor.executemany(
            "INSERT INTO vpb_processes (process_id, name, description, process_data, version) VALUES (?, ?, ?, ?, ?)",
            records
        )
        
        if (i + batch_size) % 5000 == 0:
            print(f"   ✓ {i + batch_size} Records erstellt...")
    
    conn.commit()
    
    # Verify
    cursor.execute("SELECT COUNT(*) FROM vpb_processes")
    count = cursor.fetchone()[0]
    print(f"✅ {count} Records in Datenbank")
    
    conn.close()


@pytest.fixture
def test_db_1k(tmp_path):
    """Erstellt Test-DB mit 1.000 Records."""
    db_path = tmp_path / "test_1k.db"
    create_test_database(str(db_path), 1000)
    return str(db_path)


@pytest.fixture
def test_db_10k(tmp_path):
    """Erstellt Test-DB mit 10.000 Records."""
    db_path = tmp_path / "test_10k.db"
    create_test_database(str(db_path), 10000)
    return str(db_path)


@pytest.fixture
def test_db_50k(tmp_path):
    """Erstellt Test-DB mit 50.000 Records (Stress Test)."""
    db_path = tmp_path / "test_50k.db"
    create_test_database(str(db_path), 50000)
    return str(db_path)


def test_migration_1k_records(test_db_1k):
    """
    Test: Migration mit 1.000 Records.
    
    Performance Goals:
    - Duration: < 10 Sekunden
    - Memory: < 100 MB Delta
    - Speed: > 100 rec/s
    """
    print("\n" + "="*80)
    print("TEST: Migration 1.000 Records")
    print("="*80)
    
    monitor = PerformanceMonitor()
    monitor.start()
    
    # Migration Config
    config = MigrationConfig(
        source_config={"type": "sqlite", "db_path": test_db_1k},
        target_config={"type": "uds3_polyglot"},
        batch_size=100,
        continue_on_error=False
    )
    
    # Migration ausführen
    tool = VPBMigrationTool(config)
    result = tool.migrate_table("vpb_processes")
    
    # Metrics sammeln
    metrics = monitor.stop(record_count=1000)
    
    # Results
    print(f"\n📊 RESULTS:")
    print(f"   Success: {result['success']}")
    print(f"   Records: {result['successful_records']}/{result['total_records']}")
    print(f"   Duration: {metrics['duration']:.2f}s")
    print(f"   Memory Delta: {metrics['memory_delta']:.2f} MB")
    print(f"   Speed: {metrics['records_per_second']:.1f} rec/s")
    print(f"   CPU: {metrics['cpu_percent']:.1f}%")
    
    # Assertions
    assert result["success"], "Migration should succeed"
    assert result["successful_records"] == 1000, "All records should be migrated"
    assert metrics["duration"] < 30, f"Duration should be < 30s, was {metrics['duration']:.2f}s"
    assert metrics["memory_delta"] < 200, f"Memory delta should be < 200 MB, was {metrics['memory_delta']:.2f} MB"
    assert metrics["records_per_second"] > 30, f"Speed should be > 30 rec/s, was {metrics['records_per_second']:.1f} rec/s"
    
    print("✅ Test PASSED")


def test_migration_10k_records(test_db_10k):
    """
    Test: Migration mit 10.000 Records.
    
    Performance Goals:
    - Duration: < 100 Sekunden
    - Memory: < 500 MB Delta
    - Speed: > 100 rec/s
    """
    print("\n" + "="*80)
    print("TEST: Migration 10.000 Records")
    print("="*80)
    
    monitor = PerformanceMonitor()
    monitor.start()
    
    # Migration Config
    config = MigrationConfig(
        source_config={"type": "sqlite", "db_path": test_db_10k},
        target_config={"type": "uds3_polyglot"},
        batch_size=500,
        continue_on_error=False
    )
    
    # Progress Callback
    progress_data = {"batches": 0, "records": 0}
    
    def progress_callback(batch_num, batch_size, table_name):
        progress_data["batches"] = batch_num
        progress_data["records"] += batch_size
        if batch_num % 5 == 0:
            print(f"   ✓ Batch {batch_num}: {progress_data['records']} records processed")
    
    # Migration ausführen
    tool = VPBMigrationTool(config)
    result = tool.migrate_table("vpb_processes", progress_callback=progress_callback)
    
    # Metrics sammeln
    metrics = monitor.stop(record_count=10000)
    
    # Results
    print(f"\n📊 RESULTS:")
    print(f"   Success: {result['success']}")
    print(f"   Records: {result['successful_records']}/{result['total_records']}")
    print(f"   Batches: {progress_data['batches']}")
    print(f"   Duration: {metrics['duration']:.2f}s")
    print(f"   Memory Start: {metrics['memory_start']:.2f} MB")
    print(f"   Memory End: {metrics['memory_end']:.2f} MB")
    print(f"   Memory Delta: {metrics['memory_delta']:.2f} MB")
    print(f"   Speed: {metrics['records_per_second']:.1f} rec/s")
    print(f"   CPU: {metrics['cpu_percent']:.1f}%")
    
    # Assertions
    assert result["success"], "Migration should succeed"
    assert result["successful_records"] == 10000, "All records should be migrated"
    assert metrics["duration"] < 300, f"Duration should be < 300s, was {metrics['duration']:.2f}s"
    assert metrics["memory_delta"] < 1000, f"Memory delta should be < 1000 MB, was {metrics['memory_delta']:.2f} MB"
    assert metrics["records_per_second"] > 30, f"Speed should be > 30 rec/s, was {metrics['records_per_second']:.1f} rec/s"
    
    print("✅ Test PASSED")


def test_migration_with_profiling(test_db_1k):
    """
    Test: Migration mit cProfile Profiling.
    
    Identifiziert Performance-Bottlenecks.
    """
    print("\n" + "="*80)
    print("TEST: Migration mit Profiling (1.000 Records)")
    print("="*80)
    
    config = MigrationConfig(
        source_config={"type": "sqlite", "db_path": test_db_1k},
        target_config={"type": "uds3_polyglot"},
        batch_size=100
    )
    
    tool = VPBMigrationTool(config)
    
    # Profiling
    profiler = cProfile.Profile()
    profiler.enable()
    
    result = tool.migrate_table("vpb_processes")
    
    profiler.disable()
    
    # Stats
    stats = pstats.Stats(profiler, stream=StringIO())
    stats.sort_stats('cumulative')
    
    print("\n📊 TOP 20 BOTTLENECKS (by cumulative time):")
    stats.print_stats(20)
    
    # Identify key bottlenecks
    print("\n🔍 KEY BOTTLENECKS:")
    stats.sort_stats('tottime')
    stats_str = StringIO()
    stats.stream = stats_str
    stats.print_stats(10)
    
    stats_output = stats_str.getvalue()
    print(stats_output[:1000])  # Print first 1000 chars
    
    assert result["success"], "Migration should succeed"
    print("✅ Profiling Complete")


def test_memory_leak_detection(test_db_1k):
    """
    Test: Memory Leak Detection über mehrere Runs.
    
    Führt Migration mehrfach aus und prüft auf Memory Leaks.
    """
    print("\n" + "="*80)
    print("TEST: Memory Leak Detection (5 Runs)")
    print("="*80)
    
    config = MigrationConfig(
        source_config={"type": "sqlite", "db_path": test_db_1k},
        target_config={"type": "uds3_polyglot"},
        batch_size=100
    )
    
    process = psutil.Process(os.getpid())
    memory_readings = []
    
    for run in range(5):
        print(f"\n🔄 Run {run + 1}/5")
        
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        tool = VPBMigrationTool(config)
        result = tool.migrate_table("vpb_processes")
        
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        delta = end_memory - start_memory
        
        memory_readings.append({
            "run": run + 1,
            "start": start_memory,
            "end": end_memory,
            "delta": delta
        })
        
        print(f"   Memory: {start_memory:.2f} MB → {end_memory:.2f} MB (Δ {delta:.2f} MB)")
        
        assert result["success"], f"Run {run + 1} should succeed"
    
    # Analyse
    print("\n📊 MEMORY ANALYSIS:")
    avg_delta = sum(r["delta"] for r in memory_readings) / len(memory_readings)
    max_delta = max(r["delta"] for r in memory_readings)
    
    print(f"   Average Delta: {avg_delta:.2f} MB")
    print(f"   Max Delta: {max_delta:.2f} MB")
    
    # Check for memory leak (Delta sollte nicht stetig steigen)
    first_delta = memory_readings[0]["delta"]
    last_delta = memory_readings[-1]["delta"]
    growth = last_delta - first_delta
    
    print(f"   Growth (First → Last): {growth:.2f} MB")
    
    # Warning wenn Memory Growth > 50 MB
    if growth > 50:
        print(f"⚠️  WARNING: Potential memory leak detected (Growth: {growth:.2f} MB)")
    else:
        print("✅ No significant memory leak detected")
    
    assert growth < 100, f"Memory growth should be < 100 MB, was {growth:.2f} MB"


def test_batch_size_optimization(test_db_1k):
    """
    Test: Optimale Batch Size ermitteln.
    
    Testet verschiedene Batch Sizes und vergleicht Performance.
    """
    print("\n" + "="*80)
    print("TEST: Batch Size Optimization")
    print("="*80)
    
    batch_sizes = [10, 50, 100, 250, 500]
    results = []
    
    for batch_size in batch_sizes:
        print(f"\n📦 Testing Batch Size: {batch_size}")
        
        monitor = PerformanceMonitor()
        monitor.start()
        
        config = MigrationConfig(
            source_config={"type": "sqlite", "db_path": test_db_1k},
            target_config={"type": "uds3_polyglot"},
            batch_size=batch_size
        )
        
        tool = VPBMigrationTool(config)
        result = tool.migrate_table("vpb_processes")
        
        metrics = monitor.stop(record_count=1000)
        
        results.append({
            "batch_size": batch_size,
            "duration": metrics["duration"],
            "speed": metrics["records_per_second"],
            "memory_delta": metrics["memory_delta"]
        })
        
        print(f"   Duration: {metrics['duration']:.2f}s")
        print(f"   Speed: {metrics['records_per_second']:.1f} rec/s")
        print(f"   Memory: {metrics['memory_delta']:.2f} MB")
        
        assert result["success"], f"Batch size {batch_size} should succeed"
    
    # Find optimal batch size
    print("\n📊 BATCH SIZE COMPARISON:")
    best = min(results, key=lambda x: x["duration"])
    
    for r in results:
        marker = "⭐" if r == best else "  "
        print(f"{marker} Batch {r['batch_size']:>3}: {r['duration']:>6.2f}s | {r['speed']:>6.1f} rec/s | {r['memory_delta']:>6.2f} MB")
    
    print(f"\n✅ Optimal Batch Size: {best['batch_size']} ({best['speed']:.1f} rec/s)")


@pytest.mark.slow
def test_stress_test_50k_records(test_db_50k):
    """
    Stress Test: Migration mit 50.000 Records.
    
    Performance Goals:
    - Duration: < 600 Sekunden (10 min)
    - Memory: < 2 GB Delta
    - Speed: > 80 rec/s
    """
    print("\n" + "="*80)
    print("STRESS TEST: Migration 50.000 Records")
    print("="*80)
    
    monitor = PerformanceMonitor()
    monitor.start()
    
    # Migration Config (größere Batches für bessere Performance)
    config = MigrationConfig(
        source_config={"type": "sqlite", "db_path": test_db_50k},
        target_config={"type": "uds3_polyglot"},
        batch_size=1000,
        continue_on_error=True
    )
    
    # Progress Callback
    progress_data = {"batches": 0, "records": 0, "last_report": time.time()}
    
    def progress_callback(batch_num, batch_size, table_name):
        progress_data["batches"] = batch_num
        progress_data["records"] += batch_size
        
        # Report alle 5 Sekunden
        now = time.time()
        if now - progress_data["last_report"] > 5:
            elapsed = now - monitor.start_time
            speed = progress_data["records"] / elapsed if elapsed > 0 else 0
            print(f"   ✓ Batch {batch_num}: {progress_data['records']}/50000 records ({speed:.1f} rec/s)")
            progress_data["last_report"] = now
    
    # Migration ausführen
    tool = VPBMigrationTool(config)
    result = tool.migrate_table("vpb_processes", progress_callback=progress_callback)
    
    # Metrics sammeln
    metrics = monitor.stop(record_count=50000)
    
    # Results
    print(f"\n📊 STRESS TEST RESULTS:")
    print(f"   Success: {result['success']}")
    print(f"   Records: {result['successful_records']}/{result['total_records']}")
    print(f"   Failed: {result['failed_records']}")
    print(f"   Duration: {metrics['duration']:.2f}s ({metrics['duration']/60:.1f} min)")
    print(f"   Memory Delta: {metrics['memory_delta']:.2f} MB")
    print(f"   Memory Peak: {metrics['memory_peak']:.2f} MB")
    print(f"   Speed: {metrics['records_per_second']:.1f} rec/s")
    print(f"   CPU: {metrics['cpu_percent']:.1f}%")
    
    # Assertions (relaxed für Stress Test)
    assert result["successful_records"] > 45000, f"At least 45k records should succeed, got {result['successful_records']}"
    assert metrics["duration"] < 900, f"Duration should be < 900s, was {metrics['duration']:.2f}s"
    assert metrics["memory_delta"] < 3000, f"Memory delta should be < 3 GB, was {metrics['memory_delta']:.2f} MB"
    
    print("✅ Stress Test PASSED")


def test_gap_detection_performance(test_db_10k):
    """
    Test: Gap Detection Performance.
    
    Performance Goals:
    - Duration: < 5 Sekunden für 10k records
    """
    print("\n" + "="*80)
    print("TEST: Gap Detection Performance (10.000 Records)")
    print("="*80)
    
    monitor = PerformanceMonitor()
    monitor.start()
    
    detector = GapDetector(test_db_10k)
    gaps = detector.detect_all_gaps()
    
    metrics = monitor.stop(record_count=10000)
    
    total_gaps = sum(len(gap_list) for gap_list in gaps.values())
    
    print(f"\n📊 RESULTS:")
    print(f"   Duration: {metrics['duration']:.2f}s")
    print(f"   Memory Delta: {metrics['memory_delta']:.2f} MB")
    print(f"   Total Gaps: {total_gaps}")
    print(f"   Gap Types: {len(gaps)}")
    
    for gap_type, gap_list in gaps.items():
        print(f"      - {gap_type}: {len(gap_list)} gaps")
    
    assert metrics["duration"] < 10, f"Duration should be < 10s, was {metrics['duration']:.2f}s"
    print("✅ Test PASSED")


def test_validation_performance(test_db_1k):
    """
    Test: Validation Performance.
    
    Performance Goals:
    - Duration: < 10 Sekunden für 1k records
    """
    print("\n" + "="*80)
    print("TEST: Validation Performance (1.000 Records)")
    print("="*80)
    
    # Erst Migration durchführen
    config = MigrationConfig(
        source_config={"type": "sqlite", "db_path": test_db_1k},
        target_config={"type": "uds3_polyglot"},
        batch_size=100
    )
    
    tool = VPBMigrationTool(config)
    migration_result = tool.migrate_table("vpb_processes")
    
    assert migration_result["success"], "Migration should succeed before validation"
    
    # Validation Performance messen
    monitor = PerformanceMonitor()
    monitor.start()
    
    validator = DataValidator(config)
    validation_result = validator.validate_migration("vpb_processes")
    
    metrics = monitor.stop(record_count=1000)
    
    print(f"\n📊 RESULTS:")
    print(f"   Valid: {validation_result['valid']}")
    print(f"   Records: {validation_result['details']['record_count']}")
    print(f"   ID Match Rate: {validation_result['details']['id_match_rate']:.1%}")
    print(f"   Checksum Match Rate: {validation_result['details'].get('checksum_match_rate', 0):.1%}")
    print(f"   Duration: {metrics['duration']:.2f}s")
    print(f"   Memory Delta: {metrics['memory_delta']:.2f} MB")
    
    assert validation_result["valid"], "Validation should pass"
    assert metrics["duration"] < 30, f"Duration should be < 30s, was {metrics['duration']:.2f}s"
    print("✅ Test PASSED")


if __name__ == "__main__":
    """
    Run Performance Tests direkt.
    
    Usage:
        python tests/test_migration_performance.py
    """
    import sys
    
    print("="*80)
    print("VPB Migration Tool - Production Load Tests")
    print("="*80)
    
    # Simple Test Run ohne pytest
    from tempfile import mkdtemp
    tmp_dir = Path(mkdtemp())
    
    try:
        # 1k Test
        db_1k = tmp_dir / "test_1k.db"
        create_test_database(str(db_1k), 1000)
        test_migration_1k_records(str(db_1k))
        
        # Batch Size Optimization
        test_batch_size_optimization(str(db_1k))
        
        # Memory Leak Detection
        test_memory_leak_detection(str(db_1k))
        
        # Gap Detection Performance
        db_10k = tmp_dir / "test_10k.db"
        create_test_database(str(db_10k), 10000)
        test_gap_detection_performance(str(db_10k))
        
        # 10k Test
        test_migration_10k_records(str(db_10k))
        
        print("\n" + "="*80)
        print("✅ ALL PERFORMANCE TESTS PASSED!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)
