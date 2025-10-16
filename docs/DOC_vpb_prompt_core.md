# VPB Prompt Core

Dieser Bestandteil bündelt zentrale Bausteine für die LLM-Interaktion:

## Ziele
- Konsistente, versionierte Prompt-Erzeugung (Registry)
- Sicherheit: Vermeidung von Beispiel-Leaks / Copy-Paste
- Validierung der Modellantwort (Struktur, Add-Only, Typen)
- Erweiterbarkeit via Hooks (Logging, Telemetrie, A/B Tests)

## Hauptdatei
`vpb_prompt_core.py`

## Kernkomponenten
### PromptMeta
Metadaten zu einem Prompt-Aufbau:
- mode (text_to_vpb | next_steps | diagnose_fix)
- version (z. B. v1.0)
- id (mode:version)
- example_ids, example_tags
- token_estimate (heuristisch)

### build_prompt_with_examples_meta()
Generischer Builder, der:
1. Few-Shot Beispiele rendert (nur Lesen, nicht kopieren)
2. Gemeinsame Regeln anhängt (JSON-only, keine Erklärungen)
3. Sicherheits-Hinweise ergänzt
4. Metadaten erzeugt
5. Optional before_send_hook ausführt

### Validierung: validate_vpb_json()
Prüft:
- JSON parsebar? (Codefences entfernt)
- Modusabhängige Pflichtfelder
- Add-Only (konfliktfreie IDs bei next_steps / diagnose_fix.patch)
- Erlaubte Typen (optional)
- Raster (50er) → Info-Warnungen
- Leak-Detektion (Beispiele echo)

Rückgabe: ValidationResult (parsed, issues[], fatal)

### Hooks
- set_before_send_hook(fn(meta, prompt))
- set_after_response_hook(fn(meta, raw_output, validation))

### Sicherheits-Mechanismen
- Expliziter Hinweis: Beispiele nicht wiederholen
- Markierung "Beispiele (nur lesen...)" → wenn im Output, Fehlercode `leak.examples_echo`

## Nutzung in `vpb_ai_logic.py`
Die bisherigen Funktionen *build_prompt_with_examples_* bleiben kompatibel, können optional `return_meta=True` erhalten.

## Erweiterungsideen
- Tokenisierung durch spezifisches Modell (tiktoken) ersetzen
- Adaptive Beispielauswahl (Komplexität, Tags)
- Auto-Retry Mechanismus bei fatalen Validierungsfehlern

## Beispiel Validierung
```python
from vpb_ai_logic import build_prompt_with_examples_text_to_vpb, validate_model_output

prompt, meta = build_prompt_with_examples_text_to_vpb(
    description="Genehmigung eines Bauantrags ...",
    element_types=["START_EVENT","FUNCTION","END_EVENT"],
    connection_types=["SEQUENCE"],
    example_tags=["antrag"],
    return_meta=True,
)
# ... Modell-Aufruf ...
model_output = "{\"metadata\":{...}}"  # Response
report = validate_model_output(model_output, mode=meta.mode, allow_element_types=[...], allow_connection_types=[...])
if report['fatal']:
    # Fehlerbehandlung / Retry
    pass
```
