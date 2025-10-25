"""Palette panel widgets for the VPB application."""

from __future__ import annotations

import json
import os
import tkinter as tk
from typing import Callable, Dict, List, Optional

__all__ = ["PaletteLoader", "PalettePanel"]


class PaletteLoader:
    """Utility for loading palette definitions from JSON files."""

    @staticmethod
    def load_all(folder: str) -> Dict[str, List[dict]]:
        data: Dict[str, List[dict]] = {"categories": []}
        try:
            if not os.path.isdir(folder):
                return data
            for name in sorted(os.listdir(folder)):
                if not name.lower().endswith(".json"):
                    continue
                path = os.path.join(folder, name)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        doc = json.load(f)
                except Exception:
                    continue
                cats = doc.get("categories", []) if isinstance(doc, dict) else []
                for cat in cats:
                    if not isinstance(cat, dict):
                        continue
                    layout_cfg = cat.get("layout") if isinstance(cat.get("layout"), dict) else {}
                    entry = {
                        "id": cat.get("id", f"cat_{len(data['categories'])}"),
                        "title": cat.get("title", "Kategorie"),
                        "items": [item for item in cat.get("items", []) if isinstance(item, dict)],
                    }
                    if layout_cfg:
                        entry["layout"] = layout_cfg
                    data["categories"].append(
                        entry
                    )
        except Exception:
            pass
        return data


