"""Helper utilities for building the main menu and toolbar of the VPB app."""

from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING

from .shortcut_overlay import show_shortcut_overlay

if TYPE_CHECKING:  # pragma: no cover - only used for type hints
    from typing import Callable, Iterable, Tuple
    from vpb_app import VPBDesignerApp  # type: ignore  # circular import safe behind TYPE_CHECKING


def create_main_toolbar(app: "VPBDesignerApp") -> tk.Frame:
    """Create and pack the main toolbar for the given application."""

    toolbar = tk.Frame(app, bg="#f2f2f2", height=36)
    toolbar.pack(side=tk.TOP, fill=tk.X)

    # VPB-Schriftzug mit Logo links in der Toolbar
    vpb_frame = tk.Frame(toolbar, bg="#f2f2f2")
    vpb_frame.pack(side=tk.LEFT, padx=10, pady=4)
    
    # VPB Logo/Icon - anklickbar für About-Dialog
    vpb_logo = tk.Label(vpb_frame, text="🔄", font=("Segoe UI", 14), 
                        bg="#f2f2f2", fg="#2c3e50", cursor="hand2")
    vpb_logo.pack(side=tk.LEFT, padx=(0, 5))
    vpb_logo.bind("<Button-1>", lambda e: app._about())
    
    # VPB Schriftzug - anklickbar für About-Dialog
    vpb_label = tk.Label(vpb_frame, text="VPB", font=("Segoe UI", 12, "bold"), 
                         bg="#f2f2f2", fg="#2c3e50", cursor="hand2")
    vpb_label.pack(side=tk.LEFT)
    vpb_label.bind("<Button-1>", lambda e: app._about())
    
    # Tooltip für VPB-Schriftzug
    def _create_tooltip(widget, text):
        def _on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            tooltip_label = tk.Label(tooltip, text=text, 
                                   font=("Segoe UI", 9), bg="#2c3e50", fg="white", 
                                   relief=tk.SOLID, borderwidth=1, padx=5, pady=3)
            tooltip_label.pack()
            widget.tooltip = tooltip
        
        def _on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                delattr(widget, 'tooltip')
        
        widget.bind("<Enter>", _on_enter)
        widget.bind("<Leave>", _on_leave)
    
    _create_tooltip(vpb_logo, "VPB Process Designer - Über")
    _create_tooltip(vpb_label, "VPB Process Designer - Über")

    def _add_separator() -> None:
        tk.Frame(toolbar, width=2, bg="#d0d0d0").pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=4)
    
    _add_separator()

    button_specs = [
        ("Neu", app.new_document, 4),
        ("Öffnen", app.open_document, 4),
        ("Speichern", app.save_document, 4),
        ("Speichern unter", app.save_document_as, 4),
        ("Element hinzufügen", app._add_element_dialog, 8),
        ("Neu zeichnen", lambda: app.canvas.redraw_all(), 8),
        ("Auto-Layout", lambda: app.canvas.auto_layout(), 4),
    ]

    for text, command, padx in button_specs:
        tk.Button(toolbar, text=text, command=command).pack(side=tk.LEFT, padx=padx, pady=4)

    def _add_separator() -> None:
        tk.Frame(toolbar, width=2, bg="#d0d0d0").pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=4)

    _add_separator()

    align_menu = tk.Menubutton(toolbar, text="Ausrichten", relief=tk.RAISED)
    align_menu.menu = tk.Menu(align_menu, tearoff=0)
    align_menu["menu"] = align_menu.menu
    align_menu.menu.add_command(label="Links", command=lambda: app._align_selected("left"))
    align_menu.menu.add_command(label="Horizontal zentrieren", command=lambda: app._align_selected("center"))
    align_menu.menu.add_command(label="Rechts", command=lambda: app._align_selected("right"))
    align_menu.menu.add_separator()
    align_menu.menu.add_command(label="Oben", command=lambda: app._align_selected("top"))
    align_menu.menu.add_command(label="Vertikal mittig", command=lambda: app._align_selected("middle"))
    align_menu.menu.add_command(label="Unten", command=lambda: app._align_selected("bottom"))
    align_menu.pack(side=tk.LEFT, padx=2, pady=2)

    distribute_menu = tk.Menubutton(toolbar, text="Verteilen", relief=tk.RAISED)
    distribute_menu.menu = tk.Menu(distribute_menu, tearoff=0)
    distribute_menu["menu"] = distribute_menu.menu
    distribute_menu.menu.add_command(label="Horizontal", command=lambda: app._distribute_selected("horizontal"))
    distribute_menu.menu.add_command(label="Vertikal", command=lambda: app._distribute_selected("vertical"))
    distribute_menu.pack(side=tk.LEFT, padx=2, pady=2)

    formations_menu = tk.Menubutton(toolbar, text="Formationen", relief=tk.RAISED)
    formations_menu.menu = tk.Menu(formations_menu, tearoff=0)
    formations_menu["menu"] = formations_menu.menu
    formations_menu.menu.add_command(label="Kreis anordnen", command=app._arrange_selection_circular)
    formations_menu.pack(side=tk.LEFT, padx=2, pady=2)

    _add_separator()

    return toolbar


