#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
VPB PROCESS DESIGNER CONFIGURATION
===================================
Zentrale Konfigurationsdatei für den VPB Process Designer

Enthält:
- Pfad-Konfigurationen (Templates, Export, Logs)
- UDS3/VBP-Integration-Settings
- Verwaltungsrecht-Standards
- UI/UX-Konfigurationen
- Export-Format-Einstellungen
- Compliance-Parameter

Autor: UDS3 Development Team
Datum: 26. August 2025
Version: 1.0
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
import logging

# === VPB APPLICATION VERSION ===

VPB_VERSION = "0.3.0"
VPB_VERSION_NAME = "SPS Complete"
VPB_RELEASE_DATE = "2025-10-18"

# === PFAD-KONFIGURATIONEN ===

# Basis-Verzeichnisse
BASE_DIR = Path(__file__).parent.absolute()
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"
EXPORT_DIR = BASE_DIR / "exports"
LOGS_DIR = BASE_DIR / "logs"
TEMP_DIR = BASE_DIR / "temp"

# Automatische Verzeichnis-Erstellung
for directory in [DATA_DIR, TEMPLATES_DIR, EXPORT_DIR, LOGS_DIR, TEMP_DIR]:
    directory.mkdir(exist_ok=True)

# Template-Kategorien
TEMPLATE_CATEGORIES = {
    "antragsprozesse": TEMPLATES_DIR / "antragsprozesse",
    "genehmigungsverfahren": TEMPLATES_DIR / "genehmigungsverfahren", 
    "bescheiderteilung": TEMPLATES_DIR / "bescheiderteilung",
    "widerspruchsverfahren": TEMPLATES_DIR / "widerspruchsverfahren",
    "kommunalverfahren": TEMPLATES_DIR / "kommunalverfahren",
    "landesverfahren": TEMPLATES_DIR / "landesverfahren",
    "bundesverfahren": TEMPLATES_DIR / "bundesverfahren",
    "sozialverfahren": TEMPLATES_DIR / "sozialverfahren",
    "steuerverfahren": TEMPLATES_DIR / "steuerverfahren",
    "umweltverfahren": TEMPLATES_DIR / "umweltverfahren",
    "bauverfahren": TEMPLATES_DIR / "bauverfahren",
    "verkehrsverfahren": TEMPLATES_DIR / "verkehrsverfahren",
    "geodatenverfahren": TEMPLATES_DIR / "geodatenverfahren",
    "digitale_services": TEMPLATES_DIR / "digitale_services"
}

# Template-Verzeichnisse erstellen
for category_dir in TEMPLATE_CATEGORIES.values():
    category_dir.mkdir(exist_ok=True)

# === UDS3/VBP-INTEGRATION-SETTINGS ===

@dataclass
class UDS3Config:
    """UDS3-System-Konfiguration"""
    version: str = "3.0"
    namespace: str = "http://www.verwaltung.de/uds3/v1"
    document_type_bpmn: str = "verwaltungsprozess_bpmn"
    document_type_epk: str = "verwaltungsprozess_epk"
    encoding: str = "UTF-8"
    
    # Parser-Einstellungen
    enable_bpmn_parser: bool = True
    enable_epk_parser: bool = True
    enable_export_engine: bool = True
    
    # Integration-Einstellungen
    enable_thread_coordinator: bool = True
    max_workers: int = 4
    task_timeout: int = 300  # Sekunden
    
    # Validierung-Einstellungen
    strict_validation: bool = True
    enable_compliance_check: bool = True

@dataclass
class VBPConfig:
    """VBP-Compliance-Konfiguration"""
    version: str = "1.0"
    
    # Compliance-Level
    min_compliance_score: float = 80.0
    exemplary_threshold: float = 95.0
    good_threshold: float = 85.0
    sufficient_threshold: float = 70.0
    
    # BVA/FIM-Standards
    require_bva_compliance: bool = True
    require_fim_compliance: bool = True
    require_dsgvo_compliance: bool = True
    
    # Validierung-Optionen
    check_rechtsgrundlagen: bool = True
    check_zustaendigkeiten: bool = True
    check_fristen: bool = True
    check_verfahrensrecht: bool = True
    check_datenschutz: bool = True

# Globale Instanzen
UDS3_CONFIG = UDS3Config()
VBP_CONFIG = VBPConfig()

# === VERWALTUNGSRECHT-STANDARDS ===

