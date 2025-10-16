# VPB Showcase – Anleitung

Dieses Showcase demonstriert die wichtigsten Fähigkeiten des VPB-Designers (Pan/Zoom, Grid/Snap, Ruler, Routing, Pfeilspitzen, Labels, Gruppen/Container inkl. Kompaktdarstellung, SUBPROCESS Inline/Öffnen, Diagramm↔Code Roundtrip und Validierung).

## Dateien
- processes/vpb_showcase_all_features_20250923.vpb.json – Hauptdiagramm mit allen Elementarten, Verbindungstypen und zwei Gruppen (eine davon kollabiert).
- processes/vpb_showcase_subprocess_20250923.vpb.json – Referenzierter Subprozess für das SUBPROCESS-Element.

## Laden und ausprobieren
1. Designer starten (z. B. via VPB-App).
2. Im Menü Datei → Öffnen das Hauptdiagramm laden: `processes/vpb_showcase_all_features_20250923.vpb.json`.
3. Zoom auf 50% oder darunter setzen, um die automatische Kompaktdarstellung von Gruppen zu sehen. Bei >50% wieder normale Darstellung.
4. Gruppe „Prüfphase“ auswählen – im Eigenschaften-Panel:
   - Mitgliederliste doppelklicken, um ein Mitglied auf der Zeichenfläche zu selektieren.
   - „Aus Auswahl hinzufügen/entfernen“ ausprobieren.
   - „Eingeklappt“ an-/abwählen und die Änderung auf der Zeichenfläche beobachten.
5. SUBPROCESS „Beteiligung Fachämter“: Rechtsklick → „Referenz öffnen“ oder „Inline expandieren“ testen.
6. Verbindungen anklicken und den Routing-Stil sowie Pfeilspitzen im UI wechseln (Link-Modus in der Palette nutzen), Labels verschieben.
7. Diagramm↔Code: Zum Code-Tab wechseln, JSON inspizieren, validieren und zurückschreiben; Fehler werden im Diagramm markiert.

Viel Spaß beim Erkunden! ✨
