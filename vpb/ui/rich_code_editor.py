"""
Rich Code Editor Widget mit Syntax-Highlighting für JSON und XML.
"""

import tkinter as tk
from tkinter import font as tkfont
import re
from typing import Optional


class RichCodeEditor(tk.Frame):
    """Code-Editor mit Syntax-Highlighting, Zeilennummern und Toolbar."""
    
    def __init__(self, parent, language="json", on_refresh=None, on_apply=None, **kwargs):
        """
        Initialisiert den Code-Editor.
        
        Args:
            parent: Parent Widget
            language: "json" oder "xml"
            on_refresh: Callback für Refresh-Button (lädt Daten vom Canvas)
            on_apply: Callback für Apply-Button (schreibt Daten zum Canvas)
            **kwargs: Zusätzliche Frame-Optionen
        """
        super().__init__(parent, **kwargs)
        
        self.language = language.lower()
        self._read_only = True  # Start als Read-Only
        self.on_refresh = on_refresh
        self.on_apply = on_apply
        
        # Fonts
        try:
            self.code_font = tkfont.Font(family="Consolas", size=10)
            self.line_font = tkfont.Font(family="Consolas", size=9)
        except:
            self.code_font = tkfont.Font(family="Courier", size=10)
            self.line_font = tkfont.Font(family="Courier", size=9)
        
        # Colors (VS Code Dark+ Theme)
        self.colors = {
            'bg': '#1e1e1e',
            'fg': '#d4d4d4',
            'line_bg': '#252526',
            'line_fg': '#858585',
            'selection': '#264f78',
            'keyword': '#569cd6',    # Blau
            'string': '#ce9178',     # Orange
            'number': '#b5cea8',     # Hellgrün
            'comment': '#6a9955',    # Grün
            'tag': '#4ec9b0',        # Cyan
            'attribute': '#9cdcfe',  # Hellblau
            'bracket': '#ffd700',    # Gold
        }
        
        # Toolbar
        self._create_toolbar()
        
        # Editor Container
        editor_container = tk.Frame(self, bg=self.colors['bg'])
        editor_container.pack(fill=tk.BOTH, expand=True)
        
        # Line Numbers
        self.line_numbers = tk.Text(
            editor_container,
            width=4,
            padx=8,
            pady=5,
            takefocus=0,
            border=0,
            background=self.colors['line_bg'],
            foreground=self.colors['line_fg'],
            state='disabled',
            font=self.line_font,
            cursor='arrow'
        )
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # Scrollbars
        y_scroll = tk.Scrollbar(editor_container, orient=tk.VERTICAL)
        y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        x_scroll_frame = tk.Frame(self, bg=self.colors['bg'])
        x_scroll_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Spacer für Line Numbers
        tk.Frame(x_scroll_frame, width=60, bg=self.colors['line_bg']).pack(side=tk.LEFT)
        
        x_scroll = tk.Scrollbar(x_scroll_frame, orient=tk.HORIZONTAL)
        x_scroll.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Code Text Widget
        self.text = tk.Text(
            editor_container,
            wrap=tk.NONE,
            undo=True,
            maxundo=-1,
            font=self.code_font,
            background=self.colors['bg'],
            foreground=self.colors['fg'],
            insertbackground='white',
            selectbackground=self.colors['selection'],
            selectforeground=self.colors['fg'],
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set,
            padx=5,
            pady=5,
            border=0,
            state='disabled'  # Start als Read-Only
        )
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        y_scroll.config(command=self._on_y_scroll)
        x_scroll.config(command=self.text.xview)
        
        # Tags für Syntax-Highlighting
        self._create_tags()
        
        # Event Bindings
        self.text.bind('<KeyRelease>', self._on_key_release)
        self.text.bind('<<Modified>>', self._on_modified)
        self.text.bind('<Button-1>', self._update_line_numbers)
        
        # Initial line numbers
        self._update_line_numbers()
    
    def _create_toolbar(self):
        """Erstellt die Toolbar."""
        toolbar = tk.Frame(self, bg='#2d2d30', height=30)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Language Label
        lang_label = tk.Label(
            toolbar,
            text=f"📝 {self.language.upper()}",
            bg='#2d2d30',
            fg='#cccccc',
            font=('Segoe UI', 9, 'bold'),
            padx=10
        )
        lang_label.pack(side=tk.LEFT, pady=3)
        
        # Buttons
        btn_frame = tk.Frame(toolbar, bg='#2d2d30')
        btn_frame.pack(side=tk.RIGHT, padx=5)
        
        # Refresh Button (Canvas → Code)
        refresh_btn = tk.Button(
            btn_frame,
            text="🔄 Refresh",
            command=self._on_refresh_click,
            bg='#1e6f1e',
            fg='white',
            relief=tk.FLAT,
            padx=10,
            pady=2,
            cursor='hand2'
        )
        refresh_btn.pack(side=tk.LEFT, padx=2)
        
        # Apply Button (Code → Canvas)
        self.apply_btn = tk.Button(
            btn_frame,
            text="✓ Apply",
            command=self._on_apply_click,
            bg='#c64600',
            fg='white',
            relief=tk.FLAT,
            padx=10,
            pady=2,
            cursor='hand2',
            state='disabled'  # Nur im Edit-Mode
        )
        self.apply_btn.pack(side=tk.LEFT, padx=2)
        
        # Format Button
        self.format_btn = tk.Button(
            btn_frame,
            text="⚡ Format",
            command=self._format_code,
            bg='#0e639c',
            fg='white',
            relief=tk.FLAT,
            padx=10,
            pady=2,
            cursor='hand2'
        )
        self.format_btn.pack(side=tk.LEFT, padx=2)
        
        # Copy Button
        copy_btn = tk.Button(
            btn_frame,
            text="📋 Copy",
            command=self._copy_all,
            bg='#3c3c3c',
            fg='white',
            relief=tk.FLAT,
            padx=10,
            pady=2,
            cursor='hand2'
        )
        copy_btn.pack(side=tk.LEFT, padx=2)
        
        # Toggle Read-Only
        self.readonly_btn = tk.Button(
            btn_frame,
            text="🔒 Read",
            command=self._toggle_readonly,
            bg='#5a1e1e',
            fg='white',
            relief=tk.FLAT,
            padx=10,
            pady=2,
            cursor='hand2'
        )
        self.readonly_btn.pack(side=tk.LEFT, padx=2)
    
    def _create_tags(self):
        """Erstellt Tags für Syntax-Highlighting."""
        self.text.tag_configure('keyword', foreground=self.colors['keyword'])
        self.text.tag_configure('string', foreground=self.colors['string'])
        self.text.tag_configure('number', foreground=self.colors['number'])
        self.text.tag_configure('comment', foreground=self.colors['comment'])
        self.text.tag_configure('tag', foreground=self.colors['tag'])
        self.text.tag_configure('attribute', foreground=self.colors['attribute'])
        self.text.tag_configure('bracket', foreground=self.colors['bracket'])
    
    def _on_y_scroll(self, *args):
        """Synchronisiert Scrolling zwischen Text und Line Numbers."""
        self.text.yview(*args)
        self.line_numbers.yview(*args)
    
    def _on_key_release(self, event=None):
        """Handler für Tastatur-Events."""
        self._update_line_numbers()
    
    def _on_modified(self, event=None):
        """Handler für Text-Änderungen."""
        if self.text.edit_modified():
            # Reset modified flag
            self.text.edit_modified(False)
            # Trigger syntax highlighting nach kurzer Verzögerung
            if hasattr(self, '_highlight_job'):
                self.after_cancel(self._highlight_job)
            self._highlight_job = self.after(300, self._apply_syntax_highlighting)
    
    def _update_line_numbers(self, event=None):
        """Aktualisiert Zeilennummern."""
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', tk.END)
        
        # Zeilennummern generieren
        try:
            line_count = int(self.text.index('end-1c').split('.')[0])
            line_numbers_text = "\n".join(str(i) for i in range(1, line_count + 1))
            self.line_numbers.insert('1.0', line_numbers_text)
        except:
            pass
        
        self.line_numbers.config(state='disabled')
    
    def _apply_syntax_highlighting(self):
        """Wendet Syntax-Highlighting an."""
        # Entferne alte Tags
        for tag in ['keyword', 'string', 'number', 'comment', 'tag', 'attribute', 'bracket']:
            self.text.tag_remove(tag, '1.0', tk.END)
        
        content = self.text.get('1.0', tk.END)
        
        if self.language == 'json':
            self._highlight_json(content)
        elif self.language == 'xml':
            self._highlight_xml(content)
    
    def _highlight_json(self, content):
        """Syntax-Highlighting für JSON."""
        # Keywords (true, false, null)
        for match in re.finditer(r'\b(true|false|null)\b', content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text.tag_add('keyword', start, end)
        
        # Strings
        for match in re.finditer(r'"([^"\\]|\\.)*"', content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text.tag_add('string', start, end)
        
        # Numbers
        for match in re.finditer(r'\b-?\d+\.?\d*([eE][+-]?\d+)?\b', content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text.tag_add('number', start, end)
        
        # Brackets
        for match in re.finditer(r'[{}[\],:]', content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text.tag_add('bracket', start, end)
    
    def _highlight_xml(self, content):
        """Syntax-Highlighting für XML."""
        # Comments
        for match in re.finditer(r'<!--.*?-->', content, re.DOTALL):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text.tag_add('comment', start, end)
        
        # Tags
        for match in re.finditer(r'</?(\w+)', content):
            start = f"1.0+{match.start(1)}c"
            end = f"1.0+{match.end(1)}c"
            self.text.tag_add('tag', start, end)
        
        # Attributes
        for match in re.finditer(r'(\w+)=', content):
            start = f"1.0+{match.start(1)}c"
            end = f"1.0+{match.end(1)}c"
            self.text.tag_add('attribute', start, end)
        
        # Strings
        for match in re.finditer(r'"([^"\\]|\\.)*"', content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text.tag_add('string', start, end)
        
        # Brackets
        for match in re.finditer(r'[<>/]', content):
            start = f"1.0+{match.start()}c"
            end = f"1.0+{match.end()}c"
            self.text.tag_add('bracket', start, end)
    
    def _format_code(self):
        """Formatiert den Code (pretty-print)."""
        if self._read_only:
            return
        
        content = self.get_text()
        
        try:
            if self.language == 'json':
                import json
                parsed = json.loads(content)
                formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
                self.set_text(formatted)
            elif self.language == 'xml':
                import xml.dom.minidom as minidom
                dom = minidom.parseString(content)
                formatted = dom.toprettyxml(indent="  ")
                # Remove extra blank lines
                formatted = '\n'.join([line for line in formatted.split('\n') if line.strip()])
                self.set_text(formatted)
        except Exception as e:
            print(f"❌ Format error: {e}")
    
    def _on_refresh_click(self):
        """Handler für Refresh-Button."""
        if self.on_refresh:
            self.on_refresh()
    
    def _on_apply_click(self):
        """Handler für Apply-Button."""
        if self.on_apply:
            self.on_apply()
    
    def _copy_all(self):
        """Kopiert gesamten Code in Zwischenablage."""
        try:
            self.clipboard_clear()
            self.clipboard_append(self.get_text())
        except:
            pass
    
    def _toggle_readonly(self):
        """Schaltet zwischen Read-Only und Edit-Mode um."""
        self._read_only = not self._read_only
        
        if self._read_only:
            self.text.config(state='disabled', background='#252526')
            self.readonly_btn.config(text="🔒 Read", bg='#5a1e1e')
            self.format_btn.config(state='disabled')
            self.apply_btn.config(state='disabled')
        else:
            self.text.config(state='normal', background=self.colors['bg'])
            self.readonly_btn.config(text="🔓 Edit", bg='#1e6f1e')
            self.format_btn.config(state='normal')
            self.apply_btn.config(state='normal')
    
    # Public API
    
    def set_text(self, text: str):
        """Setzt den Text im Editor."""
        was_readonly = self._read_only
        if was_readonly:
            self.text.config(state='normal')
        
        self.text.delete('1.0', tk.END)
        self.text.insert('1.0', text)
        
        if was_readonly:
            self.text.config(state='disabled')
        
        self._update_line_numbers()
        self._apply_syntax_highlighting()
    
    def get_text(self) -> str:
        """Gibt den Text aus dem Editor zurück."""
        return self.text.get('1.0', 'end-1c')
    
    def set_readonly(self, readonly: bool):
        """Setzt Read-Only Mode."""
        if readonly != self._read_only:
            self._toggle_readonly()
    
    def clear(self):
        """Löscht den Editor-Inhalt."""
        self.set_text("")
