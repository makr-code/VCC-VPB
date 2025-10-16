"""Helper für die rechte Seitenleiste des VPB-Designers."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Tuple

from .properties_panel import PropertiesPanel
from .canvas import MiniMapCanvas


def create_right_sidebar(
    parent: tk.Misc,
    *,
    on_apply: Callable[..., None],
    resolve_member_label: Callable[[str], str],
    on_member_select: Callable[[str], None],
    on_group_add: Optional[Callable[[str], None]] = None,
    on_group_remove: Optional[Callable[[str], None]] = None,
    properties_tab_title: str = "Eigenschaften",
    minimap_tab_title: str = "Minimap",
) -> Tuple[ttk.Notebook, ttk.Notebook, PropertiesPanel, MiniMapCanvas]:
    """Erstellt die rechte Seitenleiste mit separatem Minimap-Notebook über dem Settings-Notebook."""

    container = ttk.Frame(parent)
    container.pack(fill=tk.BOTH, expand=True)

    container.grid_columnconfigure(0, weight=1)
    container.grid_rowconfigure(0, weight=0)
    container.grid_rowconfigure(1, weight=1)

    minimap_notebook = ttk.Notebook(container)
    minimap_notebook.grid(row=0, column=0, sticky="nsew", pady=(0, 6))

    minimap_tab = ttk.Frame(minimap_notebook)
    minimap = MiniMapCanvas(minimap_tab, height=160)
    minimap.pack(fill=tk.BOTH, expand=True)
    minimap_notebook.add(minimap_tab, text=minimap_tab_title)

    settings_notebook = ttk.Notebook(container)
    settings_notebook.grid(row=1, column=0, sticky="nsew")

    props = PropertiesPanel(
        settings_notebook,
        on_apply=on_apply,
        resolve_member_label=resolve_member_label,
        on_member_select=on_member_select,
        on_group_add=on_group_add,
        on_group_remove=on_group_remove,
    )
    settings_notebook.add(props, text=properties_tab_title)

    return minimap_notebook, settings_notebook, props, minimap
