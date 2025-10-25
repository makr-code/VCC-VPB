"""
Tests für ERROR_HANDLER Validation.

Testet die ErrorHandlerValidator Klasse mit allen 7 Validierungsregeln.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vpb.models.element import VPBElement
from vpb.models.document import DocumentModel, VPBConnection
from vpb.services.validation_service import ValidationService, ErrorHandlerValidator, ValidationResult


def test_rule1_invalid_handler_type():
    """Regel 1: Handler-Type muss gültig sein [ERROR]"""
    print("\n=== Test 1: Ungültiger Handler-Type ===")
    
    doc = DocumentModel()
    element = VPBElement(
        element_id="eh1",
        element_type="ERROR_HANDLER",
        name="Test Error Handler",
        x=100,
        y=100,
        error_handler_type="INVALID_TYPE"
    )
    doc.add_element(element)
    
    validator = ErrorHandlerValidator()
    result = ValidationResult()
    validator.validate_error_handler(element, doc, result)
    
    assert len(result.errors) == 1, f"Expected 1 error, got {len(result.errors)}"
    assert "Invalid handler type" in result.errors[0].message
    print(f"✓ Error detected: {result.errors[0].message}")


def test_rule2_negative_retry_count():
    """Regel 2: Retry-Count muss >= 0 sein [ERROR]"""
    print("\n=== Test 2: Negativer Retry-Count ===")
    
    doc = DocumentModel()
    element = VPBElement(
        element_id="eh2",
        element_type="ERROR_HANDLER",
        error_handler_retry_count=-5
    )
    doc.add_element(element)
    
    validator = ErrorHandlerValidator()
    result = ValidationResult()
    validator.validate_error_handler(element, doc, result)
    
    assert len(result.errors) >= 1, f"Expected at least 1 error, got {len(result.errors)}"
    error_messages = [e.message for e in result.errors]
    assert any("cannot be negative" in msg for msg in error_messages)
    print(f"✓ Error detected: {result.errors[0].message}")


def test_rule3_invalid_retry_delay():
    """Regel 3: Delay muss > 0 sein wenn retry_count > 0 [ERROR]"""
    print("\n=== Test 3: Ungültiger Retry-Delay ===")
    
    doc = DocumentModel()
    element = VPBElement(
        element_id="eh3",
        element_type="ERROR_HANDLER",
        error_handler_type="RETRY",
        error_handler_retry_count=5,
        error_handler_retry_delay=0  # Invalid!
    )
    doc.add_element(element)
    
    validator = ErrorHandlerValidator()
    result = ValidationResult()
    validator.validate_error_handler(element, doc, result)
    
    assert len(result.errors) >= 1, f"Expected at least 1 error, got {len(result.errors)}"
    error_messages = [e.message for e in result.errors]
    assert any("Retry delay must be positive" in msg for msg in error_messages)
    print(f"✓ Error detected: {result.errors[0].message}")


def test_rule4_timeout_warning():
    """Regel 4: Timeout >= 0, Warnung wenn 0 [WARNING]"""
    print("\n=== Test 4: Timeout = 0 (Warnung) ===")
    
    doc = DocumentModel()
    element = VPBElement(
        element_id="eh4",
        element_type="ERROR_HANDLER",
        error_handler_timeout=0  # Should trigger warning
    )
    doc.add_element(element)
    
    validator = ErrorHandlerValidator()
    result = ValidationResult()
    validator.validate_error_handler(element, doc, result)
    
    warning_messages = [w.message for w in result.warnings]
    assert any("Timeout is disabled" in msg for msg in warning_messages)
    print(f"✓ Warning detected: {result.warnings[0].message}")


def test_rule4_negative_timeout():
    """Regel 4: Timeout < 0 ist Fehler [ERROR]"""
    print("\n=== Test 4b: Negativer Timeout ===")
    
    doc = DocumentModel()
    element = VPBElement(
        element_id="eh4b",
        element_type="ERROR_HANDLER",
        error_handler_timeout=-10  # Should trigger error
    )
    doc.add_element(element)
    
    validator = ErrorHandlerValidator()
    result = ValidationResult()
    validator.validate_error_handler(element, doc, result)
    
    assert len(result.errors) >= 1, f"Expected at least 1 error, got {len(result.errors)}"
    error_messages = [e.message for e in result.errors]
    assert any("Timeout cannot be negative" in msg for msg in error_messages)
    print(f"✓ Error detected: {result.errors[0].message}")


def test_rule5_nonexistent_error_target():
    """Regel 5: Error-Target muss existieren wenn gesetzt [ERROR]"""
    print("\n=== Test 5: Nicht existierender Error-Target ===")
    
    doc = DocumentModel()
    element = VPBElement(
        element_id="eh5",
        element_type="ERROR_HANDLER",
        error_handler_on_error_target="nonexistent_element"
    )
    doc.add_element(element)
    
    validator = ErrorHandlerValidator()
    result = ValidationResult()
    validator.validate_error_handler(element, doc, result)
    
    assert len(result.errors) >= 1, f"Expected at least 1 error, got {len(result.errors)}"
    error_messages = [e.message for e in result.errors]
    assert any("Error target element" in msg and "does not exist" in msg for msg in error_messages)
    print(f"✓ Error detected: {result.errors[0].message}")


def test_rule5_valid_error_target():
    """Regel 5: Gültiger Error-Target wird akzeptiert"""
    print("\n=== Test 5b: Gültiger Error-Target ===")
    
    doc = DocumentModel()
    target = VPBElement(element_id="target1", element_type="STEP")
    doc.add_element(target)
    
    element = VPBElement(
        element_id="eh5b",
        element_type="ERROR_HANDLER",
        error_handler_on_error_target="target1"
    )
    doc.add_element(element)
    
    validator = ErrorHandlerValidator()
    result = ValidationResult()
    validator.validate_error_handler(element, doc, result)
    
    error_messages = [e.message for e in result.errors]
    assert not any("Error target element" in msg and "does not exist" in msg for msg in error_messages)
    print("✓ Gültiger Error-Target akzeptiert")


def test_rule6_nonexistent_success_target():
    """Regel 6: Success-Target muss existieren wenn gesetzt [WARNING]"""
    print("\n=== Test 6: Nicht existierender Success-Target ===")
    
    doc = DocumentModel()
    element = VPBElement(
        element_id="eh6",
        element_type="ERROR_HANDLER",
        error_handler_on_success_target="nonexistent_success"
    )
    doc.add_element(element)
    
    validator = ErrorHandlerValidator()
    result = ValidationResult()
    validator.validate_error_handler(element, doc, result)
    
    warning_messages = [w.message for w in result.warnings]
    assert any("Success target element" in msg and "does not exist" in msg for msg in warning_messages)
    print(f"✓ Warning detected: {result.warnings[0].message}")


def test_rule7_no_incoming_connections():
    """Regel 7: Sollte eingehende Verbindungen haben [WARNING]"""
    print("\n=== Test 7: Keine eingehenden Verbindungen ===")
    
    doc = DocumentModel()
    element = VPBElement(
        element_id="eh7",
        element_type="ERROR_HANDLER"
    )
    doc.add_element(element)
    
    validator = ErrorHandlerValidator()
    result = ValidationResult()
    validator.validate_error_handler(element, doc, result)
    
    warning_messages = [w.message for w in result.warnings]
    assert any("no incoming connections" in msg for msg in warning_messages)
    print(f"✓ Warning detected: {[w.message for w in result.warnings if 'incoming' in w.message][0]}")


def test_valid_error_handler():
    """Test: Komplett gültiger ERROR_HANDLER ohne Fehler/Warnungen"""
    print("\n=== Test 8: Komplett gültiger ERROR_HANDLER ===")
    
    doc = DocumentModel()
    
    # Create target elements
    error_target = VPBElement(element_id="error_target", element_type="STEP")
    success_target = VPBElement(element_id="success_target", element_type="STEP")
    source = VPBElement(element_id="source", element_type="STEP")
    doc.add_element(error_target)
    doc.add_element(success_target)
    doc.add_element(source)
    
    # Create valid ERROR_HANDLER
    element = VPBElement(
        element_id="eh_valid",
        element_type="ERROR_HANDLER",
        error_handler_type="RETRY",
        error_handler_retry_count=3,
        error_handler_retry_delay=60,
        error_handler_timeout=300,
        error_handler_on_error_target="error_target",
        error_handler_on_success_target="success_target"
    )
    doc.add_element(element)
    
    # Add incoming connection
    connection = VPBConnection(
        connection_id="conn1",
        from_id="source",
        to_id="eh_valid"
    )
    doc.add_connection(connection)
    
    validator = ErrorHandlerValidator()
    result = ValidationResult()
    validator.validate_error_handler(element, doc, result)
    
    print(f"  Errors: {len(result.errors)}")
    print(f"  Warnings: {len(result.warnings)}")
    
    # No critical errors expected
    assert len(result.errors) == 0, f"Expected no errors, got {len(result.errors)}: {[e.message for e in result.errors]}"
    print("✓ Gültiger ERROR_HANDLER ohne Fehler")


def test_integration_with_validation_service():
    """Test: Integration mit ValidationService"""
    print("\n=== Test 9: Integration mit ValidationService ===")
    
    doc = DocumentModel()
    
    # Create ERROR_HANDLER with multiple issues
    element = VPBElement(
        element_id="eh_multi",
        element_type="ERROR_HANDLER",
        error_handler_type="INVALID",  # Error 1
        error_handler_retry_count=-1,  # Error 2
        error_handler_timeout=-50      # Error 3
    )
    doc.add_element(element)
    
    # Run full validation
    service = ValidationService(check_naming=True, check_flow=True, check_completeness=True)
    result = service.validate(doc)
    
    print(f"  Total Errors: {len(result.errors)}")
    print(f"  Total Warnings: {len(result.warnings)}")
    
    # Should have at least 3 errors from ERROR_HANDLER
    error_handler_errors = [e for e in result.errors if e.category == "error_handler"]
    assert len(error_handler_errors) >= 3, f"Expected at least 3 ERROR_HANDLER errors, got {len(error_handler_errors)}"
    print(f"✓ ValidationService erkennt {len(error_handler_errors)} ERROR_HANDLER-Fehler")


def run_all_tests():
    """Run all ERROR_HANDLER validation tests"""
    print("\n" + "="*60)
    print("ERROR_HANDLER VALIDATION TESTS")
    print("="*60)
    
    tests = [
        test_rule1_invalid_handler_type,
        test_rule2_negative_retry_count,
        test_rule3_invalid_retry_delay,
        test_rule4_timeout_warning,
        test_rule4_negative_timeout,
        test_rule5_nonexistent_error_target,
        test_rule5_valid_error_target,
        test_rule6_nonexistent_success_target,
        test_rule7_no_incoming_connections,
        test_valid_error_handler,
        test_integration_with_validation_service
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"✗ FAILED: {test.__name__}")
            print(f"  {e}")
        except Exception as e:
            failed += 1
            print(f"✗ ERROR: {test.__name__}")
            print(f"  {e}")
    
    print("\n" + "="*60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
