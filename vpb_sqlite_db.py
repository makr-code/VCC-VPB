#!/usr/bin/env python3
"""
VERITAS Protected Module
WARNING: This file contains embedded protection keys. 
Modification will be detected and may result in license violations.
"""

# === VERITAS PROTECTION KEYS (DO NOT MODIFY) ===
module_name = "vpb_sqlite_db"
module_licenced_organization = "VERITAS_TECH_GMBH"
module_licence_key = "eyJjbGllbnRfaWQi...CalP5A=="  # Gekuerzt fuer Sicherheit
module_organization_key = "4674cf19c3ce01a9375f10b55521ee900471037bb4c51ca2f35124c57e4f9870"
module_file_key = "207668c2417e451c3d1dc776f5141f8ef388bdcf305b7c043dcdf2679b654439"
module_version = "1.0"
module_protection_level = 1
# === END PROTECTION KEYS ===
"""
VPB SQLite Database Integration
Persistente Speicherung für VPB Process Designer mit SQLite

Autor: UDS3 Development Team  
Datum: 22. August 2025
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import uuid

from vpb_db_migrations import apply_pending_migrations

from uds3_vpb_schema import VPBProcessRecord, VPBElementData, VPBConnectionData, VPBProcessStatus, VPBAuthorityLevel, VPBLegalContext
from config import VPB_PROCESSES_DB

logger = logging.getLogger(__name__)

class VPBSQLiteDB:
    """SQLite Database für VPB Process Designer"""
    
    def __init__(self, db_path: str = None):
        """Initialisiert VPB SQLite Database"""
        if db_path is None:
            db_path = VPB_PROCESSES_DB
        self.db_path = Path(db_path)
        self.init_database()
    
    def init_database(self):
        """Erstellt Database-Schema falls nicht vorhanden"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                
                # Haupttabelle für Prozesse
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS vpb_processes (
                        process_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        version TEXT DEFAULT '1.0',
                        status TEXT DEFAULT 'draft',
                        legal_context TEXT DEFAULT 'verwaltungsrecht_allgemein',
                        authority_level TEXT DEFAULT 'gemeinde',
                        responsible_authority TEXT,
                        involved_authorities TEXT,  -- JSON Array
                        legal_basis TEXT,  -- JSON Array
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        created_by TEXT DEFAULT 'system',
                        last_modified_by TEXT DEFAULT 'system',
                        complexity_score REAL DEFAULT 0.0,
                        automation_score REAL DEFAULT 0.0,
                        compliance_score REAL DEFAULT 0.0,
                        citizen_satisfaction_score REAL DEFAULT 0.0,
                        geo_scope TEXT DEFAULT 'Deutschland',
                        geo_coordinates TEXT,  -- JSON [lat, lon]
                        tags TEXT,  -- JSON Array
                        process_data TEXT  -- Complete JSON backup
                    )
                """)
                
                # Tabelle für Elemente
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS vpb_elements (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        process_id TEXT NOT NULL,
                        element_id TEXT NOT NULL,
                        element_type TEXT NOT NULL,
                        name TEXT NOT NULL,
                        x REAL NOT NULL,
                        y REAL NOT NULL,
                        width REAL DEFAULT 100,
                        height REAL DEFAULT 60,
                        description TEXT,
                        legal_basis TEXT,
                        competent_authority TEXT,
                        deadline_days INTEGER,
                        swimlane TEXT,
                        geo_relevance BOOLEAN DEFAULT FALSE,
                        admin_level INTEGER,
                        compliance_tags TEXT,  -- JSON Array
                        risk_level TEXT DEFAULT 'low',
                        automation_potential REAL DEFAULT 0.0,
                        citizen_impact TEXT DEFAULT 'low',
                        FOREIGN KEY (process_id) REFERENCES vpb_processes (process_id) ON DELETE CASCADE,
                        UNIQUE(process_id, element_id)
                    )
                """)
                
                # Tabelle für Verbindungen
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS vpb_connections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        process_id TEXT NOT NULL,
                        connection_id TEXT NOT NULL,
                        source_element_id TEXT NOT NULL,
                        target_element_id TEXT NOT NULL,
                        source_point_x REAL DEFAULT 0,
                        source_point_y REAL DEFAULT 0,
                        target_point_x REAL DEFAULT 0,
                        target_point_y REAL DEFAULT 0,
                        connection_type TEXT DEFAULT 'standard',
                        condition TEXT,
                        label TEXT,
                        style TEXT DEFAULT 'solid',
                        probability REAL DEFAULT 1.0,
                        average_duration_days INTEGER,
                        bottleneck_indicator BOOLEAN DEFAULT FALSE,
                        compliance_critical BOOLEAN DEFAULT FALSE,
                        FOREIGN KEY (process_id) REFERENCES vpb_processes (process_id) ON DELETE CASCADE,
                        UNIQUE(process_id, connection_id)
                    )
                """)
                
                # Indizes für bessere Performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_vpb_processes_status ON vpb_processes(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_vpb_processes_authority ON vpb_processes(authority_level)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_vpb_processes_legal ON vpb_processes(legal_context)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_vpb_elements_process ON vpb_elements(process_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_vpb_connections_process ON vpb_connections(process_id)")
                
                conn.commit()
                logger.info(f"VPB SQLite Database initialisiert: {self.db_path}")

            # Nach Basisschema Migrationen anwenden
            apply_pending_migrations(self.db_path)
                
        except Exception as e:
            logger.error(f"Fehler bei Database-Initialisierung: {e}")
            raise
    
    def save_process(self, process: VPBProcessRecord) -> bool:
        """Speichert VPB-Prozess in SQLite"""
        try:
            process.updated_at = datetime.now()
            process.update_scores()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                
                # Hauptprozess speichern
                conn.execute("""
                    INSERT OR REPLACE INTO vpb_processes (
                        process_id, name, description, version, status,
                        legal_context, authority_level, responsible_authority,
                        involved_authorities, legal_basis, created_at, updated_at,
                        created_by, last_modified_by, complexity_score,
                        automation_score, compliance_score, citizen_satisfaction_score,
                        geo_scope, geo_coordinates, tags, process_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    process.process_id, process.name, process.description,
                    process.version, process.status.value, process.legal_context.value,
                    process.authority_level.value, process.responsible_authority,
                    json.dumps(process.involved_authorities), json.dumps(process.legal_basis),
                    process.created_at.isoformat(), process.updated_at.isoformat(),
                    process.created_by, process.last_modified_by, process.complexity_score,
                    process.automation_score, process.compliance_score, process.citizen_satisfaction_score,
                    process.geo_scope, json.dumps(process.geo_coordinates) if process.geo_coordinates else None,
                    json.dumps(process.tags), json.dumps(process.to_dict())
                ))
                
                # Alte Elemente und Verbindungen löschen
                conn.execute("DELETE FROM vpb_elements WHERE process_id = ?", (process.process_id,))
                conn.execute("DELETE FROM vpb_connections WHERE process_id = ?", (process.process_id,))
                
                # Elemente speichern
                for element in process.elements:
                    conn.execute("""
                        INSERT INTO vpb_elements (
                            process_id, element_id, element_type, name, x, y,
                            width, height, description, legal_basis, competent_authority,
                            deadline_days, swimlane, geo_relevance, admin_level,
                            compliance_tags, risk_level, automation_potential, citizen_impact
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        process.process_id, element.element_id, element.element_type,
                        element.name, element.x, element.y, element.width, element.height,
                        element.description, element.legal_basis, element.competent_authority,
                        element.deadline_days, element.swimlane, element.geo_relevance,
                        element.admin_level, json.dumps(element.compliance_tags),
                        element.risk_level, element.automation_potential, element.citizen_impact
                    ))
                
                # Verbindungen speichern  
                for connection in process.connections:
                    # Normalisierung connection_type (Uppercase Domain-Konsistenz)
                    ctype = (connection.connection_type or "").upper()
                    conn.execute("""
                        INSERT INTO vpb_connections (
                            process_id, connection_id, source_element_id, target_element_id,
                            source_point_x, source_point_y, target_point_x, target_point_y,
                            connection_type, condition, label, style, probability,
                            average_duration_days, bottleneck_indicator, compliance_critical
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        process.process_id, connection.connection_id,
                        connection.source_element_id, connection.target_element_id,
                        connection.source_point[0], connection.source_point[1],
                        connection.target_point[0], connection.target_point[1],
                        ctype, connection.condition, connection.label,
                        connection.style, connection.probability, connection.average_duration_days,
                        connection.bottleneck_indicator, connection.compliance_critical
                    ))
                
                conn.commit()
                logger.info(f"Prozess gespeichert: {process.process_id} - {process.name}")
                return True
                
        except Exception as e:
            logger.error(f"Fehler beim Speichern: {e}")
            return False
    
    def load_process(self, process_id: str) -> Optional[VPBProcessRecord]:
        """Lädt VPB-Prozess aus SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Hauptprozess laden
                cursor = conn.execute("SELECT * FROM vpb_processes WHERE process_id = ?", (process_id,))
                process_row = cursor.fetchone()
                
                if not process_row:
                    logger.warning(f"Prozess nicht gefunden: {process_id}")
                    return None
                
                # Elemente laden
                cursor = conn.execute("SELECT * FROM vpb_elements WHERE process_id = ?", (process_id,))
                element_rows = cursor.fetchall()
                
                # Verbindungen laden
                cursor = conn.execute("SELECT * FROM vpb_connections WHERE process_id = ?", (process_id,))
                connection_rows = cursor.fetchall()
                
                # VPBProcessRecord rekonstruieren
                process = VPBProcessRecord(
                    process_id=process_row["process_id"],
                    name=process_row["name"],
                    description=process_row["description"] or "",
                    version=process_row["version"],
                    status=VPBProcessStatus(process_row["status"]),
                    legal_context=VPBLegalContext(process_row["legal_context"]),
                    authority_level=VPBAuthorityLevel(process_row["authority_level"]),
                    responsible_authority=process_row["responsible_authority"] or "",
                    involved_authorities=json.loads(process_row["involved_authorities"] or "[]"),
                    legal_basis=json.loads(process_row["legal_basis"] or "[]"),
                    created_at=datetime.fromisoformat(process_row["created_at"]),
                    updated_at=datetime.fromisoformat(process_row["updated_at"]),
                    created_by=process_row["created_by"],
                    last_modified_by=process_row["last_modified_by"],
                    complexity_score=process_row["complexity_score"],
                    automation_score=process_row["automation_score"],
                    compliance_score=process_row["compliance_score"],
                    citizen_satisfaction_score=process_row["citizen_satisfaction_score"],
                    geo_scope=process_row["geo_scope"],
                    geo_coordinates=json.loads(process_row["geo_coordinates"]) if process_row["geo_coordinates"] else None,
                    tags=json.loads(process_row["tags"] or "[]")
                )
                
                # Elemente hinzufügen
                for row in element_rows:
                    element = VPBElementData(
                        element_id=row["element_id"],
                        element_type=row["element_type"],
                        name=row["name"],
                        x=row["x"],
                        y=row["y"],
                        width=row["width"],
                        height=row["height"],
                        description=row["description"] or "",
                        legal_basis=row["legal_basis"] or "",
                        competent_authority=row["competent_authority"] or "",
                        deadline_days=row["deadline_days"],
                        swimlane=row["swimlane"] or "",
                        geo_relevance=bool(row["geo_relevance"]),
                        admin_level=row["admin_level"],
                        compliance_tags=json.loads(row["compliance_tags"] or "[]"),
                        risk_level=row["risk_level"],
                        automation_potential=row["automation_potential"],
                        citizen_impact=row["citizen_impact"]
                    )
                    process.elements.append(element)
                
                # Verbindungen hinzufügen
                for row in connection_rows:
                    connection = VPBConnectionData(
                        connection_id=row["connection_id"],
                        source_element_id=row["source_element_id"],
                        target_element_id=row["target_element_id"],
                        source_point=(row["source_point_x"], row["source_point_y"]),
                        target_point=(row["target_point_x"], row["target_point_y"]),
                        connection_type=row["connection_type"],
                        condition=row["condition"] or "",
                        label=row["label"] or "",
                        style=row["style"],
                        probability=row["probability"],
                        average_duration_days=row["average_duration_days"],
                        bottleneck_indicator=bool(row["bottleneck_indicator"]),
                        compliance_critical=bool(row["compliance_critical"])
                    )
                    process.connections.append(connection)
                
                logger.info(f"Prozess geladen: {process_id} - {process.name}")
                return process
                
        except Exception as e:
            logger.error(f"Fehler beim Laden: {e}")
            return None
    
    def list_processes(self, status: Optional[str] = None, authority_level: Optional[str] = None) -> List[Dict[str, Any]]:
        """Listet alle Prozesse auf"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                query = "SELECT * FROM vpb_processes"
                params = []
                
                conditions = []
                if status:
                    conditions.append("status = ?")
                    params.append(status)
                if authority_level:
                    conditions.append("authority_level = ?")
                    params.append(authority_level)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY updated_at DESC"
                
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                
                processes = []
                for row in rows:
                    processes.append({
                        "process_id": row["process_id"],
                        "name": row["name"],
                        "description": row["description"],
                        "status": row["status"],
                        "authority_level": row["authority_level"],
                        "legal_context": row["legal_context"],
                        "updated_at": row["updated_at"],
                        "complexity_score": row["complexity_score"],
                        "automation_score": row["automation_score"],
                        "compliance_score": row["compliance_score"]
                    })
                
                return processes
                
        except Exception as e:
            logger.error(f"Fehler beim Auflisten: {e}")
            return []
    
    def delete_process(self, process_id: str) -> bool:
        """Löscht Prozess aus SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.execute("DELETE FROM vpb_processes WHERE process_id = ?", (process_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    logger.info(f"Prozess gelöscht: {process_id}")
                    return True
                else:
                    logger.warning(f"Prozess nicht gefunden zum Löschen: {process_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Fehler beim Löschen: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Erstellt Database-Statistiken"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                stats = {}
                
                # Prozess-Anzahlen
                cursor = conn.execute("SELECT COUNT(*) as total FROM vpb_processes")
                stats["total_processes"] = cursor.fetchone()["total"]
                
                # Status-Verteilung
                cursor = conn.execute("SELECT status, COUNT(*) as count FROM vpb_processes GROUP BY status")
                stats["by_status"] = {row["status"]: row["count"] for row in cursor.fetchall()}
                
                # Behörden-Verteilung
                cursor = conn.execute("SELECT authority_level, COUNT(*) as count FROM vpb_processes GROUP BY authority_level")
                stats["by_authority"] = {row["authority_level"]: row["count"] for row in cursor.fetchall()}
                
                # Durchschnittliche Scores
                cursor = conn.execute("""
                    SELECT 
                        AVG(complexity_score) as avg_complexity,
                        AVG(automation_score) as avg_automation,
                        AVG(compliance_score) as avg_compliance
                    FROM vpb_processes
                """)
                row = cursor.fetchone()
                stats["average_scores"] = {
                    "complexity": round(row["avg_complexity"] or 0, 3),
                    "automation": round(row["avg_automation"] or 0, 3),
                    "compliance": round(row["avg_compliance"] or 0, 3)
                }
                
                # Element- und Verbindungs-Anzahlen
                cursor = conn.execute("SELECT COUNT(*) as total FROM vpb_elements")
                stats["total_elements"] = cursor.fetchone()["total"]
                
                cursor = conn.execute("SELECT COUNT(*) as total FROM vpb_connections")
                stats["total_connections"] = cursor.fetchone()["total"]
                
                return stats
                
        except Exception as e:
            logger.error(f"Fehler bei Statistik-Erstellung: {e}")
            return {}

# CLI für Database-Management
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="VPB SQLite Database Management")
    parser.add_argument("--db", default=VPB_PROCESSES_DB, help="Database Pfad")
    parser.add_argument("--list", action="store_true", help="Alle Prozesse auflisten")
    parser.add_argument("--stats", action="store_true", help="Database-Statistiken")
    parser.add_argument("--init", action="store_true", help="Database initialisieren")
    parser.add_argument("--import", dest="import_file", help="VPB JSON-Datei importieren")
    parser.add_argument("--export", dest="export_id", help="Prozess als JSON exportieren")
    
    args = parser.parse_args()
    
    # Logging setup
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    db = VPBSQLiteDB(args.db)
    
    if args.init:
        print("Database initialisiert")
        
    elif args.list:
        processes = db.list_processes()
        print(f"\nGefundene Prozesse: {len(processes)}")
        print("-" * 80)
        for proc in processes:
            print(f"{proc['process_id']}: {proc['name']} [{proc['status']}]")
            print(f"  Behörde: {proc['authority_level']} | Komplexität: {proc['complexity_score']:.2f}")
            print(f"  Aktualisiert: {proc['updated_at']}")
            print()
            
    elif args.stats:
        stats = db.get_statistics()
        print("\n=== VPB Database Statistiken ===")
        print(f"Prozesse gesamt: {stats.get('total_processes', 0)}")
        print(f"Elemente gesamt: {stats.get('total_elements', 0)}")
        print(f"Verbindungen gesamt: {stats.get('total_connections', 0)}")
        
        print("\nStatus-Verteilung:")
        for status, count in stats.get('by_status', {}).items():
            print(f"  {status}: {count}")
            
        print("\nBehörden-Verteilung:")
        for auth, count in stats.get('by_authority', {}).items():
            print(f"  {auth}: {count}")
            
        print("\nDurchschnittliche Scores:")
        scores = stats.get('average_scores', {})
        print(f"  Komplexität: {scores.get('complexity', 0):.3f}")
        print(f"  Automatisierung: {scores.get('automation', 0):.3f}")
        print(f"  Compliance: {scores.get('compliance', 0):.3f}")
        
    elif args.import_file:
        # JSON-Import aus VPB-Datei
        from uds3_vpb_schema import migrate_legacy_vpb_data
        
        try:
            with open(args.import_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            process = migrate_legacy_vpb_data(data)
            if db.save_process(process):
                print(f"✅ Prozess importiert: {process.process_id} - {process.name}")
            else:
                print("❌ Import fehlgeschlagen")
                
        except Exception as e:
            print(f"❌ Import-Fehler: {e}")
            
    elif args.export_id:
        process = db.load_process(args.export_id)
        if process:
            export_data = process.to_dict()
            filename = f"{args.export_id}_export.vpb.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                
            print(f"✅ Prozess exportiert: {filename}")
        else:
            print(f"❌ Prozess nicht gefunden: {args.export_id}")
            
    else:
        parser.print_help()
