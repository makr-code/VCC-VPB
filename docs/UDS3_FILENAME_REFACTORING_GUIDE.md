# UDS3 Dateinamen-Refactoring: Migration Guide

**Datum:** 18. Oktober 2025  
**Version:** 1.0  
**Status:** 🟢 APPROVED

---

## 📋 Übersicht

**Ziel:** Dateinamen verkürzen durch Entfernung redundanter Präfixe  
**Scope:** 81 Python-Dateien im C:\VCC\uds3\ Root  
**Strategie:** Git mv (History preservation) + Automated Import Updates

---

## 🎯 Namenskonventions-Prinzipien

### Regel 1: Entferne "uds3_" Präfix

**Begründung:** Kontext bereits durch Ordnerstruktur (`uds3/`) klar

```python
# ❌ ALT
uds3_polyglot_manager.py
uds3_vpb_operations.py
uds3_dsgvo_core.py

# ✅ NEU
polyglot_manager.py  # in core/
operations.py        # in vpb/
dsgvo_core.py        # in compliance/
```

### Regel 2: Domain-Prefix nur wenn nötig

**Begründung:** Ordnerstruktur macht Domain klar

```python
# ❌ ALT
uds3_vpb_operations.py    # "vpb" redundant wenn in vpb/ Ordner

# ✅ NEU
operations.py             # vpb/ Ordner macht Kontext klar
```

### Regel 3: Funktions-Prefix statt -Suffix für Parser

**Begründung:** Besseres Grouping in Dateilisten

```python
# ❌ ALT
uds3_bpmn_process_parser.py
uds3_epk_process_parser.py
uds3_petrinet_parser.py

# ✅ NEU
parser_bpmn.py       # Alle Parser zusammen gruppiert
parser_epk.py
parser_petrinet.py
```

### Regel 4: Redundante Wörter entfernen

**Begründung:** Kontext macht Bedeutung klar

```python
# ❌ ALT
uds3_process_export_engine.py      # "process" redundant in VPB-Kontext
uds3_archive_operations.py          # "operations" implizit
uds3_single_record_cache.py         # "single" implizit

# ✅ NEU
export_engine.py
archive.py
record_cache.py
```

---

## 📊 Vollständiges Mapping (81 Dateien)

### Core Module (Neue Implementierung)

| Alt | Neu | Ordner | Status |
|-----|-----|--------|--------|
| `embeddings.py` | `embeddings.py` | `core/` | ✅ BEHALTEN (kein Präfix) |
| `llm_ollama.py` | `llm_ollama.py` | `core/` | ✅ BEHALTEN (kein Präfix) |
| `rag_pipeline.py` | `rag_pipeline.py` | `core/` | ✅ BEHALTEN (kein Präfix) |
| `uds3_polyglot_manager.py` | `polyglot_manager.py` | `core/` | 🔄 KÜRZEN |

### VPB Domain (17 Dateien → vpb/)

| Alt | Neu | Änderung |
|-----|-----|----------|
| `uds3_vpb_operations.py` | `operations.py` | -13 Zeichen |
| `uds3_bpmn_process_parser.py` | `parser_bpmn.py` | -17 Zeichen |
| `uds3_epk_process_parser.py` | `parser_epk.py` | -16 Zeichen |
| `uds3_petrinet_parser.py` | `parser_petrinet.py` | -5 Zeichen |
| `uds3_process_parser_base.py` | `parser_base.py` | -17 Zeichen |
| `uds3_process_export_engine.py` | `export_engine.py` | -13 Zeichen |
| `uds3_process_mining.py` | `process_mining.py` | -5 Zeichen |
| `uds3_complete_process_integration.py` | `complete_integration.py` | -13 Zeichen |
| `uds3_strategic_insights_analysis.py` | `insights_analysis.py` | -15 Zeichen |
| `uds3_follow_up_orchestrator.py` | `follow_up_orchestrator.py` | -5 Zeichen |
| `uds3_workflow_net_analyzer.py` | `workflow_analyzer.py` | -9 Zeichen |

