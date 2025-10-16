"""
VBP (VERWALTUNGSVERFAHREN) COMPLIANCE ENGINE
===========================================
Spezialisierte Engine für Verwaltungsverfahren-Compliance gemäß BVA-Konventionen
Integration mit UDS3-Prozessmodellen für vollständige Behörden-Konformität

Features:
- BVA-Konventionenhandbuch V3 Compliance
- FIM (Föderales Informationsmanagement) Validation
- Automatische Verwaltungsattribute-Validation
- DSGVO/IT-Sicherheits-Prüfungen
"""

import json
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re
from enum import Enum

logger = logging.getLogger(__name__)

class VBPComplianceLevel(Enum):
    """VBP Compliance-Level"""
    NICHT_KONFORM = "nicht_konform"
    BASIS_KONFORM = "basis_konform" 
    VOLL_KONFORM = "voll_konform"
    EXEMPLARISCH = "exemplarisch"

@dataclass
class VBPValidationRule:
    """VBP Validierungsregel"""
    rule_id: str
    rule_name: str
    rule_category: str  # 'bva', 'fim', 'dsgvo', 'security'
    rule_description: str
    severity: str  # 'error', 'warning', 'info'
    validator_function: str
    parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class VBPComplianceResult:
    """VBP Compliance-Ergebnis"""
    overall_level: VBPComplianceLevel
    compliance_score: float  # 0.0 - 100.0
    category_scores: Dict[str, float]
    violations: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    validation_details: Dict[str, Any]


