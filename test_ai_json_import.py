#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test-Skript für AI-JSON-Import mit dirtyjson"""

from ollama_client import OllamaClient

# Test 1: Gültiges JSON
print("=" * 60)
print("Test 1: Gültiges JSON")
print("=" * 60)
valid_json = """
```json
{
  "metadata": {"version": "1.0"},
  "elements": [
    {"element_id": "elem_1", "name": "Test", "x": 100, "y": 200}
  ],
  "connections": []
}
```
"""
try:
    result = OllamaClient.extract_json(valid_json)
    print(f"✅ Resultat: {len(result.get('elements', []))} Elemente")
except Exception as e:
    print(f"❌ Fehler: {e}")

# Test 2: JSON mit Trailing Commas
print("\n" + "=" * 60)
print("Test 2: JSON mit Trailing Commas")
print("=" * 60)
trailing_json = """
```json
{
  "metadata": {"version": "1.0"},
  "elements": [
    {"element_id": "elem_1", "name": "Test", "x": 100, "y": 200},
  ],
  "connections": [],
}
```
"""
try:
    result = OllamaClient.extract_json(trailing_json)
    print(f"✅ Resultat: {len(result.get('elements', []))} Elemente")
except Exception as e:
    print(f"❌ Fehler: {e}")

# Test 3: JSON mit Kommentaren (dirtyjson sollte es parsen)
print("\n" + "=" * 60)
print("Test 3: JSON mit unquoted keys (dirtyjson)")
print("=" * 60)
dirty_json = """
{
  metadata: {version: "1.0"},
  elements: [
    {element_id: "elem_1", name: "Test", x: 100, y: 200}
  ],
  connections: []
}
"""
try:
    result = OllamaClient.extract_json(dirty_json)
    print(f"✅ Resultat: {len(result.get('elements', []))} Elemente")
except Exception as e:
    print(f"❌ Fehler: {e}")

# Test 4: Vollständiger Prozess (wie AI ihn generiert)
print("\n" + "=" * 60)
print("Test 4: Vollständiger AI-Prozess")
print("=" * 60)
ai_response = """
Hier ist der generierte Prozess:

```json
{
  "metadata": {
    "version": "1.0",
    "description": "Baugenehmigungsverfahren"
  },
  "elements": [
    {
      "element_id": "start_001",
      "element_type": "START_EVENT",
      "name": "Antrag eingegangen",
      "x": 100,
      "y": 200,
      "description": "Bauantrag beim Bauamt eingereicht"
    },
    {
      "element_id": "func_001",
      "element_type": "FUNCTION",
      "name": "Formale Prüfung",
      "x": 300,
      "y": 200,
      "responsible_authority": "Bauamt - Sachbearbeitung",
      "legal_basis": "§ 68 BauO",
      "deadline_days": 14
    },
    {
      "element_id": "end_001",
      "element_type": "END_EVENT",
      "name": "Genehmigung erteilt",
      "x": 500,
      "y": 200
    }
  ],
  "connections": [
    {
      "connection_id": "conn_001",
      "source_element": "start_001",
      "target_element": "func_001",
      "connection_type": "SEQUENCE"
    },
    {
      "connection_id": "conn_002",
      "source_element": "func_001",
      "target_element": "end_001",
      "connection_type": "SEQUENCE"
    }
  ]
}
```

Der Prozess enthält die wichtigsten Schritte des Baugenehmigungsverfahrens.
"""

try:
    result = OllamaClient.extract_json(ai_response)
    elem_count = len(result.get('elements', []))
    conn_count = len(result.get('connections', []))
    print(f"✅ Erfolgreich: {elem_count} Elemente, {conn_count} Verbindungen")
    
    # Zeige erste Element-Details
    if elem_count > 0:
        first_elem = result['elements'][0]
        print(f"\n📝 Erstes Element:")
        print(f"   ID: {first_elem.get('element_id')}")
        print(f"   Typ: {first_elem.get('element_type')}")
        print(f"   Name: {first_elem.get('name')}")
        print(f"   Position: ({first_elem.get('x')}, {first_elem.get('y')})")
        
except Exception as e:
    print(f"❌ Fehler: {e}")

print("\n" + "=" * 60)
print("Tests abgeschlossen")
print("=" * 60)
