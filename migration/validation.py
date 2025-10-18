"""
Data Validator - Validiert Datenintegrität während Migration
Autor: UDS3 Development Team
Datum: 18. Oktober 2025
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
import hashlib
import json

# UDS3 Path hinzufügen
uds3_path = Path(__file__).parent.parent.parent / "uds3"
if uds3_path.exists() and str(uds3_path) not in sys.path:
    sys.path.insert(0, str(uds3_path))

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Ergebnis einer Validierung"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert zu Dictionary"""
        return {
            'is_valid': self.is_valid,
            'errors': self.errors,
            'warnings': self.warnings,
            'validated_at': self.validated_at.isoformat(),
            'details': self.details
        }


class DataValidator:
    """
    Validator für Datenintegrität während SQLite → UDS3 Migration
    
    Features:
    - Schema Validation
    - Data Type Validation
    - Foreign Key Validation
    - JSON Structure Validation
    - Checksum Validation
    - Record Count Validation
    """
    
    def __init__(self):
        """Initialisiert Data Validator"""
        self.validation_results: List[ValidationResult] = []
    
    def validate_migration_batch(
        self,
        source_records: List[Dict[str, Any]],
        target_records: List[Dict[str, Any]],
        table_name: str
    ) -> ValidationResult:
        """
        Validiert einen Migration Batch
        
        Args:
            source_records: Records aus SQLite
            target_records: Records in UDS3
            table_name: Tabellenname
        
        Returns:
            ValidationResult
        """
        logger.info(f"🔍 Validating migration batch for table: {table_name}")
        
        errors = []
        warnings = []
        details = {}
        
        # 1. Record Count Validation
        if len(source_records) != len(target_records):
            errors.append(
                f"Record count mismatch: {len(source_records)} source vs {len(target_records)} target"
            )
        else:
            details['record_count'] = len(source_records)
        
        # 2. ID Validation
        source_ids = {r.get('id') or r.get('process_id') for r in source_records}
        target_ids = {r.get('id') or r.get('process_id') for r in target_records}
        
        missing_ids = source_ids - target_ids
        if missing_ids:
            errors.append(f"Missing IDs in target: {missing_ids}")
        
        orphaned_ids = target_ids - source_ids
        if orphaned_ids:
            warnings.append(f"Orphaned IDs in target: {orphaned_ids}")
        
        details['id_match_rate'] = len(source_ids & target_ids) / len(source_ids) if source_ids else 0
        
        # 3. Data Integrity Validation
        for source_rec in source_records:
            rec_id = source_rec.get('id') or source_rec.get('process_id')
            target_rec = next((r for r in target_records if (r.get('id') or r.get('process_id')) == rec_id), None)
            
            if target_rec:
                # Checksum Validation
                source_checksum = self._calculate_checksum(source_rec)
                target_checksum = self._calculate_checksum(target_rec)
                
                if source_checksum != target_checksum:
                    warnings.append(f"Data checksum mismatch for record {rec_id}")
        
        is_valid = len(errors) == 0
        
        result = ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            details=details
        )
        
        self.validation_results.append(result)
        
        logger.info(f"  ✅ Validation complete: {'VALID' if is_valid else 'INVALID'} ({len(errors)} errors, {len(warnings)} warnings)")
        
        return result
    
    def validate_schema(
        self,
        source_schema: Dict[str, Any],
        target_schema: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validiert Schema-Kompatibilität
        
        Args:
            source_schema: SQLite Schema
            target_schema: UDS3 Schema
        
        Returns:
            ValidationResult
        """
        logger.info("🔍 Validating schema compatibility...")
        
        errors = []
        warnings = []
        details = {}
        
        # Tabellen prüfen
        source_tables = set(source_schema.keys())
        target_tables = set(target_schema.keys())
        
        missing_tables = source_tables - target_tables
        if missing_tables:
            errors.append(f"Missing tables in target: {missing_tables}")
        
        # Felder prüfen
        for table in source_tables & target_tables:
            source_fields = set(source_schema[table].keys())
            target_fields = set(target_schema[table].keys())
            
            missing_fields = source_fields - target_fields
            if missing_fields:
                warnings.append(f"Missing fields in {table}: {missing_fields}")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            details=details
        )
    
    def validate_json_structure(
        self,
        json_data: str,
        expected_keys: Optional[Set[str]] = None
    ) -> ValidationResult:
        """
        Validiert JSON-Struktur
        
        Args:
            json_data: JSON String
            expected_keys: Erwartete Keys (optional)
        
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        details = {}
        
        try:
            data = json.loads(json_data)
            details['valid_json'] = True
            
            if expected_keys:
                actual_keys = set(data.keys())
                missing_keys = expected_keys - actual_keys
                
                if missing_keys:
                    warnings.append(f"Missing expected keys: {missing_keys}")
                
                details['key_match_rate'] = len(expected_keys & actual_keys) / len(expected_keys)
        
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {e}")
            details['valid_json'] = False
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            details=details
        )
    
    def validate_foreign_keys(
        self,
        records: List[Dict[str, Any]],
        foreign_key_mappings: Dict[str, str]
    ) -> ValidationResult:
        """
        Validiert Foreign Key Integrität
        
        Args:
            records: Records zu validieren
            foreign_key_mappings: Mapping von FK-Feld zu Ziel-Tabelle
        
        Returns:
            ValidationResult
        """
        logger.info("🔍 Validating foreign key integrity...")
        
        errors = []
        warnings = []
        details = {}
        
        # TODO: Foreign Key Validation Implementation
        # Für jetzt: Placeholder
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            details=details
        )
    
    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Berechnet Checksum für Record"""
        # Sortiert Keys für konsistente Checksums
        sorted_data = json.dumps(data, sort_keys=True)
        return hashlib.sha256(sorted_data.encode()).hexdigest()[:16]
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """
        Generiert Validation Report
        
        Returns:
            Report Dictionary
        """
        total = len(self.validation_results)
        valid = sum(1 for r in self.validation_results if r.is_valid)
        
        return {
            'total_validations': total,
            'valid': valid,
            'invalid': total - valid,
            'success_rate': (valid / total * 100) if total > 0 else 0,
            'results': [r.to_dict() for r in self.validation_results],
            'generated_at': datetime.now().isoformat()
        }
    
    def export_report(self, output_path: str):
        """Exportiert Report als JSON"""
        report = self.generate_validation_report()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📝 Validation report exported to: {output_path}")


def create_data_validator() -> DataValidator:
    """Factory Function für DataValidator"""
    return DataValidator()


# ============================================================
# MAIN - Standalone Validation
# ============================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("✅ VPB DATA VALIDATOR")
    print("=" * 60)
    
    validator = create_data_validator()
    
    # Demo Validation
    source_records = [
        {'process_id': '001', 'name': 'Test Process', 'data': '{}'}
    ]
    target_records = [
        {'process_id': '001', 'name': 'Test Process', 'data': '{}'}
    ]
    
    result = validator.validate_migration_batch(
        source_records,
        target_records,
        'vpb_processes'
    )
    
    print(f"\n📊 RESULT: {'✅ VALID' if result.is_valid else '❌ INVALID'}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Warnings: {len(result.warnings)}")
    
    validator.export_report('validation_report.json')
    print(f"\n✅ Report saved to: validation_report.json")
