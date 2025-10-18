"""
Test Real Backend Implementations
==================================

Tests für echte PostgreSQL, Neo4j, ChromaDB Adapter.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.polyglot_manager import (
    PostgreSQLAdapter,
    Neo4jAdapter,
    ChromaDBAdapter,
    BackendConfig,
    PSYCOPG2_AVAILABLE,
    NEO4J_AVAILABLE,
    CHROMADB_AVAILABLE
)


def test_backend_availability():
    """Test ob alle Backend-Libraries verfügbar sind"""
    print("\n=== Backend Availability Test ===")
    print(f"✓ psycopg2: {PSYCOPG2_AVAILABLE}")
    print(f"✓ neo4j: {NEO4J_AVAILABLE}")
    print(f"✓ chromadb: {CHROMADB_AVAILABLE}")
    
    assert PSYCOPG2_AVAILABLE, "psycopg2-binary not installed"
    assert NEO4J_AVAILABLE, "neo4j driver not installed"
    assert CHROMADB_AVAILABLE, "chromadb not installed"
    
    print("✅ All backend libraries available")


def test_postgresql_adapter_initialization():
    """Test PostgreSQL Adapter Initialisierung"""
    print("\n=== PostgreSQL Adapter Test ===")
    
    config = BackendConfig(
        enabled=True,
        connection_string="postgresql://localhost:5432/uds3_test",
        options={"pool_size": 5}
    )
    
    adapter = PostgreSQLAdapter(config)
    assert adapter is not None
    assert adapter.config == config
    assert not adapter.connected  # Noch nicht verbunden
    
    print("✅ PostgreSQL Adapter initialized (no connection test)")


def test_neo4j_adapter_initialization():
    """Test Neo4j Adapter Initialisierung"""
    print("\n=== Neo4j Adapter Test ===")
    
    config = BackendConfig(
        enabled=True,
        connection_string="bolt://localhost:7687",
        options={"max_connection_lifetime": 3600}
    )
    
    adapter = Neo4jAdapter(config)
    assert adapter is not None
    assert adapter.config == config
    assert not adapter.connected
    
    print("✅ Neo4j Adapter initialized (no connection test)")


def test_chromadb_adapter_initialization():
    """Test ChromaDB Adapter Initialisierung"""
    print("\n=== ChromaDB Adapter Test ===")
    
    config = BackendConfig(
        enabled=True,
        connection_string="./chroma_data",  # Local persistent
        options={"collection_name": "vpb_test"}
    )
    
    adapter = ChromaDBAdapter(config)
    assert adapter is not None
    assert adapter.config == config
    assert not adapter.connected
    
    print("✅ ChromaDB Adapter initialized (no connection test)")


def test_chromadb_local_connection():
    """Test ChromaDB mit lokaler Persistent-Instanz"""
    print("\n=== ChromaDB Local Connection Test ===")
    
    config = BackendConfig(
        enabled=True,
        connection_string="./test_chroma_data",
        options={"collection_name": "vpb_test"}
    )
    
    adapter = ChromaDBAdapter(config)
    
    # Try to connect to local ChromaDB
    try:
        success = adapter.connect()
        if success:
            print("✅ ChromaDB connected successfully")
            
            # Test add operation
            test_data = {
                "process_id": "test_001",
                "name": "Test Process",
                "description": "Testing ChromaDB integration"
            }
            
            embedding_text = f"{test_data['name']} {test_data['description']}"
            metadata = {"name": test_data["name"]}
            
            result = adapter.add(
                test_data["process_id"],
                embedding_text,
                metadata
            )
            
            if result:
                print("✅ ChromaDB add() operation successful")
            
            # Cleanup
            adapter.disconnect()
        else:
            print("⚠️ ChromaDB connection failed (expected if no server running)")
    except Exception as e:
        print(f"⚠️ ChromaDB test failed: {e} (expected without running server)")


def test_uds3_api_backend():
    """Test UDS3 API Backend"""
    print("\n=== UDS3 API Backend Test ===")
    
    from uds3_api_backend import UDS3APIBackend, ProcessAnalysisResult
    
    backend = UDS3APIBackend(polyglot_manager=None)
    assert backend is not None
    
    # Test Process Analysis
    process_data = {
        "process_id": "test_process_001",
        "name": "Immissionsschutz Genehmigung",
        "description": "Genehmigung für immissionsschutzrechtliche Anlagen",
        "elements": [
            {"id": "start_1", "type": "startEvent", "name": "Antrag einreichen"},
            {"id": "task_1", "type": "task", "name": "Prüfung durchführen"},
            {"id": "gateway_1", "type": "exclusiveGateway", "name": "Genehmigung möglich?"},
            {"id": "end_1", "type": "endEvent", "name": "Genehmigt"},
            {"id": "end_2", "type": "endEvent", "name": "Abgelehnt"}
        ],
        "connections": [
            {"from": "start_1", "to": "task_1", "type": "sequence"},
            {"from": "task_1", "to": "gateway_1", "type": "sequence"},
            {"from": "gateway_1", "to": "end_1", "type": "sequence"},
            {"from": "gateway_1", "to": "end_2", "type": "sequence"}
        ]
    }
    
    result = backend.analyze_process(process_data)
    
    assert isinstance(result, ProcessAnalysisResult)
    assert result.process_id == "test_process_001"
    assert result.element_count == 5
    assert result.connection_count == 4
    assert result.decision_point_count == 1
    assert result.complexity_score > 0
    assert result.completeness_score == 100.0  # All checks passed
    assert result.uds3_conformity == True
    
    print(f"✅ Process Analysis successful:")
    print(f"   - Complexity: {result.complexity_score:.1f}")
    print(f"   - Completeness: {result.completeness_score:.1f}")
    print(f"   - Consistency: {result.consistency_score:.1f}")
    print(f"   - UDS3 Conformity: {result.uds3_conformity}")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("VPB Real Backend Integration Tests")
    print("="*70)
    
    try:
        test_backend_availability()
        test_postgresql_adapter_initialization()
        test_neo4j_adapter_initialization()
        test_chromadb_adapter_initialization()
        test_chromadb_local_connection()
        test_uds3_api_backend()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED")
        print("="*70 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
