# Strategie VPB ↔ Covina

Letzte Aktualisierung: 30.10.2025
Status: Draft (v0.1)

## Zweck und Zielbild

Die VPB-Prozesse werden nicht nur als Ablaufketten zur Antragsbearbeitung verstanden, sondern als organisationales Wissensmodell:
- Hierarchieabbildung: Wer darf was, wann und wie? (Rollen, Rechte, Eskalationen)
- Informationslenkung: Welche Informationen fließen wohin? (Quellen, Senken, Artefakte, Datenschutz)
- Beteiligung: Wer beteiligt wen in welchem Verfahrensschritt? (intern/extern, Pflicht/Fakultativ)
- Organisationsstruktur: Wie ist die Behörde aufgebaut und vernetzt? (Strukturhandbuch: Organisationseinheiten, Systeme, Kontrollen)

Ziel ist ein einheitliches Prozess- und Organisationsmodell (UPS – Unified Process Schema) mit nahtloser Integration in Covina/UDS3 (PostgreSQL, CouchDB, ChromaDB, Neo4j) für Suche, Analyse, Gap-Detection und Governance.

## Scope (MVP → Phase 2)

- MVP
  - Parser für VPB-JSON (Beispieldatei vorhanden) und optional BPMN/XML
  - Normalisierung ins UPS (Process, Step, Role, System, Control, LegalRef, OrgUnit, InfoObject, Flow)
  - Persistenz: PG (Master), Couch (Volltext/Artefakte), Neo4j (Graph), Chroma (semantische Ähnlichkeit auf Steps/Beschreibungen)
  - Ingestion-API: POST /ingestion/processes (multipart + JSON)
  - Queries (Main): GET /processes, /processes/{id}, Suche/Filter/Ähnlichkeit
  - Gap-Detection: fehlende Rollen/Kontrollen/Referenzen, Dead-Ends, Zyklen, unverbundene Steps

- Phase 2
  - Mining: Frequent Patterns, Similarity Clustering, Bottleneck-Indikatoren
  - Conformance-Checks (Soll-Ist), Eskalationspfade, SLA-Hinweise
  - Beteiligungsmatrix (intern/extern) mit Verantwortlichkeitsgraden (RACI-ähnlich)
  - Org-Handbuch-Sichten: Organisationsbaum, Rechtekatalog, Systemlandkarte, Kontrollrahmen

## UPS – Unified Process Schema (erweitert)

Kern-Entitäten:
- Process(id, key, title, version, domain, owner_org, status, created_at)
- Step(id, process_id, order, key, title, description, required, duration_est, inputs[], outputs[], control_points[])
- Role(id, key, name, level, permissions[])
- Unit(id, key, name, parent_id, type)
- System(id, key, name, type, criticality)
- Control(id, key, name, type, objective, evidence)
- LegalRef(id, citation, type, uri)
- InfoObject(id, key, name, classification, pii, retention)

Relationen:
- HAS_STEP(Process→Step)
- NEXT(Step→Step, type=sequence|parallel|exclusive)
- PERFORMED_BY(Step→Role)
- BELONGS_TO(Role→OrgUnit)
- USES_SYSTEM(Step→System)
- CONTROLS(Control→Step|Process)
- CITES(Step|Process→LegalRef)
- PRODUCES/CONSUMES(Step→InfoObject, direction)
- ESCALATES_TO(Step→Role|OrgUnit)

Hinweise:
- IDs: UUIDv7; Keys: stabile Domänen-Schlüssel aus VPB
- Versionierung: Process.version, Step.key bleibt stabil, neue Version = neue Step-IDs, gleiches key
- Sicherheit: PII-Flags auf InfoObject; DSGVO-Metadaten; Maskierung im Export

## Persistenz-Mapping (UDS3)

- PostgreSQL (Relational Master)
  - Tabellen: processes, process_steps, roles, org_units, systems, controls, legal_refs, info_objects, junctions
  - Indizes: process(key), step(process_id, order), role(key), org_unit(parent_id)

- CouchDB (Dokumente/Artefakte)
  - Vollständige VPB-Quellen, angereicherte UPS-Dokumente, Anhänge

- Neo4j (Graph)
  - Knoten: PROCESS, STEP, ROLE, ORG_UNIT, SYSTEM, CONTROL, LEGAL_REF, INFO
  - Kanten: HAS_STEP, NEXT, PERFORMED_BY, BELONGS_TO, USES_SYSTEM, CONTROLS, CITES, PRODUCES, CONSUMES, ESCALATES_TO
  - Temporales Modell (UDS3-Canon): YEAR, MONTH, DAY, DATE; Relationen: HAS_MONTH, HAS_DAY, IS_DATE, OCCURS_ON, SCHEDULED_FOR, EFFECTIVE_FROM, EFFECTIVE_UNTIL
    - Properties-Standard: created_at/updated_at via datetime() an Nodes/Edges
    - Canonical Keys:
      - (:Year {y})
      - (:Month {y, m})
      - (:Day {y, m, d})
      - (:Date {iso, year, month, day})
    - Verwendung in Prozessen:
      - (STEP)-[:OCCURS_ON]->(:Date)
      - (STEP)-[:SCHEDULED_FOR]->(:Date)
      - (CONTROL|LEGAL_REF)-[:EFFECTIVE_FROM/UNTIL]->(:Date)
    - Indizes/Constraints:
      - CONSTRAINT date_iso_unique FOR (:Date) REQUIRE date.iso IS UNIQUE
      - INDEX month_y_m FOR (:Month) ON (month.y, month.m)
      - INDEX day_y_m_d FOR (:Day) ON (day.y, day.m, day.d)

