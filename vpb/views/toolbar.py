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
from vpb.ui.theme import get_theme_manager
from vpb.ui.icons import get_icon_manager
from vpb.ui.fonts import get_font_manager
from vpb.ui.spacing import get_spacing_manager

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
        
        # UI Managers
        self.theme = get_theme_manager()
        self.icons = get_icon_manager()
        self.fonts = get_font_manager()
        self.spacing = get_spacing_manager()
        
        # Toolbar Frame erstellen mit Theme
        toolbar_bg = self.theme.get_color("toolbar_bg")
        toolbar_height = self.spacing.get_spacing("xl") + 8  # 40px
        self.toolbar = tk.Frame(parent, bg=toolbar_bg, height=toolbar_height)
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
        """Erstellt Datei-Buttons (Neu, Öffnen, Speichern) mit Icons."""
        file_buttons = [
            (self.icons.get("new"), "Neu", "file.new", "Neues Dokument (Strg+N)"),
            (self.icons.get("open"), "Öffnen", "file.open", "Dokument öffnen (Strg+O)"),
            (self.icons.get("save"), "Speichern", "file.save", "Speichern (Strg+S)"),
            (self.icons.get("save_as"), "Speichern unter", "file.save_as", "Speichern unter (Strg+Shift+S)"),
        ]
        
        toolbar_bg = self.theme.get_color("toolbar_bg")
        text_color = self.theme.get_color("text_primary")
        btn_font = self.fonts.get("button")
        
        for icon, text, action, tooltip in file_buttons:
            btn = tk.Button(
                self.toolbar,
                text=f"{icon} {text}",
                font=btn_font,
                bg=toolbar_bg,
                fg=text_color,
                relief=tk.FLAT,
                borderwidth=1,
                padx=8,
                pady=4,
                cursor="hand2",
                command=lambda a=action: self._publish_action(a)
            )
            btn.pack(side=tk.LEFT, padx=4, pady=4)
            self._create_tooltip(btn, tooltip)
            
            # Hover-Effekt
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.theme.get_color("bg_hover"), relief=tk.RAISED))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=toolbar_bg, relief=tk.FLAT))
    
    def _create_edit_buttons(self) -> None:
        """Erstellt Edit-Buttons (Element hinzufügen, Neu zeichnen, Auto-Layout) mit Icons."""
        toolbar_bg = self.theme.get_color("toolbar_bg")
        text_color = self.theme.get_color("text_primary")
        btn_font = self.fonts.get("button")
        
        edit_buttons = [
            (self.icons.get("add_element"), "Element", "edit.add_element", "Element hinzufügen"),
            (self.icons.get("refresh"), "Neu zeichnen", "edit.redraw", "Canvas neu zeichnen"),
            (self.icons.get("settings"), "Auto-Layout", "edit.auto_layout", "Automatisches Layout"),
        ]
        
        for icon, text, action, tooltip in edit_buttons:
            btn = tk.Button(
                self.toolbar,
                text=f"{icon} {text}",
                font=btn_font,
                bg=toolbar_bg,
                fg=text_color,
                relief=tk.FLAT,
                borderwidth=1,
                padx=8,
                pady=4,
                cursor="hand2",
                command=lambda a=action: self._publish_action(a)
            )
            btn.pack(side=tk.LEFT, padx=4, pady=4)
            self._create_tooltip(btn, tooltip)
            
            # Hover-Effekt
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.theme.get_color("bg_hover"), relief=tk.RAISED))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=toolbar_bg, relief=tk.FLAT))
        
        # Separator
        self._add_separator()
        
        # Gruppierungs-Buttons mit verbesserten Icons
        group_buttons = [
            (self.icons.get("group"), "Gruppe bilden", "edit.group", "Gruppe bilden"),
            (self.icons.get("rotate_right"), "Zeitschleife", "edit.time_loop", "Zeitschleife bilden"),
            (self.icons.get("ungroup"), "Auflösen", "edit.ungroup", "Gruppe auflösen"),
        ]
        
        for icon, text, action, tooltip in group_buttons:
            btn = tk.Button(
                self.toolbar,
                text=f"{icon} {text}",
                font=btn_font,
                bg=toolbar_bg,
                fg=text_color,
                relief=tk.FLAT,
                borderwidth=1,
                padx=8,
                pady=4,
                cursor="hand2",
                command=lambda a=action: self._publish_action(a)
            )
            btn.pack(side=tk.LEFT, padx=4, pady=4)
            self._create_tooltip(btn, tooltip)
            
            # Hover-Effekt
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.theme.get_color("bg_hover"), relief=tk.RAISED))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=toolbar_bg, relief=tk.FLAT))
    
    def _create_arrange_menus(self) -> None:
        """Erstellt Anordnen-Menüs (Ausrichten, Verteilen, Formationen) mit Icons."""
        toolbar_bg = self.theme.get_color("toolbar_bg")
        text_color = self.theme.get_color("text_primary")
        btn_font = self.fonts.get("button")
        
        # Ausrichten-Menü
        align_menu = tk.Menubutton(
            self.toolbar,
            text=f"{self.icons.get('align_center')} Ausrichten",
            font=btn_font,
            bg=toolbar_bg,
            fg=text_color,
            relief=tk.FLAT,
            borderwidth=1,
            padx=8,
            pady=4,
            cursor="hand2"
        )
        align_menu.menu = tk.Menu(align_menu, tearoff=0)
        align_menu["menu"] = align_menu.menu
        
        align_menu.menu.add_command(
            label=f"{self.icons.get('align_left')} Links",
            command=lambda: self._publish_action("arrange.align", {"mode": "left"})
        )
        align_menu.menu.add_command(
            label=f"{self.icons.get('align_center')} Horizontal zentrieren",
            command=lambda: self._publish_action("arrange.align", {"mode": "center"})
        )
        align_menu.menu.add_command(
            label=f"{self.icons.get('align_right')} Rechts",
            command=lambda: self._publish_action("arrange.align", {"mode": "right"})
        )
        align_menu.menu.add_separator()
        align_menu.menu.add_command(
            label=f"{self.icons.get('align_top')} Oben",
            command=lambda: self._publish_action("arrange.align", {"mode": "top"})
        )
        align_menu.menu.add_command(
            label=f"{self.icons.get('align_middle')} Vertikal mittig",
            command=lambda: self._publish_action("arrange.align", {"mode": "middle"})
        )
        align_menu.menu.add_command(
            label=f"{self.icons.get('align_bottom')} Unten",
            command=lambda: self._publish_action("arrange.align", {"mode": "bottom"})
        )
        
        align_menu.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Hover-Effekt für Menubutton
        align_menu.bind("<Enter>", lambda e: align_menu.config(bg=self.theme.get_color("bg_hover"), relief=tk.RAISED))
        align_menu.bind("<Leave>", lambda e: align_menu.config(bg=toolbar_bg, relief=tk.FLAT))
        
        # Verteilen-Menü
        distribute_menu = tk.Menubutton(
            self.toolbar,
            text=f"{self.icons.get('distribute_h')} Verteilen",
            font=btn_font,
            bg=toolbar_bg,
            fg=text_color,
            relief=tk.FLAT,
            borderwidth=1,
            padx=8,
            pady=4,
            cursor="hand2"
        )
        distribute_menu.menu = tk.Menu(distribute_menu, tearoff=0)
        distribute_menu["menu"] = distribute_menu.menu
        
        distribute_menu.menu.add_command(
            label=f"{self.icons.get('distribute_h')} Horizontal",
            command=lambda: self._publish_action("arrange.distribute", {"mode": "horizontal"})
        )
        distribute_menu.menu.add_command(
            label=f"{self.icons.get('distribute_v')} Vertikal",
            command=lambda: self._publish_action("arrange.distribute", {"mode": "vertical"})
        )
        
        distribute_menu.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Hover-Effekt
        distribute_menu.bind("<Enter>", lambda e: distribute_menu.config(bg=self.theme.get_color("bg_hover"), relief=tk.RAISED))
        distribute_menu.bind("<Leave>", lambda e: distribute_menu.config(bg=toolbar_bg, relief=tk.FLAT))
        
        # Formationen-Menü
        formations_menu = tk.Menubutton(
            self.toolbar,
            text=f"{self.icons.get('rotate_right')} Formationen",
            font=btn_font,
            bg=toolbar_bg,
            fg=text_color,
            relief=tk.FLAT,
            borderwidth=1,
            padx=8,
            pady=4,
            cursor="hand2"
        )
        formations_menu.menu = tk.Menu(formations_menu, tearoff=0)
        formations_menu["menu"] = formations_menu.menu
        
        formations_menu.menu.add_command(
            label=f"⭕ Kreis anordnen",
            command=lambda: self._publish_action("arrange.formation", {"mode": "circular"})
        )
        
        formations_menu.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Hover-Effekt
        formations_menu.bind("<Enter>", lambda e: formations_menu.config(bg=self.theme.get_color("bg_hover"), relief=tk.RAISED))
        formations_menu.bind("<Leave>", lambda e: formations_menu.config(bg=toolbar_bg, relief=tk.FLAT))
    
    def _create_canvas_controls(self) -> None:
        """Erstellt Canvas-Kontroll-Elemente (Zoom, Pan, Fit) mit Icons."""
        toolbar_bg = self.theme.get_color("toolbar_bg")
        text_color = self.theme.get_color("text_primary")
        btn_font = self.fonts.get("button")
        
        # Zoom Out Button
        zoom_out_btn = tk.Button(
            self.toolbar,
            text=self.icons.get("zoom_out"),
            font=btn_font,
            width=3,
            bg=toolbar_bg,
            fg=text_color,
            relief=tk.FLAT,
            borderwidth=1,
            cursor="hand2",
            command=lambda: self._publish_action("canvas.zoom", {"direction": "out"})
        )
        zoom_out_btn.pack(side=tk.LEFT, padx=2, pady=4)
        self._create_tooltip(zoom_out_btn, "Zoom Out (Strg + Scroll ↓)")
        
        # Hover-Effekt
        zoom_out_btn.bind("<Enter>", lambda e: zoom_out_btn.config(bg=self.theme.get_color("bg_hover"), relief=tk.RAISED))
        zoom_out_btn.bind("<Leave>", lambda e: zoom_out_btn.config(bg=toolbar_bg, relief=tk.FLAT))
        
        # Zoom-Level Anzeige/Reset
        self.zoom_label = tk.Label(
            self.toolbar,
            text="100%",
            font=self.fonts.get("statusbar"),
            bg=self.theme.get_color("bg_secondary"),
            fg=text_color,
            width=6,
            cursor="hand2",
            relief=tk.SUNKEN,
            borderwidth=1
        )
        self.zoom_label.pack(side=tk.LEFT, padx=2, pady=4)
        self.zoom_label.bind("<Button-1>", lambda e: self._publish_action("canvas.zoom_reset"))
        self._create_tooltip(self.zoom_label, "Zoom Reset (Klick oder Strg+0)")
        
        # Zoom In Button
        zoom_in_btn = tk.Button(
            self.toolbar,
            text=self.icons.get("zoom_in"),
            font=btn_font,
            width=3,
            bg=toolbar_bg,
            fg=text_color,
            relief=tk.FLAT,
            borderwidth=1,
            cursor="hand2",
            command=lambda: self._publish_action("canvas.zoom", {"direction": "in"})
        )
        zoom_in_btn.pack(side=tk.LEFT, padx=2, pady=4)
        self._create_tooltip(zoom_in_btn, "Zoom In (Strg + Scroll ↑)")
        
        # Hover-Effekt
        zoom_in_btn.bind("<Enter>", lambda e: zoom_in_btn.config(bg=self.theme.get_color("bg_hover"), relief=tk.RAISED))
        zoom_in_btn.bind("<Leave>", lambda e: zoom_in_btn.config(bg=toolbar_bg, relief=tk.FLAT))
        
        # Fit to Window Button
        fit_btn = tk.Button(
            self.toolbar,
            text=self.icons.get("zoom_fit"),
            font=btn_font,
            width=3,
            bg=toolbar_bg,
            fg=text_color,
            relief=tk.FLAT,
            borderwidth=1,
            cursor="hand2",
            command=lambda: self._publish_action("canvas.fit_to_window")
        )
        fit_btn.pack(side=tk.LEFT, padx=4, pady=4)
        self._create_tooltip(fit_btn, "Fit to Window (Strg+Shift+F)")
        
        # Hover-Effekt
        fit_btn.bind("<Enter>", lambda e: fit_btn.config(bg=self.theme.get_color("bg_hover"), relief=tk.RAISED))
        fit_btn.bind("<Leave>", lambda e: fit_btn.config(bg=toolbar_bg, relief=tk.FLAT))
        
        # Zoom to Selection Button
        zoom_sel_btn = tk.Button(
            self.toolbar,
            text=self.icons.get("zoom_100"),
            font=btn_font,
            width=3,
            bg=toolbar_bg,
            fg=text_color,
            relief=tk.FLAT,
            borderwidth=1,
            cursor="hand2",
            command=lambda: self._publish_action("canvas.zoom_to_selection")
        )
        zoom_sel_btn.pack(side=tk.LEFT, padx=2, pady=4)
        self._create_tooltip(zoom_sel_btn, "Zoom to Selection (Strg+Shift+Z)")
        
        # Hover-Effekt
        zoom_sel_btn.bind("<Enter>", lambda e: zoom_sel_btn.config(bg=self.theme.get_color("bg_hover"), relief=tk.RAISED))
        zoom_sel_btn.bind("<Leave>", lambda e: zoom_sel_btn.config(bg=toolbar_bg, relief=tk.FLAT))
        
        # Grid Toggle Button
        self.grid_btn = tk.Button(
            self.toolbar,
            text=self.icons.get("grid"),
            font=btn_font,
            width=3,
            bg=toolbar_bg,
            fg=text_color,
            relief=tk.FLAT,
            borderwidth=1,
            cursor="hand2",
            command=lambda: self._publish_action("canvas.toggle_grid")
        )
        self.grid_btn.pack(side=tk.LEFT, padx=4, pady=4)
        self._create_tooltip(self.grid_btn, "Toggle Grid (Strg+G)")
        
        # Hover-Effekt
        self.grid_btn.bind("<Enter>", lambda e: self.grid_btn.config(bg=self.theme.get_color("bg_hover"), relief=tk.RAISED))
        self.grid_btn.bind("<Leave>", lambda e: self.grid_btn.config(bg=toolbar_bg, relief=tk.FLAT))
    
    def _add_separator(self) -> None:
        """Fügt einen visuellen Separator hinzu."""
        separator_color = self.theme.get_color("toolbar_separator")
        separator = tk.Frame(self.toolbar, width=2, bg=separator_color)
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
            
            # Theme-Farben für Tooltip
            bg_color = self.theme.get_color("bg_dark")
            text_color = self.theme.get_color("text_inverse")
            tooltip_font = self.fonts.get("tooltip")
            
            tooltip_label = tk.Label(
                tooltip,
                text=text,
                font=tooltip_font,
                bg=bg_color,
                fg=text_color,
                relief=tk.SOLID,
                borderwidth=1,
                padx=6,
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
        """Erstellt großen VPB-Schriftzug rechtsbündig mit Theme-Farben."""
        toolbar_bg = self.theme.get_color("toolbar_bg")
        primary_color = self.theme.get_color("primary")
        primary_hover = self.theme.get_color("primary_hover")
        
        # VPB Schriftzug (rechtsbündig) - ohne Rahmen, große Schrift
        vpb_btn = tk.Label(
            self.toolbar,
            text="VPB",
            font=self.fonts.get("heading_2"),
            foreground=primary_color,
            bg=toolbar_bg,
            cursor='hand2',
            padx=10,
            pady=5
        )
        vpb_btn.pack(side=tk.RIGHT, padx=(5, 10))
        vpb_btn.bind('<Button-1>', lambda e: self._publish_action("help.about"))
        
        # Hover-Effekt für VPB Button
        def on_enter(e):
            vpb_btn.config(foreground=primary_hover)
        def on_leave(e):
            vpb_btn.config(foreground=primary_color)
        
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
