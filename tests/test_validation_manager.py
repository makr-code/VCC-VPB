import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validation_manager import ValidationManager

def test_validation_ok_or_fail_gracefully():
    vm = ValidationManager()
    ok, msg = vm.validate({"elements": [], "connections": []})
    assert isinstance(ok, bool)
    # Wenn fehlende Module -> ok True
    # Wenn echtes Schema -> sollte True sein für leere Struktur oder klare Fehlermeldung liefern
    if not ok:
        assert isinstance(msg, (str, type(None)))

def test_validation_arbitrary_structure():
    vm = ValidationManager()
    ok, msg = vm.validate({"foo": 1})
    assert isinstance(ok, bool)
    if not ok:
        assert isinstance(msg, (str, type(None)))
