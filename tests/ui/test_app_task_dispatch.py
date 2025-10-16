from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Callable, List

from vpb.ui.app_task_dispatch import AppTaskDispatch


class DummyTelemetry:
    def __init__(self) -> None:
        self.events: List[tuple[str, dict[str, Any]]] = []

    def record(self, event_type: str, **fields: Any) -> dict[str, Any]:
        self.events.append((event_type, fields))
        return {"type": event_type, **fields}


class DummyApp:
    def __init__(self) -> None:
        self.after_calls: List[tuple[int, Callable[[], None], str]] = []
        self.after_cancelled: List[str] = []
        self.recorded_items: List[Any] = []
        self._handle_return = True
        self._next_results: List[Any] = []
        self.task_controller = SimpleNamespace(handle_poll_item=self._handle_poll_item)
        self._app_controller = SimpleNamespace(poll_results=self._poll_results)
        self._telemetry_manager = DummyTelemetry()

    def after(self, delay: int, callback: Callable[[], None]) -> str:
        ident = f"id-{len(self.after_calls)}"
        self.after_calls.append((delay, callback, ident))
        return ident

    def after_cancel(self, ident: str) -> None:
        self.after_cancelled.append(ident)

    def queue_results(self, *items: Any) -> None:
        self._next_results.extend(items)

    def _handle_poll_item(self, item: Any) -> bool:
        self.recorded_items.append(item)
        return self._handle_return

    def _poll_results(self, max_items: int = 20) -> List[Any]:
        results = list(self._next_results[:max_items])
        self._next_results = self._next_results[max_items:]
        return results


def test_start_schedules_initial_poll_once() -> None:
    app = DummyApp()
    helper = AppTaskDispatch(app, initial_delay=150, poll_interval=90)
    helper.start()
    assert len(app.after_calls) == 1
    delay, _, _ = app.after_calls[0]
    assert delay == 150

    helper.start()
    assert len(app.after_calls) == 1


def test_poll_dispatches_items_and_reschedules() -> None:
    app = DummyApp()
    helper = AppTaskDispatch(app, initial_delay=0, poll_interval=55)
    item = ("task-1", "progress", {"fraction": 0.5})
    app.queue_results(item)

    helper.start()
    assert len(app.after_calls) == 1
    _, callback, _ = app.after_calls.pop(0)
    callback()

    assert app.recorded_items == [item]
    assert len(app.after_calls) == 1
    delay, _, _ = app.after_calls[0]
    assert delay == 55
    assert app._telemetry_manager.events[-1] == (
        "controller_poll",
        {"total": 1, "handled": 1, "unhandled": 0},
    )


def test_unhandled_items_are_recorded_in_telemetry() -> None:
    app = DummyApp()
    helper = AppTaskDispatch(app, initial_delay=0, poll_interval=40)
    app._handle_return = False
    app.queue_results(("task-9", "unknown", None))

    helper.start()
    _, callback, _ = app.after_calls.pop(0)
    callback()

    assert app._telemetry_manager.events == [
        ("controller_result_unhandled", {"descriptor": "tuple:unknown"}),
        ("controller_poll", {"total": 1, "handled": 0, "unhandled": 1}),
    ]


def test_stop_cancels_scheduled_after() -> None:
    app = DummyApp()
    helper = AppTaskDispatch(app)
    helper.start()
    assert len(app.after_calls) == 1
    _, _, ident = app.after_calls[0]

    helper.stop()
    assert app.after_cancelled == [ident]


def test_dispatch_item_without_task_controller_returns_false() -> None:
    app = DummyApp()
    helper = AppTaskDispatch(app)
    app.task_controller = None
    assert helper.dispatch_item(("task", "progress", {})) is False
