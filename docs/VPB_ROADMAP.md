# VPB – Roadmap

## Kurzfristig (0–2 Wochen)
- Merge UX: Diff-Hervorhebung, Warnungsdialog, Chat-Zusammenfassungen für Merge/Patch-Ergebnisse
- Controller/Tasks: Cancel-API + Fortschrittsmeldungen für lange Operationen (Merge, Ollama)
- Doku-Lücken schließen: Beispiele/How‑To für Text→Diagramm und Diff‑Review, aktualisierte Shortcut-Übersicht
- Tests: Minimale Unit‑Tests für Schema/Diff/Prompts und Ollama‑Client (Mock)
- Chat: „Neue Sitzung starten“-Button, manuelle Session‑Rotation, Import/Export einzelner Chats

## Mittelfristig (2–6 Wochen)
- Packaging: Portable Windows‑Binary (PyInstaller), Start‑Script, Logging‑Pfad
- Persistenz: Einstellungen robust versionieren, Backups, Migration
- AI: Prompt‑Tuning, strukturierte Tool‑Aufrufe (JSON‑Schemas), konfigurierbare Modelle
- Editor: Magnetisches Routing, automatische Layout‑Algorithmen, Swimlanes
- Datei‑I/O: Round‑Trip‑Sicherheit JSON↔XML, vollständige VPB‑XSD
- Tests/CI: Linter/Formatter, automatisierte Builds, Smoke‑Tests

## Langfristig (6+ Wochen)
- Erweiterte Compliance: Live‑Checks im Editor (nicht blockierend), Badge/Score
- Kollaboration: Mehrbenutzer‑Modus, CRDT/OT, Datei‑Locking
- Erweiterbares Plugin‑System für Elemente/Verbindungen
- Vollständige UDS3‑Backend‑Anbindung (API‑Server, SQLite), Sync/Publish

## Risiken & Gegenmaßnahmen
- LLM‑Determinismus: Strikte JSON‑Prompts, Validierungs‑Layer (Schema/Diff)
- Performance: Canvas‑Redraws drosseln, Profiling, Caching
- Windows‑Packaging: Abhängigkeiten prüfen, Consolen‑Encoding, Fonts

## Backlog‑Ideen
- Export als SVG/PNG mit Label‑Overlap‑Vermeidung
- Tastatur‑Nudging, Gitter‑Konfiguration speichern
- Vorlagen‑Galerie und Prozess‑Wizard