class VerwaltungsEbene(Enum):
    """Verwaltungsebenen der deutschen Verwaltung"""
    BUND = ("BUND", "Bundesverwaltung", 1)
    LAND = ("LAND", "Landesverwaltung", 2)
    REGIERUNGSBEZIRK = ("REG_BEZ", "Regierungsbezirk", 3)
    LANDKREIS = ("LANDKREIS", "Landkreis", 4)
    GEMEINDE = ("GEMEINDE", "Gemeinde", 5)
    ORTSCHAFT = ("ORTSCHAFT", "Ortschaft", 6)
    
    def __init__(self, code, display_name, level):
        self.code = code
        self.display_name = display_name
        self.level = level

class RechtsgebietKategorie(Enum):
    """Kategorien der deutschen Rechtsgebiete"""
    VERWALTUNGSRECHT = ("VwR", "Verwaltungsrecht")
    SOZIALRECHT = ("SozR", "Sozialrecht")  
    STEUERRECHT = ("StR", "Steuerrecht")
    UMWELTRECHT = ("UmwR", "Umweltrecht")
    BAURECHT = ("BauR", "Baurecht")
    VERKEHRSRECHT = ("VerkR", "Verkehrsrecht")
    KOMMUNALRECHT = ("KommR", "Kommunalrecht")
    EUROPARECHT = ("EuR", "Europarecht")
    VERFASSUNGSRECHT = ("VerfR", "Verfassungsrecht")
    DATENSCHUTZRECHT = ("DSR", "Datenschutzrecht")
    
    def __init__(self, code, display_name):
        self.code = code
        self.display_name = display_name

# Häufige Rechtsgrundlagen
STANDARD_RECHTSGRUNDLAGEN = {
    "VwVfG": {
        "titel": "Verwaltungsverfahrensgesetz",
        "paragraphen": {
            "§ 9 VwVfG": "Zuständigkeit",
            "§ 10 VwVfG": "Örtliche Zuständigkeit", 
            "§ 28 VwVfG": "Anhörung",
            "§ 29 VwVfG": "Akteneinsicht",
            "§ 35 VwVfG": "Verwaltungsakt",
            "§ 39 VwVfG": "Wirksamkeit des Verwaltungsakts",
            "§ 40 VwVfG": "Nichtige Verwaltungsakte",
            "§ 41 VwVfG": "Heilung von Verfahrens- und Formfehlern"
        }
    },
    "VwGO": {
        "titel": "Verwaltungsgerichtsordnung",
        "paragraphen": {
            "§ 68 VwGO": "Widerspruchsverfahren",
            "§ 70 VwGO": "Widerspruchsfrist",
            "§ 75 VwGO": "Widerspruchsbescheid"
        }
    },
    "BauGB": {
        "titel": "Baugesetzbuch",
        "paragraphen": {
            "§ 29 BauGB": "Zulässigkeit von Vorhaben",
            "§ 30 BauGB": "Im Zusammenhang bebaute Ortsteile",
            "§ 35 BauGB": "Bauen im Außenbereich"
        }
    },
    "BImSchG": {
        "titel": "Bundes-Immissionsschutzgesetz",
        "paragraphen": {
            "§ 4 BImSchG": "Genehmigungspflicht",
            "§ 6 BImSchG": "Genehmigungsverfahren",
            "§ 10 BImSchG": "Genehmigungsvoraussetzungen"
        }
    }
}

# === UI/UX-KONFIGURATIONEN ===

@dataclass 
class UIConfig:
    """UI/UX-Konfiguration"""
    # Hauptfenster
    window_title: str = "🔄 VPB Process Designer - Verwaltungsprozess-Modellierung"
    window_width: int = 1400
    window_height: int = 900
    min_width: int = 1200
    min_height: int = 800
    
    # Farb-Schema
    primary_color: str = "#2E86AB"
    secondary_color: str = "#A23B72"
    success_color: str = "#28A745"
    warning_color: str = "#F18F01"
    danger_color: str = "#C73E1D"
    light_color: str = "#F8F9FA"
    dark_color: str = "#343A40"
    muted_color: str = "#6C757D"
    
    # Canvas-Einstellungen
    canvas_bg_color: str = "white"
    canvas_width: int = 2000
    canvas_height: int = 2000
    
    # Grid-System
    grid_enabled: bool = True
    grid_size: int = 20
    grid_visible: bool = True
    snap_to_grid: bool = True
    grid_color: str = "#E8E8E8"
    
    # Zoom-Einstellungen
    min_zoom: float = 0.1
    max_zoom: float = 5.0
    zoom_step: float = 0.1
    
    # Font-Einstellungen
    default_font: str = "Segoe UI"
    default_font_size: int = 10
    header_font_size: int = 14
    code_font: str = "Consolas"