### Compliance (5 Dateien → compliance/)

| Alt | Neu | Änderung |
|-----|-----|----------|
| `uds3_dsgvo_core.py` | `dsgvo_core.py` | -5 Zeichen |
| `uds3_security_quality.py` | `security_quality.py` | -5 Zeichen |
| `uds3_identity_service.py` | `identity_service.py` | -5 Zeichen |
| `uds3_delete_operations.py` | `delete_operations.py` | -5 Zeichen |
| `uds3_validation_worker.py` | `validation_worker.py` | -5 Zeichen |

### Integration (5 Dateien → integration/)

| Alt | Neu | Änderung |
|-----|-----|----------|
| `saga_multi_db_integration.py` | `saga_integration.py` | -9 Zeichen |
| `adaptive_multi_db_strategy.py` | `adaptive_strategy.py` | -9 Zeichen |
| `uds3_multi_db_distributor.py` | `distributor.py` | -14 Zeichen |
| `pipeline_integration.py` | `pipeline.py` | -12 Zeichen |
| `uds3_polyglot_query.py` | `query_abstraction.py` | -5 Zeichen |
| `gradual_migration_manager.py` | `migration_manager.py` | -8 Zeichen |

### Operations (4 Dateien → operations/)

| Alt | Neu | Änderung |
|-----|-----|----------|
| `uds3_advanced_crud.py` | `advanced_crud.py` | -5 Zeichen |
| `uds3_archive_operations.py` | `archive.py` | -16 Zeichen |
| `uds3_streaming_operations.py` | `streaming.py` | -16 Zeichen |
| `uds3_single_record_cache.py` | `record_cache.py` | -12 Zeichen |

### Query (5 Dateien → query/)

| Alt | Neu | Änderung |
|-----|-----|----------|
| `uds3_query_filters.py` | `filters.py` | -11 Zeichen |
| `uds3_vector_filter.py` | `vector_filter.py` | -5 Zeichen |
| `uds3_graph_filter.py` | `graph_filter.py` | -5 Zeichen |
| `uds3_relational_filter.py` | `relational_filter.py` | -5 Zeichen |
| `uds3_file_storage_filter.py` | `file_filter.py` | -13 Zeichen |

### Domain (8 Dateien → domain/)

| Alt | Neu | Änderung |
|-----|-----|----------|
| `uds3_admin_types.py` | `admin_types.py` | -5 Zeichen |
| `uds3_collection_templates.py` | `templates.py` | -16 Zeichen |
| `uds3_geo_extension.py` | `geo_extension.py` | -5 Zeichen |
| `uds3_4d_geo_extension.py` | `geo_4d.py` | -14 Zeichen |
| `uds3_document_classifier.py` | `document_classifier.py` | -5 Zeichen |
| `uds3_document_reconstruction_engine.py` | `document_reconstruction.py` | -12 Zeichen |
| `uds3_naming_strategy.py` | `naming_strategy.py` | -5 Zeichen |
| `uds3_naming_integration.py` | `naming_integration.py` | -5 Zeichen |
| `document_reconstruction_engine.py` | `document_reconstruction.py` | -7 Zeichen |

### SAGA (4 Dateien → saga/)

| Alt | Neu | Änderung |
|-----|-----|----------|
| `uds3_saga_orchestrator.py` | `orchestrator.py` | -10 Zeichen |
| `uds3_saga_compliance.py` | `compliance.py` | -10 Zeichen |
| `uds3_saga_step_builders.py` | `step_builders.py` | -10 Zeichen |
| `uds3_streaming_saga_integration.py` | `streaming_integration.py` | -10 Zeichen |
| `uds3_saga_mock_orchestrator.py` | `mock_orchestrator.py` | -10 Zeichen |

### Relations (2 Dateien → relations/)

| Alt | Neu | Änderung |
|-----|-----|----------|
| `uds3_relations_core.py` | `core.py` | -14 Zeichen |
| `uds3_relations_data_framework.py` | `data_framework.py` | -14 Zeichen |

