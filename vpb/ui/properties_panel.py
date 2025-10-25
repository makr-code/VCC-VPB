from __future__ import annotations

import os

from typing import Callable, Dict, Optional

import tkinter as tk
from tkinter import colorchooser, messagebox

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

        # --- Counter-Section (COUNTER) ---
        self.counter_section_frame = tk.LabelFrame(
            self._element_section,
            text="🔢 Zähler-Eigenschaften",
            bg="#fafafa",
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=10,
        )
        counter_row = 0
        
        # Counter-Typ
        tk.Label(self.counter_section_frame, text="Typ:", bg="#fafafa").grid(row=counter_row, column=0, sticky="e", pady=2)
        self.var_counter_type = tk.StringVar(value="UP")
        counter_types = ["UP", "DOWN", "UP_DOWN"]
        self.opt_counter_type = tk.OptionMenu(self.counter_section_frame, self.var_counter_type, *counter_types)
        self.opt_counter_type.grid(row=counter_row, column=1, sticky="we", padx=4, pady=2)
        counter_row += 1
        
        # Startwert
        tk.Label(self.counter_section_frame, text="Startwert:", bg="#fafafa").grid(row=counter_row, column=0, sticky="e", pady=2)
        self.var_counter_start = tk.IntVar(value=0)
        self.spin_counter_start = tk.Spinbox(
            self.counter_section_frame,
            from_=0,
            to=10000,
            textvariable=self.var_counter_start,
            width=15,
        )
        self.spin_counter_start.grid(row=counter_row, column=1, sticky="we", padx=4, pady=2)
        counter_row += 1
        
        # Maximalwert
        tk.Label(self.counter_section_frame, text="Maximum:", bg="#fafafa").grid(row=counter_row, column=0, sticky="e", pady=2)
        self.var_counter_max = tk.IntVar(value=100)
        self.spin_counter_max = tk.Spinbox(
            self.counter_section_frame,
            from_=1,
            to=10000,
            textvariable=self.var_counter_max,
            width=15,
        )
        self.spin_counter_max.grid(row=counter_row, column=1, sticky="we", padx=4, pady=2)
        counter_row += 1
        
        # Aktueller Wert (nur Anzeige)
        tk.Label(self.counter_section_frame, text="Aktuell:", bg="#fafafa").grid(row=counter_row, column=0, sticky="e", pady=2)
        self.var_counter_current = tk.IntVar(value=0)
        self.lbl_counter_current = tk.Label(
            self.counter_section_frame,
            textvariable=self.var_counter_current,
            bg="#E8F4F8",
            fg="#2196F3",
            font=("Arial", 10, "bold"),
            relief=tk.SUNKEN,
            padx=5,
            pady=2,
        )
        self.lbl_counter_current.grid(row=counter_row, column=1, sticky="we", padx=4, pady=2)
        counter_row += 1
        
        # Reset bei Maximum
        self.var_counter_reset = tk.BooleanVar(value=False)
        self.chk_counter_reset = tk.Checkbutton(
            self.counter_section_frame,
            text="Bei Maximum zurücksetzen",
            variable=self.var_counter_reset,
            bg="#fafafa",
        )
        self.chk_counter_reset.grid(row=counter_row, column=0, columnspan=2, sticky="w", pady=2)
        counter_row += 1
        
        # Aktion bei Maximum
        tk.Label(self.counter_section_frame, text="Bei Max. zu:", bg="#fafafa").grid(row=counter_row, column=0, sticky="e", pady=2)
        self.var_counter_on_max = tk.StringVar(value="")
        self.ent_counter_on_max = tk.Entry(self.counter_section_frame, textvariable=self.var_counter_on_max, width=20)
        self.ent_counter_on_max.grid(row=counter_row, column=1, sticky="we", padx=4, pady=2)
        counter_row += 1
        
        # Hinweis
        tk.Label(
            self.counter_section_frame,
            text="(Element-ID für Eskalation)",
            bg="#fafafa",
            fg="#666",
            font=("Arial", 8),
        ).grid(row=counter_row, column=1, sticky="w", padx=4)
        counter_row += 1
        
        self.counter_section_frame.columnconfigure(1, weight=1)
        self.counter_section_frame.grid(row=element_row, column=0, columnspan=2, sticky="we", pady=(10, 0))
        self.counter_section_frame.grid_remove()
        element_row += 1
        
        # --- CONDITION-Section (🔀 Bedingung) ---
        self.condition_section_frame = tk.LabelFrame(
            self._element_section,
            text=" 🔀 Bedingung ",
            bg="#fafafa",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=10
        )
        condition_row = 0
        
        # Checks Liste
        tk.Label(self.condition_section_frame, text="Checks:", bg="#fafafa", font=("Arial", 9, "bold")).grid(
            row=condition_row, column=0, columnspan=2, sticky="w", pady=(0, 5)
        )
        condition_row += 1
        
        # Listbox für Checks mit Scrollbar
        checks_frame = tk.Frame(self.condition_section_frame, bg="#fafafa")
        checks_frame.grid(row=condition_row, column=0, columnspan=2, sticky="we", pady=(0, 5))
        
        self.lst_condition_checks = tk.Listbox(checks_frame, height=4, width=30)
        checks_scrollbar = tk.Scrollbar(checks_frame, orient=tk.VERTICAL, command=self.lst_condition_checks.yview)
        self.lst_condition_checks.config(yscrollcommand=checks_scrollbar.set)
        self.lst_condition_checks.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        checks_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        condition_row += 1
        
        # Buttons für Check-Management
        checks_btn_frame = tk.Frame(self.condition_section_frame, bg="#fafafa")
        checks_btn_frame.grid(row=condition_row, column=0, columnspan=2, sticky="we", pady=(0, 10))
        
        self.btn_check_add = tk.Button(checks_btn_frame, text="➕ Add", width=8, command=self._add_condition_check)
        self.btn_check_add.pack(side=tk.LEFT, padx=2)
        
        self.btn_check_edit = tk.Button(checks_btn_frame, text="✏️ Edit", width=8, command=self._edit_condition_check)
        self.btn_check_edit.pack(side=tk.LEFT, padx=2)
        
        self.btn_check_remove = tk.Button(checks_btn_frame, text="🗑️ Remove", width=8, command=self._remove_condition_check)
        self.btn_check_remove.pack(side=tk.LEFT, padx=2)
        condition_row += 1
        
        # Logik (AND/OR)
        tk.Label(self.condition_section_frame, text="Logik:", bg="#fafafa").grid(row=condition_row, column=0, sticky="e", pady=2)
        self.var_condition_logic = tk.StringVar(value="AND")
        logic_types = ["AND", "OR"]
        self.opt_condition_logic = tk.OptionMenu(self.condition_section_frame, self.var_condition_logic, *logic_types)
        self.opt_condition_logic.grid(row=condition_row, column=1, sticky="w", padx=4, pady=2)
        condition_row += 1
        
        # TRUE Target
        tk.Label(self.condition_section_frame, text="TRUE → :", bg="#fafafa").grid(row=condition_row, column=0, sticky="e", pady=2)
        self.var_condition_true = tk.StringVar()
        self.ent_condition_true = tk.Entry(self.condition_section_frame, textvariable=self.var_condition_true, width=20)
        self.ent_condition_true.grid(row=condition_row, column=1, sticky="w", padx=4, pady=2)
        tk.Label(
            self.condition_section_frame,
            text="(Element-ID)",
            font=("Arial", 7),
            fg="#888",
            bg="#fafafa"
        ).grid(row=condition_row + 1, column=1, sticky="w", padx=4)
        condition_row += 2
        
        # FALSE Target
        tk.Label(self.condition_section_frame, text="FALSE → :", bg="#fafafa").grid(row=condition_row, column=0, sticky="e", pady=2)
        self.var_condition_false = tk.StringVar()
        self.ent_condition_false = tk.Entry(self.condition_section_frame, textvariable=self.var_condition_false, width=20)
        self.ent_condition_false.grid(row=condition_row, column=1, sticky="w", padx=4, pady=2)
        tk.Label(
            self.condition_section_frame,
            text="(Element-ID)",
            font=("Arial", 7),
            fg="#888",
            bg="#fafafa"
        ).grid(row=condition_row + 1, column=1, sticky="w", padx=4)
        condition_row += 2
        
        self.condition_section_frame.columnconfigure(1, weight=1)
        self.condition_section_frame.grid(row=element_row, column=0, columnspan=2, sticky="we", pady=(10, 0))
        self.condition_section_frame.grid_remove()
        element_row += 1
        
        # --- ERROR_HANDLER-Section (⚠️ Fehlerbehandlung) ---
        self.error_handler_section_frame = tk.LabelFrame(
            self._element_section,
            text=" ⚠️ Fehlerbehandlung ",
            bg="#fafafa",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=10
        )
        eh_row = 0
        
        # Handler Type
        tk.Label(self.error_handler_section_frame, text="Type:", bg="#fafafa", font=("Arial", 9, "bold")).grid(
            row=eh_row, column=0, sticky="e", pady=2
        )
        self.var_error_handler_type = tk.StringVar(value="RETRY")
        handler_types = ["RETRY", "FALLBACK", "NOTIFY", "ABORT"]
        self.opt_error_handler_type = tk.OptionMenu(
            self.error_handler_section_frame,
            self.var_error_handler_type,
            *handler_types
        )
        self.opt_error_handler_type.grid(row=eh_row, column=1, sticky="w", padx=4, pady=2)
        eh_row += 1
        
        # Retry Count
        tk.Label(self.error_handler_section_frame, text="Retry Count:", bg="#fafafa").grid(
            row=eh_row, column=0, sticky="e", pady=2
        )
        self.var_error_handler_retry_count = tk.StringVar(value="3")
        self.ent_error_handler_retry_count = tk.Entry(
            self.error_handler_section_frame,
            textvariable=self.var_error_handler_retry_count,
            width=10
        )
        self.ent_error_handler_retry_count.grid(row=eh_row, column=1, sticky="w", padx=4, pady=2)
        eh_row += 1
        
        # Retry Delay
        tk.Label(self.error_handler_section_frame, text="Retry Delay (s):", bg="#fafafa").grid(
            row=eh_row, column=0, sticky="e", pady=2
        )
        self.var_error_handler_retry_delay = tk.StringVar(value="60")
        self.ent_error_handler_retry_delay = tk.Entry(
            self.error_handler_section_frame,
            textvariable=self.var_error_handler_retry_delay,
            width=10
        )
        self.ent_error_handler_retry_delay.grid(row=eh_row, column=1, sticky="w", padx=4, pady=2)
        eh_row += 1
        
        # Timeout
        tk.Label(self.error_handler_section_frame, text="Timeout (s):", bg="#fafafa").grid(
            row=eh_row, column=0, sticky="e", pady=2
        )
        self.var_error_handler_timeout = tk.StringVar(value="300")
        self.ent_error_handler_timeout = tk.Entry(
            self.error_handler_section_frame,
            textvariable=self.var_error_handler_timeout,
            width=10
        )
        self.ent_error_handler_timeout.grid(row=eh_row, column=1, sticky="w", padx=4, pady=2)
        tk.Label(
            self.error_handler_section_frame,
            text="(0 = kein Timeout)",
            font=("Arial", 7),
            fg="#888",
            bg="#fafafa"
        ).grid(row=eh_row, column=2, sticky="w", padx=2)
        eh_row += 1
        
        # Error Target
        tk.Label(self.error_handler_section_frame, text="Error → :", bg="#fafafa").grid(
            row=eh_row, column=0, sticky="e", pady=2
        )
        self.var_error_handler_on_error = tk.StringVar()
        self.ent_error_handler_on_error = tk.Entry(
            self.error_handler_section_frame,
            textvariable=self.var_error_handler_on_error,
            width=20
        )
        self.ent_error_handler_on_error.grid(row=eh_row, column=1, sticky="w", padx=4, pady=2)
        tk.Label(
            self.error_handler_section_frame,
            text="(Element-ID bei Fehler)",
            font=("Arial", 7),
            fg="#888",
            bg="#fafafa"
        ).grid(row=eh_row + 1, column=1, sticky="w", padx=4)
        eh_row += 2
        
        # Success Target
        tk.Label(self.error_handler_section_frame, text="Success → :", bg="#fafafa").grid(
            row=eh_row, column=0, sticky="e", pady=2
        )
        self.var_error_handler_on_success = tk.StringVar()
        self.ent_error_handler_on_success = tk.Entry(
            self.error_handler_section_frame,
            textvariable=self.var_error_handler_on_success,
            width=20
        )
        self.ent_error_handler_on_success.grid(row=eh_row, column=1, sticky="w", padx=4, pady=2)
        tk.Label(
            self.error_handler_section_frame,
            text="(Element-ID bei Erfolg)",
            font=("Arial", 7),
            fg="#888",
            bg="#fafafa"
        ).grid(row=eh_row + 1, column=1, sticky="w", padx=4)
        eh_row += 2
        
        # Log Errors Checkbox
        self.var_error_handler_log = tk.BooleanVar(value=True)
        self.chk_error_handler_log = tk.Checkbutton(
            self.error_handler_section_frame,
            text="Fehler loggen",
            variable=self.var_error_handler_log,
            bg="#fafafa"
        )
        self.chk_error_handler_log.grid(row=eh_row, column=0, columnspan=2, sticky="w", pady=5)
        eh_row += 1
        
        self.error_handler_section_frame.columnconfigure(1, weight=1)
        self.error_handler_section_frame.grid(row=element_row, column=0, columnspan=2, sticky="we", pady=(10, 0))
        self.error_handler_section_frame.grid_remove()
        element_row += 1
        
        # --- STATE-Section (⬤ Zustandsautomat) ---
        self.state_section_frame = tk.LabelFrame(
            self._element_section,
            text=" ⬤ Zustandsautomat ",
            bg="#fafafa",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=10
        )
        st_row = 0
        
        # State Name
        tk.Label(self.state_section_frame, text="State-Name:", bg="#fafafa", font=("Arial", 9, "bold")).grid(
            row=st_row, column=0, sticky="e", pady=2
        )
        self.var_state_name = tk.StringVar(value="")
        self.ent_state_name = tk.Entry(
            self.state_section_frame,
            textvariable=self.var_state_name,
            width=30
        )
        self.ent_state_name.grid(row=st_row, column=1, columnspan=2, sticky="w", padx=4, pady=2)
        st_row += 1
        
        # State Type
        tk.Label(self.state_section_frame, text="Type:", bg="#fafafa", font=("Arial", 9, "bold")).grid(
            row=st_row, column=0, sticky="e", pady=2
        )
        self.var_state_type = tk.StringVar(value="NORMAL")
        state_types = ["NORMAL", "INITIAL", "FINAL", "ERROR"]
        self.opt_state_type = tk.OptionMenu(
            self.state_section_frame,
            self.var_state_type,
            *state_types
        )
        self.opt_state_type.grid(row=st_row, column=1, sticky="w", padx=4, pady=2)
        st_row += 1
        
        # Entry Action
        tk.Label(self.state_section_frame, text="Entry Action:", bg="#fafafa").grid(
            row=st_row, column=0, sticky="e", pady=2
        )
        self.var_state_entry_action = tk.StringVar(value="")
        self.ent_state_entry_action = tk.Entry(
            self.state_section_frame,
            textvariable=self.var_state_entry_action,
            width=30
        )
        self.ent_state_entry_action.grid(row=st_row, column=1, columnspan=2, sticky="w", padx=4, pady=2)
        tk.Label(self.state_section_frame, text="(Element-ID oder Script)", bg="#fafafa", font=("Arial", 8)).grid(
            row=st_row, column=3, sticky="w", pady=2
        )
        st_row += 1
        
        # Exit Action
        tk.Label(self.state_section_frame, text="Exit Action:", bg="#fafafa").grid(
            row=st_row, column=0, sticky="e", pady=2
        )
        self.var_state_exit_action = tk.StringVar(value="")
        self.ent_state_exit_action = tk.Entry(
            self.state_section_frame,
            textvariable=self.var_state_exit_action,
            width=30
        )
        self.ent_state_exit_action.grid(row=st_row, column=1, columnspan=2, sticky="w", padx=4, pady=2)
        tk.Label(self.state_section_frame, text="(Element-ID oder Script)", bg="#fafafa", font=("Arial", 8)).grid(
            row=st_row, column=3, sticky="w", pady=2
        )
        st_row += 1
        
        # Transitions Label & Listbox
        tk.Label(self.state_section_frame, text="Transitions:", bg="#fafafa", font=("Arial", 9, "bold")).grid(
            row=st_row, column=0, sticky="ne", pady=2
        )
        
        # Listbox + Scrollbar
        trans_frame = tk.Frame(self.state_section_frame, bg="#fafafa")
        trans_frame.grid(row=st_row, column=1, columnspan=2, sticky="w", padx=4, pady=2)
        
        trans_scrollbar = tk.Scrollbar(trans_frame)
        trans_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.lst_state_transitions = tk.Listbox(
            trans_frame,
            height=4,
            width=35,
            yscrollcommand=trans_scrollbar.set
        )
        self.lst_state_transitions.pack(side=tk.LEFT, fill=tk.BOTH)
        trans_scrollbar.config(command=self.lst_state_transitions.yview)
        
        # Buttons: Add, Edit, Remove
        btn_frame = tk.Frame(self.state_section_frame, bg="#fafafa")
        btn_frame.grid(row=st_row, column=3, sticky="w", padx=4, pady=2)
        
        self.btn_add_transition = tk.Button(
            btn_frame,
            text="➕ Add",
            command=self._add_transition,
            width=8
        )
        self.btn_add_transition.pack(pady=2)
        
        self.btn_edit_transition = tk.Button(
            btn_frame,
            text="✏️ Edit",
            command=self._edit_transition,
            width=8
        )
        self.btn_edit_transition.pack(pady=2)
        
        self.btn_remove_transition = tk.Button(
            btn_frame,
            text="🗑️ Remove",
            command=self._remove_transition,
            width=8
        )
        self.btn_remove_transition.pack(pady=2)
        st_row += 1
        
        # Timeout
        tk.Label(self.state_section_frame, text="Timeout (s):", bg="#fafafa").grid(
            row=st_row, column=0, sticky="e", pady=2
        )
        self.var_state_timeout = tk.StringVar(value="0")
        self.ent_state_timeout = tk.Entry(
            self.state_section_frame,
            textvariable=self.var_state_timeout,
            width=10
        )
        self.ent_state_timeout.grid(row=st_row, column=1, sticky="w", padx=4, pady=2)
        tk.Label(self.state_section_frame, text="(0 = kein Timeout)", bg="#fafafa", font=("Arial", 8)).grid(
            row=st_row, column=2, sticky="w", pady=2
        )
        st_row += 1
        
        # Timeout Target
        tk.Label(self.state_section_frame, text="Timeout Target:", bg="#fafafa").grid(
            row=st_row, column=0, sticky="e", pady=2
        )
        self.var_state_timeout_target = tk.StringVar(value="")
        self.ent_state_timeout_target = tk.Entry(
            self.state_section_frame,
            textvariable=self.var_state_timeout_target,
            width=30
        )
        self.ent_state_timeout_target.grid(row=st_row, column=1, columnspan=2, sticky="w", padx=4, pady=2)
        tk.Label(self.state_section_frame, text="(Element-ID bei Timeout)", bg="#fafafa", font=("Arial", 8)).grid(
            row=st_row, column=3, sticky="w", pady=2
        )
        
        self.state_section_frame.grid_remove()
        element_row += 1
        
        # --- INTERLOCK-Section (🔒 Ressourcensperre) ---
        self.interlock_section_frame = tk.LabelFrame(
            self._element_section,
            text=" 🔒 Ressourcensperre ",
            bg="#fafafa",
            font=("Arial", 10, "bold"),
            padx=10,
            pady=10
        )
        il_row = 0
        
        # Interlock Type
        tk.Label(self.interlock_section_frame, text="Type:", bg="#fafafa", font=("Arial", 9, "bold")).grid(
            row=il_row, column=0, sticky="w", pady=5
        )
        self.var_interlock_type = tk.StringVar(value="MUTEX")
        self.opt_interlock_type = tk.OptionMenu(
            self.interlock_section_frame, self.var_interlock_type,
            "MUTEX", "SEMAPHORE"
        )
        self.opt_interlock_type.grid(row=il_row, column=1, sticky="we", pady=5)
        il_row += 1
        
        # Resource-ID
        tk.Label(self.interlock_section_frame, text="Ressourcen-ID:", bg="#fafafa", font=("Arial", 9, "bold")).grid(
            row=il_row, column=0, sticky="w", pady=5
        )
        self.var_interlock_resource_id = tk.StringVar()
        self.ent_interlock_resource_id = tk.Entry(
            self.interlock_section_frame, textvariable=self.var_interlock_resource_id, width=30
        )
        self.ent_interlock_resource_id.grid(row=il_row, column=1, sticky="we", pady=5)
        tk.Label(self.interlock_section_frame, text="(z.B. db_conn, api_rate_limit)", bg="#fafafa", fg="gray", font=("Arial", 8)).grid(
            row=il_row + 1, column=1, sticky="w"
        )
        il_row += 2
        
        # Max Count (nur für SEMAPHORE)
        tk.Label(self.interlock_section_frame, text="Max. Anzahl:", bg="#fafafa", font=("Arial", 9, "bold")).grid(
            row=il_row, column=0, sticky="w", pady=5
        )
        self.var_interlock_max_count = tk.StringVar(value="1")
        self.ent_interlock_max_count = tk.Entry(
            self.interlock_section_frame, textvariable=self.var_interlock_max_count, width=10
        )
        self.ent_interlock_max_count.grid(row=il_row, column=1, sticky="w", pady=5)
        tk.Label(self.interlock_section_frame, text="(MUTEX=1, SEMAPHORE>1)", bg="#fafafa", fg="gray", font=("Arial", 8)).grid(
            row=il_row + 1, column=1, sticky="w"
        )
        il_row += 2
        
        # Timeout
        tk.Label(self.interlock_section_frame, text="Timeout (Sek.):", bg="#fafafa", font=("Arial", 9, "bold")).grid(
            row=il_row, column=0, sticky="w", pady=5
        )
        self.var_interlock_timeout = tk.StringVar(value="0")
        self.ent_interlock_timeout = tk.Entry(
            self.interlock_section_frame, textvariable=self.var_interlock_timeout, width=10
        )
        self.ent_interlock_timeout.grid(row=il_row, column=1, sticky="w", pady=5)
        tk.Label(self.interlock_section_frame, text="(0 = unbegrenzt warten)", bg="#fafafa", fg="gray", font=("Arial", 8)).grid(
            row=il_row + 1, column=1, sticky="w"
        )
        il_row += 2
        
        # On Locked Target
        tk.Label(self.interlock_section_frame, text="Bei Sperre (Target):", bg="#fafafa", font=("Arial", 9, "bold")).grid(
            row=il_row, column=0, sticky="w", pady=5
        )
        self.var_interlock_on_locked = tk.StringVar()
        self.ent_interlock_on_locked = tk.Entry(
            self.interlock_section_frame, textvariable=self.var_interlock_on_locked, width=30
        )
        self.ent_interlock_on_locked.grid(row=il_row, column=1, sticky="we", pady=5)
        tk.Label(self.interlock_section_frame, text="(Element-ID bei Timeout/Lock)", bg="#fafafa", fg="gray", font=("Arial", 8)).grid(
            row=il_row + 1, column=1, sticky="w"
        )
        il_row += 2
        
        # Auto Release
        self.var_interlock_auto_release = tk.BooleanVar(value=True)
        self.chk_interlock_auto_release = tk.Checkbutton(
            self.interlock_section_frame,
            text="Automatisch freigeben nach Durchlauf",
            variable=self.var_interlock_auto_release,
            bg="#fafafa",
            font=("Arial", 9)
        )
        self.chk_interlock_auto_release.grid(row=il_row, column=0, columnspan=2, sticky="w", pady=5)
        il_row += 1
        
        self.interlock_section_frame.columnconfigure(1, weight=1)
        self.interlock_section_frame.grid(row=element_row, column=0, columnspan=2, sticky="we", pady=(10, 0))
        self.interlock_section_frame.grid_remove()
        element_row += 1
        
        # --- INFO/HELP-Panel (ℹ️ Element-Hilfe) ---
        self.info_panel_frame = tk.LabelFrame(
            self._element_section,
            text=" ℹ️ Element-Hilfe ",
            bg="#E8F5E9",  # Hellgrün
            font=("Arial", 10, "bold"),
            padx=10,
            pady=10
        )
        
        # Scrollbarer Text-Bereich für Info
        info_scroll_frame = tk.Frame(self.info_panel_frame, bg="#E8F5E9")
        info_scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        self.txt_element_info = tk.Text(
            info_scroll_frame,
            height=12,
            width=30,
            wrap=tk.WORD,
            bg="#F1F8E9",  # Noch helleres Grün
            fg="#2E7D32",  # Dunkelgrün
            font=("Arial", 9),
            padx=10,
            pady=10,
            state=tk.DISABLED
        )
        info_scrollbar = tk.Scrollbar(info_scroll_frame, orient=tk.VERTICAL, command=self.txt_element_info.yview)
        self.txt_element_info.config(yscrollcommand=info_scrollbar.set)
        self.txt_element_info.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.info_panel_frame.grid(row=element_row, column=0, columnspan=2, sticky="we", pady=(10, 0))
        self.info_panel_frame.grid_remove()
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
            self.opt_counter_type,
            self.spin_counter_start,
            self.spin_counter_max,
            self.chk_counter_reset,
            self.ent_counter_on_max,
            self.lst_condition_checks,
            self.btn_check_add,
            self.btn_check_edit,
            self.btn_check_remove,
            self.opt_condition_logic,
            self.ent_condition_true,
            self.ent_condition_false,
            self.opt_error_handler_type,
            self.ent_error_handler_retry_count,
            self.ent_error_handler_retry_delay,
            self.ent_error_handler_timeout,
            self.ent_error_handler_on_error,
            self.ent_error_handler_on_success,
            self.chk_error_handler_log,
            # STATE widgets
            self.ent_state_name,
            self.opt_state_type,
            self.ent_state_entry_action,
            self.ent_state_exit_action,
            self.lst_state_transitions,
            self.btn_trans_add,
            self.btn_trans_edit,
            self.btn_trans_remove,
            self.ent_state_timeout,
            self.ent_state_timeout_target,
            # INTERLOCK
            self.opt_interlock_type,
            self.ent_interlock_resource_id,
            self.ent_interlock_max_count,
            self.ent_interlock_timeout,
            self.ent_interlock_on_locked,
            self.chk_interlock_auto_release,
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

        # Container-Section (GROUP oder TIME_LOOP)
        if str(el.element_type).upper() in ("GROUP", "TIME_LOOP"):
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

        # Counter-Section (COUNTER)
        if str(el.element_type).upper() == "COUNTER":
            # Counter-Werte laden
            self.var_counter_type.set(getattr(el, "counter_type", "UP"))
            self.var_counter_start.set(int(getattr(el, "counter_start_value", 0)))
            self.var_counter_max.set(int(getattr(el, "counter_max_value", 100)))
            self.var_counter_current.set(int(getattr(el, "counter_current_value", 0)))
            self.var_counter_reset.set(bool(getattr(el, "counter_reset_on_max", False)))
            self.var_counter_on_max.set(getattr(el, "counter_on_max_reached", ""))
            
            # Section anzeigen
            self.counter_section_frame.grid()
            
            # Widgets aktivieren
            self.opt_counter_type.configure(state="normal")
            self.spin_counter_start.configure(state="normal")
            self.spin_counter_max.configure(state="normal")
            self.chk_counter_reset.configure(state="normal")
            self.ent_counter_on_max.configure(state="normal")
        else:
            # Counter-Section ausblenden
            self.counter_section_frame.grid_remove()
            
            # Widgets deaktivieren
            self.opt_counter_type.configure(state="disabled")
            self.spin_counter_start.configure(state="disabled")
            self.spin_counter_max.configure(state="disabled")
            self.chk_counter_reset.configure(state="disabled")
            self.ent_counter_on_max.configure(state="disabled")
        
        # Condition-Section (CONDITION)
        if str(el.element_type).upper() == "CONDITION":
            # Checks laden
            checks = list(getattr(el, "condition_checks", []) or [])
            self.lst_condition_checks.delete(0, tk.END)
            for check in checks:
                if isinstance(check, dict):
                    field = check.get("field", "")
                    operator = check.get("operator", "==")
                    value = check.get("value", "")
                    check_type = check.get("check_type", "string")
                    display = f"{field} {operator} {value} ({check_type})"
                    self.lst_condition_checks.insert(tk.END, display)
            
            # Logik und Targets laden
            self.var_condition_logic.set(getattr(el, "condition_logic", "AND"))
            self.var_condition_true.set(getattr(el, "condition_true_target", ""))
            self.var_condition_false.set(getattr(el, "condition_false_target", ""))
            
            # Section anzeigen
            self.condition_section_frame.grid()
            
            # Widgets aktivieren
            self.lst_condition_checks.configure(state="normal")
            self.btn_check_add.configure(state="normal")
            self.btn_check_edit.configure(state="normal")
            self.btn_check_remove.configure(state="normal")
            self.opt_condition_logic.configure(state="normal")
            self.ent_condition_true.configure(state="normal")
            self.ent_condition_false.configure(state="normal")
        else:
            # Condition-Section ausblenden
            self.condition_section_frame.grid_remove()
            
            # Widgets deaktivieren
            self.lst_condition_checks.configure(state="disabled")
            self.btn_check_add.configure(state="disabled")
            self.btn_check_edit.configure(state="disabled")
            self.btn_check_remove.configure(state="disabled")
            self.opt_condition_logic.configure(state="disabled")
            self.ent_condition_true.configure(state="disabled")
        
        # Error-Handler-Section (ERROR_HANDLER)
        if str(el.element_type).upper() == "ERROR_HANDLER":
            # Werte laden
            self.var_error_handler_type.set(getattr(el, "error_handler_type", "RETRY"))
            self.var_error_handler_retry_count.set(str(getattr(el, "error_handler_retry_count", 3)))
            self.var_error_handler_retry_delay.set(str(getattr(el, "error_handler_retry_delay", 60)))
            self.var_error_handler_timeout.set(str(getattr(el, "error_handler_timeout", 300)))
            self.var_error_handler_on_error.set(getattr(el, "error_handler_on_error_target", ""))
            self.var_error_handler_on_success.set(getattr(el, "error_handler_on_success_target", ""))
            self.var_error_handler_log.set(getattr(el, "error_handler_log_errors", True))
            
            # Section anzeigen
            self.error_handler_section_frame.grid()
            
            # Widgets aktivieren
            self.opt_error_handler_type.configure(state="normal")
            self.ent_error_handler_retry_count.configure(state="normal")
            self.ent_error_handler_retry_delay.configure(state="normal")
            self.ent_error_handler_timeout.configure(state="normal")
            self.ent_error_handler_on_error.configure(state="normal")
            self.ent_error_handler_on_success.configure(state="normal")
            self.chk_error_handler_log.configure(state="normal")
        else:
            # Error-Handler-Section ausblenden
            self.error_handler_section_frame.grid_remove()
            
            # Widgets deaktivieren
            self.opt_error_handler_type.configure(state="disabled")
            self.ent_error_handler_retry_count.configure(state="disabled")
            self.ent_error_handler_retry_delay.configure(state="disabled")
            self.ent_error_handler_timeout.configure(state="disabled")
            self.ent_error_handler_on_error.configure(state="disabled")
            self.ent_error_handler_on_success.configure(state="disabled")
            self.chk_error_handler_log.configure(state="disabled")
            self.ent_condition_false.configure(state="disabled")
        
        # State-Section (STATE)
        if str(el.element_type).upper() == "STATE":
            # Werte laden
            self.var_state_name.set(getattr(el, "state_name", ""))
            self.var_state_type.set(getattr(el, "state_type", "NORMAL"))
            self.var_state_entry_action.set(getattr(el, "state_entry_action", ""))
            self.var_state_exit_action.set(getattr(el, "state_exit_action", ""))
            self.var_state_timeout.set(str(getattr(el, "state_timeout", 0)))
            self.var_state_timeout_target.set(getattr(el, "state_timeout_target", ""))
            
            # Transitions laden
            self.lst_state_transitions.delete(0, tk.END)
            transitions = getattr(el, "state_transitions", [])
            for trans in transitions:
                event = trans.get("event", "")
                target = trans.get("target", "")
                condition = trans.get("condition", "")
                
                # Format: "event → target [condition]"
                display = f"{event} → {target}"
                if condition:
                    display += f" [{condition}]"
                
                self.lst_state_transitions.insert(tk.END, display)
            
            # Section anzeigen
            self.state_section_frame.grid()
            
            # Widgets aktivieren
            self.ent_state_name.configure(state="normal")
            self.opt_state_type.configure(state="normal")
            self.ent_state_entry_action.configure(state="normal")
            self.ent_state_exit_action.configure(state="normal")
            self.lst_state_transitions.configure(state="normal")
            self.btn_trans_add.configure(state="normal")
            self.btn_trans_edit.configure(state="normal")
            self.btn_trans_remove.configure(state="normal")
            self.ent_state_timeout.configure(state="normal")
            self.ent_state_timeout_target.configure(state="normal")
        else:
            # State-Section ausblenden
            self.state_section_frame.grid_remove()
            
            # Widgets deaktivieren
            self.ent_state_name.configure(state="disabled")
            self.opt_state_type.configure(state="disabled")
            self.ent_state_entry_action.configure(state="disabled")
            self.ent_state_exit_action.configure(state="disabled")
            self.lst_state_transitions.configure(state="disabled")
            self.btn_trans_add.configure(state="disabled")
            self.btn_trans_edit.configure(state="disabled")
            self.btn_trans_remove.configure(state="disabled")
            self.ent_state_timeout.configure(state="disabled")
            self.ent_state_timeout_target.configure(state="disabled")
        
        # Interlock-Section (INTERLOCK)
        if str(el.element_type).upper() == "INTERLOCK":
            # Werte laden
            self.var_interlock_type.set(getattr(el, "interlock_type", "MUTEX"))
            self.var_interlock_resource_id.set(getattr(el, "interlock_resource_id", ""))
            self.var_interlock_max_count.set(str(getattr(el, "interlock_max_count", 1)))
            self.var_interlock_timeout.set(str(getattr(el, "interlock_timeout", 0)))
            self.var_interlock_on_locked.set(getattr(el, "interlock_on_locked_target", ""))
            self.var_interlock_auto_release.set(getattr(el, "interlock_auto_release", True))
            
            # Section anzeigen
            self.interlock_section_frame.grid()
            
            # Widgets aktivieren
            self.opt_interlock_type.configure(state="normal")
            self.ent_interlock_resource_id.configure(state="normal")
            self.ent_interlock_max_count.configure(state="normal")
            self.ent_interlock_timeout.configure(state="normal")
            self.ent_interlock_on_locked.configure(state="normal")
            self.chk_interlock_auto_release.configure(state="normal")
        else:
            # Interlock-Section ausblenden
            self.interlock_section_frame.grid_remove()
            
            # Widgets deaktivieren
            self.opt_interlock_type.configure(state="disabled")
            self.ent_interlock_resource_id.configure(state="disabled")
            self.ent_interlock_max_count.configure(state="disabled")
            self.ent_interlock_timeout.configure(state="disabled")
            self.ent_interlock_on_locked.configure(state="disabled")
            self.chk_interlock_auto_release.configure(state="disabled")
        
        # Info/Help-Panel für alle Elemente
        self._update_info_panel(el.element_type)

    def _update_info_panel(self, element_type: str) -> None:
        """Update Info/Help panel with element-specific information."""
        try:
            from vpb.ui.element_info import format_element_help
            
            help_text = format_element_help(element_type)
            
            self.txt_element_info.configure(state="normal")
            self.txt_element_info.delete("1.0", tk.END)
            self.txt_element_info.insert("1.0", help_text)
            self.txt_element_info.configure(state="disabled")
            
            # Panel anzeigen
            self.info_panel_frame.grid()
        except Exception as e:
            # Bei Fehler Panel ausblenden
            self.info_panel_frame.grid_remove()
            print(f"Error updating info panel: {e}")
    
    def _add_condition_check(self) -> None:
        """Open dialog to add new condition check."""
        dialog = CheckEditorDialog(self, "Neuer Check")
        if dialog.result:
            field = dialog.result.get("field", "")
            operator = dialog.result.get("operator", "==")
            value = dialog.result.get("value", "")
            check_type = dialog.result.get("check_type", "string")
            display = f"{field} {operator} {value} ({check_type})"
            self.lst_condition_checks.insert(tk.END, display)
    
    def _edit_condition_check(self) -> None:
        """Open dialog to edit selected condition check."""
        selection = self.lst_condition_checks.curselection()
        if not selection:
            messagebox.showwarning("Keine Auswahl", "Bitte wählen Sie einen Check zum Bearbeiten aus.")
            return
        
        index = selection[0]
        current = self.lst_condition_checks.get(index)
        
        # Parse current check (simplified)
        # Format: "field operator value (type)"
        try:
            parts = current.rsplit(" (", 1)
            check_type = parts[1].rstrip(")") if len(parts) > 1 else "string"
            main_parts = parts[0].split(" ", 2)
            field = main_parts[0] if len(main_parts) > 0 else ""
            operator = main_parts[1] if len(main_parts) > 1 else "=="
            value = main_parts[2] if len(main_parts) > 2 else ""
        except:
            field, operator, value, check_type = "", "==", "", "string"
        
        dialog = CheckEditorDialog(
            self, 
            "Check bearbeiten",
            initial_data={
                "field": field,
                "operator": operator,
                "value": value,
                "check_type": check_type
            }
        )
        if dialog.result:
            field = dialog.result.get("field", "")
            operator = dialog.result.get("operator", "==")
            value = dialog.result.get("value", "")
            check_type = dialog.result.get("check_type", "string")
            display = f"{field} {operator} {value} ({check_type})"
            self.lst_condition_checks.delete(index)
            self.lst_condition_checks.insert(index, display)
    
    def _remove_condition_check(self) -> None:
        """Remove selected condition check."""
        selection = self.lst_condition_checks.curselection()
        if not selection:
            messagebox.showwarning("Keine Auswahl", "Bitte wählen Sie einen Check zum Entfernen aus.")
            return
        
        index = selection[0]
        self.lst_condition_checks.delete(index)
    
    def _add_transition(self) -> None:
        """Add new state transition."""
        dialog = TransitionEditorDialog(self, "Neue Transition")
        if dialog.result:
            event = dialog.result.get("event", "")
            target = dialog.result.get("target", "")
            condition = dialog.result.get("condition", "")
            
            # Format: "event → target [condition]"
            display = f"{event} → {target}"
            if condition:
                display += f" [{condition}]"
            
            self.lst_state_transitions.insert(tk.END, display)
    
    def _edit_transition(self) -> None:
        """Edit selected state transition."""
        selection = self.lst_state_transitions.curselection()
        if not selection:
            messagebox.showwarning("Keine Auswahl", "Bitte wählen Sie eine Transition zum Bearbeiten aus.")
            return
        
        index = selection[0]
        current = self.lst_state_transitions.get(index)
        
        # Parse current: "event → target [condition]"
        try:
            parts = current.split(" → ")
            event = parts[0] if len(parts) > 0 else ""
            rest = parts[1] if len(parts) > 1 else ""
            
            if " [" in rest:
                target, condition = rest.split(" [", 1)
                condition = condition.rstrip("]")
            else:
                target = rest
                condition = ""
        except:
            event, target, condition = "", "", ""
        
        dialog = TransitionEditorDialog(
            self, 
            "Transition bearbeiten",
            event=event,
            target=target,
            condition=condition
        )
        
        if dialog.result:
            event = dialog.result.get("event", "")
            target = dialog.result.get("target", "")
            condition = dialog.result.get("condition", "")
            
            # Format: "event → target [condition]"
            display = f"{event} → {target}"
            if condition:
                display += f" [{condition}]"
            
            self.lst_state_transitions.delete(index)
            self.lst_state_transitions.insert(index, display)
    
    def _remove_transition(self) -> None:
        """Remove selected state transition."""
        selection = self.lst_state_transitions.curselection()
        if not selection:
            messagebox.showwarning("Keine Auswahl", "Bitte wählen Sie eine Transition zum Entfernen aus.")
            return
        
        index = selection[0]
        self.lst_state_transitions.delete(index)

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

        # Container-Properties (GROUP oder TIME_LOOP)
        if str(self._current_element.element_type).upper() in ("GROUP", "TIME_LOOP"):
            values["collapsed"] = bool(self.var_collapsed.get())

        # Counter-Properties (COUNTER)
        if str(self._current_element.element_type).upper() == "COUNTER":
            try:
                values["counter_type"] = self.var_counter_type.get()
                values["counter_start_value"] = int(self.var_counter_start.get())
                values["counter_max_value"] = int(self.var_counter_max.get())
                values["counter_current_value"] = int(self.var_counter_current.get())
                values["counter_reset_on_max"] = bool(self.var_counter_reset.get())
                values["counter_on_max_reached"] = self.var_counter_on_max.get().strip()
            except ValueError as e:
                # Zeige Fehler wenn Werte ungültig
                messagebox.showerror("Ungültige Eingabe", f"Bitte prüfen Sie die Counter-Werte: {e}")
                return
        
        # Condition-Properties (CONDITION)
        if str(self._current_element.element_type).upper() == "CONDITION":
            # Parse Checks from Listbox
            checks = []
            for i in range(self.lst_condition_checks.size()):
                check_str = self.lst_condition_checks.get(i)
                # Format: "field operator value (type)"
                try:
                    parts = check_str.rsplit(" (", 1)
                    check_type = parts[1].rstrip(")") if len(parts) > 1 else "string"
                    main_parts = parts[0].split(" ", 2)
                    field = main_parts[0] if len(main_parts) > 0 else ""
                    operator = main_parts[1] if len(main_parts) > 1 else "=="
                    value = main_parts[2] if len(main_parts) > 2 else ""
                    
                    checks.append({
                        "field": field,
                        "operator": operator,
                        "value": value,
                        "check_type": check_type
                    })
                except Exception as e:
                    messagebox.showerror("Fehler", f"Fehler beim Parsen von Check '{check_str}': {e}")
                    return
            
            values["condition_checks"] = checks
            values["condition_logic"] = self.var_condition_logic.get()
            values["condition_true_target"] = self.var_condition_true.get().strip()
            values["condition_false_target"] = self.var_condition_false.get().strip()
        
        # Error-Handler-Properties (ERROR_HANDLER)
        if str(self._current_element.element_type).upper() == "ERROR_HANDLER":
            try:
                values["error_handler_type"] = self.var_error_handler_type.get()
                values["error_handler_retry_count"] = int(self.var_error_handler_retry_count.get() or 0)
                values["error_handler_retry_delay"] = int(self.var_error_handler_retry_delay.get() or 0)
                values["error_handler_timeout"] = int(self.var_error_handler_timeout.get() or 0)
                values["error_handler_on_error_target"] = self.var_error_handler_on_error.get().strip()
                values["error_handler_on_success_target"] = self.var_error_handler_on_success.get().strip()
                values["error_handler_log_errors"] = self.var_error_handler_log.get()
            except ValueError as e:
                messagebox.showerror("Fehler", f"Ungültiger Zahlenwert: {e}")
                return
        
        # State-Properties (STATE)
        if str(self._current_element.element_type).upper() == "STATE":
            # Parse Transitions from Listbox
            transitions = []
            for i in range(self.lst_state_transitions.size()):
                trans_str = self.lst_state_transitions.get(i)
                # Format: "event → target [condition]"
                try:
                    # Split "event → target [condition]"
                    if " → " in trans_str:
                        parts = trans_str.split(" → ", 1)
                        event = parts[0].strip()
                        rest = parts[1].strip()
                        
                        # Check for condition in brackets
                        if " [" in rest:
                            target, condition = rest.split(" [", 1)
                            target = target.strip()
                            condition = condition.rstrip("]").strip()
                        else:
                            target = rest
                            condition = ""
                        
                        transitions.append({
                            "event": event,
                            "target": target,
                            "condition": condition
                        })
                except Exception as e:
                    messagebox.showerror("Fehler", f"Fehler beim Parsen von Transition '{trans_str}': {e}")
                    return
            
            try:
                values["state_name"] = self.var_state_name.get().strip()
                values["state_type"] = self.var_state_type.get()
                values["state_entry_action"] = self.var_state_entry_action.get().strip()
                values["state_exit_action"] = self.var_state_exit_action.get().strip()
                values["state_transitions"] = transitions
                values["state_timeout"] = int(self.var_state_timeout.get() or 0)
                values["state_timeout_target"] = self.var_state_timeout_target.get().strip()
            except ValueError as e:
                messagebox.showerror("Fehler", f"Ungültiger Zahlenwert: {e}")
                return
        
        # Interlock-Properties (INTERLOCK)
        if str(self._current_element.element_type).upper() == "INTERLOCK":
            try:
                values["interlock_type"] = self.var_interlock_type.get()
                values["interlock_resource_id"] = self.var_interlock_resource_id.get().strip()
                values["interlock_max_count"] = int(self.var_interlock_max_count.get() or 1)
                values["interlock_timeout"] = int(self.var_interlock_timeout.get() or 0)
                values["interlock_on_locked_target"] = self.var_interlock_on_locked.get().strip()
                values["interlock_auto_release"] = self.var_interlock_auto_release.get()
            except ValueError as e:
                messagebox.showerror("Fehler", f"Ungültiger Zahlenwert: {e}")
                return

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
            if not self._current_element or str(self._current_element.element_type).upper() not in ("GROUP", "TIME_LOOP"):
                return
            if callable(self._on_group_add):
                self._on_group_add(self._current_element.element_id)
        except Exception:
            pass

    def _on_group_remove_from_selection(self):
        try:
            if not self._current_element or str(self._current_element.element_type).upper() not in ("GROUP", "TIME_LOOP"):
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


