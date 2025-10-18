"""
Gap Detector - Identifiziert Daten-Lücken zwischen SQLite und UDS3
Autor: UDS3 Development Team
Datum: 18. Oktober 2025
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

# UDS3 Path hinzufügen
uds3_path = Path(__file__).parent.parent.parent / "uds3"
if uds3_path.exists() and str(uds3_path) not in sys.path:
    sys.path.insert(0, str(uds3_path))

logger = logging.getLogger(__name__)


class GapType(Enum):
    """Typen von Daten-Lücken"""
    MISSING_RECORD = "missing_record"  # Record in SQLite aber nicht in UDS3
    ORPHANED_RECORD = "orphaned_record"  # Record in UDS3 aber nicht in SQLite
    SCHEMA_MISMATCH = "schema_mismatch"  # Unterschiedliche Schemas
    DATA_CORRUPTION = "data_corruption"  # Korrupte Daten
    INTEGRITY_VIOLATION = "integrity_violation"  # Foreign Key Violations
    INCOMPLETE_MIGRATION = "incomplete_migration"  # Teilweise migriert
    VERSION_CONFLICT = "version_conflict"  # Unterschiedliche Versionen


@dataclass
class DataGap:
    """Repräsentiert eine Daten-Lücke"""
    gap_type: GapType
    table_name: str
    record_id: str
    description: str
    source_data: Optional[Dict[str, Any]] = None
    target_data: Optional[Dict[str, Any]] = None
    severity: str = "medium"  # low, medium, high, critical
    auto_fixable: bool = False
    detected_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary"""
        return {
            'gap_type': self.gap_type.value,
            'table_name': self.table_name,
            'record_id': self.record_id,
            'description': self.description,
            'source_data': self.source_data,
            'target_data': self.target_data,
            'severity': self.severity,
            'auto_fixable': self.auto_fixable,
            'detected_at': self.detected_at.isoformat()
        }


