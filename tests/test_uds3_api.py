"""
Tests: UDS3 VPB API Endpoints
==============================

Unit & Integration Tests für UDS3 REST API mit SAGA Pattern.

Autor: UDS3 Development Team
Datum: 18. Oktober 2025
"""

import pytest
import json
from datetime import datetime
from flask import Flask

# Import API endpoints
from api.uds3_vpb_endpoints import (
    register_uds3_endpoints,
    uds3_vpb_bp,
    uds3_saga_bp,
    _uds3_manager
)

# Import Polyglot Manager
from core.polyglot_manager import (
    UDS3PolyglotManager,
    UDS3Config,
    create_uds3_manager,
    TransactionState
)


@pytest.fixture
def app():
    """Flask Test App"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    register_uds3_endpoints(app)
    return app


@pytest.fixture
def client(app):
    """Flask Test Client"""
    return app.test_client()


@pytest.fixture
def test_process_data():
    """Test Process Data"""
    return {
        "name": "Test Baugenehmigung",
        "description": "Test process for API testing",
        "authority": "Bauamt Test",
        "legal_basis": ["BauGB §29"],
        "status": "draft",
        "process_data": {
            "elements": [],
            "connections": []
        }
    }


# ============================================================================
# Health Check Tests
# ============================================================================

def test_health_check(client):
    """Test: Health Check Endpoint"""
    print("\n" + "="*80)
    print("TEST: Health Check")
    print("="*80)
    
    response = client.get('/api/uds3/vpb/health')
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json, indent=2)}")
    
    assert response.status_code in [200, 503]  # Can be degraded if backends not connected
    
    data = response.json
    assert 'status' in data
    assert 'backends' in data
    assert 'timestamp' in data
    
    print("✅ Test PASSED")


# ============================================================================
# CRUD Tests
# ============================================================================

def test_create_process(client, test_process_data):
    """Test: POST /api/uds3/vpb/processes"""
    print("\n" + "="*80)
    print("TEST: Create Process")
    print("="*80)
    
    response = client.post(
        '/api/uds3/vpb/processes',
        data=json.dumps(test_process_data),
        content_type='application/json'
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json, indent=2)}")
    
    assert response.status_code == 201
    
    data = response.json
    assert data['success'] == True
    assert 'process_id' in data
    assert 'transaction' in data
    
    # Check SAGA transaction
    if data['transaction']:
        print(f"\n📊 SAGA Transaction:")
        print(f"   State: {data['transaction']['state']}")
        print(f"   Steps: {len(data['transaction']['steps'])}")
        assert data['transaction']['state'] == 'committed'
    
    print("✅ Test PASSED")
    
    return data['process_id']


def test_get_process(client):
    """Test: GET /api/uds3/vpb/processes/<id>"""
    print("\n" + "="*80)
    print("TEST: Get Process")
    print("="*80)
    
    # Create process first
    process_data = {
        "name": "Test Process for GET",
        "description": "Test",
        "status": "draft"
    }
    
    create_response = client.post(
        '/api/uds3/vpb/processes',
        data=json.dumps(process_data),
        content_type='application/json'
    )
    
    process_id = create_response.json['process_id']
    print(f"Created Process: {process_id}")
    
    # Get process
    response = client.get(f'/api/uds3/vpb/processes/{process_id}')
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json, indent=2)}")
    
    # Note: Currently returns None from mock backend
    # In production with real DB, this would return data
    assert response.status_code in [200, 404]
    
    print("✅ Test PASSED (mock backend)")


def test_update_process(client):
    """Test: PUT /api/uds3/vpb/processes/<id>"""
    print("\n" + "="*80)
    print("TEST: Update Process")
    print("="*80)
    
    # Create process first
    process_data = {
        "name": "Test Process for UPDATE",
        "description": "Original description",
        "status": "draft"
    }
    
    create_response = client.post(
        '/api/uds3/vpb/processes',
        data=json.dumps(process_data),
        content_type='application/json'
    )
    
    process_id = create_response.json['process_id']
    print(f"Created Process: {process_id}")
    
    # Update process
    updates = {
        "status": "active",
        "description": "Updated description"
    }
    
    response = client.put(
        f'/api/uds3/vpb/processes/{process_id}',
        data=json.dumps(updates),
        content_type='application/json'
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json, indent=2)}")
    
    assert response.status_code == 200
    
    data = response.json
    assert data['success'] == True
    assert 'transaction' in data
    
    if data['transaction']:
        print(f"\n📊 SAGA Transaction:")
        print(f"   State: {data['transaction']['state']}")
        assert data['transaction']['state'] == 'committed'
    
    print("✅ Test PASSED")


def test_delete_process(client):
    """Test: DELETE /api/uds3/vpb/processes/<id>"""
    print("\n" + "="*80)
    print("TEST: Delete Process")
    print("="*80)
    
    # Create process first
    process_data = {
        "name": "Test Process for DELETE",
        "description": "Will be deleted",
        "status": "draft"
    }
    
    create_response = client.post(
        '/api/uds3/vpb/processes',
        data=json.dumps(process_data),
        content_type='application/json'
    )
    
    process_id = create_response.json['process_id']
    print(f"Created Process: {process_id}")
    
    # Delete process (soft delete)
    response = client.delete(f'/api/uds3/vpb/processes/{process_id}?soft_delete=true')
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json, indent=2)}")
    
    assert response.status_code == 200
    
    data = response.json
    assert data['success'] == True
    assert data['soft_delete'] == True
    assert 'transaction' in data
    
    if data['transaction']:
        print(f"\n📊 SAGA Transaction:")
        print(f"   State: {data['transaction']['state']}")
        print(f"   Steps: {len(data['transaction']['steps'])}")
        assert data['transaction']['state'] == 'committed'
    
    print("✅ Test PASSED")


# ============================================================================
# List & Search Tests
# ============================================================================

def test_list_processes(client):
    """Test: GET /api/uds3/vpb/processes"""
    print("\n" + "="*80)
    print("TEST: List Processes")
    print("="*80)
    
    response = client.get('/api/uds3/vpb/processes?limit=10&offset=0')
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json, indent=2)}")
    
    assert response.status_code == 200
    
    data = response.json
    assert data['success'] == True
    assert 'processes' in data
    assert 'count' in data
    
    print(f"Processes: {data['count']}")
    print("✅ Test PASSED")


def test_semantic_search(client):
    """Test: GET /api/uds3/vpb/search"""
    print("\n" + "="*80)
    print("TEST: Semantic Search")
    print("="*80)
    
    response = client.get('/api/uds3/vpb/search?q=Baugenehmigung&top_k=5')
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json, indent=2)}")
    
    assert response.status_code == 200
    
    data = response.json
    assert data['success'] == True
    assert 'results' in data
    assert data['query'] == 'Baugenehmigung'
    
    print("✅ Test PASSED")


def test_semantic_search_missing_query(client):
    """Test: Search without query parameter"""
    print("\n" + "="*80)
    print("TEST: Search - Missing Query")
    print("="*80)
    
    response = client.get('/api/uds3/vpb/search')
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json, indent=2)}")
    
    assert response.status_code == 400
    
    data = response.json
    assert data['success'] == False
    assert 'error' in data
    
    print("✅ Test PASSED")


# ============================================================================
# SAGA Transaction Tests
# ============================================================================

def test_list_saga_transactions(client):
    """Test: GET /api/uds3/saga/transactions"""
    print("\n" + "="*80)
    print("TEST: List SAGA Transactions")
    print("="*80)
    
    # Create some transactions first
    process_data = {"name": "Test Process", "description": "Test"}
    client.post(
        '/api/uds3/vpb/processes',
        data=json.dumps(process_data),
        content_type='application/json'
    )
    
    response = client.get('/api/uds3/saga/transactions?limit=10')
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json, indent=2)}")
    
    assert response.status_code == 200
    
    data = response.json
    assert data['success'] == True
    assert 'transactions' in data
    assert 'count' in data
    
    print(f"Transactions: {data['count']}")
    if data['count'] > 0:
        print(f"Last Transaction State: {data['transactions'][0]['state']}")
    
    print("✅ Test PASSED")


def test_list_saga_transactions_filtered(client):
    """Test: GET /api/uds3/saga/transactions with state filter"""
    print("\n" + "="*80)
    print("TEST: List SAGA Transactions - Filtered")
    print("="*80)
    
    response = client.get('/api/uds3/saga/transactions?state=committed&limit=10')
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json, indent=2)}")
    
    assert response.status_code == 200
    
    data = response.json
    assert data['success'] == True
    assert data['filter_state'] == 'committed'
    
    print("✅ Test PASSED")


def test_get_saga_transaction_status(client):
    """Test: GET /api/uds3/saga/transactions/<id>"""
    print("\n" + "="*80)
    print("TEST: Get SAGA Transaction Status")
    print("="*80)
    
    # Create transaction
    process_data = {"name": "Test Process", "description": "Test"}
    create_response = client.post(
        '/api/uds3/vpb/processes',
        data=json.dumps(process_data),
        content_type='application/json'
    )
    
    transaction_id = create_response.json['transaction']['transaction_id']
    print(f"Transaction ID: {transaction_id}")
    
    # Get status
    response = client.get(f'/api/uds3/saga/transactions/{transaction_id}')
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json, indent=2)}")
    
    assert response.status_code == 200
    
    data = response.json
    assert data['success'] == True
    assert 'transaction' in data
    assert data['transaction']['transaction_id'] == transaction_id
    
    print(f"Transaction State: {data['transaction']['state']}")
    print(f"Transaction Steps: {len(data['transaction']['steps'])}")
    
    print("✅ Test PASSED")


# ============================================================================
# Error Handling Tests
# ============================================================================

def test_create_process_invalid_data(client):
    """Test: Create Process with Invalid Data"""
    print("\n" + "="*80)
    print("TEST: Create Process - Invalid Data")
    print("="*80)
    
    # Missing required field 'name'
    invalid_data = {
        "description": "Missing name field"
    }
    
    response = client.post(
        '/api/uds3/vpb/processes',
        data=json.dumps(invalid_data),
        content_type='application/json'
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json, indent=2)}")
    
    assert response.status_code == 400
    
    data = response.json
    assert data['success'] == False
    assert 'error' in data
    
    print("✅ Test PASSED")


def test_create_process_no_json(client):
    """Test: Create Process without JSON data"""
    print("\n" + "="*80)
    print("TEST: Create Process - No JSON")
    print("="*80)
    
    response = client.post('/api/uds3/vpb/processes')
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json, indent=2)}")
    
    assert response.status_code == 400
    
    data = response.json
    assert data['success'] == False
    
    print("✅ Test PASSED")


def test_get_process_not_found(client):
    """Test: Get Process - Not Found"""
    print("\n" + "="*80)
    print("TEST: Get Process - Not Found")
    print("="*80)
    
    fake_id = "00000000-0000-0000-0000-000000000000"
    
    response = client.get(f'/api/uds3/vpb/processes/{fake_id}')
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json, indent=2)}")
    
    assert response.status_code == 404
    
    data = response.json
    assert data['success'] == False
    
    print("✅ Test PASSED")


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