- ChromaDB (Vektoren)
  - Embeddings auf Step.title/description, Controls, LegalRefs (Textfelder)
  - Metadaten: process_key, step_key, version, role_keys

## APIs und Endpunkte

- Ingestion (FastAPI, versioniert /v1)
  - POST /ingestion/processes
    - Accepts: JSON (VPB/UPS) oder multipart (vpb.json + attachments)
    - Optionen: upsert=true, validate=true, dry_run=false
    - Ergebnis: counts, ids, warnings, violations

- Main (Queries/Analytics)
  - GET /processes[?q=&role=&org=&system=&has_control=&legal=]
  - GET /processes/{id} (inkl. Graph-Ausschnitt)
  - POST /processes/similarity (Chroma, top_k)
  - POST /gaps/processes/run (Scoping: process_ids | domain)
  - POST /mining/processes/run (Algorithmen/Parameter)

## Gap-Detection (MVP-Regeln)

- Step ohne PERFORMED_BY
- Step ohne NEXT (kein Terminal/Dead-End)
- Zyklus ohne erlaubte Schleife
- Pflicht-Control fehlt (CONTROL.required=true, aber keine Zuordnung)
- Referenz im Text aber kein LegalRef (NLP-Hinweis)
- InfoObject mit PII aber ohne Control/Evidence
- Temporale Konsistenz: EFFECTIVE_FROM <= EFFECTIVE_UNTIL; Steps ohne pasado/futuro Konflikte (z. B. NEXT führt in die Vergangenheit)

## Qualitäts- und Erfolgsmetriken

- Import: 100% valide VPB-JSON Beispiele → UPS ohne Fehler
- Queries: <200ms für Detail, <500ms für Suche (Dev, 1 Worker)
- Gaps: Regel-Engine liefert deterministische Ergebnisse, 0 falsche Positivfälle in Referenzdatensatz
- Vektorsuche: Top-3 Ähnlichkeit für semantisch ähnliche Steps ≥ 0.7 (cosine)

## Betrieb und Governance

- Versionierte Imports; Audit-Log für Änderungen
- DSGVO: Kennzeichnung/Maskierung PII; Exportfilter
- Admin-Tools: Rebuild-Graph, Re-Embed, Run Gaps/Mining (Maintenance)

## Self-learning & Dynamisierung (OOP, Best Practices)

Ziel: Aus tausenden realen Verfahren Prozesswissen dynamisch ableiten und fortlaufend schärfen.

Bausteine:
- Signals: Extrahiert robuste Merkmale (datum, behörde, aktenzeichen, artefaktarten, zeitabstände).
- RuleEngine (YAML): Domain-Leitlinien, Regex-/Heuristik-Regeln, Gewichte; versioniert, auditierbar.
- Miner-Strategien: Austauschbare Strategien (z. B. Frequenzbasiert, Bayesian, GraphWalk, LLM-Reasoning) mit gemeinsamer Miner-API.
- Confidence: Gewichtete Evidenzaggregation; Normalisierung, Kalibrierung (später: Platt/Isotonic), Unsicherheitsmaße.
- Feedback: Human-in-the-Loop (Review Queue), aktive Lernbeispiele, Labeling von Pfaden.
- Persistenz: Evidenz + Confidence in PG; Knoten/Kanten in Neo4j (inkl. Date-Links); Embeddings für Schrittbeschreibungen in Chroma.
- Governance: Versionierte Regeln, Reproduzierbarkeit, Drift-Erkennung, Rollback.

Ablauf (Batch/Online):
1) Metadaten/Textschnipsel → Signals
2) YAML-Regeln/Heuristiken → initiale Evidenz
3) Häufigkeits-/Sequenzmuster über Batch → Pfad-/Schritt-Confidence
4) Optional LLM-Evaluierung/Begründung → zusätzliche Evidenz
5) Aggregation + Kalibrierung → Confidence je Node/Edge
6) Persistenz → Query/UI, Review, Retraining

Architektur (OOP):
- interfaces.MinerStrategy: infer(doc|batch) → Evidence
- mining.ProcessMiningPipeline: orchestriert Signals→Rules→Miner→Aggregate
- guidelines.RuleEngine: YAML-Parser + Condition-Evaluator
- confidence.Calibrator: optionale Kalibrierer (Platt/Isotonic)
- storage.ProcessInferenceStore: Writes nach PG/Neo4j/Chroma

## Migrations- und Implementierungsplan

1) Parser & UPS (VPB→UPS)
2) Persistenz (PG/Couch/Graph/Vector)
3) Ingestion-Endpoint /ingestion/processes
4) Main-Queries & Detailansichten
5) Gap-Detection (MVP-Regeln)
6) Mining (Phase 2)
7) Temporal Canon aktivieren (Date-Nodes, Indizes, Relationen in Writes nutzen)
8) Self-learning Pipeline aktivieren (Guidelines, Miner, Confidence, Review)

## Risiken & Gegenmaßnahmen

- Uneinheitliche VPB-Quellen → Strikte Validierung + Normalisierungsregeln
- Rechte-/Rollendaten lückenhaft → Fallback auf OrgUnit-Level, Gaps markieren
- Performance Graph/Vector → Batch-Operationen, Indizes, Caching

## Nächste Schritte

- [ ] VPB→UPS Mapping-Spezifikation finalisieren (mit Beispiel aus processes/bauleitplanung_...vpb.json)
- [ ] Ingestion: POST /ingestion/processes (JSON, multipart)
- [ ] PG/Neo4j Schemata für Prozesse deployen (Migrationen)
- [ ] Neo4j: Temporal Canon aktivieren (Constraints/Indizes, Date-Links bei Writes)
- [ ] Gap-Regeln implementieren und testen
- [ ] Queries und UI-Sichten (Org-Handbuch, Prozesslandkarte)
