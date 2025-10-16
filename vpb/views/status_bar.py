"""
StatusBar View - Statusleiste mit Nachrichten und Zoom-Anzeige.

Reine View-Komponente für die Statusleiste des VPB Process Designers.
Zeigt Status-Nachrichten, Koordinaten, Zoom-Level und optionale Rechts-Info an.

Event-Struktur:
    - Keine Events (StatusBar ist read-only)
    - Wird von Controller via Public API aktualisiert

Autor: GitHub Copilot (Phase 4: Views Layer)
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional


class StatusBarView:
    """
    StatusBar View für den VPB Process Designer.
    
    Zeigt Status-Informationen in mehreren Bereichen:
        - Links: Allgemeine Status-Nachrichten
        - Mitte: Optionale Zusatzinfo (z.B. Koordinaten)
        - Rechts: Permanente Info (z.B. Zoom, Ollama-Status)
    
    Attribute:
        statusbar: Tkinter Frame-Widget
        left_label: Label für Status-Nachrichten (links)
        center_label: Label für Zusatzinfo (Mitte)
        right_label: Label für permanente Info (rechts)
        
    Beispiel:
        >>> statusbar = StatusBarView(parent_window)
        >>> statusbar.set_message("Dokument gespeichert")
        >>> statusbar.set_right_info("Zoom: 100%")
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        background_color: str = "#eeeeee"
    ):
        """
        Initialisiert die StatusBar View.
        
        Args:
            parent: Parent Tk-Widget (normalerweise Hauptfenster)
            background_color: Hintergrundfarbe (default: "#eeeeee")
        """
        self.parent = parent
        self.background_color = background_color
        
        # StatusBar Frame erstellen
        self.statusbar = tk.Frame(parent, bg=background_color, height=24)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # StringVars für Labels
        self._left_var = tk.StringVar(value="Bereit")
        self._center_var = tk.StringVar(value="")
        self._right_var = tk.StringVar(value="")
        
        # Labels erstellen
        self.left_label = tk.Label(
            self.statusbar, 
            textvariable=self._left_var, 
            anchor="w", 
            bg=background_color,
            font=("Segoe UI", 9)
        )
        self.left_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 4))
        
        self.center_label = tk.Label(
            self.statusbar, 
            textvariable=self._center_var, 
            anchor="center", 
            bg=background_color,
            font=("Segoe UI", 9)
        )
        self.center_label.pack(side=tk.LEFT, padx=4)
        
        self.right_label = tk.Label(
            self.statusbar, 
            textvariable=self._right_var, 
            anchor="e", 
            bg=background_color,
            font=("Segoe UI", 9)
        )
        self.right_label.pack(side=tk.RIGHT, padx=(4, 8))
    
    # Public API - Message Management
    # --------------------------------
    
    def set_message(self, message: str) -> None:
        """
        Setzt die Status-Nachricht (links).
        
        Args:
            message: Status-Nachricht
            
        Beispiel:
            >>> statusbar.set_message("Dokument gespeichert")
        """
        self._left_var.set(message)
    
    def get_message(self) -> str:
        """
        Gibt die aktuelle Status-Nachricht zurück.
        
        Returns:
            Status-Nachricht
        """
        return self._left_var.get()
    
    def clear_message(self) -> None:
        """
        Löscht die Status-Nachricht (setzt auf "Bereit").
        """
        self._left_var.set("Bereit")
    
    def set_center_info(self, info: str) -> None:
        """
        Setzt die Zusatzinfo in der Mitte.
        
        Args:
            info: Zusatzinfo (z.B. Koordinaten)
            
        Beispiel:
            >>> statusbar.set_center_info("X: 100, Y: 200")
        """
        self._center_var.set(info)
    
    def get_center_info(self) -> str:
        """
        Gibt die aktuelle Zusatzinfo zurück.
        
        Returns:
            Zusatzinfo
        """
        return self._center_var.get()
    
    def clear_center_info(self) -> None:
        """
        Löscht die Zusatzinfo.
        """
        self._center_var.set("")
    
    def set_right_info(self, info: str) -> None:
        """
        Setzt die permanente Info rechts.
        
        Args:
            info: Permanente Info (z.B. Zoom, Ollama-Status)
            
        Beispiel:
            >>> statusbar.set_right_info("Zoom: 150% | Ollama: Online")
        """
        self._right_var.set(info)
    
    def get_right_info(self) -> str:
        """
        Gibt die aktuelle permanente Info zurück.
        
        Returns:
            Permanente Info
        """
        return self._right_var.get()
    
    def clear_right_info(self) -> None:
        """
        Löscht die permanente Info.
        """
        self._right_var.set("")
    
    def set_all(
        self, 
        message: Optional[str] = None, 
        center: Optional[str] = None, 
        right: Optional[str] = None
    ) -> None:
        """
        Setzt mehrere Info-Felder gleichzeitig.
        
        Args:
            message: Status-Nachricht (links, optional)
            center: Zusatzinfo (Mitte, optional)
            right: Permanente Info (rechts, optional)
            
        Beispiel:
            >>> statusbar.set_all(
            ...     message="Element verschoben",
            ...     center="X: 150, Y: 250",
            ...     right="Zoom: 125%"
            ... )
        """
        if message is not None:
            self.set_message(message)
        if center is not None:
            self.set_center_info(center)
        if right is not None:
            self.set_right_info(right)
    
    def clear_all(self) -> None:
        """
        Löscht alle Info-Felder.
        """
        self.clear_message()
        self.clear_center_info()
        self.clear_right_info()
    
    # Public API - Visibility & Styling
    # ----------------------------------
    
    def hide(self) -> None:
        """Versteckt die StatusBar."""
        self.statusbar.pack_forget()
    
    def show(self) -> None:
        """Zeigt die StatusBar wieder an."""
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def is_visible(self) -> bool:
        """
        Prüft, ob die StatusBar sichtbar ist.
        
        Returns:
            True wenn sichtbar, sonst False
        """
        return bool(self.statusbar.winfo_ismapped())
    
    def set_background_color(self, color: str) -> None:
        """
        Setzt die Hintergrundfarbe der StatusBar.
        
        Args:
            color: Farbe als Hex-String (z.B. "#eeeeee")
        """
        self.background_color = color
        self.statusbar.config(bg=color)
        self.left_label.config(bg=color)
        self.center_label.config(bg=color)
        self.right_label.config(bg=color)
    
    def get_background_color(self) -> str:
        """
        Gibt die aktuelle Hintergrundfarbe zurück.
        
        Returns:
            Farbe als Hex-String
        """
        return self.background_color
    
    def set_font(self, font: tuple) -> None:
        """
        Setzt die Schriftart für alle Labels.
        
        Args:
            font: Font-Tuple (family, size, style)
            
        Beispiel:
            >>> statusbar.set_font(("Arial", 10, "bold"))
        """
        self.left_label.config(font=font)
        self.center_label.config(font=font)
        self.right_label.config(font=font)
    
    # Convenience Methods
    # -------------------
    
    def show_coordinates(self, x: float, y: float) -> None:
        """
        Zeigt Koordinaten in der Mitte an.
        
        Args:
            x: X-Koordinate
            y: Y-Koordinate
        """
        self.set_center_info(f"X: {x:.0f}, Y: {y:.0f}")
    
    def show_zoom(self, zoom_percent: float) -> None:
        """
        Zeigt Zoom-Level rechts an.
        
        Args:
            zoom_percent: Zoom in Prozent (z.B. 100.0)
        """
        self.set_right_info(f"Zoom: {zoom_percent:.0f}%")
    
    def show_selection_count(self, count: int) -> None:
        """
        Zeigt Anzahl selektierter Elemente an.
        
        Args:
            count: Anzahl Elemente
        """
        if count == 0:
            self.clear_message()
        elif count == 1:
            self.set_message("1 Element ausgewählt")
        else:
            self.set_message(f"{count} Elemente ausgewählt")
    
    def show_error(self, message: str) -> None:
        """
        Zeigt eine Fehler-Nachricht an (roter Text).
        
        Args:
            message: Fehler-Nachricht
        """
        self.set_message(f"⚠️ {message}")
        self.left_label.config(fg="red")
        
        # Nach 3 Sekunden Farbe zurücksetzen
        self.statusbar.after(3000, lambda: self.left_label.config(fg="black"))
    
    def show_success(self, message: str) -> None:
        """
        Zeigt eine Erfolgs-Nachricht an (grüner Text).
        
        Args:
            message: Erfolgs-Nachricht
        """
        self.set_message(f"✓ {message}")
        self.left_label.config(fg="green")
        
        # Nach 2 Sekunden Farbe zurücksetzen
        self.statusbar.after(2000, lambda: self.left_label.config(fg="black"))
    
    def __repr__(self) -> str:
        """String-Repräsentation für Debugging."""
        return (
            f"StatusBarView("
            f"visible={self.is_visible()}, "
            f"message='{self.get_message()}', "
            f"bg={self.get_background_color()}"
            f")"
        )


