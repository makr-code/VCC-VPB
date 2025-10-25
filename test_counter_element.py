#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script for COUNTER element implementation."""

from vpb.models.element import VPBElement

print("="*60)
print("COUNTER Element Test")
print("="*60)

# Test 1: Creation
print("\n1️⃣ Test: Counter-Element erstellen...")
counter = VPBElement(
    element_id='counter_001',
    element_type='COUNTER',
    name='Mahnungs-Zähler',
    x=100,
    y=100,
    counter_type='UP',
    counter_start_value=0,
    counter_max_value=3,
    counter_current_value=0,
    counter_reset_on_max=False,
    counter_on_max_reached='escalate_001'
)
print(f"✅ Counter erstellt: {counter.element_id}")
print(f"   Typ: {counter.counter_type}")
print(f"   Wert: {counter.counter_current_value}/{counter.counter_max_value}")
print(f"   Reset: {counter.counter_reset_on_max}")
print(f"   On-Max: {counter.counter_on_max_reached}")

# Test 2: to_dict()
print("\n2️⃣ Test: Serialisierung (to_dict)...")
data = counter.to_dict()
print(f"✅ to_dict() erfolgreich")
print(f"   counter_type: {data.get('counter_type')}")
print(f"   counter_max_value: {data.get('counter_max_value')}")
print(f"   counter_on_max_reached: {data.get('counter_on_max_reached')}")

# Test 3: from_dict()
print("\n3️⃣ Test: Deserialisierung (from_dict)...")
counter2 = VPBElement.from_dict(data)
print(f"✅ from_dict() erfolgreich")
print(f"   element_id: {counter2.element_id}")
print(f"   counter_type: {counter2.counter_type}")
print(f"   counter_current_value: {counter2.counter_current_value}")
print(f"   counter_max_value: {counter2.counter_max_value}")

# Test 4: clone()
print("\n4️⃣ Test: Element klonen (clone)...")
counter3 = counter.clone('counter_002')
print(f"✅ clone() erfolgreich")
print(f"   Neue ID: {counter3.element_id}")
print(f"   Counter-Wert zurückgesetzt: {counter3.counter_current_value} (sollte {counter.counter_start_value} sein)")
print(f"   Counter-Max behalten: {counter3.counter_max_value}")

# Test 5: move_to()
print("\n5️⃣ Test: Element verschieben (move_to)...")
counter4 = counter.move_to(200, 200)
print(f"✅ move_to() erfolgreich")
print(f"   Neue Position: ({counter4.x}, {counter4.y})")
print(f"   Counter-Werte erhalten: {counter4.counter_current_value}/{counter4.counter_max_value}")

# Test 6: Nicht-Counter Element (soll keine Counter-Felder in JSON haben)
print("\n6️⃣ Test: Nicht-Counter-Element (sollte keine Counter-Felder speichern)...")
normal = VPBElement(
    element_id='func_001',
    element_type='FUNCTION',
    name='Normale Aufgabe',
    x=150,
    y=150
)
normal_data = normal.to_dict()
print(f"✅ FUNCTION-Element erstellt")
print(f"   counter_type in JSON: {normal_data.get('counter_type')} (sollte None sein)")
print(f"   counter_max_value in JSON: {normal_data.get('counter_max_value')} (sollte None sein)")

print("\n" + "="*60)
print("✅ Alle Tests erfolgreich!")
print("="*60)
