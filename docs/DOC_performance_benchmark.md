# Merge Performance Benchmark

Der Performance-Test (`tests/test_merge_performance.py`) misst die Laufzeit des Mergens synthetischer Payloads mit ansteigender Größe und protokolliert nur – er schlägt nicht fehl, solange keine explizite Schwellwert-Umgebungskonfiguration gesetzt ist.

## Ziele
- Laufzeit-Trend beobachten (Regressionen früh erkennen)
- Keine flakey CI-Fails durch schwankende Maschinenlast
- Optionale Grenzwerte per Environment Variable zulassen

## Testprinzip
1. Generiert Payloads mit z. B. 200, 500, 1000 neuen Elementen (lineare Kette oder einfache Verbindungsstruktur)
2. Führt `merge_full` für jede Größe aus
3. Misst `duration_s` via `time.perf_counter()`
4. Gibt Ergebnisse über `print` oder Testausgabe aus
5. Wenn `MERGE_BENCH_THRESHOLD_MS` gesetzt ist, kann der Test optional assert-en (aktuell deaktiviert – Logging only)

## Beispielausgabe (verkürzt)
```
MERGE PERF size=200 duration=0.038s
MERGE PERF size=500 duration=0.121s
MERGE PERF size=1000 duration=0.250s
```

## Aktivierung eines Schwellwerts (optional)
In einer lokalen Session (PowerShell):
```powershell
$env:MERGE_BENCH_THRESHOLD_MS = 400
pytest tests/test_merge_performance.py::test_merge_performance_logging -q
```
Wenn alle Durchläufe < 400ms (je Größe) bleiben, besteht der Test. Andernfalls würde ein AssertionError ausgelöst – aktuell bewusst deaktiviert, um Stabilität zu priorisieren.

## Erweiterungsideen
- Persistierung der Messwerte (JSONL) für Zeitreihenanalyse
- 95. Perzentil über N Wiederholungen (statt Einzelmessung)
- Vergleich gegen Baseline (z. B. vorheriges Git-Commit)
- Integration mit Telemetrie (`merge_full` Events aggregieren)
