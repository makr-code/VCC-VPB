"""ValidationService kapselt Schema- und Prompt-Validierung.
Nutzt vorhandene Module wenn installiert.
"""
from __future__ import annotations
from typing import Any, Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - nur für Typprüfung
    from controller.app_controller import TaskContext

try:
    from vpb_schema import validate_vpb_dict  # type: ignore
except Exception:  # pragma: no cover
    validate_vpb_dict = None  # type: ignore

try:
    from vpb_prompt_core import validate_vpb_json  # type: ignore
except Exception:  # pragma: no cover
    validate_vpb_json = None  # type: ignore

def _ctx_check(context: "TaskContext | None") -> None:
    if context is None:
        return
    check = getattr(context, "check_cancelled", None)
    if callable(check):
        check()


def _ctx_progress(context: "TaskContext | None", *, fraction: Optional[float] = None, message: Optional[str] = None, **fields: Any) -> None:
    if context is None:
        return
    publish = getattr(context, "publish_progress", None)
    if callable(publish):
        try:
            publish(fraction=fraction, message=message, **fields)
        except Exception:
            pass


class ValidationService:
    def validate(self, data: dict, *, context: "TaskContext | None" = None) -> Tuple[bool, Optional[str]]:
        _ctx_progress(context, fraction=0.05, message="Validierung gestartet")
        _ctx_check(context)
        # Schema zuerst
        if validate_vpb_dict:
            try:
                res = validate_vpb_dict(data)
                if isinstance(res, tuple):
                    ok = bool(res[0])
                    msg = None if ok else (res[1] if len(res) > 1 else "Schemafehler")
                else:
                    ok = bool(res)
                    msg = None if ok else "Schemafehler"
                if not ok:
                    _ctx_progress(context, fraction=1.0, message="Validierung fehlgeschlagen", error=msg)
                    return False, msg
            except Exception as e:
                _ctx_progress(context, fraction=1.0, message="Validierung fehlgeschlagen", error=str(e))
                return False, f"Schema-Exception: {e}"
        _ctx_progress(context, fraction=0.45, message="Schema validiert")
        _ctx_check(context)
        # Prompt/Business-Validation
        if validate_vpb_json:
            try:
                issues = validate_vpb_json(data)
                # Erwartet Liste, leere Liste = ok
                if isinstance(issues, list) and issues:
                    msg = f"{len(issues)} Validierungsprobleme"
                    _ctx_progress(context, fraction=1.0, message="Validierung fehlgeschlagen", error=msg)
                    return False, msg
            except Exception as e:
                _ctx_progress(context, fraction=1.0, message="Validierung fehlgeschlagen", error=str(e))
                return False, f"Prompt-Validation-Exception: {e}"
        _ctx_progress(context, fraction=1.0, message="Validierung abgeschlossen")
        return True, None
