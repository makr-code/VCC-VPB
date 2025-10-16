import os
import sys
import time
import types
import tkinter as tk
import pytest

# Wir importieren die App-Klasse aus vpb_app
from vpb_app import VPBDesignerApp

@pytest.mark.skipif('DISPLAY' not in os.environ and sys.platform.startswith('linux'), reason='Tkinter display not available')
def test_merge_adds_elements_and_renames():
    # Headless Tk root erstellen
    app = VPBDesignerApp()
    try:
        # Ausgangsdiagramm: Ein Start- und End-Event + Verbindung
        e1 = app.canvas.add_element('START_EVENT', name='Start', at=(0,0))
        e2 = app.canvas.add_element('END_EVENT', name='Ende', at=(200,0))
        app.canvas.add_connection(source_id=e1.element_id, target_id=e2.element_id, connection_type='SEQUENCE')
        existing_ids_before = set(app.canvas.elements.keys()) | set(app.canvas.connections.keys())

        # Künstliches LLM-Diagramm mit kollidierenden IDs (benutzt gleiche IDs wie bestehend + neue)
        incoming = {
            'metadata': {'name': 'MergeTest'},
            'elements': [
                {'element_id': e1.element_id, 'element_type': 'START_EVENT', 'name': 'StartNeu', 'x': 0, 'y': 100},  # Konflikt
                {'element_id': 'F001', 'element_type': 'FUNCTION', 'name': 'Neue Funktion', 'x': 120, 'y': 100},
            ],
            'connections': [
                {'connection_id': 'C001', 'source_element': e1.element_id, 'target_element': 'F001', 'connection_type': 'SEQUENCE', 'description': ''},
            ]
        }

        # Merge aufrufen
        app._merge_full_process_json(incoming)

        # Auf Abschluss des Hintergrund-Tasks warten
        deadline = time.time() + 3.0
        while app.tasks.get_pending("merge_full"):
            app.update()
            time.sleep(0.05)
            if time.time() > deadline:
                pytest.fail("Merge-Task hat nicht rechtzeitig abgeschlossen")
        # Letzte Events verarbeiten
        app.update()

        # Erwartungen:
        # - Neues FUNCTION-Element existiert
        fn = [el for el in app.canvas.elements.values() if el.element_type == 'FUNCTION']
        assert fn, 'FUNCTION Element wurde nicht hinzugefügt'
        # - Start-Konflikt wurde umbenannt (neues Start-Element mit anderer ID)
        start_ids = [el.element_id for el in app.canvas.elements.values() if el.name.startswith('Start')]
        assert len(start_ids) >= 1
        assert any(sid != e1.element_id for sid in start_ids), 'Konflikt-ID wurde nicht umbenannt'
        # - Verbindung hinzugefügt (mindestens 2 Verbindungen jetzt)
        assert len(app.canvas.connections) >= 2
        # - Keine bestehenden IDs verschwunden
        after_ids = set(app.canvas.elements.keys()) | set(app.canvas.connections.keys())
        assert existing_ids_before.issubset(after_ids)
    finally:
        try:
            app.destroy()
        except Exception:
            pass
