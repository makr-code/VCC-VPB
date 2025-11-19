# Getting Started / Erste Schritte

**Version:** 0.5.0  
**Level:** Beginner / Anfänger

---

## Deutsch

### Installation

#### Voraussetzungen
- Python 3.8 oder höher
- pip (Python Package Manager)
- Git

#### Schritt 1: Repository klonen

```bash
git clone https://github.com/makr-code/VCC-VPB.git
cd VCC-VPB
```

#### Schritt 2: Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

**Hauptabhängigkeiten:**
- PyQt6 - GUI Framework
- FastAPI - REST API Server
- SQLAlchemy - Datenbank ORM
- Pydantic - Datenvalidierung

#### Schritt 3: VPB starten

**Option A: Designer GUI**
```bash
python vpb_app.py
```

**Option B: API Server (für Backend-Entwicklung)**
```bash
uvicorn api.uds3_vpb_fastapi:app --reload
```
Dann öffnen: http://localhost:8000/api/docs

### Erste Schritte mit dem Designer

1. **Neuen Prozess erstellen**
   - Menü: `Datei` → `Neu`
   - Oder: `Ctrl+N`

2. **Elemente hinzufügen**
   - Palette auf der linken Seite verwenden
   - Element per Drag & Drop auf Canvas ziehen
   - Verfügbare Elementtypen: [[SPS-Elements]]

3. **Elemente verbinden**
   - Klicken Sie auf den Ausgang eines Elements
   - Ziehen Sie zur Eingang eines anderen Elements
   - Loslassen um Verbindung zu erstellen

4. **Eigenschaften bearbeiten**
   - Element auswählen
   - Eigenschaften-Panel auf der rechten Seite
   - Werte anpassen

5. **Speichern**
   - Menü: `Datei` → `Speichern`
   - Oder: `Ctrl+S`
   - Format: JSON (.vpb.json)

### Nächste Schritte

- **[[User-Guide]]** - Vollständige Funktionsübersicht
- **[[SPS-Elements]]** - Elementtypen im Detail
- **[[Examples]]** - Beispielprozesse
- **[[Keyboard-Shortcuts]]** - Produktivität steigern

---

## English

### Installation

#### Prerequisites
- Python 3.8 or higher
- pip (Python Package Manager)
- Git

#### Step 1: Clone Repository

```bash
git clone https://github.com/makr-code/VCC-VPB.git
cd VCC-VPB
```

#### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

**Main Dependencies:**
- PyQt6 - GUI Framework
- FastAPI - REST API Server
- SQLAlchemy - Database ORM
- Pydantic - Data validation

#### Step 3: Start VPB

**Option A: Designer GUI**
```bash
python vpb_app.py
```

**Option B: API Server (for backend development)**
```bash
uvicorn api.uds3_vpb_fastapi:app --reload
```
Then open: http://localhost:8000/api/docs

### First Steps with the Designer

1. **Create New Process**
   - Menu: `File` → `New`
   - Or: `Ctrl+N`

2. **Add Elements**
   - Use palette on left side
   - Drag & drop element onto canvas
   - Available element types: [[SPS-Elements]]

3. **Connect Elements**
   - Click on output of an element
   - Drag to input of another element
   - Release to create connection

4. **Edit Properties**
   - Select element
   - Properties panel on right side
   - Adjust values

5. **Save**
   - Menu: `File` → `Save`
   - Or: `Ctrl+S`
   - Format: JSON (.vpb.json)

### Next Steps

- **[[User-Guide]]** - Complete feature overview
- **[[SPS-Elements]]** - Element types in detail
- **[[Examples]]** - Example processes
- **[[Keyboard-Shortcuts]]** - Boost productivity

---

## Troubleshooting / Fehlerbehebung

### Common Issues / Häufige Probleme

**Problem: "ModuleNotFoundError"**
```bash
# Lösung / Solution:
pip install -r requirements.txt --upgrade
```

**Problem: "Qt platform plugin could not be initialized"**
```bash
# Linux:
sudo apt-get install python3-pyqt6
# macOS:
brew install pyqt@6
```

**Problem: GUI startet nicht / GUI doesn't start**
- Überprüfen Sie Python Version: `python --version` (muss ≥ 3.8 sein)
- Check Python version: `python --version` (must be ≥ 3.8)

### More Help / Weitere Hilfe

- **[[Troubleshooting]]** - Vollständige Problemlösungen
- **[[FAQ]]** - Häufig gestellte Fragen
- **GitHub Issues:** https://github.com/makr-code/VCC-VPB/issues

---

## What's Next?

### For Users / Für Benutzer
1. Read the **[[User-Guide]]**
2. Explore **[[Examples]]**
3. Learn **[[SPS-Elements]]**

### For Developers / Für Entwickler
1. Setup **[[Development-Guide]]**
2. Understand **[[Architecture]]**
3. Read **[[API-Reference]]**

---

[[Home]] | [[User-Guide]] | [[Examples]]
