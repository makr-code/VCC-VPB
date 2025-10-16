"""AppController: zentraler Hintergrund-Task-Dispatcher.

Verantwortung:
- Worker-Thread startet und verarbeitet TaskRequests aus einer Input-Queue
- Ergebnisse landen in einer Output-Queue für die UI (Polling)
- Handler-Registry: task_type -> Callable(payload[, context]) -> Any (oder Iterator für Streaming)
- Telemetrie-Hooks optional
- Fortschritts-/Cancel-Unterstützung für lange Tasks
"""
from __future__ import annotations
from typing import Any, Callable, Dict, Iterable, Optional
import inspect
import threading
import queue
import time
import traceback
from core.message_bus import TaskRequest, TaskResult, next_task_id


class TaskCancelled(Exception):
    """Spezifische Exception, die Handler optional werfen können."""


class TaskContext:
    """Context-Objekt, das einem Handler Zugriff auf Cancel- und Progress-Hooks gibt."""

    def __init__(self, controller: "AppController", request: TaskRequest):
        self._controller = controller
        self._request = request
        self._cancel_event = threading.Event()

    @property
    def task_id(self) -> str:
        return self._request.task_id

    @property
    def task_type(self) -> str:
        return self._request.task_type

    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()

    def wait_cancelled(self, timeout: Optional[float] = None) -> bool:
        return self._cancel_event.wait(timeout)

    def check_cancelled(self) -> None:
        if self.is_cancelled():
            raise TaskCancelled("Task cancelled")

    def publish_progress(
        self,
        *,
        fraction: Optional[float] = None,
        message: Optional[str] = None,
        **fields: Any,
    ) -> None:
        payload: Dict[str, Any] = {}
        if fraction is not None:
            payload["fraction"] = float(fraction)
        if message is not None:
            payload["message"] = str(message)
        if fields:
            payload.update(fields)
        if payload:
            self._controller._emit_progress(self.task_id, payload)

    # nur Controller darf Cancel setzen
    def _request_cancel(self) -> None:
        self._cancel_event.set()

class AppController:
    def __init__(self, telemetry: Any | None = None):
        self._in: queue.Queue[TaskRequest] = queue.Queue()
        self._out: queue.Queue[TaskResult | tuple[str, str, Any]] = queue.Queue()
        self._handlers: Dict[str, Callable[[dict], Any]] = {}
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="AppControllerWorker", daemon=True)
        self._telemetry = telemetry
        self._thread.start()
        self._stream_chunk_counter = {}
        self._active_contexts: Dict[str, TaskContext] = {}
        self._handler_context_strategy: Dict[Callable[..., Any], Optional[tuple[str, Optional[str]]]] = {}

    def register(self, task_type: str, handler: Callable[[dict], Any]):
        self._handlers[task_type] = handler

    def submit(self, task_type: str, payload: dict) -> str:
        tid = next_task_id()
        self._in.put(TaskRequest(task_id=tid, task_type=task_type, payload=payload))
        return tid

    def cancel(self, task_id: str) -> bool:
        ctx = self._active_contexts.get(task_id)
        if not ctx:
            return False
        ctx._request_cancel()
        self._out.put((task_id, "cancel_requested", None))
        return True

    def poll_results(self, max_items: int = 20) -> list[Any]:
        items: list[Any] = []
        for _ in range(max_items):
            try:
                items.append(self._out.get_nowait())
            except queue.Empty:
                break
        return items

    def shutdown(self, timeout: float = 2.0):
        self._stop.set()
        self._in.put(None)  # type: ignore
        self._thread.join(timeout=timeout)

    def _emit_progress(self, task_id: str, payload: Dict[str, Any]) -> None:
        self._out.put((task_id, "progress", payload))

    def _handler_context_info(self, handler: Callable[..., Any]) -> Optional[tuple[str, Optional[str]]]:
        cached = self._handler_context_strategy.get(handler)
        if cached is not None or handler in self._handler_context_strategy:
            return cached
        try:
            sig = inspect.signature(handler)
            params = list(sig.parameters.values())
            strategy: Optional[tuple[str, Optional[str]]] = None
            if params:
                context_param = None
                for p in params[1:]:
                    if p.name in ("context", "ctx", "task_context"):
                        context_param = p
                        break
                if context_param is not None:
                    if context_param.kind == inspect.Parameter.KEYWORD_ONLY:
                        strategy = ("keyword", context_param.name)
                    else:
                        strategy = ("positional", None)
                elif any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params):
                    strategy = ("keyword", "context")
                elif any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in params[1:]):
                    strategy = ("positional", None)
            self._handler_context_strategy[handler] = strategy
            return strategy
        except (TypeError, ValueError):
            self._handler_context_strategy[handler] = None
            return None

    # Interner Worker
    def _run(self):
        while not self._stop.is_set():
            try:
                req = self._in.get(timeout=0.25)
            except queue.Empty:
                continue
            if req is None:  # Shutdown Sentinel
                break
            handler = self._handlers.get(req.task_type)
            start = time.perf_counter()
            if not handler:
                self._out.put(TaskResult(task_id=req.task_id, task_type=req.task_type, success=False, error=f"Unknown task_type {req.task_type}"))
                continue
            context = TaskContext(self, req)
            self._active_contexts[req.task_id] = context
            cancelled = False
            try:
                context_info = self._handler_context_info(handler)
                if context_info is None:
                    result = handler(req.payload)
                else:
                    mode, name = context_info
                    if mode == "keyword" and name:
                        result = handler(req.payload, **{name: context})
                    else:
                        result = handler(req.payload, context)
                # Streaming-Unterstützung: Iterator liefert Zwischenstände => (task_id, 'chunk', data)
                if isinstance(result, Iterable) and not isinstance(result, (str, bytes, dict)):
                    self._out.put((req.task_id, 'stream_start', None))
                    chunk_count = 0
                    for chunk in result:
                        if context.is_cancelled():
                            raise TaskCancelled("Task cancelled during streaming")
                        self._out.put((req.task_id, 'chunk', chunk))
                        chunk_count += 1
                    if self._telemetry:
                        try:
                            self._telemetry.record('task_stream_summary', task_type=req.task_type, chunks=chunk_count)
                        except Exception:
                            pass
                    out_res = TaskResult(task_id=req.task_id, task_type=req.task_type, success=True, data=None)
                else:
                    out_res = TaskResult(task_id=req.task_id, task_type=req.task_type, success=True, data=result)
            except TaskCancelled as e:
                cancelled = True
                cancel_info = {"message": str(e)} if str(e) else {}
                self._out.put((req.task_id, 'cancelled', cancel_info or None))
                out_res = TaskResult(task_id=req.task_id, task_type=req.task_type, success=False, error=str(e))
            except Exception as e:
                tb = traceback.format_exc(limit=4)
                out_res = TaskResult(task_id=req.task_id, task_type=req.task_type, success=False, error=f"{e}\n{tb}")
            finally:
                self._active_contexts.pop(req.task_id, None)
                out_res.started_ts = start
                out_res.finished_ts = time.perf_counter()
                if self._telemetry:
                    try:
                        self._telemetry.record(
                            "task_event",
                            task_type=req.task_type,
                            success=out_res.success and not cancelled,
                            duration_s=round(out_res.duration_s, 6),
                        )
                    except Exception:
                        pass
                self._out.put(out_res)
        # Ende Loop
