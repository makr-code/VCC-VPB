"""Read-only XML viewer tab for the VPB mid notebook."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Sequence, Tuple


FormatOption = Tuple[str, str]


def add_xml_viewer_tab(
    notebook: ttk.Notebook,
    *,
    refresh_command: Callable[[str], None],
    font: Tuple[str, int] = ("Consolas", 10),
    available_formats: Sequence[FormatOption] | None = None,
    default_format: str = "bpmn",
) -> Tuple[tk.Text, tk.StringVar]:
    """Create a new XML viewer tab.

    Returns a tuple of (text_widget, selected_format_var).
    """

    options: Sequence[FormatOption]
    if available_formats:
        options = tuple(available_formats)
    else:
        options = (
            ("bpmn", "BPMN 2.0"),
            ("eepk", "eEPK"),
            ("atok", "ATOK XML"),
        )

    code_by_label = {label: code for code, label in options}
    label_list = [label for _, label in options]
    default_code = default_format.lower() if default_format else "bpmn"
    default_label = next((label for label, code in ((label, code) for code, label in options) if code == default_code), None)
    if default_label is None:
        default_label = label_list[0]
        default_code = code_by_label.get(default_label, "bpmn")

    xml_tab = tk.Frame(notebook)
    notebook.add(xml_tab, text="XML")

    toolbar = tk.Frame(xml_tab)
    toolbar.pack(side=tk.TOP, fill=tk.X)

    display_var = tk.StringVar(value=default_label)
    selected_format = tk.StringVar(value=default_code)

    def _sync_format_var(*_ignored: object) -> None:
        selected_format.set(code_by_label.get(display_var.get(), default_code))

    def _trigger_refresh(event: tk.Event | None = None) -> None:
        _sync_format_var()
        refresh_command(selected_format.get())

    tk.Button(toolbar, text="Diagramm  XML", command=_trigger_refresh).pack(side=tk.LEFT, padx=4, pady=4)

    fmt_box = ttk.Combobox(
        toolbar,
        state="readonly",
        width=16,
        values=label_list,
        textvariable=display_var,
    )
    fmt_box.pack(side=tk.LEFT, padx=(6, 4), pady=4)
    fmt_box.bind("<<ComboboxSelected>>", _trigger_refresh)

    display_var.trace_add("write", lambda *_: _sync_format_var())
    _sync_format_var()

    wrap = tk.Frame(xml_tab)
    wrap.pack(fill=tk.BOTH, expand=True)

    xml_text = tk.Text(wrap, wrap="none", font=font, undo=False)
    y_scroll = tk.Scrollbar(wrap, orient=tk.VERTICAL, command=xml_text.yview)
    x_scroll = tk.Scrollbar(wrap, orient=tk.HORIZONTAL, command=xml_text.xview)
    xml_text.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

    xml_text.grid(row=0, column=0, sticky="nsew")
    y_scroll.grid(row=0, column=1, sticky="ns")
    x_scroll.grid(row=1, column=0, sticky="we")

    wrap.rowconfigure(0, weight=1)
    wrap.columnconfigure(0, weight=1)

    def _block_edit(event: tk.Event) -> str:
        # Allow copy/select shortcuts (Ctrl+C, Ctrl+A) but block modifications.
        if getattr(event, "state", 0) & 0x0004:
            keysym = event.keysym.lower()
            if keysym == "c":
                return None
            if keysym == "a":
                xml_text.tag_add("sel", "1.0", "end-1c")
                return "break"
        return "break"

    for sequence in ("<Key>", "<Delete>", "<BackSpace>"):
        xml_text.bind(sequence, _block_edit)

    return xml_text, selected_format
