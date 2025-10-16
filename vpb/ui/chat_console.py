"""Hilfsfunktionen für die Chat-Konsole im VPB-Designer."""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Tuple

from .chat_panel import ChatPanel
from .task_manager import TaskManager


def create_chat_console(
    app: tk.Tk,
    parent: tk.Misc,
    *,
    on_send: Callable[[str], None],
    on_stop: Callable[[], None],
    on_attach: Callable[[str, str, bool], None],
) -> Tuple[tk.LabelFrame, ChatPanel, TaskManager]:
    """Erzeugt die Chat-Konsole und gibt Container, ChatPanel und TaskManager zurück."""

    container = tk.LabelFrame(parent, text="AI Konsole", bg="#ffffff", fg="#111111")
    try:
        container.configure(labelanchor="nw")
    except Exception:
        pass
    container.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

    chat_panel = ChatPanel(
        container,
        on_send=on_send,
        on_stop=on_stop,
        on_attach=on_attach,
    )
    chat_panel.pack(fill=tk.BOTH, expand=True)

    tasks = TaskManager(app)

    return container, chat_panel, tasks
