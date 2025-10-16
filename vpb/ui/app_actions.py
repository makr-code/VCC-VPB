from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from vpb_app import VPBApp


class AppActions:
    """Bündelt häufige Bearbeitungs- und Ansichtsaktionen der ``VPBApp``."""

    def __init__(self, app: "VPBApp") -> None:
        self._app = app

    def toggle_grid(self) -> None:
        app = self._app
        grid_var = getattr(app, "_grid_var", None)
        canvas = getattr(app, "canvas", None)
        status = getattr(app, "status", None)
        if grid_var is None or canvas is None:
            return
        try:
            show = bool(grid_var.get())
        except Exception:
            show = False
        try:
            canvas.grid_visible = show
            canvas.redraw_all()
        except Exception:
            return
        if status is not None:
            try:
                status.set("Grid sichtbar" if show else "Grid verborgen")
            except Exception:
                pass

    def delete_selected(self) -> None:
        controller = getattr(self._app, "canvas_controller", None)
        if controller:
            try:
                controller.delete_selected()
            except Exception:
                pass

    def duplicate_selected(self) -> None:
        controller = getattr(self._app, "canvas_controller", None)
        if controller:
            try:
                controller.duplicate_selected()
            except Exception:
                pass

    def toggle_snap(self) -> None:
        controller = getattr(self._app, "canvas_controller", None)
        if controller:
            try:
                controller.toggle_snap()
            except Exception:
                pass

    def toggle_link_mode(self) -> None:
        controller = getattr(self._app, "canvas_controller", None)
        if controller:
            try:
                controller.toggle_link_mode()
            except Exception:
                pass

    def undo(self) -> None:
        controller = getattr(self._app, "canvas_controller", None)
        if controller:
            try:
                controller.undo()
            except Exception:
                pass

    def redo(self) -> None:
        controller = getattr(self._app, "canvas_controller", None)
        if controller:
            try:
                controller.redo()
            except Exception:
                pass

    def reset_view(self) -> None:
        controller = getattr(self._app, "canvas_controller", None)
        if controller:
            try:
                controller.reset_view()
            except Exception:
                pass

    def fit_to_diagram(self) -> None:
        controller = getattr(self._app, "canvas_controller", None)
        if controller:
            try:
                controller.fit_to_diagram()
            except Exception:
                pass