UI_CONFIG = UIConfig()

# === EXPORT-FORMAT-EINSTELLUNGEN ===

@dataclass
class ExportConfig:
    """Export-Konfiguration"""
    # Standard-Formate
    supported_formats: List[str] = None
    default_export_format: str = "bpmn"
    
    # Datei-Erweiterungen
    file_extensions: Dict[str, str] = None
    
    # Export-Qualität
    xml_indent: str = "  "  # 2 Spaces
    xml_encoding: str = "UTF-8"
    include_metadata: bool = True
    include_verwaltungsattribute: bool = True
    include_compliance_info: bool = True
    
    # PDF-Export (zukünftig)
    pdf_page_size: str = "A4"
    pdf_orientation: str = "landscape"
    
    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = ["bpmn", "eepk", "xml", "json", "md", "csv"]
            
        if self.file_extensions is None:
            self.file_extensions = {
                "bpmn": ".bpmn",
                "eepk": ".eepk", 
                "xml": ".xml",
                "json": ".json",
                "markdown": ".md",
                "csv": ".csv",
                "pdf": ".pdf"
            }

EXPORT_CONFIG = ExportConfig()

# === LOGGING-KONFIGURATION ===

@dataclass
class LoggingConfig:
    """Logging-Konfiguration"""
    # Log-Level
    console_level: str = "INFO"
    file_level: str = "DEBUG"
    
    # Log-Dateien
    main_log_file: str = str(LOGS_DIR / "vpb_process_designer.log")
    error_log_file: str = str(LOGS_DIR / "vpb_errors.log")
    uds3_log_file: str = str(LOGS_DIR / "uds3_integration.log")
    vbp_log_file: str = str(LOGS_DIR / "vbp_compliance.log")
    
    # Log-Format
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    
    # Log-Rotation
    max_file_size: int = 10 * 1024 * 1024  # 10 MB
    backup_count: int = 5

LOGGING_CONFIG = LoggingConfig()

# === TEMPLATE-KONFIGURATIONEN ===

@dataclass
class TemplateInfo:
    """Template-Informationen"""
    name: str
    category: str
    description: str
    rechtsgrundlage: str
    verwaltungsebene: VerwaltungsEbene
    rechtsgebiet: RechtsgebietKategorie
    complexity_level: int  # 1-5
    estimated_duration: str  # z.B. "2-4 Wochen"
    required_documents: List[str]
    file_path: Path
    preview_image: Optional[Path] = None
    
    # UDS3-Metadaten
    uds3_compatible: bool = True
    vbp_compliant: bool = True
    includes_geo_context: bool = False

