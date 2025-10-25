"""Quick test for CONDITION validator."""
import sys
sys.path.insert(0, '.')

from vpb.models.element import VPBElement
from vpb.models.document import DocumentModel
from vpb.services.validation_service import ConditionValidator, ValidationResult

# Test 1: No checks
doc = DocumentModel()
cond = VPBElement(
    element_id='c1',
    element_type='CONDITION',
    name='Test',
    x=100, y=100,
    condition_checks=[]
)
doc.add_element(cond)

validator = ConditionValidator()
result = ValidationResult()
validator.validate_condition(cond, doc, result)

print(f"Test 1 - No checks: {len(result.errors)} errors")
if result.errors:
    print(f"  Message: {result.errors[0].message}")

# Test 2: Invalid operator
doc2 = DocumentModel()
cond2 = VPBElement(
    element_id='c2',
    element_type='CONDITION',
    name='Test2',
    x=100, y=100,
    condition_checks=[{"field": "x", "operator": "INVALID", "value": "y", "check_type": "string"}]
)
doc2.add_element(cond2)

result2 = ValidationResult()
validator.validate_condition(cond2, doc2, result2)

errors2 = [e for e in result2.errors if 'Invalid operator' in e.message]
print(f"Test 2 - Invalid operator: {len(errors2)} errors")
if errors2:
    print(f"  Message: {errors2[0].message}")

# Test 3: Valid operator
doc3 = DocumentModel()
cond3 = VPBElement(
    element_id='c3',
    element_type='CONDITION',
    name='Test3',
    x=100, y=100,
    condition_checks=[{"field": "status", "operator": "==", "value": "active", "check_type": "string"}]
)
doc3.add_element(cond3)

result3 = ValidationResult()
validator.validate_condition(cond3, doc3, result3)

operator_errors = [e for e in result3.errors if 'Invalid operator' in e.message]
print(f"Test 3 - Valid operator: {len(operator_errors)} operator errors (should be 0)")

print("\n✓ All quick tests completed")
