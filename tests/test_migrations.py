import os
import sqlite3
import tempfile
import time
import shutil

from vpb_db_migrations import apply_pending_migrations, MIGRATIONS


def test_apply_migrations_creates_table_and_index():
    # Windows File-Lock Workaround: kein Context-Manager für TemporaryDirectory verwenden
    tmp = tempfile.mkdtemp()
    db_path = os.path.join(tmp, 'test.db')
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute("CREATE TABLE vpb_processes (process_id TEXT PRIMARY KEY, updated_at TEXT)")
            conn.commit()
        apply_pending_migrations(db_path)
        with sqlite3.connect(db_path) as conn:
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'")
            assert cur.fetchone() is not None
            cur = conn.execute("SELECT COUNT(*) FROM schema_migrations")
            count = cur.fetchone()[0]
            assert count == len(MIGRATIONS)
            cur = conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_vpb_processes_updated_at'")
            assert cur.fetchone() is not None
    finally:
        # Retry-Löschung (nicht testrelevant falls verzögert)
        for _ in range(10):
            try:
                if os.path.exists(db_path):
                    os.remove(db_path)
                break
            except PermissionError:
                time.sleep(0.05)
        shutil.rmtree(tmp, ignore_errors=True)
