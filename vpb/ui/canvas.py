from __future__ import annotations

import json
import os
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

import heapq
import math

import tkinter as tk
from tkinter import messagebox, simpledialog

from vpb.models import VPBConnection, VPBElement
from vpb.styles import CONNECTION_STYLES, ELEMENT_STYLES


# -------- Zeichen-Helfer --------

def _diamond_points(cx: int, cy: int, w: int, h: int) -> List[int]:
    return [cx, cy - h // 2, cx + w // 2, cy, cx, cy + h // 2, cx - w // 2, cy]


def _hex_points(cx: int, cy: int, w: int, h: int) -> List[int]:
    # regelmäßiges Hexagon in Bounding-Box
    dx = w // 2
    dy = h // 2
    return [
        cx - dx // 2, cy - dy,
        cx + dx // 2, cy - dy,
        cx + dx, cy,
        cx + dx // 2, cy + dy,
        cx - dx // 2, cy + dy,
        cx - dx, cy,
    ]


def _lighten_hex(color: str, factor: float = 0.5) -> Optional[str]:
    if not color:
        return None
    color = color.strip()
    if not color:
        return None
    if color.startswith('#'):
        color = color[1:]
    if len(color) not in (6, 3):
        return None
    if len(color) == 3:
        color = ''.join(ch * 2 for ch in color)
    try:
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
    except ValueError:
        return None
    factor = max(0.0, min(1.0, factor))
    r = int(round(r + (255 - r) * factor))
    g = int(round(g + (255 - g) * factor))
    b = int(round(b + (255 - b) * factor))
    return f"#{r:02x}{g:02x}{b:02x}"


def _normalize_hex_color(color: Optional[str]) -> Optional[str]:
    if color is None:
        return None
    value = str(color).strip()
    if not value:
        return None
    if value.startswith('#'):
        value = value[1:]
    if len(value) == 3:
        value = ''.join(ch * 2 for ch in value)
    if len(value) != 6:
        return None
    try:
        int(value, 16)
    except ValueError:
        return None
    return f"#{value.lower()}"


def _hex_to_rgb(color: Optional[str]) -> Optional[Tuple[int, int, int]]:
    normalized = _normalize_hex_color(color)
    if not normalized:
        return None
    value = normalized[1:]
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16))


def _relative_luminance(color: Optional[str]) -> Optional[float]:
    rgb = _hex_to_rgb(color)
    if not rgb:
        return None

    def _channel(component: int) -> float:
        c = component / 255.0
        if c <= 0.03928:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    r_lin = _channel(r)
    g_lin = _channel(g)
    b_lin = _channel(b)
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def _contrast_ratio(color_a: Optional[str], color_b: Optional[str]) -> Optional[float]:
    lum_a = _relative_luminance(color_a)
    lum_b = _relative_luminance(color_b)
    if lum_a is None or lum_b is None:
        return None
    lighter = max(lum_a, lum_b)
    darker = min(lum_a, lum_b)
    return (lighter + 0.05) / (darker + 0.05)


def _best_contrast_color(base_color: Optional[str], candidates: Iterable[str], default: str = "#000000") -> str:
    base = _normalize_hex_color(base_color) or "#ffffff"
    best_color = _normalize_hex_color(default) or "#000000"
    best_ratio = -1.0
    for candidate in candidates:
        normalized = _normalize_hex_color(candidate)
        if not normalized:
            continue
        ratio = _contrast_ratio(base, normalized)
        if ratio is None:
            continue
        if ratio > best_ratio:
            best_ratio = ratio
            best_color = normalized
    return best_color


# -------- Haupt-Canvas --------

