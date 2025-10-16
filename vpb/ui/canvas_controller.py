"""Controller für Canvas- und Bearbeitungsfunktionen des VPB-Designers."""

from __future__ import annotations

import json
import os
import time
import traceback
from typing import Dict, Optional, TYPE_CHECKING

from vpb.styles import CONNECTION_STYLES, ELEMENT_STYLES

from .palette_panel import PaletteLoader

if TYPE_CHECKING:  # pragma: no cover - nur für Typen
    from vpb_app import VPBDesignerApp


class CanvasController:
    """Kapselt Canvas-Operationen und Palette-/Auswahl-Helfer."""

    def __init__(self, app: "VPBDesignerApp") -> None:
        self._app = app
        self._clipboard_cache: Optional[dict] = None

    # ------------------------------------------------------------------
    # interne Shortcuts
    # ------------------------------------------------------------------
    @property
    def canvas(self):
        return getattr(self._app, "canvas", None)

    def _set_status(self, message: str) -> None:
        status = getattr(self._app, "status", None)
        if status is None:
            return
        try:
            status.set(message)
        except Exception:
            pass

    def _is_text_input_focus(self) -> bool:
        try:
            return bool(self._app._is_text_input_focus())
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Palette & Element hinzufügen
    # ------------------------------------------------------------------
    def reload_palettes(self) -> None:
        try:
            data = PaletteLoader.load_all(os.path.join(os.getcwd(), "palettes"))
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Palette Fehler: {exc}")
            data = {"categories": []}
        try:
            palette_defaults: Dict[str, Dict] = {}
            for cat in data.get("categories", []) or []:
                for item in cat.get("items", []) or []:
                    elem_type = str(item.get("type", "")).upper()
                    if elem_type and elem_type in ELEMENT_STYLES and elem_type not in CONNECTION_STYLES:
                        style_override = {
                            key: item.get(key)
                            for key in ("shape", "fill", "outline", "dash")
                            if key in item
                        }
                        if style_override:
                            palette_defaults[elem_type] = style_override
            canvas = self.canvas
            if canvas is not None and palette_defaults:
                try:
                    canvas.set_element_style_palette_defaults(palette_defaults)
                except Exception:
                    pass
            palette = getattr(self._app, "palette", None)
            if palette is not None:
                try:
                    palette.render(data.get("categories", []))
                except Exception as render_exc:  # noqa: BLE001
                    self._set_status(f"Palette Render Fehler: {render_exc}")
                    return
            self._set_status("Palette geladen")
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Palette Render Fehler: {exc}")

    def handle_palette_pick(self, item: dict) -> None:
        canvas = self.canvas
        if canvas is None:
            return
        reference = item.get("reference") if isinstance(item, dict) else None
        if isinstance(reference, dict):
            self._start_reference_process_add(item, reference)
            return
        elem_type = str(item.get("type", "FUNCTION"))
        name = str(item.get("name", "Neues Element"))
        if elem_type.upper() in CONNECTION_STYLES:
            arrow = item.get("arrow_style")
            arrow_style = str(arrow).lower() if isinstance(arrow, str) else None
            self.start_connection_mode(elem_type.upper(), arrow_style=arrow_style)
            return
        try:
            canvas.start_add_mode(elem_type, name)
            self._set_status(f"Palette: {elem_type} – zum Platzieren in leeren Bereich klicken")
        except Exception:
            pass

    def _start_reference_process_add(self, item: dict, reference: dict) -> None:
        canvas = self.canvas
        if canvas is None:
            return
        snippet = reference.get("snippet") or reference.get("snippet_file") or reference.get("path")
        if not snippet:
            self._set_status("Referenz: Snippet-Pfad fehlt")
            return
        element_type = str(reference.get("element_type") or item.get("type") or "SUBPROCESS")
        default_name = str(reference.get("default_name") or reference.get("name") or item.get("name") or "Referenzprozess")

        style: Dict[str, object] = {}
        for key in ("shape", "fill", "outline", "dash", "text_color"):
            if key in item and item.get(key) not in (None, ""):
                style[key] = item.get(key)
        for key in ("shape", "fill", "outline", "dash", "text_color"):
            if key in reference and reference.get(key) not in (None, ""):
                style[key] = reference.get(key)

        properties: Dict[str, object] = {}
        for key in ("description", "responsible_authority", "legal_basis", "deadline_days", "geo_reference"):
            if key in reference and reference.get(key) is not None:
                properties[key] = reference.get(key)
            elif key in item and item.get(key) is not None:
                properties[key] = item.get(key)

        extras: Dict[str, object] = {}
        ref_id = reference.get("id") or item.get("id")
        if ref_id:
            extras["ref_process_id"] = ref_id
        label = reference.get("label") or item.get("label")
        if label:
            extras["ref_process_label"] = label
        category = reference.get("category") or item.get("category")
        if category:
            extras["ref_process_category"] = category

        payload = {
            "style": style or None,
            "ref_process": {
                "id": ref_id,
                "ref_file": snippet,
                "name": reference.get("name") or default_name,
                "original_type": element_type,
                "auto_group": reference.get("auto_group", True),
            },
            "properties": properties or None,
            "extras": extras or None,
        }

        try:
            canvas.start_add_mode(element_type, default_name=default_name, payload=payload)
            self._set_status(f"Referenzprozess '{default_name}' – zum Platzieren klicken")
        except Exception as exc:  # noqa: BLE001
            self._set_status(f"Referenzprozess konnte nicht vorbereitet werden: {exc}")

    def start_connection_mode(self, connection_type: str, arrow_style: Optional[str] = None) -> None:
        canvas = self.canvas
        if canvas is None:
            return
        try:
            canvas.start_link_mode(connection_type, arrow_style=arrow_style)
        except Exception:
            return
        label = connection_type.upper() if isinstance(connection_type, str) else str(connection_type)
        self._set_status(f"Palette: Verbindungstyp {label} – Quelle wählen")

    # ------------------------------------------------------------------
    # Auswahl- und Bearbeitungsbefehle
    # ------------------------------------------------------------------
    def delete_selected(self) -> None:
        canvas = self.canvas
        if canvas is None:
            return
        try:
            if canvas.delete_selected():
                self._set_status("Element gelöscht")
        except Exception:
            traceback.print_exc()

    def duplicate_selected(self) -> None:
        canvas = self.canvas
        if canvas is None:
            return
        try:
            if canvas.duplicate_selected():
                self._set_status("Element dupliziert")
        except Exception:
            pass

    def toggle_snap(self) -> None:
        canvas = self.canvas
        if canvas is None:
            return
        snap_var = getattr(self._app, "_snap_var", None)
        value = bool(snap_var.get()) if snap_var is not None else False
        try:
            canvas.set_snap_to_grid(value)
        except Exception:
            pass
        self._set_status("Snap-to-Grid: An" if value else "Snap-to-Grid: Aus")

    def toggle_link_mode(self) -> None:
        canvas = self.canvas
        if canvas is None:
            return
        try:
            canvas.toggle_link_mode()
        except Exception:
            pass

    def cancel_link_mode(self):
        canvas = self.canvas
        if canvas is None:
            return
        try:
            canvas.cancel_link_mode()
        except Exception:
            return
        return "break"

    def undo(self) -> None:
        canvas = self.canvas
        if canvas is None:
            return
        try:
            canvas.undo()
        except Exception:
            pass

    def redo(self) -> None:
        canvas = self.canvas
        if canvas is None:
            return
        try:
            canvas.redo()
        except Exception:
            pass

    def group_from_selection(self) -> None:
        canvas = self.canvas
        if canvas is None:
            return
        try:
            if hasattr(canvas, "_group_from_selection"):
                canvas._group_from_selection()
                return
            selected = [eid for eid in canvas.selected_ids if eid in canvas.elements]
            if len(selected) < 1:
                from tkinter import messagebox

                messagebox.showinfo("Gruppe", "Bitte wählen Sie mindestens ein Element aus.")
                return
            canvas.push_undo()
            xs = [canvas.elements[e].x for e in selected]
            ys = [canvas.elements[e].y for e in selected]
            cx = int(sum(xs) / len(xs)) if xs else 0
            cy = int(sum(ys) / len(ys)) if ys else 0
            group = canvas.add_element("GROUP", name="Gruppe", at=(cx, cy))
            group.members = list(selected)
            group.collapsed = False
            canvas.selected_ids = {group.element_id}
            canvas.selected_id = group.element_id
            canvas.redraw_all()
        except Exception:
            traceback.print_exc()

    def ungroup_selected(self) -> None:
        canvas = self.canvas
        if canvas is None:
            return
        try:
            from tkinter import messagebox

            if hasattr(canvas, "_ungroup_selected"):
                canvas._ungroup_selected()
                return
            selected_id = getattr(canvas, "selected_id", None)
            element = canvas.elements.get(selected_id) if selected_id else None
            if not element or element.element_type != "GROUP":
                messagebox.showinfo("Gruppe", "Bitte wählen Sie eine Gruppe aus.")
                return
            canvas.push_undo()
            to_remove = [cid for cid, conn in canvas.connections.items() if conn.source_element == selected_id or conn.target_element == selected_id]
            for cid in to_remove:
                canvas.connections.pop(cid, None)
            canvas.elements.pop(selected_id, None)
            for gid, grp in list(canvas.elements.items()):
                try:
                    if getattr(grp, "element_type", "") == "GROUP":
                        members = set(getattr(grp, "members", []) or [])
                        if selected_id in members:
                            members.discard(selected_id)
                            grp.members = list(members)
                except Exception:
                    pass
            canvas.selected_id = None
            try:
                canvas.selected_ids.clear()
            except Exception:
                canvas.selected_ids = set()
            canvas.redraw_all()
        except Exception:
            traceback.print_exc()

    def align_selected(self, mode: str):
        canvas = self.canvas
        if canvas is None:
            return "break"
        try:
            success = canvas.align_selection(mode)
        except Exception as exc:  # noqa: BLE001
            from tkinter import messagebox

            messagebox.showerror("Ausrichten fehlgeschlagen", str(exc))
            return "break"
        if not success:
            self._set_status("Ausrichten benötigt mindestens zwei Elemente.")
            return "break"
        labels = {
            "left": "Links",
            "right": "Rechts",
            "top": "Oben",
            "bottom": "Unten",
            "center": "Horizontal",
            "middle": "Vertikal",
        }
        self._set_status(f"Elemente ausgerichtet ({labels.get(mode, mode)}).")
        return "break"

    def distribute_selected(self, axis: str):
        canvas = self.canvas
        if canvas is None:
            return "break"
        try:
            success = canvas.distribute_selection(axis)
        except Exception as exc:  # noqa: BLE001
            from tkinter import messagebox

            messagebox.showerror("Verteilen fehlgeschlagen", str(exc))
            return "break"
        if not success:
            self._set_status("Verteilen benötigt mindestens drei Elemente.")
            return "break"
        axis_label = "horizontal" if axis == "horizontal" else "vertikal"
        self._set_status(f"Elemente gleichmäßig verteilt ({axis_label}).")
        return "break"

    def arrange_selected_circular(self):
        canvas = self.canvas
        if canvas is None:
            return "break"
        try:
            success = canvas.arrange_selection_circular()
        except Exception as exc:  # noqa: BLE001
            from tkinter import messagebox

            messagebox.showerror("Anordnen fehlgeschlagen", str(exc))
            return "break"
        if not success:
            self._set_status("Kreis-Anordnung benötigt mindestens zwei Elemente.")
            return "break"
        self._set_status("Elemente kreisförmig angeordnet.")
        return "break"

    # ------------------------------------------------------------------
    # Zoom & Ansicht
    # ------------------------------------------------------------------
    def reset_view(self) -> None:
        canvas = self.canvas
        if canvas is None:
            return
        try:
            canvas.reset_view()
        except Exception:
            pass

    def fit_to_diagram(self) -> None:
        canvas = self.canvas
        if canvas is None:
            return
        try:
            canvas.fit_to_diagram()
        except Exception:
            pass

    def zoom_selection(self):
        canvas = self.canvas
        if canvas is None:
            return "break"
        try:
            success = canvas.zoom_to_selection()
        except Exception as exc:  # noqa: BLE001
            from tkinter import messagebox

            messagebox.showerror("Zoom fehlgeschlagen", str(exc))
            return "break"
        if not success:
            self._set_status("Keine Auswahl zum Zoomen vorhanden.")
            return "break"
        self._set_status("Zoom auf Auswahl.")
        return "break"

    def center_selection(self):
        canvas = self.canvas
        if canvas is None:
            return "break"
        try:
            success = canvas.focus_selection()
        except Exception as exc:  # noqa: BLE001
            from tkinter import messagebox

            messagebox.showerror("Zentrieren fehlgeschlagen", str(exc))
            return "break"
        if not success:
            self._set_status("Keine Auswahl zum Zentrieren vorhanden.")
            return "break"
        self._set_status("Auswahl zentriert.")
        return "break"

    def zoom_at_view(self, factor: float):
        canvas = self.canvas
        if canvas is None:
            return
        try:
            canvas.zoom_at_view(factor)
        except Exception:
            return
        return "break"

    def zoom_reset(self):
        canvas = self.canvas
        if canvas is None:
            return
        try:
            canvas.zoom_reset()
        except Exception:
            return
        return "break"

    def set_view_scale(self, scale: float):
        canvas = self.canvas
        if canvas is None:
            return
        try:
            canvas.view_scale = scale
            canvas.redraw_all()
            notify = getattr(canvas, "_notify_view_changed", None)
            if callable(notify):
                notify()
        except Exception:
            return
        return "break"

    def handle_arrow(self, sx: int, sy: int, big: bool = False):
        if self._is_text_input_focus():
            return
        canvas = self.canvas
        if canvas is None:
            return
        try:
            selected_ids = getattr(canvas, "selected_ids", set()) or set()
            if selected_ids:
                step = getattr(self._app, "_nudge_step_big", 10) if big else getattr(self._app, "_nudge_step_small", 2)
                canvas.nudge_selection(step * sx, step * sy)
            else:
                step = getattr(self._app, "_pan_step_big", 60) if big else getattr(self._app, "_pan_step_small", 30)
                canvas.pan_pixels(step * sx, step * sy)
            return "break"
        except Exception:
            return

    # ------------------------------------------------------------------
    # Clipboard & Auswahl
    # ------------------------------------------------------------------
    def select_all(self) -> None:
        if self._is_text_input_focus():
            return
        canvas = self.canvas
        if canvas is None:
            return
        try:
            canvas.select_all()
            self._set_status("Alles ausgewählt")
        except Exception:
            pass

    def copy_selection(self) -> None:
        if self._is_text_input_focus():
            return
        canvas = self.canvas
        if canvas is None:
            return
        try:
            selected = [eid for eid in canvas.selected_ids if eid in canvas.elements]
            if not selected:
                return
            data = canvas.to_dict()
            elements = [e for e in data.get("elements", []) if e.get("element_id") in selected]
            element_ids = {e.get("element_id") for e in elements}
            connections = [c for c in data.get("connections", []) if c.get("source_element") in element_ids and c.get("target_element") in element_ids]
            payload = {"elements": elements, "connections": connections}
            json_data = json.dumps(payload, ensure_ascii=False)
            try:
                self._app.clipboard_clear()
                self._app.clipboard_append(json_data)
                self._app.update()
            except Exception:
                self._clipboard_cache = payload
            else:
                self._clipboard_cache = payload
            self._set_status("Kopiert")
        except Exception:
            pass

    def cut_selection(self) -> None:
        if self._is_text_input_focus():
            return
        try:
            self.copy_selection()
            canvas = self.canvas
            if canvas is not None and canvas.delete_selected():
                self._set_status("Ausgeschnitten")
        except Exception:
            pass

    def paste_clipboard(self) -> None:
        if self._is_text_input_focus():
            return
        canvas = self.canvas
        if canvas is None:
            return
        try:
            payload = None
            try:
                clipboard_data = self._app.clipboard_get()
                payload = json.loads(clipboard_data)
            except Exception:
                payload = self._clipboard_cache
            if not payload or not isinstance(payload, dict):
                return
            elements = payload.get("elements", []) or []
            connections = payload.get("connections", []) or []
            if not elements:
                return
            canvas.push_undo()
            id_map: Dict[str, str] = {}
            offset = getattr(canvas, "duplicate_offset", 30) if hasattr(canvas, "duplicate_offset") else 30
            for element in elements:
                old_id = str(element.get("element_id"))
                new_id = f"p_{old_id}_{int(time.time() * 1000) % 100000}"
                id_map[old_id] = new_id
                elem_type = str(element.get("element_type", "FUNCTION"))
                name = str(element.get("name", "Kopie"))
                nx = int(element.get("x", 0)) + offset
                ny = int(element.get("y", 0)) + offset
                new_elem = canvas.add_element(elem_type, name, at=(nx, ny))
                new_elem.description = element.get("description") or ""
                new_elem.responsible_authority = element.get("responsible_authority") or ""
                new_elem.legal_basis = element.get("legal_basis") or ""
                new_elem.deadline_days = int(element.get("deadline_days") or 0)
                new_elem.geo_reference = element.get("geo_reference") or ""
                if elem_type.upper() == "GROUP":
                    members = [id_map.get(member, member) for member in (element.get("members") or [])]
                    new_elem.members = [member for member in members if member in canvas.elements]
            for conn in connections:
                source_id = id_map.get(conn.get("source_element"))
                target_id = id_map.get(conn.get("target_element"))
                if source_id and target_id:
                    conn_type = str(conn.get("connection_type", "SEQUENCE"))
                    new_conn = canvas.add_connection(source_id, target_id, conn_type)
                    if new_conn:
                        new_conn.description = conn.get("description") or ""
            canvas.redraw_all()
            self._set_status("Eingefügt")
        except Exception:
            pass