"""
Tests für INTERLOCK-Element Schema

Testet:
- Element-Erstellung mit allen Properties
- Default-Werte
- Serialization (to_dict)
- Deserialization (from_dict)
- Cloning
- Interlock-Types (MUTEX, SEMAPHORE)
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vpb.models.element import VPBElement


def test_interlock_creation_with_all_properties():
    """Test: INTERLOCK-Element mit allen Properties erstellen"""
    print("\n1️⃣ Test: INTERLOCK-Element mit allen Properties")
    
    interlock = VPBElement(
        element_id="interlock1",
        element_type="INTERLOCK",
        name="DB Connection Lock",
        x=100,
        y=200
    )
    
    # Setze INTERLOCK-Properties
    interlock.interlock_type = "MUTEX"
    interlock.interlock_resource_id = "db_connection_pool"
    interlock.interlock_max_count = 1
    interlock.interlock_timeout = 30
    interlock.interlock_on_locked_target = "error_handler_1"
    interlock.interlock_auto_release = True
    
    assert interlock.element_id == "interlock1"
    assert interlock.element_type == "INTERLOCK"
    assert interlock.interlock_type == "MUTEX"
    assert interlock.interlock_resource_id == "db_connection_pool"
    assert interlock.interlock_max_count == 1
    assert interlock.interlock_timeout == 30
    assert interlock.interlock_on_locked_target == "error_handler_1"
    assert interlock.interlock_auto_release == True
    
    print("   ✓ Alle INTERLOCK-Properties korrekt gesetzt")


def test_interlock_default_values():
    """Test: Default-Werte für INTERLOCK-Element"""
    print("\n2️⃣ Test: INTERLOCK Default-Werte")
    
    interlock = VPBElement(
        element_id="interlock2",
        element_type="INTERLOCK",
        name="Default Interlock",
        x=100,
        y=200
    )
    
    assert interlock.interlock_type == "MUTEX"
    assert interlock.interlock_resource_id == ""
    assert interlock.interlock_max_count == 1
    assert interlock.interlock_timeout == 0
    assert interlock.interlock_on_locked_target == ""
    assert interlock.interlock_auto_release == True
    
    print("   ✓ Default-Werte korrekt:")
    print(f"      Type: {interlock.interlock_type}")
    print(f"      Max Count: {interlock.interlock_max_count}")
    print(f"      Auto Release: {interlock.interlock_auto_release}")


def test_interlock_mutex_type():
    """Test: MUTEX-Type (exklusiver Zugriff)"""
    print("\n3️⃣ Test: MUTEX-Type")
    
    mutex = VPBElement(
        element_id="mutex1",
        element_type="INTERLOCK",
        name="File Access Mutex",
        x=100,
        y=200
    )
    
    mutex.interlock_type = "MUTEX"
    mutex.interlock_resource_id = "logfile_access"
    mutex.interlock_max_count = 1  # MUTEX = immer 1
    
    assert mutex.interlock_type == "MUTEX"
    assert mutex.interlock_max_count == 1
    
    print("   ✓ MUTEX-Typ korrekt (exklusiver Zugriff, max_count=1)")


def test_interlock_semaphore_type():
    """Test: SEMAPHORE-Type (begrenzte Anzahl)"""
    print("\n4️⃣ Test: SEMAPHORE-Type")
    
    semaphore = VPBElement(
        element_id="semaphore1",
        element_type="INTERLOCK",
        name="Database Pool Semaphore",
        x=100,
        y=200
    )
    
    semaphore.interlock_type = "SEMAPHORE"
    semaphore.interlock_resource_id = "db_pool"
    semaphore.interlock_max_count = 5  # Bis zu 5 gleichzeitige Zugriffe
    
    assert semaphore.interlock_type == "SEMAPHORE"
    assert semaphore.interlock_max_count == 5
    
    print("   ✓ SEMAPHORE-Typ korrekt (max_count=5 gleichzeitige Zugriffe)")


def test_interlock_serialization():
    """Test: to_dict() Serialization"""
    print("\n5️⃣ Test: INTERLOCK Serialization (to_dict)")
    
    interlock = VPBElement(
        element_id="interlock3",
        element_type="INTERLOCK",
        name="Resource Lock",
        x=150,
        y=250
    )
    
    interlock.interlock_type = "SEMAPHORE"
    interlock.interlock_resource_id = "api_rate_limit"
    interlock.interlock_max_count = 10
    interlock.interlock_timeout = 60
    interlock.interlock_on_locked_target = "wait_state"
    interlock.interlock_auto_release = False
    
    data = interlock.to_dict()
    
    assert data['element_id'] == "interlock3"
    assert data['element_type'] == "INTERLOCK"
    assert data['interlock_type'] == "SEMAPHORE"
    assert data['interlock_resource_id'] == "api_rate_limit"
    assert data['interlock_max_count'] == 10
    assert data['interlock_timeout'] == 60
    assert data['interlock_on_locked_target'] == "wait_state"
    assert data['interlock_auto_release'] == False
    
    print("   ✓ Serialization korrekt - alle INTERLOCK-Felder in dict")


def test_interlock_conditional_serialization():
    """Test: Conditional Serialization (nur bei INTERLOCK-Type)"""
    print("\n6️⃣ Test: Conditional Serialization")
    
    # INTERLOCK-Element
    interlock = VPBElement(
        element_id="interlock4",
        element_type="INTERLOCK",
        name="Lock",
        x=100,
        y=200
    )
    interlock.interlock_type = "MUTEX"
    interlock.interlock_resource_id = "res1"
    
    data_interlock = interlock.to_dict()
    
    # Nicht-INTERLOCK-Element
    task = VPBElement(
        element_id="task1",
        element_type="TASK",
        name="Task",
        x=200,
        y=200
    )
    
    data_task = task.to_dict()
    
    # INTERLOCK-Properties nur bei INTERLOCK-Element
    assert 'interlock_type' in data_interlock and data_interlock['interlock_type'] is not None
    assert 'interlock_type' not in data_task or data_task['interlock_type'] is None
    
    print("   ✓ Conditional Serialization: INTERLOCK-Properties nur bei INTERLOCK-Type")


def test_interlock_deserialization():
    """Test: from_dict() Deserialization"""
    print("\n7️⃣ Test: INTERLOCK Deserialization (from_dict)")
    
    data = {
        'element_id': 'interlock5',
        'element_type': 'INTERLOCK',
        'name': 'Deserialized Lock',
        'x': 300,
        'y': 400,
        'interlock_type': 'SEMAPHORE',
        'interlock_resource_id': 'printer_queue',
        'interlock_max_count': 3,
        'interlock_timeout': 120,
        'interlock_on_locked_target': 'timeout_handler',
        'interlock_auto_release': True
    }
    
    interlock = VPBElement.from_dict(data)
    
    assert interlock.element_id == 'interlock5'
    assert interlock.element_type == 'INTERLOCK'
    assert interlock.interlock_type == 'SEMAPHORE'
    assert interlock.interlock_resource_id == 'printer_queue'
    assert interlock.interlock_max_count == 3
    assert interlock.interlock_timeout == 120
    assert interlock.interlock_on_locked_target == 'timeout_handler'
    assert interlock.interlock_auto_release == True
    
    print("   ✓ Deserialization korrekt - alle INTERLOCK-Properties wiederhergestellt")


def test_interlock_deserialization_missing_fields():
    """Test: Deserialization mit fehlenden Feldern (Defaults)"""
    print("\n8️⃣ Test: Deserialization mit fehlenden Feldern")
    
    data = {
        'element_id': 'interlock6',
        'element_type': 'INTERLOCK',
        'name': 'Minimal Lock',
        'x': 100,
        'y': 200
        # Keine INTERLOCK-spezifischen Felder
    }
    
    interlock = VPBElement.from_dict(data)
    
    # Sollte Defaults verwenden
    assert interlock.interlock_type == "MUTEX"
    assert interlock.interlock_resource_id == ""
    assert interlock.interlock_max_count == 1
    assert interlock.interlock_timeout == 0
    assert interlock.interlock_on_locked_target == ""
    assert interlock.interlock_auto_release == True
    
    print("   ✓ Fehlende Felder mit Defaults aufgefüllt")


def test_interlock_cloning():
    """Test: clone() Methode"""
    print("\n9️⃣ Test: INTERLOCK Cloning")
    
    original = VPBElement(
        element_id="interlock7",
        element_type="INTERLOCK",
        name="Original Lock",
        x=100,
        y=200
    )
    
    original.interlock_type = "SEMAPHORE"
    original.interlock_resource_id = "shared_resource"
    original.interlock_max_count = 5
    original.interlock_timeout = 90
    original.interlock_on_locked_target = "fallback"
    original.interlock_auto_release = False
    
    clone = original.clone(new_id="interlock7_clone")
    
    assert clone.element_id == "interlock7_clone"
    assert clone.element_type == "INTERLOCK"
    assert clone.interlock_type == "SEMAPHORE"
    assert clone.interlock_resource_id == "shared_resource"
    assert clone.interlock_max_count == 5
    assert clone.interlock_timeout == 90
    assert clone.interlock_on_locked_target == "fallback"
    assert clone.interlock_auto_release == False
    
    # Änderung am Clone sollte Original nicht beeinflussen
    clone.interlock_max_count = 10
    assert original.interlock_max_count == 5
    
    print("   ✓ Cloning korrekt - alle Properties kopiert, unabhängige Instanz")


def test_interlock_roundtrip_serialization():
    """Test: Roundtrip Serialization (to_dict -> from_dict)"""
    print("\n🔟 Test: INTERLOCK Roundtrip Serialization")
    
    original = VPBElement(
        element_id="interlock8",
        element_type="INTERLOCK",
        name="Roundtrip Lock",
        x=150,
        y=300
    )
    
    original.interlock_type = "MUTEX"
    original.interlock_resource_id = "critical_section"
    original.interlock_max_count = 1
    original.interlock_timeout = 45
    original.interlock_on_locked_target = "error_state"
    original.interlock_auto_release = True
    
    # Serialize
    data = original.to_dict()
    
    # Deserialize
    restored = VPBElement.from_dict(data)
    
    # Vergleiche
    assert restored.element_id == original.element_id
    assert restored.element_type == original.element_type
    assert restored.interlock_type == original.interlock_type
    assert restored.interlock_resource_id == original.interlock_resource_id
    assert restored.interlock_max_count == original.interlock_max_count
    assert restored.interlock_timeout == original.interlock_timeout
    assert restored.interlock_on_locked_target == original.interlock_on_locked_target
    assert restored.interlock_auto_release == original.interlock_auto_release
    
    print("   ✓ Roundtrip erfolgreich - Original und Restored identisch")


if __name__ == "__main__":
    print("=" * 60)
    print("INTERLOCK ELEMENT SCHEMA TESTS")
    print("=" * 60)
    
    tests = [
        test_interlock_creation_with_all_properties,
        test_interlock_default_values,
        test_interlock_mutex_type,
        test_interlock_semaphore_type,
        test_interlock_serialization,
        test_interlock_conditional_serialization,
        test_interlock_deserialization,
        test_interlock_deserialization_missing_fields,
        test_interlock_cloning,
        test_interlock_roundtrip_serialization,
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