# Standard-Template-Definitionen (XML-basiert)
STANDARD_TEMPLATES = [
    TemplateInfo(
        name="Bauantrag Einfamilienhaus",
        category="bauverfahren",
        description="Standard-Bauantragsverfahren für Einfamilienhäuser nach BauO",
        rechtsgrundlage="§ 63 BauO NRW, § 29 BauGB",
        verwaltungsebene=VerwaltungsEbene.GEMEINDE,
        rechtsgebiet=RechtsgebietKategorie.BAURECHT,
        complexity_level=3,
        estimated_duration="8-12 Wochen", 
        required_documents=["Bauzeichnungen", "Lageplan", "Baubeschreibung"],
        file_path=TEMPLATE_CATEGORIES["bauverfahren"] / "bauantrag_efh.bpmn",
        includes_geo_context=True
    ),
    TemplateInfo(
        name="Sozialleistungsantrag",
        category="sozialverfahren", 
        description="Allgemeiner Antragsprozess für Sozialleistungen nach SGB",
        rechtsgrundlage="§ 13 SGB I, § 16 SGB II",
        verwaltungsebene=VerwaltungsEbene.LANDKREIS,
        rechtsgebiet=RechtsgebietKategorie.SOZIALRECHT,
        complexity_level=2,
        estimated_duration="4-6 Wochen",
        required_documents=["Antragsformular", "Einkommensnachweise", "Personalausweis"],
        file_path=TEMPLATE_CATEGORIES["sozialverfahren"] / "sozialleistung_antrag.bpmn"
    ),
    TemplateInfo(
        name="Gewerbeanmeldung",
        category="antragsprozesse",
        description="Anmeldung eines Gewerbebetriebs nach GewO",
        rechtsgrundlage="§ 14 GewO",
        verwaltungsebene=VerwaltungsEbene.GEMEINDE,
        rechtsgebiet=RechtsgebietKategorie.VERWALTUNGSRECHT,
        complexity_level=1,
        estimated_duration="1-2 Wochen",
        required_documents=["Gewerbeanmeldung", "Personalausweis", "ggf. Handelsregisterauszug"],
        file_path=TEMPLATE_CATEGORIES["antragsprozesse"] / "gewerbeanmeldung.bpmn"
    ),
    TemplateInfo(
        name="Umweltgenehmigung Industrie",
        category="umweltverfahren",
        description="Genehmigungsverfahren für industrielle Anlagen nach BImSchG", 
        rechtsgrundlage="§ 4 BImSchG, 4. BImSchV",
        verwaltungsebene=VerwaltungsEbene.LAND,
        rechtsgebiet=RechtsgebietKategorie.UMWELTRECHT,
        complexity_level=5,
        estimated_duration="6-12 Monate",
        required_documents=["Genehmigungsantrag", "UVP-Bericht", "Technische Unterlagen"],
        file_path=TEMPLATE_CATEGORIES["umweltverfahren"] / "umweltgenehmigung_industrie.bpmn",
        includes_geo_context=True
    ),
    TemplateInfo(
        name="Widerspruchsverfahren Standard", 
        category="widerspruchsverfahren",
        description="Standard-Widerspruchsverfahren nach VwGO",
        rechtsgrundlage="§ 68 ff. VwGO",
        verwaltungsebene=VerwaltungsEbene.LANDKREIS,
        rechtsgebiet=RechtsgebietKategorie.VERWALTUNGSRECHT,
        complexity_level=3,
        estimated_duration="3-6 Monate",
        required_documents=["Widerspruchsschrift", "Ursprünglicher Bescheid", "Begründung"],
        file_path=TEMPLATE_CATEGORIES["widerspruchsverfahren"] / "widerspruch_standard.bpmn"
    ),
    TemplateInfo(
        name="Baubescheid Erteilung",
        category="bescheiderteilung",
        description="Prozess zur Erteilung von Baubescheiden mit Rechtsmittelbelehrung",
        rechtsgrundlage="§ 72 BauO NRW, § 39 VwVfG",
        verwaltungsebene=VerwaltungsEbene.GEMEINDE,
        rechtsgebiet=RechtsgebietKategorie.BAURECHT,
        complexity_level=2,
        estimated_duration="2-4 Wochen",
        required_documents=["Bescheidtext", "Rechtsgrundlagen", "Rechtsmittelbelehrung"],
        file_path=TEMPLATE_CATEGORIES["bescheiderteilung"] / "baubescheid_erteilung.bpmn",
        includes_geo_context=True
    ),
    TemplateInfo(
        name="eEPK Antragsverfahren",
        category="antragsprozesse",
        description="Ereignisgesteuerte Prozesskette für allgemeine Antragsverfahren",
        rechtsgrundlage="§ 35 VwVfG",
        verwaltungsebene=VerwaltungsEbene.LANDKREIS,
        rechtsgebiet=RechtsgebietKategorie.VERWALTUNGSRECHT,
        complexity_level=2,
        estimated_duration="3-5 Wochen",
        required_documents=["Antragsformular", "Nachweise", "Identitätsdokumentation"],
        file_path=TEMPLATE_CATEGORIES["antragsprozesse"] / "allgemeiner_antrag.eepk"
    )
]

# === COMPLIANCE-PARAMETER ===

