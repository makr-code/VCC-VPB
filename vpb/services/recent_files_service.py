"""
Recent Files Service für VPB Process Designer.

Verwaltet die Liste der zuletzt geöffneten Dateien.
Speichert die Liste persistent in einer JSON-Datei.

Autor: GitHub Copilot
"""

import json
import os
from typing import List, Optional
from pathlib import Path


class RecentFilesService:
    """
    Service für die Verwaltung der zuletzt geöffneten Dateien.
    
    Speichert bis zu max_files Dateipfade in einer JSON-Datei.
    Automatisches Entfernen von nicht mehr existierenden Dateien.
    
    Attributes:
        max_files: Maximale Anzahl an Recent Files (default: 10)
        storage_file: Pfad zur JSON-Datei für persistente Speicherung
        recent_files: Liste der zuletzt geöffneten Dateien
    """
    
    def __init__(self, storage_file: str = "recent_files.json", max_files: int = 10):
        """
        Initialisiert den Recent Files Service.
        
        Args:
            storage_file: Pfad zur JSON-Datei (relativ zum Arbeitsverzeichnis)
            max_files: Maximale Anzahl an Recent Files
        """
        self.storage_file = storage_file
        self.max_files = max_files
        self.recent_files: List[str] = []
        
        # Lade gespeicherte Recent Files
        self._load_from_disk()
    
    def add_file(self, file_path: str) -> None:
        """
        Fügt eine Datei zur Liste der Recent Files hinzu.
        
        Wenn die Datei bereits in der Liste ist, wird sie an den Anfang verschoben.
        Wenn die maximale Anzahl überschritten wird, wird die älteste Datei entfernt.
        
        Args:
            file_path: Absoluter Pfad zur Datei
        """
        # Normalisiere Pfad
        file_path = os.path.abspath(file_path)
        
        # Entferne Datei, falls bereits vorhanden
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        
        # Füge Datei am Anfang hinzu
        self.recent_files.insert(0, file_path)
        
        # Beschränke auf max_files
        self.recent_files = self.recent_files[:self.max_files]
        
        # Speichere auf Disk
        self._save_to_disk()
    
    def get_recent_files(self, validate: bool = True) -> List[str]:
        """
        Gibt die Liste der Recent Files zurück.
        
        Args:
            validate: Wenn True, werden nur existierende Dateien zurückgegeben
        
        Returns:
            Liste der Dateipfade (neueste zuerst)
        """
        if validate:
            # Filtere nicht existierende Dateien
            valid_files = [f for f in self.recent_files if os.path.exists(f)]
            
            # Aktualisiere Liste, falls Dateien entfernt wurden
            if len(valid_files) != len(self.recent_files):
                self.recent_files = valid_files
                self._save_to_disk()
            
            return valid_files
        
        return self.recent_files.copy()
    
    def clear_recent_files(self) -> None:
        """Löscht alle Recent Files."""
        self.recent_files = []
        self._save_to_disk()
    
    def remove_file(self, file_path: str) -> None:
        """
        Entfernt eine bestimmte Datei aus der Recent Files Liste.
        
        Args:
            file_path: Pfad zur zu entfernenden Datei
        """
        file_path = os.path.abspath(file_path)
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
            self._save_to_disk()
    
    def _load_from_disk(self) -> None:
        """Lädt Recent Files von Disk."""
        if not os.path.exists(self.storage_file):
            return
        
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.recent_files = data.get('recent_files', [])
                
                # Validiere: Nur existierende Dateien behalten
                self.recent_files = [
                    f for f in self.recent_files 
                    if os.path.exists(f)
                ][:self.max_files]
        except Exception as e:
            print(f"⚠️ Fehler beim Laden der Recent Files: {e}")
            self.recent_files = []
    
    def _save_to_disk(self) -> None:
        """Speichert Recent Files auf Disk."""
        try:
            data = {
                'recent_files': self.recent_files
            }
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Fehler beim Speichern der Recent Files: {e}")
    
    def __repr__(self) -> str:
        return f"<RecentFilesService files={len(self.recent_files)}>"
