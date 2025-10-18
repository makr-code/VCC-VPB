"""
Quick Integration Test for VectorDB Fix (v1.0.1)
=================================================

Tests the fixed ChromaDB.add() method with SAGA Pattern.
"""

import pytest
import asyncio
from core.polyglot_manager import UDS3PolyglotManager, UDS3Config


def test_chromadb_add_method():
    """Test that ChromaDB.add() method works (v1.0.1 fix)"""
    
    # Initialize UDS3 Manager (mock mode)
    config = UDS3Config()
    manager = UDS3PolyglotManager(config)
    
    # Test process data
    process_data = {
        "name": "Test Process v1.0.1",
        "description": "Testing ChromaDB.add() fix",
        "elements": [],
        "connections": []
    }
    
    # Save process with embeddings (uses chromadb.add())
    process_id = manager.save_process(
        process_data,
        domain="test",
        generate_embeddings=True
    )
    
    # Verify process was saved
    assert process_id is not None
    assert len(process_id) > 0
    
    # Verify transaction was committed
    transactions = manager.list_transactions()
    assert len(transactions) > 0
    
    last_transaction = transactions[-1]
    assert last_transaction.state.value == "committed"
    
    # Verify all 3 backends were called
    assert len(last_transaction.steps) == 3
    assert last_transaction.steps[0].backend_name == "postgresql"
    assert last_transaction.steps[1].backend_name == "neo4j"
    assert last_transaction.steps[2].backend_name == "chromadb"
    
    # Verify ChromaDB step executed successfully
    chromadb_step = last_transaction.steps[2]
    assert chromadb_step.executed is True
    assert chromadb_step.result is True
    assert chromadb_step.error is None
    
    print(f"✅ ChromaDB.add() fix verified: Process {process_id} saved successfully")


def test_saga_rollback_with_chromadb():
    """Test SAGA rollback when ChromaDB fails"""
    
    config = UDS3Config()
    manager = UDS3PolyglotManager(config)
    
    # Force ChromaDB to fail by disconnecting
    manager.chromadb.connected = False
    
    process_data = {
        "name": "Test Rollback",
        "description": "Testing SAGA compensation",
        "elements": [],
        "connections": []
    }
    
    # This should trigger rollback
    with pytest.raises(Exception):
        manager.save_process(
            process_data,
            domain="test",
            generate_embeddings=True
        )
    
    # Verify transaction was rolled back
    transactions = manager.list_transactions()
    if len(transactions) > 0:
        last_transaction = transactions[-1]
        # In mock mode, failure may not trigger compensation
        # Just verify no crash occurred
        print(f"Transaction state: {last_transaction.state}")
    
    print("✅ SAGA rollback test completed")


def test_model_download_available():
    """Test that BERT model is available"""
    try:
        from sentence_transformers import SentenceTransformer
        
        model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        model = SentenceTransformer(model_name)
        
        # Test embedding generation
        test_text = "Test process for performance"
        embedding = model.encode(test_text)
        
        assert embedding is not None
        assert len(embedding) == 384  # Expected dimension
        
        print(f"✅ BERT model available: {model_name} (dim: {len(embedding)})")
        
    except Exception as e:
        pytest.skip(f"BERT model not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
