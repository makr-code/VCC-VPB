#!/usr/bin/env python3
"""
VERITAS Protected Module
WARNING: This file contains embedded protection keys. 
Modification will be detected and may result in license violations.
"""

# === VERITAS PROTECTION KEYS (DO NOT MODIFY) ===
module_name = "vpb_data_preparation"
module_licenced_organization = "VERITAS_TECH_GMBH"
module_licence_key = "eyJjbGllbnRfaWQi...TXiZug=="  # Gekuerzt fuer Sicherheit
module_organization_key = "c39be5a1bb689e68d72cda6ff7b4be80cb1aed3f69f6a704ad7342668f5e3509"
module_file_key = "b13cbea7f9a08c942c944ddf471546e43e53543c3da16d3035f212cc94b1f6f2"
module_version = "1.0"
module_protection_level = 1
# === END PROTECTION KEYS ===
"""
VPB Data Preparation for LLM Analysis
Erweiterte Datenaufbereitung für VPB-Prozesse zur Analyse durch LLMs

Konvertiert strukturierte VPB-Prozessdaten in semantisch reiche,
für LLMs optimierte Textrepräsentationen mit Kontext-Anreicherung.

Autor: UDS3 Development Team
Datum: 22. August 2025
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

# VPB Integration
from vpb_sqlite_db import VPBSQLiteDB
from uds3_vpb_schema import VPBProcessRecord

logger = logging.getLogger(__name__)

@dataclass
class VPBLLMContext:
    """Aufbereiteter VPB-Kontext für LLM-Analyse"""
    process_overview: str
    structural_analysis: str  
    legal_context: str
    compliance_points: str
    authorities_involved: str
    process_flow: str
    bottlenecks_risks: str
    optimization_potential: str
    element_details: List[Dict[str, Any]]
    connection_details: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class VPBDataPreparator:
    """Bereitet VPB-Prozessdaten für LLM-Analyse auf"""
    
    def __init__(self, db_path: str = "vpb_processes.db"):
        """Initialisiert VPB Data Preparator"""
        self.vpb_db = VPBSQLiteDB(db_path)
        self.element_type_descriptions = self._init_element_descriptions()
        self.connection_type_descriptions = self._init_connection_descriptions()
        
    def _init_element_descriptions(self) -> Dict[str, str]:
        """Initialisiert Element-Typ-Beschreibungen"""
        return {
            "start_event": "Startpunkt des Verwaltungsprozesses - meist durch Antragstellung oder Behördeninitiative ausgelöst",
            "end_event": "Abschluss des Verwaltungsprozesses - z.B. Bescheid-Zustellung, Ablehnungsbescheid",
            "task": "Bearbeitungsschritt durch Behördenmitarbeiter - umfasst Prüfung, Dokumentation, Entscheidung",
            "user_task": "Bürger-/Antragsteller-Aktivität - z.B. Unterlagen einreichen, Stellungnahme abgeben",
            "service_task": "Automatisierte Bearbeitung - z.B. System-Checks, Datenbankabfragen, E-Mail-Versand",
            "legal_checkpoint": "Rechtsprüfung - Überprüfung der rechtlichen Voraussetzungen und Zuständigkeiten",
            "decision_gateway": "Entscheidungspunkt - basierend auf Prüfung wird Prozessfortgang bestimmt",
            "parallel_gateway": "Parallelisierung - mehrere Bearbeitungsstränge werden gleichzeitig verfolgt",
            "timer_event": "Zeitbasiertes Ereignis - z.B. Fristen-Überwachung, automatische Erinnerungen",
            "message_event": "Kommunikationsereignis - z.B. Behörden-Kommunikation, Bürger-Benachrichtigung",
            "subprocess": "Unterprozess - in sich geschlossener Teilprozess mit eigenständiger Bearbeitung",
            "data_object": "Dokumentenverwaltung - z.B. Akten, Gutachten, Bescheide, digitale Dokumente",
            "annotation": "Erläuterung oder Kommentar - zusätzliche Informationen zum Prozessverständnis"
        }
    
    def _init_connection_descriptions(self) -> Dict[str, str]:
        """Initialisiert Verbindungs-Typ-Beschreibungen"""
        return {
            "sequence_flow": "Standard-Prozessfluss - normale Reihenfolge der Bearbeitung",
            "conditional_flow": "Bedingte Weiterleitung - abhängig von Prüfungsergebnis oder Entscheidung",
            "default_flow": "Standard-Weg - wird genommen wenn keine anderen Bedingungen erfüllt sind",
            "message_flow": "Kommunikationsfluss - zwischen verschiedenen Beteiligten (Behörden, Bürger)",
            "association": "Zuordnung - verbindet Elemente mit Dokumenten oder Anmerkungen",
            "parallel_split": "Aufteilung - Prozess verzweigt sich in parallele Bearbeitungsstränge",
            "parallel_join": "Zusammenführung - parallele Stränge werden wieder vereint",
            "escalation": "Eskalation - bei Problemen oder Fristen-Überschreitung",
            "approval_flow": "Genehmigungsweg - zwischen verschiedenen Entscheidungsebenen"
        }
    
    def prepare_process_for_llm(self, process_id: str, query_context: str = "") -> VPBLLMContext:
        """Bereitet VPB-Prozess für LLM-Analyse auf"""
        
        # Prozess aus Database laden
        process = self.vpb_db.load_process(process_id)
        if not process:
            raise ValueError(f"Prozess nicht gefunden: {process_id}")
        
        logger.info(f"Bereite VPB-Prozess für LLM auf: {process.name} ({len(process.elements)} Elemente)")
        
        # 1. Prozess-Überblick erstellen
        process_overview = self._create_process_overview(process)
        
        # 2. Strukturanalyse
        structural_analysis = self._create_structural_analysis(process)
        
        # 3. Rechtlicher Kontext
        legal_context = self._create_legal_context(process)
        
        # 4. Compliance-Punkte
        compliance_points = self._create_compliance_analysis(process)
        
        # 5. Beteiligte Behörden
        authorities_involved = self._create_authorities_analysis(process)
        
        # 6. Prozessfluss-Beschreibung
        process_flow = self._create_process_flow_description(process)
        
        # 7. Engpässe und Risiken
        bottlenecks_risks = self._create_bottlenecks_analysis(process)
        
        # 8. Optimierungspotential
        optimization_potential = self._create_optimization_analysis(process)
        
        # 9. Detaillierte Element-Aufbereitung
        element_details = self._prepare_element_details(process)
        
        # 10. Detaillierte Verbindungs-Aufbereitung
        connection_details = self._prepare_connection_details(process)
        
        # 11. Metadata zusammenstellen
        metadata = self._create_metadata_context(process, query_context)
        
        return VPBLLMContext(
            process_overview=process_overview,
            structural_analysis=structural_analysis,
            legal_context=legal_context,
            compliance_points=compliance_points,
            authorities_involved=authorities_involved,
            process_flow=process_flow,
            bottlenecks_risks=bottlenecks_risks,
            optimization_potential=optimization_potential,
            element_details=element_details,
            connection_details=connection_details,
            metadata=metadata
        )
    
    def _create_process_overview(self, process: VPBProcessRecord) -> str:
        """Erstellt Prozess-Überblick für LLM"""
        overview = f"=== VERWALTUNGSPROZESS ÜBERBLICK ===\n\n"
        overview += f"Prozessname: {process.name}\n"
        overview += f"Beschreibung: {process.description}\n"
        overview += f"Status: {process.status.value}\n"
        overview += f"Rechtsgebiet: {process.legal_context.value}\n"
        overview += f"Behördenebene: {process.authority_level.value}\n"
        overview += f"Zuständige Behörde: {process.responsible_authority}\n"
        overview += f"Version: {process.version}\n"
        overview += f"Letzte Aktualisierung: {process.updated_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        
        # Quantitative Übersicht
        overview += f"Prozess-Struktur:\n"
        overview += f"- {len(process.elements)} Prozesselemente\n"
        overview += f"- {len(process.connections)} Verbindungen\n"
        overview += f"- {len(process.involved_authorities)} beteiligte Behörden\n"
        overview += f"- {len(process.legal_basis)} Rechtsgrundlagen\n\n"
        
        # Intelligence Scores
        overview += f"Bewertung:\n"
        overview += f"- Komplexität: {process.complexity_score:.2f}/10\n"
        overview += f"- Automatisierungsgrad: {process.automation_score:.2f}/10\n"
        overview += f"- Compliance: {process.compliance_score:.2f}/10\n"
        overview += f"- Bürgerzufriedenheit: {process.citizen_satisfaction_score:.2f}/10\n\n"
        
        if process.tags:
            overview += f"Tags: {', '.join(process.tags)}\n\n"
        
        return overview
    
    def _create_structural_analysis(self, process: VPBProcessRecord) -> str:
        """Erstellt strukturelle Analyse für LLM"""
        analysis = f"=== STRUKTURANALYSE ===\n\n"
        
        # Element-Typ-Verteilung
        element_types = {}
        for element in process.elements:
            element_types[element.element_type] = element_types.get(element.element_type, 0) + 1
        
        analysis += f"Element-Typen im Prozess:\n"
        for elem_type, count in sorted(element_types.items()):
            description = self.element_type_descriptions.get(elem_type, "Unbekannter Elementtyp")
            analysis += f"- {elem_type} ({count}x): {description}\n"
        analysis += "\n"
        
        # Verbindungs-Typen
        connection_types = {}
        for conn in process.connections:
            conn_type = conn.connection_type or "sequence_flow"
            connection_types[conn_type] = connection_types.get(conn_type, 0) + 1
        
        analysis += f"Verbindungstypen:\n"
        for conn_type, count in sorted(connection_types.items()):
            description = self.connection_type_descriptions.get(conn_type, "Standard-Verbindung")
            analysis += f"- {conn_type} ({count}x): {description}\n"
        analysis += "\n"
        
        # Swimlanes (Verantwortlichkeiten)
        swimlanes = set()
        for element in process.elements:
            if element.swimlane:
                swimlanes.add(element.swimlane)
        
        if swimlanes:
            analysis += f"Verantwortlichkeitsbereiche (Swimlanes):\n"
            for swimlane in sorted(swimlanes):
                elements_in_lane = [e for e in process.elements if e.swimlane == swimlane]
                analysis += f"- {swimlane}: {len(elements_in_lane)} Elemente\n"
            analysis += "\n"
        
        return analysis
    
    def _create_legal_context(self, process: VPBProcessRecord) -> str:
        """Erstellt rechtlichen Kontext für LLM"""
        context = f"=== RECHTLICHER KONTEXT ===\n\n"
        
        context += f"Rechtsgebiet: {process.legal_context.value}\n"
        context += f"Behördenebene: {process.authority_level.value}\n"
        context += f"Geografischer Geltungsbereich: {process.geo_scope}\n\n"
        
        if process.legal_basis:
            context += f"Rechtsgrundlagen:\n"
            for basis in process.legal_basis:
                context += f"- {basis}\n"
            context += "\n"
        
        # Rechtliche Aspekte der Elemente
        legal_elements = [e for e in process.elements if e.legal_basis]
        if legal_elements:
            context += f"Elemente mit spezifischen Rechtsgrundlagen:\n"
            for element in legal_elements:
                context += f"- {element.name}: {element.legal_basis}\n"
            context += "\n"
        
        # Zuständigkeiten
        authorities = set()
        for element in process.elements:
            if element.competent_authority:
                authorities.add(element.competent_authority)
        
        if authorities:
            context += f"Zuständige Behörden nach Elementen:\n"
            for authority in sorted(authorities):
                elements_by_authority = [e for e in process.elements if e.competent_authority == authority]
                context += f"- {authority}: {len(elements_by_authority)} Elemente\n"
            context += "\n"
        
        return context
    
    def _create_compliance_analysis(self, process: VPBProcessRecord) -> str:
        """Erstellt Compliance-Analyse für LLM"""
        analysis = f"=== COMPLIANCE-ANALYSE ===\n\n"
        
        analysis += f"Gesamtbewertung Compliance: {process.compliance_score:.2f}/10\n\n"
        
        # Compliance-Tags
        all_compliance_tags = set()
        for element in process.elements:
            all_compliance_tags.update(element.compliance_tags)
        
        if all_compliance_tags:
            analysis += f"Identifizierte Compliance-Aspekte:\n"
            for tag in sorted(all_compliance_tags):
                elements_with_tag = [e for e in process.elements if tag in e.compliance_tags]
                analysis += f"- {tag}: {len(elements_with_tag)} Elemente betroffen\n"
            analysis += "\n"
        
        # Fristen-Analyse
        elements_with_deadlines = [e for e in process.elements if e.deadline_days and e.deadline_days > 0]
        if elements_with_deadlines:
            analysis += f"Fristen-kritische Elemente:\n"
            for element in sorted(elements_with_deadlines, key=lambda x: x.deadline_days):
                analysis += f"- {element.name}: {element.deadline_days} Tage Bearbeitungszeit\n"
            
            total_estimated_days = sum(e.deadline_days for e in elements_with_deadlines)
            analysis += f"\nGeschätzte Gesamtbearbeitungszeit: {total_estimated_days} Tage\n\n"
        
        # Risiko-Bewertung
        risk_levels = {}
        for element in process.elements:
            risk_levels[element.risk_level] = risk_levels.get(element.risk_level, 0) + 1
        
        if risk_levels:
            analysis += f"Risikobewertung der Elemente:\n"
            for risk, count in sorted(risk_levels.items()):
                analysis += f"- {risk}: {count} Elemente\n"
            analysis += "\n"
        
        return analysis
    
    def _create_authorities_analysis(self, process: VPBProcessRecord) -> str:
        """Erstellt Behörden-Analyse für LLM"""
        analysis = f"=== BETEILIGTE BEHÖRDEN ===\n\n"
        
        analysis += f"Hauptverantwortliche Behörde: {process.responsible_authority}\n\n"
        
        if process.involved_authorities:
            analysis += f"Weitere beteiligte Behörden:\n"
            for authority in process.involved_authorities:
                analysis += f"- {authority}\n"
            analysis += "\n"
        
        # Behörden nach Elementen
        authority_elements = {}
        for element in process.elements:
            if element.competent_authority:
                if element.competent_authority not in authority_elements:
                    authority_elements[element.competent_authority] = []
                authority_elements[element.competent_authority].append(element)
        
        if authority_elements:
            analysis += f"Zuständigkeitsverteilung:\n"
            for authority, elements in authority_elements.items():
                analysis += f"\n{authority}:\n"
                for element in elements:
                    analysis += f"  - {element.name} ({element.element_type})\n"
            analysis += "\n"
        
        return analysis
    
    def _create_process_flow_description(self, process: VPBProcessRecord) -> str:
        """Erstellt Prozessfluss-Beschreibung für LLM"""
        flow = f"=== PROZESSFLUSS ===\n\n"
        
        # Start-Elemente finden
        start_elements = [e for e in process.elements if e.element_type == "start_event"]
        end_elements = [e for e in process.elements if e.element_type == "end_event"]
        
        flow += f"Prozesseinstieg:\n"
        for start in start_elements:
            flow += f"- {start.name}: {start.description}\n"
        flow += "\n"
        
        flow += f"Prozessabschluss:\n"
        for end in end_elements:
            flow += f"- {end.name}: {end.description}\n"
        flow += "\n"
        
        # Entscheidungspunkte
        decision_points = [e for e in process.elements if e.element_type == "decision_gateway"]
        if decision_points:
            flow += f"Wichtige Entscheidungspunkte:\n"
            for decision in decision_points:
                flow += f"- {decision.name}: {decision.description}\n"
                # Ausgehende Verbindungen analysieren
                outgoing = [c for c in process.connections if c.source_element_id == decision.element_id]
                for conn in outgoing:
                    target_element = next((e for e in process.elements if e.element_id == conn.target_element_id), None)
                    if target_element:
                        condition_text = f" (Bedingung: {conn.condition})" if conn.condition else ""
                        flow += f"  → {target_element.name}{condition_text}\n"
            flow += "\n"
        
        # Kritischer Pfad (längste Kette)
        flow += f"Kritische Pfade und Abhängigkeiten:\n"
        # Vereinfachte Pfad-Analyse
        for element in process.elements:
            if element.element_type in ["task", "user_task", "service_task"]:
                incoming = [c for c in process.connections if c.target_element_id == element.element_id]
                outgoing = [c for c in process.connections if c.source_element_id == element.element_id]
                
                if len(incoming) > 1 or len(outgoing) > 1:
                    flow += f"- {element.name}: Konvergenz-/Divergenzpunkt mit {len(incoming)} Eingängen, {len(outgoing)} Ausgängen\n"
        
        return flow
    
    def _create_bottlenecks_analysis(self, process: VPBProcessRecord) -> str:
        """Erstellt Engpass-Analyse für LLM"""
        analysis = f"=== ENGPÄSSE UND RISIKEN ===\n\n"
        
        # Bottleneck-Indikatoren aus Verbindungen
        bottleneck_connections = [c for c in process.connections if c.bottleneck_indicator]
        if bottleneck_connections:
            analysis += f"Identifizierte Engpässe:\n"
            for conn in bottleneck_connections:
                source = next((e for e in process.elements if e.element_id == conn.source_element_id), None)
                target = next((e for e in process.elements if e.element_id == conn.target_element_id), None)
                if source and target:
                    analysis += f"- {source.name} → {target.name}"
                    if conn.average_duration_days:
                        analysis += f" (⏱️ {conn.average_duration_days} Tage Durchlaufzeit)"
                    analysis += "\n"
            analysis += "\n"
        
        # Compliance-kritische Verbindungen
        critical_connections = [c for c in process.connections if c.compliance_critical]
        if critical_connections:
            analysis += f"Compliance-kritische Übergänge:\n"
            for conn in critical_connections:
                source = next((e for e in process.elements if e.element_id == conn.source_element_id), None)
                target = next((e for e in process.elements if e.element_id == conn.target_element_id), None)
                if source and target:
                    analysis += f"- {source.name} → {target.name}\n"
            analysis += "\n"
        
        # Elemente mit hohem Risiko
        high_risk_elements = [e for e in process.elements if e.risk_level in ["high", "critical"]]
        if high_risk_elements:
            analysis += f"Hochrisiko-Elemente:\n"
            for element in high_risk_elements:
                analysis += f"- {element.name} (Risiko: {element.risk_level})\n"
                if element.deadline_days:
                    analysis += f"  ⏱️ Frist: {element.deadline_days} Tage\n"
                if element.compliance_tags:
                    analysis += f"  📋 Compliance: {', '.join(element.compliance_tags)}\n"
            analysis += "\n"
        
        # Geo-relevante Elemente (können zu Koordinationsproblemen führen)
        geo_elements = [e for e in process.elements if e.geo_relevance]
        if geo_elements:
            analysis += f"Geografisch relevante Elemente (Koordinationsrisiko):\n"
            for element in geo_elements:
                analysis += f"- {element.name}\n"
            analysis += "\n"
        
        return analysis
    
    def _create_optimization_analysis(self, process: VPBProcessRecord) -> str:
        """Erstellt Optimierungsanalyse für LLM"""
        analysis = f"=== OPTIMIERUNGSPOTENTIAL ===\n\n"
        
        analysis += f"Automatisierungsgrad: {process.automation_score:.2f}/10\n\n"
        
        # Automatisierbare Elemente identifizieren
        automatable_elements = [e for e in process.elements 
                              if e.automation_potential and e.automation_potential > 0.5]
        if automatable_elements:
            analysis += f"Elemente mit Automatisierungspotential:\n"
            for element in sorted(automatable_elements, key=lambda x: x.automation_potential, reverse=True):
                analysis += f"- {element.name}: {element.automation_potential:.1%} Automatisierungspotential\n"
                if element.element_type == "service_task":
                    analysis += f"  💡 Bereits als Service-Task konzipiert\n"
                elif element.element_type == "task":
                    analysis += f"  💡 Könnte zu Service-Task umgewandelt werden\n"
            analysis += "\n"
        
        # Service Tasks vs manuelle Tasks
        service_tasks = [e for e in process.elements if e.element_type == "service_task"]
        manual_tasks = [e for e in process.elements if e.element_type == "task"]
        
        analysis += f"Task-Verteilung:\n"
        analysis += f"- Automatisierte Service-Tasks: {len(service_tasks)}\n"
        analysis += f"- Manuelle Tasks: {len(manual_tasks)}\n"
        
        if manual_tasks:
            analysis += f"\nManuell bearbeitete Tasks:\n"
            for task in manual_tasks:
                analysis += f"- {task.name}"
                if task.automation_potential:
                    analysis += f" (Automatisierung: {task.automation_potential:.1%})"
                analysis += "\n"
        
        analysis += "\n"
        
        # Bürgerzufriedenheit-Analyse
        analysis += f"Bürgerzufriedenheit: {process.citizen_satisfaction_score:.2f}/10\n\n"
        
        citizen_impact_elements = {}
        for element in process.elements:
            impact = element.citizen_impact or "unknown"
            citizen_impact_elements[impact] = citizen_impact_elements.get(impact, 0) + 1
        
        if citizen_impact_elements:
            analysis += f"Bürgerauswirkungen:\n"
            for impact, count in sorted(citizen_impact_elements.items()):
                analysis += f"- {impact}: {count} Elemente\n"
            analysis += "\n"
        
        return analysis
    
    def _prepare_element_details(self, process: VPBProcessRecord) -> List[Dict[str, Any]]:
        """Bereitet Element-Details für LLM auf"""
        element_details = []
        
        for element in process.elements:
            detail = {
                "element_id": element.element_id,
                "name": element.name,
                "type": element.element_type,
                "type_description": self.element_type_descriptions.get(element.element_type, "Unbekannt"),
                "description": element.description,
                "position": {"x": element.x, "y": element.y},
                "competent_authority": element.competent_authority,
                "legal_basis": element.legal_basis,
                "deadline_days": element.deadline_days,
                "swimlane": element.swimlane,
                "risk_level": element.risk_level,
                "automation_potential": element.automation_potential,
                "citizen_impact": element.citizen_impact,
                "geo_relevance": element.geo_relevance,
                "compliance_tags": element.compliance_tags,
                "admin_level": element.admin_level
            }
            
            # Kontextuelle Anreicherung
            if element.deadline_days and element.deadline_days > 0:
                if element.deadline_days <= 7:
                    detail["urgency"] = "hochdringlich"
                elif element.deadline_days <= 30:
                    detail["urgency"] = "normal"
                else:
                    detail["urgency"] = "langfristig"
            
            # Verbindungen zu diesem Element
            incoming_connections = [c for c in process.connections if c.target_element_id == element.element_id]
            outgoing_connections = [c for c in process.connections if c.source_element_id == element.element_id]
            
            detail["connections"] = {
                "incoming_count": len(incoming_connections),
                "outgoing_count": len(outgoing_connections),
                "is_start_point": len(incoming_connections) == 0 and len(outgoing_connections) > 0,
                "is_end_point": len(incoming_connections) > 0 and len(outgoing_connections) == 0,
                "is_decision_point": len(outgoing_connections) > 1,
                "is_convergence_point": len(incoming_connections) > 1
            }
            
            element_details.append(detail)
        
        return element_details
    
    def _prepare_connection_details(self, process: VPBProcessRecord) -> List[Dict[str, Any]]:
        """Bereitet Verbindungs-Details für LLM auf"""
        connection_details = []
        
        for connection in process.connections:
            # Quell- und Ziel-Elemente finden
            source_element = next((e for e in process.elements if e.element_id == connection.source_element_id), None)
            target_element = next((e for e in process.elements if e.element_id == connection.target_element_id), None)
            
            detail = {
                "connection_id": connection.connection_id,
                "source_element": {
                    "id": connection.source_element_id,
                    "name": source_element.name if source_element else "Unbekannt",
                    "type": source_element.element_type if source_element else "unknown"
                },
                "target_element": {
                    "id": connection.target_element_id,
                    "name": target_element.name if target_element else "Unbekannt", 
                    "type": target_element.element_type if target_element else "unknown"
                },
                "connection_type": connection.connection_type or "sequence_flow",
                "type_description": self.connection_type_descriptions.get(
                    connection.connection_type or "sequence_flow", "Standard-Verbindung"
                ),
                "condition": connection.condition,
                "label": connection.label,
                "style": connection.style,
                "probability": connection.probability,
                "average_duration_days": connection.average_duration_days,
                "bottleneck_indicator": connection.bottleneck_indicator,
                "compliance_critical": connection.compliance_critical
            }
            
            # Kontextuelle Bewertung
            if connection.average_duration_days and connection.average_duration_days > 0:
                if connection.average_duration_days > 14:
                    detail["duration_assessment"] = "langwierig"
                elif connection.average_duration_days > 7:
                    detail["duration_assessment"] = "normal"
                else:
                    detail["duration_assessment"] = "schnell"
            
            if connection.probability and connection.probability < 1.0:
                detail["flow_likelihood"] = f"{connection.probability:.1%} Wahrscheinlichkeit"
            
            connection_details.append(detail)
        
        return connection_details
    
    def _create_metadata_context(self, process: VPBProcessRecord, query_context: str = "") -> Dict[str, Any]:
        """Erstellt Metadata-Kontext für LLM"""
        return {
            "process_id": process.process_id,
            "query_context": query_context,
            "analysis_timestamp": datetime.now().isoformat(),
            "data_quality": {
                "elements_with_descriptions": len([e for e in process.elements if e.description]),
                "elements_with_legal_basis": len([e for e in process.elements if e.legal_basis]),
                "elements_with_deadlines": len([e for e in process.elements if e.deadline_days]),
                "connections_with_conditions": len([c for c in process.connections if c.condition]),
                "completeness_score": self._calculate_completeness_score(process)
            },
            "complexity_indicators": {
                "total_elements": len(process.elements),
                "total_connections": len(process.connections),
                "decision_points": len([e for e in process.elements if e.element_type == "decision_gateway"]),
                "parallel_flows": len([e for e in process.elements if e.element_type == "parallel_gateway"]),
                "involved_authorities": len(set([e.competent_authority for e in process.elements if e.competent_authority]))
            }
        }
    
    def _calculate_completeness_score(self, process: VPBProcessRecord) -> float:
        """Berechnet Vollständigkeits-Score für Prozess"""
        total_fields = 0
        filled_fields = 0
        
        for element in process.elements:
            total_fields += 6  # Wichtige Felder pro Element
            filled_fields += sum([
                1 if element.description else 0,
                1 if element.legal_basis else 0,
                1 if element.competent_authority else 0,
                1 if element.deadline_days else 0,
                1 if element.compliance_tags else 0,
                1 if element.swimlane else 0
            ])
        
        for connection in process.connections:
            total_fields += 2
            filled_fields += sum([
                1 if connection.condition else 0,
                1 if connection.label else 0
            ])
        
        return (filled_fields / total_fields) if total_fields > 0 else 0.0
    
    def format_for_llm_prompt(self, llm_context: VPBLLMContext, query: str) -> str:
        """Formatiert aufbereiteten Kontext für LLM-Prompt"""
        
        prompt = f"""Du bist ein Experte für deutsche Verwaltungsprozesse und hilfst bei der Analyse von VPB-Prozessen (Verwaltungsprozess-Beschreibungssprache).

