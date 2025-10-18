"""
UDS3 API Backend
================

Backend-Integration für UDS3 Polyglot Persistence mit VPB Process Designer.
Stellt API-Schicht zwischen Flask/FastAPI und UDS3 PolyglotManager bereit.

Autor: UDS3 Development Team
Datum: 18. Oktober 2025
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ProcessAnalysisResult:
    """Ergebnis einer Prozess-Analyse"""
    
    # Analysis Metadata
    process_id: str
    analysis_timestamp: datetime = field(default_factory=datetime.now)
    
    # Complexity Metrics
    complexity_score: float = 0.0  # 0-100
    element_count: int = 0
    connection_count: int = 0
    decision_point_count: int = 0
    
    # Quality Metrics
    completeness_score: float = 0.0  # 0-100
    consistency_score: float = 0.0   # 0-100
    
    # UDS3 Conformity
    uds3_conformity: bool = False
    uds3_violations: List[str] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    # Similarity Analysis
    similar_processes: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['analysis_timestamp'] = self.analysis_timestamp.isoformat()
        return result


@dataclass
class BackendHealth:
    """Status der Backend-Verbindungen"""
    
    postgresql_connected: bool = False
    neo4j_connected: bool = False
    chromadb_connected: bool = False
    
    postgresql_version: Optional[str] = None
    neo4j_version: Optional[str] = None
    chromadb_version: Optional[str] = None
    
    last_check: datetime = field(default_factory=datetime.now)
    
    @property
    def all_healthy(self) -> bool:
        """Alle Backends verbunden"""
        return (self.postgresql_connected and 
                self.neo4j_connected and 
                self.chromadb_connected)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['last_check'] = self.last_check.isoformat()
        result['all_healthy'] = self.all_healthy
        return result


# ============================================================================
# UDS3 API Backend
# ============================================================================

class UDS3APIBackend:
    """
    UDS3 API Backend Integration
    
    Stellt High-Level API für VPB Process Designer bereit:
    - Process Analysis (Complexity, Quality, Conformity)
    - Semantic Search via Embeddings
    - Graph Queries
    - Backend Health Monitoring
    """
    
    def __init__(self, polyglot_manager=None):
        """
        Initialisiere UDS3 API Backend
        
        Args:
            polyglot_manager: Optional UDS3PolyglotManager instance
        """
        self.polyglot_manager = polyglot_manager
        
        # Lazy import to avoid circular dependencies
        if self.polyglot_manager is None:
            try:
                from core.polyglot_manager import UDS3PolyglotManager
                self.polyglot_manager = UDS3PolyglotManager()
            except ImportError:
                logger.warning("UDS3PolyglotManager not available - running in standalone mode")
        
        logger.info("UDS3 API Backend initialized")
    
    # ========================================================================
    # Process Analysis
    # ========================================================================
    
    def analyze_process(self, process_data: Dict[str, Any]) -> ProcessAnalysisResult:
        """
        Analysiere VPB Prozess auf Komplexität, Qualität und UDS3-Konformität
        
        Args:
            process_data: VPB Process Dictionary
            
        Returns:
            ProcessAnalysisResult mit Metriken und Empfehlungen
        """
        process_id = process_data.get('process_id', 'unknown')
        
        logger.info(f"Analyzing process {process_id}")
        
        result = ProcessAnalysisResult(process_id=process_id)
        
        # Complexity Metrics
        elements = process_data.get('elements', [])
        connections = process_data.get('connections', [])
        
        result.element_count = len(elements)
        result.connection_count = len(connections)
        result.decision_point_count = sum(
            1 for e in elements 
            if e.get('type') in ['gateway', 'exclusiveGateway', 'parallelGateway']
        )
        
        # Complexity Score (0-100)
        result.complexity_score = min(100, (
            result.element_count * 2 +
            result.connection_count * 1.5 +
            result.decision_point_count * 5
        ))
        
        # Quality Metrics
        result.completeness_score = self._calculate_completeness(process_data)
        result.consistency_score = self._calculate_consistency(process_data)
        
        # UDS3 Conformity
        result.uds3_conformity, result.uds3_violations = self._check_uds3_conformity(process_data)
        
        # Recommendations
        result.recommendations = self._generate_recommendations(process_data, result)
        
        # Similar Processes (via ChromaDB)
        if self.polyglot_manager:
            result.similar_processes = self._find_similar_processes(process_data)
        
        logger.info(f"Analysis complete: complexity={result.complexity_score:.1f}, "
                   f"completeness={result.completeness_score:.1f}, "
                   f"uds3_conformity={result.uds3_conformity}")
        
        return result
    
    def _calculate_completeness(self, process_data: Dict[str, Any]) -> float:
        """Berechne Vollständigkeits-Score"""
        score = 0.0
        checks = 0
        
        # Check 1: Name vorhanden
        if process_data.get('name'):
            score += 20
        checks += 1
        
        # Check 2: Description vorhanden
        if process_data.get('description'):
            score += 15
        checks += 1
        
        # Check 3: Mindestens ein Element
        if len(process_data.get('elements', [])) > 0:
            score += 20
        checks += 1
        
        # Check 4: Start Element vorhanden
        has_start = any(
            e.get('type') in ['startEvent', 'start']
            for e in process_data.get('elements', [])
        )
        if has_start:
            score += 20
        checks += 1
        
        # Check 5: End Element vorhanden
        has_end = any(
            e.get('type') in ['endEvent', 'end']
            for e in process_data.get('elements', [])
        )
        if has_end:
            score += 25
        checks += 1
        
        return score
    
    def _calculate_consistency(self, process_data: Dict[str, Any]) -> float:
        """Berechne Konsistenz-Score"""
        score = 100.0
        violations = 0
        
        elements = process_data.get('elements', [])
        connections = process_data.get('connections', [])
        
        # Check 1: Alle Verbindungen zeigen auf existierende Elemente
        element_ids = {e.get('id') for e in elements}
        for conn in connections:
            if conn.get('from') not in element_ids:
                violations += 1
            if conn.get('to') not in element_ids:
                violations += 1
        
        # Check 2: Keine isolierten Elemente (außer Start/End)
        connected_ids = set()
        for conn in connections:
            connected_ids.add(conn.get('from'))
            connected_ids.add(conn.get('to'))
        
        for element in elements:
            e_type = element.get('type', '')
            e_id = element.get('id')
            
            if e_type not in ['startEvent', 'start', 'endEvent', 'end']:
                if e_id not in connected_ids:
                    violations += 1
        
        # Check 3: Jedes Element hat eindeutige ID
        seen_ids = set()
        for element in elements:
            e_id = element.get('id')
            if e_id in seen_ids:
                violations += 2  # Schwerer Fehler
            seen_ids.add(e_id)
        
        # Score reduzieren basierend auf Violations
        score -= violations * 10
        return max(0.0, score)
    
    def _check_uds3_conformity(self, process_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Prüfe UDS3-Konformität"""
        violations = []
        
        # UDS3 Requirements:
        # 1. Jeder Prozess braucht process_id
        if not process_data.get('process_id'):
            violations.append("Missing process_id")
        
        # 2. Mindestens ein Element
        elements = process_data.get('elements', [])
        if len(elements) == 0:
            violations.append("No elements defined")
        
        # 3. Alle Elemente brauchen type
        for element in elements:
            if not element.get('type'):
                violations.append(f"Element {element.get('id', 'unknown')} missing type")
        
        # 4. Start und End Events müssen vorhanden sein
        has_start = any(e.get('type') in ['startEvent', 'start'] for e in elements)
        has_end = any(e.get('type') in ['endEvent', 'end'] for e in elements)
        
        if not has_start:
            violations.append("No start event found")
        if not has_end:
            violations.append("No end event found")
        
        conformity = len(violations) == 0
        return conformity, violations
    
    def _generate_recommendations(self, 
                                 process_data: Dict[str, Any], 
                                 result: ProcessAnalysisResult) -> List[str]:
        """Generiere Empfehlungen"""
        recommendations = []
        
        # Complexity Recommendations
        if result.complexity_score > 75:
            recommendations.append(
                "Process is highly complex. Consider splitting into sub-processes."
            )
        
        # Completeness Recommendations
        if result.completeness_score < 50:
            recommendations.append(
                "Process definition is incomplete. Add missing name, description, or events."
            )
        
        # UDS3 Violations
        if not result.uds3_conformity:
            recommendations.append(
                f"Fix UDS3 violations: {', '.join(result.uds3_violations)}"
            )
        
        # Quality Recommendations
        if result.consistency_score < 70:
            recommendations.append(
                "Process has consistency issues. Check for broken connections or isolated elements."
            )
        
        return recommendations
    
    def _find_similar_processes(self, process_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Finde ähnliche Prozesse via Embedding Search"""
        if not self.polyglot_manager:
            return []
        
        try:
            # Generate search text from process
            search_text = f"{process_data.get('name', '')} {process_data.get('description', '')}"
            
            # Query ChromaDB
            chromadb_adapter = self.polyglot_manager.chromadb
            if chromadb_adapter and chromadb_adapter.connected:
                results = chromadb_adapter.query(search_text, n_results=5)
                return results
            
        except Exception as e:
            logger.error(f"Similar process search failed: {e}")
        
        return []
    
    # ========================================================================
    # Backend Health
    # ========================================================================
    
    def check_health(self) -> BackendHealth:
        """
        Prüfe Status aller Backend-Verbindungen
        
        Returns:
            BackendHealth mit Connection Status
        """
        health = BackendHealth()
        
        if not self.polyglot_manager:
            logger.warning("No polyglot manager available for health check")
            return health
        
        try:
            # PostgreSQL
            pg = self.polyglot_manager.postgresql
            health.postgresql_connected = pg.connected if pg else False
            
            # Neo4j
            neo4j = self.polyglot_manager.neo4j
            health.neo4j_connected = neo4j.connected if neo4j else False
            
            # ChromaDB
            chromadb = self.polyglot_manager.chromadb
            health.chromadb_connected = chromadb.connected if chromadb else False
            
            logger.info(f"Backend health: PG={health.postgresql_connected}, "
                       f"Neo4j={health.neo4j_connected}, "
                       f"ChromaDB={health.chromadb_connected}")
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
        
        return health
    
    # ========================================================================
    # Semantic Search
    # ========================================================================
    
    def semantic_search(self, query: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """
        Semantische Suche über alle Prozesse
        
        Args:
            query: Suchtext (natürliche Sprache)
            n_results: Anzahl Ergebnisse
            
        Returns:
            Liste ähnlicher Prozesse mit Scores
        """
        if not self.polyglot_manager:
            return []
        
        try:
            chromadb = self.polyglot_manager.chromadb
            if chromadb and chromadb.connected:
                results = chromadb.query(query, n_results=n_results)
                logger.info(f"Semantic search for '{query}' returned {len(results)} results")
                return results
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
        
        return []
    
    # ========================================================================
    # Graph Queries
    # ========================================================================
    
    def get_process_graph(self, process_id: str) -> Optional[Dict[str, Any]]:
        """
        Lade Process Graph aus Neo4j
        
        Args:
            process_id: VPB Process ID
            
        Returns:
            Graph Dictionary mit Nodes und Relationships
        """
        if not self.polyglot_manager:
            return None
        
        try:
            neo4j = self.polyglot_manager.neo4j
            if neo4j and neo4j.connected:
                graph = neo4j.get_process_graph(process_id)
                if graph:
                    logger.info(f"Loaded graph for process {process_id}")
                return graph
        except Exception as e:
            logger.error(f"Graph query failed: {e}")
        
        return None
