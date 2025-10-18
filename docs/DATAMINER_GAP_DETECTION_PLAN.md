# RAG DataMiner & Gap Detection VPB - Integration Plan

**Datum:** 18. Oktober 2025  
**Version:** 1.0  
**Autor:** VPB Integration Team  
**Status:** 🟡 Planning  

---

## 📋 Executive Summary

Dieses Dokument beschreibt die **Brücke** zwischen:
- **UDS3 RAG System** (Polyglot Persistence + LLM)
- **VPB Process Designer** (Verwaltungsprozess-Beschreibungssprache)
- **Covina Gap Detection** (Prozess-Analyse & Optimierung)

**Ziel:** Automatische Prozess-Extraktion aus Dokumenten + Intelligente Gap-Detection für bestehende Prozesse.

---

## 🏗️ Architektur-Übersicht

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOKUMENTE & DATENQUELLEN                     │
│  • Verwaltungshandbücher (PDFs)                                 │
│  • Gesetze & Verordnungen                                       │
│  • Behörden-Websites                                            │
│  • Bestehende VPB-Prozesse                                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
    ┌────────────────────┴────────────────────┐
    │                                         │
┌───▼─────────────────────────┐   ┌──────────▼────────────────────┐
│   RAG DATAMINER VPB         │   │   GAP DETECTION VPB           │
│   =====================     │   │   ===================         │
│                             │   │                               │
│  1. Document Ingestion      │   │  1. Process Analysis          │
│     └→ PDF/Text Extraction  │   │     └→ Graph Traversal        │
│                             │   │                               │
│  2. Semantic Chunking       │   │  2. Gap Identification        │
│     └→ UDS3 RAG Retrieval   │   │     └→ Missing Steps          │
│                             │   │     └→ Redundant Elements     │
│  3. LLM Process Extraction  │   │     └→ Compliance Gaps        │
│     └→ VPB Schema Mapping   │   │                               │
│     └→ 23 Element Types     │   │  3. Optimization Suggestions  │
│     └→ Connections          │   │     └→ LLM-generiert          │
│     └→ Authorities          │   │     └→ Best Practices         │
│                             │   │                               │
│  4. Validation              │   │  4. Similarity Detection      │
│     └→ VPB Compliance       │   │     └→ Vector Search          │
│     └→ Schema Check         │   │     └→ Variant Merging        │
│                             │   │                               │
│  5. UDS3 Persistence        │   │  5. Report Generation         │
│     └→ Polyglot DB          │   │     └→ Visualisierung         │
│                             │   │     └→ Actionable Items       │
└─────────────┬───────────────┘   └──────────┬────────────────────┘
              │                              │
              └──────────────┬───────────────┘
                             │
              ┌──────────────▼──────────────┐
              │   UDS3 POLYGLOT SYSTEM      │
              │  • Vector DB (Embeddings)   │
              │  • Graph DB (Relationships) │
              │  • Relational DB (Details)  │
              │  • File Backend (Documents) │
              └──────────────┬──────────────┘
                             │
              ┌──────────────▼──────────────┐
              │   VPB PROCESS DESIGNER      │
              │  • Visual Editor            │
              │  • 23 Element Types         │
              │  • Export/Import            │
              └─────────────────────────────┘
```

---

## 🛠️ Komponente 1: RAG DataMiner VPB

### 1.1 Ziel

**Automatische Extraktion** von VPB-Prozessen aus unstrukturierten Dokumenten.

**Input:**
- PDFs (Verwaltungshandbücher, Leitfäden)
- Gesetzestexte (VwVfG, BauGB, etc.)
- Behörden-Websites (HTML)
- Word-Dokumente (Prozessbeschreibungen)

**Output:**
- VPB-konforme Prozess-Definitionen
- JSON/XML Export für VPB Designer
- Direkt in UDS3 Polyglot gespeichert

### 1.2 Pipeline-Architektur

```python
# dataminer_vpb.py - Orchestrator

