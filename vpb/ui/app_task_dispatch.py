from __future__ import annotations

import traceback
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:  # pragma: no cover
    from vpb_app import VPBDesignerApp


__all__ = ["AppTaskDispatch"]


class AppTaskDispatch:
    """Kapselt das Polling des Hintergrund-Controllers und verteilt Ergebnisse."""

    def __init__(
        self,
        app: "VPBDesignerApp",
        *,
        initial_delay: int = 120,
        poll_interval: int = 80,
        max_items_per_poll: int = 20,
    ) -> None:
        self._app = app
        self._initial_delay = max(0, int(initial_delay))
        self._poll_interval = max(1, int(poll_interval))
        self._max_items = max(1, int(max_items_per_poll))
        self._after_id: Optional[str] = None
        self._running: bool = False

    def start(self) -> None:
        """Startet das Polling, falls noch nicht aktiv."""
        if self._running:
            return
        self._running = True
        self._schedule(initial=True)

    def stop(self) -> None:
        """Stoppt das Polling und hebt geplante Aufrufe auf."""
        if not self._running:
            return
        self._running = False
        if self._after_id is not None:
            try:
                self._app.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def dispatch_item(self, item: Any) -> bool:
        """Leitet einen Polling-Eintrag an den Task-Controller weiter."""
        task_controller = getattr(self._app, "task_controller", None)
        if not task_controller:
            return False
        try:
            return bool(task_controller.handle_poll_item(item))
        except Exception:
            traceback.print_exc()
            return True

    def poll_once(self) -> None:
        """Verarbeitet eine Polling-Runde und plant den nächsten Durchlauf."""
        self._after_id = None
        if not self._running:
            return
        controller = getattr(self._app, "_app_controller", None)
        if controller is None:
            self._schedule()
            return
        try:
            items = controller.poll_results(max_items=self._max_items)
        except Exception:
            traceback.print_exc()
            items = []
        telemetry = getattr(self._app, "_telemetry_manager", None)
        handled_total = 0
        unhandled_total = 0
        for item in items or []:
            handled = False
            try:
                handled = self.dispatch_item(item)
            except Exception:
                traceback.print_exc()
                handled = True
            if handled:
                handled_total += 1
            else:
                unhandled_total += 1
            if not handled and telemetry is not None:
                try:
                    telemetry.record(
                        "controller_result_unhandled",
                        descriptor=self._describe_item(item),
                    )
                except Exception:
                    pass
        if telemetry is not None and items:
            try:
                telemetry.record(
                    "controller_poll",
                    total=len(items),
                    handled=handled_total,
                    unhandled=unhandled_total,
                )
            except Exception:
                pass
        self._schedule()

    def _schedule(self, *, initial: bool = False) -> None:
        if not self._running:
            return
        delay = self._initial_delay if initial else self._poll_interval
        try:
            self._after_id = self._app.after(delay, self.poll_once)
        except Exception:
            self._after_id = None
            self._running = False

    @staticmethod
    def _describe_item(item: Any) -> str:
        if isinstance(item, tuple) and len(item) >= 2:
            kind = item[1]
            return f"tuple:{kind}"
        task_type = getattr(item, "task_type", None)
        if task_type:
            return f"TaskResult:{task_type}"
        return type(item).__name__
