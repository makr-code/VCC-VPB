"""
AI Wizards Dialogs
===================

Dialoge für AI-Features:
- AI Process Generation Wizard
- AI Ingestion Wizard (Text/Dokumente zu VPB)

Event-driven mit MessageBus Integration.

Autor: VPB Development Team
Datum: 14. Oktober 2025
Version: 0.2.0-alpha
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
from typing import Optional, Callable, Dict, Any
from pathlib import Path


class AIProcessGenerationDialog:
    """
    Dialog für AI-gestützte Prozess-Generierung.
    
    Ermöglicht Eingabe von Beschreibungstext und generiert
    daraus einen VPB-Prozess mittels AI.
    """
    
    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        on_generate: Optional[Callable[[str, Dict[str, Any]], None]] = None
    ):
        """
        Initialisiert Dialog.
        
        Args:
            parent: Parent Window
            on_generate: Callback (prompt: str, settings: dict) → None
        """
        self.parent = parent
        self.on_generate = on_generate
        
        # Dialog Window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("AI-Prozess-Generierung")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Result
        self.result: Optional[Dict[str, Any]] = None
        
        self._create_widgets()
        self._center_dialog()
    
    def _create_widgets(self):
        """Erstellt Dialog-Widgets."""
        # Header
        header_frame = ttk.Frame(self.dialog, padding=10)
        header_frame.pack(fill=tk.X)
        
        ttk.Label(
            header_frame,
            text="Beschreiben Sie den gewünschten Prozess",
            font=("Arial", 12, "bold")
        ).pack()
        
        ttk.Label(
            header_frame,
            text="Die AI generiert daraus einen VPB-Prozess"
        ).pack()
        
        # Input Frame
        input_frame = ttk.LabelFrame(self.dialog, text="Prozessbeschreibung", padding=10)
        input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Text Input
        self.text_input = scrolledtext.ScrolledText(
            input_frame,
            height=10,
            wrap=tk.WORD
        )
        self.text_input.pack(fill=tk.BOTH, expand=True)
        self.text_input.insert(
            "1.0",
            "Beispiel:\nBaugenehmigungsverfahren für Einfamilienhäuser\n\n"
            "1. Antragstellung beim Bauamt\n"
            "2. Prüfung der Vollständigkeit\n"
            "3. Technische Prüfung\n"
            "4. Genehmigung oder Ablehnung\n"
            "5. Bescheiderteilung"
        )
        
        # Settings Frame
        settings_frame = ttk.LabelFrame(self.dialog, text="Einstellungen", padding=10)
        settings_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # AI Model
        ttk.Label(settings_frame, text="AI-Modell:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.model_var = tk.StringVar(value="llama3.2:latest")
        model_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.model_var,
            values=["llama3.2:latest", "mistral:latest", "phi3:latest"],
            state="readonly",
            width=30
        )
        model_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Temperature
        ttk.Label(settings_frame, text="Temperature:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.temperature_var = tk.DoubleVar(value=0.7)
        temperature_scale = ttk.Scale(
            settings_frame,
            from_=0.0,
            to=1.0,
            variable=self.temperature_var,
            orient=tk.HORIZONTAL,
            length=200
        )
        temperature_scale.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        temp_label = ttk.Label(settings_frame, textvariable=self.temperature_var)
        temp_label.grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog, padding=10)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(
            button_frame,
            text="Generieren",
            command=self._on_generate,
            default=tk.ACTIVE
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Abbrechen",
            command=self._on_cancel
        ).pack(side=tk.RIGHT, padx=5)
        
        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self._on_generate())
        self.dialog.bind('<Escape>', lambda e: self._on_cancel())
    
    def _center_dialog(self):
        """Zentriert Dialog über Parent."""
        self.dialog.update_idletasks()
        
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        
        self.dialog.geometry(f"+{x}+{y}")
    
    def _on_generate(self):
        """Handle Generate-Button."""
        prompt = self.text_input.get("1.0", tk.END).strip()
        
        if not prompt:
            tk.messagebox.showwarning(
                "Keine Eingabe",
                "Bitte beschreiben Sie den gewünschten Prozess."
            )
            return
        
        settings = {
            "model": self.model_var.get(),
            "temperature": self.temperature_var.get()
        }
        
        self.result = {
            "prompt": prompt,
            "settings": settings
        }
        
        # Callback ausführen
        if self.on_generate:
            self.on_generate(prompt, settings)
        
        self.dialog.destroy()
    
    def _on_cancel(self):
        """Handle Cancel-Button."""
        self.result = None
        self.dialog.destroy()
    
    def show(self) -> Optional[Dict[str, Any]]:
        """
        Zeigt Dialog modal an.
        
        Returns:
            {'prompt': str, 'settings': dict} oder None wenn abgebrochen
        """
        self.dialog.wait_window()
        return self.result


class AIIngestionWizard:
    """
    Wizard für AI-gestützte Prozess-Extraktion.
    
    Extrahiert VPB-Prozesse aus:
    - Text-Dokumenten (PDF, Word, TXT)
    - Bilder/Screenshots (OCR)
    - Strukturierten Daten (XML, JSON)
    """
    
    def __init__(
        self,
        parent: tk.Tk | tk.Toplevel,
        on_ingest: Optional[Callable[[Path, Dict[str, Any]], None]] = None
    ):
        """
        Initialisiert Wizard.
        
        Args:
            parent: Parent Window
            on_ingest: Callback (file_path: Path, settings: dict) → None
        """
        self.parent = parent
        self.on_ingest = on_ingest
        
        # Dialog Window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("AI-Prozess-Extraktion")
        self.dialog.geometry("700x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # State
        self.selected_file: Optional[Path] = None
        self.result: Optional[Dict[str, Any]] = None
        
        self._create_widgets()
        self._center_dialog()
    
    def _create_widgets(self):
        """Erstellt Dialog-Widgets."""
        # Header
        header_frame = ttk.Frame(self.dialog, padding=10)
        header_frame.pack(fill=tk.X)
        
        ttk.Label(
            header_frame,
            text="Prozess aus Dokumenten extrahieren",
            font=("Arial", 12, "bold")
        ).pack()
        
        ttk.Label(
            header_frame,
            text="Wählen Sie eine Datei mit Prozessbeschreibungen"
        ).pack()
        
        # File Selection
        file_frame = ttk.LabelFrame(self.dialog, text="Datei-Auswahl", padding=10)
        file_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.file_path_var = tk.StringVar(value="Keine Datei ausgewählt")
        
        ttk.Label(file_frame, textvariable=self.file_path_var, wraplength=600).pack(fill=tk.X, pady=5)
        
        ttk.Button(
            file_frame,
            text="Datei auswählen...",
            command=self._select_file
        ).pack()
        
        # Source Type
        type_frame = ttk.LabelFrame(self.dialog, text="Quell-Typ", padding=10)
        type_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.source_type_var = tk.StringVar(value="text")
        
        ttk.Radiobutton(
            type_frame,
            text="Text-Dokument (PDF, DOCX, TXT)",
            variable=self.source_type_var,
            value="text"
        ).pack(anchor=tk.W)
        
        ttk.Radiobutton(
            type_frame,
            text="Bild/Screenshot (PNG, JPG) - mit OCR",
            variable=self.source_type_var,
            value="image"
        ).pack(anchor=tk.W)
        
        ttk.Radiobutton(
            type_frame,
            text="Strukturierte Daten (XML, JSON)",
            variable=self.source_type_var,
            value="structured"
        ).pack(anchor=tk.W)
        
        # Settings Frame
        settings_frame = ttk.LabelFrame(self.dialog, text="Einstellungen", padding=10)
        settings_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # AI Model
        ttk.Label(settings_frame, text="AI-Modell:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.model_var = tk.StringVar(value="llama3.2:latest")
        model_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.model_var,
            values=["llama3.2:latest", "mistral:latest", "phi3:latest"],
            state="readonly",
            width=30
        )
        model_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Confidence Threshold
        ttk.Label(settings_frame, text="Konfidenz-Schwelle:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.confidence_var = tk.DoubleVar(value=0.7)
        confidence_scale = ttk.Scale(
            settings_frame,
            from_=0.0,
            to=1.0,
            variable=self.confidence_var,
            orient=tk.HORIZONTAL,
            length=200
        )
        confidence_scale.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        conf_label = ttk.Label(settings_frame, textvariable=self.confidence_var)
        conf_label.grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(self.dialog, padding=10)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(
            button_frame,
            text="Extrahieren",
            command=self._on_ingest,
            default=tk.ACTIVE
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Abbrechen",
            command=self._on_cancel
        ).pack(side=tk.RIGHT, padx=5)
        
        # Bind keys
        self.dialog.bind('<Return>', lambda e: self._on_ingest())
        self.dialog.bind('<Escape>', lambda e: self._on_cancel())
    
    def _center_dialog(self):
        """Zentriert Dialog über Parent."""
        self.dialog.update_idletasks()
        
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        
        self.dialog.geometry(f"+{x}+{y}")
    
    def _select_file(self):
        """Öffnet Datei-Dialog."""
        filetypes = [
            ("Alle unterstützten Formate", "*.pdf *.docx *.txt *.png *.jpg *.jpeg *.xml *.json"),
            ("PDF Dokumente", "*.pdf"),
            ("Word Dokumente", "*.docx"),
            ("Text Dateien", "*.txt"),
            ("Bilder", "*.png *.jpg *.jpeg"),
            ("Strukturiert", "*.xml *.json"),
            ("Alle Dateien", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            parent=self.dialog,
            title="Quelldatei auswählen",
            filetypes=filetypes
        )
        
        if filename:
            self.selected_file = Path(filename)
            self.file_path_var.set(str(self.selected_file))
            
            # Auto-detect source type
            suffix = self.selected_file.suffix.lower()
            if suffix in ['.pdf', '.docx', '.txt']:
                self.source_type_var.set('text')
            elif suffix in ['.png', '.jpg', '.jpeg']:
                self.source_type_var.set('image')
            elif suffix in ['.xml', '.json']:
                self.source_type_var.set('structured')
    
    def _on_ingest(self):
        """Handle Extrahieren-Button."""
        if not self.selected_file:
            tk.messagebox.showwarning(
                "Keine Datei",
                "Bitte wählen Sie eine Datei aus."
            )
            return
        
        if not self.selected_file.exists():
            tk.messagebox.showerror(
                "Datei nicht gefunden",
                f"Die Datei wurde nicht gefunden:\n{self.selected_file}"
            )
            return
        
        settings = {
            "source_type": self.source_type_var.get(),
            "model": self.model_var.get(),
            "confidence_threshold": self.confidence_var.get()
        }
        
        self.result = {
            "file_path": self.selected_file,
            "settings": settings
        }
        
        # Callback ausführen
        if self.on_ingest:
            self.on_ingest(self.selected_file, settings)
        
        self.dialog.destroy()
    
    def _on_cancel(self):
        """Handle Cancel-Button."""
        self.result = None
        self.dialog.destroy()
    
    def show(self) -> Optional[Dict[str, Any]]:
        """
        Zeigt Wizard modal an.
        
        Returns:
            {'file_path': Path, 'settings': dict} oder None wenn abgebrochen
        """
        self.dialog.wait_window()
        return self.result


# Factory Functions für einfache Nutzung

def show_ai_process_generation_dialog(
    parent: tk.Tk | tk.Toplevel,
    on_generate: Optional[Callable[[str, Dict[str, Any]], None]] = None
) -> Optional[Dict[str, Any]]:
    """
    Zeigt AI-Process-Generation Dialog.
    
    Args:
        parent: Parent Window
        on_generate: Callback (prompt, settings) → None
        
    Returns:
        {'prompt': str, 'settings': dict} oder None
    """
    dialog = AIProcessGenerationDialog(parent, on_generate)
    return dialog.show()


def show_ai_ingestion_wizard(
    parent: tk.Tk | tk.Toplevel,
    on_ingest: Optional[Callable[[Path, Dict[str, Any]], None]] = None
) -> Optional[Dict[str, Any]]:
    """
    Zeigt AI-Ingestion Wizard.
    
    Args:
        parent: Parent Window
        on_ingest: Callback (file_path, settings) → None
        
    Returns:
        {'file_path': Path, 'settings': dict} oder None
    """
    wizard = AIIngestionWizard(parent, on_ingest)
    return wizard.show()
