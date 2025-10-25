#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script for COUNTER validation."""

from vpb.models.element import VPBElement
from vpb.models.connection import VPBConnection
from vpb.models.document import DocumentModel
from vpb.services.validation_service import ValidationService, CounterValidator

print("="*60)
print("COUNTER Validation Tests")
print("="*60)

# Test 1: Valid Counter
print("\n1️⃣ Test: Valider Counter")
doc = DocumentModel()

# Add elements
start = VPBElement(
    element_id="start_001",
    element_type="START_EVENT",
    name="Start",
    x=100,
    y=100
)
doc.add_element(start)

counter = VPBElement(
    element_id="counter_001",
    element_type="COUNTER",
    name="Test Counter",
    x=250,
    y=100,
    counter_type="UP",
    counter_start_value=0,
    counter_max_value=3,
    counter_current_value=0
)
doc.add_element(counter)

func = VPBElement(
    element_id="func_001",
    element_type="FUNCTION",
    name="Function",
    x=400,
    y=100
)
doc.add_element(func)

# Add connections
conn1 = VPBConnection(
    connection_id="conn_001",
    source_element=start,
    target_element=counter,
    connection_type="SEQUENCE"
)
doc.add_connection(conn1)

conn2 = VPBConnection(
    connection_id="conn_002",
    source_element=counter,
    target_element=func,
    connection_type="SEQUENCE"
)
doc.add_connection(conn2)

# Validate
service = ValidationService()
result = service.validate_document(doc)

print(f"✅ Validierung abgeschlossen")
print(f"   Errors: {len(result.errors)}")
print(f"   Warnings: {len(result.warnings)}")
print(f"   Info: {len(result.info)}")

if result.errors:
    print("   ❌ Errors:")
    for error in result.errors:
        print(f"      - {error.message}")

if result.warnings:
    print("   ⚠️ Warnings:")
    for warning in result.warnings:
        print(f"      - {warning.message}")

# Test 2: Invalid Counter (Max <= Start)
print("\n2️⃣ Test: Invalider Counter (Max <= Start)")
doc2 = DocumentModel()

invalid_counter = VPBElement(
    element_id="counter_002",
    element_type="COUNTER",
    name="Invalid Counter",
    x=100,
    y=100,
    counter_type="UP",
    counter_start_value=10,
    counter_max_value=5,  # ERROR: Max < Start
    counter_current_value=0
)
doc2.add_element(invalid_counter)

result2 = service.validate_document(doc2)

print(f"✅ Validierung abgeschlossen")
print(f"   Errors: {len(result2.errors)}")
print(f"   Sollte 1 Error haben (Max <= Start)")

if result2.errors:
    print("   ❌ Errors gefunden:")
    for error in result2.errors:
        print(f"      - {error.message}")
        if error.suggestion:
            print(f"        Vorschlag: {error.suggestion}")

# Test 3: Counter ohne Verbindungen
print("\n3️⃣ Test: Counter ohne Verbindungen")
doc3 = DocumentModel()

isolated_counter = VPBElement(
    element_id="counter_003",
    element_type="COUNTER",
    name="Isolated Counter",
    x=100,
    y=100,
    counter_type="UP",
    counter_start_value=0,
    counter_max_value=3,
    counter_current_value=0
)
doc3.add_element(isolated_counter)

result3 = service.validate_document(doc3)

print(f"✅ Validierung abgeschlossen")
print(f"   Errors: {len(result3.errors)}")
print(f"   Warnings: {len(result3.warnings)}")
print(f"   Sollte 2 Warnings haben (keine Eingänge, keine Ausgänge)")

if result3.warnings:
    print("   ⚠️ Warnings gefunden:")
    for warning in result3.warnings:
        print(f"      - {warning.message}")

# Test 4: Counter mit ungültigem on_max_reached
print("\n4️⃣ Test: Counter mit ungültigem on_max_reached")
doc4 = DocumentModel()

counter_bad_target = VPBElement(
    element_id="counter_004",
    element_type="COUNTER",
    name="Counter with bad target",
    x=100,
    y=100,
    counter_type="UP",
    counter_start_value=0,
    counter_max_value=3,
    counter_current_value=0,
    counter_on_max_reached="non_existent_element"  # ERROR: Element existiert nicht
)
doc4.add_element(counter_bad_target)

result4 = service.validate_document(doc4)

print(f"✅ Validierung abgeschlossen")
print(f"   Errors: {len(result4.errors)}")
print(f"   Sollte 1 Error haben (on_max_reached Element existiert nicht)")

if result4.errors:
    print("   ❌ Errors gefunden:")
    for error in result4.errors:
        print(f"      - {error.message}")

# Test 5: Counter mit ungültigem Typ
print("\n5️⃣ Test: Counter mit ungültigem counter_type")
doc5 = DocumentModel()

counter_bad_type = VPBElement(
    element_id="counter_005",
    element_type="COUNTER",
    name="Counter with bad type",
    x=100,
    y=100,
    counter_type="INVALID_TYPE",  # ERROR: Ungültiger Typ
    counter_start_value=0,
    counter_max_value=3,
    counter_current_value=0
)
doc5.add_element(counter_bad_type)

result5 = service.validate_document(doc5)

print(f"✅ Validierung abgeschlossen")
print(f"   Errors: {len(result5.errors)}")
print(f"   Sollte 1 Error haben (ungültiger counter_type)")

if result5.errors:
    print("   ❌ Errors gefunden:")
    for error in result5.errors:
        print(f"      - {error.message}")

# Test 6: Counter mit current_value außerhalb Range
print("\n6️⃣ Test: Counter mit current_value außerhalb Range")
doc6 = DocumentModel()

counter_bad_current = VPBElement(
    element_id="counter_006",
    element_type="COUNTER",
    name="Counter with bad current",
    x=100,
    y=100,
    counter_type="UP",
    counter_start_value=0,
    counter_max_value=3,
    counter_current_value=5  # WARNING: außerhalb [0, 3]
)
doc6.add_element(counter_bad_current)

result6 = service.validate_document(doc6)

print(f"✅ Validierung abgeschlossen")
print(f"   Warnings: {len(result6.warnings)}")
print(f"   Sollte 1+ Warning haben (current außerhalb Range)")

if result6.warnings:
    print("   ⚠️ Warnings gefunden:")
    for warning in result6.warnings:
        print(f"      - {warning.message}")

print("\n" + "="*60)
print("✅ Alle Validierungs-Tests abgeschlossen!")
print("="*60)
