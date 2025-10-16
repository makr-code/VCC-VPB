"""Helper zum Aufbau der Statusleiste im VPB-Designer."""

from __future__ import annotations

import tkinter as tk


def create_status_bar(app: tk.Tk, status_var: tk.StringVar, ollama_var: tk.StringVar) -> tk.Frame:
    """Erzeugt die Statusleiste und hängt sie unten an das Hauptfenster."""

    statusbar = tk.Frame(app, bg="#eeeeee")
    statusbar.pack(side=tk.BOTTOM, fill=tk.X)

    tk.Label(statusbar, textvariable=status_var, anchor="w", bg="#eeeeee").pack(
        side=tk.LEFT, fill=tk.X, expand=True
    )
    tk.Label(statusbar, textvariable=ollama_var, anchor="e", bg="#eeeeee").pack(
        side=tk.RIGHT, padx=8
    )

    return statusbar
