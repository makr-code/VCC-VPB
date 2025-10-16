"""Controller für die Chat-Konsole im VPB-Designer."""

from __future__ import annotations

import datetime
import getpass
import hashlib
import json
import os
import re
import socket
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, List, Optional

from tkinter import messagebox

from vpb.styles import CONNECTION_STYLES, ELEMENT_STYLES

from .chat_panel import ChatPanel
from .task_manager import TaskManager

if TYPE_CHECKING:
    from vpb_app import VPBDesignerApp


class ChatController:
    """Kapselt Chat-spezifische Logik und Zustand vom Hauptfenster."""

    def __init__(self, app: "VPBDesignerApp") -> None:
        self._app = app
        self._chat: Optional[ChatPanel] = None
        self._tasks: Optional[TaskManager] = None
        self._messages: List[Dict[str, str]] = []
        self._assistant_buffer: str = ""
        self._history_file: Optional[str] = None
        self._pending_user_text: Optional[str] = None
        self._current_task_id: Optional[str] = None
        self._project_id: Optional[str] = None
        self._project_path: Optional[str] = None

    # -- Lifecycle -----------------------------------------------------
    def bind_ui(self, chat_panel: ChatPanel, task_manager: TaskManager) -> None:
        self._chat = chat_panel
        self._tasks = task_manager
        try:
            self.chat.reset_conversation()
        except Exception:
            pass
        self._messages = []
        self._assistant_buffer = ""
        self._pending_user_text = None

    def switch_project(self, path: Optional[str], *, preserve_current: bool = False) -> None:
        normalized_path = os.path.abspath(path) if path else None
        new_id = self._compute_project_id(normalized_path)
        if (
            new_id == self._project_id
            and (not preserve_current or normalized_path == self._project_path)
        ):
            return

        if self._project_id is not None and self._messages:
            self.save_history()

        current_messages = list(self._messages) if preserve_current else []

        self._project_id = new_id
        self._project_path = normalized_path
        self._history_file = None
        self._assistant_buffer = ""
        self._pending_user_text = None

        if self._chat:
            try:
                self.chat.reset_conversation()
            except Exception:
                pass

        if preserve_current and current_messages:
            self._messages = current_messages
            self._replay_messages_to_ui(current_messages)
            self._init_chat_history_file()
            self._save_chat_history()
            return

        self._messages = []
        if normalized_path:
            self._init_chat_history_file()
            self._load_chat_history()

    # -- Properties ----------------------------------------------------
    @property
    def chat(self) -> ChatPanel:
        if self._chat is None:
            raise RuntimeError("ChatPanel wurde noch nicht gebunden")
        return self._chat

    @property
    def tasks(self) -> TaskManager:
        if self._tasks is None:
            raise RuntimeError("TaskManager wurde noch nicht gebunden")
        return self._tasks

    # -- Public API für UI-Callbacks -----------------------------------
    def handle_send(self, text: str) -> None:
        text = (text or "").strip()
        if not text:
            return
        controller = getattr(self._app, "_app_controller", None)
        if controller is None:
            messagebox.showwarning("AI", "Hintergrund-Controller nicht verfügbar.")
            return
        if self.chat.is_busy():
            self._app.status.set("Chat läuft bereits – bitte warten")
            return

        messages = [{"role": "system", "content": self._chat_system_prompt()}]
        messages.extend(self._messages)
        messages.append({"role": "user", "content": text})

        payload = {
            "endpoint": self._app._ollama_endpoint,
            "model": self._app._ollama_model,
            "temperature": self._app._ollama_temperature,
            "num_predict": self._app._ollama_num_predict,
            "messages": messages,
        }

        self.chat.add_user(text)
        self.chat.start_assistant()
        self.chat.set_busy(True)
        self.chat.clear_dynamic_actions()
        self._assistant_buffer = ""
        self._pending_user_text = text
        self._ensure_chat_visible()

        try:
            task_id = controller.submit("ollama_chat_stream", payload)
            self._current_task_id = task_id
            self.tasks.track_start(task_id, "ollama_chat_stream")
            self.chat.set_progress("LLM wird kontaktiert …", fraction=0.0)
            self._app.status.set("AI: Chat gestartet")
        except Exception as exc:  # noqa: BLE001
            self.chat.set_busy(False)
            messagebox.showerror("AI", f"Chat konnte nicht gestartet werden: {exc}")

    def handle_attach(self, path: str, content: str, truncated: bool) -> None:
        filename = os.path.basename(path)
        prefix = f"Berücksichtige bitte die Prozessbeschreibung aus der Datei '{filename}'."
        if truncated:
            prefix += " (Hinweis: Datei wurde gekürzt auf 60.000 Zeichen.)"
        payload_text = f"{prefix}\n\n{content}"
        self.handle_send(payload_text)

    def handle_stop(self) -> None:
        controller = getattr(self._app, "_app_controller", None)
        if not controller or not self._current_task_id:
            self.chat.set_busy(False)
            self._app.status.set("AI: Kein laufender Chat")
            return
        try:
            cancelled = controller.cancel(self._current_task_id)
        except Exception as exc:  # noqa: BLE001
            self.chat.set_busy(False)
            self._app.status.set(f"AI: Abbruch fehlgeschlagen ({exc})")
            return
        if not cancelled:
            self.chat.set_busy(False)
            self._app.status.set("AI: Kein laufender Chat")
            return
        self.chat.set_progress("Abbruch wird angefordert …")
        self._app.status.set("AI: Chat-Abbruch angefordert")

    # -- Controller-Events ---------------------------------------------
    def handle_stream_event(self, kind: str, data: Any) -> bool:
        if kind == "stream_start":
            self._assistant_buffer = ""
            return True
        if kind == "chunk":
            chunk = str(data)
            self._assistant_buffer += chunk
            self.chat.append_assistant(chunk)
            return True
        return False

    def handle_task_result(self, success: bool, error: Optional[str], cancelled: bool) -> None:
        if cancelled:
            return
        if not success:
            messagebox.showerror("AI", error or "Unbekannter Fehler")
        self.chat.set_busy(False)
        self.chat.set_progress(None)
        self._current_task_id = None
        if self._pending_user_text:
            self._messages.append({"role": "user", "content": self._pending_user_text})
            self._pending_user_text = None
        if self._assistant_buffer:
            self._messages.append({"role": "assistant", "content": self._assistant_buffer})
            self._save_chat_history()
            processed = False
            try:
                processed = self._postprocess_chat_result()
            except Exception:
                processed = False
            if not processed:
                try:
                    self.chat.finalize_assistant_message()
                except Exception:  # noqa: BLE001
                    pass
        self._app.status.set("AI: Chat fertig")

    # -- Append Helpers ------------------------------------------------
    def append_block(self, title: str, lines: Iterable[str]) -> None:
        try:
            iterable = [str(line) for line in lines if str(line).strip()]
        except Exception:  # noqa: BLE001
            iterable = []
        if not iterable:
            return
        self.chat.append_assistant(f"\n[{title}]\n" + "\n".join(iterable))

    def append_merge_feedback(self, label: str, data: Dict[str, Any]) -> None:
        lines: List[str] = []
        added_e = int(data.get("added_elements") or 0)
        added_c = int(data.get("added_connections") or 0)
        lines.append(f"- Elemente hinzugefügt: {added_e}")
        lines.append(f"- Verbindungen hinzugefügt: {added_c}")

        element_renames = data.get("element_renames") or {}
        if isinstance(element_renames, dict) and element_renames:
            lines.append("- Element-ID Umbenennungen:")
            for old_id, new_id in element_renames.items():
                lines.append(f"  • {old_id} → {new_id}")

        connection_renames = data.get("connection_renames") or {}
        if isinstance(connection_renames, dict) and connection_renames:
            lines.append("- Verbindungs-ID Umbenennungen:")
            for old_id, new_id in connection_renames.items():
                lines.append(f"  • {old_id} → {new_id}")

        summary_lines = data.get("summary_lines") or []
        if isinstance(summary_lines, (list, tuple)) and summary_lines:
            lines.append("- Zusammenfassung:")
            for line in summary_lines:
                lines.append(f"  • {line}")

        warnings = data.get("warnings") or []
        if isinstance(warnings, (list, tuple)) and warnings:
            lines.append("- Warnungen:")
            for warn in warnings:
                lines.append(f"  • {warn}")

        self.append_block(label, lines)

    def append_ingestion_feedback(self, data: Dict[str, Any]) -> None:
        diff = data.get("diff") if isinstance(data.get("diff"), dict) else {}
        elements = diff.get("elements", []) if isinstance(diff, dict) else []
        connections = diff.get("connections", []) if isinstance(diff, dict) else []

        warnings = data.get("warnings") if isinstance(data.get("warnings"), (list, tuple)) else []
        issues = data.get("issues") if isinstance(data.get("issues"), (list, tuple)) else []
        guardrails = data.get("guardrail_issues") if isinstance(data.get("guardrail_issues"), (list, tuple)) else []
        guardrail_summary = data.get("guardrail_summary") if isinstance(data.get("guardrail_summary"), dict) else {}
        attempts = data.get("attempts")

        lines: List[str] = []
        lines.append(f"- Diff: {len(elements)} neue Elemente, {len(connections)} neue Verbindungen")
        if attempts not in (None, ""):
            lines.append(f"- Versuche: {attempts}")
        warnings_list = list(warnings)
        issues_list = list(issues)
        if warnings_list:
            lines.append(f"- Warnungen: {len(warnings_list)} (siehe Details)")
        if issues_list:
            lines.append(f"- Validierungs-Hinweise: {len(issues_list)}")
        if guardrails:
            errs = guardrail_summary.get("error") if isinstance(guardrail_summary, dict) else None
            warns = guardrail_summary.get("warning") if isinstance(guardrail_summary, dict) else None
            infos = guardrail_summary.get("info") if isinstance(guardrail_summary, dict) else None
            detail_parts = []
            if isinstance(errs, int) and errs:
                detail_parts.append(f"{errs} Fehler")
            if isinstance(warns, int) and warns:
                detail_parts.append(f"{warns} Hinweise")
            if isinstance(infos, int) and infos:
                detail_parts.append(f"{infos} Infos")
            if detail_parts:
                lines.append("- Guardrail-Auswertung: " + ", ".join(detail_parts))

        source_preview = data.get("source_preview")
        if isinstance(source_preview, list) and source_preview:
            lines.append("- Quellenübersicht:")
            for idx, src in enumerate(source_preview[:3], 1):
                if isinstance(src, dict):
                    label = src.get("path") or src.get("name") or src.get("type") or f"Quelle {idx}"
                    extra: List[str] = []
                    if src.get("type"):
                        extra.append(str(src.get("type")))
                    if src.get("characters"):
                        extra.append(f"{src.get('characters')} Zeichen")
                    if src.get("rows") and src.get("columns"):
                        extra.append(f"{src.get('rows')}×{src.get('columns')} Zellen")
                    info = ", ".join(extra)
                    if src.get("truncated"):
                        info = (info + "; gekürzt") if info else "gekürzt"
                    lines.append(f"  • {label}" + (f" ({info})" if info else ""))
            if len(source_preview) > 3:
                lines.append(f"  • … (+{len(source_preview) - 3} weitere)")

        prompt_meta = data.get("prompt_meta")
        if isinstance(prompt_meta, dict):
            meta_bits: List[str] = []
            if prompt_meta.get("version"):
                meta_bits.append(f"Version {prompt_meta.get('version')}")
            if prompt_meta.get("token_estimate"):
                meta_bits.append(f"≈ {prompt_meta.get('token_estimate')} Tokens")
            tags = prompt_meta.get("example_tags")
            if isinstance(tags, list) and tags:
                meta_bits.append("Tags: " + ", ".join(str(t) for t in tags[:4]))
                if len(tags) > 4:
                    meta_bits[-1] += " …"
            warnings_meta = prompt_meta.get("warnings")
            if isinstance(warnings_meta, list) and warnings_meta:
                meta_bits.append(f"Prompt-Warnungen: {len(warnings_meta)}")
            if meta_bits:
                lines.append("- Prompt: " + "; ".join(meta_bits))
        self.append_block("AI-Ingestion Ergebnis", lines)

    # -- Persistence ---------------------------------------------------
    def save_history(self) -> None:
        if self._project_id is None:
            return
        if not self._messages:
            return
        if not self._history_file:
            self._init_chat_history_file()
        path = self._history_file
        if not path:
            return
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
        except Exception:
            pass
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._messages, f, ensure_ascii=False, indent=2)
        except Exception:  # noqa: BLE001
            pass

    # -- Internals -----------------------------------------------------
    def _chat_system_prompt(self) -> str:
        try:
            element_types = ", ".join(sorted(ELEMENT_STYLES.keys()))
            connection_types = ", ".join(sorted(CONNECTION_STYLES.keys()))
            current = json.dumps(self._app.canvas.to_dict(), ensure_ascii=False)
        except Exception:
            element_types = "+".join(sorted(ELEMENT_STYLES.keys()))
            connection_types = "+".join(sorted(CONNECTION_STYLES.keys()))
            current = "{}"
        return (
            "Du bist ein hilfreicher Assistent für einen visuellen Prozess-Designer (VPB). "
            "Antworte auf Deutsch, sei knapp und konkret. Wenn du Prozesslogik erläuterst, beziehe dich auf die VPB-Typen.\n"
            f"Erlaubte Element-Typen: {element_types}.\n"
            f"Erlaubte Verbindungstypen: {connection_types}.\n"
            "Aktuelles Diagramm (JSON):\n" + current
        )

    def _ensure_chat_visible(self) -> None:
        try:
            self._app._ensure_chat_visible()
        except Exception:  # noqa: BLE001
            pass

    def _postprocess_chat_result(self) -> bool:
        buf = self._assistant_buffer.strip()
        if not buf:
            return False
        try:
            from ollama_client import OllamaClient as _OC  # type: ignore

            parsed = _OC.extract_json(buf)
        except Exception:  # noqa: BLE001
            return False
        if not isinstance(parsed, dict):
            return False
        callbacks: Dict[str, Callable[[], None]] = {}
        self.chat.clear_dynamic_actions()
        if all(k in parsed for k in ("metadata", "elements", "connections")):
            replace_cb = lambda p=parsed: self._app._apply_full_process_json(p)
            merge_cb = lambda p=parsed: self._app._merge_full_process_json(p)
            callbacks["apply_patch"] = replace_cb
            self.chat.add_dynamic_button("Diagramm ersetzen", replace_cb)
            self.chat.add_dynamic_button("Diagramm mergen", merge_cb)
        if set(parsed.keys()) <= {"elements", "connections"} and any(k in parsed for k in ("elements", "connections")):
            patch_cb = lambda p=parsed: self._app._apply_add_only_patch(p)
            callbacks["apply_patch"] = patch_cb
            self.chat.add_dynamic_button("Patch anwenden", patch_cb)
        if "issues" in parsed and isinstance(parsed.get("patch"), dict):
            issues = parsed.get("issues") or []
            self._app.status.set(f"Diagnose: {len(issues)} Issues gefunden")
            diag_cb = lambda p=parsed: self._app._apply_diagnose_patch(p)
            callbacks["apply_patch"] = diag_cb
            self.chat.add_dynamic_button("Diagnose-Patch anwenden", diag_cb)

        try:
            self.chat.finalize_assistant_message(parsed, callbacks)
        except Exception:  # noqa: BLE001
            pass
        return True

    def _chat_history_dir(self) -> str:
        base = os.path.join(os.getcwd(), "chats")
        try:
            user = getpass.getuser() or "user"
        except Exception:
            user = "user"
        try:
            host = socket.gethostname() or "host"
        except Exception:
            host = "host"
        model = (self._app._ollama_model or "model").replace("/", "_").replace(":", "_")
        path = os.path.join(base, f"{user}@{host}", model)
        if self._project_id:
            path = os.path.join(path, self._project_id)
        try:
            os.makedirs(path, exist_ok=True)
        except Exception:
            pass
        return path

    def _init_chat_history_file(self) -> None:
        if self._project_id is None:
            self._history_file = None
            return
        dirp = self._chat_history_dir()
        self._history_file = os.path.join(dirp, "chat.json")

    def _load_chat_history(self) -> None:
        if not self._history_file or not os.path.exists(self._history_file):
            return
        try:
            with open(self._history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:  # noqa: BLE001
            return
        if not isinstance(data, list):
            return
        msgs = []
        for m in data:
            if not isinstance(m, dict):
                continue
            role = str(m.get("role", "")).strip()
            content = str(m.get("content", ""))
            if role in ("user", "assistant") and content:
                msgs.append({"role": role, "content": content})
        self._messages = msgs
        self._replay_messages_to_ui(self._messages)

    def _save_chat_history(self) -> None:
        self.save_history()

    def _compute_project_id(self, path: Optional[str]) -> Optional[str]:
        if not path:
            return None
        base = os.path.splitext(os.path.basename(path))[0] or "projekt"
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", base).strip("_") or "projekt"
        digest = hashlib.sha1(path.encode("utf-8")).hexdigest()[:10]
        return f"{slug}-{digest}"

    def _replay_messages_to_ui(self, messages: Iterable[Dict[str, str]]) -> None:
        chat = self._chat
        if not chat:
            return
        chat.clear_dynamic_actions()
        chat.set_progress(None)
        for msg in messages:
            try:
                role = msg.get("role")
                content = str(msg.get("content", ""))
            except Exception:
                continue
            if not content:
                continue
            if role == "user":
                chat.add_user(content)
            elif role == "assistant":
                chat.start_assistant()
                chat.append_assistant(content)
                try:
                    chat.finalize_assistant_message()
                except Exception:
                    pass


__all__ = ["ChatController"]
