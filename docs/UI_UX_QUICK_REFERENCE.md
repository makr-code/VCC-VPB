# UI/UX Verbesserungen - Quick Reference

## Neue UI-Systeme

### Theme System
```python
from vpb.ui.theme import get_theme_manager

theme = get_theme_manager()
primary = theme.get_color("primary")      # "#2563EB"
bg = theme.get_color("bg_primary")        # "#FFFFFF"
```

### Icon System
```python
from vpb.ui.icons import get_icon_manager

icons = get_icon_manager()
save = icons.get("save")    # "💾"
new = icons.get("new")      # "📄"
```

### Font System
```python
from vpb.ui.fonts import get_font_manager

fonts = get_font_manager()
heading = fonts.get("heading_1")  # ("Segoe UI", 20, "bold")
body = fonts.get("body")           # ("Segoe UI", 12, "normal")
```

### Spacing System
```python
from vpb.ui.spacing import get_spacing_manager

spacing = get_spacing_manager()
margin = spacing.get_spacing("md")     # 16
padding = spacing.get_padding("normal") # (8, 4)
```

## Verfügbare Icons

### Datei-Operationen
📄 new | 📂 open | 💾 save | 📤 export | 📥 import | ✖ close | 🕒 recent

### Bearbeiten
↶ undo | ↷ redo | ✂ cut | 📋 copy | 🗑 delete | ⧉ duplicate

### Ansicht
🔍+ zoom_in | 🔍− zoom_out | ⊡ zoom_fit | ⊙ zoom_100 | ⛶ fullscreen | ⊞ grid | 📏 rulers

### Layout
◧ align_left | ◫ align_center | ◨ align_right | ⬒ align_top | ⬓ align_middle | ⬔ align_bottom
⬌ distribute_h | ⬍ distribute_v

### Elemente
➕ add | ⧉ group | ⧈ ungroup

### Status
✓ success | ⏳ pending | ⟳ running | ✗ failed | ⚠ warning | ℹ info

### AI/Chat
🤖 ai | 💬 chat | ➤ send | ⏹ stop | 📎 attach

## Farbpalette

### Primärfarben
- Primary: #2563EB (Blau)
- Success: #10B981 (Grün)
- Warning: #F59E0B (Orange)
- Error: #EF4444 (Rot)

### Hintergrundfarben
- bg_primary: #FFFFFF (Weiß)
- bg_secondary: #F8FAFC (Hellgrau)
- bg_tertiary: #F1F5F9 (Grau)

### Textfarben
- text_primary: #0F172A (Dunkel)
- text_secondary: #475569 (Grau)
- text_muted: #94A3B8 (Hellgrau)

## Schriftarten

### Plattform-spezifisch
- Windows: Segoe UI / Consolas
- macOS: SF Pro / SF Mono
- Linux: Ubuntu / Ubuntu Mono

### Hierarchie
- heading_1: 20px bold
- heading_2: 16px bold
- heading_3: 14px bold
- body: 12px normal
- caption: 10px normal

## Spacing (8pt Grid)

### Abstände
- xs: 4px
- sm: 8px
- md: 16px
- lg: 24px
- xl: 32px
- xxl: 48px

### Padding
- tight: (4, 2)
- normal: (8, 4)
- comfortable: (12, 6)
- spacious: (16, 8)

## Tests ausführen

```bash
python -m unittest tests.ui.test_ui_systems -v
```

## Dokumentation

- **Verbesserungsplan**: [UI_UX_IMPROVEMENT_PLAN.md](UI_UX_IMPROVEMENT_PLAN.md)
- **Abschlussbericht**: [UI_UX_COMPLETION_REPORT.md](UI_UX_COMPLETION_REPORT.md)

## Beispiel-Integration

```python
import tkinter as tk
from vpb.ui.theme import get_theme_manager
from vpb.ui.icons import get_icon_manager
from vpb.ui.fonts import get_font_manager
from vpb.ui.spacing import get_spacing_manager

# Manager holen
theme = get_theme_manager()
icons = get_icon_manager()
fonts = get_font_manager()
spacing = get_spacing_manager()

# Button erstellen
btn = tk.Button(
    text=f"{icons.get('save')} Speichern",
    font=fonts.get("button"),
    bg=theme.get_color("toolbar_bg"),
    fg=theme.get_color("text_primary"),
    padx=spacing.get_padding("normal")[0],
    pady=spacing.get_padding("normal")[1]
)

# Hover-Effekt
btn.bind("<Enter>", lambda e: btn.config(
    bg=theme.get_color("bg_hover")
))
btn.bind("<Leave>", lambda e: btn.config(
    bg=theme.get_color("toolbar_bg")
))
```
