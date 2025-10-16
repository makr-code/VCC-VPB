# AI Guardrail Evaluation Report

| Testfall | Fehler | Warnungen | Infos | Status |
|---------|-------:|----------:|------:|:-------|
| clean_diff | 0 | 0 | 0 | ✅ |
| duplicate_element_id | 1 | 0 | 0 | ✅ |
| duplicate_element_name | 0 | 1 | 0 | ✅ |
| missing_name | 0 | 1 | 0 | ✅ |
| self_loop | 0 | 1 | 0 | ✅ |
| dangling_connection | 1 | 0 | 0 | ✅ |
| unconnected_function | 0 | 1 | 0 | ✅ |
| duplicate_connection_id | 1 | 0 | 0 | ✅ |
| duplicate_connection_pair | 0 | 1 | 0 | ✅ |
| off_grid_position | 0 | 0 | 1 | ✅ |

## Details

### clean_diff
Erweiterung mit sauberem Element und Verbindung

- Fehler: 0 | Warnungen: 0 | Infos: 0 | Status: ✅
- Keine Befunde

### duplicate_element_id
Diff enthält Element-ID, die bereits existiert

- Fehler: 1 | Warnungen: 0 | Infos: 0 | Status: ✅
- [ERROR] element.id.duplicate (Element E_FUNC_1): Element-ID 'E_FUNC_1' kommt mehrfach vor

### duplicate_element_name
Zwei neue Elemente besitzen identische Namen

- Fehler: 0 | Warnungen: 1 | Infos: 0 | Status: ✅
- [WARNING] element.name.duplicate (Name 'Bearbeiten'): Element-Name 'Bearbeiten' ist nicht eindeutig

### missing_name
Neues Element ohne Namen

- Fehler: 0 | Warnungen: 1 | Infos: 0 | Status: ✅
- [WARNING] element.name.missing (Element E_FUNC_4): Element 'E_FUNC_4' hat keinen Namen

### self_loop
Verbindung erzeugt Selbstschleife

- Fehler: 0 | Warnungen: 1 | Infos: 0 | Status: ✅
- [WARNING] connection.self_loop (Element E_FUNC_1, Connection C_LOOP): Verbindung 'C_LOOP' bildet eine Schleife auf Element 'E_FUNC_1'

### dangling_connection
Verbindung referenziert unbekanntes Element

- Fehler: 1 | Warnungen: 0 | Infos: 0 | Status: ✅
- [ERROR] connection.endpoint.missing (Connection C_DANGLING): Verbindung 'C_DANGLING' referenziert unbekannte Elemente

### unconnected_function
Neue Funktion ohne eingehende/ausgehende Verbindung

- Fehler: 0 | Warnungen: 1 | Infos: 0 | Status: ✅
- [WARNING] function.unconnected (Element E_FUNC_5): Funktionales Element 'E_FUNC_5' ist weder verbunden noch erreichbar

### duplicate_connection_id
Diff enthält Connection-ID, die bereits existiert

- Fehler: 1 | Warnungen: 0 | Infos: 0 | Status: ✅
- [ERROR] connection.id.duplicate (Connection C_START_F1): Connection-ID 'C_START_F1' kommt mehrfach vor

### duplicate_connection_pair
Relation zwischen zwei Elementen wird doppelt angelegt

- Fehler: 0 | Warnungen: 1 | Infos: 0 | Status: ✅
- [WARNING] connection.duplicate_pair (Connection C_DUP_PAIR): Verbindung 'C_DUP_PAIR' dupliziert eine bestehende Relation E_START->E_FUNC_1

### off_grid_position
Element wird nicht am Raster platziert

- Fehler: 0 | Warnungen: 0 | Infos: 1 | Status: ✅
- [INFO] element.position.off_grid (Element E_FUNC_7): Element 'E_FUNC_7' liegt nicht auf dem 50er Raster

## Gesamtübersicht

- Fälle: 10 | Fehler: 3 | Warnungen: 5 | Infos: 1