class DataMinerVPB:
    """
    RAG-basierte Prozess-Extraktion aus Dokumenten
    
    Pipeline: Document → RAG → LLM → VPB Schema → UDS3
    """
    
    def __init__(self, uds3_manager, rag_pipeline, llm_client):
        self.uds3 = uds3_manager
        self.rag = rag_pipeline
        self.llm = llm_client
        self.extractor = ProcessExtractor(llm_client)
        self.mapper = VPBSchemaMapper()
        self.validator = VPBValidationEngine()
    
    def extract_process_from_document(
        self, 
        document_path: str,
        document_type: str = "verwaltungshandbuch"
    ) -> Dict[str, Any]:
        """
        Hauptpipeline: Dokument → VPB-Prozess
        
        Args:
            document_path: Pfad zum Dokument
            document_type: Dokumenttyp für Context
        
        Returns:
            VPB Process Dictionary
        """
        # 1. Document Ingestion
        text = self._ingest_document(document_path)
        
        # 2. Semantic Chunking (für lange Dokumente)
        chunks = self._chunk_document(text, max_chunk_size=2000)
        
        # 3. RAG Retrieval: Relevante Kontext-Informationen
        context = self._retrieve_context(chunks, document_type)
        
        # 4. LLM Process Extraction
        raw_process = self.extractor.extract_process(
            text=text,
            context=context,
            document_type=document_type
        )
        
        # 5. VPB Schema Mapping
        vpb_process = self.mapper.map_to_vpb_schema(raw_process)
        
        # 6. Validation
        validation_result = self.validator.validate(vpb_process)
        if not validation_result.is_valid:
            # Iterative Refinement
            vpb_process = self._refine_process(vpb_process, validation_result)
        
        # 7. UDS3 Persistence
        process_id = self.uds3.save_process(vpb_process, domain="vpb")
        
        return {
            "process_id": process_id,
            "vpb_process": vpb_process,
            "validation": validation_result,
            "source_document": document_path
        }
```

### 1.3 Komponenten

#### 1.3.1 Document Ingestion

```python
# document_ingestion.py

class DocumentIngestion:
    """Multi-Format Document Parser"""
    
    def ingest_pdf(self, path: str) -> str:
        """PDF → Text mit Layout-Erhaltung"""
        # PyMuPDF oder pdfplumber
        pass
    
    def ingest_html(self, url: str) -> str:
        """Website → strukturierter Text"""
        # BeautifulSoup + Trafilatura
        pass
    
    def ingest_word(self, path: str) -> str:
        """DOCX → Text mit Formatierung"""
        # python-docx
        pass
    
    def ingest_law(self, law_id: str) -> str:
        """Gesetz aus UDS3 Rechtsdatenbank"""
        # UDS3 Legal DB Query
        pass
```

#### 1.3.2 Process Extractor (LLM Prompts)

```python
# process_extractor.py

