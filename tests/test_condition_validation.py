"""
Tests für CONDITION Element Validierung.

Testet die ConditionValidator-Klasse und deren Integration in den
Validierungs-Service.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vpb.models.element import VPBElement, ConditionCheck
from vpb.models.document import VPBDocument
from vpb.services.validation_service import ValidationService, ConditionValidator, ValidationResult


def test_condition_validation_no_checks():
    """Test: CONDITION ohne Checks -> ERROR."""
    print("\n=== Test 1: CONDITION ohne Checks ===")
    
    doc = VPBDocument()
    condition = VPBElement(
        element_id="cond_1",
        element_type="CONDITION",
        label="Empty Condition",
        condition_checks=[]
    )
    doc.add_element(condition)
    
    validator = ConditionValidator()
    result = ValidationResult()
    validator.validate_condition(condition, doc, result)
    
    errors = [e for e in result.issues if e.severity == "error" and e.category == "condition"]
    assert len(errors) >= 1, "Sollte mindestens einen Fehler haben"
    assert any("at least 1 check" in e.message for e in errors), "Fehler sollte 'at least 1 check' enthalten"
    print(f"✓ Fehler erkannt: {errors[0].message}")


def test_condition_validation_invalid_operator():
    """Test: CONDITION mit ungültigem Operator -> ERROR."""
    print("\n=== Test 2: CONDITION mit ungültigem Operator ===")
    
    doc = VPBDocument()
    condition = VPBElement(
        element_id="cond_2",
        element_type="CONDITION",
        label="Invalid Operator Condition",
        condition_checks=[
            {"field": "status", "operator": "INVALID", "value": "active", "check_type": "string"}
        ]
    )
    doc.add_element(condition)
    
    validator = ConditionValidator()
    result = ValidationResult()
    validator.validate_condition(condition, doc, result)
    
    errors = [e for e in result.issues if e.severity == "error" and e.category == "condition"]
    assert any("Invalid operator" in e.message for e in errors), "Sollte 'Invalid operator' Fehler haben"
    print(f"✓ Fehler erkannt: {[e.message for e in errors if 'Invalid operator' in e.message][0]}")


def test_condition_validation_valid_operators():
    """Test: CONDITION mit allen gültigen Operatoren -> OK."""
    print("\n=== Test 3: CONDITION mit gültigen Operatoren ===")
    
    doc = VPBDocument()
    valid_operators = ["==", "!=", "<", ">", "<=", ">=", "contains", "regex"]
    
    for idx, op in enumerate(valid_operators):
        condition = VPBElement(
            element_id=f"cond_{idx}",
            element_type="CONDITION",
            label=f"Condition {op}",
            condition_checks=[
                {"field": "value", "operator": op, "value": "test", "check_type": "string"}
            ]
        )
        doc.add_element(condition)
        
        validator = ConditionValidator()
        result = ValidationResult()
        validator.validate_condition(condition, doc, result)
        
        errors = [e for e in result.issues if e.severity == "error" and "Invalid operator" in e.message]
        assert len(errors) == 0, f"Operator '{op}' sollte gültig sein"
        print(f"✓ Operator '{op}' ist gültig")


def test_condition_validation_missing_true_target():
    """Test: CONDITION ohne TRUE-Target -> WARNING."""
    print("\n=== Test 4: CONDITION ohne TRUE-Target ===")
    
    doc = VPBDocument()
    condition = VPBElement(
        element_id="cond_4",
        element_type="CONDITION",
        label="No TRUE Target",
        condition_checks=[
            {"field": "status", "operator": "==", "value": "active", "check_type": "string"}
        ],
        condition_true_target="",
        condition_false_target=""
    )
    doc.add_element(condition)
    
    validator = ConditionValidator()
    result = ValidationResult()
    validator.validate_condition(condition, doc, result)
    
    warnings = [w for w in result.issues if w.severity == "warning" and w.category == "condition"]
    assert any("TRUE target" in w.message for w in warnings), "Sollte WARNING für fehlendes TRUE-Target haben"
    print(f"✓ Warnung erkannt: {[w.message for w in warnings if 'TRUE target' in w.message][0]}")


def test_condition_validation_nonexistent_target():
    """Test: CONDITION mit nicht-existierendem Target -> ERROR."""
    print("\n=== Test 5: CONDITION mit nicht-existierendem Target ===")
    
    doc = VPBDocument()
    condition = VPBElement(
        element_id="cond_5",
        element_type="CONDITION",
        label="Nonexistent Target",
        condition_checks=[
            {"field": "status", "operator": "==", "value": "active", "check_type": "string"}
        ],
        condition_true_target="nonexistent_element"
    )
    doc.add_element(condition)
    
    validator = ConditionValidator()
    result = ValidationResult()
    validator.validate_condition(condition, doc, result)
    
    errors = [e for e in result.issues if e.severity == "error" and e.category == "condition"]
    assert any("does not exist" in e.message for e in errors), "Sollte ERROR für nicht-existierendes Target haben"
    print(f"✓ Fehler erkannt: {[e.message for e in errors if 'does not exist' in e.message][0]}")


def test_condition_validation_valid_target():
    """Test: CONDITION mit existierendem Target -> OK."""
    print("\n=== Test 6: CONDITION mit existierendem Target ===")
    
    doc = VPBDocument()
    
    # Target-Element erstellen
    target = VPBElement(
        element_id="target_1",
        element_type="FUNCTION",
        label="Target Function"
    )
    doc.add_element(target)
    
    # CONDITION mit gültigem Target
    condition = VPBElement(
        element_id="cond_6",
        element_type="CONDITION",
        label="Valid Target",
        condition_checks=[
            {"field": "status", "operator": "==", "value": "active", "check_type": "string"}
        ],
        condition_true_target="target_1"
    )
    doc.add_element(condition)
    
    validator = ConditionValidator()
    result = ValidationResult()
    validator.validate_condition(condition, doc, result)
    
    errors = [e for e in result.issues if e.severity == "error" and "does not exist" in e.message]
    assert len(errors) == 0, "Sollte keinen Fehler für existierendes Target haben"
    print(f"✓ Kein Fehler für existierendes Target")


def test_condition_validation_no_incoming():
    """Test: CONDITION ohne eingehende Verbindungen -> WARNING."""
    print("\n=== Test 7: CONDITION ohne eingehende Verbindungen ===")
    
    doc = VPBDocument()
    condition = VPBElement(
        element_id="cond_7",
        element_type="CONDITION",
        label="No Incoming",
        condition_checks=[
            {"field": "status", "operator": "==", "value": "active", "check_type": "string"}
        ]
    )
    doc.add_element(condition)
    
    validator = ConditionValidator()
    result = ValidationResult()
    validator.validate_condition(condition, doc, result)
    
    warnings = [w for w in result.issues if w.severity == "warning" and w.category == "condition"]
    assert any("no incoming connections" in w.message for w in warnings), "Sollte WARNING für fehlende Verbindungen haben"
    print(f"✓ Warnung erkannt: {[w.message for w in warnings if 'no incoming' in w.message][0]}")


def test_condition_validation_empty_field():
    """Test: CONDITION mit leerem Field-Namen -> ERROR."""
    print("\n=== Test 8: CONDITION mit leerem Field ===")
    
    doc = VPBDocument()
    condition = VPBElement(
        element_id="cond_8",
        element_type="CONDITION",
        label="Empty Field",
        condition_checks=[
            {"field": "", "operator": "==", "value": "test", "check_type": "string"}
        ]
    )
    doc.add_element(condition)
    
    validator = ConditionValidator()
    result = ValidationResult()
    validator.validate_condition(condition, doc, result)
    
    errors = [e for e in result.issues if e.severity == "error" and e.category == "condition"]
    assert any("Empty field name" in e.message for e in errors), "Sollte ERROR für leeres Field haben"
    print(f"✓ Fehler erkannt: {[e.message for e in errors if 'Empty field' in e.message][0]}")


def test_condition_validation_empty_value():
    """Test: CONDITION mit leerem Value -> ERROR."""
    print("\n=== Test 9: CONDITION mit leerem Value ===")
    
    doc = VPBDocument()
    condition = VPBElement(
        element_id="cond_9",
        element_type="CONDITION",
        label="Empty Value",
        condition_checks=[
            {"field": "status", "operator": "==", "value": "", "check_type": "string"}
        ]
    )
    doc.add_element(condition)
    
    validator = ConditionValidator()
    result = ValidationResult()
    validator.validate_condition(condition, doc, result)
    
    errors = [e for e in result.issues if e.severity == "error" and e.category == "condition"]
    assert any("Empty value" in e.message for e in errors), "Sollte ERROR für leeren Value haben"
    print(f"✓ Fehler erkannt: {[e.message for e in errors if 'Empty value' in e.message][0]}")


def test_condition_validation_service_integration():
    """Test: ValidationService integriert ConditionValidator korrekt."""
    print("\n=== Test 10: ValidationService Integration ===")
    
    doc = VPBDocument()
    
    # CONDITION mit mehreren Problemen
    condition = VPBElement(
        element_id="cond_10",
        element_type="CONDITION",
        label="Integration Test",
        condition_checks=[
            {"field": "status", "operator": "==", "value": "active", "check_type": "string"}
        ],
        condition_true_target="nonexistent"
    )
    doc.add_element(condition)
    
    # Über ValidationService validieren
    service = ValidationService()
    result = service.validate(doc)
    
    # Prüfen ob CONDITION-Fehler gefunden wurden
    condition_errors = [e for e in result.issues if e.category == "condition"]
    assert len(condition_errors) > 0, "ValidationService sollte CONDITION-Fehler finden"
    print(f"✓ ValidationService hat {len(condition_errors)} CONDITION-Issues gefunden")
    for issue in condition_errors:
        print(f"  - [{issue.severity.upper()}] {issue.message}")


def test_condition_validation_multiple_checks():
    """Test: CONDITION mit mehreren Checks."""
    print("\n=== Test 11: CONDITION mit mehreren Checks ===")
    
    doc = VPBDocument()
    condition = VPBElement(
        element_id="cond_11",
        element_type="CONDITION",
        label="Multiple Checks",
        condition_checks=[
            {"field": "status", "operator": "==", "value": "active", "check_type": "string"},
            {"field": "priority", "operator": ">", "value": "5", "check_type": "number"},
            {"field": "date", "operator": ">=", "value": "2024-01-01", "check_type": "date"}
        ],
        condition_logic="AND"
    )
    doc.add_element(condition)
    
    validator = ConditionValidator()
    result = ValidationResult()
    validator.validate_condition(condition, doc, result)
    
    # Sollte keine Operator-Fehler haben
    operator_errors = [e for e in result.issues if e.severity == "error" and "Invalid operator" in e.message]
    assert len(operator_errors) == 0, "Sollte keine Operator-Fehler haben"
    print(f"✓ Alle {len(condition.condition_checks)} Checks sind gültig")


if __name__ == "__main__":
    print("=" * 60)
    print("CONDITION VALIDATION TESTS")
    print("=" * 60)
    
    try:
        test_condition_validation_no_checks()
        test_condition_validation_invalid_operator()
        test_condition_validation_valid_operators()
        test_condition_validation_missing_true_target()
        test_condition_validation_nonexistent_target()
        test_condition_validation_valid_target()
        test_condition_validation_no_incoming()
        test_condition_validation_empty_field()
        test_condition_validation_empty_value()
        test_condition_validation_service_integration()
        test_condition_validation_multiple_checks()
        
        print("\n" + "=" * 60)
        print("✓ ALLE 11 TESTS ERFOLGREICH")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ TEST FEHLGESCHLAGEN: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
