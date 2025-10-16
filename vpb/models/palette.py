"""
VPB Palette Model
==================

Dieses Modul definiert das Datenmodell für VPB-Paletten.

Eine Palette ist eine Sammlung von Element-Templates und Connection-Templates,
organisiert in Kategorien. Sie wird aus JSON-Dateien geladen und validiert.

Hauptklassen:
- PaletteItem: Ein einzelnes Template (Element oder Connection)
- PaletteCategory: Eine Kategorie mit mehreren Items
- PaletteModel: Die komplette Palette mit allen Kategorien

Verwendung:
    palette = PaletteModel.from_json_file("palettes/default_palette.json")
    categories = palette.get_categories()
    items = palette.get_items_by_category("bpmn-basic")

Autor: VPB Development Team
Datum: 14. Oktober 2025
Version: 0.2.0-alpha
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class PaletteItem:
    """
    Ein einzelnes Palette-Item (Element oder Connection Template).
    
    Attributes:
        type: Item-Typ (z.B. "START_EVENT", "FUNCTION", "SEQUENCE")
        name: Anzeigename des Items
        shape: Form für Elemente (z.B. "circle", "rect", "diamond")
        fill: Füllfarbe (z.B. "#C3F7C3")
        outline: Rahmenfarbe (z.B. "#2E8B57")
        arrow_style: Arrow-Stil für Connections (z.B. "single", "double", "none")
        dash: Strichlinie-Muster (z.B. [6, 4] für gestrichelt)
        metadata: Zusätzliche Metadaten
    """
    
    type: str
    name: str
    shape: Optional[str] = None
    fill: Optional[str] = None
    outline: Optional[str] = None
    arrow_style: Optional[str] = None
    dash: Optional[List[int]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validierung nach Initialisierung."""
        if not self.type:
            raise ValueError("PaletteItem.type darf nicht leer sein")
        if not self.name:
            raise ValueError("PaletteItem.name darf nicht leer sein")
    
    def is_element(self) -> bool:
        """Prüft ob Item ein Element ist (hat shape)."""
        return self.shape is not None
    
    def is_connection(self) -> bool:
        """Prüft ob Item eine Connection ist (hat arrow_style)."""
        return self.arrow_style is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Item zu Dictionary."""
        result = {
            "type": self.type,
            "name": self.name
        }
        
        if self.shape is not None:
            result["shape"] = self.shape
        if self.fill is not None:
            result["fill"] = self.fill
        if self.outline is not None:
            result["outline"] = self.outline
        if self.arrow_style is not None:
            result["arrow_style"] = self.arrow_style
        if self.dash is not None:
            result["dash"] = self.dash
        if self.metadata:
            result.update(self.metadata)
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PaletteItem':
        """Erstellt Item aus Dictionary."""
        # Extrahiere bekannte Felder
        known_fields = {
            'type', 'name', 'shape', 'fill', 'outline', 'arrow_style', 'dash'
        }
        
        # Trenne bekannte von unbekannten Feldern
        item_data = {k: v for k, v in data.items() if k in known_fields}
        metadata = {k: v for k, v in data.items() if k not in known_fields}
        
        return cls(**item_data, metadata=metadata)


@dataclass
class PaletteCategory:
    """
    Eine Kategorie in der Palette.
    
    Attributes:
        id: Eindeutige ID der Kategorie (z.B. "bpmn-basic")
        title: Anzeigename der Kategorie (z.B. "Elemente – Basis")
        items: Liste der Items in dieser Kategorie
        metadata: Zusätzliche Metadaten
    """
    
    id: str
    title: str
    items: List[PaletteItem] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validierung nach Initialisierung."""
        if not self.id:
            raise ValueError("PaletteCategory.id darf nicht leer sein")
        if not self.title:
            raise ValueError("PaletteCategory.title darf nicht leer sein")
    
    def get_item_by_type(self, item_type: str) -> Optional[PaletteItem]:
        """Findet Item nach Typ."""
        for item in self.items:
            if item.type == item_type:
                return item
        return None
    
    def get_element_items(self) -> List[PaletteItem]:
        """Gibt alle Element-Items zurück."""
        return [item for item in self.items if item.is_element()]
    
    def get_connection_items(self) -> List[PaletteItem]:
        """Gibt alle Connection-Items zurück."""
        return [item for item in self.items if item.is_connection()]
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Kategorie zu Dictionary."""
        result = {
            "id": self.id,
            "title": self.title,
            "items": [item.to_dict() for item in self.items]
        }
        
        if self.metadata:
            result.update(self.metadata)
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PaletteCategory':
        """Erstellt Kategorie aus Dictionary."""
        items_data = data.get('items', [])
        items = [PaletteItem.from_dict(item) for item in items_data]
        
        # Extrahiere bekannte Felder
        known_fields = {'id', 'title', 'items'}
        category_data = {k: v for k, v in data.items() if k in known_fields and k != 'items'}
        metadata = {k: v for k, v in data.items() if k not in known_fields}
        
        return cls(
            **category_data,
            items=items,
            metadata=metadata
        )


class PaletteModel:
    """
    Das Palette-Model.
    
    Verwaltet alle Kategorien und Items einer Palette.
    Kann aus JSON geladen und gespeichert werden.
    
    Attributes:
        categories: Liste aller Kategorien
        metadata: Zusätzliche Palette-Metadaten
    """
    
    def __init__(
        self,
        categories: Optional[List[PaletteCategory]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialisiert Palette.
        
        Args:
            categories: Liste der Kategorien
            metadata: Palette-Metadaten
        """
        self.categories: List[PaletteCategory] = categories or []
        self.metadata: Dict[str, Any] = metadata or {}
        
        # Index für schnellen Zugriff
        self._category_index: Dict[str, PaletteCategory] = {}
        self._rebuild_index()
    
    def _rebuild_index(self):
        """Rebuildet den internen Index."""
        self._category_index = {cat.id: cat for cat in self.categories}
    
    def add_category(self, category: PaletteCategory):
        """Fügt Kategorie hinzu."""
        if category.id in self._category_index:
            raise ValueError(f"Kategorie mit ID '{category.id}' existiert bereits")
        
        self.categories.append(category)
        self._category_index[category.id] = category
    
    def remove_category(self, category_id: str) -> bool:
        """
        Entfernt Kategorie.
        
        Returns:
            True wenn entfernt, False wenn nicht gefunden
        """
        if category_id not in self._category_index:
            return False
        
        category = self._category_index[category_id]
        self.categories.remove(category)
        del self._category_index[category_id]
        return True
    
    def get_category(self, category_id: str) -> Optional[PaletteCategory]:
        """Gibt Kategorie nach ID zurück."""
        return self._category_index.get(category_id)
    
    def get_categories(self) -> List[PaletteCategory]:
        """Gibt alle Kategorien zurück."""
        return self.categories.copy()
    
    def get_items_by_category(self, category_id: str) -> List[PaletteItem]:
        """Gibt alle Items einer Kategorie zurück."""
        category = self.get_category(category_id)
        return category.items.copy() if category else []
    
    def find_item_by_type(self, item_type: str) -> Optional[PaletteItem]:
        """
        Findet Item nach Typ (über alle Kategorien).
        
        Returns:
            Erstes gefundenes Item oder None
        """
        for category in self.categories:
            item = category.get_item_by_type(item_type)
            if item:
                return item
        return None
    
    def get_all_element_types(self) -> List[str]:
        """Gibt alle Element-Typen zurück."""
        types = []
        for category in self.categories:
            for item in category.get_element_items():
                types.append(item.type)
        return types
    
    def get_all_connection_types(self) -> List[str]:
        """Gibt alle Connection-Typen zurück."""
        types = []
        for category in self.categories:
            for item in category.get_connection_items():
                types.append(item.type)
        return types
    
    def validate(self) -> List[str]:
        """
        Validiert Palette-Struktur.
        
        Returns:
            Liste der Fehler (leer wenn valid)
        """
        errors = []
        
        # Prüfe ob Kategorien vorhanden
        if not self.categories:
            errors.append("Palette hat keine Kategorien")
        
        # Prüfe Kategorie-IDs auf Duplikate
        category_ids = [cat.id for cat in self.categories]
        if len(category_ids) != len(set(category_ids)):
            errors.append("Duplikate in Kategorie-IDs gefunden")
        
        # Prüfe jede Kategorie
        for category in self.categories:
            # Prüfe ob Items vorhanden
            if not category.items:
                errors.append(f"Kategorie '{category.id}' hat keine Items")
            
            # Prüfe Item-Typen auf Duplikate innerhalb Kategorie
            item_types = [item.type for item in category.items]
            duplicates = [t for t in item_types if item_types.count(t) > 1]
            if duplicates:
                errors.append(
                    f"Kategorie '{category.id}' hat doppelte Item-Typen: {set(duplicates)}"
                )
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Palette zu Dictionary."""
        result = {
            "categories": [cat.to_dict() for cat in self.categories]
        }
        
        if self.metadata:
            result.update(self.metadata)
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PaletteModel':
        """Erstellt Palette aus Dictionary."""
        categories_data = data.get('categories', [])
        categories = [PaletteCategory.from_dict(cat) for cat in categories_data]
        
        # Extrahiere Metadata (alle nicht-categories Felder)
        metadata = {k: v for k, v in data.items() if k != 'categories'}
        
        return cls(categories=categories, metadata=metadata)
    
    @classmethod
    def from_json_file(cls, file_path: Path | str) -> 'PaletteModel':
        """
        Lädt Palette aus JSON-Datei.
        
        Args:
            file_path: Pfad zur JSON-Datei
            
        Returns:
            PaletteModel Instanz
            
        Raises:
            FileNotFoundError: Wenn Datei nicht existiert
            json.JSONDecodeError: Wenn JSON ungültig
            ValueError: Wenn Palette-Struktur ungültig
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Palette-Datei nicht gefunden: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        palette = cls.from_dict(data)
        
        # Validiere
        errors = palette.validate()
        if errors:
            raise ValueError(f"Ungültige Palette-Struktur: {', '.join(errors)}")
        
        return palette
    
    def to_json_file(self, file_path: Path | str):
        """
        Speichert Palette als JSON-Datei.
        
        Args:
            file_path: Pfad zur JSON-Datei
        """
        if isinstance(file_path, str):
            file_path = Path(file_path)
        
        # Erstelle Verzeichnis falls nicht vorhanden
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    def __repr__(self) -> str:
        """String-Repräsentation."""
        cat_count = len(self.categories)
        item_count = sum(len(cat.items) for cat in self.categories)
        return f"<PaletteModel: {cat_count} categories, {item_count} items>"