### Performance (3 Dateien → performance/)

| Alt | Neu | Änderung |
|-----|-----|----------|
| `performance_testing_optimization.py` | `testing_optimization.py` | -12 Zeichen |
| `monolithic_fallback_strategies.py` | `fallback_strategies.py` | -11 Zeichen |
| `processor_distribution_methods.py` | `distribution_methods.py` | -10 Zeichen |

### Legacy (zu deprecaten → legacy/)

| Alt | Neu | Notiz |
|-----|-----|-------|
| `uds3_core.py` | `core.py` | 285KB Monolith |
| `rag_enhanced_llm_integration.py` | `rag_enhanced.py` | Features in rag_pipeline.py mergen |
| `uds3_dsgvo_core_old.py` | **DELETE** | Alte Version |
| `uds3_quality_DEPRECATED.py` | **DELETE** | Deprecated |
| `uds3_security_DEPRECATED.py` | **DELETE** | Deprecated |

### Database (UNVERÄNDERT - bereits gut strukturiert)

```
database/
├── database_manager.py        # ✅ BEHALTEN
├── database_api_base.py       # ✅ BEHALTEN
├── database_api_chromadb.py   # ✅ BEHALTEN
├── database_api_neo4j.py      # ✅ BEHALTEN
└── ... (weitere Adapter)      # ✅ BEHALTEN
```

---

## 🛠️ Migration-Tools

### Tool 1: Automated File Renaming

```python
#!/usr/bin/env python3
"""
rename_files.py - Automatisches Umbenennen mit Git History Preservation
"""

import subprocess
from pathlib import Path

# Mapping: Alt → Neu (mit Ziel-Ordner)
RENAME_MAPPING = {
    # Core
    "uds3_polyglot_manager.py": "core/polyglot_manager.py",
    
    # VPB
    "uds3_vpb_operations.py": "vpb/operations.py",
    "uds3_bpmn_process_parser.py": "vpb/parser_bpmn.py",
    "uds3_epk_process_parser.py": "vpb/parser_epk.py",
    "uds3_petrinet_parser.py": "vpb/parser_petrinet.py",
    "uds3_process_parser_base.py": "vpb/parser_base.py",
    "uds3_process_export_engine.py": "vpb/export_engine.py",
    "uds3_process_mining.py": "vpb/process_mining.py",
    
    # Compliance
    "uds3_dsgvo_core.py": "compliance/dsgvo_core.py",
    "uds3_security_quality.py": "compliance/security_quality.py",
    "uds3_identity_service.py": "compliance/identity_service.py",
    "uds3_delete_operations.py": "compliance/delete_operations.py",
    "uds3_validation_worker.py": "compliance/validation_worker.py",
    
    # Integration
    "saga_multi_db_integration.py": "integration/saga_integration.py",
    "adaptive_multi_db_strategy.py": "integration/adaptive_strategy.py",
    "uds3_multi_db_distributor.py": "integration/distributor.py",
    "pipeline_integration.py": "integration/pipeline.py",
    "uds3_polyglot_query.py": "integration/query_abstraction.py",
    
    # ... (rest of mappings)
}

def rename_with_git(old_path: Path, new_path: Path):
    """Umbenennen mit Git mv (History bleibt erhalten)"""
    # Erstelle Ziel-Ordner falls nötig
    new_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Git mv
    result = subprocess.run(
        ["git", "mv", str(old_path), str(new_path)],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(f"✅ Renamed: {old_path} → {new_path}")
        return True
    else:
        print(f"❌ FAILED: {old_path}")
        print(f"   Error: {result.stderr}")
        return False

def main():
    uds3_root = Path("C:/VCC/uds3")
    success_count = 0
    fail_count = 0
    
    for old_name, new_relative_path in RENAME_MAPPING.items():
        old_path = uds3_root / old_name
        new_path = uds3_root / new_relative_path
        
        if old_path.exists():
            if rename_with_git(old_path, new_path):
                success_count += 1
            else:
                fail_count += 1
        else:
            print(f"⏭️  SKIP: {old_name} (not found)")
    
    print(f"\n📊 Summary: {success_count} succeeded, {fail_count} failed")

if __name__ == "__main__":
    main()
```