class CheckEditorDialog(tk.Toplevel):
    """Dialog zum Bearbeiten eines Condition-Checks."""
    
    def __init__(self, parent, title="Check Editor", initial_data=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("450x300")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.result = None
        
        # Zentral positionieren
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (450 // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (300 // 2)
        self.geometry(f"+{x}+{y}")
        
        # Frame für Formular
        form = tk.Frame(self, padx=20, pady=20)
        form.pack(fill=tk.BOTH, expand=True)
        
        row = 0
        
        # Field
        tk.Label(form, text="Feld:", font=("Arial", 9, "bold")).grid(row=row, column=0, sticky="w", pady=5)
        tk.Label(form, text="(z.B. 'status', 'betrag', 'priority')", font=("Arial", 8), fg="#888").grid(
            row=row, column=1, sticky="w", pady=5
        )
        row += 1
        
        self.var_field = tk.StringVar(value=initial_data.get("field", "") if initial_data else "")
        ent_field = tk.Entry(form, textvariable=self.var_field, width=40)
        ent_field.grid(row=row, column=0, columnspan=2, sticky="we", pady=5)
        ent_field.focus()
        row += 1
        
        # Operator
        tk.Label(form, text="Operator:", font=("Arial", 9, "bold")).grid(row=row, column=0, sticky="w", pady=5)
        row += 1
        
        self.var_operator = tk.StringVar(value=initial_data.get("operator", "==") if initial_data else "==")
        operators = ["==", "!=", "<", ">", "<=", ">=", "contains", "regex"]
        opt_operator = tk.OptionMenu(form, self.var_operator, *operators)
        opt_operator.config(width=15)
        opt_operator.grid(row=row, column=0, sticky="w", pady=5)
        row += 1
        
        # Value
        tk.Label(form, text="Wert:", font=("Arial", 9, "bold")).grid(row=row, column=0, sticky="w", pady=5)
        tk.Label(form, text="(Vergleichswert, z.B. '5000', 'approved')", font=("Arial", 8), fg="#888").grid(
            row=row, column=1, sticky="w", pady=5
        )
        row += 1
        
        self.var_value = tk.StringVar(value=initial_data.get("value", "") if initial_data else "")
        ent_value = tk.Entry(form, textvariable=self.var_value, width=40)
        ent_value.grid(row=row, column=0, columnspan=2, sticky="we", pady=5)
        row += 1
        
        # Check Type
        tk.Label(form, text="Datentyp:", font=("Arial", 9, "bold")).grid(row=row, column=0, sticky="w", pady=5)
        row += 1
        
        self.var_check_type = tk.StringVar(value=initial_data.get("check_type", "string") if initial_data else "string")
        check_types = ["string", "number", "date", "boolean"]
        opt_check_type = tk.OptionMenu(form, self.var_check_type, *check_types)
        opt_check_type.config(width=15)
        opt_check_type.grid(row=row, column=0, sticky="w", pady=5)
        row += 1
        
        # Buttons
        btn_frame = tk.Frame(form)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=(20, 0))
        
        tk.Button(btn_frame, text="✓ OK", width=12, command=self._ok).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="✗ Abbrechen", width=12, command=self._cancel).pack(side=tk.LEFT, padx=5)
        
        # Enter/Escape shortcuts
        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self._cancel())
        
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)
        
        self.wait_window()
    
    def _ok(self):
        field = self.var_field.get().strip()
        if not field:
            messagebox.showwarning("Feld erforderlich", "Bitte geben Sie einen Feldnamen ein.", parent=self)
            return
        
        value = self.var_value.get().strip()
        if not value:
            messagebox.showwarning("Wert erforderlich", "Bitte geben Sie einen Vergleichswert ein.", parent=self)
            return
        
        self.result = {
            "field": field,
            "operator": self.var_operator.get(),
            "value": value,
            "check_type": self.var_check_type.get()
        }
        self.destroy()
    
    def _cancel(self):
        self.result = None
        self.destroy()