class ProcessExtractor:
    """LLM-basierte Prozess-Extraktion"""
    
    PROCESS_EXTRACTION_PROMPT = """
Du bist ein Experte für deutsche Verwaltungsprozesse. Extrahiere aus folgendem 
Text einen strukturierten Verwaltungsprozess.

=== DOKUMENT ===
{document_text}

=== KONTEXT (aus RAG) ===
{rag_context}

=== AUFGABE ===
Extrahiere:
1. Prozessname
2. Beschreibung (2-3 Sätze)
3. Zuständige Behörde
4. Rechtsgrundlagen (Gesetze, §§)
5. Prozessschritte mit:
   - Schritt-Name
   - Schritt-Typ (Ereignis, Aufgabe, Entscheidung, etc.)
   - Verantwortliche Stelle
   - Frist/Deadline (falls vorhanden)
   - Dokumente (Input/Output)
   - Bedingungen für Verzweigungen

=== AUSGABE-FORMAT ===
JSON mit folgendem Schema:
{{
  "name": "...",
  "description": "...",
  "authority": "...",
  "legal_basis": ["VwVfG § 28", "..."],
  "steps": [
    {{
      "name": "...",
      "type": "start_event|task_user|decision|...",
      "authority": "...",
      "deadline_days": 14,
      "documents": ["Antrag", "..."],
      "condition": "falls X dann Y"
    }}
  ],
  "connections": [
    {{
      "from": "step_1",
      "to": "step_2",
      "condition": "..."
    }}
  ]
}}

Antworte NUR mit gültigem JSON.
"""
    
    def extract_process(
        self, 
        text: str, 
        context: str,
        document_type: str
    ) -> Dict[str, Any]:
        """
        LLM-basierte Extraktion
        
        Returns:
            Raw Process Dictionary (noch nicht VPB-konform)
        """
        prompt = self.PROCESS_EXTRACTION_PROMPT.format(
            document_text=text[:4000],  # Token-Limit
            rag_context=context
        )
        
        response = self.llm.generate(prompt, temperature=0.2)
        
        # Parse JSON
        import json
        try:
            process_data = json.loads(response)
        except json.JSONDecodeError:
            # Fallback: Extrahiere JSON aus Markdown
            process_data = self._extract_json_from_response(response)
        
        return process_data
```

#### 1.3.3 VPB Schema Mapper

```python
# vpb_mapper.py

class VPBSchemaMapper:
    """
    Mapping: LLM Output → VPB Schema
    
    Konvertiert generische Prozess-Beschreibungen in
    VPB-konforme 23 Element-Typen
    """
    
    # Mapping: Generische Types → VPB Element Types
    TYPE_MAPPING = {
        "start": "start_event",
        "ereignis": "start_event",
        "aufgabe": "task_user",
        "manuelle_aufgabe": "task_user",
        "automatische_aufgabe": "task_service",
        "externe_aufgabe": "task_external",
        "entscheidung": "gateway_xor",
        "verzweigung": "gateway_xor",
        "parallele_aufgaben": "gateway_and",
        "rechtsprüfung": "legal_checkpoint",
        "frist": "deadline",
        "ende": "end_event",
    }
    
    def map_to_vpb_schema(self, raw_process: Dict) -> Dict[str, Any]:
        """
        Konvertiert LLM-Output zu VPB Schema
        
        Args:
            raw_process: Generic process structure
        
        Returns:
            VPB-compliant process
        """
        vpb_process = {
            "process_id": str(uuid.uuid4()),
            "name": raw_process["name"],
            "description": raw_process["description"],
            "authority": raw_process.get("authority"),
            "legal_basis": raw_process.get("legal_basis", []),
            "legal_context": self._infer_legal_context(raw_process),
            "elements": [],
            "connections": []
        }
        
        # Map Steps → Elements
        for i, step in enumerate(raw_process.get("steps", [])):
            element = self._map_step_to_element(step, i)
            vpb_process["elements"].append(element)
        
        # Map Connections
        for conn in raw_process.get("connections", []):
            connection = self._map_connection(conn, vpb_process["elements"])
            vpb_process["connections"].append(connection)
        
        return vpb_process
    
    def _map_step_to_element(
        self, 
        step: Dict, 
        index: int
    ) -> Dict[str, Any]:
        """Maps single step to VPB element"""
        
        # Type Mapping
        raw_type = step.get("type", "task_user").lower()
        vpb_type = self.TYPE_MAPPING.get(raw_type, "task_user")
        
        element = {
            "element_id": f"element_{index:03d}",
            "element_type": vpb_type,
            "name": step["name"],
            "description": step.get("description"),
            "authority": step.get("authority"),
            "deadline_days": step.get("deadline_days"),
            "compliance_critical": self._is_compliance_critical(step),
            "automation_potential": self._estimate_automation(step),
            
            # UI Properties (default positions)
            "x": 100 + (index * 200),
            "y": 100,
            
            # VPB-specific
            "swimlane": step.get("authority"),
            "legal_basis": step.get("legal_basis"),
            "documents": step.get("documents", [])
        }
        
        return element
    
    def _infer_legal_context(self, process: Dict) -> str:
        """
        Inferiert Rechtsgebiet aus Rechtsgrundlagen
        
        Returns:
            "bauordnung" | "sozialrecht" | "verwaltungsrecht" | etc.
        """
        legal_basis = " ".join(process.get("legal_basis", []))
        
        if "BauGB" in legal_basis or "BauO" in legal_basis:
            return "bauordnung"
        elif "SGB" in legal_basis:
            return "sozialrecht"
        elif "StGB" in legal_basis or "StPO" in legal_basis:
            return "strafrecht"
        elif "VwVfG" in legal_basis:
            return "verwaltungsrecht"
        else:
            return "allgemeines_verwaltungsrecht"
