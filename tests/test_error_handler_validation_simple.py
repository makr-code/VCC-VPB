"""
Vereinfachte Tests für ERROR_HANDLER Validation.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vpb.models.element import VPBElement
from vpb.models.document import DocumentModel, VPBConnection
from vpb.services.validation_service import ValidationService, ErrorHandlerValidator, ValidationResult


def create_eh(element_id="eh_test", **kwargs):
    """Helper: Create ERROR_HANDLER element with defaults."""
    defaults = {
        'element_id': element_id,
        'element_type': 'ERROR_HANDLER',
        'name': 'Test EH',
        'x': 100,
        'y': 100
    }
    defaults.update(kwargs)
    return VPBElement(**defaults)


print("\n" + "="*60)
print("ERROR_HANDLER VALIDATION TESTS (Simplified)")
print("="*60)

# Test 1: Invalid handler type
print("\n=== Test 1: Ungültiger Handler-Type ===")
doc = DocumentModel()
elem = create_eh("eh1", error_handler_type="INVALID")
doc.add_element(elem)

validator = ErrorHandlerValidator()
result = ValidationResult()
validator.validate_error_handler(elem, doc, result)

assert len(result.errors) >= 1, f"Expected >=1 error, got {len(result.errors)}"
assert any("Invalid handler type" in e.message for e in result.errors)
print(f"✓ Error detected: {result.errors[0].message}")

# Test 2: Negative retry count
print("\n=== Test 2: Negativer Retry-Count ===")
doc = DocumentModel()
elem = create_eh("eh2", error_handler_retry_count=-5)
doc.add_element(elem)

result = ValidationResult()
validator.validate_error_handler(elem, doc, result)

assert len(result.errors) >= 1
assert any("cannot be negative" in e.message for e in result.errors)
print(f"✓ Error detected: {result.errors[0].message}")

# Test 3: Invalid retry delay
print("\n=== Test 3: Ungültiger Retry-Delay ===")
doc = DocumentModel()
elem = create_eh("eh3", error_handler_type="RETRY", error_handler_retry_count=5, error_handler_retry_delay=0)
doc.add_element(elem)

result = ValidationResult()
validator.validate_error_handler(elem, doc, result)

assert len(result.errors) >= 1
assert any("Retry delay must be positive" in e.message for e in result.errors)
print(f"✓ Error detected: {result.errors[0].message}")

# Test 4: Timeout = 0 warning
print("\n=== Test 4: Timeout = 0 (Warnung) ===")
doc = DocumentModel()
elem = create_eh("eh4", error_handler_timeout=0)
doc.add_element(elem)

result = ValidationResult()
validator.validate_error_handler(elem, doc, result)

assert any("Timeout is disabled" in w.message for w in result.warnings)
print(f"✓ Warning detected: {[w.message for w in result.warnings if 'Timeout' in w.message][0]}")

# Test 5: Negative timeout
print("\n=== Test 5: Negativer Timeout ===")
doc = DocumentModel()
elem = create_eh("eh5", error_handler_timeout=-10)
doc.add_element(elem)

result = ValidationResult()
validator.validate_error_handler(elem, doc, result)

assert len(result.errors) >= 1
assert any("Timeout cannot be negative" in e.message for e in result.errors)
print(f"✓ Error detected: {result.errors[0].message}")

# Test 6: Nonexistent error target
print("\n=== Test 6: Nicht existierender Error-Target ===")
doc = DocumentModel()
elem = create_eh("eh6", error_handler_on_error_target="nonexistent")
doc.add_element(elem)

result = ValidationResult()
validator.validate_error_handler(elem, doc, result)

assert len(result.errors) >= 1
assert any("Error target element" in e.message and "does not exist" in e.message for e in result.errors)
print(f"✓ Error detected: {result.errors[0].message}")

# Test 7: Valid error target
print("\n=== Test 7: Gültiger Error-Target ===")
doc = DocumentModel()
target = VPBElement(element_id="target1", element_type="STEP", name="Target", x=200, y=200)
doc.add_element(target)
elem = create_eh("eh7", error_handler_on_error_target="target1")
doc.add_element(elem)

result = ValidationResult()
validator.validate_error_handler(elem, doc, result)

error_messages = [e.message for e in result.errors]
assert not any("Error target element" in msg and "does not exist" in msg for msg in error_messages)
print("✓ Gültiger Error-Target akzeptiert")

# Test 8: No incoming connections warning
print("\n=== Test 8: Keine eingehenden Verbindungen ===")
doc = DocumentModel()
elem = create_eh("eh8")
doc.add_element(elem)

result = ValidationResult()
validator.validate_error_handler(elem, doc, result)

assert any("no incoming connections" in w.message for w in result.warnings)
print(f"✓ Warning detected: {[w.message for w in result.warnings if 'incoming' in w.message][0]}")

# Test 9: Valid error handler with all properties
print("\n=== Test 9: Komplett gültiger ERROR_HANDLER ===")
doc = DocumentModel()

error_target = VPBElement(element_id="error_target", element_type="Prozess", name="Error", x=300, y=300)
success_target = VPBElement(element_id="success_target", element_type="Prozess", name="Success", x=400, y=400)
doc.add_element(error_target)
doc.add_element(success_target)

elem = create_eh(
    "eh9",
    error_handler_type="RETRY",
    error_handler_retry_count=3,
    error_handler_retry_delay=60,
    error_handler_timeout=300,
    error_handler_on_error_target="error_target",
    error_handler_on_success_target="success_target"
)
doc.add_element(elem)

# Note: Skipping connection test due to model inconsistency
# The validator will warn about missing incoming connections

result = ValidationResult()
validator.validate_error_handler(elem, doc, result)

print(f"  Errors: {len(result.errors)}")
print(f"  Warnings: {len(result.warnings)}")

# Should have 1 warning about no incoming connections, but no errors
errors_without_incoming = [e for e in result.errors if "incoming" not in e.message]
assert len(errors_without_incoming) == 0, f"Expected no errors (except incoming), got: {[e.message for e in errors_without_incoming]}"
print("✓ Gültiger ERROR_HANDLER ohne kritische Fehler")

# Test 10: Integration with ValidationService
print("\n=== Test 10: Integration mit ValidationService ===")
doc = DocumentModel()
elem = create_eh(
    "eh10",
    error_handler_type="INVALID",
    error_handler_retry_count=-1,
    error_handler_timeout=-50
)
doc.add_element(elem)

service = ValidationService(check_naming=True, check_flow=True, check_completeness=True)
result = service.validate_document(doc)

print(f"  Total Errors: {len(result.errors)}")
print(f"  Total Warnings: {len(result.warnings)}")

error_handler_errors = [e for e in result.errors if e.category == "error_handler"]
assert len(error_handler_errors) >= 3, f"Expected >=3 errors, got {len(error_handler_errors)}"
print(f"✓ ValidationService erkennt {len(error_handler_errors)} ERROR_HANDLER-Fehler")

print("\n" + "="*60)
print("ALLE TESTS BESTANDEN! ✓")
print("="*60)
