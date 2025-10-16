"""Controller helpers for the Properties tab."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:  # pragma: no cover - only used for type checking
    from vpb_app import VPBDesignerApp  # type: ignore circular import


class PropertiesController:
    """Encapsulates callbacks used by the properties sidebar."""

    def __init__(self, app: "VPBDesignerApp") -> None:
        self._app = app

    # --- Callbacks wired into the PropertiesPanel ---
    def resolve_member_label(self, element_id: str) -> str:
        try:
            canvas = getattr(self._app, "canvas", None)
            if not canvas:
                return str(element_id)
            element = canvas.elements.get(element_id)
            if not element:
                return str(element_id)
            name = getattr(element, "name", "") or ""
            return f"{element_id} — {name}" if name else str(element_id)
        except Exception:
            return str(element_id)

    def select_member(self, element_id: str) -> None:
        try:
            canvas = getattr(self._app, "canvas", None)
            if not canvas or element_id not in canvas.elements:
                return
            canvas.selected_id = element_id
            try:
                canvas.selected_ids = {element_id}
            except Exception:
                pass
            canvas.selected_conn_id = None
            canvas.redraw_all()
            callback = getattr(canvas, "on_selection_changed", None)
            if callable(callback):
                try:
                    callback(canvas.elements.get(element_id), None)
                except Exception:
                    pass
        except Exception:
            pass

    def add_selection_to_group(self, group_id: str) -> None:
        try:
            canvas = getattr(self._app, "canvas", None)
            if not canvas or group_id not in canvas.elements:
                return
            if getattr(canvas.elements[group_id], "element_type", "").upper() != "GROUP":
                return
            if hasattr(canvas, "_group_add_selection"):
                canvas._group_add_selection(group_id)
                self._notify_selection_refresh(group_id)
        except Exception:
            pass

    def remove_selection_from_group(self, group_id: str) -> None:
        try:
            canvas = getattr(self._app, "canvas", None)
            if not canvas or group_id not in canvas.elements:
                return
            if getattr(canvas.elements[group_id], "element_type", "").upper() != "GROUP":
                return
            if hasattr(canvas, "_group_remove_selection"):
                canvas._group_remove_selection(group_id)
                self._notify_selection_refresh(group_id)
        except Exception:
            pass

    # --- helpers ---
    def _notify_selection_refresh(self, element_id: Optional[str]) -> None:
        try:
            canvas = getattr(self._app, "canvas", None)
            if not canvas or element_id not in canvas.elements:
                return
            if getattr(canvas, "selected_id", None) == element_id:
                callback = getattr(canvas, "on_selection_changed", None)
                if callable(callback):
                    try:
                        callback(canvas.elements.get(element_id), None)
                    except Exception:
                        pass
        except Exception:
            pass
