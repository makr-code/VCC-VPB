"""
Tests für PaletteModel
======================

Testet PaletteItem, PaletteCategory und PaletteModel.
"""

import pytest
import json
from pathlib import Path
from vpb.models.palette import PaletteItem, PaletteCategory, PaletteModel


class TestPaletteItem:
    """Tests für PaletteItem."""
    
    def test_create_element_item(self):
        """Test: Element-Item erstellen."""
        item = PaletteItem(
            type="START_EVENT",
            name="Start",
            shape="circle",
            fill="#C3F7C3",
            outline="#2E8B57"
        )
        
        assert item.type == "START_EVENT"
        assert item.name == "Start"
        assert item.shape == "circle"
        assert item.is_element()
        assert not item.is_connection()
    
    def test_create_connection_item(self):
        """Test: Connection-Item erstellen."""
        item = PaletteItem(
            type="SEQUENCE",
            name="Geschäftsgang",
            arrow_style="single"
        )
        
        assert item.type == "SEQUENCE"
        assert item.name == "Geschäftsgang"
        assert item.arrow_style == "single"
        assert item.is_connection()
        assert not item.is_element()
    
    def test_item_requires_type(self):
        """Test: Item erfordert type."""
        with pytest.raises(ValueError, match="type darf nicht leer"):
            PaletteItem(type="", name="Test")
    
    def test_item_requires_name(self):
        """Test: Item erfordert name."""
        with pytest.raises(ValueError, match="name darf nicht leer"):
            PaletteItem(type="TEST", name="")
    
    def test_item_to_dict(self):
        """Test: Item zu dict konvertieren."""
        item = PaletteItem(
            type="FUNCTION",
            name="Aufgabe",
            shape="rect",
            fill="#E6F3FF",
            outline="#004C99"
        )
        
        result = item.to_dict()
        
        assert result["type"] == "FUNCTION"
        assert result["name"] == "Aufgabe"
        assert result["shape"] == "rect"
        assert result["fill"] == "#E6F3FF"
        assert result["outline"] == "#004C99"
    
    def test_item_from_dict(self):
        """Test: Item aus dict erstellen."""
        data = {
            "type": "GATEWAY",
            "name": "Gateway",
            "shape": "diamond",
            "fill": "#FFFF99",
            "outline": "#B3B300"
        }
        
        item = PaletteItem.from_dict(data)
        
        assert item.type == "GATEWAY"
        assert item.name == "Gateway"
        assert item.shape == "diamond"
        assert item.fill == "#FFFF99"
    
    def test_item_with_metadata(self):
        """Test: Item mit zusätzlichen Metadaten."""
        data = {
            "type": "EVENT",
            "name": "Ereignis",
            "shape": "oval",
            "custom_field": "value",
            "another": 123
        }
        
        item = PaletteItem.from_dict(data)
        
        assert item.metadata["custom_field"] == "value"
        assert item.metadata["another"] == 123


class TestPaletteCategory:
    """Tests für PaletteCategory."""
    
    def test_create_category(self):
        """Test: Kategorie erstellen."""
        category = PaletteCategory(
            id="bpmn-basic",
            title="Elemente – Basis"
        )
        
        assert category.id == "bpmn-basic"
        assert category.title == "Elemente – Basis"
        assert len(category.items) == 0
    
    def test_category_requires_id(self):
        """Test: Kategorie erfordert ID."""
        with pytest.raises(ValueError, match="id darf nicht leer"):
            PaletteCategory(id="", title="Test")
    
    def test_category_requires_title(self):
        """Test: Kategorie erfordert Titel."""
        with pytest.raises(ValueError, match="title darf nicht leer"):
            PaletteCategory(id="test", title="")
    
    def test_category_with_items(self):
        """Test: Kategorie mit Items."""
        items = [
            PaletteItem(type="START_EVENT", name="Start", shape="circle"),
            PaletteItem(type="FUNCTION", name="Aufgabe", shape="rect"),
            PaletteItem(type="SEQUENCE", name="Sequenz", arrow_style="single")
        ]
        
        category = PaletteCategory(
            id="test",
            title="Test Kategorie",
            items=items
        )
        
        assert len(category.items) == 3
        assert len(category.get_element_items()) == 2
        assert len(category.get_connection_items()) == 1
    
    def test_get_item_by_type(self):
        """Test: Item nach Typ finden."""
        items = [
            PaletteItem(type="START_EVENT", name="Start", shape="circle"),
            PaletteItem(type="FUNCTION", name="Aufgabe", shape="rect")
        ]
        
        category = PaletteCategory(id="test", title="Test", items=items)
        
        item = category.get_item_by_type("FUNCTION")
        assert item is not None
        assert item.name == "Aufgabe"
        
        item = category.get_item_by_type("UNKNOWN")
        assert item is None
    
    def test_category_to_dict(self):
        """Test: Kategorie zu dict."""
        items = [
            PaletteItem(type="START_EVENT", name="Start", shape="circle")
        ]
        
        category = PaletteCategory(
            id="test",
            title="Test Kategorie",
            items=items
        )
        
        result = category.to_dict()
        
        assert result["id"] == "test"
        assert result["title"] == "Test Kategorie"
        assert len(result["items"]) == 1
        assert result["items"][0]["type"] == "START_EVENT"
    
    def test_category_from_dict(self):
        """Test: Kategorie aus dict."""
        data = {
            "id": "bpmn-basic",
            "title": "BPMN Basis",
            "items": [
                {"type": "START_EVENT", "name": "Start", "shape": "circle"},
                {"type": "FUNCTION", "name": "Aufgabe", "shape": "rect"}
            ]
        }
        
        category = PaletteCategory.from_dict(data)
        
        assert category.id == "bpmn-basic"
        assert category.title == "BPMN Basis"
        assert len(category.items) == 2


