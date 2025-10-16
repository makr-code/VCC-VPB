from __future__ import annotations

from typing import Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from vpb_app import VPBApp
    from vpb.models import VPBConnection, VPBElement


class AppPropertiesBridge:
    """Kapselt Eigenschaften-bezogene Logik der ``VPBApp``."""

    def __init__(self, app: "VPBApp") -> None:
        self._app = app

    # ----- Auswahl-Handling -----
    def on_selection_changed(
        self,
        element: Optional["VPBElement"],
        connection: Optional["VPBConnection"],
    ) -> None:
        app = self._app
        if getattr(app, "_selected_hierarchy_index", None) is not None:
            app._selected_hierarchy_index = None
            try:
                hier_canvas = getattr(app, "hier_canvas", None)
                if hier_canvas:
                    hier_canvas.set_selected_index(None)
            except Exception:
                pass
        try:
            app.props.set_hierarchy(None, None)
        except Exception:
            pass
        app.props.set_element(element, connection)

    # ----- Eigenschaften anwenden -----
    def apply_properties(self, values: Dict[str, object]) -> None:
        app = self._app
        canvas = app.canvas
        kind = str(values.get("kind", "element")).lower()
        if kind == "hierarchy":
            idx_raw = values.get("index")
            try:
                index = int(idx_raw)  # type: ignore[arg-type]
            except Exception:
                return
            data = {
                "name": values.get("name"),
                "color": values.get("color"),
                "y0": values.get("y0"),
                "y1": values.get("y1"),
            }
            app._update_hierarchy_category(index, data)  # type: ignore[attr-defined]
            return

        if kind == "connection":
            cid = getattr(canvas, "selected_conn_id", None)
            if not cid or cid not in canvas.connections:
                return
            conn = canvas.connections[cid]
            try:
                canvas.push_undo()
            except Exception:
                pass
            new_type = str(values.get("connection_type", conn.connection_type) or conn.connection_type)
            conn.connection_type = new_type
            arrow = str(values.get("arrow_style", conn.arrow_style) or conn.arrow_style)
            conn.arrow_style = arrow
            routing_mode = str(values.get("routing_mode", getattr(conn, "routing_mode", "auto") or "auto") or "auto").lower()
            if routing_mode not in {"auto", "smart", "smart-plus", "straight", "orthogonal", "curved", "multi"}:
                routing_mode = "auto"
            conn.routing_mode = routing_mode
            conn.description = str(values.get("description", conn.description) or "")
            canvas.redraw_all()
            try:
                app.status.set("Verbindung aktualisiert.")
            except Exception:
                pass
            return

        sid = canvas.selected_id
        if not sid or sid not in canvas.elements:
            return
        el = canvas.elements[sid]
        try:
            canvas.push_undo()
        except Exception:
            pass
        el.element_type = str(values.get("element_type", el.element_type))
        el.name = str(values.get("name", el.name))
        el.description = str(values.get("description", el.description))
        el.responsible_authority = str(values.get("responsible_authority", el.responsible_authority))
        try:
            el.deadline_days = int(values.get("deadline_days", el.deadline_days) or 0)
        except Exception:
            pass
        el.legal_basis = str(values.get("legal_basis", el.legal_basis))
        el.geo_reference = str(values.get("geo_reference", el.geo_reference))
        try:
            new_h = str(values.get("hierarchy", getattr(el, "hierarchy", "") or "")).strip()
            el.hierarchy = new_h if new_h else None
            if new_h:
                cats = list(getattr(canvas, "hierarchy_categories", []) or [])
                cat = next((c for c in cats if str(c.get("name")) == new_h), None)
                if cat and all(k in cat for k in ("y0", "y1")):
                    try:
                        y0 = float(cat["y0"])
                        y1 = float(cat["y1"])
                        target_y = int((y0 + y1) / 2)
                        el.y = target_y
                    except Exception:
                        pass
        except Exception:
            pass
        try:
            if getattr(el, "ref_file", ""):
                canvas._ensure_ref_group(el)
            else:
                canvas._revert_ref_group_if_needed(el)
        except Exception:
            pass
        try:
            if str(el.element_type).upper() == "GROUP":
                el.collapsed = bool(values.get("collapsed", getattr(el, "collapsed", False)))
        except Exception:
            pass
        canvas.redraw_all()