```

#### 1.3.4 Validation Engine

```python
# validation_engine.py

class VPBValidationEngine:
    """
    Validiert extrahierte Prozesse gegen VPB-Schema
    """
    
    def validate(self, vpb_process: Dict) -> ValidationResult:
        """
        Comprehensive Validation
        
        Checks:
        - Schema Compliance (23 Element Types)
        - Mandatory Fields
        - Process Flow (Start → End exists)
        - Legal Basis format
        - Authority names
        """
        errors = []
        warnings = []
        
        # 1. Schema Validation
        if not self._validate_schema(vpb_process, errors):
            return ValidationResult(False, errors, warnings)
        
        # 2. Process Flow Validation
        if not self._validate_flow(vpb_process, errors, warnings):
            warnings.append("Process flow may be incomplete")
        
        # 3. Legal Basis Validation
        self._validate_legal_basis(vpb_process, warnings)
        
        # 4. Authority Validation
        self._validate_authorities(vpb_process, warnings)
        
        is_valid = len(errors) == 0
        
        return ValidationResult(is_valid, errors, warnings)
    
    def _validate_flow(
        self, 
        process: Dict, 
        errors: List, 
        warnings: List
    ) -> bool:
        """
        Prüft ob Prozess-Fluss vollständig ist
        
        - Mindestens 1 START_EVENT
        - Mindestens 1 END_EVENT
        - Alle Elemente erreichbar von START
        """
        elements = process.get("elements", [])
        connections = process.get("connections", [])
        
        # Check START/END
        has_start = any(e["element_type"] == "start_event" for e in elements)
        has_end = any(e["element_type"] == "end_event" for e in elements)
        
        if not has_start:
            errors.append("Missing START_EVENT")
            return False
        
        if not has_end:
            warnings.append("Missing END_EVENT")
        
        # Check reachability (Graph Traversal)
        reachable = self._get_reachable_elements(elements, connections)
        unreachable = [e for e in elements if e["element_id"] not in reachable]
        
        if unreachable:
            warnings.append(f"{len(unreachable)} unreachable elements")
        
        return True
```

---

## 🔍 Komponente 2: Gap Detection VPB

### 2.1 Ziel

**Intelligente Analyse** bestehender VPB-Prozesse zur Identifikation von:
- Fehlenden Schritten
- Redundanzen
- Compliance-Lücken
- Optimierungspotential

**Input:**
- Bestehende VPB-Prozesse aus UDS3 Polyglot

**Output:**
- Gap-Report (JSON/HTML)
- Optimierungs-Vorschläge
- Actionable Items für VPB Designer

### 2.2 Analyse-Patterns

```python
# gap_detection_vpb.py - Orchestrator

