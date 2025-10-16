from __future__ import annotations

import re
from typing import Dict, List, Optional, TYPE_CHECKING

from tkinter import messagebox

if TYPE_CHECKING:  # pragma: no cover
    from vpb_app import VPBApp


class AppPaletteIntegration:
    """Kapselt Palette- und Hierarchie-Helfer für ``VPBApp``."""

    def __init__(self, app: "VPBApp", *, category_dialog_cls) -> None:
        self._app = app
        self._category_dialog_cls = category_dialog_cls

    # ----- Palette -----
    def reload_palettes(self) -> None:
        controller = getattr(self._app, "canvas_controller", None)
        if controller:
            controller.reload_palettes()

    def on_palette_pick(self, item: dict) -> None:
        controller = getattr(self._app, "canvas_controller", None)
        if controller:
            controller.handle_palette_pick(item)

    # ----- Hierarchie -----
    def apply_hierarchy_categories(
        self,
        categories: List[Dict[str, object]],
        *,
        select_index: Optional[int] = None,
        push_undo: bool = True,
        status_message: Optional[str] = None,
    ) -> None:
        app = self._app
        canvas = app.canvas
        cats = [dict(cat) for cat in categories if isinstance(cat, dict)]
        if push_undo:
            try:
                canvas.push_undo()
            except Exception:
                pass
        canvas.hierarchy_categories = cats
        try:
            if hasattr(canvas, "_hierarchy_color_cache"):
                canvas._hierarchy_color_cache.clear()  # type: ignore[attr-defined]
        except Exception:
            setattr(canvas, "_hierarchy_color_cache", {})
        try:
            canvas.redraw_all()
        except Exception:
            pass
        try:
            hier_canvas = getattr(app, "hier_canvas", None)
            if hier_canvas:
                if select_index is not None and 0 <= select_index < len(cats):
                    hier_canvas.set_selected_index(select_index)
                else:
                    hier_canvas.set_selected_index(None)
                hier_canvas.redraw()
        except Exception:
            pass
        if select_index is not None and 0 <= select_index < len(cats):
            app._selected_hierarchy_index = select_index
            try:
                app.props.set_hierarchy(select_index, cats[select_index])
            except Exception:
                pass
        else:
            app._selected_hierarchy_index = None
            try:
                app.props.set_hierarchy(None, None)
            except Exception:
                pass
        try:
            names = [str(cat.get("name")) for cat in cats if cat and cat.get("name")]
            refresh = getattr(app.props, "refresh_hierarchy_options", None)
            if callable(refresh):
                refresh(names)
        except Exception:
            pass
        try:
            if getattr(app.props, "_mode", "") == "element":
                sid = getattr(canvas, "selected_id", None)
                if sid and sid in canvas.elements:
                    app.props.set_element(canvas.elements[sid])
        except Exception:
            pass
        app._pref_hierarchy_categories = [dict(c) for c in cats]
        try:
            app._save_settings()
        except Exception:
            pass
        message = status_message or f"{len(cats)} Hierarchien aktualisiert."
        try:
            app.status.set(message)
        except Exception:
            pass

    def update_hierarchy_category(
        self,
        index: int,
        data: Dict[str, object],
        *,
        refresh_panel: bool = True,
    ) -> bool:
        app = self._app
        canvas = app.canvas
        cats = list(getattr(canvas, "hierarchy_categories", []) or [])
        if not cats or index < 0 or index >= len(cats):
            return False
        current = dict(cats[index]) if isinstance(cats[index], dict) else {}
        name = str(data.get("name", current.get("name", "")) or "").strip()
        if not name:
            messagebox.showerror("Hierarchie", "Bitte einen Namen für das Hierarchieband angeben.")
            return False
        color = str(data.get("color", current.get("color", "#f2f2f2")) or "").strip()
        if color and not re.fullmatch(r"#([0-9a-fA-F]{6})", color):
            messagebox.showerror("Hierarchie", "Bitte eine Farbe im Format #RRGGBB angeben.")
            return False
        y0_src = data.get("y0", current.get("y0", 0.0))
        y1_src = data.get("y1", current.get("y1", 0.0))
        try:
            y0 = float(str(y0_src).replace(",", "."))
            y1 = float(str(y1_src).replace(",", "."))
        except Exception:
            messagebox.showerror("Hierarchie", "Bitte numerische Werte für Y-Beginn und Y-Ende angeben.")
            return False
        if y1 < y0:
            y0, y1 = y1, y0
        updated = dict(current)
        updated["name"] = name
        updated["color"] = color if color else current.get("color", "#f2f2f2")
        updated["y0"] = y0
        updated["y1"] = y1
        try:
            canvas.push_undo()
        except Exception:
            pass
        cats[index] = updated
        status_msg = f"Hierarchie \u201e{name}\u201c aktualisiert."
        self.apply_hierarchy_categories(cats, select_index=index, push_undo=False, status_message=status_msg)
        if refresh_panel:
            try:
                app.props.set_hierarchy(index, updated)
            except Exception:
                pass
        return True

    def open_hierarchy_dialog(self, index: int, category: Dict[str, object]) -> None:
        dialog = self._category_dialog_cls(self._app, category)
        self._app.wait_window(dialog)
        if getattr(dialog, "result", None):
            self.update_hierarchy_category(index, dialog.result)