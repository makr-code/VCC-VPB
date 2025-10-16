# VPB CLI - Quick Reference ⚡

## 🚀 Häufigste Befehle

```bash
# Normal starten
python vpb_app.py

# Datei laden
python vpb_app.py --load myfile.vpb.json

# Debug-Modus
python vpb_app.py --load myfile.vpb.json --debug --info

# Export
python vpb_app.py --load myfile.vpb.json --export output.pdf

# Präsentation
python vpb_app.py --load demo.vpb.json --fullscreen --no-grid

# Hilfe
python vpb_app.py --help
```

---

## 📝 Alle Argumente

| Kurz | Lang | Beschreibung | Beispiel |
|------|------|--------------|----------|
| `-l` | `--load FILE` | Datei laden | `-l test.vpb.json` |
| `-e` | `--export FILE` | Exportieren | `-e out.pdf` |
| `-d` | `--debug` | Debug-Modus | `-d` |
| `-i` | `--info` | Canvas-Info | `-i` |
| `-v` | `--validate` | Validieren | `-v` |
| `-h` | `--help` | Hilfe | `-h` |
| | `--grid` | Grid an | `--grid` |
| | `--no-grid` | Grid aus | `--no-grid` |
| | `--snap` | Snap aktivieren | `--snap` |
| | `--geometry WxH` | Fenster-Größe | `--geometry 1920x1080` |
| | `--fullscreen` | Vollbild | `--fullscreen` |
| | `--version` | Version | `--version` |

---

## 🎯 Workflows

### Development
```bash
python vpb_app.py -l current.vpb.json -d --snap
```

### Testing
```bash
python vpb_app.py -l test.vpb.json -d -i -v
```

### Presentation
```bash
python vpb_app.py -l demo.vpb.json --fullscreen --no-grid
```

### Batch Export
```bash
python vpb_app.py -l file.vpb.json -e output.pdf
python vpb_app.py -l file.vpb.json -e output.svg
python vpb_app.py -l file.vpb.json -e output.png
```

---

## 💡 Kombinationen

```bash
# Alles auf einmal
python vpb_app.py \
    --load myfile.vpb.json \
    --debug \
    --info \
    --validate \
    --snap \
    --geometry 1920x1080

# Quick Debug
python vpb_app.py -l file.vpb.json -d -i

# Production Export
python vpb_app.py -l process.vpb.json -e final.pdf --no-grid
```

---

✅ **VPB Process Designer 0.2.0-alpha**