def create_main_menu(app: "VPBDesignerApp") -> tk.Menu:
    """Create the main menu bar for the given application and attach it."""

    menubar = tk.Menu(app)

    # Datei-Menü
    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(label="Neu", command=app.new_document)
    file_menu.add_command(label="Öffnen...", command=app.open_document)
    file_menu.add_command(label="AI-Ingestion Wizard…", command=app._open_ingestion_wizard)
    file_menu.add_separator()
    file_menu.add_command(label="Speichern", command=app.save_document)
    file_menu.add_command(label="Speichern unter...", command=app.save_document_as)
    file_menu.add_separator()
    file_menu.add_command(label="Metadaten bearbeiten...", command=app._edit_metadata)
    file_menu.add_command(label="Export als PNG...", command=app._export_png)
    file_menu.add_command(label="Export als PDF...", command=app._export_pdf)
    file_menu.add_command(label="Export als SVG...", command=app._export_svg)
    file_menu.add_command(label="Export als PostScript...", command=app._export_ps)
    file_menu.add_separator()
    file_menu.add_command(label="Beenden", command=app._on_close)
    menubar.add_cascade(label="Datei", menu=file_menu)

    # Bearbeiten-Menü
    edit_menu = tk.Menu(menubar, tearoff=0)
    edit_menu.add_command(label="Element hinzufügen", command=app._add_element_dialog)
    edit_menu.add_command(label="Verbindung hinzufügen", command=app._add_connection_dialog)
    edit_menu.add_separator()
    edit_menu.add_command(label="Ausgewähltes löschen (Entf)", command=app._delete_selected)
    edit_menu.add_command(label="Duplizieren (Ctrl+D)", command=app._duplicate_selected)
    edit_menu.add_separator()
    app._snap_var = tk.BooleanVar(master=app, value=False)
    edit_menu.add_checkbutton(label="Snap-to-Grid", variable=app._snap_var, command=app._toggle_snap)
    edit_menu.add_command(label="Link-Modus (L)", command=app._toggle_link_mode)
    edit_menu.add_command(label="Palette neu laden", command=app._reload_palettes)
    edit_menu.add_separator()
    edit_menu.add_command(label="Neu zeichnen", command=lambda: app.canvas.redraw_all())
    edit_menu.add_command(label="Auto-Layout", command=lambda: app.canvas.auto_layout())
    edit_menu.add_separator()
    edit_menu.add_command(label="Gruppe aus Auswahl bilden", command=app._group_from_selection)
    edit_menu.add_command(label="Gruppe auflösen", command=app._ungroup_selected)
    edit_menu.add_separator()
    edit_menu.add_command(label="Rückgängig (Ctrl+Z)", command=app._undo)
    edit_menu.add_command(label="Wiederholen (Ctrl+Y)", command=app._redo)
    menubar.add_cascade(label="Bearbeiten", menu=edit_menu)

    # Anordnen-Menü
    arrange_menu = tk.Menu(menubar, tearoff=0)
    arrange_menu.add_command(label="Links ausrichten", command=lambda: app._align_selected("left"))
    arrange_menu.add_command(label="Horizontal zentrieren", command=lambda: app._align_selected("center"))
    arrange_menu.add_command(label="Rechts ausrichten", command=lambda: app._align_selected("right"))
    arrange_menu.add_separator()
    arrange_menu.add_command(label="Oben ausrichten", command=lambda: app._align_selected("top"))
    arrange_menu.add_command(label="Vertikal mittig", command=lambda: app._align_selected("middle"))
    arrange_menu.add_command(label="Unten ausrichten", command=lambda: app._align_selected("bottom"))
    arrange_menu.add_separator()
    arrange_menu.add_command(label="Horizontal verteilen", command=lambda: app._distribute_selected("horizontal"))
    arrange_menu.add_command(label="Vertikal verteilen", command=lambda: app._distribute_selected("vertical"))
    menubar.add_cascade(label="Anordnen", menu=arrange_menu)

    # Ansicht-Menü
    view_menu = tk.Menu(menubar, tearoff=0)
    view_menu.add_command(label="Zoom zurücksetzen", command=app._reset_view)
    view_menu.add_command(label="Auf Diagramm zoomen", command=app._fit_to_diagram)
    view_menu.add_command(label="Zoom auf Auswahl", command=app._zoom_selection)
    view_menu.add_command(label="Auswahl zentrieren", command=app._center_selection)
    view_menu.add_separator()
    app._grid_var = tk.BooleanVar(master=app, value=True)
    view_menu.add_checkbutton(label="Grid anzeigen", variable=app._grid_var, command=app._toggle_grid)
    app._time_axis_var = tk.BooleanVar(master=app, value=True)
    view_menu.add_checkbutton(label="Zeitachse anzeigen", variable=app._time_axis_var, command=app._toggle_time_axis)
    view_menu.add_command(label="Zeitintervall setzen…", command=app._set_time_interval_dialog)
    view_menu.add_command(label="Hierarchien verwalten…", command=app._open_hierarchy_manager)
    view_menu.add_command(label="Hierarchie JSON bearbeiten…", command=app._configure_hierarchy_dialog)
    view_menu.add_command(label="Hierarchie-Bänder auto berechnen", command=app._auto_calculate_hierarchy_ranges)
    view_menu.add_separator()
    app._route_var = tk.StringVar(master=app, value="smart")
    view_menu.add_radiobutton(label="Routing: Gerade", value="straight", variable=app._route_var, command=app._apply_routing_style)
    view_menu.add_radiobutton(label="Routing: Orthogonal", value="orthogonal", variable=app._route_var, command=app._apply_routing_style)
    view_menu.add_radiobutton(label="Routing: Kurvig", value="curved", variable=app._route_var, command=app._apply_routing_style)
    view_menu.add_radiobutton(label="Routing: Smart (Auto)", value="smart", variable=app._route_var, command=app._apply_routing_style)
    view_menu.add_radiobutton(label="Routing: Smart+ (Grid)", value="smart-plus", variable=app._route_var, command=app._apply_routing_style)
    view_menu.add_separator()
    app._mousewheel_mode_var = tk.StringVar(master=app, value=app._mousewheel_behavior)
    view_menu.add_radiobutton(
        label="Mausrad: Zoomen (Strg=Pannen)",
        value="zoom-primary",
        variable=app._mousewheel_mode_var,
        command=app._on_mousewheel_mode_change,
    )
    view_menu.add_radiobutton(
        label="Mausrad: Pannen (Strg=Zoomen)",
        value="pan-primary",
        variable=app._mousewheel_mode_var,
        command=app._on_mousewheel_mode_change,
    )
    menubar.add_cascade(label="Ansicht", menu=view_menu)

    # Werkzeuge-Menü
    tools_menu = tk.Menu(menubar, tearoff=0)
    tools_menu.add_command(label="Prozess prüfen…", command=app._validate_process_dialog)
    menubar.add_cascade(label="Werkzeuge", menu=tools_menu)

    # Einstellungen-Menü
    settings_menu = tk.Menu(menubar, tearoff=0)
    settings_menu.add_command(label="Element-Stile bearbeiten...", command=app._edit_element_styles)
    settings_menu.add_command(label="Navigation Schrittgrößen…", command=app._configure_navigation_dialog)
    settings_menu.add_command(label="Autosave Einstellungen…", command=app._configure_autosave_dialog)
    menubar.add_cascade(label="Einstellungen", menu=settings_menu)

    # AI-Menü
    ai_menu = tk.Menu(menubar, tearoff=0)
    ai_menu.add_command(label="Ollama konfigurieren...", command=app._configure_ollama)
    ai_menu.add_command(label="Ollama Health-Check", command=app._ollama_health)
    ai_menu.add_command(label="Modell wechseln…", command=app._quick_switch_model)
    ai_menu.add_separator()
    ai_menu.add_command(label="Text → Diagramm…", command=app._text_to_diagram)
    ai_menu.add_command(label="Nächster Schritt vorschlagen…", command=app._suggest_next_step)
    ai_menu.add_command(label="Diagnose/Fix…", command=app._diagnose_fix)
    try:
        app._merge_snap_var = tk.BooleanVar(master=app, value=app._merge_snap_enabled)
        ai_menu.add_checkbutton(label="Merge: Raster-Snap (50)", variable=app._merge_snap_var, command=app._toggle_merge_snap)
        merge_mode_menu = tk.Menu(ai_menu, tearoff=0)
        app._merge_mode_var = tk.StringVar(master=app, value=app._merge_update_mode)
        merge_mode_menu.add_radiobutton(label="Keine Updates", value="none", variable=app._merge_mode_var, command=app._set_merge_mode)
        merge_mode_menu.add_radiobutton(label="Nur leere Felder füllen", value="fill-empty", variable=app._merge_mode_var, command=app._set_merge_mode)
        merge_mode_menu.add_radiobutton(label="Bestehende überschreiben", value="overwrite", variable=app._merge_mode_var, command=app._set_merge_mode)
        ai_menu.add_cascade(label="Merge: Update-Modus", menu=merge_mode_menu)
        app._auto_rename_var = tk.BooleanVar(master=app, value=app._auto_rename_enabled)
        ai_menu.add_checkbutton(label="Auto-Rename bei ID-Konflikten", variable=app._auto_rename_var, command=app._toggle_auto_rename)
    except Exception:
        pass
    menubar.add_cascade(label="AI", menu=ai_menu)

    # Hilfe-Menü
    help_menu = tk.Menu(menubar, tearoff=0)
    help_menu.add_command(label="Tastaturkürzel (F1)", command=lambda: show_shortcut_overlay(app))
    help_menu.add_command(label="Über", command=app._about)
    menubar.add_cascade(label="Hilfe", menu=help_menu)

    app.config(menu=menubar)
    return menubar
