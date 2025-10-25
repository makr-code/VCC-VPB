"""Helper zum Anlegen des Diagramm-Tabs im Hauptnotebook."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Tuple

from .canvas import VPBCanvas, HierarchyCanvas, RulerCanvas


def add_diagram_tab(notebook: ttk.Notebook) -> Tuple[
    tk.Frame,
    VPBCanvas,
    RulerCanvas,
    RulerCanvas,
    HierarchyCanvas,
    tk.Scrollbar,
    tk.Scrollbar,
]:
    """Erstellt den Diagramm-Tab samt Canvas, Linealen und Scrollbars."""

    diagram_tab = tk.Frame(notebook)
    notebook.add(diagram_tab, text="Diagramm")

    canvas_wrap = tk.Frame(diagram_tab)
    canvas_wrap.pack(fill=tk.BOTH, expand=True)

    tk.Canvas(canvas_wrap, width=20, height=20, background="#f0f0f0", highlightthickness=0).grid(
        row=0,
        column=0,
        columnspan=2,
        sticky="nw",
    )

    ruler_x = RulerCanvas(canvas_wrap, orientation="x", height=20)
    ruler_x.grid(row=0, column=2, sticky="we")

    hier_canvas = HierarchyCanvas(canvas_wrap, width=90)
    hier_canvas.grid(row=1, column=0, sticky="ns")

    ruler_y = RulerCanvas(canvas_wrap, orientation="y", width=20)
    ruler_y.grid(row=1, column=1, sticky="ns")

    canvas = VPBCanvas(canvas_wrap)
    canvas.grid(row=1, column=2, sticky="nsew")

    x_scroll = tk.Scrollbar(canvas_wrap, orient=tk.HORIZONTAL)
    x_scroll.grid(row=2, column=2, sticky="we")
    x_scroll.configure(troughcolor="#e0e0e0")
    x_scroll.grid_remove = lambda: None  # Scrollbar nie ausblenden

    y_scroll = tk.Scrollbar(canvas_wrap, orient=tk.VERTICAL)
    y_scroll.grid(row=1, column=3, sticky="ns")
    y_scroll.configure(troughcolor="#e0e0e0")
    y_scroll.grid_remove = lambda: None  # Scrollbar nie ausblenden

    canvas_wrap.rowconfigure(1, weight=1)
    canvas_wrap.columnconfigure(0, weight=0, minsize=90)
    canvas_wrap.columnconfigure(1, weight=0, minsize=20)
    canvas_wrap.columnconfigure(2, weight=1)
    canvas_wrap.columnconfigure(3, weight=0)

    return diagram_tab, canvas, ruler_x, ruler_y, hier_canvas, x_scroll, y_scroll
