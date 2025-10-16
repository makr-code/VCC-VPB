# Merge Konfliktstrategien & Auto-Rename

Dieser Abschnitt beschreibt das Verhalten des `MergeManager.merge_full()` nach der Einführung der konfigurierbaren Konfliktstrategie.

## Überblick
Beim Mergen eines eingehenden Diagramms können Element-IDs mit bereits vorhandenen IDs kollidieren. Daraus ergeben sich drei Dimensionen des Verhaltens:

1. conflict_strategy: `skip` (Standard) oder `duplicate`
2. auto_rename: `True` / `False`
3. update_mode: `none` | `fill-empty` | `overwrite`

| conflict_strategy | auto_rename | vorhandene ID kollidiert | Ergebnis |
|-------------------|------------|--------------------------|----------|
| skip              | True       | Ja                       | Element wird ignoriert (kein neues Element, keine Änderung) |
| skip              | False      | Ja                       | Element wird ignoriert (kein Fehler) |
| duplicate         | True       | Ja                       | Element wird als Kopie hinzugefügt; neue ID per `_next_free()` |
| duplicate         | False      | Ja                       | Element wird ignoriert (kein Fehler – Fallback) |

Hinweis: Früher wurden Kollisions-Elemente stets dupliziert, die Standardtests erwarteten jedoch das Ignorieren; daher wurde `skip` als Default festgelegt. Die UI (`vpb_app.py`) ruft `merge_full(... conflict_strategy="duplicate")` auf, um das ursprüngliche Nutzerverhalten (Duplizieren) beizubehalten.

## Auto-Rename
`auto_rename=True` bewirkt, dass für neue (noch nicht existierende) IDs, die innerhalb des gleichen Merge-Payloads erneut auftreten oder mit bestehenden kollidieren, ein eindeutiger Suffix (`_1`, `_2`, …) generiert wird.

Zusätzlich findet ein "Deep Reference Rename" für verschachtelte Strukturen statt (z. B. in `members`, `linked_elements`, verschachtelten Dicts), damit interne Referenzen konsistent bleiben.

## Update-Modus
Wenn `update_mode in {fill-empty, overwrite}` und eine eingehende ID bereits existiert, wird kein neues Element angelegt. Stattdessen werden Felder des vorhandenen Elements aktualisiert:
- `fill-empty`: Nur leere / fehlende Felder werden ergänzt.
- `overwrite`: Alle übergebenen Felder überschreiben bestehende Werte.

Betroffene Felder (derzeit): `name`, `description`, `responsible_authority`, `legal_basis`, `deadline_days`.

## Telemetrie-Felder
Bei aktivem TelemetryManager erzeugt `merge_full` ein Ereignis `merge_full` mit u. a.:
- `added_elements`
- `added_connections`
- `element_renames`
- `connection_renames`
- `update_mode`
- `auto_rename`
- `snap`
- (künftige Erweiterung) `conflict_strategy` (TODO)

## Best Practices
- Verwende in automatisierten Tests `conflict_strategy="skip"` für deterministische Zählungen.
- In interaktiver UI `duplicate`, um LLM-Vorschläge sichtbarer zu machen.
- Deaktiviere `auto_rename` nur, wenn du harte Fehler bei Konflikten erzwingen möchtest (künftige Option: expliziter `error` Modus denkbar).

## Erweiterungen (Roadmap)
- Telemetrie-Feld `conflict_strategy` hinzufügen
- Persistenz der bevorzugten Konfliktstrategie in Settings
- UI Toggle für Konfliktstrategie
- Optionaler Modus `error`: wirft Exception bei Konflikt
