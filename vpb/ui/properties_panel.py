from __future__ import annotations

import os

from typing import Callable, Dict, Optional

import tkinter as tk
from tkinter import colorchooser

from vpb.models import VPBConnection, VPBElement
from vpb.styles import CONNECTION_STYLES, ELEMENT_STYLES


class PropertiesPanel(tk.Frame):
    """Einfache Eigenschaftsleiste rechts zur Bearbeitung des ausgewählten Elements (scrollfähig)."""

    def __init__(
        self,
        master,
        on_apply: Optional[Callable[[Dict[str, object]], None]] = None,
        resolve_member_label: Optional[Callable[[str], str]] = None,
        on_member_select: Optional[Callable[[str], None]] = None,
        on_group_add: Optional[Callable[[str], None]] = None,
        on_group_remove: Optional[Callable[[str], None]] = None,
    ):
        super().__init__(master, width=360, bg="#fafafa", relief=tk.GROOVE, borderwidth=1)
        self.on_apply = on_apply
        self._resolve_member_label = resolve_member_label
        self._on_member_select = on_member_select
        self._on_group_add = on_group_add
        self._on_group_remove = on_group_remove

        self._current_element: Optional[VPBElement] = None
        self._current_connection: Optional[VPBConnection] = None
        self._current_hierarchy_index: Optional[int] = None
        self._current_hierarchy: Optional[Dict[str, object]] = None
        self._mode: str = "element"
        self._arrow_styles: list[str] = ["single", "double", "none"]

        container = tk.Frame(self, bg="#fafafa")
        container.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(container, bg="#fafafa", highlightthickness=0)
        ysb = tk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
        self._inner = tk.Frame(canvas, bg="#fafafa", padx=8, pady=8)
        self._inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._inner, anchor="nw")
        canvas.configure(yscrollcommand=ysb.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ysb.pack(side=tk.RIGHT, fill=tk.Y)

        self._inner.grid_columnconfigure(0, weight=1)
        self._inner.grid_rowconfigure(0, weight=1)

        # --- Elementbereich ---
        self._element_section = tk.Frame(self._inner, bg="#fafafa")
        self._element_section.grid(row=0, column=0, sticky="nsew")
        element_row = 0
        tk.Label(self._element_section, text="Eigenschaften", bg="#fafafa", font=("Segoe UI", 11, "bold")).grid(row=element_row, column=0, columnspan=2, sticky="we", pady=(0, 6))
        element_row += 1

        tk.Label(self._element_section, text="Element-ID:", bg="#fafafa").grid(row=element_row, column=0, sticky="e")
        self.var_id = tk.StringVar()
        self.ent_id = tk.Entry(self._element_section, textvariable=self.var_id, state="disabled")
        self.ent_id.grid(row=element_row, column=1, sticky="we", padx=4, pady=2)
        element_row += 1

        tk.Label(self._element_section, text="Typ:", bg="#fafafa").grid(row=element_row, column=0, sticky="e")
        self.var_type = tk.StringVar(value="FUNCTION")
        element_types = sorted(ELEMENT_STYLES.keys()) or ["FUNCTION"]
        self.opt_type = tk.OptionMenu(self._element_section, self.var_type, *element_types)
        self.opt_type.grid(row=element_row, column=1, sticky="we", padx=4, pady=2)
        element_row += 1

        tk.Label(self._element_section, text="Name:", bg="#fafafa").grid(row=element_row, column=0, sticky="e")
        self.var_name = tk.StringVar()
        self.ent_name = tk.Entry(self._element_section, textvariable=self.var_name)
        self.ent_name.grid(row=element_row, column=1, sticky="we", padx=4, pady=2)
        element_row += 1

        tk.Label(self._element_section, text="Beschreibung:", bg="#fafafa").grid(row=element_row, column=0, sticky="ne")
        self.txt_desc = tk.Text(self._element_section, height=4, width=28)
        self.txt_desc.grid(row=element_row, column=1, sticky="we", padx=4, pady=2)
        element_row += 1

        tk.Label(self._element_section, text="Zuständige Stelle:", bg="#fafafa").grid(row=element_row, column=0, sticky="e")
        self.var_auth = tk.StringVar()
        self.ent_auth = tk.Entry(self._element_section, textvariable=self.var_auth)
        self.ent_auth.grid(row=element_row, column=1, sticky="we", padx=4, pady=2)
        element_row += 1

        tk.Label(self._element_section, text="Rechtsgrundlage:", bg="#fafafa").grid(row=element_row, column=0, sticky="e")
        self.var_legal = tk.StringVar()
        self.ent_legal = tk.Entry(self._element_section, textvariable=self.var_legal)
        self.ent_legal.grid(row=element_row, column=1, sticky="we", padx=4, pady=2)
        element_row += 1

        tk.Label(self._element_section, text="Frist (Tage):", bg="#fafafa").grid(row=element_row, column=0, sticky="e")
        self.var_deadline = tk.StringVar(value="0")
        self.ent_deadline = tk.Spinbox(self._element_section, from_=0, to=3650, textvariable=self.var_deadline, width=6)
        self.ent_deadline.grid(row=element_row, column=1, sticky="w", padx=4, pady=2)
        element_row += 1

        tk.Label(self._element_section, text="Geo-Referenz:", bg="#fafafa").grid(row=element_row, column=0, sticky="e")
        self.var_geo = tk.StringVar()
        self.ent_geo = tk.Entry(self._element_section, textvariable=self.var_geo)
        self.ent_geo.grid(row=element_row, column=1, sticky="we", padx=4, pady=2)
        element_row += 1

        tk.Label(self._element_section, text="Hierarchie:", bg="#fafafa").grid(row=element_row, column=0, sticky="e")
        self.var_hierarchy = tk.StringVar(value="")
        self.opt_hierarchy = tk.OptionMenu(self._element_section, self.var_hierarchy, "")
        self.opt_hierarchy.grid(row=element_row, column=1, sticky="we", padx=4, pady=2)
        element_row += 1

        self.ref_section_frame = tk.LabelFrame(self._element_section, text="Referenz", bg="#fafafa", padx=6, pady=4, labelanchor="n")
        self.ref_section_frame.grid(row=element_row, column=0, columnspan=2, sticky="we", pady=(8, 4))
        self.ref_section_frame.columnconfigure(1, weight=1)
        self.ref_section_frame.rowconfigure(2, weight=1)

        tk.Label(self.ref_section_frame, text="ref_file:", bg="#fafafa").grid(row=0, column=0, sticky="ne", pady=(0, 2))
        self.var_ref_file = tk.StringVar()
        self.ent_ref_file = tk.Entry(self.ref_section_frame, textvariable=self.var_ref_file, state="readonly")
        self.ent_ref_file.grid(row=0, column=1, sticky="we", padx=(4, 0), pady=(0, 4))

        self.var_ref_status = tk.StringVar(value="")
        self.lbl_ref_status = tk.Label(self.ref_section_frame, textvariable=self.var_ref_status, bg="#fafafa", anchor="w", fg="#666666")
        self.lbl_ref_status.grid(row=1, column=0, columnspan=2, sticky="we", pady=(0, 4))

        preview_wrap = tk.Frame(self.ref_section_frame, bg="#fafafa")
        preview_wrap.grid(row=2, column=0, columnspan=2, sticky="nsew")
        preview_wrap.columnconfigure(0, weight=1)
        preview_wrap.rowconfigure(0, weight=1)
        self.txt_ref_preview = tk.Text(preview_wrap, height=8, wrap="word", state="disabled")
        self.txt_ref_preview.grid(row=0, column=0, sticky="nsew")
        self._ref_scroll = tk.Scrollbar(preview_wrap, orient=tk.VERTICAL, command=self.txt_ref_preview.yview)
        self._ref_scroll.grid(row=0, column=1, sticky="ns")
        self.txt_ref_preview.configure(yscrollcommand=self._ref_scroll.set)

        self.ref_section_frame.grid_remove()
        element_row += 1

        self.grp_section_frame = tk.Frame(self._element_section, bg="#fafafa")
        tk.Label(self.grp_section_frame, text="Gruppe", bg="#fafafa", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky="we", pady=(8, 4))
        tk.Label(self.grp_section_frame, text="Zugeklappt:", bg="#fafafa").grid(row=1, column=0, sticky="e")
        self.var_collapsed = tk.BooleanVar(value=False)
        self.chk_collapsed = tk.Checkbutton(self.grp_section_frame, variable=self.var_collapsed, bg="#fafafa")
        self.chk_collapsed.grid(row=1, column=1, sticky="w", padx=4, pady=2)
        tk.Label(self.grp_section_frame, text="Mitglieder:", bg="#fafafa").grid(row=2, column=0, sticky="ne")
        self.lst_members = tk.Listbox(self.grp_section_frame, height=5)
        self.lst_members.grid(row=2, column=1, sticky="we", padx=4, pady=2)
        self.lst_members.bind("<Double-Button-1>", self._on_member_dblclick)
        self.grp_section_frame.columnconfigure(1, weight=1)
        self._member_index_to_id: list[str] = []
        btn_wrap = tk.Frame(self.grp_section_frame, bg="#fafafa")
        btn_wrap.grid(row=3, column=0, columnspan=2, sticky="we", pady=(2, 0))
        self.btn_grp_add = tk.Button(btn_wrap, text="Aus Auswahl hinzufügen", command=self._on_group_add_from_selection)
        self.btn_grp_add.pack(side=tk.LEFT, padx=2)
        self.btn_grp_remove = tk.Button(btn_wrap, text="Aus Auswahl entfernen", command=self._on_group_remove_from_selection)
        self.btn_grp_remove.pack(side=tk.LEFT, padx=2)
        self.grp_section_frame.grid(row=element_row, column=0, columnspan=2, sticky="we")
        self.grp_section_frame.grid_remove()
        element_row += 1

        self._element_section.columnconfigure(1, weight=1)
        self._element_inputs = [
            self.opt_type,
            self.ent_name,
            self.ent_auth,
            self.ent_legal,
            self.ent_deadline,
            self.ent_geo,
            self.opt_hierarchy,
            self.chk_collapsed,
            self.lst_members,
            self.btn_grp_add,
            self.btn_grp_remove,
        ]
        self._element_texts = [self.txt_desc]

        # --- Verbindungsbereich ---
        self._connection_section = tk.Frame(self._inner, bg="#fafafa")
        self._connection_section.grid(row=0, column=0, sticky="nsew")
        self._connection_section.grid_remove()
        conn_row = 0
        tk.Label(self._connection_section, text="Verbindung", bg="#fafafa", font=("Segoe UI", 11, "bold")).grid(row=conn_row, column=0, columnspan=2, sticky="we", pady=(0, 6))
        conn_row += 1

        tk.Label(self._connection_section, text="Verbindung-ID:", bg="#fafafa").grid(row=conn_row, column=0, sticky="e")
        self.var_conn_id = tk.StringVar()
        self.ent_conn_id = tk.Entry(self._connection_section, textvariable=self.var_conn_id, state="disabled")
        self.ent_conn_id.grid(row=conn_row, column=1, sticky="we", padx=4, pady=2)
        conn_row += 1

        tk.Label(self._connection_section, text="Typ:", bg="#fafafa").grid(row=conn_row, column=0, sticky="e")
        conn_types = sorted(CONNECTION_STYLES.keys()) or ["SEQUENCE"]
        self.var_conn_type = tk.StringVar(value=conn_types[0])
        self.opt_conn_type = tk.OptionMenu(self._connection_section, self.var_conn_type, *conn_types)
        self.opt_conn_type.grid(row=conn_row, column=1, sticky="we", padx=4, pady=2)
        conn_row += 1

        tk.Label(self._connection_section, text="Quelle:", bg="#fafafa").grid(row=conn_row, column=0, sticky="e")
        self.var_conn_source = tk.StringVar(value="")
        tk.Label(self._connection_section, textvariable=self.var_conn_source, bg="#fafafa", anchor="w").grid(row=conn_row, column=1, sticky="we", padx=4, pady=2)
        conn_row += 1

        tk.Label(self._connection_section, text="Ziel:", bg="#fafafa").grid(row=conn_row, column=0, sticky="e")
        self.var_conn_target = tk.StringVar(value="")
        tk.Label(self._connection_section, textvariable=self.var_conn_target, bg="#fafafa", anchor="w").grid(row=conn_row, column=1, sticky="we", padx=4, pady=2)
        conn_row += 1

        tk.Label(self._connection_section, text="Pfeilspitze:", bg="#fafafa").grid(row=conn_row, column=0, sticky="e")
        self.var_conn_arrow = tk.StringVar(value=self._arrow_styles[0])
        self.opt_conn_arrow = tk.OptionMenu(self._connection_section, self.var_conn_arrow, *self._arrow_styles)
        self.opt_conn_arrow.grid(row=conn_row, column=1, sticky="we", padx=4, pady=2)
        conn_row += 1

        tk.Label(self._connection_section, text="Routing:", bg="#fafafa").grid(row=conn_row, column=0, sticky="e")
        self._routing_modes = ["auto", "smart", "smart-plus", "straight", "orthogonal", "curved", "multi"]
        self.var_conn_routing = tk.StringVar(value=self._routing_modes[0])
        self.opt_conn_routing = tk.OptionMenu(self._connection_section, self.var_conn_routing, *self._routing_modes)
        self.opt_conn_routing.grid(row=conn_row, column=1, sticky="we", padx=4, pady=2)
        conn_row += 1

        tk.Label(self._connection_section, text="Beschreibung:", bg="#fafafa").grid(row=conn_row, column=0, sticky="ne")
        self.txt_conn_desc = tk.Text(self._connection_section, height=4, width=28)
        self.txt_conn_desc.grid(row=conn_row, column=1, sticky="we", padx=4, pady=2)
        conn_row += 1

        self._connection_section.columnconfigure(1, weight=1)
        self._connection_inputs = [self.opt_conn_type, self.opt_conn_arrow, self.opt_conn_routing]
        self._connection_texts = [self.txt_conn_desc]

        # --- Hierarchiebereich ---
        self._hierarchy_section = tk.Frame(self._inner, bg="#fafafa")
        self._hierarchy_section.grid(row=0, column=0, sticky="nsew")
        self._hierarchy_section.grid_remove()
        hier_row = 0
        tk.Label(
            self._hierarchy_section,
            text="Hierarchieband",
            bg="#fafafa",
            font=("Segoe UI", 11, "bold"),
        ).grid(row=hier_row, column=0, columnspan=2, sticky="we", pady=(0, 6))
        hier_row += 1

        tk.Label(self._hierarchy_section, text="Name:", bg="#fafafa").grid(row=hier_row, column=0, sticky="e")
        self.var_hier_name = tk.StringVar()
        self.ent_hier_name = tk.Entry(self._hierarchy_section, textvariable=self.var_hier_name)
        self.ent_hier_name.grid(row=hier_row, column=1, sticky="we", padx=4, pady=2)
        hier_row += 1

        tk.Label(self._hierarchy_section, text="Farbe:", bg="#fafafa").grid(row=hier_row, column=0, sticky="e")
        color_frame = tk.Frame(self._hierarchy_section, bg="#fafafa")
        color_frame.grid(row=hier_row, column=1, sticky="we", padx=4, pady=2)
        color_frame.columnconfigure(0, weight=1)
        self.var_hier_color = tk.StringVar()
        self.ent_hier_color = tk.Entry(color_frame, textvariable=self.var_hier_color)
        self.ent_hier_color.grid(row=0, column=0, sticky="we")
        self.btn_hier_color = tk.Button(color_frame, text="Wählen", command=self._choose_hierarchy_color)
        self.btn_hier_color.grid(row=0, column=1, padx=(4, 0))
        hier_row += 1

        tk.Label(self._hierarchy_section, text="Y-Beginn:", bg="#fafafa").grid(row=hier_row, column=0, sticky="e")
        self.var_hier_y0 = tk.StringVar(value="0")
        self.ent_hier_y0 = tk.Entry(self._hierarchy_section, textvariable=self.var_hier_y0)
        self.ent_hier_y0.grid(row=hier_row, column=1, sticky="we", padx=4, pady=2)
        hier_row += 1

        tk.Label(self._hierarchy_section, text="Y-Ende:", bg="#fafafa").grid(row=hier_row, column=0, sticky="e")
        self.var_hier_y1 = tk.StringVar(value="0")
        self.ent_hier_y1 = tk.Entry(self._hierarchy_section, textvariable=self.var_hier_y1)
        self.ent_hier_y1.grid(row=hier_row, column=1, sticky="we", padx=4, pady=2)
        hier_row += 1

        self._hierarchy_section.columnconfigure(1, weight=1)
        self._hierarchy_inputs = [
            self.ent_hier_name,
            self.ent_hier_color,
            self.btn_hier_color,
            self.ent_hier_y0,
            self.ent_hier_y1,
        ]

        # --- Buttons ---
        btns = tk.Frame(self._inner, bg="#fafafa")
        btns.grid(row=1, column=0, pady=(8, 0), sticky="we")
        tk.Button(btns, text="Übernehmen", command=self._apply).pack(side=tk.LEFT, padx=4)
        tk.Button(btns, text="Zurücksetzen", command=self._reset).pack(side=tk.LEFT, padx=4)

        self._show_element_section()
        self._set_element_enabled(False)
        self._set_connection_enabled(False)
        self._set_hierarchy_enabled(False)
        self.grp_section_frame.grid_remove()

    def _show_element_section(self) -> None:
        self._connection_section.grid_remove()
        self._hierarchy_section.grid_remove()
        self._element_section.grid()
        self._mode = "element"

    def _show_connection_section(self) -> None:
        self._element_section.grid_remove()
        self._hierarchy_section.grid_remove()
        self._connection_section.grid()
        self._mode = "connection"

    def _show_hierarchy_section(self) -> None:
        self._element_section.grid_remove()
        self._connection_section.grid_remove()
        self._hierarchy_section.grid()
        self._mode = "hierarchy"

    def _toggle_widgets(self, widgets, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        for widget in widgets:
            try:
                widget.configure(state=state)
            except Exception:
                pass

    def _set_element_enabled(self, enabled: bool) -> None:
        self._toggle_widgets(self._element_inputs, enabled)
        self.txt_desc.configure(state="normal" if enabled else "disabled")
        self.lst_members.configure(state="normal" if enabled else "disabled")
        self.btn_grp_add.configure(state="normal" if enabled else "disabled")
        self.btn_grp_remove.configure(state="normal" if enabled else "disabled")

    def _set_connection_enabled(self, enabled: bool) -> None:
        self._toggle_widgets(self._connection_inputs, enabled)
        self.txt_conn_desc.configure(state="normal" if enabled else "disabled")

    def _set_hierarchy_enabled(self, enabled: bool) -> None:
        self._toggle_widgets(self._hierarchy_inputs, enabled)

    def _set_option_values(self, option_menu: tk.OptionMenu, variable: tk.StringVar, values: list[str]) -> None:
        menu = option_menu["menu"]
        menu.delete(0, "end")
        options = values or [""]
        for val in options:
            menu.add_command(label=val, command=tk._setit(variable, val))

    def _set_entry_readonly(self, entry: tk.Entry, value: str) -> None:
        entry.configure(state="normal")
        entry.delete(0, tk.END)
        entry.insert(0, value)
        entry.configure(state="readonly")

    def _set_text_widget(self, widget: tk.Text, value: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        if value:
            widget.insert("1.0", value)
        widget.configure(state="disabled")

    def _clear_ref_section(self) -> None:
        try:
            self.ref_section_frame.grid_remove()
        except Exception:
            pass
        self.var_ref_file.set("")
        self.var_ref_status.set("")
        self._set_text_widget(self.txt_ref_preview, "")

    def _update_ref_section(
        self,
        ref_file: str,
        resolved_path: Optional[str],
        content: Optional[str],
        error: Optional[str],
        truncated: bool,
    ) -> None:
        visible = bool(ref_file or content or error)
        if not visible:
            self._clear_ref_section()
            return
        try:
            self.ref_section_frame.grid()
        except Exception:
            pass
        display_ref = ref_file or ""
        self._set_entry_readonly(self.ent_ref_file, display_ref)
        if error:
            status = error
        else:
            status_parts: list[str] = []
            if resolved_path:
                try:
                    base = os.path.basename(resolved_path)
                    status_parts.append(base if base else resolved_path)
                except Exception:
                    status_parts.append(resolved_path)
            if content:
                length = len(content)
                suffix = " (gekürzt)" if truncated else ""
                status_parts.append(f"Vorschau: {length} Zeichen{suffix}")
            elif truncated:
                status_parts.append("Vorschau gekürzt")
            status = " | ".join(status_parts)
        self.var_ref_status.set(status)
        preview_text = content or (error or "")
        self._set_text_widget(self.txt_ref_preview, preview_text)

    def _format_member_label(self, element_id: Optional[str]) -> str:
        if not element_id:
            return ""
        if callable(self._resolve_member_label):
            try:
                label = self._resolve_member_label(element_id)
                if label:
                    return str(label)
            except Exception:
                pass
        return str(element_id)

    def set_element(self, el: Optional[VPBElement], connection: Optional[VPBConnection] = None) -> None:
        self._current_hierarchy_index = None
        self._current_hierarchy = None
        if connection is not None:
            self._current_element = None
            self._current_connection = connection
            self._show_connection_section()
            self._populate_connection(connection)
            return
        self._current_element = el
        self._current_connection = None
        self._show_element_section()
        self._populate_element(el)

    def set_hierarchy(self, index: Optional[int], data: Optional[Dict[str, object]]) -> None:
        self._current_element = None
        self._current_connection = None
        self._current_hierarchy_index = index
        self._current_hierarchy = dict(data) if data else None
        if not data:
            self._populate_hierarchy(None)
            self._show_element_section()
            return
        self._show_hierarchy_section()
        self._populate_hierarchy(self._current_hierarchy)

    def _populate_element(self, el: Optional[VPBElement]) -> None:
        if not el:
            self.var_id.set("")
            self.var_type.set((sorted(ELEMENT_STYLES.keys()) or ["FUNCTION"])[0])
            self.var_name.set("")
            self.var_auth.set("")
            self.var_legal.set("")
            self.var_deadline.set("0")
            self.var_geo.set("")
            self.var_hierarchy.set("")
            self.var_collapsed.set(False)
            self.txt_desc.configure(state="normal")
            self.txt_desc.delete("1.0", tk.END)
            self.txt_desc.configure(state="disabled")
            self.lst_members.delete(0, tk.END)
            self._member_index_to_id = []
            self.grp_section_frame.grid_remove()
            self._set_element_enabled(False)
            self._set_connection_enabled(False)
            self._clear_ref_section()
            return

        self._set_element_enabled(True)
        self._set_connection_enabled(False)
        self.var_id.set(el.element_id)
        self.var_type.set(el.element_type)
        self.var_name.set(el.name)
        self.txt_desc.configure(state="normal")
        self.txt_desc.delete("1.0", tk.END)
        self.txt_desc.insert("1.0", el.description or "")
        self.var_auth.set(el.responsible_authority or "")
        self.var_legal.set(el.legal_basis or "")
        self.var_deadline.set(str(el.deadline_days or 0))
        self.var_geo.set(el.geo_reference or "")

        try:
            names: list[str] = []
            app = self.master.master.master  # type: ignore[attr-defined]
            cats = list(getattr(app.canvas, "hierarchy_categories", []) or [])  # type: ignore[attr-defined]
            names = [str(c.get("name")) for c in cats if c and c.get("name")]
        except Exception:
            names = []
        self._set_option_values(self.opt_hierarchy, self.var_hierarchy, names or [""])
        self.var_hierarchy.set(getattr(el, "hierarchy", "") or "")

        ref_file = getattr(el, "ref_file", "") or ""
        resolved_path = getattr(el, "ref_inline_path", None)
        ref_content = getattr(el, "ref_inline_content", None)
        ref_error = getattr(el, "ref_inline_error", None)
        ref_truncated = bool(getattr(el, "ref_inline_truncated", False))
        self._update_ref_section(ref_file, resolved_path, ref_content, ref_error, ref_truncated)

        if str(el.element_type).upper() == "GROUP":
            self.var_collapsed.set(bool(getattr(el, "collapsed", False)))
            self.lst_members.configure(state="normal")
            self.lst_members.delete(0, tk.END)
            self._member_index_to_id = []
            members = list(getattr(el, "members", []) or [])
            for mid in members:
                label = self._format_member_label(mid)
                self.lst_members.insert(tk.END, label)
                self._member_index_to_id.append(str(mid))
            self.grp_section_frame.grid()
            self.btn_grp_add.configure(state="normal")
            self.btn_grp_remove.configure(state="normal")
        else:
            self.var_collapsed.set(False)
            self.lst_members.delete(0, tk.END)
            self._member_index_to_id = []
            self.lst_members.configure(state="disabled")
            self.btn_grp_add.configure(state="disabled")
            self.btn_grp_remove.configure(state="disabled")
            self.grp_section_frame.grid_remove()

    def _populate_hierarchy(self, cat: Optional[Dict[str, object]]) -> None:
        if not cat:
            self.var_hier_name.set("")
            self.var_hier_color.set("")
            self.var_hier_y0.set("0")
            self.var_hier_y1.set("0")
            self._set_hierarchy_enabled(False)
            return

        self._set_hierarchy_enabled(True)
        self.var_hier_name.set(str(cat.get("name", "") or ""))
        self.var_hier_color.set(str(cat.get("color", "") or ""))
        try:
            self.var_hier_y0.set(str(float(cat.get("y0", 0.0) or 0.0)))
        except Exception:
            self.var_hier_y0.set("0")
        try:
            self.var_hier_y1.set(str(float(cat.get("y1", 0.0) or 0.0)))
        except Exception:
            self.var_hier_y1.set("0")

    def _choose_hierarchy_color(self) -> None:
        try:
            current = self.var_hier_color.get() or "#ffffff"
        except Exception:
            current = "#ffffff"
        try:
            result = colorchooser.askcolor(parent=self.winfo_toplevel(), initialcolor=current)
        except Exception:
            result = (None, None)
        if result and result[1]:
            self.var_hier_color.set(str(result[1]))

    def refresh_hierarchy_options(self, names: Optional[list[str]]) -> None:
        values = [str(name) for name in (names or []) if name]
        current = self.var_hierarchy.get()
        self._set_option_values(self.opt_hierarchy, self.var_hierarchy, values or [""])
        if current and current in values:
            self.var_hierarchy.set(current)
        elif values:
            self.var_hierarchy.set(values[0])
        else:
            self.var_hierarchy.set("")

    def _populate_connection(self, conn: Optional[VPBConnection]) -> None:
        if not conn:
            self.var_conn_id.set("")
            self.var_conn_type.set((sorted(CONNECTION_STYLES.keys()) or ["SEQUENCE"])[0])
            self.var_conn_source.set("")
            self.var_conn_target.set("")
            self.var_conn_arrow.set(self._arrow_styles[0])
            self.var_conn_routing.set(self._routing_modes[0])
            self._set_option_values(self.opt_conn_routing, self.var_conn_routing, self._routing_modes)
            self.txt_conn_desc.configure(state="normal")
            self.txt_conn_desc.delete("1.0", tk.END)
            self.txt_conn_desc.configure(state="disabled")
            self._set_connection_enabled(False)
            return

        self._set_connection_enabled(True)
        self._set_element_enabled(False)
        self.var_conn_id.set(conn.connection_id)
        conn_type = str(getattr(conn, "connection_type", "") or "SEQUENCE")
        type_options = sorted(CONNECTION_STYLES.keys())
        if conn_type not in type_options:
            type_options.append(conn_type)
        self._set_option_values(self.opt_conn_type, self.var_conn_type, type_options or ["SEQUENCE"])
        self.var_conn_type.set(conn_type)

        self.var_conn_source.set(self._format_member_label(getattr(conn, "source_element", "")))
        self.var_conn_target.set(self._format_member_label(getattr(conn, "target_element", "")))

        arrow = str(getattr(conn, "arrow_style", "single") or "single").lower()
        if arrow not in self._arrow_styles:
            self._arrow_styles.append(arrow)
        self._set_option_values(self.opt_conn_arrow, self.var_conn_arrow, self._arrow_styles)
        self.var_conn_arrow.set(arrow)

        routing = str(getattr(conn, "routing_mode", "auto") or "auto").lower()
        if routing not in self._routing_modes:
            self._routing_modes.append(routing)
        self._set_option_values(self.opt_conn_routing, self.var_conn_routing, self._routing_modes)
        self.var_conn_routing.set(routing)

        self.txt_conn_desc.configure(state="normal")
        self.txt_conn_desc.delete("1.0", tk.END)
        self.txt_conn_desc.insert("1.0", getattr(conn, "description", "") or "")

    def _apply(self) -> None:
        if self._mode == "connection":
            if not self._current_connection:
                return
            values = {
                "kind": "connection",
                "connection_type": self.var_conn_type.get().strip(),
                "arrow_style": self.var_conn_arrow.get().strip(),
                "routing_mode": self.var_conn_routing.get().strip(),
                "description": self.txt_conn_desc.get("1.0", tk.END).strip(),
            }
            if self.on_apply:
                self.on_apply(values)
            return

        if self._mode == "hierarchy":
            if self._current_hierarchy_index is None:
                return
            values = {
                "kind": "hierarchy",
                "index": self._current_hierarchy_index,
                "name": self.var_hier_name.get().strip(),
                "color": self.var_hier_color.get().strip(),
                "y0": self.var_hier_y0.get().strip(),
                "y1": self.var_hier_y1.get().strip(),
            }
            if self.on_apply:
                self.on_apply(values)
            return

        if not self._current_element:
            return

        values = {
            "kind": "element",
            "element_type": self.var_type.get(),
            "name": self.var_name.get(),
            "description": self.txt_desc.get("1.0", tk.END).strip(),
            "responsible_authority": self.var_auth.get(),
            "legal_basis": self.var_legal.get(),
            "deadline_days": self.var_deadline.get(),
            "geo_reference": self.var_geo.get(),
            "hierarchy": self.var_hierarchy.get().strip(),
        }

        if str(self._current_element.element_type).upper() == "GROUP":
            values["collapsed"] = bool(self.var_collapsed.get())

        if self.on_apply:
            self.on_apply(values)

    # ---- GROUP: Event-Handler ----
    def _on_member_dblclick(self, event=None):
        try:
            sel = self.lst_members.curselection()
            if not sel:
                return
            idx = int(sel[0])
            if 0 <= idx < len(self._member_index_to_id):
                eid = self._member_index_to_id[idx]
                if callable(self._on_member_select):
                    self._on_member_select(eid)
        except Exception:
            pass

    def _on_group_add_from_selection(self):
        try:
            if not self._current_element or str(self._current_element.element_type).upper() != "GROUP":
                return
            if callable(self._on_group_add):
                self._on_group_add(self._current_element.element_id)
        except Exception:
            pass

    def _on_group_remove_from_selection(self):
        try:
            if not self._current_element or str(self._current_element.element_type).upper() != "GROUP":
                return
            if callable(self._on_group_remove):
                self._on_group_remove(self._current_element.element_id)
        except Exception:
            pass

    # Externe Setter, falls Konstruktor nicht genutzt wird
    def set_group_helpers(self, resolve_member_label: Optional[Callable[[str], str]] = None,
                          on_member_select: Optional[Callable[[str], None]] = None,
                          on_group_add: Optional[Callable[[str], None]] = None,
                          on_group_remove: Optional[Callable[[str], None]] = None):
        if resolve_member_label is not None:
            self._resolve_member_label = resolve_member_label
        if on_member_select is not None:
            self._on_member_select = on_member_select
        if on_group_add is not None:
            self._on_group_add = on_group_add
        if on_group_remove is not None:
            self._on_group_remove = on_group_remove

    def _reset(self):
        if self._mode == "hierarchy":
            self.set_hierarchy(self._current_hierarchy_index, self._current_hierarchy)
        else:
            self.set_element(self._current_element, self._current_connection)