# Factory Functions
# ----------------

def create_status_bar(
    parent: tk.Widget,
    background_color: str = "#eeeeee"
) -> StatusBarView:
    """
    Factory-Funktion zum Erstellen einer StatusBar View.
    
    Args:
        parent: Parent Tk-Widget
        background_color: Hintergrundfarbe (default: "#eeeeee")
    
    Returns:
        StatusBarView Instanz
    
    Beispiel:
        >>> statusbar = create_status_bar(root_window)
        >>> statusbar.set_message("Willkommen!")
    """
    return StatusBarView(parent, background_color)


def get_status_bar_state(statusbar: StatusBarView) -> dict:
    """
    Gibt den aktuellen Status der StatusBar als Dictionary zurück.
    
    Args:
        statusbar: StatusBarView Instanz
    
    Returns:
        Dictionary mit allen Werten
    
    Beispiel:
        >>> state = get_status_bar_state(statusbar)
        >>> # state = {"message": "Bereit", "center": "", "right": "Zoom: 100%"}
    """
    return {
        "message": statusbar.get_message(),
        "center": statusbar.get_center_info(),
        "right": statusbar.get_right_info(),
        "visible": statusbar.is_visible(),
        "background": statusbar.get_background_color(),
    }


def restore_status_bar_state(statusbar: StatusBarView, state: dict) -> None:
    """
    Stellt den StatusBar-Status aus einem Dictionary wieder her.
    
    Args:
        statusbar: StatusBarView Instanz
        state: Dictionary mit Werten
    
    Beispiel:
        >>> state = {"message": "Bereit", "right": "Zoom: 100%"}
        >>> restore_status_bar_state(statusbar, state)
    """
    if "message" in state:
        statusbar.set_message(state["message"])
    if "center" in state:
        statusbar.set_center_info(state["center"])
    if "right" in state:
        statusbar.set_right_info(state["right"])
    if "background" in state:
        statusbar.set_background_color(state["background"])
    if "visible" in state:
        if state["visible"]:
            statusbar.show()
        else:
            statusbar.hide()
