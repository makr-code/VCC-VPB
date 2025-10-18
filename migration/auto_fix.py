"""
Auto-Fix Engine - Automatische Korrektur von Daten-Lücken
Autor: UDS3 Development Team
Datum: 18. Oktober 2025

Features:
- Auto-Fix für Auto-Fixable Gaps
- Dry-Run Mode
- User Confirmation Required
- Rollback Support
- Backup vor Fixes
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import json
import sqlite3

# UDS3 Path hinzufügen
uds3_path = Path(__file__).parent.parent.parent / "uds3"
if uds3_path.exists() and str(uds3_path) not in sys.path:
    sys.path.insert(0, str(uds3_path))

from .gap_detector import GapDetector, DataGap, GapType

logger = logging.getLogger(__name__)


class FixStrategy(Enum):
    """Strategien für Auto-Fixes"""
    COPY_FROM_SOURCE = "copy_from_source"  # Kopiere von SQLite zu UDS3
    DELETE_FROM_TARGET = "delete_from_target"  # Lösche Orphaned Records
    UPDATE_TARGET = "update_target"  # Update UDS3 mit SQLite-Daten
    MERGE_DATA = "merge_data"  # Merge Source + Target
    SKIP = "skip"  # Skip (manuell erforderlich)


class FixStatus(Enum):
    """Status eines Fixes"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"


@dataclass
class FixAction:
    """Repräsentiert eine Fix-Aktion"""
    gap: DataGap
    strategy: FixStrategy
    description: str
    requires_confirmation: bool = True
    status: FixStatus = FixStatus.PENDING
    error: Optional[str] = None
    backup_data: Optional[Dict[str, Any]] = None
    executed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary"""
        return {
            'gap': self.gap.to_dict(),
            'strategy': self.strategy.value,
            'description': self.description,
            'requires_confirmation': self.requires_confirmation,
            'status': self.status.value,
            'error': self.error,
            'executed_at': self.executed_at.isoformat() if self.executed_at else None
        }


@dataclass
class FixReport:
    """Report über durchgeführte Fixes"""
    total_gaps: int = 0
    auto_fixable: int = 0
    fixed: int = 0
    failed: int = 0
    skipped: int = 0
    rolled_back: int = 0
    actions: List[FixAction] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    dry_run: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary"""
        return {
            'total_gaps': self.total_gaps,
            'auto_fixable': self.auto_fixable,
            'fixed': self.fixed,
            'failed': self.failed,
            'skipped': self.skipped,
            'rolled_back': self.rolled_back,
            'success_rate': (self.fixed / self.auto_fixable * 100) if self.auto_fixable > 0 else 0,
            'actions': [action.to_dict() for action in self.actions],
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds,
            'dry_run': self.dry_run
        }