@dataclass
class ComplianceRules:
    """VBP-Compliance-Regeln"""
    # Mindestanforderungen
    min_start_events: int = 1
    max_start_events: int = 3
    min_end_events: int = 1
    max_end_events: int = 5
    
    # Strukturelle Anforderungen
    require_rechtsgrundlage: bool = True
    require_zustaendigkeit: bool = True
    require_fristen: bool = False  # Optional für einfache Prozesse
    
    # Verwaltungsrecht-Spezifisch
    require_anhoerung: bool = False  # Für förmliche Verfahren
    require_akteneinsicht: bool = False  # Bei Antragstellerrechten
    require_rechtsbehelfsbelehrung: bool = True
    
    # Dokumentation
    min_description_length: int = 20
    require_element_descriptions: bool = False  # Optional
    
    # Geo-Kontext
    geo_processes_require_coordinates: bool = True
    geo_processes_require_admin_level: bool = True

COMPLIANCE_RULES = ComplianceRules()

# === HILFSFUNKTIONEN ===

def get_template_by_category(category: str) -> List[TemplateInfo]:
    """Gibt alle Templates einer Kategorie zurück"""
    return [t for t in STANDARD_TEMPLATES if t.category == category]

def get_template_by_complexity(max_level: int = 3) -> List[TemplateInfo]:
    """Gibt Templates bis zu einem bestimmten Komplexitätslevel zurück"""
    return [t for t in STANDARD_TEMPLATES if t.complexity_level <= max_level]

def get_template_by_verwaltungsebene(ebene: VerwaltungsEbene) -> List[TemplateInfo]:
    """Gibt Templates für eine bestimmte Verwaltungsebene zurück"""
    return [t for t in STANDARD_TEMPLATES if t.verwaltungsebene == ebene]

def get_rechtsgrundlage_by_gebiet(rechtsgebiet: RechtsgebietKategorie) -> Dict[str, Any]:
    """Gibt relevante Rechtsgrundlagen für ein Rechtsgebiet zurück"""
    mapping = {
        RechtsgebietKategorie.VERWALTUNGSRECHT: ["VwVfG", "VwGO"],
        RechtsgebietKategorie.BAURECHT: ["BauGB", "BauO"],
        RechtsgebietKategorie.UMWELTRECHT: ["BImSchG", "BNatSchG"], 
        RechtsgebietKategorie.SOZIALRECHT: ["SGB I", "SGB II", "SGB XII"]
    }
    
    relevant_gesetze = mapping.get(rechtsgebiet, [])
    return {gesetz: STANDARD_RECHTSGRUNDLAGEN.get(gesetz, {}) for gesetz in relevant_gesetze}

def setup_logging():
    """Konfiguriert das Logging-System"""
    
    # Hauptlogger konfigurieren
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, LOGGING_CONFIG.file_level))
    
    # Formatter
    formatter = logging.Formatter(
        LOGGING_CONFIG.log_format, 
        LOGGING_CONFIG.date_format
    )
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, LOGGING_CONFIG.console_level))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    file_handler = logging.FileHandler(LOGGING_CONFIG.main_log_file, encoding='utf-8')
    file_handler.setLevel(getattr(logging, LOGGING_CONFIG.file_level))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

def validate_config():
    """Validiert die Konfiguration"""
    errors = []
    
    # Verzeichnisse prüfen
    if not TEMPLATES_DIR.exists():
        errors.append(f"Templates-Verzeichnis fehlt: {TEMPLATES_DIR}")
    
    # UDS3-Konfiguration prüfen
    if UDS3_CONFIG.max_workers < 1:
        errors.append("UDS3_CONFIG.max_workers muss mindestens 1 sein")
    
    # VBP-Konfiguration prüfen
    if not (0 <= VBP_CONFIG.min_compliance_score <= 100):
        errors.append("VBP_CONFIG.min_compliance_score muss zwischen 0 und 100 liegen")
    
    return errors

# === MODUL-INITIALISIERUNG ===

if __name__ == "__main__":
    # Konfiguration validieren
    config_errors = validate_config()
    if config_errors:
        print("⚠️ Konfigurationsfehler:")
        for error in config_errors:
            print(f"  - {error}")
    else:
        print("✅ VPB-Konfiguration erfolgreich validiert")
    
    # Verzeichnisse anzeigen
    print(f"\n📁 Verzeichnisstruktur:")
    print(f"  Templates: {TEMPLATES_DIR}")
    print(f"  Exports: {EXPORT_DIR}")
    print(f"  Logs: {LOGS_DIR}")
    
    # Template-Übersicht
    print(f"\n📋 Verfügbare Templates: {len(STANDARD_TEMPLATES)}")
    for template in STANDARD_TEMPLATES:
        print(f"  - {template.name} ({template.category}, Level {template.complexity_level})")