### Tool 2: Automated Import Updates

```python
#!/usr/bin/env python3
"""
update_imports.py - Aktualisiert alle Imports nach Umbenennung
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple

# Import-Mappings (Regular Expressions)
IMPORT_PATTERNS = [
    # Core
    (r'from uds3\.uds3_polyglot_manager import', 'from uds3.core.polyglot_manager import'),
    (r'import uds3\.uds3_polyglot_manager', 'import uds3.core.polyglot_manager'),
    
    # VPB
    (r'from uds3\.uds3_vpb_operations import', 'from uds3.vpb.operations import'),
    (r'from uds3\.uds3_bpmn_process_parser import', 'from uds3.vpb.parser_bpmn import'),
    (r'from uds3\.uds3_epk_process_parser import', 'from uds3.vpb.parser_epk import'),
    
    # Compliance
    (r'from uds3\.uds3_dsgvo_core import', 'from uds3.compliance.dsgvo_core import'),
    (r'from uds3\.uds3_security_quality import', 'from uds3.compliance.security_quality import'),
    
    # Integration
    (r'from uds3\.saga_multi_db_integration import', 'from uds3.integration.saga_integration import'),
    (r'from uds3\.adaptive_multi_db_strategy import', 'from uds3.integration.adaptive_strategy import'),
    
    # ... (weitere Mappings)
]

def update_imports_in_file(file_path: Path) -> Tuple[int, List[str]]:
    """Aktualisiert Imports in einer Datei"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        changes = []
        
        for old_pattern, new_import in IMPORT_PATTERNS:
            matches = re.findall(old_pattern, content)
            if matches:
                content = re.sub(old_pattern, new_import, content)
                changes.append(f"  {old_pattern} → {new_import}")
        
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            return len(changes), changes
        
        return 0, []
        
    except Exception as e:
        print(f"❌ Error in {file_path}: {e}")
        return 0, []

def main():
    uds3_root = Path("C:/VCC/uds3")
    total_files = 0
    updated_files = 0
    total_changes = 0
    
    # Alle Python-Dateien durchsuchen
    for py_file in uds3_root.rglob("*.py"):
        if "legacy" not in str(py_file) and ".venv" not in str(py_file):
            total_files += 1
            change_count, changes = update_imports_in_file(py_file)
            
            if change_count > 0:
                updated_files += 1
                total_changes += change_count
                print(f"✅ Updated: {py_file.relative_to(uds3_root)}")
                for change in changes:
                    print(change)
    
    print(f"\n📊 Summary:")
    print(f"   Total files scanned: {total_files}")
    print(f"   Files updated: {updated_files}")
    print(f"   Total import changes: {total_changes}")

if __name__ == "__main__":
    main()
```

### Tool 3: __init__.py Generator (Backwards Compatibility)