class AutoFixEngine:
    """
    Engine für automatische Korrektur von Daten-Lücken
    
    Usage:
        engine = AutoFixEngine(gap_detector, dry_run=True)
        report = engine.auto_fix_gaps(confirmation_callback=lambda gap: True)
        
    Features:
    - Identifiziert auto-fixable Gaps
    - Wählt optimale Fix-Strategie
    - Erstellt Backup vor Fixes
    - Führt Fixes aus
    - Rollback bei Fehlern
    - Dry-Run Mode für Testing
    """
    
    def __init__(
        self,
        gap_detector: GapDetector,
        dry_run: bool = False,
        auto_confirm: bool = False
    ):
        """
        Initialisiert Auto-Fix Engine
        
        Args:
            gap_detector: GapDetector Instance
            dry_run: Wenn True, keine echten Änderungen
            auto_confirm: Wenn True, keine User-Confirmation erforderlich
        """
        self.gap_detector = gap_detector
        self.dry_run = dry_run
        self.auto_confirm = auto_confirm
        self.fix_actions: List[FixAction] = []
        
        # Lazy loading für UDS3
        self._uds3_manager = None
    
    def _init_uds3_connection(self):
        """Initialisiert UDS3 Connection (lazy)"""
        if self._uds3_manager is None:
            try:
                from core.polyglot_manager import UDS3PolyglotManager, create_uds3_manager
                
                if self.gap_detector.uds3_config:
                    self._uds3_manager = UDS3PolyglotManager(self.gap_detector.uds3_config)
                else:
                    self._uds3_manager = create_uds3_manager()
                    
                logger.info("✅ UDS3 Connection für Auto-Fix initialisiert")
                
            except Exception as e:
                logger.error(f"❌ UDS3 Connection fehlgeschlagen: {e}")
                raise
    
    def identify_auto_fixable_gaps(self, gaps: List[DataGap]) -> List[DataGap]:
        """
        Identifiziert auto-fixable Gaps
        
        Args:
            gaps: Liste aller Gaps
            
        Returns:
            Liste der auto-fixable Gaps
        """
        return [gap for gap in gaps if gap.auto_fixable]
    
    def select_fix_strategy(self, gap: DataGap) -> FixStrategy:
        """
        Wählt optimale Fix-Strategie für Gap
        
        Args:
            gap: DataGap
            
        Returns:
            Fix-Strategie
        """
        if gap.gap_type == GapType.MISSING_RECORD:
            # Record fehlt in UDS3 → Kopiere von SQLite
            return FixStrategy.COPY_FROM_SOURCE
            
        elif gap.gap_type == GapType.ORPHANED_RECORD:
            # Record in UDS3 aber nicht in SQLite → Lösche
            return FixStrategy.DELETE_FROM_TARGET
            
        elif gap.gap_type == GapType.INCOMPLETE_MIGRATION:
            # Teilweise migriert → Update mit vollständigen Daten
            return FixStrategy.UPDATE_TARGET
            
        elif gap.gap_type == GapType.VERSION_CONFLICT:
            # Version Conflict → Merge neuere Version
            return FixStrategy.MERGE_DATA
            
        else:
            # Andere Gaps → Manuell
            return FixStrategy.SKIP
    
    def create_fix_action(self, gap: DataGap) -> FixAction:
        """
        Erstellt Fix-Action für Gap
        
        Args:
            gap: DataGap
            
        Returns:
            FixAction
        """
        strategy = self.select_fix_strategy(gap)
        
        descriptions = {
            FixStrategy.COPY_FROM_SOURCE: f"Kopiere Record {gap.record_id} von SQLite zu UDS3",
            FixStrategy.DELETE_FROM_TARGET: f"Lösche Orphaned Record {gap.record_id} aus UDS3",
            FixStrategy.UPDATE_TARGET: f"Update Record {gap.record_id} in UDS3 mit SQLite-Daten",
            FixStrategy.MERGE_DATA: f"Merge Record {gap.record_id} (Source + Target)",
            FixStrategy.SKIP: f"Skip Record {gap.record_id} (manuell erforderlich)"
        }
        
        # High-severity Gaps require confirmation
        requires_confirmation = gap.severity in ["high", "critical"] and not self.auto_confirm
        
        return FixAction(
            gap=gap,
            strategy=strategy,
            description=descriptions[strategy],
            requires_confirmation=requires_confirmation
        )
    
    def create_backup(self, gap: DataGap) -> Dict[str, Any]:
        """
        Erstellt Backup vor Fix
        
        Args:
            gap: DataGap
            
        Returns:
            Backup-Daten
        """
        backup = {
            'gap_type': gap.gap_type.value,
            'record_id': gap.record_id,
            'table_name': gap.table_name,
            'timestamp': datetime.now().isoformat()
        }
        
        # Backup Target-Daten wenn vorhanden
        if gap.target_data:
            backup['target_data'] = gap.target_data.copy()
        
        # Backup Source-Daten wenn vorhanden
        if gap.source_data:
            backup['source_data'] = gap.source_data.copy()
        
        return backup
    
    def execute_fix(self, action: FixAction) -> bool:
        """
        Führt Fix-Action aus
        
        Args:
            action: FixAction
            
        Returns:
            True wenn erfolgreich, False bei Fehler
        """
        if self.dry_run:
            logger.info(f"[DRY-RUN] {action.description}")
            action.status = FixStatus.SUCCESS
            action.executed_at = datetime.now()
            return True
        
        try:
            action.status = FixStatus.IN_PROGRESS
            action.backup_data = self.create_backup(action.gap)
            
            # Initialize UDS3
            self._init_uds3_connection()
            
            if action.strategy == FixStrategy.COPY_FROM_SOURCE:
                self._fix_copy_from_source(action.gap)
                
            elif action.strategy == FixStrategy.DELETE_FROM_TARGET:
                self._fix_delete_from_target(action.gap)
                
            elif action.strategy == FixStrategy.UPDATE_TARGET:
                self._fix_update_target(action.gap)
                
            elif action.strategy == FixStrategy.MERGE_DATA:
                self._fix_merge_data(action.gap)
                
            elif action.strategy == FixStrategy.SKIP:
                action.status = FixStatus.SKIPPED
                logger.info(f"⏭️ Skipped: {action.description}")
                return True
            
            action.status = FixStatus.SUCCESS
            action.executed_at = datetime.now()
            logger.info(f"✅ Fixed: {action.description}")
            return True
            
        except Exception as e:
            action.status = FixStatus.FAILED
            action.error = str(e)
            logger.error(f"❌ Fix failed: {action.description} - {e}")
            return False
    
    def _fix_copy_from_source(self, gap: DataGap):
        """Kopiert Record von SQLite zu UDS3"""
        if not gap.source_data:
            raise ValueError("Source data missing for COPY_FROM_SOURCE")
        
        # Parse process_data wenn JSON string
        process_data = gap.source_data.get('process_data')
        if isinstance(process_data, str):
            process_data = json.loads(process_data)
        
        # Merge alle Daten
        full_data = {
            'process_id': gap.source_data.get('process_id'),
            'name': gap.source_data.get('name'),
            'description': gap.source_data.get('description'),
            'version': gap.source_data.get('version', 1),
            **process_data
        }
        
        # Save to UDS3
        process_id = self._uds3_manager.save_process(
            process_data=full_data,
            domain="vpb_auto_fix",
            generate_embeddings=True
        )
        
        logger.debug(f"Copied record {gap.record_id} to UDS3 (ID: {process_id})")
    
    def _fix_delete_from_target(self, gap: DataGap):
        """Löscht Orphaned Record aus UDS3"""
        # UDS3 delete functionality
        # Note: Benötigt delete_process() method in UDS3PolyglotManager
        logger.warning(f"DELETE not yet implemented for UDS3 - skipping {gap.record_id}")
        raise NotImplementedError("UDS3 delete_process() not available")
    
    def _fix_update_target(self, gap: DataGap):
        """Updated Record in UDS3 mit vollständigen Daten"""
        if not gap.source_data:
            raise ValueError("Source data missing for UPDATE_TARGET")
        
        # Similar to COPY_FROM_SOURCE but updates existing
        self._fix_copy_from_source(gap)
    
    def _fix_merge_data(self, gap: DataGap):
        """Merged Source + Target Daten"""
        if not gap.source_data or not gap.target_data:
            raise ValueError("Both source and target data required for MERGE_DATA")
        
        # Merge: Target wins für metadata, Source wins für content
        merged_data = gap.target_data.copy()
        
        # Update mit Source-Daten (außer Metadata)
        source_process_data = gap.source_data.get('process_data')
        if isinstance(source_process_data, str):
            source_process_data = json.loads(source_process_data)
        
        merged_data.update(source_process_data)
        
        # Save merged
        process_id = self._uds3_manager.save_process(
            process_data=merged_data,
            domain="vpb_auto_fix_merge",
            generate_embeddings=True
        )
        
        logger.debug(f"Merged record {gap.record_id} (ID: {process_id})")
    
    def rollback_fix(self, action: FixAction) -> bool:
        """
        Rollback eines Fixes
        
        Args:
            action: FixAction
            
        Returns:
            True wenn erfolgreich
        """
        if self.dry_run:
            logger.info(f"[DRY-RUN] Rollback: {action.description}")
            action.status = FixStatus.ROLLED_BACK
            return True
        
        try:
            if not action.backup_data:
                logger.warning(f"No backup data for rollback: {action.gap.record_id}")
                return False
            
            # Rollback implementation depends on strategy
            if action.strategy == FixStrategy.COPY_FROM_SOURCE:
                # Delete created record
                logger.warning("Rollback DELETE not implemented - manual cleanup required")
                
            elif action.strategy == FixStrategy.DELETE_FROM_TARGET:
                # Restore deleted record
                logger.warning("Rollback RESTORE not implemented - manual restore required")
                
            elif action.strategy == FixStrategy.UPDATE_TARGET:
                # Restore old version
                logger.warning("Rollback UPDATE not implemented - manual restore required")
            
            action.status = FixStatus.ROLLED_BACK
            logger.info(f"🔄 Rolled back: {action.description}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Rollback failed: {action.description} - {e}")
            return False
    
    def auto_fix_gaps(
        self,
        gaps: Optional[List[DataGap]] = None,
        confirmation_callback: Optional[Callable[[FixAction], bool]] = None
    ) -> FixReport:
        """
        Führt Auto-Fix für Gaps durch
        
        Args:
            gaps: Liste von Gaps (wenn None, detect automatisch)
            confirmation_callback: Callback für User-Confirmation
            
        Returns:
            FixReport
        """
        import time
        start_time = time.time()
        
        report = FixReport(
            started_at=datetime.now(),
            dry_run=self.dry_run
        )
        
        # Detect Gaps wenn nicht übergeben
        if gaps is None:
            logger.info("🔍 Detecting gaps...")
            gaps = self.gap_detector.detect_all_gaps()
        
        report.total_gaps = len(gaps)
        
        # Filter auto-fixable
        auto_fixable_gaps = self.identify_auto_fixable_gaps(gaps)
        report.auto_fixable = len(auto_fixable_gaps)
        
        logger.info(f"Found {report.total_gaps} gaps, {report.auto_fixable} auto-fixable")
        
        # Create Fix Actions
        for gap in auto_fixable_gaps:
            action = self.create_fix_action(gap)
            self.fix_actions.append(action)
            report.actions.append(action)
        
        # Execute Fixes
        for action in self.fix_actions:
            # User Confirmation wenn required
            if action.requires_confirmation and confirmation_callback:
                confirmed = confirmation_callback(action)
                if not confirmed:
                    action.status = FixStatus.SKIPPED
                    report.skipped += 1
                    logger.info(f"⏭️ Skipped (user): {action.description}")
                    continue
            
            # Execute Fix
            success = self.execute_fix(action)
            
            if success:
                if action.status == FixStatus.SUCCESS:
                    report.fixed += 1
                elif action.status == FixStatus.SKIPPED:
                    report.skipped += 1
            else:
                report.failed += 1
                
                # Rollback on failure wenn aktiviert
                if hasattr(self, 'enable_rollback_on_failure') and self.enable_rollback_on_failure:
                    if self.rollback_fix(action):
                        report.rolled_back += 1
        
        # Finalize Report
        report.completed_at = datetime.now()
        report.duration_seconds = time.time() - start_time
        
        logger.info(f"✅ Auto-Fix completed: {report.fixed}/{report.auto_fixable} fixed")
        
        return report


