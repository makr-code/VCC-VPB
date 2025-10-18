"""
Migration Dialog - UI für SQLite → UDS3 Migration.

Provides:
- Migration Configuration Dialog
- Progress Bar with Real-time Updates
- Error Display & User Feedback
- Migration Report Viewer
- Result Export UI

Author: VPB Development Team
Date: 18. Oktober 2025
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import json
from datetime import datetime


class MigrationDialog(tk.Toplevel):
    """
    Migration Dialog für SQLite → UDS3 Migration.
    
    Features:
    - Source/Target DB Configuration
    - Batch Size & Table Selection
    - Progress Bar with Status Updates
    - Error Display
    - Report Export
    """
    
    def __init__(self, parent: tk.Tk, on_start_callback: Optional[Callable] = None):
        """
        Initialisiert den Migration Dialog.
        
        Args:
            parent: Parent Window (VPB Application)
            on_start_callback: Callback(config) wenn Migration gestartet wird
        """
        super().__init__(parent)
        
        self.parent = parent
        self.on_start_callback = on_start_callback
        self.migration_running = False
        self.migration_result = None
        
        # Window Configuration
        self.title("SQLite → UDS3 Migration")
        self.geometry("700x800")
        self.resizable(True, True)
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.winfo_screenheight() // 2) - (800 // 2)
        self.geometry(f"700x800+{x}+{y}")
        
        self._create_widgets()
        self._load_default_config()
    
    def _create_widgets(self) -> None:
        """Erstellt alle UI-Widgets."""
        # Main Container mit Padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title Label
        title_label = ttk.Label(
            main_frame,
            text="SQLite → UDS3 Polyglot Migration",
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Notebook für Tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Tab 1: Configuration
        self.config_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.config_frame, text="Konfiguration")
        self._create_config_tab()
        
        # Tab 2: Progress
        self.progress_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.progress_frame, text="Fortschritt")
        self._create_progress_tab()
        
        # Tab 3: Results
        self.results_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.results_frame, text="Ergebnisse")
        self._create_results_tab()
        
        # Button Frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Buttons
        self.start_button = ttk.Button(
            button_frame,
            text="Migration starten",
            command=self._on_start_migration,
            width=20
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.cancel_button = ttk.Button(
            button_frame,
            text="Abbrechen",
            command=self._on_cancel,
            width=15
        )
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
        self.close_button = ttk.Button(
            button_frame,
            text="Schließen",
            command=self.destroy,
            width=15
        )
        self.close_button.pack(side=tk.RIGHT)
    
    def _create_config_tab(self) -> None:
        """Erstellt Configuration Tab."""
        # Source Database
        source_frame = ttk.LabelFrame(self.config_frame, text="Source (SQLite)", padding="10")
        source_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(source_frame, text="SQLite Datenbankpfad:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.source_db_var = tk.StringVar(value="vpb_processes.db")
        source_entry = ttk.Entry(source_frame, textvariable=self.source_db_var, width=50)
        source_entry.grid(row=0, column=1, padx=5)
        
        ttk.Button(
            source_frame,
            text="Durchsuchen…",
            command=self._browse_source_db
        ).grid(row=0, column=2)
        
        # Target Database
        target_frame = ttk.LabelFrame(self.config_frame, text="Target (UDS3 Polyglot)", padding="10")
        target_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(target_frame, text="UDS3 Backend:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.backend_var = tk.StringVar(value="auto")
        backend_combo = ttk.Combobox(
            target_frame,
            textvariable=self.backend_var,
            values=["auto", "mongodb", "postgresql", "sqlite", "chromadb", "neo4j"],
            state="readonly",
            width=20
        )
        backend_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(target_frame, text="(auto = Standard-Konfiguration)").grid(row=0, column=2, sticky=tk.W)
        
        # Migration Options
        options_frame = ttk.LabelFrame(self.config_frame, text="Optionen", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(options_frame, text="Batch Size:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.batch_size_var = tk.IntVar(value=100)
        ttk.Spinbox(
            options_frame,
            from_=1,
            to=1000,
            textvariable=self.batch_size_var,
            width=10
        ).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        self.gap_detection_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Gap Detection durchführen (vor Migration)",
            variable=self.gap_detection_var
        ).grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        self.validation_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Validierung durchführen (nach Migration)",
            variable=self.validation_var
        ).grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        self.generate_embeddings_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            options_frame,
            text="Embeddings generieren (German BERT)",
            variable=self.generate_embeddings_var
        ).grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        self.continue_on_error_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame,
            text="Bei Fehlern fortfahren",
            variable=self.continue_on_error_var
        ).grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # Table Selection
        tables_frame = ttk.LabelFrame(self.config_frame, text="Tabellen", padding="10")
        tables_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(tables_frame, text="Zu migrierende Tabellen:").pack(anchor=tk.W, pady=(0, 5))
        
        self.tables_listbox = tk.Listbox(
            tables_frame,
            selectmode=tk.MULTIPLE,
            height=6
        )
        self.tables_listbox.pack(fill=tk.BOTH, expand=True)
        
        # Standard-Tabellen
        tables = ["vpb_processes", "vpb_elements", "vpb_connections", "vpb_metadata"]
        for table in tables:
            self.tables_listbox.insert(tk.END, table)
        
        # Vorauswahl: vpb_processes
        self.tables_listbox.selection_set(0)
    
    def _create_progress_tab(self) -> None:
        """Erstellt Progress Tab."""
        # Status Label
        self.status_label = ttk.Label(
            self.progress_frame,
            text="Bereit für Migration",
            font=("Arial", 10, "bold")
        )
        self.status_label.pack(pady=(0, 10))
        
        # Progress Bar
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='determinate',
            length=600
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Progress Info
        info_frame = ttk.Frame(self.progress_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.records_label = ttk.Label(info_frame, text="Datensätze: 0 / 0")
        self.records_label.pack(side=tk.LEFT, padx=(0, 20))
        
        self.speed_label = ttk.Label(info_frame, text="Geschwindigkeit: 0 rec/s")
        self.speed_label.pack(side=tk.LEFT, padx=(0, 20))
        
        self.eta_label = ttk.Label(info_frame, text="ETA: --:--")
        self.eta_label.pack(side=tk.LEFT)
        
        # Log Output
        ttk.Label(self.progress_frame, text="Log Output:").pack(anchor=tk.W, pady=(10, 5))
        
        self.log_text = scrolledtext.ScrolledText(
            self.progress_frame,
            height=20,
            wrap=tk.WORD,
            font=("Courier", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Tag für verschiedene Log-Levels
        self.log_text.tag_config("info", foreground="black")
        self.log_text.tag_config("success", foreground="green")
        self.log_text.tag_config("warning", foreground="orange")
        self.log_text.tag_config("error", foreground="red")
    
    def _create_results_tab(self) -> None:
        """Erstellt Results Tab."""
        # Summary Frame
        summary_frame = ttk.LabelFrame(self.results_frame, text="Zusammenfassung", padding="10")
        summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.summary_text = tk.Text(
            summary_frame,
            height=8,
            wrap=tk.WORD,
            font=("Courier", 9)
        )
        self.summary_text.pack(fill=tk.BOTH, expand=True)
        self.summary_text.config(state=tk.DISABLED)
        
        # Gap Detection Results
        gaps_frame = ttk.LabelFrame(self.results_frame, text="Gap Detection", padding="10")
        gaps_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.gaps_text = scrolledtext.ScrolledText(
            gaps_frame,
            height=10,
            wrap=tk.WORD,
            font=("Courier", 9)
        )
        self.gaps_text.pack(fill=tk.BOTH, expand=True)
        
        # Validation Results
        validation_frame = ttk.LabelFrame(self.results_frame, text="Validierung", padding="10")
        validation_frame.pack(fill=tk.BOTH, expand=True)
        
        self.validation_text = scrolledtext.ScrolledText(
            validation_frame,
            height=10,
            wrap=tk.WORD,
            font=("Courier", 9)
        )
        self.validation_text.pack(fill=tk.BOTH, expand=True)
        
        # Export Button
        export_button = ttk.Button(
            self.results_frame,
            text="Report als JSON exportieren…",
            command=self._export_report
        )
        export_button.pack(pady=(10, 0))
    
    def _load_default_config(self) -> None:
        """Lädt Default-Konfiguration."""
        # Versuche, bestehende SQLite DB zu finden
        db_paths = [
            Path("vpb_processes.db"),
            Path("data/vpb_processes.db"),
            Path("../vpb_processes.db")
        ]
        
        for path in db_paths:
            if path.exists():
                self.source_db_var.set(str(path.resolve()))
                break
    
    def _browse_source_db(self) -> None:
        """Öffnet File Browser für Source DB."""
        filename = filedialog.askopenfilename(
            title="SQLite Datenbank auswählen",
            filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")]
        )
        if filename:
            self.source_db_var.set(filename)
    
    def _get_migration_config(self) -> Dict[str, Any]:
        """
        Sammelt Migration Configuration aus UI.
        
        Returns:
            Migration Config Dictionary
        """
        # Ausgewählte Tabellen
        selected_indices = self.tables_listbox.curselection()
        selected_tables = [self.tables_listbox.get(i) for i in selected_indices]
        
        # Backend Config
        backend = self.backend_var.get()
        backend_config = None if backend == "auto" else {"type": backend}
        
        return {
            "source": {
                "type": "sqlite",
                "db_path": self.source_db_var.get()
            },
            "target": {
                "type": "uds3_polyglot",
                "backend_config": backend_config
            },
            "options": {
                "batch_size": self.batch_size_var.get(),
                "tables": selected_tables,
                "gap_detection": self.gap_detection_var.get(),
                "validation": self.validation_var.get(),
                "generate_embeddings": self.generate_embeddings_var.get(),
                "continue_on_error": self.continue_on_error_var.get()
            }
        }
    
    def _on_start_migration(self) -> None:
        """Startet Migration."""
        if self.migration_running:
            messagebox.showwarning("Migration läuft", "Eine Migration ist bereits aktiv.")
            return
        
        # Config validieren
        config = self._get_migration_config()
        
        if not config["options"]["tables"]:
            messagebox.showerror("Fehler", "Bitte wählen Sie mindestens eine Tabelle aus.")
            return
        
        if not Path(config["source"]["db_path"]).exists():
            messagebox.showerror("Fehler", f"SQLite Datei nicht gefunden:\n{config['source']['db_path']}")
            return
        
        # UI State ändern
        self.migration_running = True
        self.start_button.config(state=tk.DISABLED)
        self.notebook.select(1)  # Switch to Progress Tab
        
        # Log leeren
        self.log_text.delete(1.0, tk.END)
        self._log_message("🚀 Migration gestartet...", "info")
        self._log_message(f"Source: {config['source']['db_path']}", "info")
        self._log_message(f"Tables: {', '.join(config['options']['tables'])}", "info")
        self._log_message(f"Batch Size: {config['options']['batch_size']}", "info")
        
        # Callback aufrufen
        if self.on_start_callback:
            self.on_start_callback(config, self)
    
    def _on_cancel(self) -> None:
        """Bricht Migration ab."""
        if self.migration_running:
            result = messagebox.askyesno(
                "Migration abbrechen",
                "Möchten Sie die laufende Migration wirklich abbrechen?"
            )
            if result:
                self.migration_running = False
                self._log_message("❌ Migration abgebrochen durch Benutzer", "warning")
                self.start_button.config(state=tk.NORMAL)
    
    def _log_message(self, message: str, level: str = "info") -> None:
        """
        Fügt Log-Message hinzu.
        
        Args:
            message: Log-Nachricht
            level: "info", "success", "warning", "error"
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", level)
        self.log_text.see(tk.END)
        self.log_text.update_idletasks()
    
    def update_progress(
        self,
        current: int,
        total: int,
        status: str = None,
        speed: float = None
    ) -> None:
        """
        Aktualisiert Progress Bar.
        
        Args:
            current: Aktuelle Records
            total: Gesamt Records
            status: Status-Text
            speed: Records/Second
        """
        if total > 0:
            progress = (current / total) * 100
            self.progress_bar['value'] = progress
        
        self.records_label.config(text=f"Datensätze: {current} / {total}")
        
        if status:
            self.status_label.config(text=status)
        
        if speed:
            self.speed_label.config(text=f"Geschwindigkeit: {speed:.1f} rec/s")
            
            # ETA berechnen
            if speed > 0:
                remaining = total - current
                eta_seconds = remaining / speed
                eta_minutes = int(eta_seconds // 60)
                eta_seconds = int(eta_seconds % 60)
                self.eta_label.config(text=f"ETA: {eta_minutes:02d}:{eta_seconds:02d}")
        
        self.update_idletasks()
    
    def show_results(self, result: Dict[str, Any]) -> None:
        """
        Zeigt Migration Results an.
        
        Args:
            result: Migration Result Dictionary
        """
        self.migration_result = result
        self.migration_running = False
        self.start_button.config(state=tk.NORMAL)
        
        # Switch to Results Tab
        self.notebook.select(2)
        
        # Summary
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        
        summary = f"""Migration abgeschlossen!

Dauer: {result.get('duration', 0):.2f} Sekunden
Status: {'✅ ERFOLG' if result.get('success') else '❌ FEHLER'}

Datensätze:
  - Gesamt: {result.get('total_records', 0)}
  - Erfolgreich: {result.get('successful_records', 0)}
  - Fehler: {result.get('failed_records', 0)}

Durchsatz: {result.get('records_per_second', 0):.1f} records/s
"""
        self.summary_text.insert(1.0, summary)
        self.summary_text.config(state=tk.DISABLED)
        
        # Gap Detection Results
        if 'gap_detection' in result:
            gaps = result['gap_detection']
            self.gaps_text.delete(1.0, tk.END)
            self.gaps_text.insert(1.0, json.dumps(gaps, indent=2, ensure_ascii=False))
        
        # Validation Results
        if 'validation' in result:
            validation = result['validation']
            self.validation_text.delete(1.0, tk.END)
            self.validation_text.insert(1.0, json.dumps(validation, indent=2, ensure_ascii=False))
        
        # Log Message
        if result.get('success'):
            self._log_message("✅ Migration erfolgreich abgeschlossen!", "success")
        else:
            self._log_message(f"❌ Migration mit Fehlern: {result.get('error', 'Unknown')}", "error")
    
    def _export_report(self) -> None:
        """Exportiert Migration Report als JSON."""
        if not self.migration_result:
            messagebox.showwarning("Keine Daten", "Es gibt noch keine Ergebnisse zum Exportieren.")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Report exportieren",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            initialfile=f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.migration_result, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Export erfolgreich", f"Report gespeichert:\n{filename}")
            except Exception as e:
                messagebox.showerror("Export Fehler", f"Fehler beim Speichern:\n{str(e)}")


# Standalone Test
if __name__ == "__main__":
    def test_callback(config, dialog):
        """Test Callback."""
        print("Migration gestartet mit Config:")
        print(json.dumps(config, indent=2))
        
        # Simuliere Migration
        import time
        for i in range(1, 101):
            time.sleep(0.05)
            dialog.update_progress(i, 100, status=f"Migriere Batch {i}...", speed=20.0)
            dialog._log_message(f"Batch {i} verarbeitet", "info")
        
        # Zeige Results
        result = {
            "success": True,
            "duration": 5.0,
            "total_records": 100,
            "successful_records": 100,
            "failed_records": 0,
            "records_per_second": 20.0,
            "gap_detection": {"gaps": []},
            "validation": {"valid": True}
        }
        dialog.show_results(result)
    
    root = tk.Tk()
    root.withdraw()
    
    dialog = MigrationDialog(root, on_start_callback=test_callback)
    root.mainloop()
