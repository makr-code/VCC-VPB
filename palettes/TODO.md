# Palette – Aufgabenübersicht

Stand: 2025-09-28

Dieser Backlog bündelt alle Schritte, um einen belastbaren Grundstock an JSON-Paletten für wiederverwendbare Prozessbausteine zu pflegen. Die Ziele: eindeutige IDs, konsistente Farb-/Symbolwelten, vollständige Referenz-Metadaten und begleitende Tests.

## Leitlinien

- **Dateiablage**: Jede Palette liegt unter `palettes/` als eigenständige `.json`. Referenzierte Diagramme liegen unter `processes/`.
- **Metadaten**: Für Referenz-Snippets stets `reference`-Objekt mit `id`, `snippet`, `element_type`, `default_name`, `auto_group`, `description`, `responsible_authority`, `legal_basis`, `deadline_days` und optionalen `label` / `category` ergänzen.
- **Farbcodes**: Helle Hintergrundfarben (`fill`) mit gutem Kontrast (`text_color`). Symbol-Emoji oder ein ASCII-Kürzel setzen.
- **Tests**: Für neue Paletteneinträge Sicherstellen, dass `tests/test_reference_palette.py` analog erweiterbar ist (Happy Path + Properties).
- **Priorisierung**: Nächste Schritte vorbereiten – `Leistungsklage`-Varianten, ergänzender Rechtsschutz (`Aussetzung der Vollziehung`) sowie neue Querschnitts-/Personalprozesse (Onboarding, Vertragsmanagement).
- **Qualität**: Vor jedem Commit prüfen, ob alle Referenzen auf existierende `.vpb.json` zeigen und Tests/Docs aktualisiert sind.

## Aufgaben – Bürgerdienste

- [x] `Terminvereinbarung – Bürgerbüro` (`processes/terminvereinbarung_einfach.vpb.json`) in `reference_palette.json`
- [x] `Meldebescheinigung – Mehrstufig` (`processes/meldebescheinigung_hierarchie.vpb.json`)
- [ ] `Anmeldung Wohnsitzwechsel` (`processes/umzug_ummeldung_medium.vpb.json`) – Palette-Eintrag anlegen, Fristen + Behörde ergänzen
- [ ] `Auskunft Melderegister` (`processes/melderegister_auskunft_low.vpb.json`) – Tag "Auskunft" vergeben, Info-Text vorbereiten

## Aufgaben – Wirtschaft & Förderung

- [x] `Gewerbeanmeldung – Standard` (`processes/gewerbeanmeldung_medium.vpb.json`)
- [x] `Förderantrag – Mehrstufig` (`processes/foerderantrag_mehrstufig.vpb.json`)
- [ ] `Gaststättenerlaubnis` – passendes Prozessmodell auswählen/erstellen, danach Palette-Eintrag erstellen
- [ ] `Handwerkskarte Ausgabe` – Datenquelle prüfen, ggf. neuen Prozess modellieren

## Aufgaben – Bauen & Umwelt

- [x] `Bauantrag – Prüfung komplex` (`processes/bauantrag_pruefung_komplex.vpb.json`)
- [x] `Umweltprüfung – Bauleitplanung` (`processes/bauleitplanung_umweltpruefung_20250923_vpb.json`)
- [ ] `Bauleitplanung – Offenlage` (`processes/bauleitplanung_offenlage_20250923_vpb.json`) – Referenzpalette ergänzen, Stil anpassen
- [ ] `Altlastenauskunft` – Prozess recherchieren, Snippet entwerfen, Palette anpassen

## Aufgaben – Immissionsschutz (BImSchG / LImSchG / BImSchV)

- [x] `Immissionsschutz-Genehmigung für Industrieanlagen` (`processes/immissionsschutz_genehmigung.vpb.json`) – Palette-Eintrag `ref-immissionsschutz-genehmigung`
	- Phasen: Vorantragsgespräch, Antragsannahme, Vollständigkeitsprüfung, UVP/Vorprüfung, Öffentlichkeitsbeteiligung, Entscheidung, Nebenbestimmungen, Bekanntgabe
	- Beteiligte: Antragsteller, Genehmigungsbehörde, Fachbehörden, Öffentlichkeit, ggf. EU-Notifizierung
	- Dokumente: Antragsunterlagen (Anhang 1 und 2 9. BImSchV), Sicherheitsbericht, Emissionsprognose, Betriebsplan, Umweltverträglichkeitsstudie
	- Fristen: § 10 Abs. 6, § 12 BImSchG (3/7 Monate), § 15 Abs. 1a BImSchG für Teilgenehmigungen; Wiedervorlage bei fehlenden Unterlagen
	- Verfahrensschritte: Antragskonferenz, UVP-Prüfung, Öffentlichkeitsbeteiligung, Entscheidung, Nebenbestimmungen
	- Varianten: vereinfachtes Verfahren (§ 19), Teilgenehmigung, Vorbescheid (§§ 8, 9)
