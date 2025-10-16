"""Shortcut overlay helper for the VPB designer."""

from __future__ import annotations

from typing import Optional

import tkinter as tk
from tkinter import ttk


SHORTCUT_SECTIONS = [
    (
        "Datei & Verwaltung",
        [
            ("Ctrl+N", "Neues Diagramm"),
            ("Ctrl+O", "Diagramm öffnen"),
            ("Ctrl+S / Ctrl+Shift+S", "Speichern / Speichern unter"),
        ],
    ),
    (
        "Auswahl & Bearbeitung",
        [
            ("Entf / Backspace", "Auswahl löschen"),
            ("Ctrl+D", "Auswahl duplizieren"),
            ("Ctrl+C / Ctrl+X / Ctrl+V", "Kopieren, Ausschneiden, Einfügen"),
            ("Ctrl+Z / Ctrl+Y", "Rückgängig / Wiederholen"),
        ],
    ),
    (
        "Navigation",
        [
            ("Pfeiltasten", "Auswahl verschieben (Shift = großer Schritt)"),
            ("Ohne Auswahl: Pfeiltasten", "Canvas pannen (Shift = großer Schritt)"),
            ("Space gedrückt + Ziehen", "Hand-Tool (Pan)"),
            ("Alt + Scrollrad", "Vertikales Panning"),
            ("Shift + Scrollrad", "Horizontales Panning"),
        ],
    ),
    (
        "Ansicht & Zoom",
        [
            ("Strg+Mausrad", "Zoom oder Pan (je nach Einstellung)"),
            ("Ctrl++ / Ctrl+-", "Zoom In/Out"),
            ("Ctrl+1", "Zoom auf 100 %"),
            ("Ctrl+0", "Ansicht zurücksetzen"),
            ("Ctrl+9", "Auf Diagramm zoomen"),
        ],
    ),
    (
        "Diagramm & Gruppen",
        [
            ("L", "Link-Modus umschalten"),
            ("Ctrl+G / Ctrl+Shift+G", "Gruppe bilden / auflösen"),
            ("Ctrl+Enter", "Chat senden oder Text→Diagramm"),
            ("F2", "Chat fokussieren"),
        ],
    ),
    (
        "Hilfe & Overlay",
        [
            ("F1", "Shortcut-Übersicht öffnen"),
            ("Ctrl+Shift+?", "Shortcut-Übersicht öffnen"),
            ("Esc", "Aktives Overlay oder Modus abbrechen"),
        ],
    ),
]


def toggle_shortcut_overlay(app: tk.Tk) -> str:
    """Toggle the visibility of the shortcut overlay."""

    try:
        overlay = getattr(app, "_shortcut_overlay", None)
        if overlay is not None and overlay.winfo_exists():
            hide_shortcut_overlay(app)
        else:
            show_shortcut_overlay(app)
    except Exception:
        pass
    return "break"


def show_shortcut_overlay(app: tk.Tk) -> None:
    """Show the shortcut overlay window."""

    try:
        overlay: Optional[tk.Toplevel] = getattr(app, "_shortcut_overlay", None)
        if overlay is not None and overlay.winfo_exists():
            try:
                overlay.deiconify()
                overlay.lift()
                overlay.focus_force()
            except Exception:
                pass
            return

        overlay = tk.Toplevel(app)
        overlay.title("Tastaturkürzel")
        overlay.transient(app)
        overlay.resizable(False, False)
        overlay.configure(background="#202428")
        try:
            overlay.attributes("-topmost", True)
        except Exception:
            pass
        try:
            overlay.attributes("-alpha", 0.96)
        except Exception:
            pass

        width, height = 720, 540
        try:
            screen_w = overlay.winfo_screenwidth()
            screen_h = overlay.winfo_screenheight()
            x = max(0, (screen_w - width) // 2)
            y = max(0, (screen_h - height) // 3)
            overlay.geometry(f"{width}x{height}+{x}+{y}")
        except Exception:
            overlay.geometry(f"{width}x{height}")

        container = ttk.Frame(overlay, padding=24)
        container.pack(fill=tk.BOTH, expand=True)

        heading = ttk.Label(container, text="Tastaturkürzel", font=("Segoe UI", 18, "bold"))
        heading.grid(row=0, column=0, sticky="w")
        subheading = ttk.Label(
            container,
            text="Praktische Navigationstasten für Diagramm, Bearbeitung, Ansicht und KI.",
            font=("Segoe UI", 11),
        )
        subheading.grid(row=1, column=0, sticky="w", pady=(4, 16))

        body = ttk.Frame(container)
        body.grid(row=2, column=0, sticky="nsew")
        container.rowconfigure(2, weight=1)
        container.columnconfigure(0, weight=1)

        cols = 2
        per_col = (len(SHORTCUT_SECTIONS) + cols - 1) // cols
        for col in range(cols):
            body.columnconfigure(col, weight=1)
        for idx, (title, items) in enumerate(SHORTCUT_SECTIONS):
            col = idx // per_col
            row = idx % per_col
            card = ttk.Frame(body, padding=(12, 10, 12, 14))
            card.grid(row=row, column=col, sticky="nsew", padx=8, pady=6)
            ttk.Label(card, text=title, font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
            for i, (keys, description) in enumerate(items, start=1):
                row_frame = ttk.Frame(card)
                row_frame.grid(row=i, column=0, sticky="we", pady=(6 if i == 1 else 2, 0))
                row_frame.columnconfigure(0, weight=0)
                row_frame.columnconfigure(1, weight=1)
                key_lbl = ttk.Label(row_frame, text=keys, font=("Consolas", 10, "bold"))
                key_lbl.grid(row=0, column=0, sticky="w")
                desc_lbl = ttk.Label(row_frame, text=description, font=("Segoe UI", 10))
                desc_lbl.grid(row=0, column=1, sticky="w", padx=(10, 0))

        footer = ttk.Label(
            container,
            text="Schließen mit Esc, F1 oder Klick außerhalb.",
            font=("Segoe UI", 10, "italic"),
        )
        footer.grid(row=3, column=0, sticky="e", pady=(16, 0))

        overlay.bind("<Escape>", lambda e: hide_shortcut_overlay(app))
        overlay.bind("<F1>", lambda e: hide_shortcut_overlay(app))
        overlay.bind("<Control-Shift-slash>", lambda e: hide_shortcut_overlay(app))
        overlay.protocol("WM_DELETE_WINDOW", lambda: hide_shortcut_overlay(app))

        def _on_overlay_click(event):
            try:
                if event.widget is overlay:
                    hide_shortcut_overlay(app)
            except Exception:
                pass

        overlay.bind("<Button-1>", _on_overlay_click)

        try:
            overlay.grab_set()
        except Exception:
            pass
        try:
            overlay.focus_force()
        except Exception:
            pass

        app._shortcut_overlay = overlay  # type: ignore[attr-defined]
    except Exception:
        try:
            existing = getattr(app, "_shortcut_overlay", None)
            if isinstance(existing, tk.Toplevel):
                existing.destroy()
        except Exception:
            pass
        app._shortcut_overlay = None  # type: ignore[attr-defined]


def hide_shortcut_overlay(app: tk.Tk) -> str:
    """Hide and dispose the shortcut overlay."""

    overlay = getattr(app, "_shortcut_overlay", None)
    if overlay is None:
        return "break"
    try:
        if overlay.winfo_exists():
            overlay.grab_release()
            overlay.destroy()
    except Exception:
        pass
    app._shortcut_overlay = None  # type: ignore[attr-defined]
    return "break"
