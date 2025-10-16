from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Optional

from vpb.ui import toggle_shortcut_overlay

if TYPE_CHECKING:  # pragma: no cover
    from vpb_app import VPBApp


class AppShortcuts:
    """Bündelt sämtliche Tastenkombinationen der ``VPBApp``."""

    def __init__(self, app: "VPBApp") -> None:
        self._app = app

    def register(self) -> None:
        app = self._app
        bind = getattr(app, "bind_all", None)
        if bind is None:
            return

        def safe_bind(sequence: str, handler: Callable) -> None:
            try:
                bind(sequence, handler)
            except Exception:
                pass

        def call(method: Callable[[], object]) -> Callable[[Optional[object]], Optional[object]]:
            def handler(event=None):
                try:
                    return method()
                except Exception:
                    return None
            return handler

        def call_if_text_focus_allows(method: Callable[[], object], *, return_break: bool = False) -> Callable[[Optional[object]], Optional[object]]:
            def handler(event=None):
                try:
                    checker = getattr(app, "_is_text_input_focus", None)
                    if callable(checker) and checker():
                        return None
                except Exception:
                    pass
                try:
                    method()
                except Exception:
                    return None
                return "break" if return_break else None
            return handler

        def controller_call(attr: str, *args) -> Callable[[Optional[object]], Optional[object]]:
            def handler(event=None):
                controller = getattr(app, "canvas_controller", None)
                if controller is None:
                    return None
                try:
                    func = getattr(controller, attr)
                except AttributeError:
                    return None
                try:
                    return func(*args)
                except Exception:
                    return None
            return handler

        safe_bind("<Control-s>", call(app.save_document))
        safe_bind("<Control-S>", call(app.save_document))
        safe_bind("<Control-Shift-s>", call(app.save_document_as))
        safe_bind("<Control-o>", call(app.open_document))
        safe_bind("<Control-n>", call(app.new_document))

        safe_bind("<Delete>", call_if_text_focus_allows(app._delete_selected))
        safe_bind("<BackSpace>", call_if_text_focus_allows(app._delete_selected))
        safe_bind("<Control-d>", call(app._duplicate_selected))
        safe_bind("l", call_if_text_focus_allows(app._toggle_link_mode, return_break=True))
        safe_bind("<Control-l>", call(app._toggle_link_mode))
        safe_bind("<Escape>", controller_call("cancel_link_mode"))

        safe_bind("<Control-a>", call(app._select_all))
        safe_bind("<Control-A>", call(app._select_all))
        safe_bind("<Control-c>", call(app._copy_selection))
        safe_bind("<Control-x>", call(app._cut_selection))
        safe_bind("<Control-v>", call(app._paste_clipboard))

        safe_bind("<F1>", call(lambda: toggle_shortcut_overlay(app)))
        safe_bind("<Control-Shift-slash>", call(lambda: toggle_shortcut_overlay(app)))

        safe_bind("<Control-equal>", controller_call("zoom_at_view", 1.1))
        safe_bind("<Control-plus>", controller_call("zoom_at_view", 1.1))
        safe_bind("<Control-KP_Add>", controller_call("zoom_at_view", 1.1))
        safe_bind("<Control-minus>", controller_call("zoom_at_view", 1 / 1.1))
        safe_bind("<Control-KP_Subtract>", controller_call("zoom_at_view", 1 / 1.1))
        safe_bind("<Control-0>", controller_call("zoom_reset"))
        safe_bind("<Control-1>", controller_call("set_view_scale", 1.0))

        safe_bind("<Control-Shift-E>", call_if_text_focus_allows(app._zoom_selection))
        safe_bind("<Control-Shift-e>", call_if_text_focus_allows(app._zoom_selection))
        safe_bind("<Control-Shift-C>", call_if_text_focus_allows(app._center_selection))
        safe_bind("<Control-Shift-c>", call_if_text_focus_allows(app._center_selection))

        safe_bind("<Control-g>", call(app._group_from_selection))
        safe_bind("<Control-Shift-G>", call(app._ungroup_selected))

        safe_bind("<Control-Key-0>", call(app._reset_view))
        safe_bind("<Control-Key-9>", call(app._fit_to_diagram))

        safe_bind("<Control-Return>", getattr(app, "_handle_ctrl_enter", lambda event=None: None))
        safe_bind("<F2>", call(app._focus_chat))

        safe_bind("<Left>", call(lambda: app._handle_arrow(-1, 0, False)))
        safe_bind("<Right>", call(lambda: app._handle_arrow(1, 0, False)))
        safe_bind("<Up>", call(lambda: app._handle_arrow(0, -1, False)))
        safe_bind("<Down>", call(lambda: app._handle_arrow(0, 1, False)))
        safe_bind("<Shift-Left>", call(lambda: app._handle_arrow(-1, 0, True)))
        safe_bind("<Shift-Right>", call(lambda: app._handle_arrow(1, 0, True)))
        safe_bind("<Shift-Up>", call(lambda: app._handle_arrow(0, -1, True)))
        safe_bind("<Shift-Down>", call(lambda: app._handle_arrow(0, 1, True)))