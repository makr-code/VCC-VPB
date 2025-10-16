#!/usr/bin/env python3
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS Protected Module
WARNING: This file contains embedded protection keys. 
Modification will be detected and may result in license violations.
"""



#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERITAS Protected Module
WARNING: This file contains embedded protection keys. 
Modification will be detected and may result in license violations.
"""


"""
UDS3 VPB API Backend
Flask REST API für VPB Process Designer mit SQLite-Persistierung

Endpoints:
- GET    /api/vpb/processes          - Liste aller Prozesse  
- GET    /api/vpb/processes/{id}     - Einzelnen Prozess laden
- POST   /api/vpb/processes          - Neuen Prozess speichern
- PUT    /api/vpb/processes/{id}     - Prozess aktualisieren
- DELETE /api/vpb/processes/{id}     - Prozess löschen
- POST   /api/vpb/processes/{id}/analyze - Prozess analysieren
- POST   /api/vpb/processes/{id}/validate - Prozess validieren
- GET    /api/vpb/statistics         - Database-Statistiken

Autor: UDS3 Development Team
Datum: 22. August 2025
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess

# VPB SQLite Integration
from vpb_sqlite_db import VPBSQLiteDB
from uds3_vpb_schema import VPBProcessRecord, migrate_legacy_vpb_data
from uds3_api_backend import UDS3APIBackend, ProcessAnalysisResult

logger = logging.getLogger(__name__)

class VPBAPIServer:
    """Flask API Server für VPB Process Designer"""
    
    def __init__(self, db_path: str = "vpb_processes.db", host: str = "localhost", port: int = 5000):
        """Initialisiert VPB API Server"""
        self.db_path = db_path
        self.host = host
        self.port = port
        
        # Database und Backend
        self.vpb_db = VPBSQLiteDB(db_path)
        self.uds3_backend = UDS3APIBackend()
        
        # Flask App
        self.app = Flask(__name__)
        CORS(self.app)  # CORS für Frontend-Integration
        
        # Setup Routes
        self.setup_routes()
        
        logger.info(f"VPB API Server initialisiert auf {host}:{port}")
    
    def setup_routes(self):
        """Setup aller API-Routen"""
        
        # Health Check
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """API Gesundheitsstatus"""
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "database": "connected",
                "version": "1.0.0"
            }), 200
        
        # VPB Process CRUD Endpoints
        @self.app.route('/api/vpb/processes', methods=['GET'])
        def list_processes():
            """Liste alle VPB Prozesse"""
            try:
                status = request.args.get('status')
                authority = request.args.get('authority_level')
                
                processes = self.vpb_db.list_processes(status=status, authority_level=authority)
                
                return jsonify({
                    "success": True,
                    "processes": processes,
                    "count": len(processes),
                    "timestamp": datetime.now().isoformat()
                }), 200
                
            except Exception as e:
                logger.error(f"Fehler beim Auflisten der Prozesse: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/vpb/processes/<process_id>', methods=['GET'])
        def get_process(process_id):
            """Lade spezifischen VPB Prozess"""
            try:
                process = self.vpb_db.load_process(process_id)
                
                if process:
                    return jsonify({
                        "success": True,
                        "process": process.to_dict(),
                        "timestamp": datetime.now().isoformat()
                    }), 200
                else:
                    return jsonify({
                        "success": False,
                        "error": f"Prozess nicht gefunden: {process_id}",
                        "timestamp": datetime.now().isoformat()
                    }), 404
                    
            except Exception as e:
                logger.error(f"Fehler beim Laden des Prozesses {process_id}: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/vpb/processes', methods=['POST'])
        def save_process():
            """Speichere neuen VPB Prozess"""
            try:
                data = request.get_json()
                
                if not data:
                    return jsonify({
                        "success": False,
                        "error": "Keine JSON-Daten empfangen",
                        "timestamp": datetime.now().isoformat()
                    }), 400
                
                # VPBProcessRecord aus Input-Daten erstellen
                process = migrate_legacy_vpb_data(data)
                
                # Validation durchführen
                validation = process.validate()
                if not validation["is_valid"]:
                    return jsonify({
                        "success": False,
                        "error": "Prozess-Validierung fehlgeschlagen",
                        "validation_errors": validation["errors"],
                        "timestamp": datetime.now().isoformat()
                    }), 400
                
                # In Database speichern
                if self.vpb_db.save_process(process):
                    logger.info(f"Neuer Prozess gespeichert: {process.process_id} - {process.name}")
                    return jsonify({
                        "success": True,
                        "process_id": process.process_id,
                        "message": "Prozess erfolgreich gespeichert",
                        "validation": validation,
                        "timestamp": datetime.now().isoformat()
                    }), 201
                else:
                    return jsonify({
                        "success": False,
                        "error": "Speichern in Database fehlgeschlagen",
                        "timestamp": datetime.now().isoformat()
                    }), 500
                    
            except Exception as e:
                logger.error(f"Fehler beim Speichern: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/vpb/processes/<process_id>', methods=['PUT'])
        def update_process(process_id):
            """Aktualisiere bestehenden VPB Prozess"""
            try:
                data = request.get_json()
                
                if not data:
                    return jsonify({
                        "success": False,
                        "error": "Keine JSON-Daten empfangen",
                        "timestamp": datetime.now().isoformat()
                    }), 400
                
                # Bestehenden Prozess laden
                existing_process = self.vpb_db.load_process(process_id)
                if not existing_process:
                    return jsonify({
                        "success": False,
                        "error": f"Prozess nicht gefunden: {process_id}",
                        "timestamp": datetime.now().isoformat()
                    }), 404
                
                # Process-ID sicherstellen
                data["process_id"] = process_id
                
                # Aktualisierte Daten migrieren
                updated_process = migrate_legacy_vpb_data(data)
                
                # Metadata vom bestehenden Prozess übernehmen
                updated_process.created_at = existing_process.created_at
                updated_process.created_by = existing_process.created_by
                
                # Validation durchführen
                validation = updated_process.validate()
                if not validation["is_valid"]:
                    return jsonify({
                        "success": False,
                        "error": "Prozess-Validierung fehlgeschlagen",
                        "validation_errors": validation["errors"],
                        "timestamp": datetime.now().isoformat()
                    }), 400
                
                if self.vpb_db.save_process(updated_process):
                    logger.info(f"Prozess aktualisiert: {process_id} - {updated_process.name}")
                    return jsonify({
                        "success": True,
                        "process_id": process_id,
                        "message": "Prozess erfolgreich aktualisiert",
                        "validation": validation,
                        "timestamp": datetime.now().isoformat()
                    }), 200
                else:
                    return jsonify({
                        "success": False,
                        "error": "Aktualisierung in Database fehlgeschlagen",
                        "timestamp": datetime.now().isoformat()
                    }), 500
                    
            except Exception as e:
                logger.error(f"Fehler beim Aktualisieren von {process_id}: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/vpb/processes/<process_id>', methods=['DELETE'])
        def delete_process(process_id):
            """Lösche VPB Prozess"""
            try:
                # Prüfen ob Prozess existiert
                existing_process = self.vpb_db.load_process(process_id)
                if not existing_process:
                    return jsonify({
                        "success": False,
                        "error": f"Prozess nicht gefunden: {process_id}",
                        "timestamp": datetime.now().isoformat()
                    }), 404
                
                if self.vpb_db.delete_process(process_id):
                    logger.info(f"Prozess gelöscht: {process_id}")
                    return jsonify({
                        "success": True,
                        "message": f"Prozess {process_id} erfolgreich gelöscht",
                        "timestamp": datetime.now().isoformat()
                    }), 200
                else:
                    return jsonify({
                        "success": False,
                        "error": "Löschung in Database fehlgeschlagen",
                        "timestamp": datetime.now().isoformat()
                    }), 500
                    
            except Exception as e:
                logger.error(f"Fehler beim Löschen von {process_id}: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500
        
        # VPB Analysis Endpoints
        @self.app.route('/api/vpb/processes/<process_id>/analyze', methods=['POST'])
        def analyze_process(process_id):
            """Analysiere VPB Prozess mit UDS3 LLM"""
            try:
                process = self.vpb_db.load_process(process_id)
                
                if not process:
                    return jsonify({
                        "success": False,
                        "error": f"Prozess nicht gefunden: {process_id}",
                        "timestamp": datetime.now().isoformat()
                    }), 404
                
                # Prozess-Elemente und -Verbindungen für Analyse aufbereiten
                elements = [element.to_dict() for element in process.elements]
                connections = [connection.to_dict() for connection in process.connections]
                
                # UDS3 LLM-Analyse durchführen
                analysis_result = self.uds3_backend.analyze_process_with_llm(elements, connections)
                
                logger.info(f"Prozessanalyse abgeschlossen für {process_id}: Komplexität {analysis_result.complexity_score}")
                
                return jsonify({
                    "success": True,
                    "analysis": {
                        "process_id": process_id,
                        "process_name": process.name,
                        "complexity_score": analysis_result.complexity_score,
                        "compliance_issues": analysis_result.compliance_issues,
                        "optimization_suggestions": analysis_result.optimization_suggestions,
                        "missing_elements": analysis_result.missing_elements,
                        "authority_mapping": analysis_result.authority_mapping,
                        "estimated_duration_days": analysis_result.estimated_duration_days,
                        "risk_assessment": analysis_result.risk_assessment,
                        "element_count": len(elements),
                        "connection_count": len(connections)
                    },
                    "timestamp": datetime.now().isoformat()
                }), 200
                
            except Exception as e:
                logger.error(f"Fehler bei Prozessanalyse für {process_id}: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500
        
        # VPB Validation Endpoint
        @self.app.route('/api/vpb/processes/<process_id>/validate', methods=['POST'])
        def validate_process(process_id):
            """Validiere VPB Prozess"""
            try:
                process = self.vpb_db.load_process(process_id)
                
                if not process:
                    return jsonify({
                        "success": False,
                        "error": f"Prozess nicht gefunden: {process_id}",
                        "timestamp": datetime.now().isoformat()
                    }), 404
                
                # Validation mit Schema durchführen
                validation_result = process.validate()
                
                logger.info(f"Prozessvalidierung für {process_id}: {'✅ Valid' if validation_result['is_valid'] else '❌ Invalid'}")
                
                return jsonify({
                    "success": True,
                    "validation": {
                        "process_id": process_id,
                        "process_name": process.name,
                        "is_valid": validation_result["is_valid"],
                        "errors": validation_result["errors"],
                        "warnings": validation_result["warnings"],
                        "statistics": validation_result["statistics"]
                    },
                    "timestamp": datetime.now().isoformat()
                }), 200
                
            except Exception as e:
                logger.error(f"Fehler bei Prozess-Validierung für {process_id}: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500
        
        # VPB Statistics Endpoint
        @self.app.route('/api/vpb/statistics', methods=['GET'])
        def get_statistics():
            """Database-Statistiken abrufen"""
            try:
                stats = self.vpb_db.get_statistics()
                
                return jsonify({
                    "success": True,
                    "statistics": stats,
                    "timestamp": datetime.now().isoformat()
                }), 200
                
            except Exception as e:
                logger.error(f"Fehler bei Statistik-Abfrage: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500
        
        # VPB Export Endpoint
        @self.app.route('/api/vpb/processes/<process_id>/export', methods=['GET'])
        def export_process(process_id):
            """Exportiere Prozess als JSON/XML"""
            try:
                process = self.vpb_db.load_process(process_id)
                
                if not process:
                    return jsonify({
                        "success": False,
                        "error": f"Prozess nicht gefunden: {process_id}",
                        "timestamp": datetime.now().isoformat()
                    }), 404
                
                export_format = request.args.get('format', 'json').lower()
                
                if export_format == 'json':
                    return jsonify({
                        "success": True,
                        "format": "json",
                        "data": process.to_dict(),
                        "timestamp": datetime.now().isoformat()
                    }), 200
                elif export_format == 'xml':
                    # XML-Export implementieren (für späteren Ausbau)
                    return jsonify({
                        "success": False,
                        "error": "XML-Export noch nicht implementiert",
                        "timestamp": datetime.now().isoformat()
                    }), 501
                else:
                    return jsonify({
                        "success": False,
                        "error": f"Unbekanntes Export-Format: {export_format}",
                        "timestamp": datetime.now().isoformat()
                    }), 400
                    
            except Exception as e:
                logger.error(f"Fehler beim Exportieren von {process_id}: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500
        
        # Error Handler
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                "success": False,
                "error": "API Endpoint nicht gefunden",
                "timestamp": datetime.now().isoformat()
            }), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({
                "success": False,
                "error": "Interner Server-Fehler",
                "timestamp": datetime.now().isoformat()
            }), 500
    
    def run(self, debug: bool = False):
        """Startet den Flask API Server"""
        try:
            logger.info(f"🚀 VPB API Server startet auf http://{self.host}:{self.port}")
            logger.info(f"   Database: {self.db_path}")
            logger.info(f"   Debug-Modus: {debug}")
            logger.info("   Verfügbare Endpoints:")
            logger.info("   - GET    /api/vpb/processes")
            logger.info("   - POST   /api/vpb/processes")
            logger.info("   - GET    /api/vpb/processes/{id}")
            logger.info("   - PUT    /api/vpb/processes/{id}")
            logger.info("   - DELETE /api/vpb/processes/{id}")
            logger.info("   - POST   /api/vpb/processes/{id}/analyze")
            logger.info("   - POST   /api/vpb/processes/{id}/validate")
            logger.info("   - GET    /api/vpb/statistics")
            
            self.app.run(
                host=self.host,
                port=self.port,
                debug=debug,
                threaded=True
            )
            
        except Exception as e:
            logger.error(f"Fehler beim Starten des API Servers: {e}")
            raise

# CLI für API Server
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="VPB API Server")
    parser.add_argument("--db", default="vpb_processes.db", help="SQLite Database Pfad")
    parser.add_argument("--host", default="localhost", help="Server Host")
    parser.add_argument("--port", type=int, default=5000, help="Server Port")
    parser.add_argument("--debug", action="store_true", help="Debug-Modus aktivieren")
    
    args = parser.parse_args()
    
    # Logging setup
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # API Server starten
    server = VPBAPIServer(
        db_path=args.db,
        host=args.host,
        port=args.port
    )
    
    try:
        server.run(debug=args.debug)
    except KeyboardInterrupt:
        logger.info("API Server beendet durch Benutzer")
    except Exception as e:
        logger.error(f"Server-Fehler: {e}")

"""
VERITAS Protected Module
WARNING: This file contains embedded protection keys. 
Modification will be detected and may result in license violations.
"""

# === VERITAS PROTECTION KEYS (DO NOT MODIFY) ===
module_name = "vpb_api_server"
module_licenced_organization = "VERITAS_TECH_GMBH"
module_licence_key = "eyJjbGllbnRfaWQi...NzRkYzhl"  # Gekuerzt fuer Sicherheit
module_organization_key = "6f5304c29594443086e1ace0011c094614b612c22aa16af9f1a63f02a0c9bf5c"
module_file_key = "954220b06b71f8fb18b804361f08a0810bc9030517050f17cd0c3b84bf8c84a7"
module_version = "1.0"
module_protection_level = 3
# === END PROTECTION KEYS ===