class PalettePanel(tk.Frame):
    """Scrollable palette with search and reload support."""

    def __init__(
        self,
        master,
        on_pick: Optional[Callable[[dict], None]] = None,
        on_reload: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(master, width=220, bg="#f7f7f7", relief=tk.GROOVE, borderwidth=1)
        self._on_pick = on_pick
        self._on_reload = on_reload
        self._cats: List[Dict[str, object]] = []
        self._default_columns = 4
        self._min_column_width = 60  # Reduziert von 70 auf 60 für mehr Flexibilität
        self._button_wraplength = 80  # Wird dynamisch angepasst
        self._category_spacing = (0, 6)
        self._tooltip = _Tooltip(self)

        header = tk.Frame(self, bg="#f0f0f0")
        header.pack(side=tk.TOP, fill=tk.X)
        tk.Label(header, text="Palette", bg="#f0f0f0", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=6, pady=6)

        reload_cmd = self._on_reload or (lambda: None)
        tk.Button(header, text="↻", width=3, command=reload_cmd).pack(side=tk.RIGHT, padx=2, pady=4)
        tk.Button(header, text="▸▸", width=3, command=self._collapse_all_categories).pack(side=tk.RIGHT, padx=2, pady=4)
        tk.Button(header, text="▾▾", width=3, command=self._expand_all_categories).pack(side=tk.RIGHT, padx=2, pady=4)

        self._search = tk.StringVar(value="")
        entry = tk.Entry(self, textvariable=self._search)
        entry.pack(side=tk.TOP, fill=tk.X, padx=6, pady=(0, 6))
        entry.bind("<KeyRelease>", lambda _event: self._apply_filter())

        body = tk.Frame(self)
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self._canvas = tk.Canvas(body, bg="#ffffff", highlightthickness=0)
        yscroll = tk.Scrollbar(body, orient=tk.VERTICAL, command=self._canvas.yview)
        self._inner = tk.Frame(self._canvas, bg="#ffffff")
        
        # Configure-Event für scrollregion und Breite
        self._inner.bind("<Configure>", lambda _event: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        
        # Canvas-Window erstellen und ID speichern
        self._canvas_window = self._canvas.create_window((0, 0), window=self._inner, anchor="nw")
        
        self._canvas.configure(yscrollcommand=yscroll.set)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._data: Dict[str, List[dict]] = {"categories": []}
        
        # Canvas-Resize-Event: Breite des Inner-Frames anpassen
        self._canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_canvas_configure(self, event):
        """
        Wird aufgerufen, wenn der Canvas seine Größe ändert.
        Passt die Breite des Inner-Frames an die Canvas-Breite an.
        """
        # Canvas-Breite ermitteln (abzüglich Scrollbar-Breite)
        canvas_width = event.width
        
        # Inner-Frame-Breite an Canvas anpassen
        self._canvas.itemconfig(self._canvas_window, width=canvas_width)
        
        # Reflow triggern für dynamische Button-Anpassung
        self._reflow()

    def render(self, categories: List[dict]) -> None:
        self._tooltip.hide()
        for widget in list(self._inner.children.values()):
            try:
                widget.destroy()
            except Exception:
                pass
        self._cats.clear()
        self._data = {"categories": categories or []}

        for cat in self._data["categories"]:
            title = str(cat.get("title", "Kategorie"))

            layout_cfg = cat.get("layout")
            if not isinstance(layout_cfg, dict):
                layout_cfg = {}
            try:
                preferred_columns = int(layout_cfg.get("columns", self._default_columns))
            except Exception:
                preferred_columns = self._default_columns
            preferred_columns = max(1, preferred_columns)
            expanded_raw = layout_cfg.get("expanded")
            expanded = bool(expanded_raw) if expanded_raw is not None else True

            container = tk.Frame(self._inner, bg="#ffffff")
            container.pack(fill=tk.BOTH, expand=True, padx=0, pady=(6, 0))

            header = tk.Frame(container, bg="#e8e8e8")
            header.pack(fill=tk.X)
            toggle_label = tk.Label(header, text="▼" if expanded else "►", width=2, bg="#e8e8e8", font=("Segoe UI", 10, "bold"))
            toggle_label.pack(side=tk.LEFT, padx=(6, 2), pady=4)
            title_label = tk.Label(header, text=title, anchor="w", bg="#e8e8e8", font=("Segoe UI", 9, "bold"))
            title_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=4)

            pack_opts = {"fill": tk.BOTH, "expand": True, "padx": 4, "pady": self._category_spacing}
            grid = tk.Frame(container, bg="#ffffff")
            grid.pack(**pack_opts)

            cat_entry: Dict[str, object] = {
                "container": container,
                "header": header,
                "toggle": toggle_label,
                "header_widgets": (header, toggle_label, title_label),
                "frame": grid,
                "buttons": [],
                "columns": preferred_columns,
                "expanded": expanded,
                "has_visible": True,
                "pack_opts": pack_opts,
            }

            def _bind_toggle(widget: tk.Misc, entry: Dict[str, object]) -> None:
                try:
                    widget.bind("<Button-1>", lambda _event, e=entry: self._toggle_category(e))
                except Exception:
                    pass

            _bind_toggle(header, cat_entry)
            _bind_toggle(toggle_label, cat_entry)
            _bind_toggle(title_label, cat_entry)

            buttons: List[Dict[str, object]] = []
            items = cat.get("items", [])
            for item in items:
                symbol = str(item.get("symbol")) if item.get("symbol") else self._symbol_for_type(str(item.get("type", "")))
                label = f"{symbol} {item.get('name', item.get('type', '?'))}".strip()
                button = tk.Button(
                    grid,
                    text=label,
                    command=lambda item=item: self._pick(item),
                    wraplength=self._button_wraplength,
                    justify="left",
                    anchor="w",
                )
                # Button-Breite wird dynamisch im _reflow() gesetzt
                fill = item.get("fill")
                if isinstance(fill, str) and fill:
                    try:
                        button.configure(bg=fill, activebackground=fill)
                    except Exception:
                        pass
                text_color = item.get("text_color")
                if isinstance(text_color, str) and text_color:
                    try:
                        button.configure(fg=text_color)
                    except Exception:
                        pass
                tooltip_text = self._build_tooltip_text(item)
                if tooltip_text:
                    button.bind("<Enter>", lambda event, text=tooltip_text: self._on_button_enter(event, text))
                    button.bind("<Leave>", lambda _event: self._hide_tooltip())
                    button.bind("<Motion>", lambda event, text=tooltip_text: self._on_button_motion(event, text))
                buttons.append({"widget": button, "item": item, "visible": True, "tooltip": tooltip_text})

            cat_entry["buttons"] = buttons
            self._cats.append(cat_entry)

            if not expanded:
                try:
                    grid.pack_forget()
                except Exception:
                    pass

        self._apply_filter()
        self._reflow()

    def _expand_all_categories(self) -> None:
        self._hide_tooltip()
        any_change = False
        for entry in self._cats:
            if not entry.get("expanded", True) or not self._is_frame_packed(entry):
                self._set_category_expanded(entry, True)
                frame = entry.get("frame")
                if isinstance(frame, tk.Frame):
                    frame.pack(**(entry.get("pack_opts") or {"fill": tk.BOTH, "expand": True, "padx": 4, "pady": self._category_spacing}))
                any_change = True
        if any_change:
            self._reflow()

    def _collapse_all_categories(self) -> None:
        self._hide_tooltip()
        query_active = bool(self._search.get().strip())
        collapsed = False
        for entry in self._cats:
            if query_active and entry.get("has_visible", False):
                continue
            if entry.get("expanded", True) or self._is_frame_packed(entry):
                self._set_category_expanded(entry, False)
                frame = entry.get("frame")
                if isinstance(frame, tk.Frame):
                    try:
                        frame.pack_forget()
                    except Exception:
                        pass
                collapsed = True
        if collapsed:
            self._reflow()

    def _symbol_for_type(self, element_type: str) -> str:
        mapping = {
            "START_EVENT": "⭘",
            "END_EVENT": "⦿",
            "EVENT": "⭘",
            "FUNCTION": "▭",
            "ORGANIZATION_UNIT": "▭",
            "INFORMATION_OBJECT": "◆",
            "AND_CONNECTOR": "●",
            "OR_CONNECTOR": "●",
            "XOR_CONNECTOR": "◆",
            "GATEWAY": "◆",
            "SUBPROCESS": "▭",
            "LEGAL_CHECKPOINT": "⚖",
            "DEADLINE": "⏱",
            "COMPETENCY_CHECK": "🏛",
            "GEO_CONTEXT": "📍",
            "GROUP": "▢",
            "TIME_LOOP": "⟳",  # NEU: Kreispfeil für Wiederholung
            "TIMER": "⏰",      # NEU: Wecker/Uhr-Symbol
            "SEQUENCE": "➝",
            "MESSAGE": "✉",
            "ASSOCIATION": "－",
            "LEGAL": "⚖",
            "APPROVAL": "✔",
            "REJECTION": "✖",
            "DOCUMENT": "📄",
            "NOTIFICATION": "🔔",
            "ESCALATION": "⬆",
            "GEO_REF": "📍",
        }
        return mapping.get(element_type.upper(), "•")

    def _build_tooltip_text(self, item: dict) -> Optional[str]:
        reference = item.get("reference") if isinstance(item.get("reference"), dict) else {}
        description = reference.get("description") or item.get("description")
        authority = reference.get("responsible_authority") or item.get("responsible_authority")
        legal_basis = reference.get("legal_basis") or item.get("legal_basis")
        deadline = reference.get("deadline_days") if reference.get("deadline_days") not in (None, "") else item.get("deadline_days")

        parts: List[str] = []
        if description:
            parts.append(str(description))
        if authority:
            parts.append(f"Zuständig: {authority}")
        if legal_basis:
            parts.append(f"Rechtsgrundlage: {legal_basis}")
        if isinstance(deadline, (int, float)) and deadline > 0:
            parts.append(f"Frist (Tage): {int(deadline)}")
        elif isinstance(deadline, str) and deadline.strip():
            parts.append(f"Frist: {deadline}")

        return "\n".join(parts) if parts else None

    def _on_button_enter(self, event, text: str) -> None:
        self._tooltip.show(event.x_root + 14, event.y_root + 12, text)

    def _on_button_motion(self, event, text: str) -> None:
        self._tooltip.move(event.x_root + 14, event.y_root + 12, text)

    def _hide_tooltip(self) -> None:
        self._tooltip.hide()

    def _toggle_category(self, entry: Dict[str, object]) -> None:
        expanded = bool(entry.get("expanded", True))
        self._set_category_expanded(entry, not expanded, user_action=True)

    def _set_category_expanded(self, entry: Dict[str, object], expanded: bool, *, user_action: bool = False) -> None:
        if entry.get("expanded", True) == expanded:
            if expanded and entry.get("has_visible", True):
                self._pack_category_frame(entry)
            return
        entry["expanded"] = expanded
        toggle = entry.get("toggle")
        if isinstance(toggle, tk.Label):
            try:
                toggle.configure(text="▼" if expanded else "►")
            except Exception:
                pass
        if expanded and entry.get("has_visible", True):
            self._pack_category_frame(entry)
        else:
            frame = entry.get("frame")
            if isinstance(frame, tk.Frame):
                try:
                    frame.pack_forget()
                except Exception:
                    pass
        if user_action:
            self.after_idle(self._reflow)

    def _pack_category_frame(self, entry: Dict[str, object]) -> None:
        frame = entry.get("frame")
        opts = entry.get("pack_opts") if isinstance(entry.get("pack_opts"), dict) else None
        if isinstance(frame, tk.Frame):
            if not frame.winfo_manager():
                try:
                    frame.pack(**(opts or {"fill": tk.BOTH, "expand": True, "padx": 4, "pady": self._category_spacing}))
                except Exception:
                    frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=self._category_spacing)

    def _is_frame_packed(self, entry: Dict[str, object]) -> bool:
        frame = entry.get("frame")
        if isinstance(frame, tk.Frame):
            return bool(frame.winfo_manager())
        return False

    def _reflow(self) -> None:
        try:
            available = max(1, int(self._canvas.winfo_width() or 220))
        except Exception:
            available = 220
        
        for cat in self._cats:
            frame = cat.get("frame")
            if not isinstance(frame, tk.Frame):
                continue
            buttons = cat.get("buttons", [])
            for info in buttons:
                widget = info.get("widget") if isinstance(info, dict) else None
                if hasattr(widget, "grid_forget"):
                    widget.grid_forget()
            
            try:
                preferred_columns = int(cat.get("columns", self._default_columns))
            except Exception:
                preferred_columns = self._default_columns
            preferred_columns = max(1, preferred_columns)
            
            # Dynamische Spaltenberechnung basierend auf verfügbarer Breite
            # Abzüglich Padding und Scrollbar
            effective_width = available - 20  # 20px für Scrollbar und Padding
            max_columns = max(1, effective_width // self._min_column_width)
            columns = max(1, min(preferred_columns, max_columns))
            
            # Dynamische Button-Breite und wraplength basierend auf Spaltenanzahl
            button_width = (effective_width // columns) - 10  # 10px für padx
            wraplength = max(50, button_width - 10)  # wraplength etwas kleiner als Button-Breite
            
            visible_buttons = [b for b in buttons if isinstance(b, dict) and b.get("visible", True)]
            for index, info in enumerate(visible_buttons):
                widget = info.get("widget") if isinstance(info, dict) else None
                if not hasattr(widget, "grid"):
                    continue
                
                # Aktualisiere Button-Eigenschaften dynamisch
                try:
                    widget.configure(wraplength=wraplength)
                except Exception:
                    pass
                
                row = index // columns
                column = index % columns
                widget.grid(row=row, column=column, padx=2, pady=2, sticky="nsew")
            
            for column_index in range(columns):
                try:
                    frame.columnconfigure(column_index, weight=1, uniform="button")
                except Exception:
                    pass

    def _apply_filter(self) -> None:
        self._hide_tooltip()
        query = self._search.get().strip().lower()
        for cat in self._cats:
            buttons = cat.get("buttons", [])
            visible_any = False
            for info in buttons:
                widget = info.get("widget") if isinstance(info, dict) else None
                if not widget:
                    continue
                try:
                    label = str(widget["text"]).lower()
                    match = (query in label) if query else True
                except Exception:
                    match = True
                info["visible"] = match
                if match:
                    visible_any = True

            cat["has_visible"] = visible_any

            if query and visible_any and not cat.get("expanded", True):
                self._set_category_expanded(cat, True)

            frame = cat.get("frame")
            if isinstance(frame, tk.Frame):
                if cat.get("expanded", True) and visible_any:
                    self._pack_category_frame(cat)
                else:
                    try:
                        frame.pack_forget()
                    except Exception:
                        pass

            header_widgets = cat.get("header_widgets")
            if isinstance(header_widgets, (list, tuple)):
                bg = "#e8e8e8" if visible_any or not query else "#f3f3f3"
                for widget in header_widgets:
                    if hasattr(widget, "configure"):
                        try:
                            widget.configure(bg=bg)
                        except Exception:
                            pass

        self._reflow()

    def _pick(self, item: dict) -> None:
        self._hide_tooltip()
        if not self._on_pick:
            return
        try:
            self._on_pick(item)
        except Exception:
            pass


class _Tooltip:
    """Simple tooltip helper bound to the palette panel."""

    def __init__(self, master: tk.Misc) -> None:
        self._master = master
        self._window: Optional[tk.Toplevel] = None
        self._label: Optional[tk.Label] = None

    def show(self, x: int, y: int, text: str) -> None:
        if not text:
            self.hide()
            return
        if self._window is None:
            self._window = tk.Toplevel(self._master)
            self._window.wm_overrideredirect(True)
            try:
                self._window.attributes("-topmost", True)
            except Exception:
                pass
            self._label = tk.Label(
                self._window,
                text=text,
                justify="left",
                background="#ffffe0",
                relief=tk.SOLID,
                borderwidth=1,
                font=("Segoe UI", 8),
                padx=6,
                pady=4,
                wraplength=260,
            )
            self._label.pack()
        elif self._label is not None:
            try:
                self._label.configure(text=text)
            except Exception:
                pass
        self.move(x, y, text)

    def move(self, x: int, y: int, text: str | None = None) -> None:
        if self._window is None:
            if text:
                self.show(x, y, text)
            return
        try:
            self._window.geometry(f"+{x}+{y}")
        except Exception:
            pass

    def hide(self) -> None:
        if self._window is not None:
            try:
                self._window.destroy()
            except Exception:
                pass
            finally:
                self._window = None
                self._label = None