BENUTZERANFRAGE: {query}

PROZESS-ANALYSE-KONTEXT:

{llm_context.process_overview}

{llm_context.structural_analysis}

{llm_context.legal_context}

{llm_context.compliance_points}

{llm_context.authorities_involved}

{llm_context.process_flow}

{llm_context.bottlenecks_risks}

{llm_context.optimization_potential}

ELEMENT-DETAILS:
"""
        
        # Top 10 wichtigste Elemente hinzufügen
        sorted_elements = sorted(llm_context.element_details, 
                               key=lambda x: (x.get('deadline_days', 999), -x.get('automation_potential', 0)))[:10]
        
        for element in sorted_elements:
            prompt += f"\n{element['name']} ({element['type']}):\n"
            prompt += f"- Beschreibung: {element['description']}\n"
            if element['competent_authority']:
                prompt += f"- Zuständig: {element['competent_authority']}\n"
            if element['deadline_days']:
                prompt += f"- Bearbeitungszeit: {element['deadline_days']} Tage\n"
            if element['compliance_tags']:
                prompt += f"- Compliance: {', '.join(element['compliance_tags'])}\n"
        
        prompt += f"\n\nVERBINDUNGS-DETAILS:\n"
        
        # Wichtigste Verbindungen (Engpässe, kritische)
        important_connections = [c for c in llm_context.connection_details 
                               if c.get('bottleneck_indicator') or c.get('compliance_critical')][:5]
        
        for connection in important_connections:
            prompt += f"\n{connection['source_element']['name']} → {connection['target_element']['name']}:\n"
            if connection['condition']:
                prompt += f"- Bedingung: {connection['condition']}\n"
            if connection['average_duration_days']:
                prompt += f"- Durchlaufzeit: {connection['average_duration_days']} Tage\n"
            if connection['bottleneck_indicator']:
                prompt += f"- ⚠️ Identifizierter Engpass\n"
            if connection['compliance_critical']:
                prompt += f"- 📋 Compliance-kritisch\n"
        
        prompt += f"""