class VPBCanvas(tk.Canvas):
    NODE_W = 150
    NODE_H = 60

    def __init__(self, master: tk.Widget, **kwargs):
        super().__init__(master, background="#ffffff", highlightthickness=0, **kwargs)
        self.elements: Dict[str, VPBElement] = {}
        self.connections: Dict[str, VPBConnection] = {}
        self._id_to_element: Dict[int, str] = {}
        self._id_to_connection: Dict[int, str] = {}
        self._drag_state: Optional[Tuple[str, int, int]] = None  # (element_id, dx, dy)
        self.selected_id: Optional[str] = None
        self.selected_ids: set[str] = set()
        self.selected_conn_id: Optional[str] = None
        self.link_mode: bool = False
        self.link_source_id: Optional[str] = None
        # Link-Modus: gewählter Verbindungstyp/Pfeilstil aus der Palette
        self._link_connection_type: Optional[str] = None
        self._link_arrow_style: Optional[str] = None
        self.default_connection_routing: str = "auto"
        self.connection_magnet_enabled: bool = True
        self.connection_magnet_step: int = 20
        self.snap_to_grid: bool = True
        self.grid_size = 25
        self.grid_visible = True
        self.on_selection_changed: Optional[Callable[[Optional[VPBElement], Optional[VPBConnection]], None]] = None
        self._status_cb: Optional[Callable[[str], None]] = None
        self.metadata: Dict[str, object] = {"name": "VPB Prozess", "version": "1.0"}
        # Basisverzeichnis für SUBPROCESS-Referenzen
        self.base_dir: str = os.getcwd()
        self._expanded_subprocesses: set[str] = set()
        self.ref_preview_limit: int = 20000

        # Add-Modus (Palette)
        self.add_mode: bool = False
        self._add_element_type: Optional[str] = None
        self._add_element_name: Optional[str] = None
        self._add_element_payload: Optional[Dict[str, Any]] = None

        # View Transform (Zoom/Pan)
        self.view_scale: float = 1.0
        self.view_tx: float = 0.0
        self.view_ty: float = 0.0
        self._pan_last: Optional[Tuple[int, int]] = None
        self._min_zoom: float = 0.1
        self._max_zoom: float = 5.0
        # Verbindungslinien-Routing
        self.routing_style: str = "smart"  # 'straight' | 'orthogonal' | 'curved' | 'smart'
        # Navigation (Pan) Schrittgrößen in Pixeln
        self.pan_step_small_px: int = 30
        self.pan_step_big_px: int = 60
        # Mausrad-Verhalten ("zoom-primary" | "pan-primary")
        self.mousewheel_mode: str = "zoom-primary"
        # Multi-drag state
        self._drag_multi: Optional[Dict[str, Tuple[int, int]]] = None  # eid -> (dx, dy) in model coords

        # Callback für View-Änderungen (Lineale/Scrollbars)
        self.on_view_changed: Optional[Callable[[], None]] = None  # legacy single-callback
        self._view_changed_listeners: List[Callable[[], None]] = []

        # Undo/Redo History
        self._undo_stack: List[Dict] = []
        self._redo_stack: List[Dict] = []
        self._max_history: int = 50

        # Stil-Overrides (global) und Palette-Defaults pro Elementtyp
        self.element_style_overrides = {}
        self.element_style_palette_defaults = {}

        # Temporäre Highlights (z. B. nach Merge/Patch)
        self._temp_highlight_elements: Dict[str, str] = {}
        self._temp_highlight_connections: Dict[str, str] = {}
        self._temp_highlight_after: Optional[str] = None
        self._hierarchy_color_cache: Dict[str, Tuple[Optional[str], Optional[str]]] = {}

        # Zeitachse (horizontal) Einstellungen
        self.time_axis_enabled = True
        self.time_axis_interval = 100.0  # Model-Einheiten pro Tick
        # Hand-Tool Status (Space zum temporären Pannen)
        self._space_pan_active: bool = False
        self._connection_points_cache: Dict[str, List[int]] = {}
        self._collapsed_redirect: Dict[str, str] = {}
        self.ref_refresh_interval_ms = 2000  # type: int
        self._ref_refresh_job = None  # type: Optional[str]
        self._schedule_ref_refresh()
        
        # Zeitachsen-Farbe
        self.time_axis_color = "#2d7ff9"

        # Hierarchie-Kategorien (für HierarchyBar genutzt)
        # Liste von Dicts: {name: str, y0: float, y1: float, color: str}
        self.hierarchy_categories = []
        # Wenn True, zeichnet ein externes Canvas (HierarchyCanvas) die Leiste; intern dann nicht zeichnen
        self.hierarchy_external: bool = True

        # Bindings
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Double-Button-1>", self._on_double_click)
        # Rechtsklick
        self.bind("<Button-3>", self._on_right_click)
        # Multi-Select (Shift-Klick)
        self.bind("<Shift-ButtonPress-1>", self._on_shift_press)
        # Zoom & Pan
        self.bind("<MouseWheel>", self._on_mousewheel_primary)
        self.bind("<Control-MouseWheel>", self._on_mousewheel_ctrl)
        self.bind("<Button-4>", self._on_mousewheel_primary)
        self.bind("<Button-5>", self._on_mousewheel_primary)
        self.bind("<Control-Button-4>", self._on_mousewheel_ctrl)
        self.bind("<Control-Button-5>", self._on_mousewheel_ctrl)
        self.bind("<ButtonPress-2>", self._on_pan_start)
        self.bind("<B2-Motion>", self._on_pan_move)
        self.bind("<ButtonRelease-2>", self._on_pan_end)
        # Alternativen ohne mittlere Maustaste
        # 1) Alt + Linke Maustaste gedrückt halten → Pannen
        self.bind("<Alt-ButtonPress-1>", self._on_pan_start)
        self.bind("<Alt-B1-Motion>", self._on_pan_move)
        self.bind("<Alt-ButtonRelease-1>", self._on_pan_end)
        # 2) Space gedrückt halten → temporäres Hand-Tool, Linksklick-Drag panned
        try:
            self.configure(takefocus=True)
        except Exception:
            pass
        self.bind("<KeyPress-space>", self._on_space_down)
        self.bind("<KeyRelease-space>", self._on_space_up)
        self.bind("<Delete>", self._on_delete_key)
        self.bind("<BackSpace>", self._on_delete_key)
        self.bind("<ButtonPress-1>", self._on_left_pan_press, add="+")
        self.bind("<B1-Motion>", self._on_left_pan_move, add="+")
        self.bind("<ButtonRelease-1>", self._on_left_pan_release, add="+")
        # 3) Mausrad mit Modifikatoren → Panning
        self.bind("<Shift-MouseWheel>", self._on_mousewheel_pan_h)
        self.bind("<Alt-MouseWheel>", self._on_mousewheel_pan_v)
        # X11-Kompatibilität (Button-4/5 sind Wheel-Up/Down)
        self.bind("<Shift-Button-4>", self._on_mousewheel_pan_h)
        self.bind("<Shift-Button-5>", self._on_mousewheel_pan_h)
        self.bind("<Alt-Button-4>", self._on_mousewheel_pan_v)
        self.bind("<Alt-Button-5>", self._on_mousewheel_pan_v)
        # Redraw bei Größenänderung (inkl. Grid)
        self.bind("<Configure>", self._on_canvas_configure)
        # Rechteckauswahl (Drag auf leerem Bereich mit linker Taste)
        self._sel_rect_start: Optional[Tuple[int, int]] = None
        self._sel_rect_canvas_item: Optional[int] = None
        self.bind("<ButtonPress-1>", self._on_press_rect, add="+")
        self.bind("<B1-Motion>", self._on_drag_rect, add="+")
        self.bind("<ButtonRelease-1>", self._on_release_rect, add="+")

        # Ausrichtungshilfen (Guides)
        self._guide_items: List[int] = []
        self._align_threshold: int = 8

    # ----- Referenz-Gruppen Hilfen -----
    def _is_ref_subprocess(self, el: Optional[VPBElement]) -> bool:
        if not el:
            return False
        base_type = getattr(el, "original_element_type", None) or getattr(el, "element_type", "")
        ref_file = getattr(el, "ref_file", "") or ""
        return str(base_type).upper() == "SUBPROCESS" and bool(ref_file)

    def _ensure_ref_group(self, el: Optional[VPBElement]) -> None:
        if not el:
            return
        ref_file = getattr(el, "ref_file", "") or ""
        if not ref_file:
            self._revert_ref_group_if_needed(el)
            return

        if str(getattr(el, "element_type", "")).upper() != "GROUP":
            if not getattr(el, "original_element_type", None):
                el.original_element_type = el.element_type
            el.element_type = "GROUP"
        if not hasattr(el, "members") or getattr(el, "members", None) is None:
            el.members = []
        if not el.members:
            el.collapsed = True

    def _revert_ref_group_if_needed(self, el: VPBElement) -> None:
        original = getattr(el, "original_element_type", None)
        if not original or original == "GROUP":
            return
        el.element_type = original
        el.original_element_type = None
        try:
            if hasattr(el, "members"):
                el.members.clear()
        except Exception:
            el.members = []
        el.collapsed = False

    def _schedule_ref_refresh(self) -> None:
        try:
            if getattr(self, "_ref_refresh_job", None):
                self.after_cancel(self._ref_refresh_job)
        except Exception:
            pass
        interval = max(500, int(getattr(self, "ref_refresh_interval_ms", 2000) or 0))
        if interval <= 0:
            self._ref_refresh_job = None
            return

        def _run() -> None:
            self._ref_refresh_job = None
            try:
                if not self.winfo_exists():
                    return
            except Exception:
                return
            self._refresh_reference_groups()
            self._schedule_ref_refresh()

        try:
            self._ref_refresh_job = self.after(interval, _run)
        except Exception:
            self._ref_refresh_job = None

    def _refresh_reference_groups(self) -> None:
        changed = False
        for el in list(self.elements.values()):
            if not self._is_ref_subprocess(el):
                continue
            ok, undo_done = self._ensure_group_reference_loaded(el)
            if not ok:
                continue
            if undo_done:
                changed = True
        if changed:
            try:
                self.after_idle(self.redraw_all)
            except Exception:
                self.redraw_all()

    def destroy(self) -> None:
        try:
            if getattr(self, "_ref_refresh_job", None):
                self.after_cancel(self._ref_refresh_job)
        except Exception:
            pass
        self._ref_refresh_job = None
        super().destroy()

    def _ref_status_text(self, el: Optional[VPBElement]) -> Optional[str]:
        if not el or not getattr(el, "ref_file", ""):
            return None
        path = getattr(el, "ref_inline_path", None) or getattr(el, "ref_file", "")
        if not path:
            return None
        try:
            base = os.path.basename(path)
            display = base if base else path
        except Exception:
            display = path
        return f"Referenz: {display}"

    def _decorate_ref_element(self, el: VPBElement) -> None:
        if not self._is_ref_subprocess(el):
            return
        tag = f"node:{el.element_id}"
        bbox = None
        try:
            bbox = self.bbox(tag)
        except Exception:
            bbox = None
        if bbox:
            x0, y0, x1, y1 = bbox
            scale = max(self.view_scale, 0.3)
            size = max(12, int(round(12 * scale)))
            pad = max(2, int(round(3 * scale)))
            left = int(round(x1 - size - pad))
            top = int(round(y0 + pad))
            right = int(round(x1 - pad))
            bottom = int(round(y0 + size + pad))
            badge = self.create_oval(left, top, right, bottom, fill="#2d7ff9", outline="#ffffff", width=1)
            font_size = max(7, int(round(6 * scale)))
            icon = self.create_text(
                int(round((left + right) / 2)),
                int(round((top + bottom) / 2)),
                text="↗",
                fill="#ffffff",
                font=("Segoe UI", font_size, "bold"),
            )
            for item in (badge, icon):
                self.addtag_withtag(tag, item)
                self._id_to_element[item] = el.element_id
        status_text = self._ref_status_text(el)
        if status_text:
            try:
                self.tag_bind(tag, "<Enter>", lambda event, text=status_text: self._status(text))
                self.tag_bind(tag, "<Leave>", lambda event: self._status(""))
            except Exception:
                pass

    # ----- Tastatur-Helfer: Auswahl/Nudge -----
    def select_all(self):
        """Wählt alle Elemente im Diagramm aus."""
        try:
            self.selected_ids = set(self.elements.keys())
            self.selected_id = next(iter(self.selected_ids)) if self.selected_ids else None
            self.selected_conn_id = None
            self.redraw_all()
            sel = self.elements.get(self.selected_id) if self.selected_id else None
            self._notify_selection(sel, None)
        except Exception:
            pass

    def nudge_selection(self, dx: int, dy: int):
        """Verschiebt die aktuelle Auswahl um (dx, dy) in Modellkoordinaten.
        Erzeugt einen Undo-Eintrag und zeichnet neu."""
        try:
            if not self.selected_ids:
                return
            # Nur gültige Elemente verschieben
            move_ids = [eid for eid in self.selected_ids if eid in self.elements]
            if not move_ids:
                return
            self.push_undo()
            for eid in move_ids:
                el = self.elements.get(eid)
                if not el:
                    continue
                try:
                    el.x = int(el.x + dx)
                    el.y = int(el.y + dy)
                except Exception:
                    pass
            self.redraw_all()
        except Exception:
            pass

    def _selected_element_objects(self) -> List[VPBElement]:
        try:
            ids = set(self.selected_ids or set())
            if self.selected_id and self.selected_id in self.elements:
                ids.add(self.selected_id)
            return [self.elements[eid] for eid in ids if eid in self.elements]
        except Exception:
            return []

    def _element_bounds_model(self, el: VPBElement) -> Tuple[float, float, float, float]:
        try:
            bbox = self.bbox(f"node:{el.element_id}")
            if bbox and len(bbox) == 4:
                x0, y0 = self.to_model(bbox[0], bbox[1])
                x1, y1 = self.to_model(bbox[2], bbox[3])
                left, right = (min(x0, x1), max(x0, x1))
                top, bottom = (min(y0, y1), max(y0, y1))
                if right > left and bottom > top:
                    return (left, top, right, bottom)
        except Exception:
            pass
        try:
            cx, cy = el.center()
        except Exception:
            cx, cy = getattr(el, "x", 0), getattr(el, "y", 0)
        w = float(getattr(self, "NODE_W", 150))
        h = float(getattr(self, "NODE_H", 60))
        half_w = w / 2.0
        half_h = h / 2.0
        return (cx - half_w, cy - half_h, cx + half_w, cy + half_h)

    def _selection_bounds_model(self, include_connections: bool = True) -> Optional[Tuple[float, float, float, float]]:
        try:
            elements = self._selected_element_objects()
            if include_connections and not elements:
                conn_id = getattr(self, "selected_conn_id", None)
                conn = self.connections.get(conn_id) if conn_id else None
                if conn:
                    src = self.elements.get(conn.source_element)
                    tgt = self.elements.get(conn.target_element)
                    elements = [el for el in (src, tgt) if el]
            if not elements:
                return None
            bounds = [self._element_bounds_model(el) for el in elements]
            min_x = min(b[0] for b in bounds)
            min_y = min(b[1] for b in bounds)
            max_x = max(b[2] for b in bounds)
            max_y = max(b[3] for b in bounds)
            return (min_x, min_y, max_x, max_y)
        except Exception:
            return None

    def focus_selection(self) -> bool:
        bounds = self._selection_bounds_model(include_connections=True)
        if not bounds:
            return False
        min_x, min_y, max_x, max_y = bounds
        cx = (min_x + max_x) / 2.0
        cy = (min_y + max_y) / 2.0
        vw = max(1, int(self.winfo_width() or self.winfo_reqwidth() or 1200))
        vh = max(1, int(self.winfo_height() or self.winfo_reqheight() or 800))
        scale = max(self.view_scale, 1e-6)
        self.view_tx = vw / 2.0 - cx * scale
        self.view_ty = vh / 2.0 - cy * scale
        self.redraw_all()
        self._notify_view_changed()
        return True

    def zoom_to_selection(self, padding: float = 40.0) -> bool:
        bounds = self._selection_bounds_model(include_connections=True)
        if not bounds:
            return False
        min_x, min_y, max_x, max_y = bounds
        width = max(1.0, (max_x - min_x))
        height = max(1.0, (max_y - min_y))
        vw = max(1, int(self.winfo_width() or self.winfo_reqwidth() or 1200))
        vh = max(1, int(self.winfo_height() or self.winfo_reqheight() or 800))
        target_w = width + padding * 2.0
        target_h = height + padding * 2.0
        sx = vw / target_w
        sy = vh / target_h
        new_scale = min(self._max_zoom, max(self._min_zoom, min(sx, sy)))
        cx = (min_x + max_x) / 2.0
        cy = (min_y + max_y) / 2.0
        self.view_scale = new_scale
        self.view_tx = vw / 2.0 - cx * new_scale
        self.view_ty = vh / 2.0 - cy * new_scale
        self.redraw_all()
        self._notify_view_changed()
        return True

    def align_selection(self, mode: str) -> bool:
        elements = self._selected_element_objects()
        if len(elements) < 2:
            return False
        bounds = {el.element_id: self._element_bounds_model(el) for el in elements}
        centers = {el.element_id: ((b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0) for el, b in ((el, bounds[el.element_id]) for el in elements)}
        mode = (mode or "").lower()
        target_x = None
        target_y = None
        if mode == "left":
            target_x = min(b[0] for b in bounds.values())
        elif mode == "right":
            target_x = max(b[2] for b in bounds.values())
        elif mode in {"center", "centre"}:
            target_x = sum(c[0] for c in centers.values()) / len(centers)
        elif mode == "top":
            target_y = min(b[1] for b in bounds.values())
        elif mode == "bottom":
            target_y = max(b[3] for b in bounds.values())
        elif mode in {"middle", "vertical", "middle_vertical"}:
            target_y = sum(c[1] for c in centers.values()) / len(centers)
        else:
            return False

        pending: List[Tuple[VPBElement, float, float]] = []
        for el in elements:
            b = bounds[el.element_id]
            cx, cy = centers[el.element_id]
            new_x = float(el.x)
            new_y = float(el.y)
            if target_x is not None:
                width = max(1.0, b[2] - b[0])
                if mode == "left":
                    new_x = target_x + width / 2.0
                elif mode == "right":
                    new_x = target_x - width / 2.0
                else:  # center aligned
                    new_x = target_x
            if target_y is not None:
                height = max(1.0, b[3] - b[1])
                if mode == "top":
                    new_y = target_y + height / 2.0
                elif mode == "bottom":
                    new_y = target_y - height / 2.0
                else:  # middle aligned
                    new_y = target_y
            pending.append((el, new_x, new_y))

        if not any(int(round(nx)) != el.x or int(round(ny)) != el.y for el, nx, ny in pending):
            return False

        selection_ids = {el.element_id for el, _, _ in pending}

        self.push_undo()
        for el, nx, ny in pending:
            try:
                el.x = int(round(nx))
                el.y = int(round(ny))
            except Exception:
                pass
        for conn in self.connections.values():
            try:
                if (
                    getattr(conn, "source_element", None) in selection_ids
                    or getattr(conn, "target_element", None) in selection_ids
                ):
                    conn.routing_mode = "curved"
            except Exception:
                pass
        self.redraw_all()
        sel = self.elements.get(self.selected_id) if self.selected_id else None
        self._notify_selection(sel, None)
        return True

    def distribute_selection(self, axis: str) -> bool:
        elements = self._selected_element_objects()
        if len(elements) < 3:
            return False
        axis = (axis or "").lower()
        if axis not in {"horizontal", "vertical"}:
            return False
        bounds = {el.element_id: self._element_bounds_model(el) for el in elements}
        if axis == "horizontal":
            ordered = sorted(elements, key=lambda el: ((bounds[el.element_id][0] + bounds[el.element_id][2]) / 2.0, el.element_id))
            left_edge = min(bounds[el.element_id][0] for el in ordered)
            right_edge = max(bounds[el.element_id][2] for el in ordered)
            widths = [max(1.0, bounds[el.element_id][2] - bounds[el.element_id][0]) for el in ordered]
            total_width = sum(widths)
            span = right_edge - left_edge
            gap = 0.0 if len(ordered) <= 1 else (span - total_width) / (len(ordered) - 1)
            current_left = left_edge
            pending: List[Tuple[VPBElement, float, float]] = []
            for idx, el in enumerate(ordered):
                width = widths[idx]
                center_x = current_left + width / 2.0
                pending.append((el, center_x, float(el.y)))
                current_left += width + gap
        else:
            ordered = sorted(elements, key=lambda el: ((bounds[el.element_id][1] + bounds[el.element_id][3]) / 2.0, el.element_id))
            top_edge = min(bounds[el.element_id][1] for el in ordered)
            bottom_edge = max(bounds[el.element_id][3] for el in ordered)
            heights = [max(1.0, bounds[el.element_id][3] - bounds[el.element_id][1]) for el in ordered]
            total_height = sum(heights)
            span = bottom_edge - top_edge
            gap = 0.0 if len(ordered) <= 1 else (span - total_height) / (len(ordered) - 1)
            current_top = top_edge
            pending = []
            for idx, el in enumerate(ordered):
                height = heights[idx]
                center_y = current_top + height / 2.0
                pending.append((el, float(el.x), center_y))
                current_top += height + gap

        if not any(int(round(nx)) != el.x or int(round(ny)) != el.y for el, nx, ny in pending):
            return False

        self.push_undo()
        for el, nx, ny in pending:
            try:
                el.x = int(round(nx))
                el.y = int(round(ny))
            except Exception:
                pass
        self.redraw_all()
        sel = self.elements.get(self.selected_id) if self.selected_id else None
        self._notify_selection(sel, None)
        return True

    def arrange_selection_circular(self, element_ids: Optional[Iterable[str]] = None) -> bool:
        """Ordnet ausgewählte Elemente gleichmäßig auf einem Kreis an."""
        import math

        if element_ids is None:
            ids = [eid for eid in getattr(self, "selected_ids", set()) if eid in self.elements]
        else:
            ids = [eid for eid in element_ids if eid in self.elements]
        if len(ids) < 2:
            return False

        elements: List[VPBElement] = [self.elements[eid] for eid in ids]
        try:
            cx = sum(el.x for el in elements) / len(elements)
            cy = sum(el.y for el in elements) / len(elements)
        except Exception:
            return False

        bounds = [self._element_bounds_model(el) for el in elements]
        max_extent = max(
            max(b[2] - b[0], b[3] - b[1])
            for b in bounds
        ) if bounds else max(float(self.NODE_W), float(self.NODE_H))

        try:
            max_distance = max(math.hypot(el.x - cx, el.y - cy) for el in elements)
        except Exception:
            max_distance = 0.0
        circumference_needed = len(elements) * max_extent * 1.15
        radius_min = circumference_needed / (2.0 * math.pi) if circumference_needed > 0 else 0.0
        radius = max(radius_min, max_distance, max_extent * 0.75, 80.0)

        angle_pairs = []
        for el in elements:
            try:
                angle = math.atan2(el.y - cy, el.x - cx)
            except Exception:
                angle = 0.0
            angle_pairs.append((el, angle))
        angle_pairs.sort(key=lambda item: (item[1], getattr(item[0], "element_id", "")))
        if not angle_pairs:
            return False

        step = (2.0 * math.pi) / len(angle_pairs)
        start_angle = angle_pairs[0][1] if len(angle_pairs) > 0 else 0.0
        pending: List[Tuple[VPBElement, float, float]] = []
        for index, (el, _) in enumerate(angle_pairs):
            angle = start_angle + index * step
            nx = cx + radius * math.cos(angle)
            ny = cy + radius * math.sin(angle)
            pending.append((el, nx, ny))

        if not any(int(round(nx)) != el.x or int(round(ny)) != el.y for el, nx, ny in pending):
            return False

        self.push_undo()
        for el, nx, ny in pending:
            try:
                el.x = int(round(nx))
                el.y = int(round(ny))
            except Exception:
                pass
        self.redraw_all()
        sel = self.elements.get(self.selected_id) if self.selected_id else None
        self._notify_selection(sel, None)
        return True

    # ----- View-Steuerung (Pan/Zoom/Zentrierung) -----
    def pan_pixels(self, dx_px: float, dy_px: float):
        """Verschiebt die Ansicht um Pixel (Viewport-Koordinaten)."""
        try:
            self.view_tx += dx_px
            self.view_ty += dy_px
            self.redraw_all()
            self._notify_view_changed()
        except Exception:
            pass

    def zoom_at_view(self, factor: float, vx: Optional[float] = None, vy: Optional[float] = None):
        """Zoomt relativ am Punkt (vx, vy) in Viewport-Pixeln."""
        try:
            if vx is None or vy is None:
                vx = max(0, int(self.winfo_width() or 0)) / 2
                vy = max(0, int(self.winfo_height() or 0)) / 2
            mx, my = self.to_model(vx, vy)
            new_scale = max(getattr(self, '_min_zoom', 0.1), min(getattr(self, '_max_zoom', 5.0), self.view_scale * factor))
            self.view_scale = new_scale
            self.view_tx = vx - mx * self.view_scale
            self.view_ty = vy - my * self.view_scale
            self.redraw_all()
            self._notify_view_changed()
        except Exception:
            pass

    def center_time_axis_vertical(self):
        """Setzt die Ansicht so, dass die Nulllinie (y=0) vertikal mittig liegt."""
        try:
            # Hole Canvas-Dimensionen
            w = int(self.winfo_width() or 1200)
            h = int(self.winfo_height() or 800)
            
            # Berechne, wo y=0 in View-Koordinaten sein soll (Mitte des Canvas)
            target_view_y = h / 2
            
            # Berechne die benötigte view_ty, damit y=0 (model) auf target_view_y (view) liegt
            # view_y = model_y * scale + view_ty
            # target_view_y = 0 * scale + view_ty
            # => view_ty = target_view_y
            self.view_ty = target_view_y
            
            # Hole Content Bounds für horizontale Zentrierung
            min_x, min_y, max_x, max_y = self.get_content_bounds(include_connections=True)
            
            # Horizontale Zentrierung: Zeige Content mittig, oder bei leerem Canvas x=0 mittig
            if min_x < max_x:
                # Mit Content: Zeige Content-Mitte
                content_center_x = (min_x + max_x) / 2
                target_view_x = w / 2
                self.view_tx = target_view_x - content_center_x * self.view_scale
            else:
                # Leerer Canvas: Zeige x=0 in der Mitte
                target_view_x = w / 2
                self.view_tx = target_view_x
            
            self.redraw_all()
            self._notify_view_changed()
        except Exception as e:
            print(f"⚠️ center_time_axis_vertical failed: {e}")
            pass

    # ----- Koordinaten-Transform -----
    def to_view(self, x: float, y: float) -> Tuple[int, int]:
        s = self.view_scale
        return int(x * s + self.view_tx), int(y * s + self.view_ty)

    def to_model(self, vx: float, vy: float) -> Tuple[float, float]:
        s = max(self.view_scale, 1e-6)
        return (vx - self.view_tx) / s, (vy - self.view_ty) / s

    # ----- View/Content-Hilfen für Scrollbars -----
    def get_content_bounds(self, include_connections: bool = True) -> Tuple[float, float, float, float]:
        """Berechnet die minimalen Umschließungs-Bounds aller Elemente (Model-Koordinaten).
        Bezieht die Knotenbreite/-höhe und optional Verbindungsendpunkte mit ein.
        Rückgabe: (min_x, min_y, max_x, max_y)
        """
        if not self.elements:
            return (0.0, 0.0, 0.0, 0.0)
        xs: List[float] = []
        ys: List[float] = []
        for el in self.elements.values():
            try:
                x, y = el.center()
            except Exception:
                x, y = getattr(el, 'x', 0), getattr(el, 'y', 0)
            xs.append(float(x))
            ys.append(float(y))
        if not xs or not ys:
            return (0.0, 0.0, 0.0, 0.0)
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        # Knotenbreite/Höhe berücksichtigen (rechteckige Standardknoten)
        w, h = self.NODE_W, self.NODE_H
        min_x -= w / 2
        max_x += w / 2
        min_y -= h / 2
        max_y += h / 2
        if include_connections and self.connections:
            for conn in self.connections.values():
                s_el = self.elements.get(conn.source_element)
                t_el = self.elements.get(conn.target_element)
                if not s_el or not t_el:
                    continue
                x1, y1 = s_el.center()
                x2, y2 = t_el.center()
                min_x = min(min_x, x1, x2)
                max_x = max(max_x, x1, x2)
                min_y = min(min_y, y1, y2)
                max_y = max(max_y, y1, y2)
        return (float(min_x), float(min_y), float(max_x), float(max_y))

    def get_viewport_model_size(self) -> Tuple[float, float]:
        """Gibt die aktuelle Viewport-Größe in Model-Einheiten zurück."""
        vw = max(1, int(self.winfo_width() or self.winfo_reqwidth() or 1))
        vh = max(1, int(self.winfo_height() or self.winfo_reqheight() or 1))
        s = max(self.view_scale, 1e-6)
        return vw / s, vh / s

    def get_view_origin_model(self) -> Tuple[float, float]:
        """Top-Left des Viewports in Model-Koordinaten."""
        return self.to_model(0, 0)

    def set_view_origin_model(self, x_model: float, y_model: float):
        """Setzt den View so, dass (x_model, y_model) oben links sichtbar ist. Klemmt in die Content-Grenzen."""
        try:
            min_x, min_y, max_x, max_y = self.get_content_bounds(include_connections=True)
            view_w_m, view_h_m = self.get_viewport_model_size()
            max_x0 = max(min_x, max_x - view_w_m)
            max_y0 = max(min_y, max_y - view_h_m)
            x0 = min(max(x_model, min_x), max_x0)
            y0 = min(max(y_model, min_y), max_y0)
        except Exception:
            x0, y0 = x_model, y_model
        s = max(self.view_scale, 1e-6)
        self.view_tx = -x0 * s
        self.view_ty = -y0 * s
        self.redraw_all()
        self._notify_view_changed()

    def _notify_view_changed(self):
        try:
            # legacy
            if self.on_view_changed:
                self.on_view_changed()
            # fan-out
            for cb in list(self._view_changed_listeners):
                try:
                    cb()
                except Exception:
                    pass
        except Exception:
            pass

    def add_view_changed_listener(self, cb: Callable[[], None]):
        try:
            if cb not in self._view_changed_listeners:
                self._view_changed_listeners.append(cb)
        except Exception:
            pass

    def remove_view_changed_listener(self, cb: Callable[[], None]):
        try:
            if cb in self._view_changed_listeners:
                self._view_changed_listeners.remove(cb)
        except Exception:
            pass

    # ----- Laden/Speichern -----
    def load_from_dict(self, data: Dict):
        self.clear()
        # Metadaten
        try:
            self.metadata = dict(data.get("metadata", {}))
        except Exception:
            self.metadata = {"name": "VPB Prozess", "version": "1.0"}

        # Projektweite Hierarchie-Kategorien (optisch) laden
        try:
            cats = data.get("hierarchy_categories")
            if isinstance(cats, list):
                self.hierarchy_categories = cats
                try:
                    self._hierarchy_color_cache.clear()
                except Exception:
                    self._hierarchy_color_cache = {}
        except Exception:
            pass

        # Element-Typ-Synonyme auflösen (Kompatibilität)
        def _normalize_element_type(et: Optional[str]) -> str:
            t = (et or "FUNCTION").strip()
            t_up = t.upper()
            # Häufige Synonyme/Abkürzungen
            synonyms = {
                "TASK": "FUNCTION",
                "DECISION": "GATEWAY",
                "DECISION_GATEWAY": "GATEWAY",
                # BPMN-Gateways ohne Suffix
                "AND": "AND_CONNECTOR",
                "OR": "OR_CONNECTOR",
                "XOR": "XOR_CONNECTOR",
            }
            return synonyms.get(t_up, t_up)

        for e in data.get("elements", []):
            el = VPBElement(
                element_id=e.get("element_id"),
                element_type=_normalize_element_type(e.get("element_type", "FUNCTION")),
                name=e.get("name", e.get("element_id", "Element")),
                x=int(e.get("x", 100)),
                y=int(e.get("y", 100)),
                description=e.get("description", ""),
                responsible_authority=e.get("responsible_authority", ""),
                legal_basis=e.get("legal_basis", ""),
                deadline_days=int(e.get("deadline_days", 0) or 0),
                geo_reference=e.get("geo_reference", ""),
            )
            try:
                orig_type = e.get("original_element_type")
                if orig_type:
                    el.original_element_type = str(orig_type)
            except Exception:
                el.original_element_type = None
            # SUBPROCESS: ref_file
            try:
                el.ref_file = str(e.get("ref_file", "") or "")
            except Exception:
                el.ref_file = ""
            try:
                if getattr(el, "ref_file", ""):
                    self._load_ref_preview(el)
                else:
                    el.ref_inline_content = None
                    el.ref_inline_error = None
                    el.ref_inline_path = None
                    el.ref_inline_truncated = False
            except Exception:
                el.ref_inline_error = "Vorschau konnte nicht geladen werden"
            # Alte Daten ohne original_element_type für SUBPROCESS-Referenzen korrigieren
            if getattr(el, "ref_file", "") and not getattr(el, "original_element_type", None):
                el.original_element_type = e.get("element_type", "SUBPROCESS")
            # GROUP Felder
            if el.element_type == "GROUP":
                try:
                    el.members = [str(i) for i in e.get("members", []) if isinstance(i, (str, int))]
                except Exception:
                    el.members = []
                el.collapsed = bool(e.get("collapsed", False))
            if self._is_ref_subprocess(el):
                self._ensure_ref_group(el)
            # Optional: visuelle Hierarchie-Referenz
            try:
                el.hierarchy = str(e.get("hierarchy")) if e.get("hierarchy") is not None else None
            except Exception:
                el.hierarchy = None
            self.elements[el.element_id] = el

        for c in data.get("connections", []):
            conn = VPBConnection(
                connection_id=c.get("connection_id"),
                source_element=c.get("source_element"),
                target_element=c.get("target_element"),
                connection_type=c.get("connection_type", "SEQUENCE"),
                description=c.get("description", ""),
                arrow_style=str(c.get("arrow_style", "single") or "single"),
                routing_mode=str(c.get("routing_mode", "auto") or "auto"),
            )
            self.connections[conn.connection_id] = conn

        self.redraw_all()

    def to_dict(self) -> Dict:
        # einfache Rekonstruktion mit nur relevanten Feldern
        elements = []
        for e in self.elements.values():
            obj = {
                "element_id": e.element_id,
                "element_type": e.element_type,
                "name": e.name,
                "description": e.description,
                "x": e.x,
                "y": e.y,
                "responsible_authority": e.responsible_authority,
                "legal_basis": e.legal_basis,
                "deadline_days": e.deadline_days,
                "geo_reference": e.geo_reference,
            }
            if getattr(e, "ref_file", ""):
                obj["ref_file"] = e.ref_file
            if getattr(e, "original_element_type", None):
                obj["original_element_type"] = e.original_element_type
            # Optionale visuelle Hierarchie-Referenz
            if getattr(e, "hierarchy", None):
                obj["hierarchy"] = e.hierarchy
            
            # Container-Typen (GROUP und TIME_LOOP)
            if e.element_type in ("GROUP", "TIME_LOOP"):
                if getattr(e, "members", None):
                    obj["members"] = list(e.members)
                if getattr(e, "collapsed", False):
                    obj["collapsed"] = True
            
            # Zeit-Properties für TIME_LOOP und TIMER
            if e.element_type in ("TIME_LOOP", "TIMER"):
                if getattr(e, "loop_type", "none") != "none":
                    obj["loop_type"] = e.loop_type
                if getattr(e, "loop_interval_minutes", 0) > 0:
                    obj["loop_interval_minutes"] = e.loop_interval_minutes
                if getattr(e, "loop_cron", ""):
                    obj["loop_cron"] = e.loop_cron
                if getattr(e, "loop_date", ""):
                    obj["loop_date"] = e.loop_date
                if getattr(e, "loop_relative_days", 0) > 0:
                    obj["loop_relative_days"] = e.loop_relative_days
                if getattr(e, "loop_max_iterations", 0) > 0:
                    obj["loop_max_iterations"] = e.loop_max_iterations
            
            elements.append(obj)
        connections = [
            {
                "connection_id": c.connection_id,
                "source_element": c.source_element,
                "target_element": c.target_element,
                "connection_type": c.connection_type,
                "description": c.description,
                "arrow_style": getattr(c, "arrow_style", "single"),
                **({"routing_mode": c.routing_mode} if getattr(c, "routing_mode", "auto") not in {None, "", "auto"} else {}),
            }
            for c in self.connections.values()
        ]
        return {
            "metadata": self.metadata if hasattr(self, 'metadata') and isinstance(self.metadata, dict) else {"name": "VPB Prozess", "version": "1.0"},
            "elements": elements,
            "connections": connections,
            # Nur optisch genutzt – Kategorien für die linke Hierarchie-Leiste
            "hierarchy_categories": list(getattr(self, 'hierarchy_categories', [])),
        }

    # ----- Zeichenlogik -----
    def clear(self):
        self.delete("all")
        self.elements.clear()
        self.connections.clear()
        self._id_to_element.clear()
        self._id_to_connection.clear()
        self.selected_id = None
        if hasattr(self, 'selected_ids'):
            try:
                self.selected_ids.clear()
            except Exception:
                self.selected_ids = set()
        self.selected_conn_id = None
        self.link_mode = False
        self.link_source_id = None
        self._connection_points_cache = {}
        self._collapsed_redirect = {}
        try:
            self._hierarchy_color_cache.clear()
        except Exception:
            self._hierarchy_color_cache = {}
        # Historie zurücksetzen
        if hasattr(self, '_undo_stack'):
            self._undo_stack.clear()
        if hasattr(self, '_redo_stack'):
            self._redo_stack.clear()
        # View-Änderung signalisieren (z.B. Scrollbars/Minimap updaten)
        try:
            self._notify_view_changed()
        except Exception:
            pass
        self._notify_selection(None, None)

    def redraw_all(self):
        self.delete("all")
        try:
            for el in list(self.elements.values()):
                if not self._is_ref_subprocess(el):
                    continue
                self._ensure_ref_group(el)
                self._ensure_group_reference_loaded(el, force_reload=False)
        except Exception:
            pass
        # Grid zuerst zeichnen
        if getattr(self, 'grid_visible', False):
            self._draw_grid()
        # Zeitachse zeichnen (durch Ursprung y=0)
        try:
            if getattr(self, 'time_axis_enabled', False):
                self._draw_time_axis()
        except Exception:
            pass
        # Hierarchie-Balken: nur intern zeichnen, wenn kein externes Canvas verwendet wird
        try:
            if not getattr(self, 'hierarchy_external', True):
                if getattr(self, 'hierarchy_categories', None):
                    self._draw_hierarchy_bars()
        except Exception:
            pass
        self._id_to_element.clear()
        self._id_to_connection.clear()
        # Zeichnen: zuerst Verbindungen, aber Container brauchen Kenntnis, welche Elemente versteckt werden
        # Markiere Elemente, die von KOLLAPIERTEN Gruppen verdeckt werden sollen (werden nicht einzeln gezeichnet)
        hidden_members: set[str] = set()
        hidden_groups: set[str] = set()
        collapsed_redirect: Dict[str, str] = {}
        for el in self.elements.values():
            if el.element_type == "GROUP" and getattr(el, "collapsed", False):
                # Alle Mitglieder (rekursiv) verstecken
                stack = list((getattr(el, "members", []) or []))
                while stack:
                    mid = stack.pop()
                    if mid in hidden_members:
                        continue
                    hidden_members.add(mid)
                    if mid not in collapsed_redirect:
                        collapsed_redirect[mid] = el.element_id
                    ch = self.elements.get(mid)
                    if ch and ch.element_type == "GROUP":
                        hidden_groups.add(mid)
                        # deren Mitglieder ebenfalls verstecken
                        for sm in getattr(ch, "members", []) or []:
                            if sm not in hidden_members:
                                stack.append(sm)
        self._collapsed_redirect = collapsed_redirect
        self._connection_points_cache: Dict[str, List[int]] = {}
        # Verbindungen zeichnen (unverändert)
        for conn in self.connections.values():
            self._draw_connection(conn)
        # Container zuerst, dann andere
        groups = [e for e in self.elements.values() if e.element_type == "GROUP"]
        others = [e for e in self.elements.values() if e.element_type != "GROUP"]
        for el in groups:
            if el.element_id in hidden_groups:
                continue
            self._draw_element(el)
        for el in others:
            if el.element_id in hidden_members:
                continue
            self._draw_element(el)
        # Labels oben halten: nachzeichnen
        for el in groups:
            if el.element_id in hidden_groups:
                continue
            self._draw_label(el)
        for el in others:
            if el.element_id in hidden_members:
                continue
            self._draw_label(el)
        for conn in self.connections.values():
            self._draw_connection_label(conn)

    def _create_selection_outline_item(self, shape: Optional[str], cx: int, cy: int, w: int, h: int) -> Optional[int]:
        margin = max(4, int(round(4 * max(self.view_scale, 0.25))))
        dash_pattern = (4, 2)
        outline_color = "#FF9900"
        shape = (shape or "").lower()
        if shape in ("oval", "circle"):
            radius = max(4, min(w, h) // 2)
            r = radius + margin
            return self.create_oval(
                cx - r,
                cy - r,
                cx + r,
                cy + r,
                outline=outline_color,
                width=2,
                dash=dash_pattern,
                fill="",
            )
        if shape == "diamond":
            pts = _diamond_points(cx, cy, w + 2 * margin, h + 2 * margin)
            return self.create_polygon(pts, outline=outline_color, width=2, dash=dash_pattern, fill="")
        if shape == "hex":
            pts = _hex_points(cx, cy, w + 2 * margin, h + 2 * margin)
            return self.create_polygon(pts, outline=outline_color, width=2, dash=dash_pattern, fill="")
        half_w = w // 2
        half_h = h // 2
        return self.create_rectangle(
            cx - half_w - margin,
            cy - half_h - margin,
            cx + half_w + margin,
            cy + half_h + margin,
            outline=outline_color,
            width=2,
            dash=dash_pattern,
            fill="",
        )

    def _draw_element(self, el: VPBElement):
        style = self._resolve_element_style(el.element_type, el)
        try:
            el._resolved_style = style
        except Exception:
            pass
        cx, cy = self.to_view(*el.center())
        # skaliere Knoten, min. sichtbare Größe
        w = max(30, int(self.NODE_W * self.view_scale))
        h = max(20, int(self.NODE_H * self.view_scale))
        items: List[int] = []

        # GROUP oder TIME_LOOP: Container mit gestricheltem Rahmen
        if el.element_type in ("GROUP", "TIME_LOOP"):
            # Zeichne Container: großer gestrichelter Rahmen. Größe aus Bounding-Box der Mitglieder, ansonsten Standard
            members = getattr(el, "members", []) or []
            collapsed = getattr(el, "collapsed", False)
            # Auto-Kompaktdarstellung bei kleiner Zoomstufe, ohne Flag zu ändern
            auto_compact = False
            try:
                if not collapsed and self.view_scale <= 0.5:
                    auto_compact = True
            except Exception:
                pass
            # Wenn nicht collapsed und Mitglieder existieren: berechne Bounds in Model-Koordinaten
            if members and not collapsed and not auto_compact:
                xs: List[int] = []
                ys: List[int] = []
                for mid in members:
                    child = self.elements.get(mid)
                    if not child:
                        continue
                    xs.extend([child.x - self.NODE_W // 2, child.x + self.NODE_W // 2])
                    ys.extend([child.y - self.NODE_H // 2, child.y + self.NODE_H // 2])
                if xs and ys:
                    left, right = min(xs) - 20, max(xs) + 20
                    top, bottom = min(ys) - 20, max(ys) + 20
                    vx0, vy0 = self.to_view(left, top)
                    vx1, vy1 = self.to_view(right, bottom)
                    item = self.create_rectangle(vx0, vy0, vx1, vy1,
                                                 outline=style.get("outline", "#666"),
                                                 width=2, dash=style.get("dash", (6, 4)), fill="")
                    items.append(item)
                else:
                    # Fallback: Standardgröße um Center
                    item = self.create_rectangle(
                        cx - w, cy - h, cx + w, cy + h,
                        outline=style.get("outline", "#666"), width=2, dash=style.get("dash", (6, 4)), fill="")
                    items.append(item)
            else:
                # Collapsed oder keine Mitglieder: kompaktes Element zeichnen
                item = self.create_rectangle(
                    cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2,
                    fill=style.get("fill", ""), outline=style.get("outline", "#666"), width=2, dash=style.get("dash", (6, 4))
                )
                items.append(item)

            # Selektion hervorheben
            if el.element_id in self.selected_ids or self.selected_id == el.element_id:
                # Markiere die Rahmen-Bounds
                if members and not collapsed and 'vx0' in locals():
                    sel = self.create_rectangle(vx0 - 4, vy0 - 4, vx1 + 4, vy1 + 4, outline="#FF9900", width=2, dash=(4, 2))
                else:
                    sel = self.create_rectangle(cx - w // 2 - 4, cy - h // 2 - 4, cx + w // 2 + 4, cy + h // 2 + 4,
                                                outline="#FF9900", width=2, dash=(4, 2))
                items.append(sel)

            for it in items:
                self.addtag_withtag(f"node:{el.element_id}", it)
                self._id_to_element[it] = el.element_id
            self._decorate_ref_element(el)
            el.canvas_items = items
            return

        shape = style.get("shape")
        
        # Shadow offset for depth effect (Blender-inspired)
        shadow_offset = 3
        shadow_color = "#D0D0D0"
        
        if shape in ("rect", "rectangle"):
            # Draw shadow first (behind element)
            shadow = self.create_rectangle(
                cx - w // 2 + shadow_offset, cy - h // 2 + shadow_offset,
                cx + w // 2 + shadow_offset, cy + h // 2 + shadow_offset,
                fill=shadow_color, outline="", width=0
            )
            items.append(shadow)
            self.tag_lower(shadow)
            
            # Draw main element
            item = self.create_rectangle(
                cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2,
                fill=style.get("fill"), outline=style.get("outline"), width=2,
                dash=style.get("dash")
            )
            items.append(item)
        elif shape in ("oval", "circle"):
            # Kreis: min(w,h)
            r = min(w, h) // 2
            
            # Draw shadow
            shadow = self.create_oval(
                cx - r + shadow_offset, cy - r + shadow_offset,
                cx + r + shadow_offset, cy + r + shadow_offset,
                fill=shadow_color, outline="", width=0
            )
            items.append(shadow)
            self.tag_lower(shadow)
            
            # Draw main element
            item = self.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                fill=style.get("fill"), outline=style.get("outline"), width=2,
                dash=style.get("dash")
            )
            items.append(item)
        elif shape == "diamond":
            pts = _diamond_points(cx, cy, w, h)
            
            # Draw shadow for diamond
            shadow_pts = [p + shadow_offset for p in pts]
            shadow = self.create_polygon(
                shadow_pts, fill=shadow_color, outline="", width=0
            )
            items.append(shadow)
            self.tag_lower(shadow)
            
            # Draw main element
            item = self.create_polygon(pts, fill=style.get("fill"), outline=style.get("outline"), width=2, dash=style.get("dash"))
            items.append(item)
            
            # COUNTER: Zeige aktuellen Wert
            if el.element_type == "COUNTER":
                try:
                    current = getattr(el, "counter_current_value", 0)
                    maximum = getattr(el, "counter_max_value", 100)
                    counter_text = f"{current}/{maximum}"
                    
                    # Wert innerhalb des Diamanten
                    value_item = self.create_text(
                        cx, cy + 5,
                        text=counter_text,
                        font=("Arial", max(8, int(10 * self.view_scale)), "bold"),
                        fill="#2196F3",
                        anchor="center"
                    )
                    items.append(value_item)
                    self.addtag_withtag(f"node:{el.element_id}", value_item)
                    self._id_to_element[value_item] = el.element_id
                    
                    # Counter-Typ klein unter dem Diamanten
                    counter_type = getattr(el, "counter_type", "UP")
                    type_item = self.create_text(
                        cx, cy + h // 2 + 15,
                        text=f"🔢 {counter_type}",
                        font=("Arial", max(6, int(8 * self.view_scale))),
                        fill="#666",
                        anchor="center"
                    )
                    items.append(type_item)
                    self.addtag_withtag(f"node:{el.element_id}", type_item)
                    self._id_to_element[type_item] = el.element_id
                except Exception as e:
                    pass  # Fehler beim Rendern ignorieren
                    
        elif shape == "hex":
            pts = _hex_points(cx, cy, w, h)
            item = self.create_polygon(pts, fill=style.get("fill"), outline=style.get("outline"), width=2, dash=style.get("dash"))
            items.append(item)
            
            # CONDITION: Zeige Anzahl Checks und Logik
            if el.element_type == "CONDITION":
                try:
                    checks = getattr(el, "condition_checks", [])
                    num_checks = len(checks) if checks else 0
                    logic = getattr(el, "condition_logic", "AND")
                    
                    # Anzahl Checks innerhalb des Hexagons
                    check_text = f"{num_checks} Check{'s' if num_checks != 1 else ''}"
                    check_item = self.create_text(
                        cx, cy,
                        text=check_text,
                        font=("Arial", max(8, int(10 * self.view_scale)), "bold"),
                        fill="#FFA000",
                        anchor="center"
                    )
                    items.append(check_item)
                    self.addtag_withtag(f"node:{el.element_id}", check_item)
                    self._id_to_element[check_item] = el.element_id
                    
                    # Logik-Operator klein unter dem Hexagon
                    logic_item = self.create_text(
                        cx, cy + h // 2 + 15,
                        text=f"🔀 {logic}",
                        font=("Arial", max(6, int(8 * self.view_scale))),
                        fill="#666",
                        anchor="center"
                    )
                    items.append(logic_item)
                    self.addtag_withtag(f"node:{el.element_id}", logic_item)
                    self._id_to_element[logic_item] = el.element_id
                except Exception as e:
                    pass  # Fehler beim Rendern ignorieren
            
            # ERROR_HANDLER: Zeige Handler-Type und Retry-Count
            if el.element_type == "ERROR_HANDLER":
                try:
                    handler_type = getattr(el, "error_handler_type", "RETRY")
                    retry_count = getattr(el, "error_handler_retry_count", 3)
                    
                    # Handler-Type in der Mitte
                    type_text = f"⚠️ {handler_type}"
                    type_item = self.create_text(
                        cx, cy - 5,
                        text=type_text,
                        font=("Arial", max(8, int(10 * self.view_scale)), "bold"),
                        fill="#C62828",
                        anchor="center"
                    )
                    items.append(type_item)
                    self.addtag_withtag(f"node:{el.element_id}", type_item)
                    self._id_to_element[type_item] = el.element_id
                    
                    # Retry-Count (nur bei RETRY)
                    if handler_type == "RETRY":
                        retry_text = f"Retries: {retry_count}"
                        retry_item = self.create_text(
                            cx, cy + 10,
                            text=retry_text,
                            font=("Arial", max(7, int(8 * self.view_scale))),
                            fill="#666",
                            anchor="center"
                        )
                        items.append(retry_item)
                        self.addtag_withtag(f"node:{el.element_id}", retry_item)
                        self._id_to_element[retry_item] = el.element_id
                except Exception as e:
                    pass  # Fehler beim Rendern ignorieren
            
            # STATE: Zeige State-Name und Type
            if el.element_type == "STATE":
                try:
                    state_name = getattr(el, "state_name", "")
                    state_type = getattr(el, "state_type", "NORMAL")
                    
                    # State-Type Icon
                    type_icons = {
                        "INITIAL": "▶️",
                        "FINAL": "🏁",
                        "ERROR": "❌",
                        "NORMAL": "⬤"
                    }
                    icon = type_icons.get(state_type, "⬤")
                    
                    # State-Name (falls vorhanden)
                    if state_name:
                        name_text = f"{icon} {state_name}"
                    else:
                        name_text = f"{icon} {state_type}"
                    
                    name_item = self.create_text(
                        cx, cy - 5,
                        text=name_text,
                        font=("Arial", max(8, int(10 * self.view_scale)), "bold"),
                        fill="#2E7D32",
                        anchor="center"
                    )
                    items.append(name_item)
                    self.addtag_withtag(f"node:{el.element_id}", name_item)
                    self._id_to_element[name_item] = el.element_id
                    
                    # Transitions-Count
                    transitions = getattr(el, "state_transitions", [])
                    if transitions:
                        trans_text = f"{len(transitions)} Transitions"
                        trans_item = self.create_text(
                            cx, cy + 10,
                            text=trans_text,
                            font=("Arial", max(7, int(8 * self.view_scale))),
                            fill="#666",
                            anchor="center"
                        )
                        items.append(trans_item)
                        self.addtag_withtag(f"node:{el.element_id}", trans_item)
                        self._id_to_element[trans_item] = el.element_id
                except Exception as e:
                    pass  # Fehler beim Rendern ignorieren
            
            # INTERLOCK (Mutex/Semaphore) - Rounded Rectangle mit Lock-Info
            if el.element_type == "INTERLOCK":
                try:
                    # Icon basierend auf Type
                    interlock_type = getattr(el, "interlock_type", "MUTEX")
                    type_icons = {
                        "MUTEX": "🔒",  # Geschlossenes Schloss
                        "SEMAPHORE": "🔓"  # Offenes Schloss / Zähl-Sperre
                    }
                    icon = type_icons.get(interlock_type, "🔒")
                    
                    # Resource-ID (falls gesetzt)
                    resource_id = getattr(el, "resource_id", "")
                    if not resource_id:
                        resource_id = getattr(el, "interlock_resource_id", "")
                    
                    # Max Count (für SEMAPHORE)
                    max_count = getattr(el, "interlock_max_count", 1)
                    
                    # Display-Text
                    if interlock_type == "SEMAPHORE" and max_count > 1:
                        display_text = f"{icon} {interlock_type}\nMax: {max_count}"
                    else:
                        display_text = f"{icon} {interlock_type}"
                    
                    if resource_id:
                        display_text += f"\n{resource_id}"
                    
                    # Text anzeigen
                    text_item = self.create_text(
                        cx, cy,
                        text=display_text,
                        fill=style.get("text_color", "#000"),
                        font=("Arial", 9),
                        justify="center"
                    )
                    items.append(text_item)
                    self._id_to_element[text_item] = el.element_id
                except Exception as e:
                    pass  # Fehler beim Rendern ignorieren
                    
        else:
            # Fallback Rechteck
            item = self.create_rectangle(
                cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2,
                fill=style.get("fill", "#EEEEEE"), outline=style.get("outline", "#888"), width=2,
                dash=style.get("dash")
            )
            items.append(item)

        # Selektion hervorheben
        if el.element_id in self.selected_ids or self.selected_id == el.element_id:
            sel = self._create_selection_outline_item(style.get("shape"), cx, cy, w, h)
            if sel:
                items.append(sel)

        # Klickbereich mit Tag für Selektion
        for it in items:
            self.addtag_withtag(f"node:{el.element_id}", it)
            self._id_to_element[it] = el.element_id

        self._decorate_ref_element(el)

        highlight_color = getattr(self, "_temp_highlight_elements", {}).get(el.element_id)
        if highlight_color:
            try:
                bbox = self.bbox(f"node:{el.element_id}")
                if bbox:
                    hx0, hy0, hx1, hy1 = bbox
                    margin = max(4, int(6 + self.view_scale))
                    rect = self.create_rectangle(
                        hx0 - margin,
                        hy0 - margin,
                        hx1 + margin,
                        hy1 + margin,
                        outline=highlight_color,
                        width=3,
                        dash=(),
                    )
                    self.addtag_withtag(f"node:{el.element_id}", rect)
                    self._id_to_element[rect] = el.element_id
                    items.append(rect)
            except Exception:
                pass

        el.canvas_items = items

    def _draw_label(self, el: VPBElement):
        cx, cy = self.to_view(*el.center())
        text = el.name or el.element_id
        style = getattr(el, "_resolved_style", None)
        if not style:
            style = self._resolve_element_style(el.element_type, el)
        text_color = style.get("text_color", "#000000")
        is_ref = self._is_ref_subprocess(el)
        ref_display = ""
        if is_ref and getattr(el, "ref_file", ""):
            try:
                ref_display = os.path.basename(el.ref_file) or el.ref_file
            except Exception:
                ref_display = el.ref_file
        # SUBPROCESS Hinweis
        if is_ref and ref_display and el.element_type != "GROUP":
            text = f"{text}\n↳ {ref_display}"
        if el.element_type == "GROUP":
            members = getattr(el, "members", []) or []
            collapsed = getattr(el, "collapsed", False)
            auto_compact = False
            try:
                if not collapsed and self.view_scale <= 0.5:
                    auto_compact = True
            except Exception:
                pass
            # Beschriftung mit Anzahl
            addon = f" [{len(members)}]" if members else ""
            text = (el.name or el.element_id) + addon + (" (zu)" if collapsed else (" (kompakt)" if auto_compact else ""))
            if is_ref and ref_display:
                text = f"{text}\n↳ {ref_display}"
            # Für expandierte Gruppe versuchen, Label links oben am Rahmen zu platzieren
            if members and not collapsed and not auto_compact:
                xs: List[int] = []
                ys: List[int] = []
                for mid in members:
                    ch = self.elements.get(mid)
                    if ch:
                        xs.extend([ch.x - self.NODE_W // 2, ch.x + self.NODE_W // 2])
                        ys.extend([ch.y - self.NODE_H // 2, ch.y + self.NODE_H // 2])
                if xs and ys:
                    left, top = min(xs) - 20, min(ys) - 20
                    vx, vy = self.to_view(left + 6, top + 6)
                    label = self.create_text(vx, vy, anchor="nw", text=text, fill=text_color, font=("Segoe UI", 10, "bold"))
                else:
                    label = self.create_text(cx, cy, text=text, fill=text_color, font=("Segoe UI", 10, "bold"))
            else:
                label = self.create_text(cx, cy, text=text, fill=text_color, font=("Segoe UI", 10, "bold"))
        else:
            label = self.create_text(cx, cy, text=text, fill=text_color, font=("Segoe UI", 10, "bold"))
        self.addtag_withtag(f"node:{el.element_id}", label)
        self._id_to_element[label] = el.element_id
        el.canvas_items.append(label)

    def _resolve_connection_render(self, conn: VPBConnection) -> Optional[Tuple[VPBElement, VPBElement]]:
        redirect = getattr(self, "_collapsed_redirect", {}) or {}
        src_id = getattr(conn, "source_element", None)
        tgt_id = getattr(conn, "target_element", None)
        if not src_id or not tgt_id:
            return None
        eff_src_id = redirect.get(src_id, src_id)
        eff_tgt_id = redirect.get(tgt_id, tgt_id)
        if eff_src_id == eff_tgt_id and (eff_src_id != src_id or eff_tgt_id != tgt_id):
            return None
        src_el = self.elements.get(eff_src_id)
        tgt_el = self.elements.get(eff_tgt_id)
        if not src_el or not tgt_el:
            return None
        return src_el, tgt_el

    def _draw_connection(self, conn: VPBConnection):
        resolved_endpoints = self._resolve_connection_render(conn)
        if not resolved_endpoints:
            conn.canvas_item = None
            self._connection_points_cache.pop(conn.connection_id, None)
            return
        src, tgt = resolved_endpoints
        pts, resolved_mode = self._get_route_points(src, tgt, conn)
        style = CONNECTION_STYLES.get(conn.connection_type, {"fill": "#000", "width": 2, "dash": None})
        smooth = resolved_mode == 'curved'
        
        # Improved smoothing for curved connections (Mermaid-inspired)
        if smooth:
            smooth = True
            # Use higher splinesteps for smoother curves
            splinesteps = 12
        else:
            splinesteps = None
        
        # Pfeilstil bestimmen
        astyle = (getattr(conn, 'arrow_style', 'single') or 'single').lower()
        if astyle == 'none':
            arrow_opt = None
        elif astyle == 'double':
            arrow_opt = tk.BOTH
        else:
            arrow_opt = tk.LAST
        highlight_color = getattr(self, "_temp_highlight_connections", {}).get(conn.connection_id)
        line_color = style.get("fill", "#000")
        line_width = style.get("width", 2)
        if highlight_color:
            line_color = highlight_color
            line_width = max(line_width + 1, line_width)
        
        # Draw subtle shadow for depth (Blender-inspired)
        if resolved_mode == 'curved' and not highlight_color:
            shadow_offset = 2
            shadow_pts = [p + shadow_offset if i % 2 == 0 else p + shadow_offset for i, p in enumerate(pts)]
            shadow_item = self.create_line(
                *shadow_pts,
                arrow=arrow_opt,
                fill="#CCCCCC",
                width=line_width,
                smooth=smooth,
                splinesteps=splinesteps if smooth else None,
                dash=style.get("dash")
            )
            self.tag_lower(shadow_item)
            self._id_to_connection[shadow_item] = conn.connection_id
        
        # Main connection line
        conn.canvas_item = self.create_line(
            *pts,
            arrow=arrow_opt,
            fill=line_color,
            width=line_width,
            dash=style.get("dash"),
            smooth=smooth,
            splinesteps=splinesteps if smooth and splinesteps else None
        )
        self._connection_points_cache[conn.connection_id] = pts
        self._id_to_connection[conn.canvas_item] = conn.connection_id
        # Highlight bei Auswahl
        if getattr(self, 'selected_conn_id', None) == conn.connection_id:
            self.itemconfigure(conn.canvas_item, width=line_width + 2)

    def _element_view_geometry(self, el: VPBElement) -> Tuple[int, int, int, int, str]:
        cx, cy = self.to_view(*el.center())
        if getattr(el, "element_type", "") == "GROUP":
            bounds = self._group_bounds_model(el)
            if bounds:
                vx0, vy0 = self.to_view(bounds[0], bounds[1])
                vx1, vy1 = self.to_view(bounds[2], bounds[3])
                cx = int((vx0 + vx1) / 2)
                cy = int((vy0 + vy1) / 2)
                w = max(2, abs(vx1 - vx0))
                h = max(2, abs(vy1 - vy0))
                return cx, cy, w, h, "rect"
        w = max(30, int(self.NODE_W * self.view_scale))
        h = max(20, int(self.NODE_H * self.view_scale))
        style = self._resolve_element_style(getattr(el, "element_type", ""), el)
        shape = (style.get("shape") or "rect").lower()
        return cx, cy, w, h, shape

    def _element_view_box(self, el: VPBElement) -> Tuple[int, int, int, int]:
        """Gibt (cx, cy, hw, hh) in View-Koordinaten zurück."""
        cx, cy, w, h, _ = self._element_view_geometry(el)
        return cx, cy, w // 2, h // 2

    def _anchor_on_polygon(self, cx: int, cy: int, points: List[Tuple[int, int]], tx: int, ty: int) -> Tuple[int, int]:
        dx = tx - cx
        dy = ty - cy
        if dx == 0 and dy == 0:
            return cx, cy
        best_t: Optional[float] = None
        best_point: Tuple[float, float] = (cx, cy)
        n = len(points)
        for i in range(n):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % n]
            ex = x2 - x1
            ey = y2 - y1
            denom = dx * ey - dy * ex
            if abs(denom) < 1e-6:
                continue
            rx = x1 - cx
            ry = y1 - cy
            t = (rx * ey - ry * ex) / denom
            u = (rx * dy - ry * dx) / denom
            if t < 0:
                continue
            if u < -1e-6 or u > 1 + 1e-6:
                continue
            px = cx + t * dx
            py = cy + t * dy
            if best_t is None or t < best_t:
                best_t = t
                best_point = (px, py)
        if best_t is None:
            return cx, cy
        return int(round(best_point[0])), int(round(best_point[1]))

    def _edge_anchor(self, el: VPBElement, tx: int, ty: int, geom: Optional[Tuple[int, int, int, int, str]] = None) -> Tuple[int, int]:
        """Ermittelt den Ankerpunkt am Elementrand in Zielrichtung (View-Koordinaten)."""
        if geom is None:
            geom = self._element_view_geometry(el)
        cx, cy, w, h, shape = geom
        dx = tx - cx
        dy = ty - cy
        if dx == 0 and dy == 0:
            return cx, cy
        shape = (shape or "rect").lower()
        if shape in ("oval", "circle"):
            import math

            radius = max(1.0, min(w, h) / 2.0)
            length = math.hypot(dx, dy)
            if length < 1e-6:
                return int(round(cx + radius)), int(round(cy))
            scale = radius / length
            px = cx + dx * scale
            py = cy + dy * scale
            return int(round(px)), int(round(py))
        if shape == "diamond":
            pts_flat = _diamond_points(cx, cy, w, h)
            points = list(zip(pts_flat[::2], pts_flat[1::2]))
            return self._anchor_on_polygon(cx, cy, points, tx, ty)
        if shape == "hex":
            pts_flat = _hex_points(cx, cy, w, h)
            points = list(zip(pts_flat[::2], pts_flat[1::2]))
            return self._anchor_on_polygon(cx, cy, points, tx, ty)
        half_w = w / 2.0
        half_h = h / 2.0
        scale_x = half_w / abs(dx) if dx != 0 else float("inf")
        scale_y = half_h / abs(dy) if dy != 0 else float("inf")
        scale = min(scale_x, scale_y)
        if scale == float("inf"):
            if abs(dx) < 1e-6:
                offset = half_h if dy >= 0 else -half_h
                return int(round(cx)), int(round(cy + offset))
            offset = half_w if dx >= 0 else -half_w
            return int(round(cx + offset)), int(round(cy))
        px = cx + dx * scale
        py = cy + dy * scale
        return int(round(px)), int(round(py))

    def _connection_offset(self, element_id: str, attr: str, conn: VPBConnection) -> float:
        if not getattr(self, "connection_magnet_enabled", False):
            return 0.0
        step_value = getattr(self, "connection_magnet_step", 20) or 20
        try:
            step = float(max(1, int(step_value)))
        except Exception:
            step = 20.0
        redirect = getattr(self, "_collapsed_redirect", {}) or {}

        def _effective_endpoint(conn_obj: VPBConnection) -> Optional[str]:
            original = getattr(conn_obj, attr, None)
            if original is None:
                return None
            return redirect.get(original, original)

        siblings = [c for c in self.connections.values() if _effective_endpoint(c) == element_id]
        if conn not in siblings:
            siblings.append(conn)
        try:
            siblings.sort(key=lambda c: str(getattr(c, "connection_id", "")))
        except Exception:
            pass
        if not siblings:
            return 0.0
        center = (len(siblings) - 1) / 2.0
        try:
            index = siblings.index(conn)
        except ValueError:
            index = 0
        return (index - center) * step

    def _apply_connection_magnet(self, points: List[int]) -> List[int]:
        if not getattr(self, "connection_magnet_enabled", False):
            return points
        step_value = getattr(self, "connection_magnet_step", 20) or 20
        try:
            step = float(max(1, int(step_value)))
        except Exception:
            step = 20.0
        snapped: List[int] = []
        coords = list(points)
        pairs = len(coords) // 2
        for idx in range(pairs):
            x = coords[2 * idx]
            y = coords[2 * idx + 1]
            if 0 < idx < pairs - 1:
                x = int(round(x / step) * step)
                y = int(round(y / step) * step)
            snapped.extend([int(x), int(y)])
        return snapped

    def _get_route_points(self, src: VPBElement, tgt: VPBElement, conn: VPBConnection) -> Tuple[List[int], str]:
        """Berechnet die Routenpunkte in View-Koordinaten gemäß Verbindungseinstellungen."""
        src_geom = self._element_view_geometry(src)
        tgt_geom = self._element_view_geometry(tgt)
        scx, scy = src_geom[0], src_geom[1]
        tcx, tcy = tgt_geom[0], tgt_geom[1]
        dx = tcx - scx
        dy = tcy - scy
        horizontal = abs(dx) >= abs(dy)

        raw_mode = str(getattr(conn, "routing_mode", "auto") or "auto").lower()
        if raw_mode in {"auto", "default", "inherit"}:
            base_mode = str(getattr(self, "routing_style", "smart") or "smart").lower()
        else:
            base_mode = raw_mode
        alias_map = {
            "line": "straight",
            "gerade": "straight",
            "straight": "straight",
            "curved": "curved",
            "curve": "curved",
            "gebogen": "curved",
            "bogen": "curved",
            "orthogonal": "orthogonal",
            "right-angle": "orthogonal",
            "rightangle": "orthogonal",
            "geknickt": "orthogonal",
            "angled": "orthogonal",
            "knick": "orthogonal",
            "multi": "multi",
            "multi-kink": "multi",
            "multiknick": "multi",
            "mehrfach": "multi",
            "multiorthogonal": "multi",
            "smart": "smart",
            "smart+": "smart-plus",
            "smartplus": "smart-plus",
            "smart-plus": "smart-plus",
        }
        mode = alias_map.get(base_mode, "smart")
        if mode not in {"straight", "curved", "orthogonal", "multi", "smart", "smart-plus"}:
            mode = "smart"

        source_offset = self._connection_offset(src.element_id, "source_element", conn)
        target_offset = self._connection_offset(tgt.element_id, "target_element", conn)
        if horizontal:
            sy_hint = tcy + source_offset
            ty_hint = scy + target_offset
            sx, sy = self._edge_anchor(src, tcx, int(round(sy_hint)), src_geom)
            tx, ty = self._edge_anchor(tgt, scx, int(round(ty_hint)), tgt_geom)
        else:
            sx_hint = tcx + source_offset
            tx_hint = scx + target_offset
            sx, sy = self._edge_anchor(src, int(round(sx_hint)), tcy, src_geom)
            tx, ty = self._edge_anchor(tgt, int(round(tx_hint)), scy, tgt_geom)

        def _straight_points() -> List[int]:
            return [sx, sy, tx, ty]

        def _curved_points() -> List[int]:
            # Improved Bezier curve with better control points (Mermaid-inspired)
            distance = max(abs(tx - sx), abs(ty - sy))
            curve_strength = min(distance * 0.4, 100)  # Adaptive curve strength
            
            if horizontal:
                # Horizontal flow: control points offset horizontally
                cp1_x = int(sx + curve_strength)
                cp1_y = sy
                cp2_x = int(tx - curve_strength)
                cp2_y = ty
            else:
                # Vertical flow: control points offset vertically
                cp1_x = sx
                cp1_y = int(sy + curve_strength)
                cp2_x = tx
                cp2_y = int(ty - curve_strength)
            
            # Return cubic Bezier control points for smoother curves
            return [sx, sy, cp1_x, cp1_y, cp2_x, cp2_y, tx, ty]

        def _orthogonal_points() -> List[int]:
            if horizontal:
                midx = (sx + tx) // 2
                return [sx, sy, midx, sy, midx, ty, tx, ty]
            midy = (sy + ty) // 2
            return [sx, sy, sx, midy, tx, midy, tx, ty]

        def _multi_points() -> List[int]:
            step_value = getattr(self, "connection_magnet_step", 20) or 20
            try:
                step = int(max(10, abs(step_value)))
            except Exception:
                step = 20
            if horizontal:
                direction = 1 if tx >= sx else -1
                midx1 = sx + direction * step
                midx2 = tx - direction * step
                midy = (sy + ty) // 2
                return [
                    sx, sy,
                    midx1, sy,
                    midx1, midy,
                    midx2, midy,
                    midx2, ty,
                    tx, ty,
                ]
            direction = 1 if ty >= sy else -1
            midy1 = sy + direction * step
            midy2 = ty - direction * step
            midx = (sx + tx) // 2
            return [
                sx, sy,
                sx, midy1,
                midx, midy1,
                midx, midy2,
                tx, midy2,
                tx, ty,
            ]

        points: Optional[List[int]] = None
        resolved_mode = mode

        if mode == "smart-plus":
            grid_points = self._route_polyline_grid(sx, sy, tx, ty, conn, src, tgt)
            if grid_points:
                points = grid_points
                resolved_mode = "smart-plus"
            else:
                mode = "smart"
                resolved_mode = "smart"

        if points is None and mode == "smart":
            if horizontal:
                if abs(ty - sy) <= 15:
                    mode = "straight"
                else:
                    mode = "orthogonal"
            else:
                if abs(tx - sx) <= 15:
                    mode = "straight"
                else:
                    mode = "orthogonal"
            resolved_mode = mode

        if points is None:
            if mode == "straight":
                points = _straight_points()
            elif mode == "curved":
                points = _curved_points()
            elif mode == "multi":
                points = _multi_points()
            else:  # orthogonal
                points = _orthogonal_points()

        if resolved_mode != "smart-plus":
            points = self._apply_connection_magnet(points)
        return points, resolved_mode

    def _route_polyline_grid(
        self,
        sx: int,
        sy: int,
        tx: int,
        ty: int,
        conn: VPBConnection,
        src: VPBElement,
        tgt: VPBElement,
    ) -> Optional[List[int]]:
        try:
            cache_key = (
                sx,
                sy,
                tx,
                ty,
                int(round(self.view_scale * 100)),
                len(self.elements),
                len(self.connections),
            )
        except Exception:
            cache_key = None
        cache = getattr(conn, "_grid_route_cache", None)
        if isinstance(cache, dict) and cache_key and cache.get("key") == cache_key:
            cached_points = cache.get("points")
            if isinstance(cached_points, list) and cached_points:
                return [int(p) for p in cached_points]

        try:
            grid_step = int(max(24, min(120, self.NODE_W * max(self.view_scale, 0.6))))
        except Exception:
            grid_step = 60
        grid_step = max(24, min(grid_step, 140))
        margin = grid_step * 2

        xs = [sx, tx]
        ys = [sy, ty]
        try:
            for el in self.elements.values():
                cx, cy, hw, hh = self._element_view_box(el)
                xs.extend([cx - hw - margin, cx + hw + margin])
                ys.extend([cy - hh - margin, cy + hh + margin])
        except Exception:
            pass
        min_x = int(math.floor(min(xs) / grid_step) * grid_step)
        max_x = int(math.ceil(max(xs) / grid_step) * grid_step)
        min_y = int(math.floor(min(ys) / grid_step) * grid_step)
        max_y = int(math.ceil(max(ys) / grid_step) * grid_step)

        width = int((max_x - min_x) / grid_step) + 1
        height = int((max_y - min_y) / grid_step) + 1
        if width <= 0 or height <= 0:
            return None
        if width * height > 60000:
            return None

        def _to_cell(x: int, y: int) -> Tuple[int, int]:
            gx = int(math.floor((x - min_x) / grid_step))
            gy = int(math.floor((y - min_y) / grid_step))
            return gx, gy

        def _clamp_cell(cell: Tuple[int, int]) -> Tuple[int, int]:
            return (max(0, min(width - 1, cell[0])), max(0, min(height - 1, cell[1])))

        start = _clamp_cell(_to_cell(sx, sy))
        goal = _clamp_cell(_to_cell(tx, ty))
        if start == goal:
            return [sx, sy, tx, ty]

        blocked = set()
        penalty = set()

        src_id = getattr(src, "element_id", None)
        tgt_id = getattr(tgt, "element_id", None)

        try:
            for el in self.elements.values():
                cx, cy, hw, hh = self._element_view_box(el)
                pad_x = hw + grid_step // 2
                pad_y = hh + grid_step // 2
                if getattr(el, "element_id", None) in {src_id, tgt_id}:
                    pad_x = max(0, pad_x - grid_step // 2)
                    pad_y = max(0, pad_y - grid_step // 2)
                ix0 = max(0, int(math.floor((cx - pad_x - min_x) / grid_step)))
                ix1 = min(width - 1, int(math.ceil((cx + pad_x - min_x) / grid_step)))
                iy0 = max(0, int(math.floor((cy - pad_y - min_y) / grid_step)))
                iy1 = min(height - 1, int(math.ceil((cy + pad_y - min_y) / grid_step)))
                for gx in range(ix0, ix1 + 1):
                    for gy in range(iy0, iy1 + 1):
                        blocked.add((gx, gy))
        except Exception:
            pass

        clearance = max(6, grid_step // 2)
        try:
            for cid, pts in (getattr(self, "_connection_points_cache", {}) or {}).items():
                if not pts or len(pts) < 4 or cid == getattr(conn, "connection_id", None):
                    continue
                for idx in range(0, len(pts) - 2, 2):
                    x1, y1 = pts[idx], pts[idx + 1]
                    x2, y2 = pts[idx + 2], pts[idx + 3]
                    min_seg_x = min(x1, x2) - clearance
                    max_seg_x = max(x1, x2) + clearance
                    min_seg_y = min(y1, y2) - clearance
                    max_seg_y = max(y1, y2) + clearance
                    ix0 = max(0, int(math.floor((min_seg_x - min_x) / grid_step)))
                    ix1 = min(width - 1, int(math.ceil((max_seg_x - min_x) / grid_step)))
                    iy0 = max(0, int(math.floor((min_seg_y - min_y) / grid_step)))
                    iy1 = min(height - 1, int(math.ceil((max_seg_y - min_y) / grid_step)))
                    for gx in range(ix0, ix1 + 1):
                        for gy in range(iy0, iy1 + 1):
                            if (gx, gy) in blocked:
                                continue
                            penalty.add((gx, gy))
        except Exception:
            pass

        blocked.discard(start)
        blocked.discard(goal)

        def _heuristic(cell: Tuple[int, int]) -> float:
            return abs(cell[0] - goal[0]) + abs(cell[1] - goal[1])

        open_heap: List[Tuple[float, int, Tuple[int, int]]] = []
        g_score = {start: 0.0}
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        counter = 0
        heapq.heappush(open_heap, (_heuristic(start), counter, start))

        found = False
        while open_heap:
            _, _, current = heapq.heappop(open_heap)
            if current == goal:
                found = True
                break
            base_cost = g_score[current]
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nb = (current[0] + dx, current[1] + dy)
                if not (0 <= nb[0] < width and 0 <= nb[1] < height):
                    continue
                if nb in blocked:
                    continue
                step_cost = 1.0
                if nb in penalty:
                    step_cost += 4.0
                tentative = base_cost + step_cost
                if tentative + 1e-6 < g_score.get(nb, float("inf")):
                    came_from[nb] = current
                    g_score[nb] = tentative
                    counter += 1
                    heapq.heappush(open_heap, (tentative + _heuristic(nb), counter, nb))

        if not found:
            return None

        path_cells = [goal]
        while path_cells[-1] != start:
            prev = came_from.get(path_cells[-1])
            if prev is None:
                return None
            path_cells.append(prev)
        path_cells.reverse()

        coords: List[int] = []
        for gx, gy in path_cells:
            px = int(min_x + gx * grid_step)
            py = int(min_y + gy * grid_step)
            coords.extend([px, py])
        if len(coords) < 4:
            return None
        coords[0], coords[1] = sx, sy
        coords[-2], coords[-1] = tx, ty
        simplified = self._simplify_polyline(coords)
        if simplified:
            simplified[0], simplified[1] = sx, sy
            simplified[-2], simplified[-1] = tx, ty
        else:
            simplified = coords
        simplified = [int(p) for p in simplified]
        if cache_key:
            try:
                conn._grid_route_cache = {"key": cache_key, "points": simplified}
            except Exception:
                pass
        return simplified

    def _simplify_polyline(self, points: List[int]) -> List[int]:
        if not points:
            return []
        if len(points) <= 4:
            return [int(p) for p in points]
        simplified: List[int] = [int(points[0]), int(points[1])]
        prev_dir: Optional[Tuple[int, int]] = None
        for idx in range(2, len(points), 2):
            x = int(points[idx])
            y = int(points[idx + 1])
            last_x = simplified[-2]
            last_y = simplified[-1]
            dx = x - last_x
            dy = y - last_y
            if dx == 0 and dy == 0:
                continue
            dir_vec = (
                0 if dx == 0 else (1 if dx > 0 else -1),
                0 if dy == 0 else (1 if dy > 0 else -1),
            )
            if prev_dir is not None and dir_vec == prev_dir:
                simplified[-2] = x
                simplified[-1] = y
            else:
                simplified.extend([x, y])
                prev_dir = dir_vec
        return simplified

    def _floor_to(self, x: float, step: float) -> float:
        import math
        if step == 0:
            return x
        return math.floor(x / step) * step

    def _draw_time_axis(self):
        """Zeichnet eine horizontale Zeitachse durch y=0 mit Ticks im Intervall."""
        w = int(self.winfo_width() or 0)
        h = int(self.winfo_height() or 0)
        if w <= 0 or h <= 0:
            return
        # Sichtbarer Bereich in Model-Koordinaten
        x0_model, y0_model = self.to_model(0, 0)
        x1_model, y1_model = self.to_model(w, h)
        # Linie bei y=0
        vx0, vy = self.to_view(x0_model, 0)
        vx1, _ = self.to_view(x1_model, 0)
        line = self.create_line(vx0, vy, vx1, vy, fill=self.time_axis_color, width=1)
        self.addtag_withtag("time_axis", line)
        # Ticks
        step = float(self.time_axis_interval or 100.0)
        start = self._floor_to(x0_model, step)
        x = start
        font = ("Consolas", 8)
        while x <= x1_model + step:
            vx, _ = self.to_view(x, 0)
            if -50 <= vx <= w + 50:
                tick = self.create_line(vx, vy - 6, vx, vy + 6, fill=self.time_axis_color)
                self.addtag_withtag("time_axis", tick)
                lbl = self.create_text(vx + 2, vy - 8, text=f"{int(x)}", anchor="sw", font=font, fill=self.time_axis_color)
                self.addtag_withtag("time_axis", lbl)
            x += step

    def _draw_hierarchy_bars(self):
        """Zeichnet vertikale Hierarchie-Blöcke am linken Rand des Viewports.
        Y-Positionen folgen den Model-Koordinaten, X ist bildschirmfix (wie das Lineal)."""
        w = int(self.winfo_width() or 0)
        h = int(self.winfo_height() or 0)
        if w <= 0 or h <= 0:
            return
        bar_w = 70  # Pixelbreite des Bereichs
        x0 = 0
        x1 = bar_w
        for cat in (self.hierarchy_categories or []):
            try:
                name = str(cat.get('name', ''))
                y0 = float(cat.get('y0', 0.0))
                y1 = float(cat.get('y1', 0.0))
                color = str(cat.get('color', '#f2f2f2'))
            except Exception:
                continue
            # In View-Koordinaten umrechnen (nur Y transformieren)
            _, vy0 = self.to_view(0, y0)
            _, vy1 = self.to_view(0, y1)
            r = self.create_rectangle(x0, vy0, x1, vy1, fill=color, outline='#cccccc')
            self.addtag_withtag('hierbar', r)
            # Kategorie-Name
            cy = (vy0 + vy1) / 2
            t = self.create_text(x0 + 6, cy, text=name, anchor='w', font=("Segoe UI", 9), fill="#333333")
            self.addtag_withtag('hierbar', t)

    # ----- Auto-Layout (einfach) -----
    def auto_layout(self):
        """Ein einfaches automatisches Layout:
        - Graph in Ebenen aufteilen (grobe Topologie via BFS ab Start-ähnlichen Knoten)
        - Elemente spaltenweise anordnen, Verbindungen minimieren
        - Gruppen: lassen Mitgliederpositionen mitlaufen; Gruppe selbst mittig der Mitglieder
        """
        if not self.elements:
            return
        try:
            self.push_undo()
        except Exception:
            pass
        # 1) Graph-Kanten aus Verbindungen (nur existierende Elemente)
        outgoing: Dict[str, List[str]] = {}
        incoming_count: Dict[str, int] = {eid: 0 for eid in self.elements.keys()}
        for conn in self.connections.values():
            s, t = conn.source_element, conn.target_element
            if s in self.elements and t in self.elements:
                outgoing.setdefault(s, []).append(t)
                incoming_count[t] = incoming_count.get(t, 0) + 1
                incoming_count.setdefault(s, incoming_count.get(s, 0))
        # 2) Startkandidaten: START_EVENT oder Knoten mit in-degree 0
        starts = [eid for eid, el in self.elements.items() if el.element_type in ("START_EVENT", "EVENT")]
        if not starts:
            starts = [eid for eid, deg in incoming_count.items() if deg == 0]
        if not starts:
            starts = list(self.elements.keys())[:1]
        # 3) BFS-Schichten
        level: Dict[str, int] = {}
        from collections import deque
        dq = deque()
        for s in starts:
            level[s] = 0
            dq.append(s)
        while dq:
            u = dq.popleft()
            for v in outgoing.get(u, []) or []:
                if v not in level:
                    level[v] = level[u] + 1
                    dq.append(v)
        # Unbesuchte auf letzte Ebene setzen
        maxlvl = max(level.values()) if level else 0
        for eid in self.elements.keys():
            if eid not in level:
                level[eid] = maxlvl + 1
        # 4) Pro Ebene anordnen
        layers: Dict[int, List[str]] = {}
        for eid, lv in level.items():
            layers.setdefault(lv, []).append(eid)
        # Sortierung nach Typ für bessere Optik: Connectoren eher mittig
        def _type_weight(t: str) -> int:
            t = (t or "").upper()
            if "CONNECTOR" in t or t in ("AND_CONNECTOR", "OR_CONNECTOR", "XOR_CONNECTOR", "GATEWAY"):
                return 1
            if t in ("END_EVENT",):
                return 3
            return 2
        for lv in layers:
            layers[lv].sort(key=lambda eid: (_type_weight(self.elements[eid].element_type), self.elements[eid].name or self.elements[eid].element_id))
        # 5) Koordinaten vergeben
        x0, y0 = 200, 120
        x_step, y_step = int(self.NODE_W * 2.2), int(self.NODE_H * 2.0)
        for lv in sorted(layers.keys()):
            ids = layers[lv]
            n = len(ids)
            for i, eid in enumerate(ids):
                el = self.elements[eid]
                if el.element_type == "GROUP":
                    # Position der Gruppe wird nach den Mitgliedern gesetzt
                    continue
                el.x = x0 + lv * x_step
                # vertikal gleichmäßig
                el.y = y0 + i * y_step
        # 6) Gruppen mittig über Mitglieder platzieren und Größe implizit lassen
        for el in self.elements.values():
            if el.element_type == "GROUP":
                mem = getattr(el, "members", []) or []
                xs, ys = [], []
                for mid in mem:
                    ch = self.elements.get(mid)
                    if ch:
                        xs.append(ch.x)
                        ys.append(ch.y)
                if xs and ys:
                    el.x = int(sum(xs) / len(xs))
                    el.y = int(sum(ys) / len(ys))
        # 7) Neu zeichnen und Ansicht passend machen
        self.redraw_all()
        # Nach neuem Inhalt: Scrollbars/Minimap/Ruler aktualisieren
        try:
            self._notify_view_changed()
        except Exception:
            pass
        try:
            self.fit_to_diagram()
        except Exception:
            pass

    # ----- Stil-Auflösung -----
    def _normalize_dash(self, dash_val):
        try:
            if dash_val is None:
                return None
            if isinstance(dash_val, tuple):
                return dash_val
            if isinstance(dash_val, list):
                return tuple(int(x) for x in dash_val)
            if isinstance(dash_val, str):
                parts = [p.strip() for p in dash_val.split(',') if p.strip()]
                return tuple(int(x) for x in parts) if parts else None
        except Exception:
            return None
        return None

    def _hierarchy_style_for_element(self, el: Optional[VPBElement]) -> Tuple[Optional[str], Optional[str]]:
        if not el:
            return (None, None)
        hierarchy = getattr(el, "hierarchy", None)
        if not hierarchy:
            return (None, None)
        cache = self._hierarchy_color_cache
        if hierarchy in cache:
            return cache[hierarchy]
        cats = getattr(self, "hierarchy_categories", None) or []
        color: Optional[str] = None
        for cat in cats:
            try:
                if str(cat.get("name")) == hierarchy:
                    color = str(cat.get("color", "") or "")
                    break
            except Exception:
                continue
        if not color:
            cache[hierarchy] = (None, None)
            return (None, None)
        outline = color if color.startswith("#") else f"#{color}"
        fill = _lighten_hex(outline, 0.55)
        cache[hierarchy] = (outline, fill)
        return cache[hierarchy]

    def _resolve_element_style(self, element_type: str, element: Optional[VPBElement] = None) -> Dict:
        base = dict(ELEMENT_STYLES.get(element_type, {"shape": "rect", "fill": "#EEEEEE", "outline": "#888888"}))
        pdef = self.element_style_palette_defaults.get(element_type, {}) or {}
        over = self.element_style_overrides.get(element_type, {}) or {}
        style = {**base, **pdef, **over}
        if element is not None:
            custom = getattr(element, "style_override", None)
            if isinstance(custom, dict):
                for key, value in custom.items():
                    if value not in (None, ""):
                        style[key] = value
        # Dash normalisieren
        if "dash" in style:
            style["dash"] = self._normalize_dash(style.get("dash"))
        outline, fill = self._hierarchy_style_for_element(element)
        if outline:
            style["outline"] = outline
        if fill:
            if element and element.element_type == "GROUP":
                if getattr(element, "collapsed", False):
                    style["fill"] = fill
                else:
                    style.setdefault("fill", "")
            else:
                style["fill"] = fill
        return self._apply_contrast_defaults(style)

    def _apply_contrast_defaults(self, style: Dict) -> Dict:
        fill_value = style.get("fill")
        normalized_fill = _normalize_hex_color(fill_value)
        effective_background = normalized_fill or "#ffffff"

        text_color = _normalize_hex_color(style.get("text_color"))
        if not text_color:
            text_color = _best_contrast_color(effective_background, ("#000000", "#ffffff"), "#000000")

        outline_value = style.get("outline")
        normalized_outline = _normalize_hex_color(outline_value)
        outline_ratio = _contrast_ratio(effective_background, normalized_outline) if normalized_outline else None
        if outline_ratio is None or outline_ratio < 3.0:
            candidates = [text_color, "#000000", "#ffffff"]
            if outline_value:
                candidates.insert(0, outline_value)
            normalized_outline = _best_contrast_color(effective_background, candidates, text_color)

        style["text_color"] = text_color
        if normalized_outline:
            style["outline"] = normalized_outline
        if normalized_fill:
            style["fill"] = normalized_fill
        elif fill_value == "":
            style["fill"] = ""
        return style

    def set_element_style_overrides(self, overrides: Dict[str, Dict]):
        """Setzt globale Stil-Overrides und zeichnet neu."""
        try:
            self.element_style_overrides = dict(overrides or {})
        except Exception:
            self.element_style_overrides = {}
        self.redraw_all()

    def set_element_style_palette_defaults(self, defaults: Dict[str, Dict]):
        """Setzt Palette-Default-Stile pro Typ und zeichnet neu."""
        try:
            self.element_style_palette_defaults = dict(defaults or {})
        except Exception:
            self.element_style_palette_defaults = {}
        self.redraw_all()

    # ----- Container-/Gruppen-Helfer -----
    def _collect_group_descendants(self, gid: str) -> set[str]:
        """Alle direkten und indirekten Mitglieder einer Gruppe (rekursiv).
        Enthält keine gid selbst. Unbekannte/fehlende IDs werden übersprungen.
        """
        res: set[str] = set()
        try:
            g = self.elements.get(gid)
            if not g or getattr(g, 'element_type', '') != 'GROUP':
                return res
            stack = list(getattr(g, 'members', []) or [])
            while stack:
                mid = stack.pop()
                if mid in res:
                    continue
                if mid not in self.elements:
                    continue
                res.add(mid)
                ch = self.elements.get(mid)
                if ch and getattr(ch, 'element_type', '') == 'GROUP':
                    for sm in getattr(ch, 'members', []) or []:
                        if sm not in res:
                            stack.append(sm)
        except Exception:
            pass
        return res

    def _group_bounds_model(self, group: VPBElement) -> Optional[Tuple[float, float, float, float]]:
        if not group or getattr(group, 'element_type', '') != 'GROUP':
            return None
        members = getattr(group, 'members', []) or []
        collapsed = bool(getattr(group, 'collapsed', False))
        auto_compact = False
        try:
            if not collapsed and members and self.view_scale <= 0.5:
                auto_compact = True
        except Exception:
            auto_compact = False
        if members and not collapsed and not auto_compact:
            xs: List[int] = []
            ys: List[int] = []
            for mid in members:
                child = self.elements.get(mid)
                if not child:
                    continue
                xs.extend([child.x - self.NODE_W // 2, child.x + self.NODE_W // 2])
                ys.extend([child.y - self.NODE_H // 2, child.y + self.NODE_H // 2])
            if xs and ys:
                left = min(xs) - 20
                right = max(xs) + 20
                top = min(ys) - 20
                bottom = max(ys) + 20
                return (float(left), float(top), float(right), float(bottom))
        try:
            cx, cy = group.center()
        except Exception:
            cx, cy = getattr(group, 'x', 0), getattr(group, 'y', 0)
        half_w = self.NODE_W / 2.0
        half_h = self.NODE_H / 2.0
        return (float(cx - half_w), float(cy - half_h), float(cx + half_w), float(cy + half_h))

    # ----- Interaktion -----
    def _hit_test(self, event) -> Optional[str]:
        ids = self.find_overlapping(event.x, event.y, event.x, event.y)
        for cid in reversed(ids):  # oberstes zuerst
            # Priorität: Elemente > Verbindungen
            el_id = self._id_to_element.get(cid)
            if el_id:
                return el_id
        # Fallback: Gruppen anhand ihrer Bounds erkennen, auch wenn kein Canvas-Item getroffen wurde
        try:
            mx, my = self.to_model(event.x, event.y)
        except Exception:
            mx, my = None, None
        if mx is not None and my is not None:
            candidates: List[Tuple[float, str]] = []
            for el in self.elements.values():
                if getattr(el, 'element_type', '') != 'GROUP':
                    continue
                bounds = self._group_bounds_model(el)
                if not bounds:
                    continue
                left, top, right, bottom = bounds
                if left <= mx <= right and top <= my <= bottom:
                    area = max((right - left) * (bottom - top), 1.0)
                    candidates.append((area, el.element_id))
            if candidates:
                candidates.sort(key=lambda item: item[0])
                return candidates[0][1]
        return None

    def _hit_test_connection(self, event) -> Optional[str]:
        ids = self.find_overlapping(event.x, event.y, event.x, event.y)
        for cid in reversed(ids):
            conn_id = self._id_to_connection.get(cid)
            if conn_id:
                return conn_id
        return None

    def _on_press(self, event):
        # Hand-Tool (Space) aktiv? Dann keine Auswahl/Drag starten
        try:
            if getattr(self, '_space_pan_active', False):
                return
        except Exception:
            pass
        try:
            self.focus_set()
        except Exception:
            pass
        el_id = self._hit_test(event)
        conn_id = self._hit_test_connection(event)
        # Add-Modus: Klick in leeren Bereich erzeugt Element
        if self.add_mode:
            if not el_id and not conn_id:
                mx, my = self.to_model(event.x, event.y)
                if self.snap_to_grid:
                    g = self.grid_size
                    mx = int(round(mx / g) * g)
                    my = int(round(my / g) * g)
                et = self._add_element_type or "FUNCTION"
                nm = self._add_element_name or "Neues Element"
                el = self.add_element(et, nm, at=(int(mx), int(my)))
                # Ende Add-Modus
                self.add_mode = False
                self._add_element_type = None
                self._add_element_name = None
                payload = self._add_element_payload
                self._add_element_payload = None
                if payload and el:
                    try:
                        self._apply_add_payload(el, payload)
                    except Exception:
                        pass
                self._status(f"Hinzugefügt: {el.element_type} – {el.name}")
                return
            else:
                # Hinweis, dass leerer Bereich benötigt wird
                self._status("Bitte in einen leeren Bereich klicken, um das Element zu platzieren.")
                return
        if conn_id:
            # Verbindung selektieren
            self.selected_conn_id = conn_id
            self.selected_id = None
            self.selected_ids.clear()
            self.redraw_all()
            self._notify_selection(None, self.connections.get(conn_id))
            return
        if self.link_mode:
            if el_id and el_id in self.elements:
                if self.link_source_id is None:
                    self.link_source_id = el_id
                    ctyp = self._link_connection_type or "SEQUENCE"
                    self._status(f"Quelle gewählt – wählen Sie das Ziel. (Typ: {ctyp})")
                else:
                    if el_id != self.link_source_id:
                        ctyp = self._link_connection_type or "SEQUENCE"
                        conn = self.add_connection(self.link_source_id, el_id, ctyp)
                        # ggf. Pfeilstil aus Palette übernehmen
                        if conn and self._link_arrow_style:
                            conn.arrow_style = self._link_arrow_style
                            self.redraw_all()
                        if conn:
                            self.selected_conn_id = conn.connection_id
                            self.selected_id = None
                            try:
                                self.selected_ids.clear()
                            except Exception:
                                self.selected_ids = set()
                            self._notify_selection(None, conn)
                        self._status(f"Verbindung erstellt ({ctyp}): {self.link_source_id} -> {el_id}")
                    else:
                        self._status("Quelle und Ziel sind identisch – Verbindung verworfen.")
                    self.toggle_link_mode(False)
            return

        if el_id and el_id in self.elements:
            el = self.elements[el_id]
            # Event-Koordinate in Modell umrechnen
            mx, my = self.to_model(event.x, event.y)
            # Ctrl gedrückt? → Kopieren & die Kopien ziehen
            try:
                ctrl_pressed = bool(getattr(event, 'state', 0) & 0x0004)
            except Exception:
                ctrl_pressed = False
            if ctrl_pressed:
                # Quellen bestimmen: Multi-Auswahl oder nur getroffenes Element
                sources = list(self.selected_ids) if (self.selected_ids and el_id in self.selected_ids) else [el_id]
                if sources:
                    self.push_undo()
                    new_ids: list[str] = []
                    for sid in sources:
                        src = self.elements.get(sid)
                        if not src:
                            continue
                        name = f"{getattr(src, 'name', '')} (Kopie)" if getattr(src, 'name', '') else "Kopie"
                        new_el = self._add_element_no_undo(getattr(src, 'element_type', 'FUNCTION'), name, at=(src.x, src.y))
                        # Attribute kopieren
                        try:
                            new_el.description = getattr(src, 'description', '')
                            new_el.responsible_authority = getattr(src, 'responsible_authority', '')
                            new_el.legal_basis = getattr(src, 'legal_basis', '')
                            new_el.deadline_days = getattr(src, 'deadline_days', 0)
                            new_el.geo_reference = getattr(src, 'geo_reference', '')
                            new_el.hierarchy = getattr(src, 'hierarchy', '')
                            new_el.original_element_type = getattr(src, 'original_element_type', None)
                            try:
                                new_el.ref_file = getattr(src, 'ref_file', '')
                                if getattr(new_el, 'ref_file', ''):
                                    self._load_ref_preview(new_el)
                                elif self._is_ref_subprocess(new_el):
                                    self._ensure_ref_group(new_el)
                            except Exception:
                                new_el.ref_file = ''
                            if getattr(src, 'element_type', '') == 'GROUP':
                                new_el.collapsed = bool(getattr(src, 'collapsed', False))
                                # Wenn Ctrl+Alt: nur Container kopieren (ohne Mitgliederliste)
                                alt_pressed = bool(getattr(event, 'state', 0) & 0x0008)
                                if not alt_pressed:
                                    try:
                                        new_el.members = list(getattr(src, 'members', []) or [])
                                    except Exception:
                                        pass
                        except Exception:
                            pass
                        new_ids.append(new_el.element_id)
                    if new_ids:
                        # Kopien auswählen und Multi-Drag vorbereiten
                        self.selected_ids = set(new_ids)
                        self.selected_id = new_ids[0]
                        self.selected_conn_id = None
                        self._drag_multi = {nid: (mx - self.elements[nid].x, my - self.elements[nid].y) for nid in new_ids if nid in self.elements}
                        # Dummy-Drag-State setzen, damit _on_drag nicht frühzeitig abbricht
                        self._drag_state = ("__multi__", 0, 0)
                        self.redraw_all()
                        self._notify_selection(self.elements.get(self.selected_id), None)
                        self._status("Kopie(n) erzeugt – ziehen zum Platzieren (Strg+Ziehen)")
                        return
            if (el_id in self.selected_ids) and len(self.selected_ids) > 1:
                # Multi-Drag
                self.push_undo()
                alt_pressed = bool(getattr(event, 'state', 0) & 0x0008)
                drag_ids: set[str] = {eid for eid in self.selected_ids if eid in self.elements}
                if not alt_pressed:
                    additional: set[str] = set()
                    for eid in list(drag_ids):
                        elem = self.elements.get(eid)
                        if not elem or getattr(elem, 'element_type', '') != 'GROUP':
                            continue
                        additional.update(self._collect_group_descendants(eid))
                    drag_ids.update(eid for eid in additional if eid in self.elements)
                # Speichere Offset und Startposition je Element (für Shift-Achsen-Sperre)
                self._drag_origin_multi = {eid: (self.elements[eid].x, self.elements[eid].y) for eid in drag_ids}
                self._drag_multi = {eid: (mx - self.elements[eid].x, my - self.elements[eid].y) for eid in drag_ids}
                # Dummy-Drag-State setzen, damit _on_drag nicht frühzeitig abbricht
                self._drag_state = ("__multi__", 0, 0)
            else:
                dx = mx - el.x
                dy = my - el.y
                self.push_undo()
                # Startposition für Single-Drag merken (für Shift-Achsen-Sperre)
                self._drag_start_x = el.x
                self._drag_start_y = el.y
                # Wenn Gruppe: Multi-Drag über (rekursive) Mitglieder vorbereiten
                if el.element_type == "GROUP" and getattr(el, 'members', None):
                    # Alt gedrückt? → nur die Gruppe bewegen (Kinder bleiben stehen)
                    alt_pressed = bool(getattr(event, 'state', 0) & 0x0008)
                    if alt_pressed:
                        self._drag_multi = None
                        self._drag_origin_multi = None
                        self._drag_state = (el_id, int(dx), int(dy))
                    else:
                        ids = self._collect_group_descendants(el_id)
                        ids.add(el_id)
                        self._drag_origin_multi = {eid: (self.elements[eid].x, self.elements[eid].y) for eid in ids if eid in self.elements}
                        self._drag_multi = {eid: (mx - self.elements[eid].x, my - self.elements[eid].y) for eid in ids if eid in self.elements}
                        # Dummy-Drag-State setzen, damit _on_drag nicht frühzeitig abbricht
                        self._drag_state = ("__multi__", 0, 0)
                else:
                    self._drag_origin_multi = None
                    self._drag_state = (el_id, int(dx), int(dy))
                # Auswahl setzen (Single)
                if self.selected_id != el_id or self.selected_ids != {el_id}:
                    self.selected_id = el_id
                    self.selected_ids = {el_id}
                    self.redraw_all()
                    self._notify_selection(self.elements.get(self.selected_id), None)
        else:
            self._drag_state = None
            self._drag_multi = None
            if self.selected_id is not None or getattr(self, 'selected_conn_id', None) is not None or self.selected_ids:
                self.selected_id = None
                self.selected_conn_id = None
                self.selected_ids.clear()
                self.redraw_all()
                self._notify_selection(None, None)

    # --- Rechteckauswahl: Handler ---
    def _on_press_rect(self, event):
        # Nur starten, wenn kein Element getroffen wurde und nicht im Link-/Pan-Modus
        if self.link_mode or self._pan_last is not None:
            return
        if self._hit_test(event) or self._hit_test_connection(event):
            return
        self._sel_rect_start = (event.x, event.y)
        self._sel_rect_canvas_item = None

    def _on_drag_rect(self, event):
        if not self._sel_rect_start:
            return
        x0, y0 = self._sel_rect_start
        x1, y1 = event.x, event.y
        # Rechteck zeichnen/aktualisieren
        if self._sel_rect_canvas_item is None:
            self._sel_rect_canvas_item = self.create_rectangle(x0, y0, x1, y1, outline="#3399FF", dash=(4, 2))
        else:
            self.coords(self._sel_rect_canvas_item, x0, y0, x1, y1)

    def _on_release_rect(self, event):
        if not self._sel_rect_start:
            return
        x0, y0 = self._sel_rect_start
        x1, y1 = event.x, event.y
        # Aufräumen Rechteck
        if self._sel_rect_canvas_item is not None:
            try:
                self.delete(self._sel_rect_canvas_item)
            except Exception:
                pass
        self._sel_rect_canvas_item = None
        self._sel_rect_start = None
        # Auswahlbereich in Modellkoordinaten normalisieren
        mx0, my0 = self.to_model(x0, y0)
        mx1, my1 = self.to_model(x1, y1)
        left, right = sorted([mx0, mx1])
        top, bottom = sorted([my0, my1])
        # Elemente, deren Bounding-Box den Bereich schneidet, selektieren
        new_sel = set()
        half_w = self.NODE_W / 2
        half_h = self.NODE_H / 2
        for eid, el in self.elements.items():
            el_left = el.x - half_w
            el_right = el.x + half_w
            el_top = el.y - half_h
            el_bottom = el.y + half_h
            # Schnittmenge prüfen
            if not (el_right < left or el_left > right or el_bottom < top or el_top > bottom):
                new_sel.add(eid)
        # Falls eine Gruppe selektiert wird, ist es meist hilfreicher, nicht gleichzeitig alle Kinder zu selektieren
        groups = {eid for eid in new_sel if self.elements.get(eid) and self.elements[eid].element_type == "GROUP"}
        if groups:
            for gid in groups:
                # Entferne rekursive Nachfahren aus der Auswahl, um Doppeleffekte zu vermeiden
                mems = self._collect_group_descendants(gid)
                new_sel -= mems
        # Shift: toggeln, ansonsten ersetzen
        shift_pressed = bool(getattr(event, 'state', 0) & 0x0001)
        if shift_pressed:
            for eid in new_sel:
                if eid in self.selected_ids:
                    self.selected_ids.remove(eid)
                else:
                    self.selected_ids.add(eid)
        else:
            self.selected_ids = new_sel

        if self.selected_ids:
            # primary selection auf erstes Element setzen
            self.selected_id = next(iter(self.selected_ids))
        else:
            self.selected_id = None
        self.selected_conn_id = None
        self.redraw_all()
        self._notify_selection(self.elements.get(self.selected_id) if self.selected_id else None, None)

    def _on_drag(self, event):
        # Bei aktivem Hand-Tool wird das Panning separat gehandhabt
        try:
            if getattr(self, '_space_pan_active', False) and self._pan_last is not None:
                return
        except Exception:
            pass
        if not self._drag_state:
            return
        if self._drag_multi:
            mx, my = self.to_model(event.x, event.y)
            # Shift: Achsensperre relativ zu Startpositionen
            shift_pressed = bool(getattr(event, 'state', 0) & 0x0001)
            for eid, (dx, dy) in self._drag_multi.items():
                el = self.elements.get(eid)
                if not el:
                    continue
                nx = mx - dx
                ny = my - dy
                if shift_pressed and getattr(self, '_drag_origin_multi', None) and eid in self._drag_origin_multi:
                    ox, oy = self._drag_origin_multi[eid]
                    # dominante Achse bestimmen
                    if abs(nx - ox) >= abs(ny - oy):
                        ny = oy
                    else:
                        nx = ox
                if self.snap_to_grid:
                    g = self.grid_size
                    nx = int(round(nx / g) * g)
                    ny = int(round(ny / g) * g)
                el.x = int(nx)
                el.y = int(ny)
            self.redraw_all()
            return
        el_id, dx, dy = self._drag_state
        el = self.elements.get(el_id)
        if not el:
            return
        mx, my = self.to_model(event.x, event.y)
        nx = mx - dx
        ny = my - dy
        # Shift: Achsensperre relativ zur Startposition des Elements
        try:
            shift_pressed = bool(getattr(event, 'state', 0) & 0x0001)
        except Exception:
            shift_pressed = False
        if shift_pressed:
            ox = getattr(self, '_drag_start_x', el.x)
            oy = getattr(self, '_drag_start_y', el.y)
            if abs(nx - ox) >= abs(ny - oy):
                ny = oy
            else:
                nx = ox
        # magnetische Ausrichtung prüfen
        nx, ny, vline_x, hline_y = self._compute_alignment(el_id, nx, ny)
        self._draw_guides(vline_x, hline_y)
        if self.snap_to_grid:
            g = self.grid_size
            nx = int(round(nx / g) * g)
            ny = int(round(ny / g) * g)
        el.x = int(nx)
        el.y = int(ny)
        self.redraw_all()

    def _on_release(self, event):
        # Hand-Tool aktiv? Auswahl-Drag ignorieren (Pan endet in _on_left_pan_release)
        try:
            if getattr(self, '_space_pan_active', False) and self._pan_last is not None:
                return
        except Exception:
            pass
        self._drag_state = None
        self._drag_multi = None
        self._clear_guides()

    def _on_double_click(self, event):
        el_id = self._hit_test(event)
        if not el_id:
            # Verbindung umbenennen/Typ bearbeiten könnte hier folgen
            conn_id = self._hit_test_connection(event)
            if conn_id:
                # Für jetzt: Typ ändern Dialog
                types = sorted(CONNECTION_STYLES.keys())
                # Einfacher Dialog per simpledialog
                new_type = simpledialog.askstring("Verbindungstyp", f"Neuer Typ für {conn_id} (z.B. SEQUENCE):\n{', '.join(types)}", parent=self)
                if new_type:
                    self.set_connection_type(conn_id, new_type)
            return
        if el_id and el_id in self.elements:
            el = self.elements[el_id]
            self.push_undo()
            new_name = simpledialog.askstring("Element umbenennen", "Neuer Name:", initialvalue=el.name, parent=self)
            if new_name:
                el.name = new_name
                self.redraw_all()
                if self.selected_id == el_id:
                    self._notify_selection(self.elements.get(self.selected_id), None)

    # ----- Editieren -----
    def add_element(self, element_type: str = "FUNCTION", name: str = "Neues Element", at: Optional[Tuple[int, int]] = None,
                    element_id: Optional[str] = None, push_undo: bool = True) -> VPBElement:
        """Fügt ein Element hinzu.
        - element_id: optional vorgegebene ID (wird bei Kollision auto-incrementiert mit _1, _2 ...)
        - push_undo: kann bei Batch-Operationen (Merge) deaktiviert werden, wenn extern bereits ein Undo-Punkt gesetzt wurde.
        """
        if push_undo:
            self.push_undo()
        x, y = at or (200, 200)
        # ID bestimmen
        if element_id:
            base = element_id
            if base in self.elements:
                # Suffix-Strategie wie im Merge-Pfad
                import re
                m = re.match(r"^(.*?)(?:_(\d+))?$", base)
                stem = m.group(1) if m else base
                i = 1
                cand = base
                while cand in self.elements:
                    cand = f"{stem}_{i}"
                    i += 1
                element_id = cand
        else:
            idx = 1
            base = element_type[:1] if element_type else "E"
            element_id = f"{base}{idx:03d}"
            while element_id in self.elements:
                idx += 1
                element_id = f"{base}{idx:03d}"
        el = VPBElement(element_id, element_type, name, x, y)
        self.elements[element_id] = el
        self.redraw_all()
        return el

    def _add_element_no_undo(self, element_type: str, name: str, at: Optional[Tuple[int, int]] = None) -> VPBElement:
        """Interne Hilfe: Element hinzufügen ohne Undo/Redraw (für zusammengesetzte Operationen)."""
        idx = 1
        base = element_type[:1] if element_type else "E"
        new_id = f"{base}{idx:03d}"
        while new_id in self.elements:
            idx += 1
            new_id = f"{base}{idx:03d}"
        x, y = at or (200, 200)
        el = VPBElement(new_id, element_type, name, x, y)
        self.elements[new_id] = el
        return el

    def _apply_add_payload(self, element: VPBElement, payload: Dict[str, Any]) -> None:
        if not element or not isinstance(payload, dict):
            return

        style = payload.get("style")
        if isinstance(style, dict) and style:
            element.style_override = {
                key: style[key]
                for key in ("shape", "fill", "outline", "dash", "text_color")
                if key in style and style[key] not in (None, "")
            }

        properties = payload.get("properties")
        if isinstance(properties, dict):
            if properties.get("description") is not None:
                element.description = str(properties.get("description"))
            if properties.get("responsible_authority") is not None:
                element.responsible_authority = str(properties.get("responsible_authority"))
            if properties.get("legal_basis") is not None:
                element.legal_basis = str(properties.get("legal_basis"))
            if properties.get("deadline_days") is not None:
                try:
                    element.deadline_days = int(properties.get("deadline_days"))
                except Exception:
                    pass
            if properties.get("geo_reference") is not None:
                element.geo_reference = str(properties.get("geo_reference"))

        extras = payload.get("extras")
        if isinstance(extras, dict):
            for key, value in extras.items():
                try:
                    setattr(element, key, value)
                except Exception:
                    pass

        ref_info = payload.get("ref_process")
        if isinstance(ref_info, dict):
            name = ref_info.get("name")
            if isinstance(name, str) and name:
                element.name = name
            original_type = ref_info.get("original_type")
            if original_type:
                element.original_element_type = original_type
            ref_file = ref_info.get("ref_file")
            if isinstance(ref_file, str) and ref_file:
                element.ref_file = ref_file
            ref_id = ref_info.get("id")
            if ref_id:
                try:
                    element.ref_process_id = ref_id
                except Exception:
                    setattr(element, "ref_process_id", ref_id)
            auto_group = ref_info.get("auto_group", True)
            if getattr(element, "ref_file", ""):
                if auto_group:
                    self._ensure_ref_group(element)
                try:
                    self._load_ref_preview(element)
                except Exception:
                    pass

    def add_connection(self, source_id: Optional[str] = None, target_id: Optional[str] = None,
                       connection_type: str = "SEQUENCE", name: str = "", connection_id: Optional[str] = None,
                       source_element: Optional[str] = None, target_element: Optional[str] = None,
                       push_undo: bool = True) -> Optional[VPBConnection]:
        """Fügt eine Verbindung hinzu.
        Akzeptiert sowohl source_id/target_id als auch Alias-Namen source_element/target_element (Kompatibilität zum Merge-Code).
        connection_id kann optional vorgegeben werden; bei Kollision erfolgt Suffix-Anpassung (_1, _2 ...).
        """
        # Alias-Parameter auflösen
        if source_id is None:
            source_id = source_element
        if target_id is None:
            target_id = target_element
        if not source_id or not target_id:
            return None
        if source_id not in self.elements or target_id not in self.elements:
            return None
        if push_undo:
            self.push_undo()
        if connection_id:
            base = connection_id
            if base in self.connections:
                import re
                m = re.match(r"^(.*?)(?:_(\d+))?$", base)
                stem = m.group(1) if m else base
                i = 1
                cand = base
                while cand in self.connections:
                    cand = f"{stem}_{i}"
                    i += 1
                connection_id = cand
        else:
            idx = 1
            connection_id = f"C{idx:03d}"
            while connection_id in self.connections:
                idx += 1
                connection_id = f"C{idx:03d}"
        conn = VPBConnection(
            connection_id=connection_id,
            source_element=source_id,
            target_element=target_id,
            connection_type=connection_type,
            description=name or "",
            arrow_style="single",
            routing_mode=self.default_connection_routing or "auto",
        )
        self.connections[connection_id] = conn
        self.redraw_all()
        return conn

    def delete_selected(self) -> bool:
        targets = list(self.selected_ids) if self.selected_ids else ([self.selected_id] if self.selected_id else [])
        if not targets:
            return False
        self.push_undo()
        for eid in targets:
            if not eid:
                continue
            to_del = [cid for cid, c in self.connections.items() if c.source_element == eid or c.target_element == eid]
            for cid in to_del:
                self.connections.pop(cid, None)
            self.elements.pop(eid, None)
        self.selected_id = None
        self.selected_ids.clear()
        self.redraw_all()
        self._notify_selection(None, None)
        return True

    def duplicate_selected(self) -> Optional[VPBElement]:
        sources = list(self.selected_ids) if self.selected_ids else ([self.selected_id] if self.selected_id else [])
        if not sources:
            return None
        self.push_undo()
        last_new: Optional[VPBElement] = None
        for sid in sources:
            src = self.elements.get(sid)
            if not src:
                continue
            offset = int(getattr(self, 'duplicate_offset', 30) or 30)
            name = f"{src.name} (Kopie)" if src.name else "Kopie"
            el = self.add_element(src.element_type, name, at=(src.x + offset, src.y + offset))
            el.description = src.description
            el.responsible_authority = src.responsible_authority
            el.legal_basis = src.legal_basis
            el.deadline_days = src.deadline_days
            el.geo_reference = src.geo_reference
            el.original_element_type = getattr(src, "original_element_type", None)
            # SUBPROCESS: Referenz übernehmen
            try:
                el.ref_file = getattr(src, "ref_file", "")
                if getattr(el, "ref_file", ""):
                    self._load_ref_preview(el)
                elif self._is_ref_subprocess(el):
                    self._ensure_ref_group(el)
            except Exception:
                pass
            last_new = el
        if last_new:
            self.selected_id = last_new.element_id
            self.selected_ids = {last_new.element_id}
            self.redraw_all()
            self._notify_selection(last_new, None)
        return last_new

    def toggle_link_mode(self, enabled: Optional[bool] = None, connection_type: Optional[str] = None, arrow_style: Optional[str] = None):
        """Schaltet den Link-Modus um. Optional kann ein Verbindungstyp und Pfeilstil vorgegeben werden
        (z. B. aus der Palette)."""
        if enabled is None:
            self.link_mode = not self.link_mode
        else:
            self.link_mode = bool(enabled)
        # Typ/Pfeil übernehmen (falls angegeben)
        if connection_type:
            self._link_connection_type = connection_type
        if arrow_style:
            self._link_arrow_style = arrow_style
        if not self.link_mode:
            # Reset, wenn beendet
            self.link_source_id = None
            self._link_connection_type = None
            self._link_arrow_style = None
        else:
            self.link_source_id = None
        self.config(cursor='tcross' if self.link_mode else 'arrow')
        if self.link_mode:
            ttxt = f" [{self._link_connection_type}]" if self._link_connection_type else ""
            self._status(f"Link-Modus{ttxt} aktiv – Quelle klicken.")
        else:
            self._status("Link-Modus beendet")

    def start_link_mode(self, connection_type: str, arrow_style: Optional[str] = None):
        """Aktiviert den Link-Modus explizit für einen Verbindungstyp (aus Palette)."""
        self.toggle_link_mode(True, connection_type=connection_type, arrow_style=arrow_style)

    def cancel_link_mode(self):
        if self.link_mode:
            self.link_mode = False
            self.link_source_id = None
            self._link_connection_type = None
            self._link_arrow_style = None
            self.config(cursor='arrow')
            self._status("Link-Modus abgebrochen")

    # ---- Add-Modus Steuerung ----
    def start_add_mode(self, element_type: str, default_name: str = "Neues Element", payload: Optional[Dict[str, Any]] = None):
        self.add_mode = True
        self._add_element_type = element_type
        self._add_element_name = default_name
        self._add_element_payload = dict(payload) if isinstance(payload, dict) else None
        self.config(cursor='plus')
        self._status(f"Add-Modus: {element_type} – in leeren Bereich klicken.")

    def cancel_add_mode(self):
        if self.add_mode:
            self.add_mode = False
            self._add_element_type = None
            self._add_element_name = None
            self._add_element_payload = None
            self.config(cursor='arrow')
            self._status("Add-Modus abgebrochen")

    def set_snap_to_grid(self, enabled: bool):
        self.snap_to_grid = bool(enabled)
        self.redraw_all()

    def _draw_grid(self):
        g = self.grid_size
        w = int(self.winfo_width() or self.winfo_reqwidth() or 1200)
        h = int(self.winfo_height() or self.winfo_reqheight() or 800)
        # sichtbaren Bereich in Modellkoordinaten berechnen
        mx0, my0 = self.to_model(0, 0)
        mx1, my1 = self.to_model(w, h)
        # Start auf Raster runden
        import math
        start_x = int(math.floor(min(mx0, mx1) / g) * g)
        end_x = int(math.ceil(max(mx0, mx1) / g) * g)
        start_y = int(math.floor(min(my0, my1) / g) * g)
        end_y = int(math.ceil(max(my0, my1) / g) * g)
        # helle graue Linien, transformiert
        for x in range(start_x, end_x + 1, g):
            vx0, vy0 = self.to_view(x, start_y)
            vx1, vy1 = self.to_view(x, end_y)
            self.create_line(vx0, vy0, vx1, vy1, fill="#f0f0f0", tags=("grid",))
        for y in range(start_y, end_y + 1, g):
            vx0, vy0 = self.to_view(start_x, y)
            vx1, vy1 = self.to_view(end_x, y)
            self.create_line(vx0, vy0, vx1, vy1, fill="#f0f0f0", tags=("grid",))

    def set_status_callback(self, cb: Optional[Callable[[str], None]]):
        self._status_cb = cb

    def _status(self, msg: str):
        if self._status_cb:
            try:
                self._status_cb(msg)
            except Exception:
                pass

    def _notify_selection(self, element: Optional[VPBElement] = None, connection: Optional[VPBConnection] = None):
        if not self.on_selection_changed:
            return
        try:
            self.on_selection_changed(element, connection)
        except Exception:
            pass

    # ----- Ausrichtungshilfen (magnetische Guides) -----
    def _clear_guides(self):
        if getattr(self, '_guide_items', None):
            for gid in list(self._guide_items):
                try:
                    self.delete(gid)
                except Exception:
                    pass
            self._guide_items.clear()

    def _compute_alignment(self, moving_id: str, nx: float, ny: float) -> Tuple[float, float, Optional[float], Optional[float]]:
        """Berechnet Snap-Koordinaten und optionale Guide-Linien (in Modellkoordinaten).
        Rückgabe: (snapped_x, snapped_y, vline_x, hline_y)
        """
        el = self.elements.get(moving_id)
        if not el:
            return nx, ny, None, None
        threshold = getattr(self, '_align_threshold', 8)
        w = self.NODE_W
        h = self.NODE_H
        best_v = (None, threshold + 1)  # (x, dist)
        best_h = (None, threshold + 1)  # (y, dist)

        def edges_for(xc: float, yc: float) -> Tuple[float, float, float, float, float, float]:
            left = xc - w / 2
            right = xc + w / 2
            top = yc - h / 2
            bottom = yc + h / 2
            return left, right, top, bottom, xc, yc

        l, r, t, b, cx, cy = edges_for(nx, ny)
        for oid, other in self.elements.items():
            if oid == moving_id:
                continue
            ol, or_, ot, ob, ocx, ocy = edges_for(other.x, other.y)
            # Vertikal ausrichten (X)
            candidates_v = [
                (l, ol), (l, or_), (r, ol), (r, or_), (cx, ocx)
            ]
            for a, b2 in candidates_v:
                d = abs(a - b2)
                if d <= best_v[1]:
                    best_v = (b2 if a in (l, cx) else (b2 + w / 2 if a == r else b2), d)
                    # Korrektur:
                    if a == l:
                        nx = b2 + w / 2
                    elif a == r:
                        nx = b2 - w / 2
                    elif a == cx:
                        nx = b2
            # Horizontal ausrichten (Y)
            candidates_h = [
                (t, ot), (t, ob), (b, ot), (b, ob), (cy, ocy)
            ]
            for a, b2 in candidates_h:
                d = abs(a - b2)
                if d <= best_h[1]:
                    best_h = (b2 if a in (t, cy) else (b2 + h / 2 if a == b else b2), d)
                    if a == t:
                        ny = b2 + h / 2
                    elif a == b:
                        ny = b2 - h / 2
                    elif a == cy:
                        ny = b2

            # Update aktuelle Kanten nach eventueller Anpassung
            l, r, t, b, cx, cy = edges_for(nx, ny)

        vline_x = None
        hline_y = None
        if best_v[0] is not None and best_v[1] <= threshold:
            vline_x = best_v[0]
        if best_h[0] is not None and best_h[1] <= threshold:
            hline_y = best_h[0]
        return nx, ny, vline_x, hline_y

    def _draw_guides(self, vline_x: Optional[float], hline_y: Optional[float]):
        self._clear_guides()
        if vline_x is None and hline_y is None:
            return
        w = int(self.winfo_width() or self.winfo_reqwidth() or 1200)
        h = int(self.winfo_height() or self.winfo_reqheight() or 800)
        mx0, my0 = self.to_model(0, 0)
        mx1, my1 = self.to_model(w, h)
        if vline_x is not None:
            vx0, vy0 = self.to_view(vline_x, my0)
            vx1, vy1 = self.to_view(vline_x, my1)
            gid = self.create_line(vx0, vy0, vx1, vy1, fill="#66AAFF", dash=(4, 2), width=1)
            self._guide_items.append(gid)
        if hline_y is not None:
            vx0, vy0 = self.to_view(mx0, hline_y)
            vx1, vy1 = self.to_view(mx1, hline_y)
            gid = self.create_line(vx0, vy0, vx1, vy1, fill="#66AAFF", dash=(4, 2), width=1)
            self._guide_items.append(gid)

    # ----- Verbindung: Label/Typ/Löschen -----
    def _draw_connection_label(self, conn: VPBConnection):
        """Zeichnet ein Label auf der Verbindung (Mermaid-inspired with background)."""
        pts = self._connection_points_cache.get(conn.connection_id)
        if pts is None:
            resolved_endpoints = self._resolve_connection_render(conn)
            if not resolved_endpoints:
                return
            src, tgt = resolved_endpoints
            pts, _ = self._get_route_points(src, tgt, conn)
        if not pts:
            return
        # Label ungefähr in der Mitte platzieren
        if len(pts) >= 4:
            # nehme mittleres Segment
            mid_index = (len(pts) // 2) - 2
            x1, y1, x2, y2 = pts[mid_index], pts[mid_index + 1], pts[mid_index + 2], pts[mid_index + 3]
            mx, my = (x1 + x2) // 2, (y1 + y2) // 2
        else:
            mx, my = pts[0], pts[1]
        desc = (conn.description or "").strip()
        txt = desc if desc else (conn.connection_type or "SEQUENCE")
        
        # Create background rectangle for label (Mermaid-style)
        font_size = 9
        font = ("Segoe UI", font_size)
        
        # Estimate text dimensions
        text_width = len(txt) * font_size * 0.6
        text_height = font_size * 1.4
        padding = 4
        
        # Draw background
        bg = self.create_rectangle(
            mx - text_width/2 - padding, my - 10 - text_height/2 - padding,
            mx + text_width/2 + padding, my - 10 + text_height/2 + padding,
            fill="#FFFFFF", outline="#CCCCCC", width=1
        )
        self._id_to_connection[bg] = conn.connection_id
        
        # Draw label text
        label = self.create_text(mx, my - 10, text=txt, fill="#222", font=font)
        self._id_to_connection[label] = conn.connection_id
        
        # Ensure label is on top
        self.tag_raise(bg)
        self.tag_raise(label)

    def highlight_merge_results(
        self,
        *,
        added_elements: Optional[Iterable[str]] = None,
        updated_elements: Optional[Iterable[str]] = None,
        added_connections: Optional[Iterable[str]] = None,
        updated_connections: Optional[Iterable[str]] = None,
        duration_ms: int = 2200,
    ) -> None:
        try:
            if not hasattr(self, "_temp_highlight_elements"):
                return
            added_elements = [eid for eid in (added_elements or []) if eid and eid in self.elements]
            updated_elements = [eid for eid in (updated_elements or []) if eid and eid in self.elements]
            added_connections = [cid for cid in (added_connections or []) if cid and cid in self.connections]
            updated_connections = [cid for cid in (updated_connections or []) if cid and cid in self.connections]

            if not (added_elements or updated_elements or added_connections or updated_connections):
                return

            element_colors: Dict[str, str] = {}
            connection_colors: Dict[str, str] = {}
            for eid in added_elements:
                element_colors[eid] = "#2ecc71"  # Grün für neu
            for eid in updated_elements:
                element_colors.setdefault(eid, "#1f8ef1")  # Blau für aktualisiert/umbenannt
            for cid in added_connections:
                connection_colors[cid] = "#2ecc71"
            for cid in updated_connections:
                connection_colors.setdefault(cid, "#1f8ef1")

            self._temp_highlight_elements.update(element_colors)
            self._temp_highlight_connections.update(connection_colors)
            if self._temp_highlight_after:
                try:
                    self.after_cancel(self._temp_highlight_after)
                except Exception:
                    pass
            self.redraw_all()

            def _clear_highlights():
                try:
                    for eid in element_colors.keys():
                        self._temp_highlight_elements.pop(eid, None)
                    for cid in connection_colors.keys():
                        self._temp_highlight_connections.pop(cid, None)
                finally:
                    self._temp_highlight_after = None
                    self.redraw_all()

            self._temp_highlight_after = self.after(max(500, int(duration_ms)), _clear_highlights)
        except Exception:
            pass

    def delete_selected_connection(self) -> bool:
        cid = getattr(self, 'selected_conn_id', None)
        if not cid:
            return False
        self.push_undo()
        self.connections.pop(cid, None)
        self.selected_conn_id = None
        self.redraw_all()
        return True

    def set_connection_type(self, connection_id: str, new_type: str):
        conn = self.connections.get(connection_id)
        if not conn:
            return
        self.push_undo()
        if new_type not in CONNECTION_STYLES:
            # akzeptiere unbekannte, zeichne mit Default
            pass
        conn.connection_type = new_type
        self.redraw_all()

    # ----- Kontextmenü -----
    def _on_right_click(self, event):
        el_id = self._hit_test(event)
        conn_id = self._hit_test_connection(event)
        menu = tk.Menu(self, tearoff=0)
        if el_id and el_id in self.elements:
            self.selected_id = el_id
            self.selected_ids = {el_id}
            self.selected_conn_id = None
            self.redraw_all()
            menu.add_command(label="Umbenennen", command=lambda: self._rename_element(el_id))
            menu.add_command(label="Duplizieren", command=self.duplicate_selected)
            menu.add_command(label="Löschen", command=self.delete_selected)
            # SUBPROCESS-Aktionen
            el = self.elements.get(el_id)
            is_ref = self._is_ref_subprocess(el) if el else False
            if is_ref:
                menu.add_separator()
                menu.add_command(label="Subprozess expandieren (inline)", command=lambda eid=el_id: self.expand_subprocess_inline(eid))
                menu.add_command(label="Referenz öffnen (ersetzen)", command=lambda eid=el_id: self.open_subprocess_replace(eid))
            # GROUP Aktionen
            if el and el.element_type == "GROUP":
                menu.add_separator()
                menu.add_command(label=("Aufklappen" if getattr(el, 'collapsed', False) else "Zuklappen"), command=lambda eid=el_id: self._toggle_group_collapsed(eid))
                menu.add_command(label="Auswahl zu Gruppe hinzufügen", command=lambda eid=el_id: self._group_add_selection(eid))
                menu.add_command(label="Aus Auswahl aus Gruppe entfernen", command=lambda eid=el_id: self._group_remove_selection(eid))
            
            # TIME_LOOP Aktionen (ähnlich wie GROUP)
            if el and el.element_type == "TIME_LOOP":
                menu.add_separator()
                menu.add_command(label=("Aufklappen" if getattr(el, 'collapsed', False) else "Zuklappen"), command=lambda eid=el_id: self._toggle_group_collapsed(eid))
                menu.add_command(label="Auswahl zu Zeitschleife hinzufügen", command=lambda eid=el_id: self._group_add_selection(eid))
                menu.add_command(label="Auswahl aus Zeitschleife entfernen", command=lambda eid=el_id: self._group_remove_selection(eid))
        elif conn_id and conn_id in self.connections:
            self.selected_id = None
            self.selected_conn_id = conn_id
            self.selected_ids.clear()
            self.redraw_all()
            menu.add_command(label="Typ ändern", command=lambda: self._change_connection_type(conn_id))
            # Pfeilstil Untermenü mit aktuellem Zustand
            arrow_menu = tk.Menu(menu, tearoff=0)
            cur = self.connections.get(conn_id)
            arrow_var = tk.StringVar(value=(cur.arrow_style if cur and getattr(cur, 'arrow_style', None) else "single"))
            def _set_arrow(style: str, cid=conn_id):
                c = self.connections.get(cid)
                if not c:
                    return
                self.push_undo()
                c.arrow_style = style
                arrow_var.set(style)
                self.redraw_all()
            arrow_menu.add_radiobutton(label="Keine", value="none", variable=arrow_var, command=lambda: _set_arrow("none"))
            arrow_menu.add_radiobutton(label="Einfach", value="single", variable=arrow_var, command=lambda: _set_arrow("single"))
            arrow_menu.add_radiobutton(label="Doppelt", value="double", variable=arrow_var, command=lambda: _set_arrow("double"))
            menu.add_cascade(label="Pfeilspitzen", menu=arrow_menu)
            menu.add_command(label="Löschen", command=self.delete_selected_connection)
        else:
            menu.add_command(label="Element hier hinzufügen", command=lambda: self._add_element_here(event.x, event.y))
            menu.add_command(label="Link-Modus (L)", command=self.toggle_link_mode)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    # ----- Gruppe: Aktionen -----
    def _group_from_selection(self):
        sels = [eid for eid in self.selected_ids if eid in self.elements]
        if len(sels) < 1:
            messagebox.showinfo("Gruppe", "Bitte wählen Sie mindestens ein Element aus.")
            return
        self.push_undo()
        # Gruppe an Schwerpunkt platzieren
        xs = [self.elements[e].x for e in sels]
        ys = [self.elements[e].y for e in sels]
        cx = int(sum(xs) / len(xs)) if xs else 0
        cy = int(sum(ys) / len(ys)) if ys else 0
        g = self.add_element("GROUP", name="Gruppe", at=(cx, cy))
        g.members = list(sels)
        g.collapsed = False
        self.selected_ids = {g.element_id}
        self.selected_id = g.element_id
        self.redraw_all()
    
    def _time_loop_from_selection(self):
        """Erstellt eine Zeitschleife aus der aktuellen Auswahl."""
        sels = [eid for eid in self.selected_ids if eid in self.elements]
        if len(sels) < 1:
            messagebox.showinfo("Zeitschleife", "Bitte wählen Sie mindestens ein Element aus.")
            return
        self.push_undo()
        # Zeitschleife an Schwerpunkt platzieren
        xs = [self.elements[e].x for e in sels]
        ys = [self.elements[e].y for e in sels]
        cx = int(sum(xs) / len(xs)) if xs else 0
        cy = int(sum(ys) / len(ys)) if ys else 0
        
        # TIME_LOOP mit Default-Werten erstellen
        tl = self.add_element("TIME_LOOP", name="Zeitschleife", at=(cx, cy))
        tl.members = list(sels)
        tl.collapsed = False
        
        # Standard: Intervall-Typ mit 60 Minuten
        tl.loop_type = "interval"
        tl.loop_interval_minutes = 60
        
        self.selected_ids = {tl.element_id}
        self.selected_id = tl.element_id
        self.redraw_all()

    def _ungroup_selected(self):
        sid = self.selected_id
        el = self.elements.get(sid) if sid else None
        if not el or el.element_type != "GROUP":
            messagebox.showinfo("Gruppe", "Bitte wählen Sie eine Gruppe aus.")
            return
        # Undo
        self.push_undo()
        # 1) Alle Verbindungen zur/von der Gruppe löschen
        to_del = [cid for cid, c in self.connections.items() if c.source_element == sid or c.target_element == sid]
        for cid in to_del:
            self.connections.pop(cid, None)
        # 2) Gruppe selbst löschen
        self.elements.pop(sid, None)
        # 3) Falls andere Gruppen diese Gruppe als Mitglied führen, dort entfernen
        for gid, grp in list(self.elements.items()):
            if getattr(grp, 'element_type', '') == 'GROUP':
                try:
                    if sid in (grp.members or []):
                        grp.members = [m for m in grp.members if m != sid]
                except Exception:
                    pass
        # Auswahl aufheben und neu zeichnen
        self.selected_id = None
        try:
            self.selected_ids.clear()
        except Exception:
            self.selected_ids = set()
        self.redraw_all()

    def _toggle_group_collapsed(self, eid: str):
        g = self.elements.get(eid)
        if not g or getattr(g, "element_type", "") != "GROUP":
            return
        collapsed_before = bool(getattr(g, "collapsed", False))
        target_collapsed = not collapsed_before
        undo_pushed = False
        if not target_collapsed:
            ok, undo_pushed = self._ensure_group_reference_loaded(g)
            if not ok:
                return
        if not undo_pushed:
            self.push_undo()
        g.collapsed = target_collapsed
        self.redraw_all()

    def _group_add_selection(self, eid: str):
        g = self.elements.get(eid)
        if not g:
            return
        self.push_undo()
        mem = set(getattr(g, 'members', []) or [])
        for sid in list(self.selected_ids):
            if sid != eid and sid in self.elements:
                mem.add(sid)
        g.members = list(mem)
        self.redraw_all()

    def _group_remove_selection(self, eid: str):
        g = self.elements.get(eid)
        if not g:
            return
        self.push_undo()
        mem = set(getattr(g, 'members', []) or [])
        for sid in list(self.selected_ids):
            if sid in mem:
                mem.remove(sid)
        g.members = list(mem)
        self.redraw_all()

    # ----- SUBPROCESS: Hilfsfunktionen -----
    def set_open_reference_callback(self, cb: Optional[Callable[[str], None]]):
        self._open_reference_cb = cb

    def _resolve_ref_path(self, ref_file: str) -> Optional[str]:
        if not ref_file:
            return None
        try:
            if os.path.isabs(ref_file):
                return ref_file
            base = getattr(self, "base_dir", os.getcwd())
            cand = os.path.join(base, ref_file)
            if os.path.exists(cand):
                return cand
            cand2 = os.path.join(os.getcwd(), ref_file)
            return cand2
        except Exception:
            return ref_file

    def _load_ref_preview(self, element: VPBElement) -> None:
        if not element:
            return
        ref_file = getattr(element, "ref_file", "") or ""
        element.ref_inline_content = None
        element.ref_inline_error = None
        element.ref_inline_path = None
        element.ref_inline_truncated = False
        element.ref_source_mtime = None
        if not ref_file:
            return
        path = self._resolve_ref_path(ref_file)
        element.ref_inline_path = path
        if not path or not os.path.exists(path):
            element.ref_inline_error = f"Referenz nicht gefunden: {ref_file}"
            return
        try:
            with open(path, "r", encoding="utf-8") as fh:
                raw = fh.read()
        except UnicodeDecodeError:
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    raw = fh.read()
            except Exception as exc:
                element.ref_inline_error = f"Fehler beim Lesen: {exc}"
                return
        except Exception as exc:
            element.ref_inline_error = f"Fehler beim Lesen: {exc}"
            return
        preview = raw
        stripped = preview.lstrip()
        if stripped.startswith("{") or stripped.startswith("["):
            try:
                obj = json.loads(preview)
                preview = json.dumps(obj, ensure_ascii=False, indent=2)
            except Exception:
                pass
        try:
            max_chars = int(getattr(self, "ref_preview_limit", 0) or 0)
        except Exception:
            max_chars = 0
        truncated = False
        if max_chars > 0 and len(preview) > max_chars:
            preview = preview[:max_chars].rstrip() + "\n… (gekürzt)"
            truncated = True
        element.ref_inline_content = preview
        element.ref_inline_truncated = truncated
        try:
            element.ref_source_mtime = os.path.getmtime(path)
        except Exception:
            element.ref_source_mtime = None
        if self._is_ref_subprocess(element):
            self._ensure_ref_group(element)

    def _clear_ref_group_contents(self, group: VPBElement) -> None:
        prefix = f"{group.element_id}__"
        existing_members = set(getattr(group, "members", []) or [])
        targets = []
        for eid in list(self.elements.keys()):
            if eid in existing_members or (prefix and str(eid).startswith(prefix)):
                targets.append(eid)
        for eid in targets:
            for cid, conn in list(self.connections.items()):
                if conn.source_element == eid or conn.target_element == eid:
                    self.connections.pop(cid, None)
            self.elements.pop(eid, None)
            if getattr(self, "selected_id", None) == eid:
                self.selected_id = None
            try:
                if hasattr(self, "selected_ids") and eid in self.selected_ids:
                    self.selected_ids.discard(eid)
            except Exception:
                pass
        for cid in list(self.connections.keys()):
            if prefix and cid.startswith(prefix):
                self.connections.pop(cid, None)
        try:
            group.members = [mid for mid in getattr(group, "members", []) if mid not in targets]
        except Exception:
            group.members = []

    def _ensure_group_reference_loaded(self, group: VPBElement, force_reload: bool = False) -> Tuple[bool, bool]:
        """Lädt bzw. aktualisiert eine referenzierte vpb.json für die angegebene Gruppe."""
        if not group or getattr(group, "element_type", "") != "GROUP":
            return True, False
        ref_file = getattr(group, "ref_file", "")
        if not ref_file:
            return True, False
        path = self._resolve_ref_path(ref_file)
        if not path or not os.path.exists(path):
            messagebox.showerror("Gruppe", f"Referenz nicht gefunden:\n{path or ref_file}")
            self._status(f"Referenz nicht gefunden: {ref_file}")
            return False, False

        try:
            current_mtime = os.path.getmtime(path)
        except Exception:
            current_mtime = None

        cached_mtime = getattr(group, "_ref_mtime", None)
        loaded = bool(getattr(group, "_ref_loaded", False))
        needs_reload = force_reload
        if loaded and not needs_reload:
            if current_mtime is not None and cached_mtime is not None:
                needs_reload = current_mtime > cached_mtime + 1e-6
            else:
                needs_reload = False
        if loaded and not needs_reload:
            return True, False

        try:
            with open(path, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
        except Exception as exc:
            messagebox.showerror("Gruppe", f"Fehler beim Laden der Referenz:\n{exc}")
            self._status(f"Fehler beim Laden: {ref_file}")
            return False, False

        if not isinstance(payload, dict):
            payload = {}
        raw_elements = payload.get("elements", []) if isinstance(payload, dict) else []
        raw_connections = payload.get("connections", []) if isinstance(payload, dict) else []
        if not isinstance(raw_elements, list):
            raw_elements = []
        if not isinstance(raw_connections, list):
            raw_connections = []

        undo_done = False
        if loaded and needs_reload:
            self.push_undo()
            undo_done = True
            self._clear_ref_group_contents(group)
            setattr(group, "_ref_loaded", False)
            loaded = False

        if not raw_elements:
            if not undo_done and loaded:
                self.push_undo()
                undo_done = True
                self._clear_ref_group_contents(group)
            setattr(group, "_ref_loaded", True)
            setattr(group, "_ref_mtime", current_mtime)
            group.ref_source_mtime = current_mtime
            group.members = []
            self._status(f"Referenz {os.path.basename(path)} enthält keine Elemente")
            return True, undo_done

        normalised_elements: List[Tuple[str, Dict]] = []
        id_map: Dict[str, str] = {}
        existing_ids = set(self.elements.keys())
        prefix = f"{group.element_id}__"
        for idx, entry in enumerate(raw_elements):
            if not isinstance(entry, dict):
                continue
            raw_id = entry.get("element_id")
            if raw_id is None or str(raw_id).strip() == "":
                raw_id = f"EL{idx + 1:04d}"
            key = str(raw_id)
            new_id = prefix + key
            while new_id in existing_ids or new_id in id_map.values():
                new_id = "_" + new_id
            id_map[key] = new_id
            normalised_elements.append((key, entry))
            existing_ids.add(new_id)

        if not normalised_elements:
            if not undo_done and loaded:
                self.push_undo()
                undo_done = True
                self._clear_ref_group_contents(group)
            setattr(group, "_ref_loaded", True)
            setattr(group, "_ref_mtime", current_mtime)
            group.ref_source_mtime = current_mtime
            group.members = []
            self._status(f"Referenz {os.path.basename(path)} enthält nur ungültige Elemente")
            return True, undo_done

        try:
            xs = [int(entry.get("x", 0)) for _, entry in normalised_elements]
            ys = [int(entry.get("y", 0)) for _, entry in normalised_elements]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            cx = (min_x + max_x) / 2
            cy = (min_y + max_y) / 2
        except Exception:
            cx, cy = float(group.x), float(group.y)
        dx = int(group.x - cx)
        dy = int(group.y - cy)

        if not undo_done:
            self.push_undo()
            undo_done = True
        elif getattr(group, "members", None):
            self._clear_ref_group_contents(group)

        new_member_ids: List[str] = []
        for key, entry in normalised_elements:
            new_id = id_map.get(key)
            if not new_id:
                continue
            try:
                ex = int(entry.get("x", group.x)) + dx
                ey = int(entry.get("y", group.y)) + dy
            except Exception:
                ex, ey = group.x, group.y
            obj = VPBElement(
                element_id=new_id,
                element_type=entry.get("element_type", "FUNCTION"),
                name=entry.get("name", key),
                x=ex,
                y=ey,
                description=entry.get("description", ""),
                responsible_authority=entry.get("responsible_authority", ""),
                legal_basis=entry.get("legal_basis", ""),
                deadline_days=int(entry.get("deadline_days", 0) or 0),
                geo_reference=entry.get("geo_reference", ""),
            )
            obj.ref_file = str(entry.get("ref_file", "") or "")
            if getattr(obj, "ref_file", ""):
                try:
                    self._load_ref_preview(obj)
                except Exception:
                    obj.ref_inline_error = "Vorschau konnte nicht geladen werden"
            if getattr(obj, "element_type", "") == "GROUP":
                members = []
                for mid in entry.get("members", []) or []:
                    mapped = id_map.get(str(mid))
                    if mapped:
                        members.append(mapped)
                obj.members = members
                obj.collapsed = bool(entry.get("collapsed", False))
            self.elements[new_id] = obj
            new_member_ids.append(new_id)

        new_connections = 0
        for entry in raw_connections:
            if not isinstance(entry, dict):
                continue
            src_key = str(entry.get("source_element", "") or "")
            tgt_key = str(entry.get("target_element", "") or "")
            src_id = id_map.get(src_key)
            tgt_id = id_map.get(tgt_key)
            if not src_id or not tgt_id:
                continue
            raw_cid = entry.get("connection_id")
            if raw_cid is None or str(raw_cid).strip() == "":
                raw_cid = f"C{len(self.connections) + new_connections + 1:04d}"
            new_cid = prefix + str(raw_cid)
            while new_cid in self.connections:
                new_cid = "_" + new_cid
            conn = VPBConnection(
                connection_id=new_cid,
                source_element=src_id,
                target_element=tgt_id,
                connection_type=entry.get("connection_type", "SEQUENCE"),
                description=entry.get("description", ""),
                arrow_style=str(entry.get("arrow_style", "single") or "single"),
                routing_mode=str(entry.get("routing_mode", "auto") or "auto"),
            )
            self.connections[new_cid] = conn
            new_connections += 1

        group.members = new_member_ids
        setattr(group, "_ref_loaded", True)
        setattr(group, "_ref_mtime", current_mtime)
        group.ref_source_mtime = current_mtime
        self._status(
            f"{len(new_member_ids)} Elemente und {new_connections} Verbindungen aus {os.path.basename(path)} geladen"
        )
        return True, undo_done

    def expand_subprocess_inline(self, el_id: str):
        el = self.elements.get(el_id)
        if not el or not self._is_ref_subprocess(el):
            return
        ref_file = getattr(el, "ref_file", "")
        if not ref_file:
            return
        path = self._resolve_ref_path(ref_file)
        if not path or not os.path.exists(path):
            messagebox.showerror("SUBPROCESS", f"Referenz nicht gefunden:\n{path or ref_file}")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("SUBPROCESS", f"Fehler beim Laden:\n{e}")
            return
        # Elemente/Verbindungen extrahieren
        sub_elems = data.get("elements", []) if isinstance(data, dict) else []
        sub_conns = data.get("connections", []) if isinstance(data, dict) else []
        if not sub_elems:
            messagebox.showinfo("SUBPROCESS", "Referenz enthält keine Elemente.")
            return
        # Bounding Box & Center des Subdiagramms
        try:
            xs = [int(e.get("x", 0)) for e in sub_elems]
            ys = [int(e.get("y", 0)) for e in sub_elems]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            cx = (min_x + max_x) / 2
            cy = (min_y + max_y) / 2
        except Exception:
            cx, cy = 0.0, 0.0
        # Ziel-Center rechts vom SUBPROCESS-Knoten
        target_cx = el.x + self.NODE_W + 200
        target_cy = el.y
        dx = int(target_cx - cx)
        dy = int(target_cy - cy)
        # Präfix zur Kollisionsvermeidung
        prefix = f"{el.element_id}__"
        # Undo
        self.push_undo()
        # Elemente anlegen
        id_map: Dict[str, str] = {}
        for se in sub_elems:
            old_id = str(se.get("element_id"))
            new_id = prefix + old_id
            # falls Kollisionsgefahr, erweitern
            while new_id in self.elements:
                new_id = "_" + new_id
            id_map[old_id] = new_id
            typ = se.get("element_type", "FUNCTION")
            name = se.get("name", old_id)
            try:
                ex = int(se.get("x", 0)) + dx
                ey = int(se.get("y", 0)) + dy
            except Exception:
                ex, ey = el.x, el.y
            obj = VPBElement(
                element_id=new_id,
                element_type=typ,
                name=name,
                x=ex,
                y=ey,
                description=se.get("description", ""),
                responsible_authority=se.get("responsible_authority", ""),
                legal_basis=se.get("legal_basis", ""),
                deadline_days=int(se.get("deadline_days", 0) or 0),
                geo_reference=se.get("geo_reference", ""),
            )
            obj.ref_file = str(se.get("ref_file", "") or "")
            if getattr(obj, "ref_file", ""):
                try:
                    self._load_ref_preview(obj)
                except Exception:
                    obj.ref_inline_error = "Vorschau konnte nicht geladen werden"
            obj.original_element_type = se.get("original_element_type")
            self.elements[new_id] = obj
        # Verbindungen anlegen
        for sc in sub_conns:
            old_cid = str(sc.get("connection_id", "")) or f"C{len(self.connections)+1:03d}"
            new_cid = prefix + old_cid
            while new_cid in self.connections:
                new_cid = "_" + new_cid
            src_old = sc.get("source_element")
            tgt_old = sc.get("target_element")
            src_new = id_map.get(src_old, src_old)
            tgt_new = id_map.get(tgt_old, tgt_old)
            conn = VPBConnection(
                connection_id=new_cid,
                source_element=src_new,
                target_element=tgt_new,
                connection_type=sc.get("connection_type", "SEQUENCE"),
                description=sc.get("description", ""),
                arrow_style=str(sc.get("arrow_style", "single") or "single"),
                routing_mode=str(sc.get("routing_mode", "auto") or "auto"),
            )
            self.connections[new_cid] = conn
        self.redraw_all()
        self._status(f"Subprozess expandiert: {os.path.basename(path)} → {len(sub_elems)} Elemente")

    def open_subprocess_replace(self, el_id: str):
        el = self.elements.get(el_id)
        if not el or not self._is_ref_subprocess(el):
            return
        ref_file = getattr(el, "ref_file", "")
        if not ref_file:
            return
        path = self._resolve_ref_path(ref_file)
        if not path or not os.path.exists(path):
            messagebox.showerror("SUBPROCESS", f"Referenz nicht gefunden:\n{path or ref_file}")
            return
        if hasattr(self, "_open_reference_cb") and callable(self._open_reference_cb):
            try:
                self._open_reference_cb(path)
            except Exception as e:
                messagebox.showerror("SUBPROCESS", f"Konnte Referenz nicht öffnen:\n{e}")
        else:
            messagebox.showinfo("SUBPROCESS", f"Öffnen nicht verfügbar. Pfad:\n{path}")

    def _rename_element(self, el_id: str):
        el = self.elements.get(el_id)
        if not el:
            return
        new_name = simpledialog.askstring("Element umbenennen", "Neuer Name:", initialvalue=el.name, parent=self)
        if new_name:
            el.name = new_name
            self.redraw_all()
            if self.selected_id == el_id:
                self._notify_selection(el, None)

    def _change_connection_type(self, conn_id: str):
        types = sorted(CONNECTION_STYLES.keys())
        new_type = simpledialog.askstring("Verbindungstyp", f"Neuer Typ für {conn_id} (z.B. SEQUENCE):\n{', '.join(types)}", parent=self)
        if new_type:
            self.set_connection_type(conn_id, new_type)

    def _add_element_here(self, x: int, y: int):
        mx, my = self.to_model(x, y)
        if self.snap_to_grid:
            g = self.grid_size
            mx = int(round(mx / g) * g)
            my = int(round(my / g) * g)
        el = self.add_element("FUNCTION", "Neues Element", at=(int(mx), int(my)))
        self.selected_id = el.element_id
        self.selected_ids = {el.element_id}
        self.selected_conn_id = None
        self.redraw_all()
        self._notify_selection(el, None)

    # ----- Auswahl (Shift-Klick) -----
    def _on_shift_press(self, event):
        el_id = self._hit_test(event)
        if not el_id:
            return
        if el_id in self.selected_ids:
            self.selected_ids.remove(el_id)
            if self.selected_id == el_id:
                self.selected_id = next(iter(self.selected_ids), None)
        else:
            self.selected_ids.add(el_id)
            self.selected_id = el_id
        self.selected_conn_id = None
        self.redraw_all()
        self._notify_selection(self.elements.get(self.selected_id) if self.selected_id else None, None)

    # ----- Zoom & Pan -----
    def _on_mousewheel_zoom(self, event):
        # Unterstützt Windows (MouseWheel) und X11 (Button-4/5)
        direction = 0
        if hasattr(event, 'num') and event.num in (4, 5):
            direction = 1 if event.num == 4 else -1
        elif hasattr(event, 'delta') and event.delta != 0:
            direction = 1 if event.delta > 0 else -1
        if direction == 0:
            return
        factor = 1.1 if direction > 0 else (1 / 1.1)
        mx, my = self.to_model(event.x, event.y)
        new_scale = max(getattr(self, '_min_zoom', 0.1), min(getattr(self, '_max_zoom', 5.0), self.view_scale * factor))
        self.view_scale = new_scale
        self.view_tx = event.x - mx * self.view_scale
        self.view_ty = event.y - my * self.view_scale
        self.redraw_all()
        self._notify_view_changed()

    def _on_canvas_configure(self, event):
        # Bei Größenänderung neu zeichnen (z.B. Grid-Dichte)
        try:
            self.redraw_all()
            self._notify_view_changed()
        except Exception:
            pass

    def _on_pan_start(self, event):
        self._pan_last = (event.x, event.y)
        self.config(cursor="fleur")

    def _on_pan_move(self, event):
        if not self._pan_last:
            return
        lx, ly = self._pan_last
        dx = event.x - lx
        dy = event.y - ly
        self.view_tx += dx
        self.view_ty += dy
        self._pan_last = (event.x, event.y)
        self.redraw_all()
        self._notify_view_changed()

    def _on_pan_end(self, event):
        self._pan_last = None
        self.config(cursor="arrow")

    # ----- Alternative Navigations-Handler (ohne MMB) -----
    def _on_space_down(self, event):
        try:
            self._space_pan_active = True
            # Cursor nur ändern, wenn nicht bereits im Pan-Drag
            if self._pan_last is None:
                self.config(cursor="fleur")
        except Exception:
            pass

    def _on_space_up(self, event):
        try:
            self._space_pan_active = False
            if self._pan_last is None:
                self.config(cursor="arrow")
        except Exception:
            pass

    def _on_delete_key(self, event):
        try:
            if getattr(self, '_space_pan_active', False) and self._pan_last is not None:
                return
        except Exception:
            pass
        if getattr(self, 'link_mode', False):
            return
        removed = False
        try:
            removed = bool(self.delete_selected())
        except Exception:
            removed = False
        if removed:
            try:
                self._status("Auswahl gelöscht.")
            except Exception:
                pass
            return "break"
        return None

    def _on_left_pan_press(self, event):
        try:
            if self._space_pan_active:
                self._on_pan_start(event)
                return "break"
        except Exception:
            pass

    def _on_left_pan_move(self, event):
        try:
            if self._space_pan_active and self._pan_last is not None:
                self._on_pan_move(event)
                return "break"
        except Exception:
            pass

    def _on_left_pan_release(self, event):
        try:
            if self._space_pan_active:
                self._on_pan_end(event)
                return "break"
        except Exception:
            pass

    # ----- Mausrad-Modus -----
    def set_mousewheel_mode(self, mode: str) -> None:
        if mode not in {"zoom-primary", "pan-primary"}:
            mode = "zoom-primary"
        self.mousewheel_mode = mode

    def get_mousewheel_mode(self) -> str:
        return getattr(self, "mousewheel_mode", "zoom-primary")

    def _on_mousewheel_primary(self, event):
        mode = self.get_mousewheel_mode()
        if mode == "pan-primary":
            return self._on_mousewheel_pan_v(event)
        return self._on_mousewheel_zoom(event)

    def _on_mousewheel_ctrl(self, event):
        mode = self.get_mousewheel_mode()
        if mode == "pan-primary":
            self._on_mousewheel_zoom(event)
        else:
            self._on_mousewheel_pan_v(event)
        return "break"

    def _on_mousewheel_pan_v(self, event):
        """Alt+Mausrad: vertikal pannen (Pixel-basiert)."""
        try:
            direction = 0
            if hasattr(event, 'num') and event.num in (4, 5):
                direction = 1 if event.num == 4 else -1
            elif hasattr(event, 'delta') and event.delta != 0:
                direction = 1 if event.delta > 0 else -1
            if direction == 0:
                return
            step = -direction * int(getattr(self, "pan_step_small_px", 60) or 60)
            self.pan_pixels(0, step)
            return "break"
        except Exception:
            pass

    def _on_mousewheel_pan_h(self, event):
        """Shift+Mausrad: horizontal pannen (Pixel-basiert)."""
        try:
            direction = 0
            if hasattr(event, 'num') and event.num in (4, 5):
                direction = 1 if event.num == 4 else -1
            elif hasattr(event, 'delta') and event.delta != 0:
                direction = 1 if event.delta > 0 else -1
            if direction == 0:
                return
            step = -direction * int(getattr(self, "pan_step_small_px", 60) or 60)
            self.pan_pixels(step, 0)
            return "break"
        except Exception:
            pass

    # ----- Undo/Redo -----
    def _snapshot(self) -> Dict:
        return self.to_dict()

    def _load_snapshot(self, data: Dict):
        # Lädt Zustand ohne Historienänderung
        self.load_from_dict(data)

    def push_undo(self):
        try:
            self._undo_stack.append(self._snapshot())
            if len(self._undo_stack) > self._max_history:
                self._undo_stack = self._undo_stack[-self._max_history:]
            self._redo_stack.clear()
        except Exception:
            pass

    def undo(self):
        if not self._undo_stack:
            self._status("Nichts zum Rückgängig machen")
            return
        current = self._snapshot()
        state = self._undo_stack.pop()
        self._redo_stack.append(current)
        self._load_snapshot(state)
        self._status("Rückgängig")

    def redo(self):
        if not self._redo_stack:
            self._status("Nichts zum Wiederholen")
            return
        current = self._snapshot()
        state = self._redo_stack.pop()
        self._undo_stack.append(current)
        self._load_snapshot(state)
        self._status("Wiederholen")

    # ----- Ansicht: Reset & Fit -----
    def reset_view(self):
        self.view_scale = 1.0
        self.view_tx = 0.0
        self.view_ty = 0.0
        self.redraw_all()
        self._notify_view_changed()

    def fit_to_diagram(self, padding: int = 40, include_connections: bool = True):
        if not self.elements:
            self.reset_view()
            return
        xs = [e.x for e in self.elements.values()]
        ys = [e.y for e in self.elements.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        # Knotenbreite/Höhe berücksichtigen (Modellgröße)
        w, h = self.NODE_W, self.NODE_H
        min_x -= w // 2
        max_x += w // 2
        min_y -= h // 2
        max_y += h // 2
        if include_connections and self.connections:
            # Verbindungen können außerhalb liegen; berücksichtige deren Mittelpunkte
            for conn in self.connections.values():
                s = self.elements.get(conn.source_element)
                t = self.elements.get(conn.target_element)
                if not s or not t:
                    continue
                x1, y1 = s.center()
                x2, y2 = t.center()
                # optional: Pfeilspitzen berücksichtigen (klein)
                min_x = min(min_x, x1, x2)
                max_x = max(max_x, x1, x2)
                min_y = min(min_y, y1, y2)
                max_y = max(max_y, y1, y2)
        # Ziel-Viewportgröße
        vw = max(1, int(self.winfo_width() or self.winfo_reqwidth() or 1200))
        vh = max(1, int(self.winfo_height() or self.winfo_reqheight() or 800))
        diag_w = max(1, (max_x - min_x) + 2 * padding)
        diag_h = max(1, (max_y - min_y) + 2 * padding)
        sx = vw / diag_w
        sy = vh / diag_h
        s = min(2.0, max(0.2, min(sx, sy)))
        self.view_scale = s
        # Centering
        # wir möchten, dass (min_x - pad, min_y - pad) -> (0,0)
        # und (max_x + pad, max_y + pad) -> (vw, vh)
        # also tx,ty so wählen, dass min links/oben landet und dann mittig verschieben
        mx = min_x - padding
        my = min_y - padding
        content_w = diag_w * s
        content_h = diag_h * s
        self.view_tx = (vw - content_w) / 2 - mx * s
        self.view_ty = (vh - content_h) / 2 - my * s
        self.redraw_all()
        self._notify_view_changed()


class RulerCanvas(tk.Canvas):
    """Einfaches Lineal (horizontal oder vertikal) synchronisiert mit VPBCanvas.
    - orientation: 'x' oder 'y'
    - zeigt Ticks in Model-Koordinaten, skaliert mit view_scale
    - offset ergibt sich aus view_tx/view_ty
    """
    def __init__(self, master: tk.Widget, orientation: str, **kw):
        height = kw.pop('height', 20)
        width = kw.pop('width', 20)
        bg = kw.pop('background', '#f6f6f6')
        if orientation == 'x':
            super().__init__(master, height=height, background=bg, highlightthickness=0, **kw)
        else:
            super().__init__(master, width=width, background=bg, highlightthickness=0, **kw)
        self.orientation = orientation
        self._target: Optional[VPBCanvas] = None
        self._minor_px = 10
        self._font = ("Consolas", 8)
        self.bind('<Configure>', lambda e: self.redraw())

    def attach(self, canvas: 'VPBCanvas'):
        self._target = canvas
        def _sync():
            self.redraw()
        # Wenn der Canvas Listener unterstützt, registrieren; sonst legacy on_view_changed
        if hasattr(canvas, 'add_view_changed_listener'):
            try:
                canvas.add_view_changed_listener(_sync)
            except Exception:
                canvas.on_view_changed = _sync
        else:
            canvas.on_view_changed = _sync
        self.redraw()

    def redraw(self):
        self.delete('all')
        if not self._target:
            return
        c = self._target
        s = max(c.view_scale, 1e-6)
        if self.orientation == 'x':
            w = int(self.winfo_width() or 0)
            h = int(self.winfo_height() or 0)
            if w <= 0 or h <= 0:
                return
            px_target = 60
            step_model = self._nice_step(px_target / s)
            x0_model, _ = c.to_model(0, 0)
            start = self._floor_to(x0_model, step_model)
            x = start
            while True:
                vx, _ = c.to_view(x, 0)
                if vx > w + 50:
                    break
                if vx >= -50:
                    self.create_line(vx, h, vx, h-8, fill="#666")
                    label = f"{int(x)}"
                    self.create_text(vx+2, h-10, text=label, anchor='sw', font=self._font, fill="#444")
                    minor = step_model / 10
                    for i in range(1, 10):
                        xm = x + i*minor
                        vm, _ = c.to_view(xm, 0)
                        if -50 <= vm <= w + 50:
                            self.create_line(vm, h, vm, h-4, fill="#aaa")
                x += step_model
        else:
            w = int(self.winfo_width() or 0)
            h = int(self.winfo_height() or 0)
            if w <= 0 or h <= 0:
                return
            py_target = 60
            step_model = self._nice_step(py_target / s)
            _, y0_model = c.to_model(0, 0)
            start = self._floor_to(y0_model, step_model)
            y = start
            while True:
                _, vy = c.to_view(0, y)
                if vy > h + 50:
                    break
                if vy >= -50:
                    self.create_line(w, vy, w-8, vy, fill="#666")
                    label = f"{int(y)}"
                    self.create_text(w-2, vy+2, text=label, anchor='se', font=self._font, fill="#444")
                    minor = step_model / 10
                    for i in range(1, 10):
                        ym = y + i*minor
                        _, vm = c.to_view(0, ym)
                        if -50 <= vm <= h + 50:
                            self.create_line(w, vm, w-4, vm, fill="#aaa")
                y += step_model

    # ----- Panning/Zommen per Methoden (für Tastatur) -----
    def pan_pixels(self, dx_px: float, dy_px: float):
        """Verschiebt die Ansicht um Pixel (Viewport-Koordinaten)."""
        try:
            self.view_tx += dx_px
            self.view_ty += dy_px
            self.redraw_all()
            self._notify_view_changed()
        except Exception:
            pass

    def zoom_at_view(self, factor: float, vx: Optional[float] = None, vy: Optional[float] = None):
        """Zoomt um einen Faktor an einem Viewport-Punkt (vx, vy)."""
        try:
            if vx is None or vy is None:
                vx = max(0, int(self.winfo_width() or 0)) / 2
                vy = max(0, int(self.winfo_height() or 0)) / 2
            mx, my = self.to_model(vx, vy)
            new_scale = max(getattr(self, '_min_zoom', 0.1), min(getattr(self, '_max_zoom', 5.0), self.view_scale * factor))
            self.view_scale = new_scale
            self.view_tx = vx - mx * self.view_scale
            self.view_ty = vy - my * self.view_scale
            self.redraw_all()
            self._notify_view_changed()
        except Exception:
            pass

    def center_time_axis_vertical(self):
        """Setzt die Ansicht so, dass die Zeitachse (y=0) vertikal mittig liegt.
        Vermeidet absichtsvoll Clamping an Content-Grenzen, damit echte Zentrierung
        auch bei Inhalten rein im positiven/negativen y-Bereich funktioniert.
        """
        try:
            # Viewport-Höhe in Pixel
            vh_px = int(self.winfo_height() or self.winfo_reqheight() or 0)
            if vh_px <= 0:
                # Falls noch nicht gelayoutet, kurz verzögert erneut versuchen
                try:
                    self.after(60, self.center_time_axis_vertical)
                except Exception:
                    pass
                return
            # Vertikale Translation so setzen, dass y=0 auf der Mitte landet
            self.view_ty = vh_px / 2.0
            # x-Translation/Scale bleiben unverändert
            self.redraw_all()
            self._notify_view_changed()
        except Exception:
            pass

    @staticmethod
    def _nice_step(raw: float) -> float:
        # runde auf 1, 2, 5, 10 * 10^n
        if raw <= 0:
            return 1
        import math
        exp = math.floor(math.log10(raw))
        base = raw / (10**exp)
        if base <= 1:
            nice = 1
        elif base <= 2:
            nice = 2
        elif base <= 5:
            nice = 5
        else:
            nice = 10
        return nice * (10**exp)

    @staticmethod
    def _floor_to(x: float, step: float) -> float:
        import math
        return math.floor(x / step) * step


# -------- Hauptfenster --------

class MiniMapCanvas(tk.Canvas):
    """Zeigt eine Übersicht des gesamten Diagramms und den aktuellen Viewport."""
    def __init__(self, master: tk.Widget, **kw):
        height = kw.pop('height', 120)
        super().__init__(master, height=height, background="#fafafa", highlightthickness=0, **kw)
        self._target: Optional[VPBCanvas] = None
        self._dragging: bool = False
        self.bind('<Configure>', lambda e: self.redraw())
        self.bind('<ButtonPress-1>', self._on_press)
        self.bind('<B1-Motion>', self._on_drag)
        self.bind('<ButtonRelease-1>', self._on_release)

    def attach(self, canvas: 'VPBCanvas'):
        self._target = canvas
        def _sync():
            self.redraw()
        if hasattr(canvas, 'add_view_changed_listener'):
            canvas.add_view_changed_listener(_sync)
        else:
            canvas.on_view_changed = _sync
        self.redraw()

    def _compute_mapping(self) -> Optional[Tuple[float, float, float, float]]:
        if not self._target:
            return None
        min_x, min_y, max_x, max_y = self._target.get_content_bounds(include_connections=True)
        if max_x - min_x <= 1e-6 or max_y - min_y <= 1e-6:
            return None
        w = max(1, int(self.winfo_width() or 0))
        h = max(1, int(self.winfo_height() or 0))
        return (min_x, min_y, max_x, max_y, w, h)

    def redraw(self):
        self.delete('all')
        if not self._target:
            return
        mapping = self._compute_mapping()
        if not mapping:
            return
        min_x, min_y, max_x, max_y, w, h = mapping
        bx = max_x - min_x
        by = max_y - min_y
        sx = w / bx
        sy = h / by
        s = min(sx, sy)
        offx = (w - bx * s) / 2
        offy = (h - by * s) / 2
        content_vx0 = offx
        content_vy0 = offy
        content_vx1 = offx + bx * s
        content_vy1 = offy + by * s
        self.create_rectangle(content_vx0, content_vy0, content_vx1, content_vy1, outline="#d0d0d0", fill="")

        def _map(x: float, y: float) -> Tuple[float, float]:
            return (offx + (x - min_x) * s, offy + (y - min_y) * s)

        # Verbindungen zeichnen (falls Routing verfügbar)
        cache = getattr(self._target, "_connection_points_cache", {}) or {}
        for conn in self._target.connections.values():
            pts = cache.get(getattr(conn, "connection_id", None))
            coords: List[float] = []
            if isinstance(pts, list) and len(pts) >= 4:
                try:
                    it = iter(pts)
                    for px, py in zip(it, it):
                        vx, vy = _map(float(px), float(py))
                        coords.extend([vx, vy])
                except Exception:
                    coords = []
            if not coords:
                src = self._target.elements.get(getattr(conn, "source_element", None))
                tgt = self._target.elements.get(getattr(conn, "target_element", None))
                if not src or not tgt:
                    continue
                sx_m, sy_m = src.center()
                tx_m, ty_m = tgt.center()
                sx_v, sy_v = _map(sx_m, sy_m)
                tx_v, ty_v = _map(tx_m, ty_m)
                coords = [sx_v, sy_v, tx_v, ty_v]
            if len(coords) >= 4:
                self.create_line(*coords, fill="#9aa7c1", width=1, smooth=False)

        selected = set(getattr(self._target, "selected_ids", set()) or [])
        if getattr(self._target, "selected_id", None):
            selected.add(self._target.selected_id)

        # Elemente als grobe Rechtecke
        node_w = getattr(self._target, "NODE_W", 150)
        node_h = getattr(self._target, "NODE_H", 60)
        min_size = 4
        for el in self._target.elements.values():
            try:
                cx, cy = el.center()
            except Exception:
                cx, cy = getattr(el, "x", 0), getattr(el, "y", 0)
            vx, vy = _map(cx, cy)
            hw = max(min_size / 2, (node_w * s) / 2)
            hh = max(min_size / 2, (node_h * s) / 2)
            fill = "#6c8bd4"
            if getattr(el, "element_type", "").upper() == "GROUP":
                fill = "#c6d6f3"
            if getattr(el, "element_type", "").upper() == "EVENT":
                fill = "#92d36e"
            outline = "#405f9e"
            rect = self.create_rectangle(vx - hw, vy - hh, vx + hw, vy + hh, fill=fill, outline=outline, width=1)
            if getattr(el, "element_id", None) in selected:
                self.create_rectangle(vx - hw, vy - hh, vx + hw, vy + hh, outline="#ff8c00", width=2)

        x0_m, y0_m = self._target.get_view_origin_model()
        vw_m, vh_m = self._target.get_viewport_model_size()
        x1_m, y1_m = x0_m + vw_m, y0_m + vh_m
        vx0 = offx + (x0_m - min_x) * s
        vy0 = offy + (y0_m - min_y) * s
        vx1 = offx + (x1_m - min_x) * s
        vy1 = offy + (y1_m - min_y) * s
        shade_opts = {"fill": "#1f2a44", "stipple": "gray25", "outline": ""}
        try:
            self.create_rectangle(content_vx0, content_vy0, content_vx1, vy0, **shade_opts)
            self.create_rectangle(content_vx0, vy1, content_vx1, content_vy1, **shade_opts)
            self.create_rectangle(content_vx0, vy0, vx0, vy1, **shade_opts)
            self.create_rectangle(vx1, vy0, content_vx1, vy1, **shade_opts)
        except Exception:
            pass
        self.create_rectangle(vx0, vy0, vx1, vy1, outline="#2d7ff9", width=2)

    def _to_model_from_minimap(self, vx: float, vy: float) -> Optional[Tuple[float, float]]:
        mapping = self._compute_mapping()
        if not mapping:
            return None
        min_x, min_y, max_x, max_y, w, h = mapping
        bx = max_x - min_x
        by = max_y - min_y
        s = min(w / bx, h / by)
        offx = (w - bx * s) / 2
        offy = (h - by * s) / 2
        mx = (vx - offx) / s + min_x
        my = (vy - offy) / s + min_y
        return (mx, my)

    def _on_press(self, event):
        self._dragging = True
        self._pan_to_event(event)

    def _on_drag(self, event):
        if self._dragging:
            self._pan_to_event(event)

    def _on_release(self, event):
        self._dragging = False

    def _pan_to_event(self, event):
        if not self._target:
            return
        to_m = self._to_model_from_minimap(event.x, event.y)
        if not to_m:
            return
        mx, my = to_m
        vw_m, vh_m = self._target.get_viewport_model_size()
        # Zentriere Viewport um Klickpunkt
        self._target.set_view_origin_model(mx - vw_m/2, my - vh_m/2)
        self.redraw()

class HierarchyCanvas(tk.Canvas):
    """Zeichnet vertikale Hierarchie-Blöcke links, Y folgt Model-Koordinaten, X ist viewportfix."""
    def __init__(self, master: tk.Widget, **kw):
        width = kw.pop('width', 90)
        bg = kw.pop('background', '#fbfbfb')
        super().__init__(master, width=width, background=bg, highlightthickness=0, **kw)
        self._target: Optional[VPBCanvas] = None
        self._font = ("Segoe UI", 9)
        self._selected_index: Optional[int] = None
        self._on_select: Optional[Callable[[Optional[int], Optional[Dict]], None]] = None
        self._on_double_click: Optional[Callable[[Optional[int], Optional[Dict]], None]] = None
        self.bind('<Configure>', lambda e: self.redraw())
        self.bind('<Button-1>', self._on_click)
        self.bind('<Double-Button-1>', self._on_double_click)

    def attach(
        self,
        canvas: 'VPBCanvas',
        on_select: Optional[Callable[[Optional[int], Optional[Dict]], None]] = None,
        on_double_click: Optional[Callable[[Optional[int], Optional[Dict]], None]] = None,
    ):
        self._target = canvas
        self._on_select = on_select
        self._on_double_click = on_double_click
        # Canvas zeichnet Hierarchie nicht intern
        try:
            canvas.hierarchy_external = True
        except Exception:
            pass
        def _sync():
            self.redraw()
        if hasattr(canvas, 'add_view_changed_listener'):
            try:
                canvas.add_view_changed_listener(_sync)
            except Exception:
                canvas.on_view_changed = _sync
        else:
            canvas.on_view_changed = _sync
        self.redraw()

    def redraw(self):
        self.delete('all')
        c = self._target
        if not c:
            return
        w = int(self.winfo_width() or 0)
        h = int(self.winfo_height() or 0)
        if w <= 0 or h <= 0:
            return
        cats = getattr(c, 'hierarchy_categories', None) or []
        if self._selected_index is not None and (self._selected_index < 0 or self._selected_index >= len(cats)):
            self._selected_index = None
        for idx, cat in enumerate(cats):
            try:
                name = str(cat.get('name', ''))
                y0 = float(cat.get('y0', 0.0))
                y1 = float(cat.get('y1', 0.0))
                color = str(cat.get('color', '#f2f2f2'))
            except Exception:
                continue
            _, vy0 = c.to_view(0, y0)
            _, vy1 = c.to_view(0, y1)
            r = self.create_rectangle(0, vy0, w, vy1, fill=color, outline='#d0d0d0')
            cy = (vy0 + vy1) / 2
            self.create_text(6, cy, text=name, anchor='w', font=self._font, fill='#333')
            if idx == self._selected_index:
                self.create_rectangle(0, vy0, w, vy1, outline='#2d7ff9', width=2)

    def set_selected_index(self, index: Optional[int]) -> None:
        if index == self._selected_index:
            return
        self._selected_index = index
        self.redraw()

    def _notify_selection(self) -> None:
        if not callable(self._on_select):
            return
        cats = getattr(self._target, 'hierarchy_categories', None) or []
        if self._selected_index is None or self._selected_index < 0 or self._selected_index >= len(cats):
            self._on_select(None, None)
            return
        cat = cats[self._selected_index]
        self._on_select(self._selected_index, dict(cat) if isinstance(cat, dict) else cat)

    def _notify_double_click(self, index: Optional[int]) -> None:
        if not callable(self._on_double_click):
            return
        cats = getattr(self._target, 'hierarchy_categories', None) or []
        if index is None or index < 0 or index >= len(cats):
            self._on_double_click(None, None)
            return
        cat = cats[index]
        self._on_double_click(index, dict(cat) if isinstance(cat, dict) else cat)

    def _hit_category(self, view_y: float) -> Optional[int]:
        if not self._target:
            return None
        try:
            _, my = self._target.to_model(0, view_y)
        except Exception:
            return None
        cats = getattr(self._target, 'hierarchy_categories', None) or []
        for idx, cat in enumerate(cats):
            try:
                y0 = float(cat.get('y0', 0.0))
                y1 = float(cat.get('y1', 0.0))
            except Exception:
                continue
            low = min(y0, y1)
            high = max(y0, y1)
            if low <= my <= high:
                return idx
        return None

    def _on_click(self, event):
        idx = self._hit_category(event.y)
        self.set_selected_index(idx)
        self._notify_selection()

    def _on_double_click(self, event):
        idx = self._hit_category(event.y)
        if idx is None:
            return
        if idx != self._selected_index:
            self.set_selected_index(idx)
            self._notify_selection()
        self._notify_double_click(idx)

