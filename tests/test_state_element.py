"""
Tests für STATE Element Schema.

Testet die VPBElement Erweiterungen für STATE-Elemente.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vpb.models.element import VPBElement


def test_state_element_creation():
    """Test: STATE Element mit allen Properties erstellen"""
    print("\n=== Test 1: STATE Element Erstellung ===")
    
    element = VPBElement(
        element_id="state1",
        element_type="STATE",
        name="Eingereicht",
        x=100,
        y=200,
        state_name="Eingereicht",
        state_type="INITIAL",
        state_entry_action="log_entry",
        state_exit_action="log_exit",
        state_transitions=[
            {"event": "approve", "target": "state2", "condition": "valid"},
            {"event": "reject", "target": "state3", "condition": ""}
        ],
        state_timeout=300,
        state_timeout_target="timeout_handler"
    )
    
    assert element.element_id == "state1"
    assert element.element_type == "STATE"
    assert element.state_name == "Eingereicht"
    assert element.state_type == "INITIAL"
    assert element.state_entry_action == "log_entry"
    assert element.state_exit_action == "log_exit"
    assert len(element.state_transitions) == 2
    assert element.state_timeout == 300
    assert element.state_timeout_target == "timeout_handler"
    
    print("✓ STATE Element erfolgreich erstellt")


def test_state_default_values():
    """Test: STATE Element mit Default-Werten"""
    print("\n=== Test 2: STATE Default-Werte ===")
    
    element = VPBElement(
        element_id="state2",
        element_type="STATE",
        name="Normal State",
        x=150,
        y=250
    )
    
    assert element.state_name == ""
    assert element.state_type == "NORMAL"
    assert element.state_entry_action == ""
    assert element.state_exit_action == ""
    assert element.state_transitions == []
    assert element.state_timeout == 0
    assert element.state_timeout_target == ""
    
    print("✓ Default-Werte korrekt")


def test_state_to_dict():
    """Test: STATE Element to_dict Serialization"""
    print("\n=== Test 3: to_dict() Serialization ===")
    
    element = VPBElement(
        element_id="state3",
        element_type="STATE",
        name="In Bearbeitung",
        x=200,
        y=300,
        state_name="In Bearbeitung",
        state_type="NORMAL",
        state_entry_action="start_timer",
        state_exit_action="stop_timer",
        state_transitions=[{"event": "complete", "target": "state4"}],
        state_timeout=600
    )
    
    data = element.to_dict()
    
    assert data["element_id"] == "state3"
    assert data["element_type"] == "STATE"
    assert data["state_name"] == "In Bearbeitung"
    assert data["state_type"] == "NORMAL"
    assert data["state_entry_action"] == "start_timer"
    assert data["state_exit_action"] == "stop_timer"
    assert len(data["state_transitions"]) == 1
    assert data["state_timeout"] == 600
    
    print("✓ to_dict() funktioniert korrekt")


def test_state_to_dict_conditional():
    """Test: Conditional Serialization (nur STATE-Felder bei STATE)"""
    print("\n=== Test 4: Conditional Serialization ===")
    
    # Non-STATE Element sollte keine STATE-Properties haben
    element = VPBElement(
        element_id="normal1",
        element_type="Prozess",
        name="Normal Process",
        x=100,
        y=100
    )
    
    data = element.to_dict()
    
    assert data["state_name"] is None
    assert data["state_type"] is None
    assert data["state_entry_action"] is None
    assert data["state_exit_action"] is None
    assert data["state_transitions"] is None
    assert data["state_timeout"] is None
    assert data["state_timeout_target"] is None
    
    print("✓ Conditional Serialization funktioniert")


def test_state_from_dict():
    """Test: STATE Element from_dict Deserialization"""
    print("\n=== Test 5: from_dict() Deserialization ===")
    
    data = {
        "element_id": "state5",
        "element_type": "STATE",
        "name": "Abgeschlossen",
        "x": 300,
        "y": 400,
        "state_name": "Abgeschlossen",
        "state_type": "FINAL",
        "state_entry_action": "notify_user",
        "state_exit_action": "",
        "state_transitions": [],
        "state_timeout": 0,
        "state_timeout_target": ""
    }
    
    element = VPBElement.from_dict(data)
    
    assert element.element_id == "state5"
    assert element.element_type == "STATE"
    assert element.state_name == "Abgeschlossen"
    assert element.state_type == "FINAL"
    assert element.state_entry_action == "notify_user"
    assert element.state_exit_action == ""
    assert element.state_transitions == []
    assert element.state_timeout == 0
    
    print("✓ from_dict() funktioniert korrekt")


def test_state_from_dict_missing_fields():
    """Test: from_dict mit fehlenden STATE-Feldern (Defaults)"""
    print("\n=== Test 6: from_dict() mit fehlenden Feldern ===")
    
    data = {
        "element_id": "state6",
        "element_type": "STATE",
        "name": "Minimal State",
        "x": 400,
        "y": 500
    }
    
    element = VPBElement.from_dict(data)
    
    assert element.state_name == ""
    assert element.state_type == "NORMAL"
    assert element.state_entry_action == ""
    assert element.state_exit_action == ""
    assert element.state_transitions == []
    assert element.state_timeout == 0
    assert element.state_timeout_target == ""
    
    print("✓ Fehlende Felder erhalten Defaults")


def test_state_clone():
    """Test: STATE Element clone()"""
    print("\n=== Test 7: clone() Methode ===")
    
    original = VPBElement(
        element_id="state_orig",
        element_type="STATE",
        name="Original State",
        x=100,
        y=200,
        state_name="Original",
        state_type="NORMAL",
        state_entry_action="entry",
        state_exit_action="exit",
        state_transitions=[{"event": "test", "target": "other"}],
        state_timeout=120,
        state_timeout_target="timeout"
    )
    
    cloned = original.clone("state_clone")
    
    assert cloned.element_id == "state_clone"
    assert cloned.element_type == "STATE"
    assert cloned.x == 120  # +20 offset
    assert cloned.y == 220  # +20 offset
    assert cloned.state_name == "Original"
    assert cloned.state_type == "NORMAL"
    assert cloned.state_entry_action == "entry"
    assert cloned.state_exit_action == "exit"
    assert len(cloned.state_transitions) == 1
    assert cloned.state_timeout == 120
    assert cloned.state_timeout_target == "timeout"
    
    # Transitions sollten kopiert sein (nicht referenz)
    assert cloned.state_transitions is not original.state_transitions
    
    print("✓ clone() funktioniert korrekt")


def test_state_roundtrip():
    """Test: Roundtrip to_dict() → from_dict()"""
    print("\n=== Test 8: Roundtrip Serialization ===")
    
    original = VPBElement(
        element_id="state_round",
        element_type="STATE",
        name="Roundtrip State",
        x=500,
        y=600,
        state_name="Roundtrip",
        state_type="NORMAL",
        state_entry_action="action1",
        state_exit_action="action2",
        state_transitions=[
            {"event": "e1", "target": "t1"},
            {"event": "e2", "target": "t2"}
        ],
        state_timeout=180,
        state_timeout_target="timeout_elem"
    )
    
    # Serialisieren
    data = original.to_dict()
    
    # Deserialisieren
    restored = VPBElement.from_dict(data)
    
    # Vergleichen
    assert restored.element_id == original.element_id
    assert restored.state_name == original.state_name
    assert restored.state_type == original.state_type
    assert restored.state_entry_action == original.state_entry_action
    assert restored.state_exit_action == original.state_exit_action
    assert len(restored.state_transitions) == len(original.state_transitions)
    assert restored.state_timeout == original.state_timeout
    assert restored.state_timeout_target == original.state_timeout_target
    
    print("✓ Roundtrip erfolgreich")


def test_state_types():
    """Test: Verschiedene State-Typen"""
    print("\n=== Test 9: State-Typen ===")
    
    types = ["NORMAL", "INITIAL", "FINAL", "ERROR"]
    
    for state_type in types:
        element = VPBElement(
            element_id=f"state_{state_type.lower()}",
            element_type="STATE",
            name=f"{state_type} State",
            x=100,
            y=100,
            state_type=state_type
        )
        
        assert element.state_type == state_type
        print(f"  ✓ {state_type} State erstellt")
    
    print("✓ Alle State-Typen funktionieren")


def test_state_transitions_structure():
    """Test: Transitions Liste Struktur"""
    print("\n=== Test 10: Transitions Struktur ===")
    
    transitions = [
        {"event": "submit", "target": "state_review", "condition": "valid"},
        {"event": "cancel", "target": "state_cancelled", "condition": ""},
        {"event": "timeout", "target": "state_error", "condition": "timeout > 300"}
    ]
    
    element = VPBElement(
        element_id="state_trans",
        element_type="STATE",
        name="State with Transitions",
        x=100,
        y=100,
        state_transitions=transitions
    )
    
    assert len(element.state_transitions) == 3
    assert element.state_transitions[0]["event"] == "submit"
    assert element.state_transitions[1]["target"] == "state_cancelled"
    assert element.state_transitions[2]["condition"] == "timeout > 300"
    
    # Roundtrip
    data = element.to_dict()
    restored = VPBElement.from_dict(data)
    
    assert len(restored.state_transitions) == 3
    assert restored.state_transitions[0]["event"] == "submit"
    
    print("✓ Transitions Struktur korrekt")


def run_all_tests():
    """Run all STATE schema tests"""
    print("\n" + "="*60)
    print("STATE ELEMENT SCHEMA TESTS")
    print("="*60)
    
    tests = [
        test_state_element_creation,
        test_state_default_values,
        test_state_to_dict,
        test_state_to_dict_conditional,
        test_state_from_dict,
        test_state_from_dict_missing_fields,
        test_state_clone,
        test_state_roundtrip,
        test_state_types,
        test_state_transitions_structure
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