- [x] `Anzeige wesentlicher Änderungen (§ 15 BImSchG)` (`processes/immissionsschutz_aenderungsanzeige.vpb.json`) – Palette-Eintrag `ref-immissionsschutz-aenderung`
	- Prüfen: Relevanzschwellen, Stellungnahme Behörden, Fristenmanagement (1 Monat), Dokumentationspflichten
	- Phasen: Anzeigeeingang, Vollständigkeitsprüfung, Bewertung der Änderung (wesentlich?), Stellungnahmen, Entscheidung (Genehmigungspflicht ja/nein), Bestätigung mit Auflagen
	- Dokumente: Änderungsschreiben, Vergleich Ist/Soll, Umweltbericht (falls relevant), ggf. Betriebs- oder Sicherheitsplan
	- Fristen: § 15 Abs. 1 BImSchG (1 Monat Reaktionsfrist), Option zur Verlängerung bei komplexen Prüfungen
- [x] `Emissionsüberwachung & Jahresbericht` (`processes/immissionsschutz_emissionsmonitoring.vpb.json`) – Palette-Eintrag `ref-immissionsschutz-monitoring`
	- Aufgaben: Messstellenbeauftragung, kontinuierliche Messung, Berichterstellung, Upload an Behörde (e-KAS)
	- Edge Cases: Abweichungen, Ersatzmessungen, Fristverlängerung beantragen
	- Phasen: Jahresplanung, Messdatenerfassung, Validierung, Berichtserstellung, Übermittlung, Nachverfolgung von Auflagen
	- Rollen: Betreiber, anerkannte Messstelle, Immissionsschutzbehörde, ggf. Zertifizierungsstelle
	- Dokumente: Messberichte, Kalibrierungsprotokolle, Betriebsstundennachweise, Emissionsjournal
	- Fristen: Berichtserstellung i. d. R. bis 31.03. Folgejahr, unverzügliche Meldung bei Grenzwertüberschreitung
- [x] `Störfall- & Notfallmanagement` (`processes/immissionsschutz_stoerfallmanagement.vpb.json`) – Palette-Eintrag `ref-immissionsschutz-stoerfall`
	- Inhalte: Sicherheitsbericht, Alarm- und Gefahrenabwehrplan, Übungen, Behördenkommunikation
	- Phasen: Einstufung (Betriebsbereich), Erstellung Sicherheitsbericht, Kommunikation mit Behörden/Öffentlichkeit, Notfallübungen, Ereignisbewältigung, Nachbereitung
	- Rollen: Betreiber (Betriebsbereichsleiter, Sicherheitsbeauftragter), Katastrophenschutzbehörde, Feuerwehr, Leitstelle, Öffentlichkeit
	- Dokumente: Sicherheitsbericht, Alarm- und Gefahrenabwehrplan, Sicherheitsmanagementsystem, Informationsblätter für Öffentlichkeit
	- Fristen: Aktualisierung Sicherheitsbericht alle 5 Jahre, Übung mindestens alle 3 Jahre, unverzügliche Meldung von Störfällen
- [x] `Kommunaler Lärmaktionsplan` (`processes/immissionsschutz_laermaktionsplan.vpb.json`) – Prozess gem. §§ 47a ff. BImSchG & 18., 32., 39. BImSchV modelliert
	- Enthält Zyklus von Lärmkarten bis Monitoring inkl. Beteiligung/Abwägung & Ratsbeschluss, Palette `ref-immissionsschutz-laermaktionsplan`
- [x] `Genehmigung nach Landes-Immissionsschutzgesetz (Sondernutzungen)` (`processes/immissionsschutz_sondernutzung.vpb.json`) – Verfahren inklusive Auflagen- und Kontrolllogik umgesetzt
	- Palette `ref-immissionsschutz-sondernutzung`, Nachforderungen/Kooperationsschleifen abgebildet (Ortstermin, Auflagen, Monitoring)

