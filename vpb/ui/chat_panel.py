from __future__ import annotations

import os
from typing import Any, Callable, Dict, Optional

import tkinter as tk
from tkinter import filedialog, messagebox


class ChatPanel(tk.Frame):
    """Einfache Chat-Seitenleiste mit Verlauf, Eingabe, Senden/Stop."""

    def __init__(
        self,
        master,
        on_send: Optional[Callable[[str], None]] = None,
        on_stop: Optional[Callable[[], None]] = None,
        on_attach: Optional[Callable[[str, str, bool], None]] = None,
    ):
        super().__init__(master, bg="#ffffff")
        self._on_send = on_send
        self._on_stop = on_stop
        self._on_attach = on_attach
        self._busy = False
        self._active_assistant_start = None
        self._active_assistant_end = None

        base_bg = "#ffffff"
        surface_bg = "#f5f5f5"
        console_bg = "#ffffff"
        accent_primary = "#2563eb"
        accent_stop = "#dc2626"
        text_fg = "#111111"
        subtle_fg = "#4b5563"
        input_bg = "#ffffff"

        self.configure(bg=base_bg)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._last_attachment_dir: Optional[str] = None

        # Toolbar für Schnellzugriffe
        toolbar = tk.Frame(self, bg=surface_bg, highlightbackground="#d1d5db", highlightthickness=1)
        toolbar.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 6))
        btn_explain = tk.Button(
            toolbar,
            text="Erklären",
            command=lambda: self._send_text("Erkläre das aktuelle Diagramm kurz und prägnant."),
            bg=surface_bg,
            fg=text_fg,
            activebackground="#e5e7eb",
            activeforeground=text_fg,
            relief=tk.FLAT,
            padx=8,
        )
        btn_explain.pack(side=tk.LEFT, padx=4, pady=4)
        btn_improve = tk.Button(
            toolbar,
            text="Verbessern",
            command=lambda: self._send_text("Schlage konkrete Verbesserungen für das aktuelle Diagramm vor (klar, stichpunktartig)."),
            bg=surface_bg,
            fg=text_fg,
            activebackground="#e5e7eb",
            activeforeground=text_fg,
            relief=tk.FLAT,
            padx=8,
        )
        btn_improve.pack(side=tk.LEFT, padx=4, pady=4)
        btn_draft = tk.Button(
            toolbar,
            text="Entwurf",
            command=lambda: self._send_text("Erzeuge einen kurzen Textentwurf für den nächsten Prozessschritt."),
            bg=surface_bg,
            fg=text_fg,
            activebackground="#e5e7eb",
            activeforeground=text_fg,
            relief=tk.FLAT,
            padx=8,
        )
        btn_draft.pack(side=tk.LEFT, padx=4, pady=4)
        btn_attach = tk.Button(
            toolbar,
            text="Dokument senden",
            command=self._handle_attach,
            bg=surface_bg,
            fg=text_fg,
            activebackground="#e5e7eb",
            activeforeground=text_fg,
            relief=tk.FLAT,
            padx=8,
        )
        btn_attach.pack(side=tk.LEFT, padx=4, pady=4)

        # Verlauf
        top = tk.Frame(self, bg=base_bg)
        top.grid(row=1, column=0, sticky="nsew", padx=0, pady=(0, 6))
        top.grid_rowconfigure(0, weight=1)
        top.grid_columnconfigure(0, weight=1)
        self.txt = tk.Text(
            top,
            wrap="word",
            state="disabled",
            bg=console_bg,
            fg=text_fg,
            insertbackground=text_fg,
            relief=tk.FLAT,
            font=("Cascadia Mono", 10),
        )
        ysb = tk.Scrollbar(top, orient=tk.VERTICAL, command=self.txt.yview)
        self.txt.configure(yscrollcommand=ysb.set)
        self.txt.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")

        # Text-Tag-Styling für Rich-Content
        self.txt.tag_configure("user_label", font=("Segoe UI", 9, "bold"), foreground="#1d4ed8")
        self.txt.tag_configure("assistant_label", font=("Segoe UI", 9, "bold"), foreground="#047857")
        self.txt.tag_configure("assistant_body", foreground=text_fg)
        self.txt.tag_configure("user_body", foreground=text_fg)
        self.txt.tag_configure("assistant_code", font=("Cascadia Mono", 10), background="#eef2ff")
        self.txt.tag_configure("assistant_code_fence", font=("Cascadia Mono", 10, "bold"), foreground="#6366f1")
        self.txt.tag_configure("assistant_diff_add", foreground="#166534")
        self.txt.tag_configure("assistant_diff_del", foreground="#b91c1c")
        self.txt.tag_configure("assistant_diff_header", foreground="#0f172a", font=("Cascadia Mono", 10, "bold"))

        # Dynamischer Aktionsbereich für kontextuelle Buttons (z.B. JSON anwenden)
        self.dynamic_actions = tk.Frame(self, bg=base_bg)
        self.dynamic_actions.grid(row=2, column=0, sticky="ew", padx=0, pady=(0, 6))

        self._progress_var = tk.StringVar(value="")
        self.progress_label = tk.Label(self, textvariable=self._progress_var, anchor="w", bg=base_bg, fg=subtle_fg)
        self.progress_label.grid(row=3, column=0, sticky="ew", padx=6, pady=(0, 4))

        # Eingabe
        bottom = tk.Frame(self, bg=surface_bg)
        bottom.grid(row=4, column=0, sticky="ew", padx=0, pady=(0, 6))
        bottom.grid_columnconfigure(0, weight=1)
        self.entry = tk.Entry(bottom, bg=input_bg, fg=text_fg, insertbackground=text_fg, relief=tk.FLAT)
        self.entry.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        self.entry.bind("<Return>", lambda e: self.trigger_send())

        self.btn_send = tk.Button(
            bottom,
            text="Senden",
            command=self.trigger_send,
            bg=accent_primary,
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=10,
        )
        self.btn_send.grid(row=0, column=1, padx=(0, 6), pady=6)
        self.btn_stop = tk.Button(
            bottom,
            text="Stop",
            command=(self._on_stop or (lambda: None)),
            bg=accent_stop,
            fg="#ffffff",
            activebackground="#b91c1c",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=10,
        )
        self.btn_stop.grid(row=0, column=2, padx=(0, 6), pady=6)

        # Initialer Button-Zustand
        self.set_busy(False)

    def clear_dynamic_actions(self):
        try:
            for w in list(self.dynamic_actions.winfo_children()):
                w.destroy()
        except Exception:
            pass

    def reset_conversation(self):
        """Setzt den gesamten Chat-Verlauf und UI-Zustand zurück."""
        try:
            self.txt.configure(state="normal")
            self.txt.delete("1.0", tk.END)
            self.txt.configure(state="disabled")
        except Exception:
            pass
        self.clear_dynamic_actions()
        try:
            self._progress_var.set("")
        except Exception:
            pass
        try:
            self.set_busy(False)
        except Exception:
            pass
        try:
            self.entry.delete(0, tk.END)
        except Exception:
            pass
        self._active_assistant_start = None
        self._active_assistant_end = None

    def add_dynamic_button(self, label: str, command: Callable[[], None]):
        try:
            b = tk.Button(
                self.dynamic_actions,
                text=label,
                command=command,
                bg="#e5e7eb",
                fg="#111111",
                activebackground="#d1d5db",
                activeforeground="#111111",
                relief=tk.FLAT,
                padx=8,
            )
            b.pack(side=tk.LEFT, padx=4, pady=4)
            return b
        except Exception:
            return None

    def _send_text(self, text: str):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, text)
        self.trigger_send()

    def trigger_send(self):
        txt = self.entry.get().strip()
        if not txt:
            return
        if self._on_send:
            self._on_send(txt)
        # Eingabe leeren
        self.entry.delete(0, tk.END)

    def focus_input(self):
        try:
            self.entry.focus_set()
        except Exception:
            pass

    def _append(self, prefix: str, text: str, prefix_tag: Optional[str] = None, body_tag: Optional[str] = None):
        self.txt.configure(state="normal")
        if prefix:
            self.txt.insert(tk.END, prefix, prefix_tag)
        if text:
            self.txt.insert(tk.END, text, body_tag)
        self.txt.insert(tk.END, "\n")
        self.txt.see(tk.END)
        self.txt.configure(state="disabled")

    def add_user(self, text: str):
        self._append("Du: ", text, "user_label", "user_body")

    def start_assistant(self):
        # Start einer neuen AI-Antwortzeile ohne Zeilenumbruch
        self.txt.configure(state="normal")
        self.txt.insert(tk.END, "AI: ", "assistant_label")
        self._active_assistant_start = self.txt.index(tk.END)
        self._active_assistant_end = self._active_assistant_start
        self.txt.configure(state="disabled")
        self.txt.see(tk.END)

    def append_assistant(self, chunk: str):
        self.txt.configure(state="normal")
        self.txt.insert(tk.END, chunk, "assistant_body")
        self._active_assistant_end = self.txt.index(tk.END)
        self.txt.see(tk.END)
        self.txt.configure(state="disabled")

    def finalize_assistant_message(
        self,
        structured: Optional[Dict[str, Any]] = None,
        callbacks: Optional[Dict[str, Callable[[], None]]] = None,
    ) -> None:
        if not self._active_assistant_start:
            return
        try:
            self.txt.configure(state="normal")
        except Exception:
            pass
        try:
            start_idx = self._active_assistant_start
            end_idx = self._active_assistant_end or self.txt.index(tk.END)
            content = self.txt.get(start_idx, end_idx)
        except Exception:
            self._active_assistant_start = None
            self._active_assistant_end = None
            try:
                self.txt.configure(state="disabled")
            except Exception:
                pass
            return
        try:
            self._apply_markdown_highlighting(start_idx, content)
            if not content.endswith("\n"):
                self.txt.insert(tk.END, "\n")
        except Exception:
            pass
        finally:
            try:
                self.txt.configure(state="disabled")
            except Exception:
                pass
            self._active_assistant_start = None
            self._active_assistant_end = None

        if structured:
            try:
                self._render_structured_blocks(structured, callbacks or {})
            except Exception:
                pass

    # ---- Richtext Helpers -----------------------------------------
    def _apply_markdown_highlighting(self, base_index: str, content: str) -> None:
        offset = 0
        in_code = False
        code_body_start = 0
        code_lang = ""
        lines = content.splitlines(True) or []
        for line in lines:
            line_len = len(line)
            fence = line.strip()
            if fence.startswith("```"):
                fence_start = f"{base_index}+{offset}c"
                fence_end = f"{base_index}+{offset + line_len}c"
                self.txt.tag_add("assistant_code_fence", fence_start, fence_end)
                lang = fence.strip("`").strip().lower()
                if in_code:
                    code_end = f"{base_index}+{offset}c"
                    self.txt.tag_add("assistant_code", f"{base_index}+{code_body_start}c", code_end)
                    if code_lang in ("diff", "patch"):
                        self._highlight_diff_lines(f"{base_index}+{code_body_start}c", code_end)
                    in_code = False
                    code_lang = ""
                else:
                    in_code = True
                    code_body_start = offset + line_len
                    code_lang = lang or code_lang
                offset += line_len
                continue

            if in_code and code_lang in ("diff", "patch"):
                line_start = f"{base_index}+{offset}c"
                line_end = f"{base_index}+{offset + line_len}c"
                stripped = line.lstrip()
                if line.startswith("+") and not line.startswith("+++"):
                    self.txt.tag_add("assistant_diff_add", line_start, line_end)
                elif line.startswith("-") and not line.startswith("---"):
                    self.txt.tag_add("assistant_diff_del", line_start, line_end)
                elif line.startswith("@@") or line.startswith("diff ") or line.startswith("index ") or line.startswith("---") or line.startswith("+++"):
                    self.txt.tag_add("assistant_diff_header", line_start, line_end)
            offset += line_len

        if in_code:
            end_offset = len(content)
            code_end = f"{base_index}+{end_offset}c"
            self.txt.tag_add("assistant_code", f"{base_index}+{code_body_start}c", code_end)
            if code_lang in ("diff", "patch"):
                self._highlight_diff_lines(f"{base_index}+{code_body_start}c", code_end)

    def _highlight_diff_lines(self, start_idx: str, end_idx: str) -> None:
        try:
            current = self.txt.get(start_idx, end_idx)
        except Exception:
            return
        offset = 0
        for line in current.splitlines(True):
            line_len = len(line)
            segment_start = f"{start_idx}+{offset}c"
            segment_end = f"{start_idx}+{offset + line_len}c"
            if line.startswith("+") and not line.startswith("+++"):
                self.txt.tag_add("assistant_diff_add", segment_start, segment_end)
            elif line.startswith("-") and not line.startswith("---"):
                self.txt.tag_add("assistant_diff_del", segment_start, segment_end)
            elif line.startswith("@@") or line.startswith("diff ") or line.startswith("index ") or line.startswith("---") or line.startswith("+++"):
                self.txt.tag_add("assistant_diff_header", segment_start, segment_end)
            offset += line_len

    def _render_structured_blocks(self, payload: Dict[str, Any], callbacks: Dict[str, Callable[[], None]]) -> None:
        if not isinstance(payload, dict):
            return
        try:
            self.txt.configure(state="normal")
        except Exception:
            return

        def _norm_content(value: Any) -> Optional[str]:
            if value is None:
                return None
            if isinstance(value, str):
                return value.strip("\n")
            try:
                import json as _json
                return _json.dumps(value, ensure_ascii=False, indent=2)
            except Exception:
                return str(value)

        handled = False
        diff_content = _norm_content(payload.get("diff"))
        if diff_content:
            self._insert_rich_block(
                "Diff-Vorschlag",
                diff_content,
                callbacks.get("apply_patch") or callbacks.get("apply_diff"),
            )
            handled = True

        patch_content = _norm_content(payload.get("patch"))
        if patch_content:
            self._insert_rich_block(
                "Patch",
                patch_content,
                callbacks.get("apply_patch"),
            )
            handled = True

        code_keys = ["code", "script", "python", "sql", "json"]
        for key in code_keys:
            code_content = _norm_content(payload.get(key))
            if code_content:
                self._insert_rich_block(f"Code ({key})", code_content, callbacks.get("apply_code"))
                handled = True

        if (
            not handled
            and payload
            and not all(k in payload for k in ("metadata", "elements", "connections"))
        ):
            summary = _norm_content(payload)
            if summary and len(summary) <= 4000:
                self._insert_rich_block("LLM Ergebnis", summary, callbacks.get("apply_patch"))

        try:
            self.txt.configure(state="disabled")
        except Exception:
            pass

    def _insert_rich_block(
        self,
        title: str,
        content: str,
        on_apply: Optional[Callable[[], None]] = None,
    ) -> None:
        if not content:
            return
        frame = tk.Frame(self.txt, bg="#f8fafc", highlightbackground="#cbd5f5", highlightthickness=1, bd=0)
        header = tk.Frame(frame, bg="#f8fafc")
        header.pack(fill=tk.X, padx=8, pady=(8, 0))
        tk.Label(header, text=title, font=("Segoe UI", 10, "bold"), bg="#f8fafc", anchor="w").pack(side=tk.LEFT)
        if callable(on_apply):
            tk.Button(
                header,
                text="Auf Canvas anwenden",
                command=on_apply,
                bg="#2563eb",
                fg="#ffffff",
                activebackground="#1d4ed8",
                activeforeground="#ffffff",
                relief=tk.FLAT,
                padx=10,
                pady=2,
            ).pack(side=tk.RIGHT)

        body = tk.Text(
            frame,
            wrap="none",
            height=min(18, max(3, content.count("\n") + 1)),
            font=("Cascadia Mono", 10),
            bg="#f1f5f9",
            fg="#1f2937",
            relief=tk.FLAT,
        )
        body.insert("1.0", content)
        body.configure(state="disabled", cursor="arrow")
        body.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 8))

        self.txt.window_create(tk.END, window=frame, padx=4, pady=6)
        self.txt.insert(tk.END, "\n")

    def set_busy(self, busy: bool):
        try:
            self.btn_send.configure(state=("disabled" if busy else "normal"))
            self.btn_stop.configure(state=("normal" if busy else "disabled"))
            if busy:
                self.entry.configure(state="disabled")
            else:
                self.entry.configure(state="normal")
            self._busy = bool(busy)
        except Exception:
            pass

    def is_busy(self) -> bool:
        return bool(getattr(self, "_busy", False))

    def set_progress(self, message: Optional[str], fraction: Optional[float] = None):
        try:
            if not message:
                self._progress_var.set("")
                return
            if fraction is not None:
                try:
                    pct = int(max(0.0, min(1.0, float(fraction))) * 100)
                    self._progress_var.set(f"{message} ({pct}%)")
                except Exception:
                    self._progress_var.set(message)
            else:
                self._progress_var.set(message)
        except Exception:
            pass

    def _handle_attach(self):
        path = filedialog.askopenfilename(
            title="Prozessdokument auswählen",
            filetypes=(
                ("Prozessdokumente", "*.txt *.md *.markdown *.json *.vpb.json"),
                ("Alle Dateien", "*.*"),
            ),
            initialdir=self._last_attachment_dir or os.getcwd(),
        )
        if not path:
            return
        try:
            self._last_attachment_dir = os.path.dirname(path) or self._last_attachment_dir
        except Exception:
            pass
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(path, "r", encoding="latin-1") as f:
                    content = f.read()
            except Exception as exc:
                messagebox.showerror("Dokument senden", f"Dokument konnte nicht gelesen werden:\n{exc}")
                return
        except Exception as exc:
            messagebox.showerror("Dokument senden", f"Dokument konnte nicht gelesen werden:\n{exc}")
            return

        max_len = 60000
        truncated = False
        if len(content) > max_len:
            content = content[:max_len]
            truncated = True

        filename = os.path.basename(path)
        if truncated:
            self._append("System: ", f"Dokument '{filename}' wird mit gekürztem Inhalt an die AI gesendet (max {max_len} Zeichen).")
        else:
            self._append("System: ", f"Dokument '{filename}' wird an die AI gesendet.")

        if self._on_attach:
            try:
                self._on_attach(path, content, truncated)
            except Exception as exc:
                messagebox.showerror("Dokument senden", f"Weitergabe an die AI fehlgeschlagen:\n{exc}")
        elif self._on_send:
            text = f"Bitte berücksichtige die folgenden Inhalte aus der Datei '{filename}':\n\n{content}"
            if truncated:
                text += "\n\n[Hinweis: Dokument wurde aufgrund der Größe gekürzt.]"
            self._on_send(text)
        else:
            self._append("System: ", "Es ist kein AI-Zugriff konfiguriert.")

