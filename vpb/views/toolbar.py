"""
Toolbar View - Toolbar mit VPB-Branding und Schnellzugriff-Buttons.

Reine View-Komponente für die Toolbar des VPB Process Designers.
Publiziert alle Benutzeraktionen über den Event-Bus.

Event-Struktur:
    - ui:action:file.*      (Datei-Aktionen: Neu, Öffnen, Speichern)
    - ui:action:edit.*      (Edit-Aktionen: Element hinzufügen, Neu zeichnen, Auto-Layout)
    - ui:action:arrange.*   (Anordnen: Ausrichten, Verteilen, Formationen)
    - ui:action:help.about  (Über-Dialog via VPB-Logo-Klick)

Autor: GitHub Copilot (Phase 4: Views Layer)
"""

import tkinter as tk
from typing import Optional, TYPE_CHECKING
from vpb.infrastructure.event_bus import get_global_event_bus

if TYPE_CHECKING:
    from vpb.infrastructure.event_bus import EventBus


class ToolbarView:
    """
    Toolbar View für den VPB Process Designer.
    
    Erstellt die Toolbar mit VPB-Branding, Schnellzugriff-Buttons und
    Anordnungs-Menüs. Publiziert alle Benutzeraktionen über den Event-Bus.
    
    Komponenten:
        - VPB-Logo & Schriftzug (anklickbar → About-Dialog)
        - Datei-Buttons: Neu, Öffnen, Speichern, Speichern unter
        - Edit-Buttons: Element hinzufügen, Neu zeichnen, Auto-Layout
        - Anordnen-Menüs: Ausrichten (6), Verteilen (2), Formationen (1)
    
    Attribute:
        toolbar: Tkinter Frame-Widget
        event_bus: Event-Bus für Action-Publishing
        
    Beispiel:
        >>> toolbar = ToolbarView(parent_frame)
        >>> # Toolbar ist automatisch gepackt (side=TOP, fill=X)
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        event_bus: Optional["EventBus"] = None
    ):
        """
        Initialisiert die Toolbar View.
        
        Args:
            parent: Parent Tk-Widget (normalerweise Hauptfenster)
            event_bus: Event-Bus Instanz (optional, nutzt global event bus)
        """
        self.parent = parent
        self.event_bus = event_bus or get_global_event_bus()
        
        # Toolbar Frame erstellen
        self.toolbar = tk.Frame(parent, bg="#f2f2f2", height=36)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Komponenten erstellen
        self._create_file_buttons()
        self._create_edit_buttons()
        self._add_separator()
        self._create_arrange_menus()
        self._add_separator()
        self._create_canvas_controls()
        self._add_separator()
        self._create_vpb_logo_right()  # VPB-Schriftzug rechts
    
    def _create_vpb_branding(self) -> None:
        """Erstellt VPB-Logo und Schriftzug mit About-Tooltip."""
        vpb_frame = tk.Frame(self.toolbar, bg="#f2f2f2")
        vpb_frame.pack(side=tk.LEFT, padx=10, pady=4)
        
        # VPB Logo/Icon - anklickbar für About-Dialog
        vpb_logo = tk.Label(
            vpb_frame, 
            text="🔄", 
            font=("Segoe UI", 14), 
            bg="#f2f2f2", 
            fg="#2c3e50", 
            cursor="hand2"
        )
        vpb_logo.pack(side=tk.LEFT, padx=(0, 5))
        vpb_logo.bind("<Button-1>", lambda e: self._publish_action("help.about"))
        
        # VPB Schriftzug - anklickbar für About-Dialog
        vpb_label = tk.Label(
            vpb_frame, 
            text="VPB", 
            font=("Segoe UI", 12, "bold"), 
            bg="#f2f2f2", 
            fg="#2c3e50", 
            cursor="hand2"
        )
        vpb_label.pack(side=tk.LEFT)
        vpb_label.bind("<Button-1>", lambda e: self._publish_action("help.about"))
        
        # Tooltips hinzufügen
        self._create_tooltip(vpb_logo, "VPB Process Designer - Über")
        self._create_tooltip(vpb_label, "VPB Process Designer - Über")
    
    def _create_file_buttons(self) -> None:
        """Erstellt Datei-Buttons (Neu, Öffnen, Speichern)."""
        file_buttons = [
            ("Neu", "file.new", 4),
            ("Öffnen", "file.open", 4),
            ("Speichern", "file.save", 4),
            ("Speichern unter", "file.save_as", 4),
        ]
        
        for text, action, padx in file_buttons:
            btn = tk.Button(
                self.toolbar, 
                text=text, 
                command=lambda a=action: self._publish_action(a)
            )
            btn.pack(side=tk.LEFT, padx=padx, pady=4)
    
    def _create_edit_buttons(self) -> None:
        """Erstellt Edit-Buttons (Element hinzufügen, Neu zeichnen, Auto-Layout)."""
        edit_buttons = [
            ("Element hinzufügen", "edit.add_element", 8),
            ("Neu zeichnen", "edit.redraw", 8),
            ("Auto-Layout", "edit.auto_layout", 4),
        ]
        
        for text, action, padx in edit_buttons:
            btn = tk.Button(
                self.toolbar, 
                text=text, 
                command=lambda a=action: self._publish_action(a)
            )
            btn.pack(side=tk.LEFT, padx=padx, pady=4)
        
        # Separator
        self._add_separator()
        
        # Gruppierungs-Buttons
        group_buttons = [
            ("⬜ Gruppe bilden", "edit.group", 4),
            ("⟳ Zeitschleife bilden", "edit.time_loop", 4),
            ("◻ Gruppe auflösen", "edit.ungroup", 8),
        ]
        
        for text, action, padx in group_buttons:
            btn = tk.Button(
                self.toolbar, 
                text=text, 
                command=lambda a=action: self._publish_action(a)
            )
            btn.pack(side=tk.LEFT, padx=padx, pady=4)
    
    def _create_arrange_menus(self) -> None:
        """Erstellt Anordnen-Menüs (Ausrichten, Verteilen, Formationen)."""
        # Ausrichten-Menü
        align_menu = tk.Menubutton(self.toolbar, text="Ausrichten", relief=tk.RAISED)
        align_menu.menu = tk.Menu(align_menu, tearoff=0)
        align_menu["menu"] = align_menu.menu
        
        align_menu.menu.add_command(
            label="Links", 
            command=lambda: self._publish_action("arrange.align", {"mode": "left"})
        )
        align_menu.menu.add_command(
            label="Horizontal zentrieren", 
            command=lambda: self._publish_action("arrange.align", {"mode": "center"})
        )
        align_menu.menu.add_command(
            label="Rechts", 
            command=lambda: self._publish_action("arrange.align", {"mode": "right"})
        )
        align_menu.menu.add_separator()
        align_menu.menu.add_command(
            label="Oben", 
            command=lambda: self._publish_action("arrange.align", {"mode": "top"})
        )
        align_menu.menu.add_command(
            label="Vertikal mittig", 
            command=lambda: self._publish_action("arrange.align", {"mode": "middle"})
        )
        align_menu.menu.add_command(
            label="Unten", 
            command=lambda: self._publish_action("arrange.align", {"mode": "bottom"})
        )
        
        align_menu.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Verteilen-Menü
        distribute_menu = tk.Menubutton(self.toolbar, text="Verteilen", relief=tk.RAISED)
        distribute_menu.menu = tk.Menu(distribute_menu, tearoff=0)
        distribute_menu["menu"] = distribute_menu.menu
        
        distribute_menu.menu.add_command(
            label="Horizontal", 
            command=lambda: self._publish_action("arrange.distribute", {"mode": "horizontal"})
        )
        distribute_menu.menu.add_command(
            label="Vertikal", 
            command=lambda: self._publish_action("arrange.distribute", {"mode": "vertical"})
        )
        
        distribute_menu.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Formationen-Menü
        formations_menu = tk.Menubutton(self.toolbar, text="Formationen", relief=tk.RAISED)
        formations_menu.menu = tk.Menu(formations_menu, tearoff=0)
        formations_menu["menu"] = formations_menu.menu
        
        formations_menu.menu.add_command(
            label="Kreis anordnen", 
            command=lambda: self._publish_action("arrange.formation", {"mode": "circular"})
        )
        
        formations_menu.pack(side=tk.LEFT, padx=2, pady=2)
    
    def _create_canvas_controls(self) -> None:
        """Erstellt Canvas-Kontroll-Elemente (Zoom, Pan, Fit)."""
        # Zoom Out Button
        zoom_out_btn = tk.Button(
            self.toolbar,
            text="🔍−",
            width=3,
            command=lambda: self._publish_action("canvas.zoom", {"direction": "out"})
        )
        zoom_out_btn.pack(side=tk.LEFT, padx=2, pady=4)
        self._create_tooltip(zoom_out_btn, "Zoom Out (Ctrl + Scroll ↓)")
        
        # Zoom-Level Anzeige/Reset
        self.zoom_label = tk.Label(
            self.toolbar,
            text="100%",
            font=("Segoe UI", 9),
            bg="#f2f2f2",
            fg="#2c3e50",
            width=6,
            cursor="hand2",
            relief=tk.SUNKEN,
            borderwidth=1
        )
        self.zoom_label.pack(side=tk.LEFT, padx=2, pady=4)
        self.zoom_label.bind("<Button-1>", lambda e: self._publish_action("canvas.zoom_reset"))
        self._create_tooltip(self.zoom_label, "Zoom Reset (Klick oder Ctrl+0)")
        
        # Zoom In Button
        zoom_in_btn = tk.Button(
            self.toolbar,
            text="🔍+",
            width=3,
            command=lambda: self._publish_action("canvas.zoom", {"direction": "in"})
        )
        zoom_in_btn.pack(side=tk.LEFT, padx=2, pady=4)
        self._create_tooltip(zoom_in_btn, "Zoom In (Ctrl + Scroll ↑)")
        
        # Fit to Window Button
        fit_btn = tk.Button(
            self.toolbar,
            text="⊡",
            width=3,
            command=lambda: self._publish_action("canvas.fit_to_window")
        )
        fit_btn.pack(side=tk.LEFT, padx=4, pady=4)
        self._create_tooltip(fit_btn, "Fit to Window (Ctrl+Shift+F)")
        
        # Zoom to Selection Button
        zoom_sel_btn = tk.Button(
            self.toolbar,
            text="⊙",
            width=3,
            command=lambda: self._publish_action("canvas.zoom_to_selection")
        )
        zoom_sel_btn.pack(side=tk.LEFT, padx=2, pady=4)
        self._create_tooltip(zoom_sel_btn, "Zoom to Selection (Ctrl+Shift+Z)")
        
        # Grid Toggle Button
        self.grid_btn = tk.Button(
            self.toolbar,
            text="⊞",
            width=3,
            relief=tk.RAISED,
            command=lambda: self._publish_action("canvas.toggle_grid")
        )
        self.grid_btn.pack(side=tk.LEFT, padx=4, pady=4)
        self._create_tooltip(self.grid_btn, "Toggle Grid (Ctrl+G)")
    
    def _add_separator(self) -> None:
        """Fügt einen visuellen Separator hinzu."""
        separator = tk.Frame(self.toolbar, width=2, bg="#d0d0d0")
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=4)
    
    def _create_tooltip(self, widget: tk.Widget, text: str) -> None:
        """
        Erstellt einen Tooltip für ein Widget.
        
        Args:
            widget: Widget für Tooltip
            text: Tooltip-Text
        """
        def _on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            tooltip_label = tk.Label(
                tooltip, 
                text=text, 
                font=("Segoe UI", 9), 
                bg="#2c3e50", 
                fg="white", 
                relief=tk.SOLID, 
                borderwidth=1, 
                padx=5, 
                pady=3
            )
            tooltip_label.pack()
            widget.tooltip = tooltip
        
        def _on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                delattr(widget, 'tooltip')
        
        widget.bind("<Enter>", _on_enter)
        widget.bind("<Leave>", _on_leave)
    
    def _publish_action(self, action: str, data: Optional[dict] = None) -> None:
        """
        Publiziert eine UI-Action über den Event-Bus.
        
        Args:
            action: Action-Name (z.B. "file.new")
            data: Optionale Daten (z.B. {"mode": "left"})
        """
        event_name = f"ui:action:{action}"
        payload = data or {}
        self.event_bus.publish(event_name, payload)
    
    # Public API
    # ----------
    
    def update_zoom_level(self, zoom: float) -> None:
        """
        Aktualisiert die Zoom-Level-Anzeige.
        
        Args:
            zoom: Zoom-Faktor (1.0 = 100%)
        """
        if hasattr(self, 'zoom_label'):
            percentage = int(zoom * 100)
            self.zoom_label.config(text=f"{percentage}%")
    
    def set_grid_active(self, active: bool) -> None:
        """
        Setzt den Grid-Button-Status.
        
        Args:
            active: True wenn Grid aktiv
        """
        if hasattr(self, 'grid_btn'):
            self.grid_btn.config(relief=tk.SUNKEN if active else tk.RAISED)
    
    def hide(self) -> None:
        """Versteckt die Toolbar."""
        self.toolbar.pack_forget()
    
    def show(self) -> None:
        """Zeigt die Toolbar wieder an."""
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
    
    def is_visible(self) -> bool:
        """
        Prüft, ob die Toolbar sichtbar ist.
        
        Returns:
            True wenn sichtbar, sonst False
        """
        return bool(self.toolbar.winfo_ismapped())
    
    def set_background_color(self, color: str) -> None:
        """
        Setzt die Hintergrundfarbe der Toolbar.
        
        Args:
            color: Farbe als Hex-String (z.B. "#f2f2f2")
        """
        self.toolbar.config(bg=color)
        # Aktualisiere alle Child-Frames
        for child in self.toolbar.winfo_children():
            if isinstance(child, tk.Frame):
                child.config(bg=color)
    
    def get_background_color(self) -> str:
        """
        Gibt die aktuelle Hintergrundfarbe zurück.
        
        Returns:
            Farbe als Hex-String
        """
        return self.toolbar.cget("bg")
    
    def _create_vpb_logo_right(self) -> None:
        """Erstellt großen VPB-Schriftzug rechtsbündig (wie VERITAS-Vorbild)."""
        # VPB Schriftzug (rechtsbündig) - ohne Rahmen, große Schrift
        vpb_btn = tk.Label(
            self.toolbar,
            text="VPB",
            font=('Segoe UI', 16, 'bold'),
            foreground='#0066CC',
            bg="#f2f2f2",
            cursor='hand2',
            padx=10,
            pady=5
        )
        vpb_btn.pack(side=tk.RIGHT, padx=(5, 10))
        vpb_btn.bind('<Button-1>', lambda e: self._publish_action("help.about"))
        
        # Hover-Effekt für VPB Button
        def on_enter(e):
            vpb_btn.config(foreground='#004499')
        def on_leave(e):
            vpb_btn.config(foreground='#0066CC')
        
        vpb_btn.bind('<Enter>', on_enter)
        vpb_btn.bind('<Leave>', on_leave)
        
        # Tooltip hinzufügen
        self._create_tooltip(vpb_btn, "VPB Process Designer - Über")
    
    def __repr__(self) -> str:
        """String-Repräsentation für Debugging."""
        return f"ToolbarView(visible={self.is_visible()}, bg={self.get_background_color()})"


# Factory Functions
# ----------------

def create_toolbar(
    parent: tk.Widget,
    event_bus: Optional["EventBus"] = None
) -> ToolbarView:
    """
    Factory-Funktion zum Erstellen einer Toolbar View.
    
    Args:
        parent: Parent Tk-Widget
        event_bus: Event-Bus Instanz (optional)
    
    Returns:
        ToolbarView Instanz
    
    Beispiel:
        >>> toolbar = create_toolbar(root_window)
        >>> toolbar.hide()  # Verstecke Toolbar
        >>> toolbar.show()  # Zeige Toolbar wieder
    """
    return ToolbarView(parent, event_bus)
