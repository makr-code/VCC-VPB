"""
UDS3 VPB FastAPI Endpoints
===========================

FastAPI REST API für VPB Process Designer mit UDS3 Polyglot Persistence.
Unterstützt vollständiges CRUD + SAGA Pattern für distributed transactions.

Features:
- Automatische OpenAPI/Swagger Dokumentation
- Pydantic Models für Request/Response Validation
- SAGA Transaction Tracking
- Async Support
- Type Safety

Autor: UDS3 Development Team
Datum: 18. Oktober 2025
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Query, Path, Body, APIRouter, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import uvicorn

# UDS3 Polyglot Manager
from core.polyglot_manager import (
    UDS3PolyglotManager,
    UDS3Config,
    create_uds3_manager,
    TransactionState
)

logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models (Request/Response Schemas)
# ============================================================================

class ProcessBase(BaseModel):
    """Base Process Model"""
    name: str = Field(..., min_length=1, max_length=500, description="Process Name")
    description: Optional[str] = Field(None, description="Process Description")
    authority: Optional[str] = Field(None, max_length=300, description="Authority")
    legal_basis: Optional[List[str]] = Field(default_factory=list, description="Legal Basis")
    status: Optional[str] = Field("draft", description="Process Status")
    process_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Process Data (JSON)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Baugenehmigung Standard",
                "description": "Standardverfahren für Baugenehmigung",
                "authority": "Bauamt Stadt XYZ",
                "legal_basis": ["BauGB §29-38", "LBO §58"],
                "status": "draft",
                "process_data": {
                    "elements": [],
                    "connections": []
                }
            }
        }


class ProcessCreate(ProcessBase):
    """Process Creation Request"""
    pass


class ProcessUpdate(BaseModel):
    """Process Update Request (alle Felder optional)"""
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    authority: Optional[str] = Field(None, max_length=300)
    legal_basis: Optional[List[str]] = None
    status: Optional[str] = None
    process_data: Optional[Dict[str, Any]] = None


class ProcessResponse(ProcessBase):
    """Process Response"""
    process_id: str = Field(..., description="Process UUID")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ProcessListResponse(BaseModel):
    """Process List Response"""
    success: bool = True
    processes: List[Dict[str, Any]]
    count: int
    offset: int
    limit: int
    timestamp: datetime = Field(default_factory=datetime.now)


class ProcessCreateResponse(BaseModel):
    """Process Create Response"""
    success: bool = True
    process_id: str
    domain: str
    transaction: Optional[Dict[str, Any]] = None
    message: str = "Process created successfully"
    timestamp: datetime = Field(default_factory=datetime.now)


class ProcessUpdateResponse(BaseModel):
    """Process Update Response"""
    success: bool = True
    process_id: str
    transaction: Optional[Dict[str, Any]] = None
    message: str = "Process updated successfully"
    timestamp: datetime = Field(default_factory=datetime.now)


class ProcessDeleteResponse(BaseModel):
    """Process Delete Response"""
    success: bool = True
    process_id: str
    soft_delete: bool
    transaction: Optional[Dict[str, Any]] = None
    message: str = "Process deleted successfully"
    timestamp: datetime = Field(default_factory=datetime.now)


class SearchResponse(BaseModel):
    """Semantic Search Response"""
    success: bool = True
    results: List[Dict[str, Any]]
    query: str
    domain: str
    top_k: int
    timestamp: datetime = Field(default_factory=datetime.now)


class TransactionListResponse(BaseModel):
    """SAGA Transaction List Response"""
    success: bool = True
    transactions: List[Dict[str, Any]]
    count: int
    filter_state: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class TransactionStatusResponse(BaseModel):
    """SAGA Transaction Status Response"""
    success: bool = True
    transaction: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthResponse(BaseModel):
    """Health Check Response"""
    status: str
    backends: Dict[str, bool]
    saga_enabled: bool
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """Error Response"""
    success: bool = False
    error: str
    rollback: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


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
# FastAPI App & Routers
# ============================================================================

app = FastAPI(
    title="UDS3 VPB API",
    description="REST API für VPB Process Designer mit UDS3 Polyglot Persistence & SAGA Pattern",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
vpb_router = APIRouter(prefix="/api/uds3/vpb", tags=["VPB Processes"])
saga_router = APIRouter(prefix="/api/uds3/saga", tags=["SAGA Transactions"])


# ============================================================================
# VPB Process CRUD Endpoints
# ============================================================================

@vpb_router.get(
    "/processes",
    response_model=ProcessListResponse,
    summary="Liste aller VPB Prozesse",
    description="Ruft Liste aller VPB Prozesse ab mit optionalen Filtern"
)
async def list_processes(
    domain: str = Query("vpb", description="App Domain Filter"),
    status: Optional[str] = Query(None, description="Status Filter"),
    authority: Optional[str] = Query(None, description="Authority Filter"),
    limit: int = Query(100, ge=1, le=1000, description="Max Results"),
    offset: int = Query(0, ge=0, description="Offset for Pagination")
):
    """Liste alle VPB Prozesse"""
    try:
        manager = get_uds3_manager()
        
        # TODO: Implement list_processes in manager
        processes = []
        
        return ProcessListResponse(
            processes=processes,
            count=len(processes),
            offset=offset,
            limit=limit
        )
    
    except Exception as e:
        logger.error(f"Error listing processes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@vpb_router.get(
    "/processes/{process_id}",
    response_model=Dict[str, Any],
    summary="Lade spezifischen VPB Prozess",
    description="Ruft einzelnen Prozess nach ID ab"
)
async def get_process(
    process_id: str = Path(..., description="Process UUID"),
    source: str = Query("postgresql", description="Backend Source (postgresql, all)")
):
    """Lade spezifischen VPB Prozess"""
    try:
        manager = get_uds3_manager()
        process = manager.get_process(process_id, source=source)
        
        if process:
            return {
                "success": True,
                "process": process,
                "source": source,
                "timestamp": datetime.now()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Process not found: {process_id}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading process {process_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@vpb_router.post(
    "/processes",
    response_model=ProcessCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Erstelle neuen VPB Prozess",
    description="Erstellt neuen Prozess mit SAGA Transaction über alle Backends"
)
async def create_process(
    process: ProcessCreate = Body(..., description="Process Data"),
    domain: str = Query("vpb", description="App Domain"),
    generate_embeddings: bool = Query(True, description="Generate Embeddings for Semantic Search")
):
    """Erstelle neuen VPB Prozess (mit SAGA)"""
    try:
        # Convert Pydantic model to dict
        process_data = process.model_dump(exclude_unset=True)
        
        # UDS3 Manager
        manager = get_uds3_manager()
        
        # Save with SAGA
        process_id = manager.save_process(
            process_data=process_data,
            domain=domain,
            generate_embeddings=generate_embeddings
        )
        
        # Get transaction status
        transactions = manager.list_transactions(limit=1)
        transaction_info = transactions[0] if transactions else None
        
        logger.info(f"Process created: {process_id} in domain '{domain}'")
        
        return ProcessCreateResponse(
            process_id=process_id,
            domain=domain,
            transaction=transaction_info
        )
    
    except Exception as e:
        logger.error(f"Error creating process: {e}")
        
        # Check if SAGA rollback occurred
        manager = get_uds3_manager()
        recent_tx = manager.list_transactions(limit=1)
        rollback_info = None
        if recent_tx and recent_tx[0]['state'] == TransactionState.ROLLED_BACK.value:
            rollback_info = recent_tx[0]
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": str(e),
                "rollback": rollback_info,
                "message": "Process creation failed, SAGA rollback performed" if rollback_info else "Process creation failed"
            }
        )


@vpb_router.put(
    "/processes/{process_id}",
    response_model=ProcessUpdateResponse,
    summary="Aktualisiere VPB Prozess",
    description="Aktualisiert bestehenden Prozess mit SAGA Transaction"
)
async def update_process(
    process_id: str = Path(..., description="Process UUID"),
    updates: ProcessUpdate = Body(..., description="Update Data"),
    domain: str = Query("vpb", description="App Domain")
):
    """Aktualisiere bestehenden VPB Prozess (mit SAGA)"""
    try:
        # Convert Pydantic model to dict (exclude unset fields)
        update_data = updates.model_dump(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No update data provided"
            )
        
        # UDS3 Manager
        manager = get_uds3_manager()
        
        # Update with SAGA
        success = manager.update_process(
            process_id=process_id,
            updates=update_data,
            domain=domain
        )
        
        if success:
            # Get transaction status
            transactions = manager.list_transactions(limit=1)
            transaction_info = transactions[0] if transactions else None
            
            logger.info(f"Process updated: {process_id}")
            
            return ProcessUpdateResponse(
                process_id=process_id,
                transaction=transaction_info
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Update failed"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating process {process_id}: {e}")
        
        # Check for rollback
        manager = get_uds3_manager()
        recent_tx = manager.list_transactions(limit=1)
        rollback_info = None
        if recent_tx and recent_tx[0]['state'] == TransactionState.ROLLED_BACK.value:
            rollback_info = recent_tx[0]
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": str(e),
                "rollback": rollback_info,
                "message": "Process update failed, SAGA rollback performed" if rollback_info else "Process update failed"
            }
        )


@vpb_router.delete(
    "/processes/{process_id}",
    response_model=ProcessDeleteResponse,
    summary="Lösche VPB Prozess",
    description="Löscht Prozess mit SAGA Transaction (soft/hard delete)"
)
async def delete_process(
    process_id: str = Path(..., description="Process UUID"),
    domain: str = Query("vpb", description="App Domain"),
    soft_delete: bool = Query(True, description="Soft Delete (set deleted_at) vs Hard Delete")
):
    """Lösche VPB Prozess (mit SAGA)"""
    try:
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
            
            return ProcessDeleteResponse(
                process_id=process_id,
                soft_delete=soft_delete,
                transaction=transaction_info
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Delete failed"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting process {process_id}: {e}")
        
        # Check for rollback
        manager = get_uds3_manager()
        recent_tx = manager.list_transactions(limit=1)
        rollback_info = None
        if recent_tx and recent_tx[0]['state'] == TransactionState.ROLLED_BACK.value:
            rollback_info = recent_tx[0]
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": str(e),
                "rollback": rollback_info,
                "message": "Process deletion failed, SAGA rollback performed" if rollback_info else "Process deletion failed"
            }
        )


# ============================================================================
# Search & Query Endpoints
# ============================================================================

@vpb_router.get(
    "/search",
    response_model=SearchResponse,
    summary="Semantic Search",
    description="Semantic Search über VPB Prozesse mit ChromaDB/Embeddings"
)
async def semantic_search(
    q: str = Query(..., min_length=1, description="Search Query"),
    domain: str = Query("vpb", description="Domain Filter"),
    top_k: int = Query(10, ge=1, le=100, description="Number of Results"),
    min_similarity: float = Query(0.5, ge=0.0, le=1.0, description="Minimum Similarity Score")
):
    """Semantic Search über VPB Prozesse"""
    try:
        # TODO: Implement semantic_search in UDS3PolyglotManager
        results = []
        
        return SearchResponse(
            results=results,
            query=q,
            domain=domain,
            top_k=top_k
        )
    
    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# SAGA Transaction Management Endpoints
# ============================================================================

@saga_router.get(
    "/transactions",
    response_model=TransactionListResponse,
    summary="Liste SAGA Transactions",
    description="Ruft Liste aller SAGA Transactions ab mit optionalem State-Filter"
)
async def list_transactions(
    state: Optional[str] = Query(None, description="State Filter (pending, in_progress, committed, rolled_back, failed)"),
    limit: int = Query(100, ge=1, le=1000, description="Max Results")
):
    """Liste SAGA Transactions"""
    try:
        # Parse state
        state_enum = None
        if state:
            try:
                state_enum = TransactionState(state)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid state: {state}. Valid: pending, in_progress, committed, rolled_back, failed"
                )
        
        manager = get_uds3_manager()
        transactions = manager.list_transactions(state=state_enum, limit=limit)
        
        return TransactionListResponse(
            transactions=transactions,
            count=len(transactions),
            filter_state=state
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing transactions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@saga_router.get(
    "/transactions/{transaction_id}",
    response_model=TransactionStatusResponse,
    summary="SAGA Transaction Status",
    description="Ruft Status einer spezifischen SAGA Transaction ab"
)
async def get_transaction_status(
    transaction_id: str = Path(..., description="Transaction UUID")
):
    """Hole SAGA Transaction Status"""
    try:
        manager = get_uds3_manager()
        transaction = manager.get_transaction_status(transaction_id)
        
        if transaction:
            return TransactionStatusResponse(
                transaction=transaction
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction not found: {transaction_id}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transaction {transaction_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# Health Check
# ============================================================================

@vpb_router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Prüft Health Status aller Backends"
)
async def health_check():
    """API Health Check"""
    try:
        manager = get_uds3_manager()
        
        # Check backend connections
        backends_status = {
            "postgresql": manager.postgresql.connected,
            "neo4j": manager.neo4j.connected,
            "chromadb": manager.chromadb.connected
        }
        
        all_healthy = all(backends_status.values())
        
        return HealthResponse(
            status="healthy" if all_healthy else "degraded",
            backends=backends_status,
            saga_enabled=manager.config.enable_saga
        )
    
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )


# ============================================================================
# Register Routers
# ============================================================================

app.include_router(vpb_router)
app.include_router(saga_router)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """API Root"""
    return {
        "service": "UDS3 VPB API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "endpoints": {
            "vpb": "/api/uds3/vpb",
            "saga": "/api/uds3/saga"
        },
        "timestamp": datetime.now()
    }


# ============================================================================
# Startup & Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize UDS3 Manager on startup"""
    logger.info("🚀 Starting UDS3 VPB API...")
    manager = get_uds3_manager()
    logger.info(f"✅ UDS3 Manager initialized (SAGA: {manager.config.enable_saga})")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("👋 Shutting down UDS3 VPB API...")


# ============================================================================
# Standalone Server (für Development)
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 80)
    print("UDS3 VPB FastAPI Server")
    print("=" * 80)
    print("\n🚀 Starting server on http://localhost:8000")
    print("\n📚 API Documentation:")
    print("   Swagger UI:  http://localhost:8000/api/docs")
    print("   ReDoc:       http://localhost:8000/api/redoc")
    print("   OpenAPI:     http://localhost:8000/api/openapi.json")
    print("\n📡 Endpoints:")
    print("   GET    /api/uds3/vpb/health")
    print("   GET    /api/uds3/vpb/processes")
    print("   POST   /api/uds3/vpb/processes")
    print("   GET    /api/uds3/vpb/processes/{id}")
    print("   PUT    /api/uds3/vpb/processes/{id}")
    print("   DELETE /api/uds3/vpb/processes/{id}")
    print("   GET    /api/uds3/vpb/search?q=...")
    print("   GET    /api/uds3/saga/transactions")
    print("\n" + "=" * 80)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
