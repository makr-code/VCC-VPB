# VPB Process Designer - Erweiterte Mausintegration

## Neue Features Version 1.2 (22. August 2025)

### 🖱️ Verbesserte Mausintegration

#### Pan-Funktion (Canvas verschieben)
- **Mittlere Maustaste halten + Bewegen:** Canvas-Ausschnitt verschieben
- **Visual Feedback:** Cursor wechselt zu "fleur" (Vierwege-Pfeil)
- **Console-Log:** Aktivierung/Deaktivierung wird protokolliert
- **Natürliches Gefühl:** Invertierte Bewegung für intuitive Bedienung

```python
# Implementation Details
def _on_middle_mouse_press(self, event):
    self.pan_active = True
    self.configure(cursor="fleur")  # Vierwege-Pfeil-Cursor

def _on_middle_mouse_drag(self, event):
    # Berechne Bewegungsdelta und aktualisiere Canvas-View
    delta_x = event.x - self.pan_start_x
    new_x = self.pan_start_view_x - delta_x  # Invertiert für natürliches Gefühl
```

#### Zoom-Funktion (Mausrad)
- **Mausrad nach oben:** Hineinzoomen (Vergrößern)
- **Mausrad nach unten:** Herauszoomen (Verkleinern)
- **Zoom-Zentrum:** Mausposition beim Zoomen
- **Cross-Platform:** Windows & Linux Support
- **Zoom-Limits:** 10% - 500% (konfigurierbar)

```python
# Zoom-Parameter
self.zoom_factor = 1.0     # Aktueller Zoom-Faktor
self.min_zoom = 0.1        # Minimaler Zoom (10%)
self.max_zoom = 5.0        # Maximaler Zoom (500%)
self.zoom_step = 0.1       # Zoom-Schritte (10%)
```

#### Intelligente Zoom-Zentrierung
- **Maus-zentriert:** Zoom zentriert sich auf Mausposition
- **Canvas-Koordinaten:** Korrekte Umrechnung zwischen Screen- und Canvas-Koordinaten
- **Scroll-Region:** Automatische Anpassung der scrollbaren Region

### 🛠️ Neue Toolbar-Kontrollen

#### Zoom-Kontrollen
- **🔍−** Zoom Out (Verkleinern)
- **100%** Zoom-Level Anzeige (aktualisiert sich live)  
- **🔍+** Zoom In (Vergrößern)
- **🎯** Zoom Reset (zurück auf 100%)
- **📐** Zoom to Fit (alle Elemente sichtbar machen)

#### Grid-System mit Zoom-Unterstützung
- **Adaptive Grid-Darstellung:** Grid-Dichte passt sich an Zoom-Level an
- **Performance-Optimierung:** Überspringt Grid bei sehr kleinem Zoom
- **Zoom-bewusste Spacing:** Reduzierte Grid-Linien bei starkem Zoom-Out

```python
# Grid-Optimierung für verschiedene Zoom-Level
effective_grid_size = self.grid_size * self.zoom_factor

if effective_grid_size < 10:
    grid_spacing = self.grid_size * 5    # Jede 5. Linie
elif effective_grid_size < 5:
    grid_spacing = self.grid_size * 10   # Jede 10. Linie
```

### 📊 Technische Details

#### Event-Binding-System
```python
# Erweiterte Maus-Events
self.bind("<Button-2>", self._on_middle_mouse_press)
self.bind("<B2-Motion>", self._on_middle_mouse_drag)  
self.bind("<ButtonRelease-2>", self._on_middle_mouse_release)
self.bind("<MouseWheel>", self._on_mousewheel_zoom)
self.bind("<Button-4>", self._on_mousewheel_zoom)  # Linux
self.bind("<Button-5>", self._on_mousewheel_zoom)  # Linux
```

#### Zoom-Mathematik
```python
def _apply_zoom(self, new_zoom_factor, mouse_x, mouse_y):
    # Maus-Position in Canvas-Koordinaten
    canvas_x = self.canvasx(mouse_x)  
    canvas_y = self.canvasy(mouse_y)
    
    # Zoom-Verhältnis berechnen
    zoom_ratio = new_zoom_factor / old_zoom_factor
    
    # Alle Canvas-Objekte skalieren
    self.scale("all", canvas_x, canvas_y, zoom_ratio, zoom_ratio)
```

#### Performance-Optimierungen
- **Lazy Grid-Redraw:** Grid nur bei Bedarf neu zeichnen
- **Bbox-Updates:** Scroll-Region dynamisch anpassen
- **Event-Throttling:** Vermeidung von zu häufigen Updates

### 🎯 Benutzerfreundlichkeit

#### Intuitive Bedienung
- **Standard-Verhalten:** Wie in professionellen CAD/Design-Tools
- **Visual Feedback:** Cursor-Änderungen und Console-Logs
- **Smooth Experience:** Keine merkbaren Verzögerungen

#### Keyboard-Integration (Vorbereitet)
```python
# Zukünftige Erweiterungen
# Strg + Mausrad = Schneller Zoom
# Alt + Mittlere Maus = Konstrained Pan
# Leertaste + Maus = Temporärer Pan
```

### 🧪 Test-Szenarien

#### Getestete Funktionen ✅
1. **Pan mit mittlerer Maustaste**
   - Smooth scrolling in alle Richtungen
   - Korrekte Cursor-Anzeige
   - Natürliches Bewegungsgefühl

2. **Zoom mit Mausrad**
   - Stufenloser Zoom von 10% bis 500%
   - Maus-zentrierte Vergrößerung
   - Cross-Platform-Kompatibilität

3. **Toolbar-Zoom-Kontrollen**
   - Alle Buttons funktional
   - Live-Update der Zoom-Anzeige
   - Zoom to Fit für geladene Prozesse

4. **Grid-System mit Zoom**
   - Adaptive Grid-Darstellung
   - Performance bei starkem Zoom
   - Snap-to-Grid funktioniert bei allen Zoom-Levels

### 🔮 Geplante Erweiterungen

#### Erweiterte Navigation
- **Mini-Map:** Übersichtskarte für große Prozesse
- **Navigator-Panel:** Schnelle Navigation zu Elementen
- **Bookmark-System:** Gespeicherte Ansichten

#### Zusätzliche Mausfunktionen
- **Lasso-Selection:** Mehrere Elemente mit Maus auswählen
- **Smart-Pan:** Automatisches Panning bei Drag-and-Drop am Rand
- **Zoom-Bereiche:** Definierte Zoom-Presets für verschiedene Arbeitsschritte

### 📝 Bedienungshinweise

#### Maus-Shortcuts
| Aktion | Beschreibung |
|--------|-------------|
| **Mittlere Maustaste halten + Bewegen** | Canvas verschieben (Pan) |
| **Mausrad drehen** | Zoom In/Out |
| **Linke Maustaste** | Element auswählen/bewegen |
| **Rechte Maustaste** | Kontext-Menü |

#### Toolbar-Shortcuts
| Button | Beschreibung |
|--------|-------------|
| **🔍−** | Zoom Out (90%) |
| **🔍+** | Zoom In (110%) |
| **🎯** | Zoom Reset (100%) |
| **📐** | Zoom to Fit (alle Elemente sichtbar) |

---

**🚀 Der VPB Process Designer bietet jetzt professionelle Navigation und Zoom-Funktionalität wie in modernen CAD-Anwendungen!**

*Entwickelt vom UDS3 Development Team - 22. August 2025*