class GapDetectionVPB:
    """
    Intelligente Gap-Detection für VPB-Prozesse
    
    Nutzt:
    - Graph DB für Pfad-Analyse
    - Vector DB für Ähnlichkeits-Suche
    - RAG für Compliance-Dokumentation
    - LLM für Optimierungs-Vorschläge
    """
    
    def __init__(self, uds3_manager, rag_pipeline, llm_client):
        self.uds3 = uds3_manager
        self.rag = rag_pipeline
        self.llm = llm_client
        self.analyzer = ProcessAnalyzer(uds3_manager)
        self.compliance_checker = ComplianceChecker(rag_pipeline)
        self.suggester = OptimizationSuggester(llm_client)
    
    def analyze_process(self, process_id: str) -> GapReport:
        """
        Vollständige Gap-Analyse
        
        Args:
            process_id: VPB Process ID
        
        Returns:
            GapReport with findings & suggestions
        """
        # 1. Load Process
        process = self.uds3.get_process_details(process_id, include_elements=True)
        
        # 2. Multi-Pattern Analysis
        gaps = {
            "missing_steps": self.analyzer.detect_missing_steps(process),
            "redundant_elements": self.analyzer.detect_redundancies(process),
            "compliance_gaps": self.compliance_checker.check_compliance(process),
            "authority_mismatches": self.analyzer.check_authority_consistency(process),
            "bottlenecks": self.analyzer.detect_bottlenecks(process),
            "similar_processes": self.analyzer.find_similar_processes(process)
        }
        
        # 3. LLM-Generated Suggestions
        suggestions = self.suggester.generate_suggestions(process, gaps)
        
        # 4. Prioritization
        prioritized_gaps = self._prioritize_gaps(gaps)
        
        return GapReport(
            process_id=process_id,
            gaps=prioritized_gaps,
            suggestions=suggestions,
            score=self._calculate_quality_score(gaps)
        )
```

### 2.3 Analyse-Patterns im Detail

#### 2.3.1 Missing Steps Detection

```python
# process_analyzer.py

class ProcessAnalyzer:
    """Graph-basierte Prozess-Analyse"""
    
    def detect_missing_steps(self, process: Dict) -> List[Gap]:
        """
        Erkennt fehlende Prozess-Schritte
        
        Methoden:
        1. Graph-Analyse: Sind alle Pfade vollständig?
        2. Best-Practice-Vergleich: Ähnliche Prozesse haben Schritte X
        3. Compliance-Check: Gesetzlich vorgeschriebene Schritte fehlen
        """
        gaps = []
        
        # 1. Graph Completeness
        graph = self._build_process_graph(process)
        start_nodes = [n for n in graph.nodes if graph.nodes[n]["type"] == "start_event"]
        end_nodes = [n for n in graph.nodes if graph.nodes[n]["type"] == "end_event"]
        
        for start in start_nodes:
            for end in end_nodes:
                paths = nx.all_simple_paths(graph, start, end)
                if not list(paths):
                    gaps.append(Gap(
                        type="missing_connection",
                        severity="high",
                        description=f"No path from {start} to {end}",
                        suggestion="Add intermediate steps or connections"
                    ))
        
        # 2. Best Practice Comparison
        similar_processes = self.uds3.semantic_search(
            query=process["description"],
            domain="vpb",
            top_k=5
        )
        
        for similar in similar_processes:
            similar_steps = set(e["name"] for e in similar["elements"])
            current_steps = set(e["name"] for e in process["elements"])
            missing = similar_steps - current_steps
            
            if missing:
                gaps.append(Gap(
                    type="best_practice_deviation",
                    severity="medium",
                    description=f"Similar processes include steps: {missing}",
                    suggestion=f"Consider adding: {', '.join(list(missing)[:3])}"
                ))
        
        return gaps
```

#### 2.3.2 Compliance Gap Detection

```python
# compliance_checker.py

class ComplianceChecker:
    """RAG-basierte Compliance-Prüfung"""
    
    def check_compliance(self, process: Dict) -> List[Gap]:
        """
        Prüft Compliance gegen Rechtsgrundlagen
        
        Nutzt RAG um relevante Gesetze zu finden und
        LLM um Compliance-Anforderungen zu extrahieren
        """
        gaps = []
        
        legal_basis = process.get("legal_basis", [])
        
        for law in legal_basis:
            # RAG: Hole Gesetzestext
            law_context = self.rag.retrieve_context(
                query=f"Anforderungen {law} Verwaltungsverfahren",
                domain="legal"
            )
            
            # LLM: Extrahiere Compliance-Requirements
            requirements = self._extract_requirements(law, law_context)
            
            # Check if process fulfills requirements
            for req in requirements:
                if not self._check_requirement(process, req):
                    gaps.append(Gap(
                        type="compliance_gap",
                        severity="critical",
                        description=f"Missing requirement from {law}: {req['description']}",
                        suggestion=req["suggestion"],
                        legal_reference=req["paragraph"]
                    ))
        
        return gaps
