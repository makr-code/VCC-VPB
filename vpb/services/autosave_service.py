"""
AutoSave Service für VPB Process Designer.

Automatisches Speichern von Projekten in regelmäßigen Intervallen.
Verwendet Timer-basiertes Speichern und speichert nur bei Änderungen.

Autor: GitHub Copilot
"""

import threading
from typing import Optional, Callable


class AutoSaveService:
    """
    Service für automatisches Speichern von Projekten.
    
    Speichert Projekte in konfigurierbaren Intervallen, wenn Änderungen vorliegen.
    Verwendet einen Background-Thread mit Timer.
    
    Attributes:
        interval_seconds: Intervall in Sekunden (default: 300 = 5 Minuten)
        enabled: Aktiviert/deaktiviert Auto-Save
        save_callback: Callback-Funktion für das Speichern
    """
    
    def __init__(self, interval_seconds: int = 300, enabled: bool = True):
        """
        Initialisiert den AutoSave Service.
        
        Args:
            interval_seconds: Auto-Save Intervall in Sekunden (default: 300 = 5 Min)
            enabled: Auto-Save aktiviert (default: True)
        """
        self.interval_seconds = interval_seconds
        self.enabled = enabled
        self.save_callback: Optional[Callable] = None
        self.is_modified_callback: Optional[Callable] = None
        self._timer: Optional[threading.Timer] = None
        self._running = False
    
    def set_save_callback(self, callback: Callable) -> None:
        """
        Setzt die Callback-Funktion für das Speichern.
        
        Args:
            callback: Funktion, die zum Speichern aufgerufen wird
        """
        self.save_callback = callback
    
    def set_is_modified_callback(self, callback: Callable) -> None:
        """
        Setzt die Callback-Funktion zur Prüfung, ob Änderungen vorliegen.
        
        Args:
            callback: Funktion, die True zurückgibt, wenn Änderungen vorliegen
        """
        self.is_modified_callback = callback
    
    def start(self) -> None:
        """Startet den Auto-Save Timer."""
        if not self.enabled:
            return
        
        if self._running:
            return
        
        self._running = True
        self._schedule_next_save()
        print(f"✅ Auto-Save gestartet (Intervall: {self.interval_seconds}s)")
    
    def stop(self) -> None:
        """Stoppt den Auto-Save Timer."""
        self._running = False
        
        if self._timer:
            self._timer.cancel()
            self._timer = None
        
        print("⏸️ Auto-Save gestoppt")
    
    def trigger_save(self) -> None:
        """Triggert manuell ein Auto-Save (für sofortiges Speichern)."""
        if not self.enabled:
            return
        
        self._auto_save()
    
    def set_interval(self, interval_seconds: int) -> None:
        """
        Ändert das Auto-Save Intervall.
        
        Args:
            interval_seconds: Neues Intervall in Sekunden
        """
        self.interval_seconds = interval_seconds
        
        # Restart timer mit neuem Intervall, wenn aktiv
        if self._running:
            self.stop()
            self.start()
    
    def set_enabled(self, enabled: bool) -> None:
        """
        Aktiviert/deaktiviert Auto-Save.
        
        Args:
            enabled: True = aktiviert, False = deaktiviert
        """
        self.enabled = enabled
        
        if enabled and not self._running:
            self.start()
        elif not enabled and self._running:
            self.stop()
    
    def _schedule_next_save(self) -> None:
        """Plant das nächste Auto-Save."""
        if not self._running:
            return
        
        self._timer = threading.Timer(self.interval_seconds, self._auto_save)
        self._timer.daemon = True
        self._timer.start()
    
    def _auto_save(self) -> None:
        """Führt Auto-Save durch (wird vom Timer aufgerufen)."""
        if not self._running:
            return
        
        try:
            # Prüfe ob Änderungen vorliegen
            has_changes = False
            if self.is_modified_callback:
                has_changes = self.is_modified_callback()
            
            # Speichere nur, wenn Änderungen vorliegen
            if has_changes and self.save_callback:
                print("💾 Auto-Save: Speichere Änderungen...")
                self.save_callback()
                print("✅ Auto-Save: Erfolgreich gespeichert")
            
        except Exception as e:
            print(f"⚠️ Auto-Save Fehler: {e}")
        
        # Plane nächstes Auto-Save
        if self._running:
            self._schedule_next_save()
    
    def __repr__(self) -> str:
        status = "aktiv" if self._running else "inaktiv"
        return f"<AutoSaveService interval={self.interval_seconds}s enabled={self.enabled} status={status}>"
