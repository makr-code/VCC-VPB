"""Task management utilities for the VPB application."""

from __future__ import annotations

from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - imported only for type checking
    from vpb_app import VPBDesignerApp  # noqa: F401


class TaskManager:
    """Encapsulates background task bookkeeping and UI updates."""

    _PENDING_ATTR = {
        "validate_process": "pending_validation_task",
        "merge_full": "pending_merge_task",
        "patch_add_only": "pending_patch_task",
        "ai_ingestion": "pending_ingestion_task",
    }

    def __init__(self, app: "VPBDesignerApp") -> None:
        self._app = app
        self._task_types: Dict[str, str] = {}
        self._task_progress: Dict[str, dict] = {}
        self._task_cancel_requested: set[str] = set()
        self._task_cancelled: set[str] = set()

        self.pending_validation_task: Optional[str] = None
        self.pending_merge_task: Optional[str] = None
        self.pending_patch_task: Optional[str] = None
        self.pending_ingestion_task: Optional[str] = None

    # ---- public helpers -------------------------------------------------

    def track_start(self, task_id: Optional[str], task_type: str) -> None:
        if not task_id:
            return
        self._task_types[task_id] = task_type
        self._task_progress.pop(task_id, None)
        self._task_cancel_requested.discard(task_id)
        self._task_cancelled.discard(task_id)

    def track_end(self, task_id: Optional[str]) -> None:
        if not task_id:
            return
        self._task_types.pop(task_id, None)
        self._task_progress.pop(task_id, None)
        self._task_cancel_requested.discard(task_id)
        self._task_cancelled.discard(task_id)

    def set_pending(self, task_type: str, task_id: Optional[str]) -> None:
        attr = self._PENDING_ATTR.get(task_type)
        if attr:
            setattr(self, attr, task_id)

    def get_pending(self, task_type: str) -> Optional[str]:
        attr = self._PENDING_ATTR.get(task_type)
        return getattr(self, attr, None) if attr else None

    def clear_pending(self, task_type: str) -> None:
        self.set_pending(task_type, None)

    def is_cancelled(self, task_id: Optional[str]) -> bool:
        return bool(task_id and task_id in self._task_cancelled)

    # ---- controller event wiring ----------------------------------------

    def handle_progress_event(self, task_id: str, payload: Any) -> None:
        info = payload if isinstance(payload, dict) else {}
        self._task_progress[task_id] = info

        task_type = self._task_types.get(task_id)
        if not task_type:
            return

        message = info.get("message") if isinstance(info, dict) else None
        fraction = info.get("fraction") if isinstance(info, dict) else None

        chat = getattr(self._app, "chat", None)
        status = getattr(self._app, "status", None)

        if task_type == "ollama_chat_stream" and chat is not None:
            if message:
                try:
                    chat.set_progress(message, fraction=fraction)
                except Exception:
                    pass
        elif task_type == "validate_process" and status is not None:
            if message:
                self._set_status(f"Validierung: {message}")
        elif task_type in ("merge_full", "patch_add_only") and status is not None:
            if message:
                label = "Merge" if task_type == "merge_full" else "Patch"
                self._set_status(f"{label}: {message}")
        elif task_type == "ai_ingestion":
            if chat is not None:
                try:
                    chat.set_progress(message or "AI-Ingestion läuft", fraction=fraction)
                except Exception:
                    pass
            if message:
                self._set_status(f"AI-Ingestion: {message}")

    def handle_cancel_requested(self, task_id: str) -> None:
        task_type = self._task_types.get(task_id)
        if not task_type:
            return
        self._task_cancel_requested.add(task_id)
        label = self._task_label(task_type)

        if task_type == "ollama_chat_stream":
            chat = getattr(self._app, "chat", None)
            if chat is not None:
                try:
                    chat.set_progress("Abbruch wird angefordert …")
                except Exception:
                    pass
        elif task_type == "ai_ingestion":
            chat = getattr(self._app, "chat", None)
            if chat is not None:
                try:
                    chat.set_progress("Abbruch wird angefordert …")
                except Exception:
                    pass
        self._set_status(f"{label}: Abbruch angefordert")

    def handle_cancelled(self, task_id: str, data: Any) -> None:
        task_type = self._task_types.get(task_id)
        self._task_cancelled.add(task_id)
        self._task_cancel_requested.discard(task_id)

        reason = None
        if isinstance(data, dict):
            reason = data.get("message")

        if not task_type:
            return

        label = self._task_label(task_type)
        chat = getattr(self._app, "chat", None)

        if task_type == "ollama_chat_stream":
            if chat is not None:
                try:
                    chat.set_progress(reason or "Abgebrochen")
                    chat.set_busy(False)
                except Exception:
                    pass
            setattr(self._app, "_current_chat_task", None)
            self._set_status("AI: Chat abgebrochen")
        elif task_type == "validate_process":
            self.clear_pending("validate_process")
            self._set_status("Validierung abgebrochen")
        elif task_type == "merge_full":
            self.clear_pending("merge_full")
            self._set_status("Merge abgebrochen")
        elif task_type == "patch_add_only":
            self.clear_pending("patch_add_only")
            self._set_status("Patch abgebrochen")
        elif task_type == "ai_ingestion":
            self.clear_pending("ai_ingestion")
            self._set_status("AI-Ingestion abgebrochen")
            if chat is not None:
                try:
                    chat.set_progress(reason or "Abgebrochen")
                    chat.clear_dynamic_actions()
                    chat.add_dynamic_button("AI-Ingestion starten", self._app._start_ingestion_from_pending)
                except Exception:
                    pass

    # ---- helpers --------------------------------------------------------

    @staticmethod
    def _task_label(task_type: str) -> str:
        return {
            "ollama_chat_stream": "AI Chat",
            "validate_process": "Validierung",
            "merge_full": "Merge",
            "patch_add_only": "Patch",
            "ai_ingestion": "AI-Ingestion",
        }.get(task_type, task_type)

    def _set_status(self, message: str) -> None:
        status = getattr(self._app, "status", None)
        if status is None:
            return
        try:
            status.set(message)
        except Exception:
            pass
# ---------------------------------------------------------------------------