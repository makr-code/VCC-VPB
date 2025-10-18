"""
Quick Performance Test - 100 Records.

Schneller Test zur Verifikation der Performance-Test-Infrastruktur.
"""

import sqlite3
import time
import json
from pathlib import Path
import tempfile
import psutil
import os

# Simple Performance Test
def quick_performance_test():
    """Quick test mit 100 Records."""
    
    print("="*80)
    print("QUICK PERFORMANCE TEST - 100 Records")
    print("="*80)
    
    # Create temp DB
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Create test database
        print(f"\n📦 Creating test database...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE vpb_processes (
                process_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                process_data TEXT,
                version INTEGER DEFAULT 1
            )
        """)
        
        # Insert 100 test records
        records = []
        for i in range(100):
            process_data = {
                "elements": [{"id": f"elem_{i}", "type": "activity", "label": f"Activity {i}"}],
                "connections": [],
                "metadata": {"test_id": i}
            }
            records.append((
                f"test_process_{i:03d}",
                f"Test Process {i}",
                f"Test Description {i}",
                json.dumps(process_data),
                1
            ))
        
        cursor.executemany(
            "INSERT INTO vpb_processes VALUES (?, ?, ?, ?, ?)",
            records
        )
        conn.commit()
        conn.close()
        
        print(f"✅ Created {len(records)} test records")
        
        # Performance Test
        print(f"\n🚀 Starting migration...")
        
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from migration.migration_tool import VPBMigrationTool, MigrationConfig
        
        process = psutil.Process(os.getpid())
        start_time = time.time()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        config = MigrationConfig(
            source_db_path=db_path,
            target_config={"type": "uds3_polyglot"},
            batch_size=25,
            enable_gap_detection=False,  # Disable for quick test
            enable_validation=False,  # Disable for quick test
            enable_rollback=False  # Disable rollback
        )
        
        tool = VPBMigrationTool(config)
        result = tool.migrate()  # Corrected API call
        
        end_time = time.time()
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Results
        duration = end_time - start_time
        memory_delta = end_memory - start_memory
        speed = 100 / duration if duration > 0 else 0
        
        print(f"\n📊 RESULTS:")
        print(f"   Status: {result.status.value}")
        print(f"   Records: {result.migrated_records}/{result.total_records}")
        print(f"   Failed: {result.failed_records}")
        print(f"   Duration: {duration:.2f}s")
        print(f"   Memory Delta: {memory_delta:.2f} MB")
        print(f"   Speed: {speed:.1f} rec/s")
        
        if result.errors:
            print(f"\n❌ ERRORS:")
            for error in result.errors[:5]:  # Show first 5 errors
                print(f"   - {error}")
        
        if result.warnings:
            print(f"\n⚠️ WARNINGS:")
            for warning in result.warnings[:3]:
                print(f"   - {warning}")
        
        # Basic assertions
        success = result.status.value in ["completed", "in_progress"]
        if not success:
            print(f"\n❌ Migration Status: {result.status.value}")
            return {"success": False, "error": f"Status: {result.status.value}", "errors": result.errors}
        
        assert result.migrated_records == 100, f"All 100 records should migrate, got {result.migrated_records}"
        
        print(f"\n✅ QUICK TEST PASSED!")
        
        # Performance estimates for larger datasets
        print(f"\n📈 PERFORMANCE ESTIMATES:")
        print(f"   1,000 records:  ~{1000/speed:.1f}s ({1000/speed/60:.1f} min)")
        print(f"   10,000 records: ~{10000/speed:.1f}s ({10000/speed/60:.1f} min)")
        print(f"   50,000 records: ~{50000/speed:.1f}s ({50000/speed/60:.1f} min)")
        
        return {
            "success": True,
            "duration": duration,
            "memory_delta": memory_delta,
            "speed": speed
        }
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}
        
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.remove(db_path)


if __name__ == "__main__":
    quick_performance_test()