```

#### 2.3.3 Optimization Suggester

```python
# optimization_suggester.py

class OptimizationSuggester:
    """LLM-basierte Optimierungs-Vorschläge"""
    
    OPTIMIZATION_PROMPT = """
Du bist ein Experte für Verwaltungsprozess-Optimierung.

=== PROZESS ===
Name: {process_name}
Beschreibung: {process_description}
Schritte: {num_steps}
Durchschnittsdauer: {avg_duration} Tage
Automatisierungsgrad: {automation_score}%

=== GEFUNDENE GAPS ===
{gaps_summary}

=== AUFGABE ===
Generiere 3-5 konkrete Optimierungs-Vorschläge die:
1. Die gefundenen Gaps adressieren
2. Prozess-Dauer reduzieren
3. Automatisierungspotential erhöhen
4. Compliance verbessern
5. Bürger-freundlichkeit steigern

Format: JSON Array mit {{action, benefit, effort, priority}}
"""
    
    def generate_suggestions(
        self, 
        process: Dict, 
        gaps: Dict
    ) -> List[Suggestion]:
        """
        LLM-generierte Optimierungs-Vorschläge
        """
        prompt = self.OPTIMIZATION_PROMPT.format(
            process_name=process["name"],
            process_description=process["description"],
            num_steps=len(process["elements"]),
            avg_duration=process.get("avg_duration_days", "N/A"),
            automation_score=process.get("automation_score", 0) * 100,
            gaps_summary=self._format_gaps_summary(gaps)
        )
        
        response = self.llm.generate(prompt, temperature=0.7)
        suggestions = json.loads(response)
        
        return [Suggestion(**s) for s in suggestions]
```

---

## 🔗 Integration mit UDS3 & VPB

### 3.1 UDS3 Integration

```python
# Integration in uds3_polyglot_manager.py

class UDS3PolyglotManager:
    """Extended with DataMiner & Gap Detection"""
    
    def __init__(self, config):
        # ... existing init ...
        
        # NEU: DataMiner & Gap Detection
        self.dataminer = DataMinerVPB(
            uds3_manager=self,
            rag_pipeline=self.rag,
            llm_client=self.llm
        )
        
        self.gap_detector = GapDetectionVPB(
            uds3_manager=self,
            rag_pipeline=self.rag,
            llm_client=self.llm
        )
    
    def mine_process_from_document(self, document_path: str) -> str:
        """
        High-Level API: Dokument → VPB-Prozess
        
        Returns:
            process_id
        """
        result = self.dataminer.extract_process_from_document(document_path)
        return result["process_id"]
    
    def analyze_process_gaps(self, process_id: str) -> GapReport:
        """
        High-Level API: Prozess-Gap-Analyse
        
        Returns:
            GapReport
        """
        return self.gap_detector.analyze_process(process_id)
```

### 3.2 VPB Designer Integration

```python
# VPB Designer: Import aus DataMiner

class VPBProcessDesigner:
    """Extended with DataMiner Import"""
    
    def import_from_dataminer(self, document_path: str):
        """
        Import-Workflow: Dokument → VPB Canvas
        
        1. DataMiner extrahiert Prozess
        2. Visualisiere auf Canvas
        3. User kann editieren
        4. Save zu UDS3
        """
        # Extract via UDS3 DataMiner
        process_id = self.uds3_manager.mine_process_from_document(document_path)
        
        # Load extracted process
        process = self.uds3_manager.get_process_details(process_id)
        
        # Visualize on Canvas
        self.clear_canvas()
        self.load_process(process)
        
        # Show Gap Detection Results
        gaps = self.uds3_manager.analyze_process_gaps(process_id)
        self.show_gap_report(gaps)
        
        messagebox.showinfo(
            "Import Complete",
            f"Process '{process['name']}' imported.\n"
            f"Found {len(gaps.gaps)} potential issues.\n"
            f"Review and edit as needed."
        )
