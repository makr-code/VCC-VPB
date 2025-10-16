#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Einfache Schema-Migrations-Infrastruktur für VPB SQLite.

Low-Risk Ansatz:
- Eine Tabelle `schema_migrations` trackt angewendete Versionen.
- MIGRATIONS Liste enthält (version, [SQL...]).
- apply_pending_migrations() führt fehlende Versionen in definierter Reihenfolge aus.

Versionierungskonzept:
- Semantic-Lite: MAJOR.MINOR (Patch optional ignoriert => stabilitätsorientiert)
- Nur additive, rückwärtskompatible Änderungen in diesem Modul (Indizes, Hilfstabellen)

Aktuelle Migrationen:
1.1
  - Anlage Tabelle schema_migrations
  - Index auf vpb_processes.updated_at
"""
from __future__ import annotations

from typing import List, Tuple
import sqlite3
import time
import gc
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Definierte Migrationen (geordnet): (version, [sql statements])
MIGRATIONS: List[Tuple[str, List[str]]] = [
    (
        "1.1",
        [
            # Tabelle zur Verwaltung angewandter Migrationen
            "CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)",
            # Index Ergänzung
            "CREATE INDEX IF NOT EXISTS idx_vpb_processes_updated_at ON vpb_processes(updated_at)",
        ],
    ),
]


def _get_applied_versions(conn: sqlite3.Connection) -> set[str]:
    try:
        cur = conn.execute("SELECT version FROM schema_migrations")
        return {row[0] for row in cur.fetchall()}
    except sqlite3.OperationalError:
        # Tabelle existiert noch nicht
        return set()


def apply_pending_migrations(db_path: str | Path) -> None:
    """Führt alle noch nicht angewandten Migrationen aus.

    Idempotent: Bereits angewandte Versionen werden übersprungen.
    Angepasst für Windows: Explizites Schließen der Verbindung, um File-Locks zu vermeiden.
    """
    path = Path(db_path)
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    # Mehrfaches Öffnen/Schließen pro Migration reduziert Lock-Probleme auf Windows
    for version, statements in MIGRATIONS:
        # Öffne frische Verbindung für Abfrage + evtl. Ausführung
        with sqlite3.connect(path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            applied = _get_applied_versions(conn)
            if version in applied:
                continue
            logger.info("Wende Migration %s an ...", version)
            try:
                for sql in statements:
                    conn.execute(sql)
                conn.execute(
                    "INSERT INTO schema_migrations (version, applied_at) VALUES (?, datetime('now'))",
                    (version,),
                )
                conn.commit()
                logger.info("Migration %s erfolgreich", version)
            except Exception as exc:  # noqa: BLE001
                conn.rollback()
                logger.error("Migration %s fehlgeschlagen: %s", version, exc)
                raise
        # Kleines Delay, damit Windows Dateihandle freigibt (verhindert sporadische WinError 32 in CI)
        time.sleep(0.01)
    # Abschließende minimale Pause – verhindert, dass der Test direkt danach versucht das File zu löschen
    time.sleep(0.05)
    # Force final close cycle by opening & closing once + GC (Windows Lock Workaround)
    try:
        with sqlite3.connect(path) as _c:
            _c.execute("PRAGMA schema_version")
    except Exception:
        pass
    gc.collect()
