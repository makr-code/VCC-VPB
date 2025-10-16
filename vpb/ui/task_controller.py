"""Controller für Hintergrund-Tasks im VPB-Designer."""

from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

from tkinter import messagebox

from .task_manager import TaskManager

if TYPE_CHECKING:  # pragma: no cover
    from vpb_app import VPBDesignerApp


class TaskController:
    """Koordiniert Hintergrund-Tasks und UI-Aktualisierungen."""

    def __init__(self, app: "VPBDesignerApp") -> None:
        self._app = app
        self._tasks: Optional[TaskManager] = None

    # -- Lifecycle -------------------------------------------------
    def bind_ui(self, task_manager: TaskManager) -> None:
        self._tasks = task_manager

    # -- Convenience ----------------------------------------------
    @property
    def tasks(self) -> Optional[TaskManager]:
        if self._tasks is not None:
            return self._tasks
        return getattr(self._app, "tasks", None)

    def has_pending(self, task_type: str) -> bool:
        tasks = self.tasks
        return bool(tasks and tasks.get_pending(task_type))

    def pending_id(self, task_type: str) -> Optional[str]:
        tasks = self.tasks
        return tasks.get_pending(task_type) if tasks else None

    def register_task_start(self, task_type: str, task_id: Optional[str]) -> None:
        tasks = self.tasks
        if not tasks or not task_id:
            return
        tasks.set_pending(task_type, task_id)
        tasks.track_start(task_id, task_type)

    def clear_pending(self, task_type: str) -> None:
        tasks = self.tasks
        if tasks:
            tasks.clear_pending(task_type)

    def mark_task_end(self, task_id: Optional[str]) -> None:
        tasks = self.tasks
        if tasks and task_id:
            tasks.track_end(task_id)

    def is_cancelled(self, task_id: Optional[str]) -> bool:
        tasks = self.tasks
        return bool(tasks and tasks.is_cancelled(task_id))

    # -- Controller Events ----------------------------------------
    def handle_poll_item(self, item: Any) -> bool:
        try:
            from core.message_bus import TaskResult  # type: ignore
        except Exception:  # pragma: no cover - TaskResult optional
            TaskResult = None  # type: ignore

        if isinstance(item, tuple) and len(item) == 3:
            task_id, kind, data = item
            tasks = self.tasks
            if tasks:
                if kind == "progress":
                    tasks.handle_progress_event(task_id, data)
                    return True
                if kind == "cancel_requested":
                    tasks.handle_cancel_requested(task_id)
                    return True
                if kind == "cancelled":
                    tasks.handle_cancelled(task_id, data)
                    return True
            chat_controller = getattr(self._app, "chat_controller", None)
            if chat_controller and chat_controller.handle_stream_event(kind, data):
                return True
            return False

        if TaskResult and isinstance(item, TaskResult):
            self._handle_task_result(item)
            return True

        return False

    # -- Internals -------------------------------------------------
    def _handle_task_result(self, item: Any) -> None:
        tasks = self.tasks
        cancelled = bool(tasks and tasks.is_cancelled(item.task_id))
        task_id = getattr(item, "task_id", None)
        task_type = getattr(item, "task_type", None)

        try:
            if task_type == "validate_process":
                pending_id = self.pending_id("validate_process")
                if pending_id and task_id != pending_id:
                    return
                if pending_id == task_id:
                    self.clear_pending("validate_process")
                if cancelled:
                    return
                if not item.success:
                    messagebox.showerror("Prozess prüfen", item.error or "Unbekannter Fehler")
                    self._app.status.set("Validierung Fehler")
                    return
                data = item.data
                if isinstance(data, tuple):
                    ok = bool(data[0]) if len(data) >= 1 else False
                    err = data[1] if len(data) > 1 else None
                elif isinstance(data, bool):
                    ok, err = data, None
                elif isinstance(data, dict):
                    ok = bool(data.get("ok"))
                    err = data.get("error")
                else:
                    ok, err = bool(data), None
                if err is not None and not isinstance(err, str):
                    err = str(err)
                self._app._display_validation_result(ok, err)
                return

            if task_type in {"merge_full", "patch_add_only"}:
                pending_id = self.pending_id(task_type)
                if pending_id and task_id != pending_id:
                    return
                if pending_id == task_id:
                    self.clear_pending(task_type)
                label = "Merge" if task_type == "merge_full" else "Patch"
                if cancelled:
                    return
                if not item.success:
                    messagebox.showerror(label, item.error or "Unbekannter Fehler")
                    self._app.status.set(f"{label}: Fehler")
                    return

                result = item.data or {}
                prev_element_ids = set(self._app.canvas.elements.keys())
                prev_connection_ids = set(self._app.canvas.connections.keys())
                diagram = result.get("diagram") if isinstance(result, dict) else None
                if isinstance(diagram, dict):
                    try:
                        self._app.canvas.push_undo()
                    except Exception:
                        pass
                    try:
                        self._app.canvas.load_from_dict(diagram)
                        self._app.canvas.redraw_all()
                    except Exception as exc:  # noqa: BLE001
                        messagebox.showerror(label, f"Diagramm konnte nicht übernommen werden: {exc}")
                        self._app.status.set(f"{label}: Fehler bei Übernahme")
                        return

                element_renames = (result.get("element_renames") or {}).values()
                connection_renames = (result.get("connection_renames") or {}).values()
                self._app._highlight_merge_changes(
                    prev_element_ids,
                    prev_connection_ids,
                    element_renames=element_renames,
                    connection_renames=connection_renames,
                )

                block_title = "Merge Ergebnis" if task_type == "merge_full" else "Patch Ergebnis"
                chat_controller = getattr(self._app, "chat_controller", None)
                if chat_controller:
                    chat_controller.append_merge_feedback(block_title, result)

                warnings = result.get("warnings") or []
                if warnings:
                    try:
                        messagebox.showwarning(label, "\n".join(str(w) for w in warnings))
                    except Exception:
                        pass

                added_e = result.get("added_elements", 0)
                added_c = result.get("added_connections", 0)
                status_text = (
                    f"Merge abgeschlossen (+{added_e}/+{added_c})"
                    if task_type == "merge_full"
                    else f"Patch angewendet (+{added_e}/+{added_c})"
                )
                self._app.status.set(status_text)
                return

            if task_type == "ai_ingestion":
                pending_id = self.pending_id("ai_ingestion")
                if pending_id and task_id != pending_id:
                    return
                if pending_id == task_id:
                    self.clear_pending("ai_ingestion")
                if hasattr(self._app, "chat"):
                    try:
                        self._app.chat.set_progress(None)
                    except Exception:
                        pass
                if cancelled:
                    return
                if not item.success:
                    messagebox.showerror("AI-Ingestion", item.error or "Unbekannter Fehler")
                    self._app.status.set("AI-Ingestion: Fehler")
                    if hasattr(self._app, "chat"):
                        try:
                            self._app.chat.clear_dynamic_actions()
                            self._app.chat.add_dynamic_button(
                                "AI-Ingestion starten",
                                self._app._start_ingestion_from_pending,
                            )
                        except Exception:
                            pass
                    return

                raw_result = item.data if isinstance(item.data, dict) else {}
                result = dict(raw_result)
                diff = result.get("diff") if isinstance(result.get("diff"), dict) else None
                warnings = []
                raw_warnings = result.get("warnings")
                if isinstance(raw_warnings, (list, tuple)):
                    warnings = [str(w) for w in raw_warnings if w is not None]
                self._app._latest_ingestion_diff = diff
                self._app._latest_ingestion_result = result
                self._app._latest_ingestion_warnings = warnings

                chat_controller = getattr(self._app, "chat_controller", None)
                if chat_controller:
                    chat_controller.append_ingestion_feedback(result)

                if warnings:
                    try:
                        messagebox.showwarning("AI-Ingestion", "\n".join(warnings))
                    except Exception:
                        pass

                if hasattr(self._app, "chat"):
                    try:
                        self._app.chat.clear_dynamic_actions()
                        if diff:
                            self._app.chat.add_dynamic_button("Diff prüfen…", self._app._review_ingestion_diff)
                        self._app.chat.add_dynamic_button("Details anzeigen…", self._app._show_ingestion_details)
                        self._app.chat.add_dynamic_button("AI-Ingestion erneut starten", self._app._start_ingestion_from_pending)
                    except Exception:
                        pass
                added_e = len(diff.get("elements", [])) if isinstance(diff, dict) else 0
                added_c = len(diff.get("connections", [])) if isinstance(diff, dict) else 0
                self._app.status.set(f"AI-Ingestion abgeschlossen (+{added_e}/+{added_c})")
                return

            if task_type == "ollama_chat_stream":
                chat_controller = getattr(self._app, "chat_controller", None)
                if chat_controller:
                    chat_controller.handle_task_result(item.success, item.error, cancelled)
                elif not cancelled and not item.success:
                    messagebox.showerror("AI", item.error or "Unbekannter Fehler")
                return
        finally:
            if tasks and task_id:
                tasks.track_end(task_id)