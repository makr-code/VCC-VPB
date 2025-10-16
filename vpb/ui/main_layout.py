"""Main layout helpers for the VPB application."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import tkinter as tk
from tkinter import ttk

from .palette_panel import PalettePanel
from .arrange_panel import ArrangePanel


@dataclass
class MainLayout:
    """Container for the primary layout widgets of the VPB designer."""

    paned: ttk.Panedwindow
    left_pane: ttk.Frame
    mid_pane: ttk.Frame
    right_pane: ttk.Frame
    palette: PalettePanel
    arrange_panel: Optional[ArrangePanel]
    mid_split: ttk.Panedwindow
    mid_notebook: ttk.Notebook
    chat_console_wrap: tk.Frame
    sidebar_left_width: int
    sidebar_right_width: int


def create_main_layout(
    app: tk.Tk,
    pref_sidebar_left: Optional[int],
    pref_sidebar_right: Optional[int],
    *,
    on_palette_pick: Callable,
    on_palette_reload: Callable,
    show_arrange_panel: bool = True,
) -> MainLayout:
    """Create the main layout: paned window, sidebars, and notebook split."""

    paned = ttk.Panedwindow(app, orient=tk.HORIZONTAL)
    paned.pack(fill=tk.BOTH, expand=True)

    left_pane = ttk.Frame(paned, width=250)
    mid_pane = ttk.Frame(paned)
    right_pane = ttk.Frame(paned, width=250)

    paned.add(left_pane, weight=0)
    paned.add(mid_pane, weight=1)
    paned.add(right_pane, weight=0)

    sidebar_left_width = pref_sidebar_left if isinstance(pref_sidebar_left, int) and pref_sidebar_left > 0 else 250
    sidebar_right_width = pref_sidebar_right if isinstance(pref_sidebar_right, int) and pref_sidebar_right > 0 else 250

    left_pane.grid_columnconfigure(0, weight=1)

    palette = PalettePanel(left_pane, on_pick=on_palette_pick, on_reload=on_palette_reload)
    palette.grid(row=0, column=0, sticky="nsew")

    arrange_panel: Optional[ArrangePanel]
    if show_arrange_panel:
        arrange_panel = ArrangePanel(left_pane)
        arrange_panel.grid(row=1, column=0, sticky="we", padx=0, pady=(4, 0))
        left_pane.grid_rowconfigure(0, weight=1)
        left_pane.grid_rowconfigure(1, weight=0)
    else:
        arrange_panel = None
        left_pane.grid_rowconfigure(0, weight=1)

    mid_split = ttk.Panedwindow(mid_pane, orient=tk.VERTICAL)
    mid_split.pack(fill=tk.BOTH, expand=True)

    mid_notebook_wrap = ttk.Frame(mid_split)
    chat_console_wrap = tk.Frame(mid_split, bg="#ffffff")

    mid_split.add(mid_notebook_wrap, weight=5)
    mid_split.add(chat_console_wrap, weight=2)
    try:
        mid_split.pane(chat_console_wrap, minsize=160)
    except Exception:
        pass

    mid_notebook = ttk.Notebook(mid_notebook_wrap)
    mid_notebook.pack(fill=tk.BOTH, expand=True)

    layout = MainLayout(
        paned=paned,
        left_pane=left_pane,
        mid_pane=mid_pane,
        right_pane=right_pane,
        palette=palette,
        arrange_panel=arrange_panel,
        mid_split=mid_split,
        mid_notebook=mid_notebook,
        chat_console_wrap=chat_console_wrap,
        sidebar_left_width=sidebar_left_width,
        sidebar_right_width=sidebar_right_width,
    )

    def _apply_initial_sashes() -> None:
        try:
            total_width = int(paned.winfo_width() or 0)
            if total_width <= 0:
                app.after(80, _apply_initial_sashes)
                return

            left_width = max(160, int(layout.sidebar_left_width))
            right_width = max(260, int(layout.sidebar_right_width))
            try:
                paned.sashpos(0, left_width)
                paned.sashpos(1, max(left_width + 320, total_width - right_width))
            except Exception:
                pass
        except Exception:
            pass

    def _update_sidebar_widths(event=None) -> None:  # type: ignore[override]
        try:
            layout.sidebar_left_width = int(left_pane.winfo_width() or layout.sidebar_left_width)
            layout.sidebar_right_width = int(right_pane.winfo_width() or layout.sidebar_right_width)
        except Exception:
            pass
        else:
            setattr(app, "_sidebar_left_width", layout.sidebar_left_width)
            setattr(app, "_sidebar_right_width", layout.sidebar_right_width)

    def _enforce_min_widths(event=None) -> None:  # type: ignore[override]
        try:
            total_width = int(paned.winfo_width() or 0)
            if total_width <= 0:
                return

            min_left, min_right, min_mid = 160, 260, 200
            s0 = int(paned.sashpos(0))
            s1 = int(paned.sashpos(1))

            if s0 < min_left:
                paned.sashpos(0, min_left)
                s0 = min_left

            max_s1 = max(s0 + min_mid, total_width - min_right)
            if s1 < max(s0 + min_mid, 0):
                s1 = max(s0 + min_mid, 0)
            if s1 > max_s1:
                s1 = max_s1
            paned.sashpos(1, s1)
        except Exception:
            pass

    app.after(150, _apply_initial_sashes)

    try:
        paned.bind("<ButtonRelease-1>", lambda e: (_update_sidebar_widths(), _enforce_min_widths()))
    except Exception:
        pass

    return layout