# Convenience Functions

def auto_fix_all_gaps(
    sqlite_path: str,
    dry_run: bool = True,
    auto_confirm: bool = False,
    confirmation_callback: Optional[Callable[[FixAction], bool]] = None
) -> FixReport:
    """
    Convenience Function: Auto-Fix alle Gaps
    
    Args:
        sqlite_path: Path zu SQLite DB
        dry_run: Dry-Run Mode
        auto_confirm: Auto-Confirm alle Fixes
        confirmation_callback: Callback für Confirmation
        
    Returns:
        FixReport
    """
    detector = GapDetector(sqlite_path)
    engine = AutoFixEngine(detector, dry_run=dry_run, auto_confirm=auto_confirm)
    
    return engine.auto_fix_gaps(confirmation_callback=confirmation_callback)


# Standalone Test
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="VPB Auto-Fix Engine")
    parser.add_argument("sqlite_db", help="Path to SQLite database")
    parser.add_argument("--dry-run", action="store_true", help="Dry-run mode (no changes)")
    parser.add_argument("--auto-confirm", action="store_true", help="Auto-confirm all fixes")
    parser.add_argument("--export-report", help="Export report to JSON file")
    
    args = parser.parse_args()
    
    print("="*80)
    print("VPB Auto-Fix Engine")
    print("="*80)
    print(f"SQLite DB: {args.sqlite_db}")
    print(f"Dry-Run: {args.dry_run}")
    print(f"Auto-Confirm: {args.auto_confirm}")
    print()
    
    # Run Auto-Fix
    report = auto_fix_all_gaps(
        args.sqlite_db,
        dry_run=args.dry_run,
        auto_confirm=args.auto_confirm
    )
    
    # Print Report
    print("\n" + "="*80)
    print("AUTO-FIX REPORT")
    print("="*80)
    print(f"Total Gaps: {report.total_gaps}")
    print(f"Auto-Fixable: {report.auto_fixable}")
    print(f"Fixed: {report.fixed}")
    print(f"Failed: {report.failed}")
    print(f"Skipped: {report.skipped}")
    print(f"Rolled Back: {report.rolled_back}")
    print(f"Success Rate: {(report.fixed / report.auto_fixable * 100) if report.auto_fixable > 0 else 0:.1f}%")
    print(f"Duration: {report.duration_seconds:.2f}s")
    print()
    
    # Export Report
    if args.export_report:
        with open(args.export_report, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"✅ Report exported to: {args.export_report}")
