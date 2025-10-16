"""ValidationManager
Kapselt die Prozess-/Diagrammvalidierung gegen Schema (vpb_schema) und optional
Prompt-Core (vpb_prompt_core). Fällt robust auf OK zurück, wenn keine Module
vorhanden sind.
"""
from __future__ import annotations
from typing import Any, Optional, Tuple

try:  # optionales Schema-Modul
    from vpb_schema import validate_vpb_dict  # type: ignore
except Exception:  # pragma: no cover
    validate_vpb_dict = None  # type: ignore

try:  # optionaler Prompt-Core (falls unterschiedliche API nötig wäre)
    from vpb_prompt_core import validate_vpb_json  # type: ignore
except Exception:  # pragma: no cover
    validate_vpb_json = None  # type: ignore

class ValidationManager:
    def __init__(self):
        pass

    def validate(self, data: dict, element_style_keys: list[str] | None = None, connection_style_keys: list[str] | None = None) -> Tuple[bool, Optional[str]]:
        """Validiert ein VPB-Diagramm.
        Reihenfolge:
          1. Falls validate_vpb_dict verfügbar → nutzen (mit kompatiblen Signaturen)
          2. Falls validate_vpb_json verfügbar → als zusätzliche Prüfung
        Bei Ausnahmen wird (False, Fehlermeldung) zurückgegeben, außer Modul fehlt → (True, None).
        """
        # Fallback: ohne Module immer OK
        if validate_vpb_dict is None and validate_vpb_json is None:
            return True, None

        # Erst Schema
        if validate_vpb_dict is not None:
            try:
                if element_style_keys is None:
                    res = validate_vpb_dict(data)
                else:
                    # Versuche Signatur mit (data, elems, conns)
                    conns = connection_style_keys or []
                    try:
                        res = validate_vpb_dict(data, element_style_keys, conns)
                    except TypeError:
                        res = validate_vpb_dict(data)
                ok, msg = self._normalize_result(res)
                if not ok:
                    return ok, msg
            except Exception as e:
                return False, str(e)
        # Dann optional Prompt-Core (nur wenn Schema ok war)
        if validate_vpb_json is not None:
            try:
                res2 = validate_vpb_json(data)  # type: ignore
                ok2, msg2 = self._normalize_result(res2)
                if not ok2:
                    return ok2, msg2
            except Exception as e:  # Prompt-Core Fehler -> Fehler zurückgeben
                return False, str(e)
        return True, None

    @staticmethod
    def _normalize_result(res: Any) -> tuple[bool, Optional[str]]:
        if isinstance(res, tuple) and len(res) >= 1 and isinstance(res[0], bool):
            return bool(res[0]), (str(res[1]) if len(res) > 1 and res[1] is not None else None)
        if isinstance(res, bool):
            return res, None
        return True, None
