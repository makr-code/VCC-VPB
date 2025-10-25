"""
Tests für INTERLOCK Element Validierung.

Test-Regeln:
1. Resource-ID not empty [ERROR]
2. Type valid (MUTEX/SEMAPHORE) [ERROR]
3. Max-Count > 0 [ERROR]
4. Timeout >= 0 [ERROR]
5. Locked-Target exists wenn gesetzt [WARNING]
6. Resource-ID Duplikate [WARNING]
7. Timeout ohne Locked-Target [WARNING]
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vpb.models.element import VPBElement
from vpb.models.document import DocumentModel
from vpb.services.validation_service import ValidationResult, InterlockValidator


def test_interlock_empty_resource_id():
    """Test: Resource-ID leer -> ERROR"""
    print("\n[TEST 1] INTERLOCK ohne Resource-ID (ERROR)")
    
    doc = DocumentModel()
    interlock = VPBElement(
        element_id="interlock_1",
        element_type="INTERLOCK",
        name="DB Lock",
        x=100, y=100
    )
    interlock.interlock_type = "MUTEX"
    interlock.interlock_resource_id = ""  # LEER -> ERROR
    interlock.interlock_max_count = 1
    interlock.interlock_timeout = 0
    interlock.interlock_on_locked_target = ""
    interlock.interlock_auto_release = True
    
    doc.add_element(interlock)
    
    validator = InterlockValidator()
    result = ValidationResult()
    validator.validate_interlock(interlock, doc, result)
    
    errors = [e for e in result.errors if e.category == "interlock"]
    assert len(errors) > 0, "Expected ERROR for empty resource_id"
    assert any("resource ID" in e.message for e in errors), "Error should mention resource ID"
    
    print(f"✅ ERROR gefunden: {errors[0].message}")


def test_interlock_invalid_type():
    """Test: Ungültiger Type -> ERROR"""
    print("\n[TEST 2] INTERLOCK mit ungültigem Type (ERROR)")
    
    doc = DocumentModel()
    interlock = VPBElement(
        element_id="interlock_2",
        element_type="INTERLOCK",
        name="Invalid Lock",
        x=100, y=100
    )
    interlock.interlock_type = "INVALID_TYPE"  # UNGÜLTIG -> ERROR
    interlock.interlock_resource_id = "test_resource"
    interlock.interlock_max_count = 1
    interlock.interlock_timeout = 0
    interlock.interlock_on_locked_target = ""
    interlock.interlock_auto_release = True
    
    doc.add_element(interlock)
    
    validator = InterlockValidator()
    result = ValidationResult()
    validator.validate_interlock(interlock, doc, result)
    
    errors = [e for e in result.errors if e.category == "interlock"]
    assert len(errors) > 0, "Expected ERROR for invalid type"
    assert any("Invalid interlock type" in e.message for e in errors), "Error should mention invalid type"
    
    print(f"✅ ERROR gefunden: {errors[0].message}")


def test_interlock_invalid_max_count():
    """Test: Max-Count <= 0 -> ERROR"""
    print("\n[TEST 3] INTERLOCK mit max_count=0 (ERROR)")
    
    doc = DocumentModel()
    interlock = VPBElement(
        element_id="interlock_3",
        element_type="INTERLOCK",
        name="Zero Lock",
        x=100, y=100
    )
    interlock.interlock_type = "SEMAPHORE"
    interlock.interlock_resource_id = "api_limit"
    interlock.interlock_max_count = 0  # <= 0 -> ERROR
    interlock.interlock_timeout = 0
    interlock.interlock_on_locked_target = ""
    interlock.interlock_auto_release = True
    
    doc.add_element(interlock)
    
    validator = InterlockValidator()
    result = ValidationResult()
    validator.validate_interlock(interlock, doc, result)
    
    errors = [e for e in result.errors if e.category == "interlock"]
    assert len(errors) > 0, "Expected ERROR for max_count=0"
    assert any("Max count must be > 0" in e.message for e in errors), "Error should mention max count"
    
    print(f"✅ ERROR gefunden: {errors[0].message}")


def test_interlock_negative_timeout():
    """Test: Timeout < 0 -> ERROR"""
    print("\n[TEST 4] INTERLOCK mit negativem Timeout (ERROR)")
    
    doc = DocumentModel()
    interlock = VPBElement(
        element_id="interlock_4",
        element_type="INTERLOCK",
        name="Negative Timeout",
        x=100, y=100
    )
    interlock.interlock_type = "MUTEX"
    interlock.interlock_resource_id = "db_conn"
    interlock.interlock_max_count = 1
    interlock.interlock_timeout = -5  # NEGATIV -> ERROR
    interlock.interlock_on_locked_target = ""
    interlock.interlock_auto_release = True
    
    doc.add_element(interlock)
    
    validator = InterlockValidator()
    result = ValidationResult()
    validator.validate_interlock(interlock, doc, result)
    
    errors = [e for e in result.errors if e.category == "interlock"]
    assert len(errors) > 0, "Expected ERROR for negative timeout"
    assert any("cannot be negative" in e.message for e in errors), "Error should mention negative timeout"
    
    print(f"✅ ERROR gefunden: {errors[0].message}")


def test_interlock_nonexistent_locked_target():
    """Test: Locked-Target existiert nicht -> WARNING"""
    print("\n[TEST 5] INTERLOCK mit nicht-existierendem Locked-Target (WARNING)")
    
    doc = DocumentModel()
    interlock = VPBElement(
        element_id="interlock_5",
        element_type="INTERLOCK",
        name="Lock with Target",
        x=100, y=100
    )
    interlock.interlock_type = "MUTEX"
    interlock.interlock_resource_id = "file_access"
    interlock.interlock_max_count = 1
    interlock.interlock_timeout = 10
    interlock.interlock_on_locked_target = "nonexistent_element"  # EXISTIERT NICHT -> WARNING
    interlock.interlock_auto_release = True
    
    doc.add_element(interlock)
    
    validator = InterlockValidator()
    result = ValidationResult()
    validator.validate_interlock(interlock, doc, result)
    
    warnings = [w for w in result.warnings if w.category == "interlock"]
    assert len(warnings) > 0, "Expected WARNING for nonexistent target"
    assert any("does not exist" in w.message for w in warnings), "Warning should mention nonexistent target"
    
    print(f"✅ WARNING gefunden: {warnings[0].message}")


def test_interlock_valid_mutex():
    """Test: Gültiger MUTEX -> Keine Errors"""
    print("\n[TEST 6] Gültiger MUTEX INTERLOCK (keine Errors)")
    
    doc = DocumentModel()
    interlock = VPBElement(
        element_id="interlock_6",
        element_type="INTERLOCK",
        name="Valid MUTEX",
        x=100, y=100
    )
    interlock.interlock_type = "MUTEX"
    interlock.interlock_resource_id = "db_connection"
    interlock.interlock_max_count = 1
    interlock.interlock_timeout = 0
    interlock.interlock_on_locked_target = ""
    interlock.interlock_auto_release = True
    
    doc.add_element(interlock)
    
    validator = InterlockValidator()
    result = ValidationResult()
    validator.validate_interlock(interlock, doc, result)
    
    errors = [e for e in result.errors if e.category == "interlock" and e.element_id == "interlock_6"]
    assert len(errors) == 0, f"Expected no errors for valid MUTEX, got: {[e.message for e in errors]}"
    
    print("✅ Keine Errors für gültigen MUTEX")


def test_interlock_valid_semaphore():
    """Test: Gültiger SEMAPHORE -> Keine Errors"""
    print("\n[TEST 7] Gültiger SEMAPHORE INTERLOCK (keine Errors)")
    
    doc = DocumentModel()
    interlock = VPBElement(
        element_id="interlock_7",
        element_type="INTERLOCK",
        name="Valid SEMAPHORE",
        x=100, y=100
    )
    interlock.interlock_type = "SEMAPHORE"
    interlock.interlock_resource_id = "api_rate_limit"
    interlock.interlock_max_count = 10  # > 1 für SEMAPHORE
    interlock.interlock_timeout = 30
    interlock.interlock_on_locked_target = ""
    interlock.interlock_auto_release = True
    
    doc.add_element(interlock)
    
    validator = InterlockValidator()
    result = ValidationResult()
    validator.validate_interlock(interlock, doc, result)
    
    errors = [e for e in result.errors if e.category == "interlock" and e.element_id == "interlock_7"]
    assert len(errors) == 0, f"Expected no errors for valid SEMAPHORE, got: {[e.message for e in errors]}"
    
    print("✅ Keine Errors für gültigen SEMAPHORE")


def test_interlock_semaphore_with_max_count_one():
    """Test: SEMAPHORE mit max_count=1 -> WARNING"""
    print("\n[TEST 8] SEMAPHORE mit max_count=1 (WARNING)")
    
    doc = DocumentModel()
    interlock = VPBElement(
        element_id="interlock_8",
        element_type="INTERLOCK",
        name="SEMAPHORE=1",
        x=100, y=100
    )
    interlock.interlock_type = "SEMAPHORE"
    interlock.interlock_resource_id = "single_access"
    interlock.interlock_max_count = 1  # SEMAPHORE mit 1 -> WARNING
    interlock.interlock_timeout = 0
    interlock.interlock_on_locked_target = ""
    interlock.interlock_auto_release = True
    
    doc.add_element(interlock)
    
    validator = InterlockValidator()
    result = ValidationResult()
    validator.validate_interlock(interlock, doc, result)
    
    warnings = [w for w in result.warnings if w.category == "interlock" and w.element_id == "interlock_8"]
    assert len(warnings) > 0, "Expected WARNING for SEMAPHORE with max_count=1"
    assert any("behaves like MUTEX" in w.message for w in warnings), "Warning should mention MUTEX behavior"
    
    print(f"✅ WARNING gefunden: {warnings[0].message}")


def test_interlock_duplicate_resource_ids():
    """Test: Mehrere INTERLOCKs mit gleicher Resource-ID -> WARNING"""
    print("\n[TEST 9] Mehrere INTERLOCKs mit gleicher Resource-ID (WARNING)")
    
    doc = DocumentModel()
    
    # INTERLOCK 1
    interlock1 = VPBElement(
        element_id="interlock_9a",
        element_type="INTERLOCK",
        name="Lock 1",
        x=100, y=100
    )
    interlock1.interlock_type = "MUTEX"
    interlock1.interlock_resource_id = "shared_resource"
    interlock1.interlock_max_count = 1
    interlock1.interlock_timeout = 0
    interlock1.interlock_on_locked_target = ""
    interlock1.interlock_auto_release = True
    
    # INTERLOCK 2 mit gleicher Resource-ID
    interlock2 = VPBElement(
        element_id="interlock_9b",
        element_type="INTERLOCK",
        name="Lock 2",
        x=250, y=100
    )
    interlock2.interlock_type = "MUTEX"
    interlock2.interlock_resource_id = "shared_resource"  # GLEICH -> WARNING
    interlock2.interlock_max_count = 1
    interlock2.interlock_timeout = 0
    interlock2.interlock_on_locked_target = ""
    interlock2.interlock_auto_release = True
    
    doc.add_element(interlock1)
    doc.add_element(interlock2)
    
    validator = InterlockValidator()
    result1 = ValidationResult()
    result2 = ValidationResult()
    validator.validate_interlock(interlock1, doc, result1)
    validator.validate_interlock(interlock2, doc, result2)
    
    warnings = result1.warnings + result2.warnings
    warnings = [w for w in warnings if w.category == "interlock"]
    # Beide INTERLOCKs sollten Warning bekommen
    assert len(warnings) >= 2, f"Expected at least 2 warnings for duplicate resource IDs, got {len(warnings)}"
    assert any("is used by" in w.message for w in warnings), "Warning should mention duplicate usage"
    
    print(f"✅ {len(warnings)} WARNINGs gefunden für duplizierte Resource-IDs")


def test_interlock_timeout_without_target():
    """Test: Timeout > 0 ohne Locked-Target -> WARNING"""
    print("\n[TEST 10] INTERLOCK mit Timeout aber ohne Locked-Target (WARNING)")
    
    doc = DocumentModel()
    interlock = VPBElement(
        element_id="interlock_10",
        element_type="INTERLOCK",
        name="Timeout No Target",
        x=100, y=100
    )
    interlock.interlock_type = "MUTEX"
    interlock.interlock_resource_id = "timeout_resource"
    interlock.interlock_max_count = 1
    interlock.interlock_timeout = 20  # > 0 aber kein Target -> WARNING
    interlock.interlock_on_locked_target = ""  # LEER
    interlock.interlock_auto_release = True
    
    doc.add_element(interlock)
    
    validator = InterlockValidator()
    result = ValidationResult()
    validator.validate_interlock(interlock, doc, result)
    
    warnings = [w for w in result.warnings if w.category == "interlock" and w.element_id == "interlock_10"]
    assert len(warnings) > 0, "Expected WARNING for timeout without target"
    assert any("but no fallback target" in w.message for w in warnings), "Warning should mention missing fallback"
    
    print(f"✅ WARNING gefunden: {warnings[0].message}")


def run_all_tests():
    """Führt alle Tests aus."""
    print("=" * 60)
    print("INTERLOCK ELEMENT VALIDATION TESTS")
    print("=" * 60)
    
    tests = [
        test_interlock_empty_resource_id,
        test_interlock_invalid_type,
        test_interlock_invalid_max_count,
        test_interlock_negative_timeout,
        test_interlock_nonexistent_locked_target,
        test_interlock_valid_mutex,
        test_interlock_valid_semaphore,
        test_interlock_semaphore_with_max_count_one,
        test_interlock_duplicate_resource_ids,
        test_interlock_timeout_without_target
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    if failed > 0:
        print(f"⚠️  {failed} tests failed")
    else:
        print("✅ All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
