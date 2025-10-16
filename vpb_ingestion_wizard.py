from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Dict


@dataclass
class IngestionWizardRequest:
    sources: List[str] = field(default_factory=list)
    inline_text: str = ""
    prompt_context: str = ""
    options: Dict[str, object] = field(default_factory=dict)


class IngestionWizardDialog(tk.Toplevel):
    """Mehrstufiger Wizard für AI-Ingestion (TXT/MD/CSV)."""

    def __init__(
        self,
        master: tk.Widget,
        *,
        title: str = "AI-Ingestion Wizard",
        initial_dir: Optional[str] = None,
        on_submit: Optional[Callable[[IngestionWizardRequest], None]] = None,
    ) -> None:
        super().__init__(master)
        self.transient(master)
        self.title(title)
        self.geometry("720x520")
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.grab_set()

        self._on_submit = on_submit
        self._initial_dir = initial_dir or os.getcwd()
        self.result: Optional[IngestionWizardRequest] = None

        self._steps: list[tk.Frame] = []
        self._current_step = 0
        self._step_titles = ["Quelle auswählen", "Zusammenfassung"]

        self._sources: list[str] = []
        self._inline_text = tk.Text(self, height=10, wrap="word")  # placeholder init
        self._prompt_context_var = tk.StringVar()

        self._create_ui()
        self._show_step(0)

    # ------------------------------------------------------------------
    # UI Aufbau
    # ------------------------------------------------------------------
    def _create_ui(self) -> None:
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)

        # Kopfzeile
        self._title_var = tk.StringVar(value=self._step_titles[0])
        title_lbl = ttk.Label(container, textvariable=self._title_var, font=("Segoe UI", 14, "bold"))
        title_lbl.pack(anchor="w", pady=(0, 10))

        # Step-Container
        self._step_container = ttk.Frame(container)
        self._step_container.pack(fill=tk.BOTH, expand=True)

        # Navigation
        nav = ttk.Frame(container)
        nav.pack(fill=tk.X, pady=(12, 0))
        self._btn_cancel = ttk.Button(nav, text="Abbrechen", command=self._on_cancel)
        self._btn_cancel.pack(side=tk.LEFT)
        self._btn_back = ttk.Button(nav, text="Zurück", command=self._prev_step)
        self._btn_back.pack(side=tk.RIGHT, padx=(0, 8))
        self._btn_next = ttk.Button(nav, text="Weiter", command=self._next_step)
        self._btn_next.pack(side=tk.RIGHT)

        # Steps erstellen
        self._steps.append(self._build_step_sources(self._step_container))
        self._steps.append(self._build_step_summary(self._step_container))

    def _build_step_sources(self, parent: ttk.Frame) -> tk.Frame:
        frame = ttk.Frame(parent)

        info = ttk.Label(
            frame,
            text="Wähle eine oder mehrere Dateien aus (TXT/MD/CSV) oder füge freien Text hinzu.\n" "Mindestens eine Quelle ist erforderlich.",
            justify=tk.LEFT,
            wraplength=640,
        )
        info.pack(anchor="w", pady=(0, 12))

        # Datei-Liste
        files_frame = ttk.LabelFrame(frame, text="Ausgewählte Dateien")
        files_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 12))

        list_frame = ttk.Frame(files_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self._sources_list = tk.Listbox(list_frame, selectmode=tk.EXTENDED, height=6)
        self._sources_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        y_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self._sources_list.yview)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._sources_list.configure(yscrollcommand=y_scroll.set)

        btns = ttk.Frame(files_frame)
        btns.pack(fill=tk.X, padx=6, pady=(0, 6))
        ttk.Button(btns, text="Dateien hinzufügen…", command=self._add_files).pack(side=tk.LEFT)
        ttk.Button(btns, text="Entfernen", command=self._remove_selected_files).pack(side=tk.LEFT, padx=(6, 0))

        # Freitext
        text_frame = ttk.LabelFrame(frame, text="Freier Text (optional)")
        text_frame.pack(fill=tk.BOTH, expand=True)
        self._inline_text = tk.Text(text_frame, height=6, wrap="word")
        self._inline_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Prompt-Kontext
        context_frame = ttk.LabelFrame(frame, text="Prompt-Kontext / Hinweise (optional)")
        context_frame.pack(fill=tk.X, pady=(12, 0))
        ttk.Entry(context_frame, textvariable=self._prompt_context_var).pack(fill=tk.X, padx=6, pady=6)

        return frame

    def _build_step_summary(self, parent: ttk.Frame) -> tk.Frame:
        frame = ttk.Frame(parent)

        self._summary_text = tk.Text(frame, height=20, wrap="word", state="disabled", background="#f9fafb")
        self._summary_text.pack(fill=tk.BOTH, expand=True)

        hint = ttk.Label(
            frame,
            text="Prüfe die Zusammenfassung und starte anschließend die Ingestion.\nDieser Schritt wird später die AI-Verarbeitung anstoßen.",
            justify=tk.LEFT,
            wraplength=640,
        )
        hint.pack(anchor="w", pady=(8, 0))

        return frame

    # ------------------------------------------------------------------
    # Dateien & Quellen
    # ------------------------------------------------------------------
    def _add_files(self) -> None:
        try:
            paths = filedialog.askopenfilenames(
                parent=self,
                title="Dateien auswählen",
                initialdir=self._initial_dir,
                filetypes=[
                    ("Textdateien", "*.txt *.md *.markdown"),
                    ("CSV", "*.csv"),
                    ("Alle Dateien", "*.*"),
                ],
            )
        except Exception:
            paths = []
        if not paths:
            return
        added = False
        for path in paths:
            if not path:
                continue
            norm = os.path.abspath(path)
            if norm not in self._sources and os.path.exists(norm):
                self._sources.append(norm)
                self._sources_list.insert(tk.END, norm)
                added = True
        if added:
            try:
                self._initial_dir = os.path.dirname(self._sources[-1]) or self._initial_dir
            except Exception:
                pass
            self._update_summary()

    def _remove_selected_files(self) -> None:
        sel = list(self._sources_list.curselection())
        if not sel:
            return
        sel.sort(reverse=True)
        for idx in sel:
            try:
                self._sources_list.delete(idx)
                self._sources.pop(idx)
            except Exception:
                pass
        self._update_summary()

    # ------------------------------------------------------------------
    # Schrittsteuerung
    # ------------------------------------------------------------------
    def _show_step(self, index: int) -> None:
        index = max(0, min(len(self._steps) - 1, index))
        self._current_step = index
        for i, frame in enumerate(self._steps):
            if i == index:
                frame.pack(fill=tk.BOTH, expand=True)
            else:
                frame.pack_forget()
        self._title_var.set(self._step_titles[index])
        self._update_nav()
        if index == 1:
            self._update_summary()

    def _update_nav(self) -> None:
        self._btn_back.configure(state=(tk.NORMAL if self._current_step > 0 else tk.DISABLED))
        if self._current_step >= len(self._steps) - 1:
            self._btn_next.configure(text="Ingestion starten", command=self._finish)
        else:
            self._btn_next.configure(text="Weiter", command=self._next_step)

    def _next_step(self) -> None:
        if not self._validate_step(self._current_step):
            return
        self._show_step(self._current_step + 1)

    def _prev_step(self) -> None:
        self._show_step(self._current_step - 1)

    def _validate_step(self, index: int) -> bool:
        if index == 0:
            sources = list(self._sources)
            text = self._inline_text.get("1.0", tk.END).strip()
            if not sources and not text:
                messagebox.showwarning("AI-Ingestion", "Bitte wähle mindestens eine Datei aus oder füge Text hinzu.")
                return False
        return True

    def _finish(self) -> None:
        if not self._validate_step(self._current_step):
            return
        req = IngestionWizardRequest(
            sources=list(self._sources),
            inline_text=self._inline_text.get("1.0", tk.END).strip(),
            prompt_context=self._prompt_context_var.get().strip(),
            options={},
        )
        self.result = req
        if self._on_submit:
            try:
                self._on_submit(req)
            except Exception as exc:
                messagebox.showerror("AI-Ingestion", f"Fehler beim Starten der Ingestion: {exc}")
                return
        self.destroy()

    def _on_cancel(self) -> None:
        self.result = None
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()

    def _update_summary(self) -> None:
        if not hasattr(self, "_summary_text"):
            return
        lines: list[str] = []
        if self._sources:
            lines.append("Dateien:")
            for path in self._sources:
                lines.append(f"  • {path}")
        else:
            lines.append("Dateien: (keine)")
        text = self._inline_text.get("1.0", tk.END).strip()
        if text:
            lines.append("")
            preview = text.splitlines()[:5]
            if len(text.splitlines()) > 5:
                preview.append("…")
            lines.append("Freitext:")
            lines.extend(f"  {line}" for line in preview)
        else:
            lines.append("")
            lines.append("Freitext: (leer)")
        ctx = self._prompt_context_var.get().strip()
        lines.append("")
        lines.append(f"Prompt-Kontext: {ctx if ctx else '(leer)'}")

        try:
            self._summary_text.configure(state="normal")
            self._summary_text.delete("1.0", tk.END)
            self._summary_text.insert("1.0", "\n".join(lines))
            self._summary_text.configure(state="disabled")
        except Exception:
            pass

    # Komfort: externe Aufrufer können Dialog modal verwenden
    def show(self) -> Optional[IngestionWizardRequest]:
        self.wait_window(self)
        return self.result