```python
#!/usr/bin/env python3
"""
generate_init_files.py - Erstellt __init__.py mit Re-Exports für Backwards Compatibility
"""

from pathlib import Path

def generate_vpb_init():
    """Generiert vpb/__init__.py mit Re-Exports"""
    content = '''"""
VPB Domain Module
Verwaltungsprozessbearbeitung (VPB) Domain Models & Operations
"""

# Re-exports für Backwards Compatibility
from .operations import (
    VPBProcess,
    VPBTask,
    VPBDocument,
    VPBParticipant,
    ProcessStatus,
    TaskStatus,
    ParticipantRole,
    AuthorityLevel,
    LegalContext,
    ProcessComplexity,
)

from .parser_bpmn import BPMNParser
from .parser_epk import EPKParser
from .parser_petrinet import PetriNetParser
from .parser_base import ProcessParserBase

__all__ = [
    # Domain Models
    "VPBProcess",
    "VPBTask",
    "VPBDocument",
    "VPBParticipant",
    
    # Enums
    "ProcessStatus",
    "TaskStatus",
    "ParticipantRole",
    "AuthorityLevel",
    "LegalContext",
    "ProcessComplexity",
    
    # Parsers
    "BPMNParser",
    "EPKParser",
    "PetriNetParser",
    "ProcessParserBase",
]
'''
    return content

def generate_core_init():
    """Generiert core/__init__.py"""
    content = '''"""
UDS3 Core Module
Kern-Komponenten: Embeddings, LLM, RAG, Polyglot Manager
"""

from .embeddings import UDS3GermanEmbeddings
from .llm_ollama import OllamaClient
from .rag_pipeline import UDS3GenericRAG, QueryType
from .polyglot_manager import UDS3PolyglotManager

__all__ = [
    "UDS3GermanEmbeddings",
    "OllamaClient",
    "UDS3GenericRAG",
    "QueryType",
    "UDS3PolyglotManager",
]
'''
    return content

def generate_compliance_init():
    """Generiert compliance/__init__.py"""
    content = '''"""
Compliance Module
DSGVO, Security, Identity Management
"""

from .dsgvo_core import UDS3DSGVOCore, DSGVOOperationType, PIIType
from .security_quality import DataSecurityManager, DataQualityManager
from .identity_service import IdentityService
from .delete_operations import SoftDeleteManager, HardDeleteManager

__all__ = [
    "UDS3DSGVOCore",
    "DSGVOOperationType",
    "PIIType",
    "DataSecurityManager",
    "DataQualityManager",
    "IdentityService",
    "SoftDeleteManager",
    "HardDeleteManager",
]
'''
    return content

def main():
    uds3_root = Path("C:/VCC/uds3")
    
    init_files = {
        "core": generate_core_init(),
        "vpb": generate_vpb_init(),
        "compliance": generate_compliance_init(),
        # ... weitere Ordner
    }
    
    for folder, content in init_files.items():
        init_path = uds3_root / folder / "__init__.py"
        init_path.parent.mkdir(parents=True, exist_ok=True)
        init_path.write_text(content, encoding='utf-8')
        print(f"✅ Created: {init_path}")

if __name__ == "__main__":
    main()
```

---

## 📅 Migration-Plan

### Phase 1: Vorbereitung (Tag 1)
- [ ] Git Branch erstellen: `refactoring/rename-files`
- [ ] Backup erstellen
- [ ] Tools testen (Dry-Run)

### Phase 2: Ordner erstellen (Tag 1)
- [ ] `mkdir core vpb compliance integration operations query domain saga legacy`
- [ ] `__init__.py` Dateien erstellen

### Phase 3: Dateien umbenennen (Tag 1-2)
- [ ] `rename_files.py` ausführen (mit Git mv)
- [ ] Validieren (alle Dateien verschoben?)

### Phase 4: Imports aktualisieren (Tag 2)
- [ ] `update_imports.py` ausführen
- [ ] Manuelle Prüfung kritischer Files

### Phase 5: Testing (Tag 3)
- [ ] Alle Tests ausführen (`pytest`)
- [ ] Import-Errors fixen
- [ ] Backwards Compatibility validieren

### Phase 6: Commit & Merge (Tag 4)
- [ ] Git Commit (mit aussagekräftiger Message)
- [ ] Code Review
- [ ] Merge in main Branch

---

## ✅ Success Metrics

**Erfolg wenn:**
- ✅ Alle 81 Dateien korrekt umbenannt
- ✅ Alle Imports funktionieren
- ✅ Alle Tests passing
- ✅ Git History erhalten (git log --follow funktioniert)
- ✅ Backwards Compatibility via __init__.py
- ✅ Durchschnittliche Dateinamen-Länge: -30%

---

**Status:** 🟢 READY FOR EXECUTION  
**Owner:** UDS3 Refactoring Team  
**Estimated Effort:** 3-4 Tage  
**Risk Level:** NIEDRIG (mit Git History Preservation)
