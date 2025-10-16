"""
Code Sync Service - Bidirektionale Synchronisation zwischen Canvas und Code-Editoren.

Synchronisiert Canvas-Daten mit JSON/XML Code-Editoren:
- Canvas → JSON/XML (automatisch bei Änderungen)
- JSON/XML → Canvas (auf Anfrage/Apply)
"""

import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, Any, Optional, Callable
from datetime import datetime


class CodeSyncService:
    """Service für Canvas ↔ Code Synchronisation."""
    
    def __init__(self):
        """Initialisiert den Sync Service."""
        self._auto_sync_enabled = True
        self._on_error_callback: Optional[Callable] = None
    
    # ============================================================================
    # Canvas → Code (Export)
    # ============================================================================
    
    def canvas_to_json(self, canvas_data: Dict[str, Any], pretty: bool = True) -> str:
        """
        Konvertiert Canvas-Daten zu JSON.
        
        Args:
            canvas_data: Dictionary vom Canvas (canvas.to_dict())
            pretty: Pretty-print mit Einrückung
            
        Returns:
            JSON String
        """
        try:
            if pretty:
                return json.dumps(canvas_data, indent=2, ensure_ascii=False)
            else:
                return json.dumps(canvas_data, ensure_ascii=False)
        except Exception as e:
            self._handle_error(f"JSON Export Fehler: {e}")
            return f"{{\n  \"error\": \"JSON Export failed: {e}\"\n}}"
    
    def canvas_to_xml(self, canvas_data: Dict[str, Any], pretty: bool = True) -> str:
        """
        Konvertiert Canvas-Daten zu XML (VPB Format).
        
        Args:
            canvas_data: Dictionary vom Canvas (canvas.to_dict())
            pretty: Pretty-print mit Einrückung
            
        Returns:
            XML String
        """
        try:
            # Root Element
            root = ET.Element("vpb:process")
            root.set("xmlns:vpb", "http://uds3.org/vpb/1.0")
            root.set("version", canvas_data.get("version", "1.0"))
            
            # Metadata
            metadata = canvas_data.get("metadata", {})
            if metadata:
                meta_elem = ET.SubElement(root, "metadata")
                for key, value in metadata.items():
                    if value:
                        elem = ET.SubElement(meta_elem, key)
                        elem.text = str(value)
            
            # Elements
            elements_list = canvas_data.get("elements", [])
            if elements_list:
                elements_elem = ET.SubElement(root, "elements")
                for elem_data in elements_list:
                    elem = ET.SubElement(elements_elem, "element")
                    elem.set("id", elem_data.get("element_id", ""))
                    elem.set("type", elem_data.get("element_type", ""))
                    
                    # Position
                    pos_elem = ET.SubElement(elem, "position")
                    pos_elem.set("x", str(elem_data.get("x", 0)))
                    pos_elem.set("y", str(elem_data.get("y", 0)))
                    
                    # Name
                    if elem_data.get("name"):
                        name_elem = ET.SubElement(elem, "name")
                        name_elem.text = elem_data["name"]
                    
                    # Description
                    if elem_data.get("description"):
                        desc_elem = ET.SubElement(elem, "description")
                        desc_elem.text = elem_data["description"]
                    
                    # Optional Fields
                    optional_fields = [
                        "responsible_authority",
                        "legal_basis",
                        "deadline_days",
                        "geo_reference",
                        "ref_file"
                    ]
                    
                    for field in optional_fields:
                        value = elem_data.get(field)
                        if value:
                            field_elem = ET.SubElement(elem, field)
                            field_elem.text = str(value)
            
            # Connections
            connections_list = canvas_data.get("connections", [])
            if connections_list:
                connections_elem = ET.SubElement(root, "connections")
                for conn_data in connections_list:
                    conn = ET.SubElement(connections_elem, "connection")
                    conn.set("id", conn_data.get("connection_id", ""))
                    conn.set("type", conn_data.get("connection_type", "SEQUENCE"))
                    
                    # Source/Target können IDs oder Objekte sein
                    source = conn_data.get("source_element")
                    target = conn_data.get("target_element")
                    
                    # Extrahiere IDs
                    source_id = source if isinstance(source, str) else getattr(source, "element_id", str(source))
                    target_id = target if isinstance(target, str) else getattr(target, "element_id", str(target))
                    
                    conn.set("source", source_id)
                    conn.set("target", target_id)
                    
                    # Label
                    if conn_data.get("label"):
                        label_elem = ET.SubElement(conn, "label")
                        label_elem.text = conn_data["label"]
            
            # Convert to string
            xml_string = ET.tostring(root, encoding='unicode')
            
            # Pretty print
            if pretty:
                dom = minidom.parseString(xml_string)
                xml_string = dom.toprettyxml(indent="  ")
                # Remove extra blank lines
                lines = [line for line in xml_string.split('\n') if line.strip()]
                xml_string = '\n'.join(lines)
            
            return xml_string
            
        except Exception as e:
            self._handle_error(f"XML Export Fehler: {e}")
            return f'<?xml version="1.0"?>\n<error>XML Export failed: {e}</error>'
    
    # ============================================================================
    # Code → Canvas (Import)
    # ============================================================================
    
    def json_to_canvas(self, json_text: str) -> Optional[Dict[str, Any]]:
        """
        Konvertiert JSON zu Canvas-Daten.
        
        Args:
            json_text: JSON String
            
        Returns:
            Canvas-Dict oder None bei Fehler
        """
        try:
            data = json.loads(json_text)
            
            # Validierung
            if not isinstance(data, dict):
                raise ValueError("JSON muss ein Objekt sein")
            
            # Struktur validieren
            if "elements" not in data:
                data["elements"] = []
            if "connections" not in data:
                data["connections"] = []
            if "metadata" not in data:
                data["metadata"] = {}
            
            return data
            
        except json.JSONDecodeError as e:
            self._handle_error(f"JSON Parse Fehler: {e}")
            return None
        except Exception as e:
            self._handle_error(f"JSON Import Fehler: {e}")
            return None
    
    def xml_to_canvas(self, xml_text: str) -> Optional[Dict[str, Any]]:
        """
        Konvertiert XML (VPB Format) zu Canvas-Daten.
        
        Args:
            xml_text: XML String
            
        Returns:
            Canvas-Dict oder None bei Fehler
        """
        try:
            # Parse XML
            root = ET.fromstring(xml_text)
            
            # Initialize canvas data
            canvas_data = {
                "metadata": {},
                "elements": [],
                "connections": [],
                "version": root.get("version", "1.0")
            }
            
            # Parse Metadata
            meta_elem = root.find("metadata")
            if meta_elem is not None:
                for child in meta_elem:
                    canvas_data["metadata"][child.tag] = child.text or ""
            
            # Parse Elements
            elements_elem = root.find("elements")
            if elements_elem is not None:
                for elem in elements_elem.findall("element"):
                    elem_data = {
                        "element_id": elem.get("id", ""),
                        "element_type": elem.get("type", ""),
                    }
                    
                    # Position
                    pos = elem.find("position")
                    if pos is not None:
                        elem_data["x"] = int(pos.get("x", "0"))
                        elem_data["y"] = int(pos.get("y", "0"))
                    else:
                        elem_data["x"] = 0
                        elem_data["y"] = 0
                    
                    # Name
                    name_elem = elem.find("name")
                    elem_data["name"] = name_elem.text if name_elem is not None else ""
                    
                    # Description
                    desc_elem = elem.find("description")
                    elem_data["description"] = desc_elem.text if desc_elem is not None else ""
                    
                    # Optional Fields
                    optional_fields = [
                        "responsible_authority",
                        "legal_basis",
                        "geo_reference",
                        "ref_file"
                    ]
                    
                    for field in optional_fields:
                        field_elem = elem.find(field)
                        if field_elem is not None and field_elem.text:
                            elem_data[field] = field_elem.text
                    
                    # deadline_days (int)
                    deadline_elem = elem.find("deadline_days")
                    if deadline_elem is not None and deadline_elem.text:
                        try:
                            elem_data["deadline_days"] = int(deadline_elem.text)
                        except ValueError:
                            elem_data["deadline_days"] = None
                    
                    canvas_data["elements"].append(elem_data)
            
            # Parse Connections
            connections_elem = root.find("connections")
            if connections_elem is not None:
                for conn in connections_elem.findall("connection"):
                    conn_data = {
                        "connection_id": conn.get("id", ""),
                        "connection_type": conn.get("type", "SEQUENCE"),
                        "source_element": conn.get("source", ""),
                        "target_element": conn.get("target", ""),
                    }
                    
                    # Label
                    label_elem = conn.find("label")
                    if label_elem is not None:
                        conn_data["label"] = label_elem.text or ""
                    
                    canvas_data["connections"].append(conn_data)
            
            return canvas_data
            
        except ET.ParseError as e:
            self._handle_error(f"XML Parse Fehler: {e}")
            return None
        except Exception as e:
            self._handle_error(f"XML Import Fehler: {e}")
            return None
    
    # ============================================================================
    # Validation
    # ============================================================================
    
    def validate_json(self, json_text: str) -> tuple[bool, Optional[str]]:
        """
        Validiert JSON Text.
        
        Args:
            json_text: JSON String
            
        Returns:
            (valid, error_message)
        """
        try:
            json.loads(json_text)
            return (True, None)
        except json.JSONDecodeError as e:
            return (False, f"Zeile {e.lineno}, Spalte {e.colno}: {e.msg}")
        except Exception as e:
            return (False, str(e))
    
    def validate_xml(self, xml_text: str) -> tuple[bool, Optional[str]]:
        """
        Validiert XML Text.
        
        Args:
            xml_text: XML String
            
        Returns:
            (valid, error_message)
        """
        try:
            ET.fromstring(xml_text)
            return (True, None)
        except ET.ParseError as e:
            return (False, f"Zeile {e.position[0]}: {e.msg}")
        except Exception as e:
            return (False, str(e))
    
    # ============================================================================
    # Configuration
    # ============================================================================
    
    def set_auto_sync(self, enabled: bool):
        """Aktiviert/deaktiviert automatische Synchronisation."""
        self._auto_sync_enabled = enabled
    
    def is_auto_sync_enabled(self) -> bool:
        """Gibt zurück ob Auto-Sync aktiviert ist."""
        return self._auto_sync_enabled
    
    def set_error_callback(self, callback: Callable[[str], None]):
        """Setzt Callback für Fehler-Benachrichtigungen."""
        self._on_error_callback = callback
    
    def _handle_error(self, message: str):
        """Behandelt Fehler."""
        print(f"❌ CodeSyncService Error: {message}")
        if self._on_error_callback:
            self._on_error_callback(message)
