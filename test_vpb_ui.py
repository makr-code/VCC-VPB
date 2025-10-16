#!/usr/bin/env python3
"""
Test für VPB UI-Komponenten: Menü, Toolbar mit VPB-Schriftzug und About-Dialog
"""

import tkinter as tk
from tkinter import ttk, messagebox


class TestVPBApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("VPB Process Designer (Test)")
        self.geometry("800x600")
        
        # Test UI erstellen
        self._create_test_ui()
        
    def _create_test_ui(self):
        # Toolbar mit VPB-Schriftzug erstellen
        toolbar = tk.Frame(self, bg="#f2f2f2", height=36)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # VPB-Schriftzug mit Logo links in der Toolbar
        vpb_frame = tk.Frame(toolbar, bg="#f2f2f2")
        vpb_frame.pack(side=tk.LEFT, padx=10, pady=4)
        
        # VPB Logo/Icon - anklickbar für About-Dialog
        vpb_logo = tk.Label(vpb_frame, text="🔄", font=("Segoe UI", 14), 
                            bg="#f2f2f2", fg="#2c3e50", cursor="hand2")
        vpb_logo.pack(side=tk.LEFT, padx=(0, 5))
        vpb_logo.bind("<Button-1>", lambda e: self._about())
        
        # VPB Schriftzug - anklickbar für About-Dialog
        vpb_label = tk.Label(vpb_frame, text="VPB", font=("Segoe UI", 12, "bold"), 
                             bg="#f2f2f2", fg="#2c3e50", cursor="hand2")
        vpb_label.pack(side=tk.LEFT)
        vpb_label.bind("<Button-1>", lambda e: self._about())
        
        # Tooltips
        self._create_tooltip(vpb_logo, "VPB Process Designer - Über")
        self._create_tooltip(vpb_label, "VPB Process Designer - Über")
        
        # Separator
        separator = tk.Frame(toolbar, width=2, bg="#d0d0d0")
        separator.pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=4)
        
        # Einige Test-Buttons
        test_buttons = [
            ("Neu", lambda: messagebox.showinfo("Test", "Neu-Funktion")),
            ("Öffnen", lambda: messagebox.showinfo("Test", "Öffnen-Funktion")),
            ("Speichern", lambda: messagebox.showinfo("Test", "Speichern-Funktion")),
        ]
        
        for text, command in test_buttons:
            btn = tk.Button(toolbar, text=text, command=command)
            btn.pack(side=tk.LEFT, padx=4, pady=4)
        
        # Menü erstellen
        self._create_menu()
        
        # Hauptinhalt
        main_frame = tk.Frame(self, bg="white")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        info_label = tk.Label(main_frame, 
                             text="VPB Process Designer - Test UI\n\nKlicken Sie auf das VPB-Logo oder den Schriftzug\num den About-Dialog zu öffnen.",
                             font=("Segoe UI", 16),
                             bg="white", justify=tk.CENTER)
        info_label.pack(expand=True)
        
    def _create_menu(self):
        """Erstellt das Hauptmenü mit VPB-About."""
        menubar = tk.Menu(self)
        
        # Datei-Menü
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Neu", command=lambda: messagebox.showinfo("Test", "Neu"))
        file_menu.add_command(label="Öffnen", command=lambda: messagebox.showinfo("Test", "Öffnen"))
        file_menu.add_separator()
        file_menu.add_command(label="Beenden", command=self.quit)
        menubar.add_cascade(label="Datei", menu=file_menu)
        
        # Hilfe-Menü
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Über VPB", command=self._about)
        menubar.add_cascade(label="Hilfe", menu=help_menu)
        
        self.config(menu=menubar)
    
    def _create_tooltip(self, widget, text):
        """Erstellt ein Tooltip für ein Widget."""
        def _on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
            tooltip_label = tk.Label(tooltip, text=text, 
                                   font=("Segoe UI", 9), bg="#2c3e50", fg="white", 
                                   relief=tk.SOLID, borderwidth=1, padx=5, pady=3)
            tooltip_label.pack()
            widget.tooltip = tooltip
        
        def _on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                delattr(widget, 'tooltip')
        
        widget.bind("<Enter>", _on_enter)
        widget.bind("<Leave>", _on_leave)
    
    def _about(self):
        """Zeigt den VPB About-Dialog."""
        about_window = tk.Toplevel(self)
        about_window.title("Über VPB Process Designer")
        about_window.geometry("500x400")
        about_window.resizable(False, False)
        about_window.transient(self)
        about_window.grab_set()
        
        # Zentriere das Fenster
        about_window.update_idletasks()
        x = (about_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (about_window.winfo_screenheight() // 2) - (400 // 2)
        about_window.geometry(f"+{x}+{y}")
        
        # Header mit VPB-Logo und Titel
        header_frame = tk.Frame(about_window, bg="#2c3e50", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # VPB Logo/Icon
        logo_label = tk.Label(header_frame, text="🔄", font=("Segoe UI", 32), 
                             bg="#2c3e50", fg="#ecf0f1")
        logo_label.pack(side=tk.LEFT, padx=20, pady=20)
        
        # Titel und Untertitel
        title_frame = tk.Frame(header_frame, bg="#2c3e50")
        title_frame.pack(side=tk.LEFT, padx=10, pady=20, expand=True, fill=tk.BOTH)
        
        title_label = tk.Label(title_frame, text="VPB Process Designer", 
                              font=("Segoe UI", 18, "bold"), 
                              bg="#2c3e50", fg="#ecf0f1")
        title_label.pack(anchor="w")
        
        subtitle_label = tk.Label(title_frame, text="Verwaltungsprozess-Beschreibungssprache Editor", 
                                 font=("Segoe UI", 10), 
                                 bg="#2c3e50", fg="#bdc3c7")
        subtitle_label.pack(anchor="w")
        
        # Inhalt
        content_frame = tk.Frame(about_window, bg="#ecf0f1", padx=30, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Version und Informationen
        version_text = """Version: 1.0 (Minimal)
Entwickelt für die deutsche Verwaltung

VPB (Verwaltungsprozess-Beschreibungssprache) ist eine 
speziell für deutsche Behörden entwickelte Sprache zur 
Modellierung und Dokumentation von Verwaltungsprozessen.

Basierend auf:
• BMI Organisationshandbuch eEPK-Standards  
• UDS3 4D-Geodaten-Integration
• Deutsche Verwaltungsrecht-Spezifika

© 2025 UDS3 Development Team
Lizenz: Behörden-intern"""
        
        info_label = tk.Label(content_frame, text=version_text, 
                             font=("Segoe UI", 10), 
                             bg="#ecf0f1", fg="#2c3e50",
                             justify=tk.LEFT, anchor="nw")
        info_label.pack(fill=tk.BOTH, expand=True)
        
        # Buttons
        button_frame = tk.Frame(about_window, bg="#ecf0f1", pady=10)
        button_frame.pack(fill=tk.X)
        
        ok_button = tk.Button(button_frame, text="OK", 
                             command=about_window.destroy,
                             font=("Segoe UI", 10), 
                             bg="#3498db", fg="white",
                             relief=tk.FLAT, padx=20, pady=8)
        ok_button.pack(side=tk.RIGHT, padx=30)
        
        # ESC-Taste bindet auf Schließen
        about_window.bind("<Escape>", lambda e: about_window.destroy())
        about_window.focus_set()


def main():
    try:
        print("[VPB Test] Starte Test-Anwendung...")
        app = TestVPBApp()
        print("[VPB Test] Test-UI erstellt - entering mainloop")
        app.mainloop()
        print("[VPB Test] Test-Anwendung beendet")
    except Exception as e:
        print(f"[VPB Test] Fehler: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()