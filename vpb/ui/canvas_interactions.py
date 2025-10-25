"""Hilfsfunktionen zur Konfiguration von Canvas-Interaktionen."""

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - nur für Typprüfungen
    from vpb_app import VPBDesignerApp  # type: ignore
    from .canvas import VPBCanvas


def configure_canvas_interactions(
    app: "VPBDesignerApp",
    canvas: "VPBCanvas",
    x_scroll: tk.Scrollbar,
    y_scroll: tk.Scrollbar,
) -> None:
    """Richtet Scrollbars, View-Listener und Tastatur-Shortcuts für den Canvas ein."""

    def _update_scrollbars_from_view() -> None:
        try:
            min_x, min_y, max_x, max_y = canvas.get_content_bounds(include_connections=True)
            view_w_m, view_h_m = canvas.get_viewport_model_size()
            view_x0_m, view_y0_m = canvas.get_view_origin_model()
            content_w_m = max(1e-6, (max_x - min_x))
            content_h_m = max(1e-6, (max_y - min_y))
            fx0 = (view_x0_m - min_x) / content_w_m
            fy0 = (view_y0_m - min_y) / content_h_m
            fx_len = view_w_m / content_w_m
            fy_len = view_h_m / content_h_m
            fx0 = max(0.0, min(1.0, fx0))
            fy0 = max(0.0, min(1.0, fy0))
            fx1 = max(fx0, min(1.0, fx0 + fx_len))
            fy1 = max(fy0, min(1.0, fy0 + fy_len))
            x_scroll.set(fx0, fx1)
            y_scroll.set(fy0, fy1)
            # Scrollbars immer sichtbar lassen
            if hasattr(x_scroll, 'grid_remove'):
                pass  # grid_remove ist überschrieben, Scrollbar bleibt sichtbar
            if hasattr(y_scroll, 'grid_remove'):
                pass
        except Exception:
            try:
                x_scroll.set(0.0, 1.0)
                y_scroll.set(0.0, 1.0)
            except Exception:
                pass

    def _apply_scroll_moveto(axis: str, frac_str: str) -> None:
        try:
            frac = float(frac_str)
            min_x, min_y, max_x, max_y = canvas.get_content_bounds(include_connections=True)
            content_w_m = max(1e-6, (max_x - min_x))
            content_h_m = max(1e-6, (max_y - min_y))
            view_x0_m, view_y0_m = canvas.get_view_origin_model()
            if axis == "x":
                x0_m = min_x + frac * content_w_m
                canvas.set_view_origin_model(x0_m, view_y0_m)
            else:
                y0_m = min_y + frac * content_h_m
                canvas.set_view_origin_model(view_x0_m, y0_m)
        except Exception:
            pass

    def _apply_scroll_scroll(axis: str, n_str: str, what: str) -> None:
        try:
            n = int(n_str)
            scale = max(canvas.view_scale, 1e-6)
            if what == "units":
                delta_model = (20.0 / scale) * n
            else:
                vw_m, vh_m = canvas.get_viewport_model_size()
                delta_model = (vw_m if axis == "x" else vh_m) * 0.8 * n
            x0_m, y0_m = canvas.get_view_origin_model()
            if axis == "x":
                canvas.set_view_origin_model(x0_m + delta_model, y0_m)
            else:
                canvas.set_view_origin_model(x0_m, y0_m + delta_model)
        except Exception:
            pass

    def _scroll_x(*args) -> None:
        try:
            if not args:
                return
            if args[0] == "moveto":
                _apply_scroll_moveto("x", args[1])
            elif args[0] == "scroll":
                _apply_scroll_scroll("x", args[1], args[2])
        finally:
            _update_scrollbars_from_view()

    def _scroll_y(*args) -> None:
        try:
            if not args:
                return
            if args[0] == "moveto":
                _apply_scroll_moveto("y", args[1])
            elif args[0] == "scroll":
                _apply_scroll_scroll("y", args[1], args[2])
        finally:
            _update_scrollbars_from_view()

    x_scroll.configure(command=_scroll_x)
    y_scroll.configure(command=_scroll_y)

    try:
        canvas.add_view_changed_listener(_update_scrollbars_from_view)
    except Exception:
        canvas.on_view_changed = _update_scrollbars_from_view
    _update_scrollbars_from_view()

    try:
        canvas.configure(takefocus=True)

        def _left(_=None):
            return app._handle_arrow(-1, 0, False)

        def _right(_=None):
            return app._handle_arrow(1, 0, False)

        def _up(_=None):
            return app._handle_arrow(0, -1, False)

        def _down(_=None):
            return app._handle_arrow(0, 1, False)

        def _left_big(_=None):
            return app._handle_arrow(-1, 0, True)

        def _right_big(_=None):
            return app._handle_arrow(1, 0, True)

        def _up_big(_=None):
            return app._handle_arrow(0, -1, True)

        def _down_big(_=None):
            return app._handle_arrow(0, 1, True)

        def _zoom_in(_=None):
            canvas.zoom_at_view(1.1)
            return "break"

        def _zoom_out(_=None):
            canvas.zoom_at_view(1 / 1.1)
            return "break"

        canvas.bind("<Left>", _left)
        canvas.bind("<Right>", _right)
        canvas.bind("<Up>", _up)
        canvas.bind("<Down>", _down)

        canvas.bind("<Shift-Left>", _left_big)
        canvas.bind("<Shift-Right>", _right_big)
        canvas.bind("<Shift-Up>", _up_big)
        canvas.bind("<Shift-Down>", _down_big)

        canvas.bind("<Prior>", _zoom_in)
        canvas.bind("<Next>", _zoom_out)
        canvas.bind("<Page_Up>", _zoom_in)
        canvas.bind("<Page_Down>", _zoom_out)

        canvas.bind("<Button-1>", lambda e: (canvas.focus_set(), None), add="+")
    except Exception:
        pass
