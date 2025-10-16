# ollama_client.py – Leichter HTTP-Client für Ollama

## Zweck
Dünne Wrapper-Schicht um die Ollama HTTP-API ohne externe Abhängigkeiten (urllib). Bietet synchrone Aufrufe und Streaming-Generatoren für „generate“ und „chat“, JSON-Extraktion und einen einfachen Thread-Job-Wrapper mit Cancel.

## Hauptbestandteile
- `OllamaOptions`: Temperatur und `num_predict` (max Tokens)
- `OllamaClient`:
  - `health()` – GET /api/tags
  - `generate(prompt, options, stream=False)` – Textausgabe
  - `chat(messages, options, stream=False)` – Chat-Kompletion
  - `generate_stream(...)` / `chat_stream(...)` – Iteratoren für Streaming
  - `extract_json(text)` – robustes JSON-Parsen aus gemischten Antworten
  - `generate_json(prompt, options, retries=1, validate=None)` – Prompt→JSON mit optionalem Validator und Retry
- `OllamaJob`: Thread-basierte Ausführung eines Callables; sammelt Streaming-Chunks in Queue, Cancel via Event

## Nutzung (Beispiele)
- Health:
  - `client = OllamaClient()`
  - `client.health()` → Tags/Modelle
- Chat-Streaming:
  - `for chunk in client.chat_stream(messages, options): ...`
- JSON-Erzeugung mit Validierung:
  - `client.generate_json(prompt, options, validate=my_validator)`

## Fehler-/Randfälle
- Netzwerkfehler werden als `RuntimeError` mit URLError-Details geworfen
- `extract_json` versucht erst ```json-Blöcke, dann geschweifte Klammern, entfernt ggf. trailing commas
- Streaming-Response: Iterator muss vollständig konsumiert werden, sonst `resp.close()` wichtig (im Code gesichert)

## Abhängigkeiten
- Standardbibliothek: urllib.request, json, threading, queue, re
- Keine externen Pakete erforderlich

## Hinweise
- Der Client ist absichtlich minimal gehalten; Timeouts sind konfigurierbar (Default 60s)
- `OllamaJob` ist best-effort Cancel – beendet das Einlesen der Streamingquelle und stoppt weitere Chunks