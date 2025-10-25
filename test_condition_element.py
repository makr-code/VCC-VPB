#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script for CONDITION element schema."""

from vpb.models.element import VPBElement, ConditionCheck

print("="*60)
print("CONDITION Element Schema Tests")
print("="*60)

# Test 1: Create ConditionCheck
print("\n1️⃣ Test: ConditionCheck erstellen")
check1 = ConditionCheck(
    field="status",
    operator="==",
    value="approved",
    check_type="string"
)
print(f"✅ ConditionCheck erstellt: {check1.field} {check1.operator} {check1.value}")
print(f"   Type: {check1.check_type}")

# Test 2: ConditionCheck to_dict
print("\n2️⃣ Test: ConditionCheck to_dict()")
check_dict = check1.to_dict()
print(f"✅ Serialisiert: {check_dict}")
assert check_dict["field"] == "status"
assert check_dict["operator"] == "=="
assert check_dict["value"] == "approved"

# Test 3: ConditionCheck from_dict
print("\n3️⃣ Test: ConditionCheck from_dict()")
check2 = ConditionCheck.from_dict({
    "field": "amount",
    "operator": ">",
    "value": "1000",
    "check_type": "number"
})
print(f"✅ Deserialisiert: {check2.field} {check2.operator} {check2.value}")
assert check2.field == "amount"
assert check2.operator == ">"

# Test 4: CONDITION Element erstellen
print("\n4️⃣ Test: CONDITION Element erstellen")
condition = VPBElement(
    element_id="cond_001",
    element_type="CONDITION",
    name="Status Check",
    x=100,
    y=100,
    condition_checks=[
        {
            "field": "status",
            "operator": "==",
            "value": "approved",
            "check_type": "string"
        },
        {
            "field": "amount",
            "operator": "<=",
            "value": "5000",
            "check_type": "number"
        }
    ],
    condition_logic="AND",
    condition_true_target="approved_001",
    condition_false_target="rejected_001"
)
print(f"✅ CONDITION Element erstellt: {condition.name}")
print(f"   Checks: {len(condition.condition_checks)}")
print(f"   Logic: {condition.condition_logic}")
print(f"   TRUE → {condition.condition_true_target}")
print(f"   FALSE → {condition.condition_false_target}")

# Test 5: CONDITION to_dict (konditionale Serialisierung)
print("\n5️⃣ Test: CONDITION to_dict() - konditionale Serialisierung")
cond_dict = condition.to_dict()
print(f"✅ Serialisiert mit {len(cond_dict)} Feldern")
assert "condition_checks" in cond_dict
assert cond_dict["condition_checks"] is not None
assert cond_dict["condition_logic"] == "AND"
assert cond_dict["condition_true_target"] == "approved_001"
print(f"   ✅ condition_checks: {len(cond_dict['condition_checks'])} Checks")
print(f"   ✅ condition_logic: {cond_dict['condition_logic']}")

# Test 6: Nicht-CONDITION Element sollte keine Condition-Felder haben
print("\n6️⃣ Test: Nicht-CONDITION Element - keine Condition-Felder")
function = VPBElement(
    element_id="func_001",
    element_type="FUNCTION",
    name="Test Function",
    x=200,
    y=200
)
func_dict = function.to_dict()
print(f"✅ FUNCTION Element serialisiert")
assert func_dict["condition_checks"] is None or func_dict["condition_checks"] == []
assert func_dict["condition_logic"] is None
assert func_dict["condition_true_target"] is None
print(f"   ✅ Keine condition_checks: {func_dict.get('condition_checks')}")
print(f"   ✅ Keine condition_logic: {func_dict.get('condition_logic')}")

# Test 7: CONDITION from_dict (Deserialisierung)
print("\n7️⃣ Test: CONDITION from_dict() - Deserialisierung")
restored = VPBElement.from_dict({
    "element_id": "cond_002",
    "element_type": "CONDITION",
    "name": "Restored Condition",
    "x": 300,
    "y": 300,
    "condition_checks": [
        {
            "field": "priority",
            "operator": "==",
            "value": "high",
            "check_type": "string"
        }
    ],
    "condition_logic": "OR",
    "condition_true_target": "high_priority_001",
    "condition_false_target": "normal_priority_001"
})
print(f"✅ CONDITION Element deserialisiert: {restored.name}")
print(f"   Checks: {len(restored.condition_checks)}")
print(f"   Logic: {restored.condition_logic}")
assert len(restored.condition_checks) == 1
assert restored.condition_logic == "OR"
assert restored.condition_true_target == "high_priority_001"

# Test 8: CONDITION clone (Checks kopieren)
print("\n8️⃣ Test: CONDITION clone() - Checks kopieren")
cloned = condition.clone(new_id="cond_001_copy")
print(f"✅ CONDITION geklont: {cloned.element_id}")
print(f"   Original Checks: {len(condition.condition_checks)}")
print(f"   Klone Checks: {len(cloned.condition_checks)}")
assert len(cloned.condition_checks) == len(condition.condition_checks)
assert cloned.condition_logic == condition.condition_logic
assert cloned.element_id == "cond_001_copy"
# Verify it's a deep copy
cloned.condition_checks.append({"field": "test", "operator": "==", "value": "test", "check_type": "string"})
assert len(cloned.condition_checks) != len(condition.condition_checks)
print(f"   ✅ Deep Copy bestätigt (Original: {len(condition.condition_checks)}, Clone: {len(cloned.condition_checks)})")

# Test 9: Leere condition_checks
print("\n9️⃣ Test: CONDITION mit leeren Checks")
empty_cond = VPBElement(
    element_id="cond_003",
    element_type="CONDITION",
    name="Empty Condition",
    x=400,
    y=400,
    condition_checks=[],
    condition_logic="AND",
    condition_true_target="",
    condition_false_target=""
)
empty_dict = empty_cond.to_dict()
print(f"✅ Leere CONDITION serialisiert")
assert empty_dict["condition_checks"] is None or empty_dict["condition_checks"] == []
print(f"   ✅ condition_checks: {empty_dict.get('condition_checks')}")

# Test 10: Multiple Check Types
print("\n🔟 Test: Verschiedene Check-Typen")
multi_checks = [
    ConditionCheck(field="name", operator="contains", value="Test", check_type="string"),
    ConditionCheck(field="count", operator=">=", value="10", check_type="number"),
    ConditionCheck(field="active", operator="==", value="true", check_type="boolean"),
    ConditionCheck(field="date", operator="<", value="2025-12-31", check_type="date"),
]
print(f"✅ {len(multi_checks)} verschiedene Check-Typen erstellt:")
for check in multi_checks:
    print(f"   - {check.field} ({check.check_type}): {check.operator} {check.value}")

print("\n" + "="*60)
print("✅ Alle CONDITION Schema-Tests bestanden!")
print("="*60)