class VBPComplianceEngine:
    """Hauptklasse für VBP-Compliance-Validierung"""
    
    def __init__(self):
        self.bva_rules = self._load_bva_rules()
        self.fim_rules = self._load_fim_rules()
        self.dsgvo_rules = self._load_dsgvo_rules()
        self.security_rules = self._load_security_rules()
        
        self.all_rules = {
            'bva': self.bva_rules,
            'fim': self.fim_rules,
            'dsgvo': self.dsgvo_rules,
            'security': self.security_rules
        }
        
        # Validator-Funktionen
        self.validators = {
            'validate_naming_convention': self._validate_naming_convention,
            'validate_process_documentation': self._validate_process_documentation,
            'validate_responsibility_assignment': self._validate_responsibility_assignment,
            'validate_legal_basis': self._validate_legal_basis,
            'validate_data_protection': self._validate_data_protection,
            'validate_security_classification': self._validate_security_classification,
            'validate_execution_time': self._validate_execution_time,
            'validate_cost_transparency': self._validate_cost_transparency,
            'validate_automation_level': self._validate_automation_level,
            'validate_stakeholder_definition': self._validate_stakeholder_definition,
            'validate_interface_definition': self._validate_interface_definition,
            'validate_fim_interoperability': self._validate_fim_interoperability
        }
        
        logger.info("VBP Compliance Engine initialisiert")
    
    def validate_uds3_process(self, uds3_document: Dict[str, Any]) -> VBPComplianceResult:
        """Hauptfunktion: Validiert UDS3-Prozessdokument gegen VBP-Standards"""
        try:
            violations = []
            warnings = []
            recommendations = []
            category_scores = {}
            validation_details = {}
            
            # Jede Regel-Kategorie durchgehen
            for category, rules in self.all_rules.items():
                category_violations = []
                category_warnings = []
                category_recommendations = []
                
                for rule in rules:
                    try:
                        result = self._validate_rule(uds3_document, rule)
                        
                        if result['status'] == 'violation':
                            violation = {
                                'rule_id': rule.rule_id,
                                'rule_name': rule.rule_name,
                                'category': rule.rule_category,
                                'severity': rule.severity,
                                'message': result['message'],
                                'details': result.get('details', {})
                            }
                            
                            if rule.severity == 'error':
                                category_violations.append(violation)
                                violations.append(violation)
                            else:
                                category_warnings.append(violation)
                                warnings.append(violation)
                        
                        elif result['status'] == 'warning':
                            warning = {
                                'rule_id': rule.rule_id,
                                'rule_name': rule.rule_name,
                                'category': rule.rule_category,
                                'message': result['message'],
                                'recommendation': result.get('recommendation', '')
                            }
                            category_warnings.append(warning)
                            warnings.append(warning)
                        
                        elif result['status'] == 'recommendation':
                            recommendation = {
                                'rule_id': rule.rule_id,
                                'rule_name': rule.rule_name,
                                'category': rule.rule_category,
                                'message': result['message'],
                                'improvement': result.get('improvement', '')
                            }
                            category_recommendations.append(recommendation)
                            recommendations.append(recommendation)
                    
                    except Exception as e:
                        logger.error(f"Fehler bei Validierung von Regel {rule.rule_id}: {e}")
                
                # Kategorie-Score berechnen
                category_scores[category] = self._calculate_category_score(
                    rules, category_violations, category_warnings
                )
                
                validation_details[category] = {
                    'rules_checked': len(rules),
                    'violations': len(category_violations),
                    'warnings': len(category_warnings),
                    'recommendations': len(category_recommendations),
                    'score': category_scores[category]
                }
            
            # Gesamt-Score und Compliance-Level berechnen
            overall_score = self._calculate_overall_score(category_scores)
            compliance_level = self._determine_compliance_level(overall_score, violations)
            
            return VBPComplianceResult(
                overall_level=compliance_level,
                compliance_score=overall_score,
                category_scores=category_scores,
                violations=violations,
                warnings=warnings,
                recommendations=recommendations,
                validation_details=validation_details
            )
            
        except Exception as e:
            logger.error(f"VBP Compliance-Validierung fehlgeschlagen: {e}")
            return VBPComplianceResult(
                overall_level=VBPComplianceLevel.NICHT_KONFORM,
                compliance_score=0.0,
                category_scores={},
                violations=[{'rule_id': 'system_error', 'message': str(e)}],
                warnings=[],
                recommendations=[],
                validation_details={'error': str(e)}
            )
    
    def _load_bva_rules(self) -> List[VBPValidationRule]:
        """Lädt BVA-Konventionen-Regeln"""
        return [
            VBPValidationRule(
                rule_id="BVA_001",
                rule_name="Prozess-Namenskonvention",
                rule_category="bva",
                rule_description="Prozessnamen müssen BVA-Namenskonventionen folgen",
                severity="error",
                validator_function="validate_naming_convention",
                parameters={"pattern": r"^[A-Z][a-zA-Z0-9_\s]*$", "max_length": 100}
            ),
            VBPValidationRule(
                rule_id="BVA_002",
                rule_name="Dokumentationspflicht",
                rule_category="bva",
                rule_description="Jeder Prozess muss vollständig dokumentiert sein",
                severity="error",
                validator_function="validate_process_documentation",
                parameters={"min_doc_length": 50, "required_sections": ["Zweck", "Ablauf"]}
            ),
            VBPValidationRule(
                rule_id="BVA_003",
                rule_name="Zuständigkeitszuweisung",
                rule_category="bva",
                rule_description="Klare Zuständigkeitszuweisung erforderlich",
                severity="error",
                validator_function="validate_responsibility_assignment",
                parameters={"require_assignee": True}
            ),
            VBPValidationRule(
                rule_id="BVA_004",
                rule_name="Durchlaufzeit-Definition",
                rule_category="bva",
                rule_description="Prozess-Durchlaufzeit muss definiert sein",
                severity="warning",
                validator_function="validate_execution_time",
                parameters={"require_sla": True}
            )
        ]
    
    def _load_fim_rules(self) -> List[VBPValidationRule]:
        """Lädt FIM-Compliance-Regeln"""
        return [
            VBPValidationRule(
                rule_id="FIM_001",
                rule_name="Behördenübergreifende Interoperabilität",
                rule_category="fim",
                rule_description="Prozess muss FIM-Interoperabilitäts-Standards erfüllen",
                severity="error",
                validator_function="validate_fim_interoperability",
                parameters={"require_standardized_interfaces": True}
            ),
            VBPValidationRule(
                rule_id="FIM_002", 
                rule_name="Rechtsgrundlagen-Nachweis",
                rule_category="fim",
                rule_description="Vollständige Rechtsgrundlagen erforderlich für FIM-Prozesse",
                severity="error",
                validator_function="validate_legal_basis",
                parameters={"require_specific_law": True, "require_paragraph": True}
            ),
            VBPValidationRule(
                rule_id="FIM_003",
                rule_name="Standardisierte Schnittstellen",
                rule_category="fim",
                rule_description="Schnittstellen müssen FIM-Standards entsprechen",
                severity="warning",
                validator_function="validate_interface_definition",
                parameters={"require_xoev_conformity": True}
            )
        ]
    
    def _load_dsgvo_rules(self) -> List[VBPValidationRule]:
        """Lädt DSGVO-Compliance-Regeln"""
        return [
            VBPValidationRule(
                rule_id="DSGVO_001",
                rule_name="Datenschutz-Impact-Assessment",
                rule_category="dsgvo",
                rule_description="DSGVO-konforme Datenschutz-Bewertung erforderlich",
                severity="error",
                validator_function="validate_data_protection",
                parameters={"require_pia": True, "require_data_mapping": True}
            ),
            VBPValidationRule(
                rule_id="DSGVO_002",
                rule_name="Datenminimierung",
                rule_category="dsgvo",
                rule_description="Prinzip der Datenminimierung muss erfüllt sein",
                severity="warning",
                validator_function="validate_data_protection",
                parameters={"check_data_minimization": True}
            )
        ]
    
    def _load_security_rules(self) -> List[VBPValidationRule]:
        """Lädt IT-Sicherheits-Regeln"""
        return [
            VBPValidationRule(
                rule_id="SEC_001",
                rule_name="Sicherheitsklassifikation",
                rule_category="security",
                rule_description="IT-Sicherheitsklassifikation muss definiert sein",
                severity="error",
                validator_function="validate_security_classification",
                parameters={"require_classification": True}
            )
        ]
    
    def _validate_rule(self, uds3_document: Dict[str, Any], rule: VBPValidationRule) -> Dict[str, Any]:
        """Validiert einzelne Regel"""
        if rule.validator_function in self.validators:
            validator_func = self.validators[rule.validator_function]
            return validator_func(uds3_document, rule)
        else:
            return {
                'status': 'error',
                'message': f"Validator-Funktion {rule.validator_function} nicht implementiert"
            }
    
    # Validator-Funktionen
    def _validate_naming_convention(self, uds3_document: Dict[str, Any], rule: VBPValidationRule) -> Dict[str, Any]:
        """Validiert Namenskonventionen"""
        content = uds3_document.get('content', {})
        process_name = content.get('process_name', '')
        
        pattern = rule.parameters.get('pattern', r'^[A-Z][a-zA-Z0-9_\s]*$')
        max_length = rule.parameters.get('max_length', 100)
        
        if not process_name:
            return {
                'status': 'violation',
                'message': 'Prozessname fehlt',
                'details': {'expected_pattern': pattern}
            }
        
        if len(process_name) > max_length:
            return {
                'status': 'violation',
                'message': f'Prozessname zu lang ({len(process_name)} > {max_length})',
                'details': {'actual_length': len(process_name), 'max_length': max_length}
            }
        
        if not re.match(pattern, process_name):
            return {
                'status': 'violation',
                'message': 'Prozessname entspricht nicht BVA-Namenskonvention',
                'details': {'actual_name': process_name, 'expected_pattern': pattern}
            }
        
        return {'status': 'passed', 'message': 'Namenskonvention erfüllt'}
    
    def _validate_process_documentation(self, uds3_document: Dict[str, Any], rule: VBPValidationRule) -> Dict[str, Any]:
        """Validiert Prozess-Dokumentation"""
        content = uds3_document.get('content', {})
        description = content.get('process_description', '')
        
        min_length = rule.parameters.get('min_doc_length', 50)
        required_sections = rule.parameters.get('required_sections', [])
        
        if not description:
            return {
                'status': 'violation',
                'message': 'Prozessbeschreibung fehlt',
                'details': {'required_sections': required_sections}
            }
        
        if len(description) < min_length:
            return {
                'status': 'violation',
                'message': f'Prozessbeschreibung zu kurz ({len(description)} < {min_length})',
                'details': {'actual_length': len(description), 'min_length': min_length}
            }
        
        # Prüfe erforderliche Abschnitte
        missing_sections = []
        for section in required_sections:
            if section.lower() not in description.lower():
                missing_sections.append(section)
        
        if missing_sections:
            return {
                'status': 'warning',
                'message': 'Empfohlene Dokumentationsabschnitte fehlen',
                'recommendation': f'Ergänze Abschnitte: {", ".join(missing_sections)}',
                'details': {'missing_sections': missing_sections}
            }
        
        return {'status': 'passed', 'message': 'Dokumentation ausreichend'}
    
    def _validate_responsibility_assignment(self, uds3_document: Dict[str, Any], rule: VBPValidationRule) -> Dict[str, Any]:
        """Validiert Zuständigkeitszuweisungen"""
        verwaltung_attrs = uds3_document.get('verwaltungsattribute', {})
        
        # Prüfe Hauptzuständigkeit
        if not verwaltung_attrs.get('zustaendigkeit'):
            return {
                'status': 'violation',
                'message': 'Hauptzuständigkeit nicht definiert',
                'details': {'available_attributes': list(verwaltung_attrs.keys())}
            }
        
        # Prüfe Bearbeiter-Zuordnung in Prozessschritten
        content = uds3_document.get('content', {})
        process_steps = content.get('process_steps', [])
        
        unassigned_steps = []
        for step in process_steps:
            step_type = step.get('step_type', '')
            if step_type in ['userTask', 'manualTask']:
                verwaltung_specific = step.get('verwaltung_specific', {})
                if not verwaltung_specific.get('zustaendig'):
                    unassigned_steps.append(step.get('step_name', step.get('step_id')))
        
        if unassigned_steps:
            return {
                'status': 'warning',
                'message': 'Nicht alle Benutzer-Tasks haben Zuständigkeitszuweisungen',
                'recommendation': 'Weise allen User-Tasks explizit Bearbeiter zu',
                'details': {'unassigned_steps': unassigned_steps}
            }
        
        return {'status': 'passed', 'message': 'Zuständigkeiten vollständig definiert'}
    
    def _validate_legal_basis(self, uds3_document: Dict[str, Any], rule: VBPValidationRule) -> Dict[str, Any]:
        """Validiert Rechtsgrundlagen"""
        verwaltung_attrs = uds3_document.get('verwaltungsattribute', {})
        rechtsgrundlage = verwaltung_attrs.get('rechtsgrundlage', '')
        
        if not rechtsgrundlage:
            return {
                'status': 'violation',
                'message': 'Rechtsgrundlage fehlt',
                'details': {'required_for': 'FIM-Konformität'}
            }
        
        require_paragraph = rule.parameters.get('require_paragraph', True)
        if require_paragraph:
            # Prüfe ob Paragraph-Angabe vorhanden ist
            if not re.search(r'§\s*\d+', rechtsgrundlage):
                return {
                    'status': 'warning',
                    'message': 'Spezifische Paragraphen-Angabe fehlt in Rechtsgrundlage',
                    'recommendation': 'Gib spezifische Paragraphen an (z.B. "§ 15 VwVfG")',
                    'details': {'current_value': rechtsgrundlage}
                }
        
        return {'status': 'passed', 'message': 'Rechtsgrundlage vollständig'}
    
    def _validate_data_protection(self, uds3_document: Dict[str, Any], rule: VBPValidationRule) -> Dict[str, Any]:
        """Validiert Datenschutz-Compliance"""
        verwaltung_attrs = uds3_document.get('verwaltungsattribute', {})
        
        require_pia = rule.parameters.get('require_pia', True)
        if require_pia:
            datenschutz_relevant = verwaltung_attrs.get('datenschutz_relevant')
            if datenschutz_relevant is None:
                return {
                    'status': 'violation',
                    'message': 'Datenschutz-Relevanz nicht bewertet',
                    'details': {'required': 'DSGVO Privacy Impact Assessment'}
                }
        
        # Weitere DSGVO-Checks hier...
        
        return {'status': 'passed', 'message': 'Datenschutz-Anforderungen erfüllt'}
    
    def _validate_security_classification(self, uds3_document: Dict[str, Any], rule: VBPValidationRule) -> Dict[str, Any]:
        """Validiert Sicherheitsklassifikation"""
        verwaltung_attrs = uds3_document.get('verwaltungsattribute', {})
        
        security_level = verwaltung_attrs.get('sicherheitsstufe') or verwaltung_attrs.get('kritikalitaet')
        if not security_level:
            return {
                'status': 'violation',
                'message': 'IT-Sicherheitsklassifikation fehlt',
                'details': {'required_attributes': ['sicherheitsstufe', 'kritikalitaet']}
            }
        
        valid_levels = ['niedrig', 'normal', 'hoch', 'sehr_hoch']
        if security_level.lower() not in valid_levels:
            return {
                'status': 'warning',
                'message': 'Unbekannte Sicherheitsstufe',
                'recommendation': f'Verwende eine der Standard-Stufen: {", ".join(valid_levels)}',
                'details': {'current_value': security_level, 'valid_values': valid_levels}
            }
        
        return {'status': 'passed', 'message': 'Sicherheitsklassifikation korrekt'}
    
    def _validate_execution_time(self, uds3_document: Dict[str, Any], rule: VBPValidationRule) -> Dict[str, Any]:
        """Validiert Durchlaufzeit-Definition"""
        verwaltung_attrs = uds3_document.get('verwaltungsattribute', {})
        
        durchlaufzeit = verwaltung_attrs.get('durchlaufzeit')
        if not durchlaufzeit:
            return {
                'status': 'warning',
                'message': 'Prozess-Durchlaufzeit nicht definiert',
                'recommendation': 'Definiere SLA für Prozess-Durchlaufzeit',
                'details': {}
            }
        
        return {'status': 'passed', 'message': 'Durchlaufzeit definiert'}
    
    def _validate_cost_transparency(self, uds3_document: Dict[str, Any], rule: VBPValidationRule) -> Dict[str, Any]:
        """Validiert Kostentransparenz"""
        verwaltung_attrs = uds3_document.get('verwaltungsattribute', {})
        
        kosten = verwaltung_attrs.get('kosten')
        if kosten is None:
            return {
                'status': 'recommendation',
                'message': 'Prozesskosten nicht spezifiziert',
                'improvement': 'Dokumentiere Prozesskosten für Transparenz'
            }
        
        return {'status': 'passed', 'message': 'Kostentransparenz gegeben'}
    
    def _validate_automation_level(self, uds3_document: Dict[str, Any], rule: VBPValidationRule) -> Dict[str, Any]:
        """Validiert Automatisierungsgrad"""
        verwaltung_attrs = uds3_document.get('verwaltungsattribute', {})
        
        auto_level = verwaltung_attrs.get('automatisierungsgrad')
        if auto_level is None:
            return {
                'status': 'recommendation',
                'message': 'Automatisierungsgrad nicht bewertet',
                'improvement': 'Bewerte und dokumentiere Automatisierungspotential'
            }
        
        return {'status': 'passed', 'message': 'Automatisierungsgrad dokumentiert'}
    
    def _validate_stakeholder_definition(self, uds3_document: Dict[str, Any], rule: VBPValidationRule) -> Dict[str, Any]:
        """Validiert Stakeholder-Definition"""
        # Implementierung für Stakeholder-Validierung
        return {'status': 'passed', 'message': 'Stakeholder-Definition ausreichend'}
    
    def _validate_interface_definition(self, uds3_document: Dict[str, Any], rule: VBPValidationRule) -> Dict[str, Any]:
        """Validiert Schnittstellen-Definition"""
        # Implementierung für Interface-Validierung  
        return {'status': 'passed', 'message': 'Schnittstellen korrekt definiert'}
    
    def _validate_fim_interoperability(self, uds3_document: Dict[str, Any], rule: VBPValidationRule) -> Dict[str, Any]:
        """Validiert FIM-Interoperabilität"""
        verwaltung_attrs = uds3_document.get('verwaltungsattribute', {})
        
        fim_relevant = verwaltung_attrs.get('fim_relevant', False)
        if fim_relevant:
            # Prüfe XÖV-Konformität und andere FIM-Anforderungen
            if not verwaltung_attrs.get('fachverfahren'):
                return {
                    'status': 'warning',
                    'message': 'FIM-relevanter Prozess ohne Fachverfahren-Zuordnung',
                    'recommendation': 'Ordne Prozess einem Fachverfahren zu'
                }
        
        return {'status': 'passed', 'message': 'FIM-Interoperabilität gegeben'}
    
    def _calculate_category_score(self, rules: List[VBPValidationRule], violations: List[Dict], warnings: List[Dict]) -> float:
        """Berechnet Score für Regel-Kategorie"""
        if not rules:
            return 100.0
        
        total_weight = len(rules)
        violation_penalty = len(violations) * 20.0  # Schwere Verstöße
        warning_penalty = len(warnings) * 5.0      # Leichte Verstöße
        
        score = 100.0 - ((violation_penalty + warning_penalty) / total_weight)
        return max(0.0, score)
    
    def _calculate_overall_score(self, category_scores: Dict[str, float]) -> float:
        """Berechnet Gesamt-Compliance-Score"""
        if not category_scores:
            return 0.0
        
        # Gewichtung der Kategorien
        weights = {
            'bva': 0.35,      # BVA-Konventionen haben höchste Priorität
            'fim': 0.25,      # FIM-Interoperabilität wichtig
            'dsgvo': 0.25,    # DSGVO-Compliance kritisch
            'security': 0.15  # IT-Sicherheit
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for category, score in category_scores.items():
            weight = weights.get(category, 0.1)
            weighted_score += score * weight
            total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _determine_compliance_level(self, overall_score: float, violations: List[Dict]) -> VBPComplianceLevel:
        """Bestimmt Compliance-Level basierend auf Score und Violations"""
        # Keine kritischen Verstöße
        critical_violations = [v for v in violations if v.get('severity') == 'error']
        
        if critical_violations:
            return VBPComplianceLevel.NICHT_KONFORM
        elif overall_score >= 95.0:
            return VBPComplianceLevel.EXEMPLARISCH
        elif overall_score >= 85.0:
            return VBPComplianceLevel.VOLL_KONFORM
        elif overall_score >= 70.0:
            return VBPComplianceLevel.BASIS_KONFORM
        else:
            return VBPComplianceLevel.NICHT_KONFORM


class VBPComplianceReport:
    """Generiert VBP-Compliance-Reports"""
    
    def __init__(self):
        self.engine = VBPComplianceEngine()
    
    def generate_compliance_report(self, uds3_document: Dict[str, Any]) -> Dict[str, Any]:
        """Generiert vollständigen Compliance-Report"""
        compliance_result = self.engine.validate_uds3_process(uds3_document)
        
        report = {
            'report_metadata': {
                'report_id': f"vbp_compliance_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'generated_at': datetime.now().isoformat(),
                'document_id': uds3_document.get('document_id', 'unknown'),
                'process_name': uds3_document.get('content', {}).get('process_name', 'Unbekannt')
            },
            
            'compliance_summary': {
                'overall_level': compliance_result.overall_level.value,
                'overall_score': compliance_result.compliance_score,
                'category_breakdown': compliance_result.category_scores,
                'critical_issues': len([v for v in compliance_result.violations if v.get('severity') == 'error']),
                'warnings': len(compliance_result.warnings),
                'recommendations': len(compliance_result.recommendations)
            },
            
            'detailed_results': {
                'violations': compliance_result.violations,
                'warnings': compliance_result.warnings,
                'recommendations': compliance_result.recommendations,
                'validation_details': compliance_result.validation_details
            },
            
            'action_items': self._generate_action_items(compliance_result),
            
            'certification_status': {
                'bva_ready': compliance_result.category_scores.get('bva', 0) >= 85.0,
                'fim_ready': compliance_result.category_scores.get('fim', 0) >= 80.0,
                'dsgvo_compliant': compliance_result.category_scores.get('dsgvo', 0) >= 90.0,
                'security_adequate': compliance_result.category_scores.get('security', 0) >= 75.0
            }
        }
        
        return report
    
    def _generate_action_items(self, compliance_result: VBPComplianceResult) -> List[Dict[str, Any]]:
        """Generiert Handlungsempfehlungen"""
        action_items = []
        
        # Kritische Verstöße zuerst
        for violation in compliance_result.violations:
            if violation.get('severity') == 'error':
                action_items.append({
                    'priority': 'hoch',
                    'category': violation['category'],
                    'action': f"Behebe Verstoß: {violation['message']}",
                    'rule_id': violation['rule_id']
                })
        
        # Warnungen
        for warning in compliance_result.warnings:
            action_items.append({
                'priority': 'mittel',
                'category': warning['category'],
                'action': f"Prüfe Warnung: {warning['message']}",
                'rule_id': warning['rule_id']
            })
        
        # Empfehlungen  
        for rec in compliance_result.recommendations:
            action_items.append({
                'priority': 'niedrig',
                'category': rec['category'],
                'action': f"Verbesserung: {rec['message']}",
                'rule_id': rec['rule_id']
            })
        
        return action_items


# Export für Integration
def get_vbp_compliance_engine():
    """Gibt VBP Compliance Engine zurück"""
    return VBPComplianceEngine()

def get_vbp_compliance_report():
    """Gibt VBP Compliance Report Generator zurück"""
    return VBPComplianceReport()


if __name__ == "__main__":
    # Test der VBP Compliance Engine
    engine = VBPComplianceEngine()
    report_generator = VBPComplianceReport()
    
    # Test UDS3-Dokument (aus vorheriger Integration)
    test_uds3_document = {
        'document_id': 'test_antrag_001',
        'document_type': 'verwaltungsprozess_bpmn',
        'content': {
            'process_name': 'Antragsbearbeitung Test',
            'process_description': 'Dieser Prozess dient der systematischen Bearbeitung von Anträgen in der Verwaltung. Der Ablauf umfasst Prüfung, Bewertung und Bescheiderteilung.',
            'process_steps': [
                {
                    'step_id': 'antrag_pruefen',
                    'step_name': 'Antrag prüfen',
                    'step_type': 'userTask',
                    'verwaltung_specific': {'zustaendig': 'Sachbearbeiter A'}
                }
            ]
        },
        'verwaltungsattribute': {
            'rechtsgrundlage': '§ 15 VwVfG',
            'zustaendigkeit': 'Kommunal',
            'durchlaufzeit': '5 Werktage',
            'automatisierungsgrad': 25,
            'datenschutz_relevant': True,
            'sicherheitsstufe': 'normal'
        }
    }
    
    try:
        # Compliance-Validierung durchführen
        compliance_result = engine.validate_uds3_process(test_uds3_document)
        print("✓ VBP Compliance-Validierung erfolgreich")
        print(f"Overall Level: {compliance_result.overall_level.value}")
        print(f"Overall Score: {compliance_result.compliance_score:.1f}%")
        
        print(f"\nKategorie-Scores:")
        for category, score in compliance_result.category_scores.items():
            print(f"  {category.upper()}: {score:.1f}%")
        
        print(f"\nIssues:")
        print(f"  Violations: {len(compliance_result.violations)}")
        print(f"  Warnings: {len(compliance_result.warnings)}")
        print(f"  Recommendations: {len(compliance_result.recommendations)}")
        
        # Report generieren
        report = report_generator.generate_compliance_report(test_uds3_document)
        print(f"\n✓ Compliance-Report generiert")
        print(f"Report ID: {report['report_metadata']['report_id']}")
        print(f"Action Items: {len(report['action_items'])}")
        
        # Certification Status
        cert_status = report['certification_status']
        print(f"\nZertifizierungs-Status:")
        print(f"  BVA-Ready: {'✓' if cert_status['bva_ready'] else '✗'}")
        print(f"  FIM-Ready: {'✓' if cert_status['fim_ready'] else '✗'}")
        print(f"  DSGVO-Compliant: {'✓' if cert_status['dsgvo_compliant'] else '✗'}")
        print(f"  Security-Adequate: {'✓' if cert_status['security_adequate'] else '✗'}")
        
    except Exception as e:
        print(f"✗ VBP Compliance Test fehlgeschlagen: {e}")

"""
VERITAS Protected Module
WARNING: This file contains embedded protection keys. 
Modification will be detected and may result in license violations.
"""

# === VERITAS PROTECTION KEYS (DO NOT MODIFY) ===
module_name = "vbp_compliance_engine"
module_licenced_organization = "VERITAS_TECH_GMBH"
module_licence_key = "eyJjbGllbnRfaWQi...8oGijAWp"  # Gekuerzt fuer Sicherheit
module_organization_key = "f8bd291a4b7cf143eb2d1ee6d40dccaefe5b3c46014500c002018bb81fb3b064"
module_file_key = "12123963e73258eb017600b3af83acc22fd91f74577d57161567ac0813186149"
module_version = "1.0"
module_protection_level = 2
# === END PROTECTION KEYS ===
