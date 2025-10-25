"""
Backup Service für VPB Process Designer.

Erstellt automatische Backups von VPB-Dateien.
Backups werden im Unterordner 'autosaves/' gespeichert.

Autor: GitHub Copilot
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Optional


class BackupService:
    """
    Service für automatische Backups von VPB-Dateien.
    
    Erstellt Backups im Format: {original_name}.{timestamp}.backup.vpb.json
    Backups werden im Unterordner 'autosaves/' gespeichert.
    
    Attributes:
        backup_dir: Verzeichnis für Backups (default: 'autosaves/')
        max_backups_per_file: Maximale Anzahl an Backups pro Datei (default: 5)
    """
    
    def __init__(self, backup_dir: str = "autosaves", max_backups_per_file: int = 5):
        """
        Initialisiert den Backup Service.
        
        Args:
            backup_dir: Verzeichnis für Backups (relativ zum Arbeitsverzeichnis)
            max_backups_per_file: Maximale Anzahl an Backups pro Datei
        """
        self.backup_dir = backup_dir
        self.max_backups_per_file = max_backups_per_file
        
        # Erstelle Backup-Verzeichnis, falls nicht vorhanden
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, file_path: str) -> Optional[str]:
        """
        Erstellt ein Backup der angegebenen Datei.
        
        Args:
            file_path: Pfad zur zu sichernden Datei
        
        Returns:
            Pfad zum Backup oder None bei Fehler
        """
        if not os.path.exists(file_path):
            print(f"⚠️ Backup-Fehler: Datei nicht gefunden: {file_path}")
            return None
        
        try:
            # Erstelle Backup-Dateinamen mit Zeitstempel
            original_name = Path(file_path).stem  # Dateiname ohne Endung
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{original_name}.{timestamp}.backup.vpb.json"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # Kopiere Datei
            shutil.copy2(file_path, backup_path)
            
            print(f"✅ Backup erstellt: {backup_path}")
            
            # Entferne alte Backups, falls Limit überschritten
            self._cleanup_old_backups(original_name)
            
            return backup_path
            
        except Exception as e:
            print(f"⚠️ Fehler beim Erstellen des Backups: {e}")
            return None
    
    def create_auto_backup(self, file_path: str, canvas_data: dict) -> Optional[str]:
        """
        Erstellt ein Auto-Backup direkt aus Canvas-Daten (ohne Datei zu schreiben).
        
        Args:
            file_path: Ursprünglicher Dateipfad (für Namensgebung)
            canvas_data: Canvas-Daten als Dictionary
        
        Returns:
            Pfad zum Backup oder None bei Fehler
        """
        try:
            # Erstelle Backup-Dateinamen mit Zeitstempel
            if file_path:
                original_name = Path(file_path).stem
            else:
                original_name = "untitled"
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{original_name}.{timestamp}.autosave.vpb.json"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # Schreibe Canvas-Daten
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(canvas_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Auto-Backup erstellt: {backup_path}")
            
            # Entferne alte Backups, falls Limit überschritten
            self._cleanup_old_backups(original_name)
            
            return backup_path
            
        except Exception as e:
            print(f"⚠️ Fehler beim Erstellen des Auto-Backups: {e}")
            return None
    
    def restore_backup(self, backup_path: str, target_path: str) -> bool:
        """
        Stellt ein Backup wieder her.
        
        Args:
            backup_path: Pfad zum Backup
            target_path: Ziel-Pfad für die Wiederherstellung
        
        Returns:
            True bei Erfolg, False bei Fehler
        """
        if not os.path.exists(backup_path):
            print(f"⚠️ Backup nicht gefunden: {backup_path}")
            return False
        
        try:
            shutil.copy2(backup_path, target_path)
            print(f"✅ Backup wiederhergestellt: {backup_path} → {target_path}")
            return True
            
        except Exception as e:
            print(f"⚠️ Fehler beim Wiederherstellen des Backups: {e}")
            return False
    
    def list_backups(self, file_name: Optional[str] = None) -> list:
        """
        Listet alle Backups auf.
        
        Args:
            file_name: Optionaler Filter für Dateinamen (ohne Endung)
        
        Returns:
            Liste der Backup-Dateipfade (neueste zuerst)
        """
        try:
            backups = []
            for file in os.listdir(self.backup_dir):
                if file.endswith('.backup.vpb.json') or file.endswith('.autosave.vpb.json'):
                    if file_name is None or file.startswith(file_name):
                        full_path = os.path.join(self.backup_dir, file)
                        backups.append(full_path)
            
            # Sortiere nach Änderungsdatum (neueste zuerst)
            backups.sort(key=os.path.getmtime, reverse=True)
            return backups
            
        except Exception as e:
            print(f"⚠️ Fehler beim Auflisten der Backups: {e}")
            return []
    
    def _cleanup_old_backups(self, original_name: str) -> None:
        """
        Entfernt alte Backups, wenn Limit überschritten.
        
        Args:
            original_name: Name der ursprünglichen Datei (ohne Endung)
        """
        try:
            backups = self.list_backups(original_name)
            
            # Entferne älteste Backups, falls Limit überschritten
            if len(backups) > self.max_backups_per_file:
                for backup in backups[self.max_backups_per_file:]:
                    os.remove(backup)
                    print(f"🗑️ Altes Backup entfernt: {backup}")
                    
        except Exception as e:
            print(f"⚠️ Fehler beim Cleanup der Backups: {e}")
    
    def __repr__(self) -> str:
        return f"<BackupService dir={self.backup_dir} max_per_file={self.max_backups_per_file}>"
