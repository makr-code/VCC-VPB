"""
Tests für ERROR_HANDLER Element Schema.

Testet die ERROR_HANDLER-spezifischen Felder in VPBElement.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vpb.models.element import VPBElement


def test_error_handler_creation():
    """Test: ERROR_HANDLER Element mit Standard-Werten erstellen."""
    print("\n=== Test 1: ERROR_HANDLER Erstellung ===")
    
    eh = VPBElement(
        element_id="eh_1",
        element_type="ERROR_HANDLER",
        name="Retry Handler",
        x=100, y=100
    )
    
    # Standard-Werte prüfen
    assert eh.error_handler_type == "RETRY"
    assert eh.error_handler_retry_count == 3
    assert eh.error_handler_retry_delay == 60
    assert eh.error_handler_timeout == 300
    assert eh.error_handler_on_error_target == ""
    assert eh.error_handler_on_success_target == ""
    assert eh.error_handler_log_errors == True
    
    print(f"✓ ERROR_HANDLER erstellt: {eh.name}")
    print(f"  Type: {eh.error_handler_type}")
    print(f"  Retry Count: {eh.error_handler_retry_count}")
    print(f"  Retry Delay: {eh.error_handler_retry_delay}s")
    print(f"  Timeout: {eh.error_handler_timeout}s")


def test_error_handler_types():
    """Test: Verschiedene Handler-Typen."""
    print("\n=== Test 2: Handler-Typen ===")
    
    types = ["RETRY", "FALLBACK", "NOTIFY", "ABORT"]
    
    for handler_type in types:
        eh = VPBElement(
            element_id=f"eh_{handler_type.lower()}",
            element_type="ERROR_HANDLER",
            name=f"{handler_type} Handler",
            x=100, y=100,
            error_handler_type=handler_type
        )
        
        assert eh.error_handler_type == handler_type
        print(f"✓ Handler-Type '{handler_type}' gesetzt")


def test_error_handler_retry_config():
    """Test: Retry-Konfiguration."""
    print("\n=== Test 3: Retry-Konfiguration ===")
    
    eh = VPBElement(
        element_id="eh_retry",
        element_type="ERROR_HANDLER",
        name="Custom Retry",
        x=100, y=100,
        error_handler_type="RETRY",
        error_handler_retry_count=5,
        error_handler_retry_delay=120,
        error_handler_timeout=600
    )
    
    assert eh.error_handler_retry_count == 5
    assert eh.error_handler_retry_delay == 120
    assert eh.error_handler_timeout == 600
    
    print(f"✓ Retry-Config: {eh.error_handler_retry_count} Versuche, {eh.error_handler_retry_delay}s Delay, {eh.error_handler_timeout}s Timeout")


def test_error_handler_targets():
    """Test: Error/Success Targets."""
    print("\n=== Test 4: Error/Success Targets ===")
    
    eh = VPBElement(
        element_id="eh_targets",
        element_type="ERROR_HANDLER",
        name="Handler mit Targets",
        x=100, y=100,
        error_handler_on_error_target="func_error_log",
        error_handler_on_success_target="func_continue"
    )
    
    assert eh.error_handler_on_error_target == "func_error_log"
    assert eh.error_handler_on_success_target == "func_continue"
    
    print(f"✓ Error-Target: {eh.error_handler_on_error_target}")
    print(f"✓ Success-Target: {eh.error_handler_on_success_target}")


def test_error_handler_logging():
    """Test: Error-Logging aktivieren/deaktivieren."""
    print("\n=== Test 5: Error-Logging ===")
    
    # Mit Logging (Standard)
    eh1 = VPBElement(
        element_id="eh_log_on",
        element_type="ERROR_HANDLER",
        name="Mit Logging",
        x=100, y=100,
        error_handler_log_errors=True
    )
    assert eh1.error_handler_log_errors == True
    print("✓ Logging aktiviert")
    
    # Ohne Logging
    eh2 = VPBElement(
        element_id="eh_log_off",
        element_type="ERROR_HANDLER",
        name="Ohne Logging",
        x=100, y=100,
        error_handler_log_errors=False
    )
    assert eh2.error_handler_log_errors == False
    print("✓ Logging deaktiviert")


def test_error_handler_serialization():
    """Test: Serialisierung/Deserialisierung."""
    print("\n=== Test 6: Serialisierung ===")
    
    # Element erstellen
    eh = VPBElement(
        element_id="eh_serial",
        element_type="ERROR_HANDLER",
        name="Serialization Test",
        x=200, y=300,
        error_handler_type="FALLBACK",
        error_handler_retry_count=5,
        error_handler_retry_delay=90,
        error_handler_timeout=500,
        error_handler_on_error_target="func_fallback",
        error_handler_on_success_target="func_next",
        error_handler_log_errors=True
    )
    
    # to_dict()
    data = eh.to_dict()
    assert data['element_id'] == "eh_serial"
    assert data['element_type'] == "ERROR_HANDLER"
    assert data['error_handler_type'] == "FALLBACK"
    assert data['error_handler_retry_count'] == 5
    assert data['error_handler_retry_delay'] == 90
    assert data['error_handler_timeout'] == 500
    assert data['error_handler_on_error_target'] == "func_fallback"
    assert data['error_handler_on_success_target'] == "func_next"
    assert data['error_handler_log_errors'] == True
    print("✓ to_dict() erfolgreich")
    
    # from_dict()
    eh_restored = VPBElement.from_dict(data)
    assert eh_restored.element_id == eh.element_id
    assert eh_restored.error_handler_type == eh.error_handler_type
    assert eh_restored.error_handler_retry_count == eh.error_handler_retry_count
    assert eh_restored.error_handler_retry_delay == eh.error_handler_retry_delay
    assert eh_restored.error_handler_timeout == eh.error_handler_timeout
    assert eh_restored.error_handler_on_error_target == eh.error_handler_on_error_target
    assert eh_restored.error_handler_on_success_target == eh.error_handler_on_success_target
    assert eh_restored.error_handler_log_errors == eh.error_handler_log_errors
    print("✓ from_dict() erfolgreich")


def test_error_handler_clone():
    """Test: Element klonen."""
    print("\n=== Test 7: Klonen ===")
    
    eh = VPBElement(
        element_id="eh_original",
        element_type="ERROR_HANDLER",
        name="Original Handler",
        x=100, y=100,
        error_handler_type="RETRY",
        error_handler_retry_count=3,
        error_handler_retry_delay=60,
        error_handler_timeout=300,
        error_handler_on_error_target="func_error",
        error_handler_on_success_target="func_success",
        error_handler_log_errors=True
    )
    
    # Clone
    eh_clone = eh.clone(new_id="eh_clone")
    
    assert eh_clone.element_id == "eh_clone"
    assert eh_clone.x == 120  # +20 Offset
    assert eh_clone.y == 120  # +20 Offset
    assert eh_clone.error_handler_type == eh.error_handler_type
    assert eh_clone.error_handler_retry_count == eh.error_handler_retry_count
    assert eh_clone.error_handler_retry_delay == eh.error_handler_retry_delay
    assert eh_clone.error_handler_timeout == eh.error_handler_timeout
    assert eh_clone.error_handler_on_error_target == eh.error_handler_on_error_target
    assert eh_clone.error_handler_on_success_target == eh.error_handler_on_success_target
    assert eh_clone.error_handler_log_errors == eh.error_handler_log_errors
    
    print(f"✓ Geklont: {eh.element_id} → {eh_clone.element_id}")
    print(f"  Position: ({eh.x}, {eh.y}) → ({eh_clone.x}, {eh_clone.y})")


def test_error_handler_non_error_handler_element():
    """Test: ERROR_HANDLER-Felder werden nur für ERROR_HANDLER serialisiert."""
    print("\n=== Test 8: Konditionale Serialisierung ===")
    
    # Nicht-ERROR_HANDLER Element
    func = VPBElement(
        element_id="func_1",
        element_type="FUNCTION",
        name="Normal Function",
        x=100, y=100
    )
    
    data = func.to_dict()
    
    # ERROR_HANDLER-Felder sollten None sein
    assert data.get('error_handler_type') is None
    assert data.get('error_handler_retry_count') is None
    assert data.get('error_handler_retry_delay') is None
    
    print("✓ ERROR_HANDLER-Felder werden nur für ERROR_HANDLER serialisiert")


def test_error_handler_zero_timeout():
    """Test: Timeout = 0 (kein Timeout)."""
    print("\n=== Test 9: Kein Timeout ===")
    
    eh = VPBElement(
        element_id="eh_no_timeout",
        element_type="ERROR_HANDLER",
        name="No Timeout",
        x=100, y=100,
        error_handler_timeout=0
    )
    
    assert eh.error_handler_timeout == 0
    print("✓ Timeout = 0 (kein Timeout)")


def test_error_handler_extreme_values():
    """Test: Extreme Werte."""
    print("\n=== Test 10: Extreme Werte ===")
    
    eh = VPBElement(
        element_id="eh_extreme",
        element_type="ERROR_HANDLER",
        name="Extreme Values",
        x=100, y=100,
        error_handler_retry_count=999,
        error_handler_retry_delay=1,
        error_handler_timeout=86400  # 24 Stunden
    )
    
    assert eh.error_handler_retry_count == 999
    assert eh.error_handler_retry_delay == 1
    assert eh.error_handler_timeout == 86400
    
    print(f"✓ Extreme Werte: {eh.error_handler_retry_count} Retries, {eh.error_handler_retry_delay}s Delay, {eh.error_handler_timeout}s Timeout")


if __name__ == "__main__":
    print("=" * 60)
    print("ERROR_HANDLER ELEMENT SCHEMA TESTS")
    print("=" * 60)
    
    try:
        test_error_handler_creation()
        test_error_handler_types()
        test_error_handler_retry_config()
        test_error_handler_targets()
        test_error_handler_logging()
        test_error_handler_serialization()
        test_error_handler_clone()
        test_error_handler_non_error_handler_element()
        test_error_handler_zero_timeout()
        test_error_handler_extreme_values()
        
        print("\n" + "=" * 60)
        print("✓ ALLE 10 TESTS ERFOLGREICH")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n✗ TEST FEHLGESCHLAGEN: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ FEHLER: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
