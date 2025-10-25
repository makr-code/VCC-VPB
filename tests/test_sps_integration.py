"""
SPS Integration Tests - Tests für das Zusammenspiel aller 5 SPS-Elemente

Testet:
- Cross-Element Validierung
- Complex Workflows mit mehreren SPS-Elementen
- Integration zwischen COUNTER, CONDITION, ERROR_HANDLER, STATE, INTERLOCK
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vpb.models.element import VPBElement
from vpb.models.connection import VPBConnection
from vpb.models.document import DocumentModel
from vpb.services.validation_service import ValidationService, ValidationResult


def test_counter_with_condition():
    """Test: COUNTER mit CONDITION kombiniert"""
    print("\n[TEST 1] COUNTER + CONDITION Integration")
    
    doc = DocumentModel()
    
    # COUNTER
    counter = VPBElement(
        element_id="counter_1",
        element_type="COUNTER",
        name="Loop Counter",
        x=100, y=100
    )
    counter.counter_start_value = 1
    counter.counter_max_value = 10
    counter.counter_on_max_reached = "end"
    
    # CONDITION
    condition = VPBElement(
        element_id="condition_1",
        element_type="CONDITION",
        name="Check Counter",
        x=300, y=100
    )
    condition.condition_checks = [
        {
            "field": "counter_value",
            "operator": ">",
            "value": "5"
        }
    ]
    condition.condition_on_true_target = "high_branch"
    condition.condition_on_false_target = "low_branch"
    
    # Target elements
    high_branch = VPBElement(
        element_id="high_branch",
        element_type="Prozess",
        name="High Value Handler",
        x=500, y=50
    )
    
    low_branch = VPBElement(
        element_id="low_branch",
        element_type="Prozess",
        name="Low Value Handler",
        x=500, y=150
    )
    
    end = VPBElement(
        element_id="end",
        element_type="NachProzess",
        name="End",
        x=700, y=100
    )
    
    doc.add_element(counter)
    doc.add_element(condition)
    doc.add_element(high_branch)
    doc.add_element(low_branch)
    doc.add_element(end)
    
    # Connections (using element objects, not IDs)
    doc.add_connection(VPBConnection(connection_id="conn1", source_element=counter, target_element=condition))
    doc.add_connection(VPBConnection(connection_id="conn2", source_element=condition, target_element=high_branch))
    doc.add_connection(VPBConnection(connection_id="conn3", source_element=condition, target_element=low_branch))
    doc.add_connection(VPBConnection(connection_id="conn4", source_element=high_branch, target_element=counter))
    doc.add_connection(VPBConnection(connection_id="conn5", source_element=low_branch, target_element=counter))
    
    # Validate
    validator = ValidationService()
    result = validator.validate_document(doc)
    
    errors = [e for e in result.errors if e.category in ["counter", "condition"]]
    assert len(errors) == 0, f"Expected no errors, got {len(errors)}: {[e.message for e in errors]}"
    
    print("✅ COUNTER + CONDITION Integration funktioniert")


def test_state_with_interlock():
    """Test: STATE mit INTERLOCK kombiniert"""
    print("\n[TEST 2] STATE + INTERLOCK Integration")
    
    doc = DocumentModel()
    
    # STATE
    state = VPBElement(
        element_id="state_1",
        element_type="STATE",
        name="Processing State",
        x=100, y=100
    )
    state.state_name = "processing"
    state.state_type = "NORMAL"
    state.state_transitions = [
        {
            "condition": "done == true",
            "target": "state_2",
            "label": "Complete"
        }
    ]
    
    state2 = VPBElement(
        element_id="state_2",
        element_type="STATE",
        name="Done State",
        x=500, y=100
    )
    state2.state_name = "done"
    state2.state_type = "FINAL"
    state2.state_transitions = []
    
    # INTERLOCK
    interlock = VPBElement(
        element_id="interlock_1",
        element_type="INTERLOCK",
        name="DB Lock",
        x=300, y=100
    )
    interlock.interlock_type = "MUTEX"
    interlock.interlock_resource_id = "db_connection"
    interlock.interlock_max_count = 1
    interlock.interlock_timeout = 30
    interlock.interlock_on_locked_target = ""
    interlock.interlock_auto_release = True
    
    doc.add_element(state)
    doc.add_element(state2)
    doc.add_element(interlock)
    
    # Connections (using element objects, not IDs)
    doc.add_connection(VPBConnection(connection_id="conn1", source_element=state, target_element=interlock))
    doc.add_connection(VPBConnection(connection_id="conn2", source_element=interlock, target_element=state2))
    
    # Validate
    validator = ValidationService()
    result = validator.validate_document(doc)
    
    errors = [e for e in result.errors if e.category in ["state", "interlock"]]
    assert len(errors) == 0, f"Expected no errors, got {len(errors)}: {[e.message for e in errors]}"
    
    print("✅ STATE + INTERLOCK Integration funktioniert")


def test_error_handler_with_counter():
    """Test: ERROR_HANDLER mit COUNTER für Retry-Tracking"""
    print("\n[TEST 3] ERROR_HANDLER + COUNTER für Retry-Tracking")
    
    doc = DocumentModel()
    
    # ERROR_HANDLER
    error_handler = VPBElement(
        element_id="error_1",
        element_type="ERROR_HANDLER",
        name="API Error",
        x=100, y=100
    )
    error_handler.error_type = "NetworkError"
    error_handler.error_message = "API call failed"
    error_handler.error_retry_count = 3
    error_handler.error_on_retry_target = "api_call"
    error_handler.error_on_fatal_target = "fatal"
    
    # COUNTER für Retry-Tracking
    counter = VPBElement(
        element_id="retry_counter",
        element_type="COUNTER",
        name="Retry Counter",
        x=300, y=100
    )
    counter.counter_start_value = 0
    counter.counter_max_value = 3
    counter.counter_on_max_reached = "fatal"
    
    # Target elements
    api_call = VPBElement(
        element_id="api_call",
        element_type="Prozess",
        name="API Call",
        x=500, y=100
    )
    
    fatal = VPBElement(
        element_id="fatal",
        element_type="Prozess",
        name="Fatal Error",
        x=700, y=100
    )
    
    doc.add_element(error_handler)
    doc.add_element(counter)
    doc.add_element(api_call)
    doc.add_element(fatal)
    
    # Connections (using element objects, not IDs)
    doc.add_connection(VPBConnection(connection_id="conn1", source_element=error_handler, target_element=counter))
    doc.add_connection(VPBConnection(connection_id="conn2", source_element=counter, target_element=api_call))
    
    # Validate
    validator = ValidationService()
    result = validator.validate_document(doc)
    
    errors = [e for e in result.errors if e.category in ["error_handler", "counter"]]
    assert len(errors) == 0, f"Expected no errors, got {len(errors)}: {[e.message for e in errors]}"
    
    print("✅ ERROR_HANDLER + COUNTER Integration funktioniert")


def test_all_five_elements_complex():
    """Test: Alle 5 SPS-Elemente in einem komplexen Workflow"""
    print("\n[TEST 4] Alle 5 SPS-Elemente zusammen")
    
    doc = DocumentModel()
    
    # 1. COUNTER - Batch processing
    counter = VPBElement(
        element_id="batch_counter",
        element_type="COUNTER",
        name="Batch Counter",
        x=100, y=100
    )
    counter.counter_start_value = 1
    counter.counter_max_value = 100
    counter.counter_on_max_reached = "batch_done"
    
    # 2. INTERLOCK - DB Pool
    interlock = VPBElement(
        element_id="db_pool",
        element_type="INTERLOCK",
        name="DB Pool",
        x=300, y=100
    )
    interlock.interlock_type = "SEMAPHORE"
    interlock.interlock_resource_id = "db_conn_pool"
    interlock.interlock_max_count = 5
    interlock.interlock_timeout = 30
    interlock.interlock_on_locked_target = "db_busy"
    interlock.interlock_auto_release = True
    
    # 3. STATE - Processing State
    state = VPBElement(
        element_id="processing_state",
        element_type="STATE",
        name="Processing",
        x=500, y=100
    )
    state.state_name = "processing"
    state.state_type = "NORMAL"
    state.state_transitions = [
        {
            "condition": "success == true",
            "target": "done_state",
            "label": "Success"
        },
        {
            "condition": "error == true",
            "target": "error_state",
            "label": "Error"
        }
    ]
    
    # 4. CONDITION - Decision Point
    condition = VPBElement(
        element_id="check_result",
        element_type="CONDITION",
        name="Check Result",
        x=700, y=100
    )
    condition.condition_checks = [
        {
            "field": "validation",
            "operator": "==",
            "value": "passed"
        }
    ]
    condition.condition_on_true_target = "done_state"
    condition.condition_on_false_target = "error_handler"
    
    # 5. ERROR_HANDLER - Error Handling
    error_handler = VPBElement(
        element_id="error_handler",
        element_type="ERROR_HANDLER",
        name="Error Handler",
        x=900, y=100
    )
    error_handler.error_type = "ProcessingError"
    error_handler.error_message = "Processing failed"
    error_handler.error_retry_count = 3
    error_handler.error_on_retry_target = "processing_state"
    error_handler.error_on_fatal_target = "error_state"
    
    # Additional states
    done_state = VPBElement(
        element_id="done_state",
        element_type="STATE",
        name="Done",
        x=500, y=300
    )
    done_state.state_name = "done"
    done_state.state_type = "FINAL"
    done_state.state_transitions = []
    
    error_state = VPBElement(
        element_id="error_state",
        element_type="STATE",
        name="Error",
        x=900, y=300
    )
    error_state.state_name = "error"
    error_state.state_type = "ERROR"
    error_state.state_transitions = []
    
    # Additional elements
    db_busy = VPBElement(
        element_id="db_busy",
        element_type="Prozess",
        name="DB Busy Handler",
        x=300, y=300
    )
    
    batch_done = VPBElement(
        element_id="batch_done",
        element_type="NachProzess",
        name="Batch Complete",
        x=100, y=500
    )
    
    # Add all elements
    for el in [counter, interlock, state, condition, error_handler, done_state, error_state, db_busy, batch_done]:
        doc.add_element(el)
    
    # Add connections (using element objects, not IDs)
    doc.add_connection(VPBConnection(connection_id="conn1", source_element=counter, target_element=interlock))
    doc.add_connection(VPBConnection(connection_id="conn2", source_element=interlock, target_element=state))
    doc.add_connection(VPBConnection(connection_id="conn3", source_element=state, target_element=condition))
    doc.add_connection(VPBConnection(connection_id="conn4", source_element=condition, target_element=done_state))
    doc.add_connection(VPBConnection(connection_id="conn5", source_element=condition, target_element=error_handler))
    doc.add_connection(VPBConnection(connection_id="conn6", source_element=error_handler, target_element=state))
    doc.add_connection(VPBConnection(connection_id="conn7", source_element=error_handler, target_element=error_state))
    doc.add_connection(VPBConnection(connection_id="conn8", source_element=done_state, target_element=counter))
    doc.add_connection(VPBConnection(connection_id="conn9", source_element=error_state, target_element=counter))
    doc.add_connection(VPBConnection(connection_id="conn10", source_element=interlock, target_element=db_busy))
    doc.add_connection(VPBConnection(connection_id="conn11", source_element=db_busy, target_element=interlock))
    
    # Validate
    validator = ValidationService()
    result = validator.validate_document(doc)
    
    # Check for errors in SPS elements
    sps_errors = [e for e in result.errors if e.category in ["counter", "condition", "error_handler", "state", "interlock"]]
    assert len(sps_errors) == 0, f"Expected no SPS errors, got {len(sps_errors)}: {[e.message for e in sps_errors]}"
    
    # Verify all 5 element types are present
    element_types = {el.element_type for el in doc.get_all_elements()}
    assert "COUNTER" in element_types, "COUNTER element missing"
    assert "CONDITION" in element_types, "CONDITION element missing"
    assert "ERROR_HANDLER" in element_types, "ERROR_HANDLER element missing"
    assert "STATE" in element_types, "STATE element missing"
    assert "INTERLOCK" in element_types, "INTERLOCK element missing"
    
    print(f"✅ Alle 5 SPS-Elemente erfolgreich integriert ({len(doc.get_all_elements())} elements, {len(doc.get_all_connections())} connections)")


def test_multiple_interlocks_same_resource():
    """Test: Mehrere INTERLOCKs mit gleicher Resource-ID"""
    print("\n[TEST 5] Mehrere INTERLOCKs koordinieren gleiche Ressource")
    
    doc = DocumentModel()
    
    # INTERLOCK 1
    interlock1 = VPBElement(
        element_id="interlock_1",
        element_type="INTERLOCK",
        name="DB Lock 1",
        x=100, y=100
    )
    interlock1.interlock_type = "SEMAPHORE"
    interlock1.interlock_resource_id = "shared_db_pool"  # GLEICHE Resource-ID
    interlock1.interlock_max_count = 5
    interlock1.interlock_timeout = 30
    interlock1.interlock_on_locked_target = ""
    interlock1.interlock_auto_release = True
    
    # INTERLOCK 2 mit gleicher Resource-ID
    interlock2 = VPBElement(
        element_id="interlock_2",
        element_type="INTERLOCK",
        name="DB Lock 2",
        x=300, y=100
    )
    interlock2.interlock_type = "SEMAPHORE"
    interlock2.interlock_resource_id = "shared_db_pool"  # GLEICHE Resource-ID
    interlock2.interlock_max_count = 5
    interlock2.interlock_timeout = 30
    interlock2.interlock_on_locked_target = ""
    interlock2.interlock_auto_release = True
    
    # INTERLOCK 3 mit gleicher Resource-ID
    interlock3 = VPBElement(
        element_id="interlock_3",
        element_type="INTERLOCK",
        name="DB Lock 3",
        x=500, y=100
    )
    interlock3.interlock_type = "SEMAPHORE"
    interlock3.interlock_resource_id = "shared_db_pool"  # GLEICHE Resource-ID
    interlock3.interlock_max_count = 5
    interlock3.interlock_timeout = 30
    interlock3.interlock_on_locked_target = ""
    interlock3.interlock_auto_release = True
    
    doc.add_element(interlock1)
    doc.add_element(interlock2)
    doc.add_element(interlock3)
    
    # Validate
    validator = ValidationService()
    result = validator.validate_document(doc)
    
    # Should have warnings about duplicate resource_id (but no errors)
    warnings = [w for w in result.warnings if w.category == "interlock" and "is used by" in w.message]
    assert len(warnings) >= 3, f"Expected at least 3 warnings for duplicate resource_id, got {len(warnings)}"
    
    errors = [e for e in result.errors if e.category == "interlock"]
    assert len(errors) == 0, f"Expected no errors, got {len(errors)}: {[e.message for e in errors]}"
    
    print(f"✅ Mehrere INTERLOCKs koordinieren erfolgreich (3 INTERLOCKs, {len(warnings)} warnings)")


def run_all_tests():
    """Führt alle Integration-Tests aus"""
    print("=" * 70)
    print("SPS INTEGRATION TESTS")
    print("=" * 70)
    
    tests = [
        test_counter_with_condition,
        test_state_with_interlock,
        test_error_handler_with_counter,
        test_all_five_elements_complex,
        test_multiple_interlocks_same_resource
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
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    if failed > 0:
        print(f"⚠️  {failed} tests failed")
    else:
        print("✅ All integration tests passed!")
    print("=" * 70)
    
    return passed, failed


if __name__ == "__main__":
    passed, failed = run_all_tests()
    sys.exit(0 if failed == 0 else 1)
