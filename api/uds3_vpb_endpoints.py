"""
UDS3 VPB REST API Endpoints
============================

FastAPI REST API für VPB Process Designer mit UDS3 Polyglot Persistence.
Unterstützt CRUD-Operationen mit SAGA Pattern für distributed transactions.

Endpoints:
- GET    /api/uds3/vpb/processes          - Liste aller Prozesse
- GET    /api/uds3/vpb/processes/{id}     - Einzelnen Prozess laden
- POST   /api/uds3/vpb/processes          - Neuen Prozess speichern
- PUT    /api/uds3/vpb/processes/{id}     - Prozess aktualisieren
- DELETE /api/uds3/vpb/processes/{id}     - Prozess löschen
- GET    /api/uds3/vpb/search             - Semantic Search
- GET    /api/uds3/saga/transactions      - SAGA Transaction Status
- GET    /api/uds3/health                 - Health Check

Autor: UDS3 Development Team
Datum: 18. Oktober 2025
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Query, Path, Body, APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# UDS3 Polyglot Manager
from core.polyglot_manager import (
    UDS3PolyglotManager,
    UDS3Config,
    create_uds3_manager,
    TransactionState
)

logger = logging.getLogger(__name__)


# ============================================================================
# Blueprint für UDS3 VPB Endpoints
# ============================================================================

uds3_vpb_bp = Blueprint('uds3_vpb', __name__, url_prefix='/api/uds3/vpb')
uds3_saga_bp = Blueprint('uds3_saga', __name__, url_prefix='/api/uds3/saga')


# ============================================================================
# Global UDS3 Manager Instance
# ============================================================================

_uds3_manager: Optional[UDS3PolyglotManager] = None


def get_uds3_manager() -> UDS3PolyglotManager:
    """Get or create UDS3 Manager instance"""
    global _uds3_manager
    if _uds3_manager is None:
        _uds3_manager = create_uds3_manager()
    return _uds3_manager


# ============================================================================
# VPB Process CRUD Endpoints
# ============================================================================

@uds3_vpb_bp.route('/processes', methods=['GET'])
def list_processes():
    """
    Liste alle VPB Prozesse
    
    Query Parameters:
        - domain: Filter by domain (default: 'vpb')
        - status: Filter by status
        - authority: Filter by authority
        - limit: Max results (default: 100)
        - offset: Offset für Pagination (default: 0)
    
    Returns:
        200: List of processes
        500: Server error
    """
    try:
        # Query Parameters
        domain = request.args.get('domain', 'vpb')
        status = request.args.get('status')
        authority = request.args.get('authority')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        manager = get_uds3_manager()
        
        # TODO: Implement list_processes in manager
        # For now return mock data
        processes = []
        
        return jsonify({
            "success": True,
            "processes": processes,
            "count": len(processes),
            "offset": offset,
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Error listing processes: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@uds3_vpb_bp.route('/processes/<process_id>', methods=['GET'])
def get_process(process_id: str):
    """
    Lade spezifischen VPB Prozess
    
    Path Parameters:
        - process_id: Process UUID
    
    Query Parameters:
        - source: Backend source ('postgresql', 'all') (default: 'postgresql')
    
    Returns:
        200: Process data
        404: Process not found
        500: Server error
    """
    try:
        source = request.args.get('source', 'postgresql')
        
        manager = get_uds3_manager()
        process = manager.get_process(process_id, source=source)
        
        if process:
            return jsonify({
                "success": True,
                "process": process,
                "source": source,
                "timestamp": datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": f"Process not found: {process_id}",
                "timestamp": datetime.now().isoformat()
            }), 404
    
    except Exception as e:
        logger.error(f"Error loading process {process_id}: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@uds3_vpb_bp.route('/processes', methods=['POST'])
def create_process():
    """
    Erstelle neuen VPB Prozess (mit SAGA)
    
    Request Body:
        {
            "name": "Process Name",
            "description": "Description",
            "authority": "Authority Name",
            "legal_basis": ["BauGB §29"],
            "status": "draft",
            "process_data": { ... },
            ...
        }
    
    Query Parameters:
        - domain: App domain (default: 'vpb')
        - generate_embeddings: Generate embeddings (default: true)
    
    Returns:
        201: Process created successfully
        400: Invalid request data
        500: Server error (SAGA rollback performed)
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # Validate required fields
        required_fields = ['name']
        missing = [f for f in required_fields if f not in data]
        if missing:
            return jsonify({
                "success": False,
                "error": f"Missing required fields: {missing}",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # Query Parameters
        domain = request.args.get('domain', 'vpb')
        generate_embeddings = request.args.get('generate_embeddings', 'true').lower() == 'true'
        
        # UDS3 Manager
        manager = get_uds3_manager()
        
        # Save with SAGA
        process_id = manager.save_process(
            process_data=data,
            domain=domain,
            generate_embeddings=generate_embeddings
        )
        
        # Get transaction status
        transactions = manager.list_transactions(limit=1)
        transaction_info = transactions[0] if transactions else None
        
        logger.info(f"Process created: {process_id} in domain '{domain}'")
        
        return jsonify({
            "success": True,
            "process_id": process_id,
            "domain": domain,
            "transaction": transaction_info,
            "message": "Process created successfully",
            "timestamp": datetime.now().isoformat()
        }), 201
    
    except Exception as e:
        logger.error(f"Error creating process: {e}")
        
        # Check if SAGA rollback occurred
        manager = get_uds3_manager()
        recent_tx = manager.list_transactions(limit=1)
        rollback_info = None
        if recent_tx and recent_tx[0]['state'] == TransactionState.ROLLED_BACK.value:
            rollback_info = recent_tx[0]
        
        return jsonify({
            "success": False,
            "error": str(e),
            "rollback": rollback_info,
            "message": "Process creation failed, SAGA rollback performed" if rollback_info else "Process creation failed",
            "timestamp": datetime.now().isoformat()
        }), 500


@uds3_vpb_bp.route('/processes/<process_id>', methods=['PUT'])
def update_process(process_id: str):
    """
    Aktualisiere bestehenden VPB Prozess (mit SAGA)
    
    Path Parameters:
        - process_id: Process UUID
    
    Request Body:
        {
            "name": "Updated Name",
            "status": "active",
            ...
        }
    
    Query Parameters:
        - domain: App domain (default: 'vpb')
    
    Returns:
        200: Process updated successfully
        400: Invalid request data
        404: Process not found
        500: Server error (SAGA rollback performed)
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # Query Parameters
        domain = request.args.get('domain', 'vpb')
        
        # UDS3 Manager
        manager = get_uds3_manager()
        
        # Update with SAGA
        success = manager.update_process(
            process_id=process_id,
            updates=data,
            domain=domain
        )
        
        if success:
            # Get transaction status
            transactions = manager.list_transactions(limit=1)
            transaction_info = transactions[0] if transactions else None
            
            logger.info(f"Process updated: {process_id}")
            
            return jsonify({
                "success": True,
                "process_id": process_id,
                "transaction": transaction_info,
                "message": "Process updated successfully",
                "timestamp": datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Update failed",
                "timestamp": datetime.now().isoformat()
            }), 500
    
    except Exception as e:
        logger.error(f"Error updating process {process_id}: {e}")
        
        # Check for rollback
        manager = get_uds3_manager()
        recent_tx = manager.list_transactions(limit=1)
        rollback_info = None
        if recent_tx and recent_tx[0]['state'] == TransactionState.ROLLED_BACK.value:
            rollback_info = recent_tx[0]
        
        return jsonify({
            "success": False,
            "error": str(e),
            "rollback": rollback_info,
            "message": "Process update failed, SAGA rollback performed" if rollback_info else "Process update failed",
            "timestamp": datetime.now().isoformat()
        }), 500


@uds3_vpb_bp.route('/processes/<process_id>', methods=['DELETE'])
def delete_process(process_id: str):
    """
    Lösche VPB Prozess (mit SAGA)
    
    Path Parameters:
        - process_id: Process UUID
    
    Query Parameters:
        - domain: App domain (default: 'vpb')
        - soft_delete: Soft delete (default: true)
    
    Returns:
        200: Process deleted successfully
        500: Server error (SAGA rollback performed)
    """
    try:
        # Query Parameters
        domain = request.args.get('domain', 'vpb')
        soft_delete = request.args.get('soft_delete', 'true').lower() == 'true'
        
        # UDS3 Manager
        manager = get_uds3_manager()
        
        # Delete with SAGA
        success = manager.delete_process(
            process_id=process_id,
            domain=domain,
            soft_delete=soft_delete
        )
        
        if success:
            # Get transaction status
            transactions = manager.list_transactions(limit=1)
            transaction_info = transactions[0] if transactions else None
            
            logger.info(f"Process deleted: {process_id} (soft={soft_delete})")
            
            return jsonify({
                "success": True,
                "process_id": process_id,
                "soft_delete": soft_delete,
                "transaction": transaction_info,
                "message": "Process deleted successfully",
                "timestamp": datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Delete failed",
                "timestamp": datetime.now().isoformat()
            }), 500
    
    except Exception as e:
        logger.error(f"Error deleting process {process_id}: {e}")
        
        # Check for rollback
        manager = get_uds3_manager()
        recent_tx = manager.list_transactions(limit=1)
        rollback_info = None
        if recent_tx and recent_tx[0]['state'] == TransactionState.ROLLED_BACK.value:
            rollback_info = recent_tx[0]
        
        return jsonify({
            "success": False,
            "error": str(e),
            "rollback": rollback_info,
            "message": "Process deletion failed, SAGA rollback performed" if rollback_info else "Process deletion failed",
            "timestamp": datetime.now().isoformat()
        }), 500


# ============================================================================
# Search & Query Endpoints
# ============================================================================

@uds3_vpb_bp.route('/search', methods=['GET'])
def semantic_search():
    """
    Semantic Search über VPB Prozesse
    
    Query Parameters:
        - q: Search query (required)
        - domain: Filter by domain (default: 'vpb')
        - top_k: Number of results (default: 10)
        - min_similarity: Minimum similarity score (default: 0.5)
    
    Returns:
        200: Search results
        400: Missing query parameter
        500: Server error
    """
    try:
        query = request.args.get('q')
        if not query:
            return jsonify({
                "success": False,
                "error": "Missing query parameter 'q'",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        domain = request.args.get('domain', 'vpb')
        top_k = int(request.args.get('top_k', 10))
        min_similarity = float(request.args.get('min_similarity', 0.5))
        
        # TODO: Implement semantic_search in UDS3PolyglotManager
        # For now return mock
        results = {
            "results": [],
            "query": query,
            "domain": domain,
            "top_k": top_k
        }
        
        return jsonify({
            "success": True,
            **results,
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


# ============================================================================
# SAGA Transaction Management Endpoints
# ============================================================================

@uds3_saga_bp.route('/transactions', methods=['GET'])
def list_transactions():
    """
    Liste SAGA Transactions
    
    Query Parameters:
        - state: Filter by state (pending, in_progress, committed, rolled_back, failed)
        - limit: Max results (default: 100)
    
    Returns:
        200: Transaction list
        500: Server error
    """
    try:
        state_param = request.args.get('state')
        limit = int(request.args.get('limit', 100))
        
        # Parse state
        state = None
        if state_param:
            try:
                state = TransactionState(state_param)
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": f"Invalid state: {state_param}. Valid: pending, in_progress, committed, rolled_back, failed",
                    "timestamp": datetime.now().isoformat()
                }), 400
        
        manager = get_uds3_manager()
        transactions = manager.list_transactions(state=state, limit=limit)
        
        return jsonify({
            "success": True,
            "transactions": transactions,
            "count": len(transactions),
            "filter_state": state.value if state else None,
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Error listing transactions: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


@uds3_saga_bp.route('/transactions/<transaction_id>', methods=['GET'])
def get_transaction_status(transaction_id: str):
    """
    Hole SAGA Transaction Status
    
    Path Parameters:
        - transaction_id: Transaction UUID
    
    Returns:
        200: Transaction status
        404: Transaction not found
        500: Server error
    """
    try:
        manager = get_uds3_manager()
        transaction = manager.get_transaction_status(transaction_id)
        
        if transaction:
            return jsonify({
                "success": True,
                "transaction": transaction,
                "timestamp": datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": f"Transaction not found: {transaction_id}",
                "timestamp": datetime.now().isoformat()
            }), 404
    
    except Exception as e:
        logger.error(f"Error getting transaction {transaction_id}: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500


# ============================================================================
# Health Check
# ============================================================================

@uds3_vpb_bp.route('/health', methods=['GET'])
def health_check():
    """
    API Health Check
    
    Returns:
        200: Healthy
        503: Unhealthy
    """
    try:
        manager = get_uds3_manager()
        
        # Check backend connections
        backends_status = {
            "postgresql": manager.postgresql.connected,
            "neo4j": manager.neo4j.connected,
            "chromadb": manager.chromadb.connected
        }
        
        all_healthy = all(backends_status.values())
        
        return jsonify({
            "status": "healthy" if all_healthy else "degraded",
            "backends": backends_status,
            "saga_enabled": manager.config.enable_saga,
            "timestamp": datetime.now().isoformat()
        }), 200 if all_healthy else 503
    
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 503


# ============================================================================
# Flask App Integration
# ============================================================================

def register_uds3_endpoints(app: Flask):
    """
    Register UDS3 endpoints in Flask app
    
    Args:
        app: Flask application
    """
    app.register_blueprint(uds3_vpb_bp)
    app.register_blueprint(uds3_saga_bp)
    
    logger.info("UDS3 VPB Endpoints registered")
    logger.info(f"  - /api/uds3/vpb/processes (GET, POST)")
    logger.info(f"  - /api/uds3/vpb/processes/<id> (GET, PUT, DELETE)")
    logger.info(f"  - /api/uds3/vpb/search (GET)")
    logger.info(f"  - /api/uds3/saga/transactions (GET)")
    logger.info(f"  - /api/uds3/saga/transactions/<id> (GET)")


# ============================================================================
# Standalone Server (für Testing)
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 80)
    print("UDS3 VPB API Server - Standalone Mode")
    print("=" * 80)
    
    app = Flask(__name__)
    CORS(app)
    
    # Register endpoints
    register_uds3_endpoints(app)
    
    # Health check on root
    @app.route('/', methods=['GET'])
    def root():
        return jsonify({
            "service": "UDS3 VPB API",
            "version": "1.0.0",
            "endpoints": {
                "vpb": "/api/uds3/vpb",
                "saga": "/api/uds3/saga"
            },
            "timestamp": datetime.now().isoformat()
        })
    
    print("\n🚀 Starting server on http://localhost:5001")
    print("\n📚 Available endpoints:")
    print("   GET    /api/uds3/vpb/health")
    print("   GET    /api/uds3/vpb/processes")
    print("   POST   /api/uds3/vpb/processes")
    print("   GET    /api/uds3/vpb/processes/<id>")
    print("   PUT    /api/uds3/vpb/processes/<id>")
    print("   DELETE /api/uds3/vpb/processes/<id>")
    print("   GET    /api/uds3/vpb/search?q=...")
    print("   GET    /api/uds3/saga/transactions")
    print("\n" + "=" * 80)
    
    app.run(host='localhost', port=5001, debug=True)