DATENQUALITÄT:
- Vollständigkeits-Score: {llm_context.metadata['data_quality']['completeness_score']:.2f}
- Elemente mit Beschreibungen: {llm_context.metadata['data_quality']['elements_with_descriptions']}
- Elemente mit Rechtsgrundlagen: {llm_context.metadata['data_quality']['elements_with_legal_basis']}

Bitte analysiere den Prozess basierend auf der Benutzeranfrage und nutze dabei die bereitgestellten strukturierten Informationen. Gib konkrete, auf den deutschen Verwaltungskontext bezogene Antworten.
"""
        
        return prompt

# Beispiel-Nutzung und Test-Funktion
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="VPB Data Preparation Test")
    parser.add_argument("--process-id", required=True, help="VPB Process ID")
    parser.add_argument("--query", default="Analysiere diesen Verwaltungsprozess", help="Test-Query")
    parser.add_argument("--db", default="vpb_processes.db", help="Database Path")
    parser.add_argument("--output", help="Output file for prepared context")
    
    args = parser.parse_args()
    
    # Logging setup
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        preparator = VPBDataPreparator(args.db)
        llm_context = preparator.prepare_process_for_llm(args.process_id, args.query)
        
        print("=== VPB DATA PREPARATION RESULT ===")
        print(f"Process: {args.process_id}")
        print(f"Query: {args.query}")
        print()
        
        # Formatierter LLM-Prompt
        formatted_prompt = preparator.format_for_llm_prompt(llm_context, args.query)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(formatted_prompt)
            print(f"✅ Formatted context written to: {args.output}")
        else:
            print("=== FORMATTED LLM PROMPT ===")
            print(formatted_prompt)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        logging.exception("VPB Data Preparation failed")