```

---

## 📋 Implementierungs-Roadmap

### Phase 1: DataMiner Foundation (Wochen 1-2)

**Woche 1:**
- [ ] `document_ingestion.py` - PDF/HTML/DOCX Parser
- [ ] `process_extractor.py` - LLM Prompt Engineering
- [ ] Unit Tests für Ingestion

**Woche 2:**
- [ ] `vpb_mapper.py` - Schema Mapping
- [ ] `validation_engine.py` - VPB Validation
- [ ] `dataminer_vpb.py` - Orchestrator
- [ ] Integration Tests

### Phase 2: Gap Detection (Wochen 3-4)

**Woche 3:**
- [ ] `process_analyzer.py` - Graph-basierte Analyse
- [ ] `compliance_checker.py` - RAG-basierte Compliance
- [ ] Missing Steps Detection
- [ ] Redundancy Detection

**Woche 4:**
- [ ] `optimization_suggester.py` - LLM Suggestions
- [ ] `gap_detection_vpb.py` - Orchestrator
- [ ] Gap Report Generation (JSON/HTML)
- [ ] Integration Tests

### Phase 3: UDS3 & VPB Integration (Wochen 5-6)

**Woche 5:**
- [ ] Integration in `uds3_polyglot_manager.py`
- [ ] VPB Designer Import-Workflow
- [ ] Gap Report Visualisierung
- [ ] End-to-End Tests

**Woche 6:**
- [ ] Performance-Optimierung
- [ ] Dokumentation
- [ ] User Guide (DataMiner + Gap Detection)
- [ ] Demo-Videos

---

## 🎯 Success Metrics

| Metrik | Ziel | Messung |
|--------|------|---------|
| **DataMiner Accuracy** | >80% korrekte Extraktion | Manueller Review von 20 Prozessen |
| **Gap Detection Precision** | >85% relevante Gaps | User-Feedback: "War hilfreich?" |
| **Processing Time** | <30s pro Dokument | DataMiner Pipeline |
| **User Satisfaction** | >4/5 Sterne | User Survey |

---

## 📁 Datei-Struktur

```
C:\VCC\Covina\
├── gap_detection/
│   ├── __init__.py
│   ├── gap_detection_vpb.py       # Orchestrator
│   ├── process_analyzer.py        # Graph Analysis
│   ├── compliance_checker.py      # RAG Compliance
│   ├── optimization_suggester.py  # LLM Suggestions
│   └── gap_report_generator.py    # HTML/JSON Reports
│
├── dataminer/
│   ├── __init__.py
│   ├── dataminer_vpb.py           # Orchestrator
│   ├── document_ingestion.py      # PDF/HTML Parser
│   ├── process_extractor.py       # LLM Extraction
│   ├── vpb_mapper.py              # Schema Mapping
│   └── validation_engine.py       # VPB Validation
│
└── integration/
    ├── uds3_dataminer_bridge.py   # UDS3 Integration
    └── vpb_designer_import.py     # VPB Designer Integration
```

---

## 🔗 Nächste Schritte

**Sofort:**
1. [ ] Repository-Struktur erstellen
2. [ ] Dependencies installieren (sentence-transformers, PyMuPDF, etc.)
3. [ ] Erste Prompt-Templates testen

**Diese Woche:**
1. [ ] `document_ingestion.py` implementieren
2. [ ] Erste LLM-Extraktion testen mit Sample-PDF
3. [ ] Unit Tests

---

**Status:** 🟡 Planning Complete - Ready for Implementation

**Review:** [ ] Architecture Team Approval Pending
