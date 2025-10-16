from __future__ import annotations

import json
from typing import TYPE_CHECKING, List, Optional

import tkinter as tk
from tkinter import messagebox

try:  # pragma: no cover - optional dependency
    from ollama_client import OllamaClient, OllamaOptions, OllamaJob  # type: ignore
except Exception:  # pragma: no cover - optional dependency missing
    OllamaClient = None  # type: ignore
    OllamaOptions = None  # type: ignore
    OllamaJob = None  # type: ignore

from merge_manager import MergeManager, MergeResult
from vpb.styles import CONNECTION_STYLES, ELEMENT_STYLES

if TYPE_CHECKING:  # pragma: no cover
    from vpb_app import VPBApp


class AppChatIntegration:
    """Kapselt Chat- und AI-bezogene Hilfsmethoden der ``VPBApp``."""

    def __init__(self, app: "VPBApp") -> None:
        self._app = app

    def ensure_chat_visible(self, min_height: int = 200) -> None:
        app = self._app
        try:
            split = getattr(app, "_mid_split", None)
            if not split:
                return
            total = int(split.winfo_height() or 0)
            if total <= 0:
                app.after(120, lambda: self.ensure_chat_visible(min_height))
                return
            try:
                sash = int(split.sashpos(0))
            except Exception:
                return
            bottom_height = total - sash
            if bottom_height < min_height:
                new_sash = max(0, total - min_height)
                try:
                    split.sashpos(0, new_sash)
                except Exception:
                    pass
        except Exception:
            pass

    def focus_chat(self) -> None:
        app = self._app
        try:
            self.ensure_chat_visible()
            chat = getattr(app, "chat", None)
            if chat:
                chat.focus_input()
                status = getattr(app, "status", None)
                if status is not None:
                    try:
                        status.set("AI-Konsole aktiv")
                    except Exception:
                        pass
        except Exception:
            pass

    def handle_ctrl_enter(self, event=None):  # type: ignore[override]
        app = self._app
        try:
            focus = app.focus_get()
            chat = getattr(app, "chat", None)
            if focus is not None and chat is not None and (
                focus is chat.entry or str(focus) == str(chat.entry)
            ):
                chat_controller = getattr(app, "chat_controller", None)
                if chat_controller is not None:
                    try:
                        chat_controller.handle_send(chat.entry.get())
                    except Exception:
                        pass
                return
        except Exception:
            pass
        self.text_to_diagram()

    def postprocess_chat_result(self) -> None:
        app = self._app
        try:
            buffer = str(getattr(app, "_chat_assistant_buffer", "") or "").strip()
            if not buffer:
                return
            parsed = None
            try:
                from ollama_client import OllamaClient as _OC  # type: ignore

                parsed = _OC.extract_json(buffer)
            except Exception:
                return
            if not isinstance(parsed, dict):
                return
            chat = getattr(app, "chat", None)
            if chat is None:
                return
            try:
                chat.clear_dynamic_actions()
            except Exception:
                pass
            if all(k in parsed for k in ("metadata", "elements", "connections")):
                chat.add_dynamic_button(
                    "Diagramm ersetzen",
                    lambda payload=parsed: self.apply_full_process_json(payload),
                )
                chat.add_dynamic_button(
                    "Diagramm mergen",
                    lambda payload=parsed: self.merge_full_process_json(payload),
                )
            if set(parsed.keys()) <= {"elements", "connections"} and any(
                k in parsed for k in ("elements", "connections")
            ):
                chat.add_dynamic_button(
                    "Patch anwenden",
                    lambda payload=parsed: self.apply_add_only_patch(payload),
                )
            if "issues" in parsed and isinstance(parsed.get("patch"), dict):
                status = getattr(app, "status", None)
                if status is not None:
                    try:
                        issues = parsed.get("issues") or []
                        status.set(f"Diagnose: {len(issues)} Issues gefunden")
                    except Exception:
                        pass
                chat.add_dynamic_button(
                    "Diagnose-Patch anwenden",
                    lambda payload=parsed: self.apply_diagnose_patch(payload),
                )
        except Exception:
            pass

    def apply_full_process_json(self, data: dict) -> None:
        app = self._app
        try:
            if not isinstance(data, dict) or not isinstance(data.get("elements"), list) or not isinstance(
                data.get("connections"), list
            ):
                messagebox.showerror("Übernehmen", "Ungültige Prozess-Struktur (elements/connections fehlen)")
                return
            try:
                ok, err = app._validate_vpb_data_safe(data)
            except Exception:
                ok, err = True, ""
            if not ok:
                messagebox.showerror("Übernehmen", f"Schema-Fehler: {err}")
                return
            canvas = getattr(app, "canvas", None)
            if canvas is None:
                return
            try:
                canvas.push_undo()
                canvas.load_from_dict(data)
                canvas.redraw_all()
            except Exception as exc:
                messagebox.showerror("Übernehmen", f"Fehler: {exc}")
                return
            status = getattr(app, "status", None)
            if status is not None:
                try:
                    status.set("LLM Diagramm übernommen")
                except Exception:
                    pass
            try:
                app._actions.fit_to_diagram()
            except Exception:
                pass
        except Exception as exc:
            messagebox.showerror("Übernehmen", f"Fehler: {exc}")

    def _prepare_merge_payload(self, data: dict) -> tuple[dict, List[str]]:
        if not isinstance(data, dict):
            raise ValueError("Ungültige Struktur")
        elems_raw = data.get("elements") or []
        conns_raw = data.get("connections") or []
        if not isinstance(elems_raw, list) or not isinstance(conns_raw, list):
            raise ValueError("Ungültige Elemente/Verbindungen")
        elems_in = [dict(e) for e in elems_raw if isinstance(e, dict)]
        conns_in = [dict(c) for c in conns_raw if isinstance(c, dict)]
        metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
        hints: List[str] = []
        try:
            from vpb_prompt_core import validate_vpb_json  # type: ignore

            elem_types = set(ELEMENT_STYLES.keys()) if ELEMENT_STYLES else None  # type: ignore
            conn_types = set(CONNECTION_STYLES.keys()) if CONNECTION_STYLES else None  # type: ignore
            raw = json.dumps({'metadata': metadata, 'elements': elems_in, 'connections': conns_in}, ensure_ascii=False)
            vres = validate_vpb_json(
                raw,
                mode="text_to_vpb",
                allow_element_types=elem_types,
                allow_connection_types=conn_types,
                tolerance="lenient",
            )
            if getattr(vres, 'fatal', False):
                errs = [
                    f"- {i.code}: {i.message}"
                    for i in getattr(vres, 'issues', [])
                    if getattr(i, 'severity', '') == 'error'
                ]
                raise ValueError("Fataler Validierungsfehler:\n" + ("\n".join(errs) or "Unbekannt"))
            sanitized = getattr(vres, 'parsed', None)
            if isinstance(sanitized, dict):
                meta_candidate = sanitized.get("metadata")
                if isinstance(meta_candidate, dict):
                    metadata = meta_candidate
                elems_candidate = sanitized.get("elements")
                if isinstance(elems_candidate, list):
                    elems_in = [dict(e) for e in elems_candidate if isinstance(e, dict)]
                conns_candidate = sanitized.get("connections")
                if isinstance(conns_candidate, list):
                    conns_in = [dict(c) for c in conns_candidate if isinstance(c, dict)]
            issue_hints = [
                f"- {i.code}: {i.message}"
                for i in getattr(vres, 'issues', [])
                if getattr(i, 'severity', '') in ("warning", "info")
            ]
            if issue_hints:
                hints.extend(issue_hints)
            repairs = list(getattr(vres, 'repairs', []) or []) if hasattr(vres, 'repairs') else []
            if repairs:
                hints.extend(f"- Reparatur: {r}" for r in repairs)
        except ValueError:
            raise
        except Exception:
            pass

        ok, err = self._app._validate_vpb_data_safe({"elements": elems_in, "connections": conns_in})
        if not ok:
            raise ValueError(f"Schema-Fehler: {err}")

        return {"metadata": metadata, "elements": elems_in, "connections": conns_in}, hints

    def merge_full_process_json(self, data: dict) -> None:
        app = self._app
        try:
            prepared, hints = self._prepare_merge_payload(data)
        except ValueError as exc:
            messagebox.showerror("Merge", str(exc))
            return

        chat_controller = getattr(app, "chat_controller", None)
        if hints and chat_controller is not None:
            chat_controller.append_block("Merge Validierung", hints)

        controller = getattr(app, "_app_controller", None)
        merge_service = getattr(app, "_merge_service", None)
        if controller is None or merge_service is None:
            self._merge_full_process_json_sync(prepared, hints=hints, hints_logged=bool(hints))
            return

        task_controller = getattr(app, "task_controller", None)
        if task_controller is not None and task_controller.has_pending("merge_full"):
            status = getattr(app, "status", None)
            if status is not None:
                status.set("Merge läuft bereits – bitte warten")
            return

        payload = {
            "base": app.canvas.to_dict(),
            "data": prepared,
            "update_mode": getattr(app, "_merge_update_mode", "none"),
            "snap": getattr(app, "_merge_snap_enabled", False),
            "auto_rename": getattr(app, "_auto_rename_enabled", True),
            "conflict_strategy": "duplicate",
        }
        try:
            task_id = controller.submit("merge_full", payload)
        except Exception as exc:
            messagebox.showwarning("Merge", f"Hintergrund-Merge nicht möglich ({exc}). Führe lokalen Merge aus.")
            self._merge_full_process_json_sync(prepared, hints=hints, hints_logged=bool(hints))
            return

        if task_controller is not None:
            task_controller.register_task_start("merge_full", task_id)
        status = getattr(app, "status", None)
        if status is not None:
            status.set("Merge läuft…")

    def _merge_full_process_json_sync(
        self,
        prepared: dict,
        *,
        hints: Optional[List[str]] = None,
        hints_logged: bool = False,
    ) -> None:
        app = self._app
        chat_controller = getattr(app, "chat_controller", None)
        if hints and not hints_logged and chat_controller is not None:
            chat_controller.append_block("Merge Validierung", hints)
        try:
            merge_manager = getattr(app, "_merge_manager", None)
            if not merge_manager:
                merge_manager = MergeManager(app.canvas)
                app._merge_manager = merge_manager
            prev_elements = set(app.canvas.elements.keys())
            prev_connections = set(app.canvas.connections.keys())
            result: MergeResult = merge_manager.merge_full(
                prepared,
                update_mode=getattr(app, "_merge_update_mode", "none"),
                snap=getattr(app, "_merge_snap_enabled", False),
                auto_rename=getattr(app, "_auto_rename_enabled", True),
                grid=50,
                conflict_strategy="duplicate",
            )
            if chat_controller is not None:
                chat_controller.append_merge_feedback(
                    "Merge Ergebnis",
                    {
                        "added_elements": result.added_elements,
                        "added_connections": result.added_connections,
                        "element_renames": result.element_renames,
                        "connection_renames": result.connection_renames,
                        "summary_lines": result.summary_lines(),
                        "warnings": getattr(result, "warnings", []),
                    },
                )
            if getattr(result, "warnings", None):
                try:
                    messagebox.showwarning("Merge", "\n".join(str(w) for w in result.warnings))
                except Exception:
                    pass
            status = getattr(app, "status", None)
            if status is not None:
                status.set(f"Merge abgeschlossen (+{result.added_elements}/+{result.added_connections})")
            app._highlight_merge_changes(
                prev_elements,
                prev_connections,
                element_renames=result.element_renames.values(),
                connection_renames=result.connection_renames.values(),
            )
        except ValueError as exc:
            messagebox.showwarning("Merge", str(exc))
        except Exception as exc:
            messagebox.showerror("Merge", f"Fehler: {exc}")

    def _prepare_patch_payload(self, patch: dict) -> tuple[dict, List[str]]:
        if not isinstance(patch, dict):
            raise ValueError("Patch fehlt oder ist ungültig")
        elements_raw = patch.get("elements") or []
        connections_raw = patch.get("connections") or []
        if not elements_raw and not connections_raw:
            raise ValueError("Patch leer – nichts zu tun.")
        if not isinstance(elements_raw, list) or not isinstance(connections_raw, list):
            raise ValueError("Ungültige Patch-Struktur")

        elements = [dict(e) for e in elements_raw if isinstance(e, dict)]
        connections = [dict(c) for c in connections_raw if isinstance(c, dict)]

        warnings: List[str] = []
        try:
            from vpb_prompt_core import validate_vpb_json  # type: ignore

            canvas = getattr(self._app, "canvas", None)
            existing_ids = set(canvas.elements.keys()) | set(canvas.connections.keys()) if canvas else set()
            elem_types = set(ELEMENT_STYLES.keys()) if ELEMENT_STYLES else None  # type: ignore
            conn_types = set(CONNECTION_STYLES.keys()) if CONNECTION_STYLES else None  # type: ignore
            raw = json.dumps({"elements": elements, "connections": connections}, ensure_ascii=False)
            vres = validate_vpb_json(
                raw,
                mode="next_steps",
                existing_ids=existing_ids,
                allow_element_types=elem_types,
                allow_connection_types=conn_types,
                tolerance="lenient",
            )
            if getattr(vres, 'fatal', False):
                errs = [
                    f"- {i.code}: {i.message}"
                    for i in getattr(vres, 'issues', [])
                    if getattr(i, 'severity', '') == 'error'
                ]
                raise ValueError("Fataler Validierungsfehler:\n" + ("\n".join(errs) or "Unbekannt"))
            sanitized = getattr(vres, 'parsed', None)
            if isinstance(sanitized, dict):
                elems_candidate = sanitized.get("elements")
                if isinstance(elems_candidate, list):
                    elements = [dict(e) for e in elems_candidate if isinstance(e, dict)]
                conns_candidate = sanitized.get("connections")
                if isinstance(conns_candidate, list):
                    connections = [dict(c) for c in conns_candidate if isinstance(c, dict)]
            issue_warns = [
                f"- {i.code}: {i.message}"
                for i in getattr(vres, 'issues', [])
                if getattr(i, 'severity', '') in ("warning", "info")
            ]
            if issue_warns:
                warnings.extend(issue_warns)
            repairs = list(getattr(vres, 'repairs', []) or []) if hasattr(vres, 'repairs') else []
            if repairs:
                warnings.extend(f"- Reparatur: {r}" for r in repairs)
        except ValueError:
            raise
        except Exception:
            pass

        return {"elements": elements, "connections": connections}, warnings

    def apply_add_only_patch(self, patch: dict) -> None:
        try:
            prepared, warns = self._prepare_patch_payload(patch)
        except ValueError as exc:
            msg = str(exc)
            if "leer" in msg.lower():
                messagebox.showinfo("Patch", msg)
            else:
                messagebox.showerror("Patch", msg)
            return

        app = self._app
        chat_controller = getattr(app, "chat_controller", None)
        if warns and chat_controller is not None:
            chat_controller.append_block("Patch Validierung", warns)
            status = getattr(app, "status", None)
            if status is not None:
                status.set("Patch: Hinweise vorhanden")

        controller = getattr(app, "_app_controller", None)
        merge_service = getattr(app, "_merge_service", None)
        if controller is None or merge_service is None:
            self._apply_add_only_patch_sync(prepared, warns, warnings_logged=bool(warns))
            return

        task_controller = getattr(app, "task_controller", None)
        if task_controller is not None and task_controller.has_pending("patch_add_only"):
            status = getattr(app, "status", None)
            if status is not None:
                status.set("Patch läuft bereits – bitte warten")
            return

        payload = {
            "base": app.canvas.to_dict(),
            "patch": prepared,
            "auto_rename": getattr(app, "_auto_rename_enabled", True),
        }
        try:
            task_id = controller.submit("patch_add_only", payload)
        except Exception as exc:
            messagebox.showwarning("Patch", f"Hintergrund-Patch nicht möglich ({exc}). Führe lokalen Patch aus.")
            self._apply_add_only_patch_sync(prepared, warns, warnings_logged=bool(warns))
            return

        if task_controller is not None:
            task_controller.register_task_start("patch_add_only", task_id)
        status = getattr(app, "status", None)
        if status is not None:
            status.set("Patch läuft…")

    def _apply_add_only_patch_sync(
        self,
        prepared: dict,
        warnings: Optional[List[str]] = None,
        warnings_logged: bool = False,
    ) -> None:
        app = self._app
        chat_controller = getattr(app, "chat_controller", None)
        if warnings and not warnings_logged and chat_controller is not None:
            chat_controller.append_block("Patch Validierung", warnings)
        try:
            merge_manager = getattr(app, "_merge_manager", None)
            if not merge_manager:
                merge_manager = MergeManager(app.canvas)
                app._merge_manager = merge_manager
            prev_elements = set(app.canvas.elements.keys())
            prev_connections = set(app.canvas.connections.keys())
            result: MergeResult = merge_manager.apply_add_only_patch(
                prepared,
                auto_rename=getattr(app, "_auto_rename_enabled", True),
            )
            if chat_controller is not None:
                chat_controller.append_merge_feedback(
                    "Patch Ergebnis",
                    {
                        "added_elements": result.added_elements,
                        "added_connections": result.added_connections,
                        "element_renames": result.element_renames,
                        "connection_renames": result.connection_renames,
                        "summary_lines": result.summary_lines(),
                        "warnings": getattr(result, "warnings", []),
                    },
                )
            if getattr(result, "warnings", None):
                try:
                    messagebox.showwarning("Patch", "\n".join(str(w) for w in result.warnings))
                except Exception:
                    pass
            status = getattr(app, "status", None)
            if status is not None:
                status.set(f"Patch angewendet (+{result.added_elements}/+{result.added_connections})")
            app._highlight_merge_changes(
                prev_elements,
                prev_connections,
                element_renames=result.element_renames.values(),
                connection_renames=result.connection_renames.values(),
            )
        except ValueError as exc:
            messagebox.showwarning("Patch", str(exc))
        except Exception as exc:
            messagebox.showerror("Patch", f"Fehler: {exc}")

    def apply_diagnose_patch(self, diag: dict) -> None:
        app = self._app
        try:
            patch = diag.get("patch") or {}
            if not isinstance(patch, dict):
                messagebox.showerror("Diagnose", "Patch fehlt oder ist ungültig")
                return
            try:
                from vpb_prompt_core import validate_vpb_json  # type: ignore

                canvas = getattr(app, "canvas", None)
                existing_ids = set(canvas.elements.keys()) | set(canvas.connections.keys()) if canvas else set()
                try:
                    elem_types = set(ELEMENT_STYLES.keys())  # type: ignore
                except Exception:
                    elem_types = None
                try:
                    conn_types = set(CONNECTION_STYLES.keys())  # type: ignore
                except Exception:
                    conn_types = None
                raw = json.dumps({"issues": diag.get("issues") or [], "patch": patch}, ensure_ascii=False)
                vres = validate_vpb_json(
                    raw,
                    mode="diagnose_fix",
                    existing_ids=existing_ids,
                    allow_element_types=elem_types,
                    allow_connection_types=conn_types,
                    tolerance="lenient",
                )
                if getattr(vres, 'fatal', False):
                    errs = [
                        f"- {i.code}: {i.message}"
                        for i in getattr(vres, 'issues', [])
                        if getattr(i, 'severity', '') == 'error'
                    ]
                    messagebox.showerror(
                        "Diagnose – Validierung",
                        "Fataler Validierungsfehler:\n" + ("\n".join(errs) or "Unbekannt"),
                    )
                    return
                sanitized = getattr(vres, 'parsed', None)
                if isinstance(sanitized, dict):
                    patch_candidate = sanitized.get("patch")
                    if isinstance(patch_candidate, dict):
                        patch = patch_candidate
                warns = [
                    f"- {i.code}: {i.message}"
                    for i in getattr(vres, 'issues', [])
                    if getattr(i, 'severity', '') in ("warning", "info")
                ]
                repairs = list(getattr(vres, 'repairs', []) or []) if hasattr(vres, 'repairs') else []
                if repairs:
                    warns.extend(f"- Reparatur: {r}" for r in repairs)
                if warns:
                    chat = getattr(app, "chat", None)
                    if chat is not None:
                        try:
                            chat.append_assistant("\n[Diagnose Validierung]\n" + "\n".join(warns))
                        except Exception:
                            pass
                    status = getattr(app, "status", None)
                    if status is not None:
                        status.set("Diagnose: Hinweise vorhanden")
            except Exception:
                pass
            self.apply_add_only_patch(patch)
            issues = diag.get("issues") or []
            if issues:
                chat = getattr(app, "chat", None)
                if chat is not None:
                    try:
                        lines = [
                            f"Issue {i.get('id')}: {i.get('severity')} – {i.get('message')}"
                            for i in issues
                            if isinstance(i, dict)
                        ]
                        chat.append_assistant("\n[Diagnose Zusammenfassung]\n" + "\n".join(lines))
                    except Exception:
                        pass
        except Exception as exc:
            messagebox.showerror("Diagnose", f"Fehler: {exc}")

    def text_to_diagram(self) -> None:
        app = self._app
        try:
            from vpb_ai_logic import build_prompt_with_examples_text_to_vpb  # type: ignore
            from vpb_schema import validate_vpb_dict  # type: ignore
        except Exception as exc:
            messagebox.showerror("AI", f"Fehlende Module: {exc}")
            return
        if OllamaClient is None:
            messagebox.showwarning("AI", "Ollama-Client nicht verfügbar.")
            return

        T = tk.Toplevel(app)
        T.title("Text → Diagramm")
        tk.Label(T, text="Kurzbeschreibung des Prozesses:").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        txt = tk.Text(T, width=60, height=10)
        txt.grid(row=1, column=0, padx=6, pady=6, sticky="we")
        optf = tk.Frame(T)
        optf.grid(row=2, column=0, padx=6, pady=(0, 6), sticky="we")
        tk.Label(optf, text="Beispiel-Tags (optional, komma-getrennt):").grid(row=0, column=0, sticky="w")
        tags_var = tk.StringVar(value="")
        tk.Entry(optf, textvariable=tags_var, width=36).grid(row=0, column=1, padx=(6, 0), sticky="w")
        tk.Label(optf, text="Anzahl Beispiele:").grid(row=0, column=2, padx=(12, 0), sticky="e")
        max_var = tk.StringVar(value="3")
        tk.Spinbox(optf, from_=0, to=5, textvariable=max_var, width=4).grid(row=0, column=3, padx=(6, 0), sticky="w")
        info = tk.Label(T, text="Das Modell wird lokal via Ollama generiert.", fg="#666")
        info.grid(row=3, column=0, padx=6, pady=(0, 6), sticky="w")

        def run():
            desc = txt.get("1.0", tk.END).strip()
            if not desc:
                messagebox.showinfo("AI", "Bitte eine Beschreibung eingeben.")
                return
            element_types = list(ELEMENT_STYLES.keys())
            connection_types = list(CONNECTION_STYLES.keys())
            try:
                ex_count = max(0, min(5, int(max_var.get().strip() or "0")))
            except Exception:
                ex_count = 3
            raw_tags = [t.strip() for t in tags_var.get().split(",") if t.strip()]
            prompt = build_prompt_with_examples_text_to_vpb(
                desc,
                element_types,
                connection_types,
                example_tags=raw_tags,
                max_examples=ex_count,
            )
            client = OllamaClient(endpoint=getattr(app, "_ollama_endpoint", ""), model=getattr(app, "_ollama_model", ""))

            PD = tk.Toplevel(T)
            PD.title("Erzeuge Diagramm…")
            tk.Label(PD, text="LLM läuft…").pack(padx=10, pady=(10, 4))
            ptxt = tk.Text(PD, width=60, height=4)
            ptxt.pack(padx=10, pady=4)
            ptxt.insert("1.0", prompt[:2000])
            ptxt.configure(state="disabled")
            btnf = tk.Frame(PD)
            btnf.pack(fill=tk.X, padx=10, pady=(4, 10))
            cancelled = {"v": False}

            def do_cancel():
                cancelled["v"] = True
                if job and hasattr(job, "cancel"):
                    job.cancel()

            tk.Button(btnf, text="Abbrechen", command=do_cancel).pack(side=tk.RIGHT)

            def target():
                options = (
                    OllamaOptions(
                        temperature=getattr(app, "_ollama_temperature", 0.2),
                        num_predict=getattr(app, "_ollama_num_predict", 600),
                    )
                    if OllamaOptions
                    else None
                )
                return client.generate_json(
                    prompt,
                    options=options,
                    retries=1,
                    validate=lambda d: validate_vpb_dict(d, element_types, connection_types),
                )

            job = OllamaJob(target).start() if OllamaJob else None

            def poll():
                if cancelled["v"]:
                    try:
                        PD.destroy()
                    except Exception:
                        pass
                    return
                if not job:
                    try:
                        data = target()
                    except Exception as exc:
                        PD.destroy()
                        messagebox.showerror("AI", f"Fehler: {exc}")
                        return
                    _apply_result(data)
                    try:
                        PD.destroy()
                    except Exception:
                        pass
                    return
                chunk = job.get_nowait()
                if chunk is None:
                    if not job.is_done():
                        app.after(150, poll)
                        return
                    try:
                        chunk = job.get(timeout=0.1)
                    except Exception:
                        chunk = None
                if isinstance(chunk, Exception):
                    try:
                        PD.destroy()
                    except Exception:
                        pass
                    messagebox.showerror("AI", f"Fehler: {chunk}")
                    return
                if chunk is not None:
                    try:
                        PD.destroy()
                    except Exception:
                        pass
                    _apply_result(chunk)
                    return
                app.after(150, poll)

            def _apply_result(data):
                try:
                    canvas = getattr(app, "canvas", None)
                    if canvas is None:
                        return
                    canvas.push_undo()
                    canvas.load_from_dict(data)
                    canvas.redraw_all()
                    status = getattr(app, "status", None)
                    if status is not None:
                        status.set("AI: Diagramm erzeugt")
                    app._actions.fit_to_diagram()
                    T.destroy()
                except Exception as exc:
                    messagebox.showerror("AI", f"Fehler beim Anwenden: {exc}")

            poll()

        btns = tk.Frame(T)
        btns.grid(row=3, column=0, padx=6, pady=8, sticky="e")
        tk.Button(btns, text="Erzeugen", command=run).pack(side=tk.LEFT, padx=4)
        tk.Button(btns, text="Abbrechen", command=T.destroy).pack(side=tk.LEFT, padx=4)
        T.grab_set()
        T.transient(app)

    def suggest_next_step(self) -> None:
        app = self._app
        try:
            from vpb_ai_logic import build_prompt_with_examples_next_steps  # type: ignore
            from vpb_diff import validate_add_only_diff  # type: ignore
        except Exception as exc:
            messagebox.showerror("AI", f"Fehlende Module: {exc}")
            return
        if OllamaClient is None:
            messagebox.showwarning("AI", "Ollama-Client nicht verfügbar.")
            return

        current = app.canvas.to_dict()
        element_types = list(ELEMENT_STYLES.keys())
        connection_types = list(CONNECTION_STYLES.keys())
        selected = getattr(app.canvas, "selected_id", None)

        T = tk.Toplevel(app)
        T.title("Nächster Schritt vorschlagen…")
        tk.Label(T, text="Beispiel-Tags (optional, komma-getrennt):").grid(row=0, column=0, padx=6, pady=(8, 2), sticky="w")
        tags_var = tk.StringVar(value="")
        tk.Entry(T, textvariable=tags_var, width=46).grid(row=0, column=1, padx=6, pady=(8, 2), sticky="w")
        tk.Label(T, text="Anzahl Beispiele:").grid(row=1, column=0, padx=6, pady=2, sticky="e")
        max_var = tk.StringVar(value="3")
        tk.Spinbox(T, from_=0, to=5, textvariable=max_var, width=6).grid(row=1, column=1, padx=6, pady=2, sticky="w")

        def run():
            try:
                ex_count = max(0, min(5, int(max_var.get().strip() or "0")))
            except Exception:
                ex_count = 3
            raw_tags = [t.strip() for t in tags_var.get().split(",") if t.strip()]
            prompt = build_prompt_with_examples_next_steps(
                json.dumps(current, ensure_ascii=False, indent=2),
                element_types,
                connection_types,
                selected_id=selected,
                example_tags=raw_tags,
                max_examples=ex_count,
            )
            client = OllamaClient(endpoint=getattr(app, "_ollama_endpoint", ""), model=getattr(app, "_ollama_model", ""))

            PD = tk.Toplevel(T)
            PD.title("Schlage nächsten Schritt vor…")
            tk.Label(PD, text="LLM läuft…").pack(padx=10, pady=(10, 4))
            ptxt = tk.Text(PD, width=60, height=4)
            ptxt.pack(padx=10, pady=4)
            ptxt.insert("1.0", prompt[:2000])
            ptxt.configure(state="disabled")
            btnf = tk.Frame(PD)
            btnf.pack(fill=tk.X, padx=10, pady=(4, 10))
            cancelled = {"v": False}

            def do_cancel():
                cancelled["v"] = True
                if job and hasattr(job, "cancel"):
                    job.cancel()

            tk.Button(btnf, text="Abbrechen", command=do_cancel).pack(side=tk.RIGHT)

            options = (
                OllamaOptions(
                    temperature=getattr(app, "_ollama_temperature", 0.2),
                    num_predict=getattr(app, "_ollama_num_predict", 600),
                )
                if OllamaOptions
                else None
            )

            def target():
                return client.generate_json(
                    prompt,
                    options=options,
                    retries=1,
                )

            job = OllamaJob(target).start() if OllamaJob else None

            def poll():
                if cancelled["v"]:
                    try:
                        PD.destroy()
                    except Exception:
                        pass
                    return
                if not job:
                    try:
                        data = target()
                    except Exception as exc:
                        PD.destroy()
                        messagebox.showerror("AI", f"Fehler: {exc}")
                        return
                    _apply_result(data)
                    try:
                        PD.destroy()
                    except Exception:
                        pass
                    return
                chunk = job.get_nowait()
                if chunk is None:
                    if not job.is_done():
                        app.after(150, poll)
                        return
                    try:
                        chunk = job.get(timeout=0.1)
                    except Exception:
                        chunk = None
                if isinstance(chunk, Exception):
                    try:
                        PD.destroy()
                    except Exception:
                        pass
                    messagebox.showerror("AI", f"Fehler: {chunk}")
                    return
                if chunk is not None:
                    try:
                        PD.destroy()
                    except Exception:
                        pass
                    _apply_result(chunk)
                    return
                app.after(150, poll)

            def _apply_result(data):
                try:
                    if not isinstance(data, dict):
                        raise ValueError("Antwort enthält kein JSON")
                    if not data.get("elements") and not data.get("connections"):
                        messagebox.showinfo("AI", "Keine Änderungen vorgeschlagen.")
                        return
                    validate_add_only_diff(data)
                except Exception as exc:
                    messagebox.showerror("AI", f"Ungültiger Vorschlag: {exc}")
                    return
                chat_controller = getattr(app, "chat_controller", None)
                if chat_controller is not None:
                    chat_controller.append_block("AI Vorschlag", [
                        "Vorgeschlagener Patch:",
                        json.dumps(data, ensure_ascii=False, indent=2),
                    ])
                self.apply_add_only_patch(data)

            poll()

        btns = tk.Frame(T)
        btns.grid(row=2, column=0, padx=6, pady=8, sticky="e")
        tk.Button(btns, text="Vorschlagen", command=run).pack(side=tk.LEFT, padx=4)
        tk.Button(btns, text="Abbrechen", command=T.destroy).pack(side=tk.LEFT, padx=4)
        T.grab_set()
        T.transient(app)


__all__ = ["AppChatIntegration"]