## Aufgaben – Verwaltungsverfahren & Rechtsschutz

- [x] `Allgemeines Verwaltungsverfahren – Bescheidserlass` (`processes/verwaltungsverfahren_bescheid.vpb.json`)
- [x] `Anhörung Beteiligter – § 28 VwVfG` (`processes/verwaltungsverfahren_anhoerung.vpb.json`)
- [x] `Widerspruchsverfahren – §§ 68 ff. VwGO` (`processes/verwaltungsverfahren_widerspruch.vpb.json`)
- [x] `Anfechtungsklage – §§ 42 ff. VwGO` (`processes/verwaltungsgericht_anfechtungsklage.vpb.json`)
- [x] `Verpflichtungsklage / Untätigkeitsklage` (`processes/verwaltungsgericht_verpflichtungsklage.vpb.json`)
- [x] `Eilverfahren (§ 80 Abs. 5 VwGO)` (`processes/verwaltungsgericht_eilverfahren_80_5.vpb.json`)
- [x] `Fortsetzungsfeststellungsklage` – Prozess modelliert, Palette-Eintrag `ref-fortsetzungsfeststellung` aktiv
- [ ] `Leistungsklage (echte Leistung)` – Weitere Szenarien analysieren, Snippet aufbauen

**Nächste Kandidaten (Vorbereitung)**

- [x] `Fortsetzungsfeststellungsklage` (`processes/verwaltungsgericht_fortsetzungsfeststellungsklage.vpb.json`)
	- Feststellungsinteresse-Zweig (Wiederholungsgefahr/Rehabilitationsinteresse) modelliert
	- Palette: `ref-fortsetzungsfeststellung` mit rechtlicher Kurzbeschreibung und Standardfristen
- [ ] `Leistungsklage` – Pflicht- vs. echte Leistung differenzieren, ggf. zwei Varianten modellieren
	- Quellen: §§ 43, 111, 113 Abs. 5 VwGO (Verpflichtungsurteil) vs. echte Leistungsklage (fehlender Verwaltungsakt)
	- Szenarien definieren: behördliche Verpflichtung zur positiven Handlung / Zahlung / Erstattung
	- Snippet-Umfang: Eingang, Sachprüfung, Tenor (Leistungsverpflichtung), Vollstreckungshinweis (§ 167 VwGO)
- [ ] `Antrag auf Aussetzung der Vollziehung` – Ergänzend zum Eilverfahren, falls Abgrenzung erforderlich

## Aufgaben – Querschnitt / Verwaltung intern

- [x] `Posteingang & Verteilung` (`processes/verwaltung_posteingang_verteilung.vpb.json`) – Palette-Eintrag `ref-posteingang` gebaut
	- Eingangskanäle (Papier, E-Mail, De-Mail) berücksichtigen, Fristenhandling dokumentieren
	- Übergabe an Fachverfahren / Registratur mit Aktenzeichen und Eskalationspfad
	- Digitalisierung: Scanstraße/OCR, Qualitätskontrolle, Originalarchivierung, Rücksendung von Originalen
	- Security & Datenschutz: Virenscan, DSGVO-konforme Weiterleitung, Geheimschutz-Klassifizierung
	- Servicezeiten & SLAs definieren (z. B. 24h Scan, 48h Routing) und Eskalationspfad für Fristensachen
- [x] `Kommunikationsmittel – Eingang & Routing` (`processes/verwaltung_kommunikationsmittel_flow.vpb.json`) – Palette-Eintrag `ref-kommunikationsmittel` erstellt
	- Mediumstrennung (Digital, Telefon, Brief/Fax, Datenträger) mit Sicherheits- und Dokumentationspflichten modelliert
	- Routing, Klassifizierung und Eingangsbestätigung in Standardfristen abgebildet
- [x] `Rechnungseingang & Prüfung` (`processes/verwaltung_rechnungseingang_pruefung.vpb.json`) – Palette-Eintrag `ref-rechnungseingang` erstellt
	- Schritte: Eingang, formale Prüfung, sachliche Prüfung, Freigabe, Zahlung anweisen
	- Rechtsgrundlagen (HGrG, GO, Kommunale Regelungen) verlinken, Fristen (Skonto) aufnehmen
	- Rollen: Kreditorenbuchhaltung, Fachvorgesetzte, Kämmerei, ggf. Vier-Augen-Prinzip dokumentieren
	- Medienmix: E-Rechnung (XRechnung/ZUGFeRD), Papierbelege, E-Mail-Anhänge – mit Digitalisierungsstufe vermerken
	- Kontrollpunkte: Betragsabhängige Freigabeschwellen, Budgetkontrolle, Compliance-Check (Vergabe, § 55 BHO/KomVO)