class TestPaletteModel:
    """Tests für PaletteModel."""
    
    def test_create_empty_palette(self):
        """Test: Leere Palette erstellen."""
        palette = PaletteModel()
        
        assert len(palette.categories) == 0
        assert len(palette.metadata) == 0
    
    def test_add_category(self):
        """Test: Kategorie hinzufügen."""
        palette = PaletteModel()
        category = PaletteCategory(id="test", title="Test")
        
        palette.add_category(category)
        
        assert len(palette.categories) == 1
        assert palette.get_category("test") == category
    
    def test_add_duplicate_category_fails(self):
        """Test: Duplikat-Kategorie schlägt fehl."""
        palette = PaletteModel()
        palette.add_category(PaletteCategory(id="test", title="Test 1"))
        
        with pytest.raises(ValueError, match="existiert bereits"):
            palette.add_category(PaletteCategory(id="test", title="Test 2"))
    
    def test_remove_category(self):
        """Test: Kategorie entfernen."""
        palette = PaletteModel()
        palette.add_category(PaletteCategory(id="test", title="Test"))
        
        result = palette.remove_category("test")
        
        assert result is True
        assert len(palette.categories) == 0
        assert palette.get_category("test") is None
    
    def test_remove_nonexistent_category(self):
        """Test: Nicht-existente Kategorie entfernen."""
        palette = PaletteModel()
        
        result = palette.remove_category("unknown")
        
        assert result is False
    
    def test_get_items_by_category(self):
        """Test: Items nach Kategorie abrufen."""
        items = [
            PaletteItem(type="START_EVENT", name="Start", shape="circle"),
            PaletteItem(type="FUNCTION", name="Aufgabe", shape="rect")
        ]
        
        category = PaletteCategory(id="test", title="Test", items=items)
        palette = PaletteModel(categories=[category])
        
        result = palette.get_items_by_category("test")
        
        assert len(result) == 2
        assert result[0].type == "START_EVENT"
    
    def test_find_item_by_type(self):
        """Test: Item nach Typ finden (über alle Kategorien)."""
        cat1_items = [
            PaletteItem(type="START_EVENT", name="Start", shape="circle")
        ]
        cat2_items = [
            PaletteItem(type="FUNCTION", name="Aufgabe", shape="rect")
        ]
        
        palette = PaletteModel(categories=[
            PaletteCategory(id="cat1", title="Cat 1", items=cat1_items),
            PaletteCategory(id="cat2", title="Cat 2", items=cat2_items)
        ])
        
        item = palette.find_item_by_type("FUNCTION")
        
        assert item is not None
        assert item.name == "Aufgabe"
    
    def test_get_all_element_types(self):
        """Test: Alle Element-Typen abrufen."""
        items = [
            PaletteItem(type="START_EVENT", name="Start", shape="circle"),
            PaletteItem(type="FUNCTION", name="Aufgabe", shape="rect"),
            PaletteItem(type="SEQUENCE", name="Sequenz", arrow_style="single")
        ]
        
        category = PaletteCategory(id="test", title="Test", items=items)
        palette = PaletteModel(categories=[category])
        
        types = palette.get_all_element_types()
        
        assert len(types) == 2
        assert "START_EVENT" in types
        assert "FUNCTION" in types
        assert "SEQUENCE" not in types
    
    def test_get_all_connection_types(self):
        """Test: Alle Connection-Typen abrufen."""
        items = [
            PaletteItem(type="START_EVENT", name="Start", shape="circle"),
            PaletteItem(type="SEQUENCE", name="Sequenz", arrow_style="single"),
            PaletteItem(type="MESSAGE", name="Nachricht", arrow_style="double")
        ]
        
        category = PaletteCategory(id="test", title="Test", items=items)
        palette = PaletteModel(categories=[category])
        
        types = palette.get_all_connection_types()
        
        assert len(types) == 2
        assert "SEQUENCE" in types
        assert "MESSAGE" in types
        assert "START_EVENT" not in types
    
    def test_validate_empty_palette(self):
        """Test: Leere Palette validieren."""
        palette = PaletteModel()
        
        errors = palette.validate()
        
        assert len(errors) == 1
        assert "keine Kategorien" in errors[0]
    
    def test_validate_category_without_items(self):
        """Test: Kategorie ohne Items validieren."""
        palette = PaletteModel(categories=[
            PaletteCategory(id="empty", title="Empty")
        ])
        
        errors = palette.validate()
        
        assert len(errors) == 1
        assert "hat keine Items" in errors[0]
    
    def test_validate_duplicate_category_ids(self):
        """Test: Duplikat Kategorie-IDs validieren."""
        # Bypass add_category um Duplikate zu erlauben
        palette = PaletteModel()
        palette.categories = [
            PaletteCategory(id="test", title="Test 1", items=[
                PaletteItem(type="A", name="A", shape="circle")
            ]),
            PaletteCategory(id="test", title="Test 2", items=[
                PaletteItem(type="B", name="B", shape="rect")
            ])
        ]
        
        errors = palette.validate()
        
        assert any("Duplikate" in err for err in errors)
    
    def test_to_dict(self):
        """Test: Palette zu dict."""
        items = [
            PaletteItem(type="START_EVENT", name="Start", shape="circle")
        ]
        category = PaletteCategory(id="test", title="Test", items=items)
        palette = PaletteModel(categories=[category])
        
        result = palette.to_dict()
        
        assert "categories" in result
        assert len(result["categories"]) == 1
        assert result["categories"][0]["id"] == "test"
    
    def test_from_dict(self):
        """Test: Palette aus dict."""
        data = {
            "categories": [
                {
                    "id": "bpmn-basic",
                    "title": "BPMN Basis",
                    "items": [
                        {"type": "START_EVENT", "name": "Start", "shape": "circle"}
                    ]
                }
            ]
        }
        
        palette = PaletteModel.from_dict(data)
        
        assert len(palette.categories) == 1
        assert palette.categories[0].id == "bpmn-basic"
    
    def test_from_json_file(self, tmp_path):
        """Test: Palette aus JSON-Datei laden."""
        # Erstelle temporäre JSON-Datei
        json_file = tmp_path / "test_palette.json"
        data = {
            "categories": [
                {
                    "id": "test",
                    "title": "Test",
                    "items": [
                        {"type": "START_EVENT", "name": "Start", "shape": "circle"}
                    ]
                }
            ]
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        
        # Lade Palette
        palette = PaletteModel.from_json_file(json_file)
        
        assert len(palette.categories) == 1
        assert palette.categories[0].id == "test"
    
    def test_from_json_file_not_found(self):
        """Test: Palette aus nicht-existenter Datei."""
        with pytest.raises(FileNotFoundError):
            PaletteModel.from_json_file("nonexistent.json")
    
    def test_to_json_file(self, tmp_path):
        """Test: Palette als JSON-Datei speichern."""
        items = [
            PaletteItem(type="START_EVENT", name="Start", shape="circle")
        ]
        category = PaletteCategory(id="test", title="Test", items=items)
        palette = PaletteModel(categories=[category])
        
        json_file = tmp_path / "output.json"
        palette.to_json_file(json_file)
        
        assert json_file.exists()
        
        # Lade und verifiziere
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert len(data["categories"]) == 1
        assert data["categories"][0]["id"] == "test"
    
    def test_repr(self):
        """Test: String-Repräsentation."""
        items = [
            PaletteItem(type="A", name="A", shape="circle"),
            PaletteItem(type="B", name="B", shape="rect")
        ]
        category = PaletteCategory(id="test", title="Test", items=items)
        palette = PaletteModel(categories=[category])
        
        result = repr(palette)
        
        assert "1 categories" in result
        assert "2 items" in result


class TestPaletteModelRealData:
    """Tests mit echten Palette-Daten."""
    
    def test_load_default_palette(self):
        """Test: Default-Palette laden (wenn vorhanden)."""
        palette_path = Path("palettes/default_palette.json")
        
        if not palette_path.exists():
            pytest.skip("default_palette.json nicht vorhanden")
        
        palette = PaletteModel.from_json_file(palette_path)
        
        # Validiere Struktur
        errors = palette.validate()
        assert len(errors) == 0, f"Palette hat Fehler: {errors}"
        
        # Prüfe dass Kategorien vorhanden sind
        assert len(palette.categories) > 0
        
        # Prüfe dass Element- und Connection-Typen vorhanden sind
        element_types = palette.get_all_element_types()
        connection_types = palette.get_all_connection_types()
        
        assert len(element_types) > 0
        assert len(connection_types) > 0
        
        # Prüfe dass bekannte Typen vorhanden sind
        assert "START_EVENT" in element_types
        assert "SEQUENCE" in connection_types