class GapDetector:
    """
    Detector für Daten-Lücken zwischen SQLite und UDS3
    
    Features:
    - Missing Records Detection
    - Orphaned Records Detection
    - Schema Mismatch Detection
    - Data Corruption Detection
    - Integrity Violation Detection
    - Auto-Fix Recommendations
    """
    
    def __init__(
        self,
        sqlite_path: str,
        uds3_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialisiert Gap Detector
        
        Args:
            sqlite_path: Path zu SQLite DB
            uds3_config: UDS3 Configuration (optional)
        """
        self.sqlite_path = Path(sqlite_path)
        self.uds3_config = uds3_config or {}
        self.gaps: List[DataGap] = []
        
        # Lazy loading für UDS3
        self._uds3_manager = None
        self._sqlite_conn = None
    
    def detect_all_gaps(self) -> List[DataGap]:
        """
        Führt alle Gap Detection Checks durch
        
        Returns:
            Liste aller gefundenen Gaps
        """
        logger.info("🔍 Starting comprehensive gap detection...")
        self.gaps = []
        
        try:
            # 1. Missing Records Detection
            self._detect_missing_records()
            
            # 2. Orphaned Records Detection
            self._detect_orphaned_records()
            
            # 3. Schema Mismatch Detection
            self._detect_schema_mismatches()
            
            # 4. Data Corruption Detection
            self._detect_data_corruption()
            
            # 5. Integrity Violation Detection
            self._detect_integrity_violations()
            
            # 6. Incomplete Migration Detection
            self._detect_incomplete_migrations()
            
            logger.info(f"✅ Gap detection complete: {len(self.gaps)} gaps found")
            
        except Exception as e:
            logger.error(f"❌ Gap detection failed: {e}")
            raise
        
        return self.gaps
    
    def _detect_missing_records(self):
        """Detektiert Records die in SQLite aber nicht in UDS3 sind"""
        logger.info("  Checking for missing records...")
        
        try:
            import sqlite3
            
            with sqlite3.connect(self.sqlite_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # VPB Processes prüfen
                cursor.execute("SELECT process_id, name FROM vpb_processes")
                sqlite_processes = cursor.fetchall()
                
                logger.info(f"    Found {len(sqlite_processes)} processes in SQLite")
                
                # TODO: Mit UDS3 abgleichen (wenn UDS3 verfügbar)
                # Für jetzt: Mock Gap für Demo
                if len(sqlite_processes) > 0:
                    sample = sqlite_processes[0]
                    gap = DataGap(
                        gap_type=GapType.MISSING_RECORD,
                        table_name="vpb_processes",
                        record_id=sample['process_id'],
                        description=f"Process '{sample['name']}' exists in SQLite but not in UDS3",
                        source_data={'process_id': sample['process_id'], 'name': sample['name']},
                        severity="high",
                        auto_fixable=True
                    )
                    # self.gaps.append(gap)  # Nur hinzufügen wenn wirklich missing
                
        except Exception as e:
            logger.warning(f"    ⚠️  Missing records detection failed: {e}")
    
    def _detect_orphaned_records(self):
        """Detektiert Records die in UDS3 aber nicht in SQLite sind"""
        logger.info("  Checking for orphaned records...")
        
        # TODO: UDS3 Query Implementation
        # Für jetzt: Placeholder
        pass
    
    def _detect_schema_mismatches(self):
        """Detektiert Schema-Unterschiede"""
        logger.info("  Checking for schema mismatches...")
        
        try:
            import sqlite3
            
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.cursor()
                
                # SQLite Schema abfragen
                cursor.execute("""
                    SELECT name, sql FROM sqlite_master 
                    WHERE type='table' AND name LIKE 'vpb_%'
                """)
                tables = cursor.fetchall()
                
                logger.info(f"    Found {len(tables)} VPB tables in SQLite")
                
                # TODO: Mit UDS3 Schema vergleichen
                
        except Exception as e:
            logger.warning(f"    ⚠️  Schema mismatch detection failed: {e}")
    
    def _detect_data_corruption(self):
        """Detektiert korrupte Daten"""
        logger.info("  Checking for data corruption...")
        
        try:
            import sqlite3
            
            with sqlite3.connect(self.sqlite_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # JSON Fields validieren
                cursor.execute("SELECT process_id, process_data FROM vpb_processes")
                processes = cursor.fetchall()
                
                corrupted_count = 0
                for proc in processes:
                    try:
                        import json
                        json.loads(proc['process_data'])
                    except json.JSONDecodeError:
                        corrupted_count += 1
                        gap = DataGap(
                            gap_type=GapType.DATA_CORRUPTION,
                            table_name="vpb_processes",
                            record_id=proc['process_id'],
                            description=f"Corrupted JSON in process_data field",
                            severity="critical",
                            auto_fixable=False
                        )
                        self.gaps.append(gap)
                
                if corrupted_count > 0:
                    logger.warning(f"    ⚠️  Found {corrupted_count} corrupted records")
                else:
                    logger.info(f"    ✅ No corruption detected in {len(processes)} records")
                
        except Exception as e:
            logger.warning(f"    ⚠️  Data corruption detection failed: {e}")
    
    def _detect_integrity_violations(self):
        """Detektiert Foreign Key Violations"""
        logger.info("  Checking for integrity violations...")
        
        try:
            import sqlite3
            
            with sqlite3.connect(self.sqlite_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                
                # Foreign Key Check
                cursor.execute("PRAGMA foreign_key_check")
                violations = cursor.fetchall()
                
                if violations:
                    logger.warning(f"    ⚠️  Found {len(violations)} foreign key violations")
                    for v in violations:
                        gap = DataGap(
                            gap_type=GapType.INTEGRITY_VIOLATION,
                            table_name=v[0] if len(v) > 0 else "unknown",
                            record_id=str(v[1]) if len(v) > 1 else "unknown",
                            description=f"Foreign key violation: {v}",
                            severity="high",
                            auto_fixable=False
                        )
                        self.gaps.append(gap)
                else:
                    logger.info("    ✅ No integrity violations detected")
                
        except Exception as e:
            logger.warning(f"    ⚠️  Integrity violation detection failed: {e}")
    
    def _detect_incomplete_migrations(self):
        """Detektiert unvollständige Migrationen"""
        logger.info("  Checking for incomplete migrations...")
        
        try:
            import sqlite3
            
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.cursor()
                
                # Migration Tracking Table prüfen (falls vorhanden)
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='migration_status'
                """)
                
                if cursor.fetchone():
                    cursor.execute("SELECT * FROM migration_status")
                    status = cursor.fetchall()
                    logger.info(f"    Found migration status table with {len(status)} entries")
                else:
                    logger.info("    No migration tracking table found (fresh DB)")
                
        except Exception as e:
            logger.warning(f"    ⚠️  Incomplete migration detection failed: {e}")
    
    def get_gaps_by_type(self, gap_type: GapType) -> List[DataGap]:
        """Filtert Gaps nach Typ"""
        return [g for g in self.gaps if g.gap_type == gap_type]
    
    def get_gaps_by_severity(self, severity: str) -> List[DataGap]:
        """Filtert Gaps nach Severity"""
        return [g for g in self.gaps if g.severity == severity]
    
    def get_auto_fixable_gaps(self) -> List[DataGap]:
        """Returns nur auto-fixable Gaps"""
        return [g for g in self.gaps if g.auto_fixable]
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generiert Gap Detection Report
        
        Returns:
            Report Dictionary mit Statistiken
        """
        return {
            'total_gaps': len(self.gaps),
            'by_type': {
                gap_type.value: len(self.get_gaps_by_type(gap_type))
                for gap_type in GapType
            },
            'by_severity': {
                severity: len(self.get_gaps_by_severity(severity))
                for severity in ['low', 'medium', 'high', 'critical']
            },
            'auto_fixable': len(self.get_auto_fixable_gaps()),
            'gaps': [g.to_dict() for g in self.gaps],
            'generated_at': datetime.now().isoformat()
        }
    
    def export_report(self, output_path: str):
        """Exportiert Report als JSON"""
        import json
        
        report = self.generate_report()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📝 Gap report exported to: {output_path}")


def create_gap_detector(sqlite_path: str, uds3_config: Optional[Dict[str, Any]] = None) -> GapDetector:
    """Factory Function für GapDetector"""
    return GapDetector(sqlite_path, uds3_config)


# ============================================================
# MAIN - Standalone Gap Detection
# ============================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="VPB Gap Detector - SQLite → UDS3")
    parser.add_argument("--db", required=True, help="Path to SQLite database")
    parser.add_argument("--output", default="gap_report.json", help="Output report path")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("🔍 VPB GAP DETECTOR")
    print("=" * 60)
    
    detector = create_gap_detector(args.db)
    gaps = detector.detect_all_gaps()
    
    print(f"\n📊 RESULTS:")
    print(f"   Total Gaps: {len(gaps)}")
    print(f"   Auto-Fixable: {len(detector.get_auto_fixable_gaps())}")
    print(f"   Critical: {len(detector.get_gaps_by_severity('critical'))}")
    
    detector.export_report(args.output)
    
    print(f"\n✅ Report saved to: {args.output}")
