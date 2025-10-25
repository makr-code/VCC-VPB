"""
Tests für STATE-Element Validierung (StateValidator)

Testet 9 Kern-Validierungsregeln für STATE-Elemente.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vpb.models.element import VPBElement
from vpb.models.connection import VPBConnection
from vpb.models.document import DocumentModel
from vpb.services.validation_service import ValidationService, ValidationResult, StateValidator


def test_rule_1_state_name_empty():
    """Test Regel 1: State-Name darf nicht leer sein [ERROR]"""
    print("\n1️⃣ Test Regel 1: State-Name leer")
    
    doc = DocumentModel()
    state1 = VPBElement(
        element_id="state1",
        element_type="STATE",
        name="State1",
        x=100, y=100
    )
    state1.state_name = ""  # Leer - sollte ERROR
    state1.state_type = "NORMAL"
    doc.add_element(state1)
    
    validator = StateValidator()
    result = ValidationResult()
    validator.validate_state(state1, doc, result)
    
    assert len(result.errors) == 1, f"Expected 1 error, got {len(result.errors)}"
    assert "must have a name" in result.errors[0].message
    print(f"   ✓ ERROR: {result.errors[0].message}")


def test_rule_2_invalid_state_type():
    """Test Regel 2: State-Type ungültig [ERROR]"""
    print("\n2️⃣ Test Regel 2: State-Type ungültig")
    
    doc = DocumentModel()
    state1 = VPBElement(
        element_id="state1",
        element_type="STATE",
        name="State1",
        x=100, y=100
    )
    state1.state_name = "Test"
    state1.state_type = "INVALID_TYPE"  # Ungültig - sollte ERROR
    doc.add_element(state1)
    
    validator = StateValidator()
    result = ValidationResult()
    validator.validate_state(state1, doc, result)
    
    type_errors = [e for e in result.errors if "Invalid state type" in e.message]
    assert len(type_errors) == 1, f"Expected 1 type error, got {len(type_errors)}"
    assert "INVALID_TYPE" in type_errors[0].message
    print(f"   ✓ ERROR: {type_errors[0].message}")


def test_rule_3_multiple_initial_states():
    """Test Regel 3: Mehrere INITIAL-States [ERROR]"""
    print("\n3️⃣ Test Regel 3: Mehrere INITIAL-States")
    
    doc = DocumentModel()
    
    # Zwei INITIAL-States
    state1 = VPBElement(
        element_id="state1",
        element_type="STATE",
        name="Start 1",
        x=100, y=100
    )
    state1.state_name = "Start 1"
    state1.state_type = "INITIAL"
    
    state2 = VPBElement(
        element_id="state2",
        element_type="STATE",
        name="Start 2",
        x=200, y=100
    )
    state2.state_name = "Start 2"
    state2.state_type = "INITIAL"  # Zweiter INITIAL - sollte ERROR
    
    doc.add_element(state1)
    doc.add_element(state2)
    
    validator = StateValidator()
    result = ValidationResult()
    
    # Beide States validieren
    validator.validate_state(state1, doc, result)
    validator.validate_state(state2, doc, result)
    
    initial_errors = [e for e in result.errors if "Multiple INITIAL states" in e.message]
    assert len(initial_errors) >= 1, f"Expected at least 1 error for multiple INITIAL, got {len(initial_errors)}"
    print(f"   ✓ ERROR: {initial_errors[0].message}")


def test_rule_4_invalid_transition_target():
    """Test Regel 4: Transition mit ungültigem Ziel [WARNING]"""
    print("\n4️⃣ Test Regel 4: Transition mit ungültigem Ziel")
    
    doc = DocumentModel()
    
    state1 = VPBElement(
        element_id="state1",
        element_type="STATE",
        name="Start",
        x=100, y=100
    )
    state1.state_name = "Start"
    state1.state_type = "NORMAL"
    state1.state_transitions = [
        {
            "event": "submit",
            "target": "nonexistent_state",  # Existiert nicht - WARNING
            "condition": ""
        }
    ]
    doc.add_element(state1)
    
    validator = StateValidator()
    result = ValidationResult()
    validator.validate_state(state1, doc, result)
    
    target_warnings = [w for w in result.warnings if "does not exist" in w.message]
    assert len(target_warnings) == 1, f"Expected 1 warning for invalid target, got {len(target_warnings)}"
    assert "nonexistent_state" in target_warnings[0].message
    print(f"   ✓ WARNING: {target_warnings[0].message}")


def test_rule_5_entry_exit_actions_info():
    """Test Regel 5: Entry/Exit Actions [INFO]"""
    print("\n5️⃣ Test Regel 5: Entry/Exit Actions")
    
    doc = DocumentModel()
    
    state1 = VPBElement(
        element_id="state1",
        element_type="STATE",
        name="Active",
        x=100, y=100
    )
    state1.state_name = "Active"
    state1.state_type = "NORMAL"
    state1.state_entry_action = "console.log('entering')"  # Script
    state1.state_exit_action = "console.log('exiting')"  # Script
    doc.add_element(state1)
    
    validator = StateValidator()
    result = ValidationResult()
    validator.validate_state(state1, doc, result)
    
    action_info = [i for i in result.info if "action" in i.message.lower()]
    assert len(action_info) >= 2, f"Expected at least 2 info messages for actions, got {len(action_info)}"
    print(f"   ✓ INFO (Entry): {action_info[0].message}")
    print(f"   ✓ INFO (Exit): {action_info[1].message}")


def test_rule_6_timeout_without_target():
    """Test Regel 6: Timeout ohne Target [WARNING]"""
    print("\n6️⃣ Test Regel 6: Timeout ohne Target")
    
    doc = DocumentModel()
    
    state1 = VPBElement(
        element_id="state1",
        element_type="STATE",
        name="Waiting",
        x=100, y=100
    )
    state1.state_name = "Waiting"
    state1.state_type = "NORMAL"
    state1.state_timeout = 60  # Timeout gesetzt
    state1.state_timeout_target = ""  # Kein Target - WARNING
    doc.add_element(state1)
    
    validator = StateValidator()
    result = ValidationResult()
    validator.validate_state(state1, doc, result)
    
    timeout_warnings = [w for w in result.warnings if "timeout" in w.message.lower() and "no timeout target" in w.message.lower()]
    assert len(timeout_warnings) == 1, f"Expected 1 warning for timeout without target, got {len(timeout_warnings)}"
    print(f"   ✓ WARNING: {timeout_warnings[0].message}")


def test_rule_7_initial_with_incoming():
    """Test Regel 7: INITIAL mit eingehenden Verbindungen [WARNING]"""
    print("\n7️⃣ Test Regel 7: INITIAL mit eingehenden Verbindungen")
    
    doc = DocumentModel()
    
    state1 = VPBElement(
        element_id="state1",
        element_type="STATE",
        name="Start",
        x=100, y=100
    )
    state1.state_name = "Start"
    state1.state_type = "INITIAL"
    
    state2 = VPBElement(
        element_id="state2",
        element_type="STATE",
        name="Other",
        x=200, y=100
    )
    state2.state_name = "Other"
    state2.state_type = "NORMAL"
    
    doc.add_element(state1)
    doc.add_element(state2)
    
    # Verbindung ZU INITIAL (nicht typisch) - WARNING
    conn = VPBConnection(
        connection_id="conn1",
        source_element=state2,
        target_element=state1
    )
    doc.add_connection(conn)
    
    validator = StateValidator()
    result = ValidationResult()
    validator.validate_state(state1, doc, result)
    
    initial_warnings = [w for w in result.warnings if "INITIAL state has" in w.message and "incoming" in w.message]
    assert len(initial_warnings) == 1, f"Expected 1 warning for INITIAL with incoming, got {len(initial_warnings)}"
    print(f"   ✓ WARNING: {initial_warnings[0].message}")


def test_rule_8_final_with_outgoing():
    """Test Regel 8: FINAL mit ausgehenden Verbindungen [WARNING]"""
    print("\n8️⃣ Test Regel 8: FINAL mit ausgehenden Verbindungen")
    
    doc = DocumentModel()
    
    state1 = VPBElement(
        element_id="state1",
        element_type="STATE",
        name="End",
        x=100, y=100
    )
    state1.state_name = "End"
    state1.state_type = "FINAL"
    
    state2 = VPBElement(
        element_id="state2",
        element_type="STATE",
        name="Other",
        x=200, y=100
    )
    state2.state_name = "Other"
    state2.state_type = "NORMAL"
    
    doc.add_element(state1)
    doc.add_element(state2)
    
    # Verbindung VON FINAL (nicht typisch) - WARNING
    conn = VPBConnection(
        connection_id="conn1",
        source_element=state1,
        target_element=state2
    )
    doc.add_connection(conn)
    
    validator = StateValidator()
    result = ValidationResult()
    validator.validate_state(state1, doc, result)
    
    final_warnings = [w for w in result.warnings if "FINAL state has" in w.message and "outgoing" in w.message]
    assert len(final_warnings) == 1, f"Expected 1 warning for FINAL with outgoing, got {len(final_warnings)}"
    print(f"   ✓ WARNING: {final_warnings[0].message}")


def test_rule_9_normal_without_transitions():
    """Test Regel 9: NORMAL ohne Transitions [INFO]"""
    print("\n9️⃣ Test Regel 9: NORMAL ohne Transitions")
    
    doc = DocumentModel()
    
    state1 = VPBElement(
        element_id="state1",
        element_type="STATE",
        name="Idle",
        x=100, y=100
    )
    state1.state_name = "Idle"
    state1.state_type = "NORMAL"
    state1.state_transitions = []  # Keine Transitions - INFO
    doc.add_element(state1)
    
    validator = StateValidator()
    result = ValidationResult()
    validator.validate_state(state1, doc, result)
    
    trans_info = [i for i in result.info if "no transitions" in i.message.lower()]
    assert len(trans_info) == 1, f"Expected 1 info for no transitions, got {len(trans_info)}"
    print(f"   ✓ INFO: {trans_info[0].message}")


def test_comprehensive_validation_service():
    """Test komplette ValidationService Integration"""
    print("\n🔍 Test: ValidationService Integration")
    
    doc = DocumentModel()
    
    # Erstelle komplexe State-Machine
    state1 = VPBElement(
        element_id="state_start",
        element_type="STATE",
        name="Eingereicht",
        x=100, y=100
    )
    state1.state_name = "Eingereicht"
    state1.state_type = "INITIAL"
    
    state2 = VPBElement(
        element_id="state_review",
        element_type="STATE",
        name="In Prüfung",
        x=200, y=100
    )
    state2.state_name = "In Prüfung"
    state2.state_type = "NORMAL"
    state2.state_transitions = [
        {"event": "approve", "target": "state_approved", "condition": "valid==true"},
        {"event": "reject", "target": "state_rejected", "condition": ""}
    ]
    state2.state_timeout = 3600
    state2.state_timeout_target = "state_timeout"
    
    state3 = VPBElement(
        element_id="state_approved",
        element_type="STATE",
        name="Genehmigt",
        x=300, y=50
    )
    state3.state_name = "Genehmigt"
    state3.state_type = "FINAL"
    
    state4 = VPBElement(
        element_id="state_rejected",
        element_type="STATE",
        name="Abgelehnt",
        x=300, y=150
    )
    state4.state_name = "Abgelehnt"
    state4.state_type = "FINAL"
    
    state5 = VPBElement(
        element_id="state_timeout",
        element_type="STATE",
        name="Timeout",
        x=400, y=100
    )
    state5.state_name = "Timeout"
    state5.state_type = "ERROR"
    
    doc.add_element(state1)
    doc.add_element(state2)
    doc.add_element(state3)
    doc.add_element(state4)
    doc.add_element(state5)
    
    # Verbindungen (mit VPBElement-Objekten)
    doc.add_connection(VPBConnection(connection_id="c1", source_element=state1, target_element=state2))
    doc.add_connection(VPBConnection(connection_id="c2", source_element=state2, target_element=state3))
    doc.add_connection(VPBConnection(connection_id="c3", source_element=state2, target_element=state4))
    doc.add_connection(VPBConnection(connection_id="c4", source_element=state2, target_element=state5))
    
    # Validiere mit ValidationService
    service = ValidationService(check_naming=True, check_flow=True, check_completeness=True)
    result = service.validate_document(doc)
    
    print(f"   📊 Validation Results:")
    print(f"      Errors: {len(result.errors)}")
    print(f"      Warnings: {len(result.warnings)}")
    print(f"      Info: {len(result.info)}")
    
    # Sollte keine schweren Fehler haben (state_names alle gesetzt, types gültig, nur ein INITIAL)
    state_errors = [e for e in result.errors if e.category == "state"]
    assert len(state_errors) == 0, f"Expected no STATE errors, got {len(state_errors)}"
    
    print(f"   ✓ ValidationService integriert STATE-Validierung korrekt")


if __name__ == "__main__":
    print("=" * 60)
    print("STATE ELEMENT VALIDATION TESTS")
    print("=" * 60)
    
    tests = [
        # Kern-Regeln
        test_rule_1_state_name_empty,
        test_rule_2_invalid_state_type,
        test_rule_3_multiple_initial_states,
        test_rule_4_invalid_transition_target,
        test_rule_5_entry_exit_actions_info,
        test_rule_6_timeout_without_target,
        test_rule_7_initial_with_incoming,
        test_rule_8_final_with_outgoing,
        test_rule_9_normal_without_transitions,
        
        # Integration
        test_comprehensive_validation_service
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ FAILED: {test.__name__}")
            print(f"   {e}")
            failed += 1
        except Exception as e:
            print(f"\n💥 ERROR: {test.__name__}")
            print(f"   {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"TEST SUMMARY: {passed}/{len(tests)} tests PASSED")
    if failed > 0:
        print(f"⚠️  {failed} test(s) FAILED")
    else:
        print("✅ All tests PASSED!")
    print("=" * 60)
