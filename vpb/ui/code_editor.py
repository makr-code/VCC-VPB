"""Code-Editor-Tab für den Mittelbereich des VPB-Designers."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


def add_code_editor_tab(
    notebook: ttk.Notebook,
    *,
    refresh_command: Callable[[], None],
    apply_command: Callable[[], None],
    clear_error_callback: Optional[Callable[[], None]] = None,
    font: tuple[str, int] = ("Consolas", 10),
) -> tk.Text:
    """Fügt dem Notebook einen Code-Editor-Tab hinzu und gibt das Text-Widget zurück."""

    code_tab = tk.Frame(notebook)
    notebook.add(code_tab, text="Code")

    code_toolbar = tk.Frame(code_tab)
    code_toolbar.pack(side=tk.TOP, fill=tk.X)

    tk.Button(code_toolbar, text="Diagramm → Code", command=refresh_command).pack(side=tk.LEFT, padx=4, pady=4)
    tk.Button(code_toolbar, text="Code → Diagramm", command=apply_command).pack(side=tk.LEFT, padx=4, pady=4)

    code_wrap = tk.Frame(code_tab)
    code_wrap.pack(fill=tk.BOTH, expand=True)

    code_text = tk.Text(code_wrap, wrap="none", font=font)
    y_scroll = tk.Scrollbar(code_wrap, orient=tk.VERTICAL, command=code_text.yview)
    x_scroll = tk.Scrollbar(code_wrap, orient=tk.HORIZONTAL, command=code_text.xview)
    code_text.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

    code_text.grid(row=0, column=0, sticky="nsew")
    y_scroll.grid(row=0, column=1, sticky="ns")
    x_scroll.grid(row=1, column=0, sticky="we")

    code_wrap.rowconfigure(0, weight=1)
    code_wrap.columnconfigure(0, weight=1)

    try:
        code_text.tag_configure("json_error", background="#ffe6e6")
        if clear_error_callback is not None:
            code_text.bind("<KeyRelease>", lambda _: clear_error_callback())
    except Exception:
        pass

    return code_text