- [x] `Beschlussvorlage erstellen` (`processes/verwaltung_beschlussvorlage_erstellen.vpb.json`) – Palette-Eintrag `ref-beschlussvorlage`
	- Beteiligte: Fachbereich, Kämmerei, Gremienbüro; Schleife für Feedback berücksichtigen
	- Ergebnis: Vorlage, Stellungnahme, Veröffentlichung im Ratsinformationssystem
	- Meilensteine: Entwurf, Abstimmungsrunde, finale Freigabe, Veröffentlichung & Archiv
	- Pflichtinhalte: Sachverhalt, Finanzielle Auswirkungen, Beschlusspunkt, Rechtsgrundlage
	- Fristen: Einreichung bis Gremienlauf, Feedbackfenster, Versand an Mitglieder (z. B. 7 Tage vorher)

**Qualitäts-Bausteine (geplant)**

- [ ] Validierungs-Skript: Prüft Palette auf fehlende Felder, doppelte IDs, defekte Pfade
- [ ] Testfall erweitern: Palette-Eintrag ohne optionale Felder (Symbol/Farbe) akzeptiert


## Qualität & Automatisierung

- [ ] Palette-Dokumentation (`palettes/README.md`) um Farbschema-/Emoji-Guidelines erweitern
- [ ] Automatischen Check (Lint) für Referenzdateien implementieren (`validation_manager` erweitern)
	- Prüfen: JSON-Schema (Pflichtfelder), Pfad-Existenz für `snippet`, Hex-Farbvalidierung, eindeutige IDs/Symbole
	- Integration: CLI-Befehl `python -m validation_manager lint --palettes` oder pytest-Fixture
- [ ] Testsuite um Szenario "Palette Item ohne optionales Feld" ergänzen
	- Neuer Testfall erzeugt Minimal-Item (nur Pflichtfelder) und prüft, dass PaletteLoader & Linter nicht fehlschlagen
	- Edgecase: Fehlende `text_color` + `fill` → Default-Handling dokumentieren

## Weiterentwicklungsmöglichkeiten

### Palette-Ausbau (in Planung)

- [ ] `Leistungsklage – echte Leistung` (2 Varianten: Leistungspflicht & Geldleistung) – Snippets ableiten, Palette-Kachel gestalten
- [ ] `Aussetzung der Vollziehung` – Kurzverfahren für behördliche Entscheidung nach § 80 Abs. 4 VwGO
- [ ] `Dienstreisegenehmigung & Abrechnung` – Personalreferenzprozess mit BEA/Tax-relevanten Prüfschritten
- [ ] `Personal-Onboarding` – Willkommenspaket, IT-Berechtigungen, Schulungsnachweise
- [ ] `Vertragsmanagement (Energie/Dienstleistung)` – Laufzeitenkontrolle, Kündigungsfristen, Verlängerungen

### Tooling & Governance

- [ ] Palette-Validator als CLI (`vpb validation palettes`) mit JSON-Schema-Ausgabe & Farb-Check
- [ ] Automatisierte Screenshot-/Preview-Generierung für Referenzprozesse (Canvas-Export als PNG)
- [ ] Metadata-Lint: Prüfen auf doppelte Emojis/Farbkonflikte und kollidierende `default_name`
- [ ] Git-Hook/Ruff-ähnlicher Check für `.vpb.json`-Formatierung und konsistente Sortierung der Felder

### Dokumentation & Enablement

- [ ] `palettes/README.md`: Abschnitt "Interne Verwaltung" mit Anwendungsbeispielen ergänzen
- [ ] How-to-Guide im `docs/`-Ordner für "Eigene Referenzprozesse modellieren" (inkl. Checkliste)
- [ ] Wissensdatenbank-Eintrag (Notion/SharePoint) für Cross-Cutting-Prozesse mit Ansprechpartnern & KPIs

## Nächste Review

- Wöchentlicher Sync: Prüfen, welche Snippets modelliert wurden und ob neue Domänen (z. B. Soziales, Sicherheit) aufgenommen werden sollen.
- Bei Abschluss einer Kategorie Checkbox abhaken und Kurznotiz im `docs/VPB_TODO.md` ergänzen.