class TransitionEditorDialog(tk.Toplevel):
    """Dialog zum Bearbeiten einer STATE-Transition."""
    
    def __init__(self, parent, title="Transition Editor", event="", target="", condition=""):
        super().__init__(parent)
        self.title(title)
        self.geometry("450x250")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.result = None
        
        # Zentral positionieren
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (450 // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (250 // 2)
        self.geometry(f"+{x}+{y}")
        
        # Frame für Formular
        form = tk.Frame(self, padx=20, pady=20)
        form.pack(fill=tk.BOTH, expand=True)
        
        row = 0
        
        # Event
        tk.Label(form, text="Event:", font=("Arial", 9, "bold")).grid(row=row, column=0, sticky="w", pady=5)
        self.var_event = tk.StringVar(value=event)
        tk.Entry(form, textvariable=self.var_event, width=40).grid(row=row, column=1, sticky="ew", pady=5)
        tk.Label(form, text="(z.B. submit, approve, reject)", font=("Arial", 8), fg="gray").grid(
            row=row+1, column=1, sticky="w"
        )
        row += 2
        
        # Target
        tk.Label(form, text="Ziel-State:", font=("Arial", 9, "bold")).grid(row=row, column=0, sticky="w", pady=5)
        self.var_target = tk.StringVar(value=target)
        tk.Entry(form, textvariable=self.var_target, width=40).grid(row=row, column=1, sticky="ew", pady=5)
        tk.Label(form, text="(Element-ID des Ziel-States)", font=("Arial", 8), fg="gray").grid(
            row=row+1, column=1, sticky="w"
        )
        row += 2
        
        # Condition (optional)
        tk.Label(form, text="Bedingung:", font=("Arial", 9, "bold")).grid(row=row, column=0, sticky="w", pady=5)
        self.var_condition = tk.StringVar(value=condition)
        tk.Entry(form, textvariable=self.var_condition, width=40).grid(row=row, column=1, sticky="ew", pady=5)
        tk.Label(form, text="(optional: Expression, z.B. valid==true)", font=("Arial", 8), fg="gray").grid(
            row=row+1, column=1, sticky="w"
        )
        row += 2
        
        form.columnconfigure(1, weight=1)
        
        # Buttons
        btn_frame = tk.Frame(self, pady=10)
        btn_frame.pack(fill=tk.X)
        
        tk.Button(btn_frame, text="OK", command=self._ok, width=10).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="Abbrechen", command=self._cancel, width=10).pack(side=tk.RIGHT)
        
        # Enter-Taste für OK
        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self._cancel())
        
        self.wait_window()
    
    def _ok(self):
        event = self.var_event.get().strip()
        if not event:
            messagebox.showwarning("Event erforderlich", "Bitte geben Sie einen Event-Namen ein.", parent=self)
            return
        
        target = self.var_target.get().strip()
        if not target:
            messagebox.showwarning("Ziel erforderlich", "Bitte geben Sie ein Ziel-State an.", parent=self)
            return
        
        self.result = {
            "event": event,
            "target": target,
            "condition": self.var_condition.get().strip()
        }
        self.destroy()
    
    def _cancel(self):
        self.result = None
        self.destroy()


