"""
Test script for complete workflow:
Upload → Process → Report → Chat
"""

import requests
import json
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8080"
API_KEY = "demo-key-12345"  # From .env
USER_ID = "test_user"

headers = {
    "X-API-Key": API_KEY
}

def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.status_code == 200

def test_single_upload():
    """Test single file upload"""
    print("\n=== Testing Single File Upload ===")
    
    # Use sample data
    sample_file = Path("../sample_data/bank_statement.csv")
    if not sample_file.exists():
        print("Sample file not found!")
        return False
    
    with open(sample_file, 'rb') as f:
        files = {'file': ('bank_statement.csv', f, 'text/csv')}
        response = requests.post(
            f"{BASE_URL}/upload",
            files=files,
            params={"user_id": USER_ID},
            headers=headers
        )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2))
    return response.status_code == 200

def test_multiple_upload():
    """Test multiple file upload"""
    print("\n=== Testing Multiple File Upload ===")
    
    sample_files = [
        Path("../sample_data/bank_statement.csv"),
        Path("../sample_data/invoice_register.csv")
    ]
    
    files = []
    for sample_file in sample_files:
        if sample_file.exists():
            files.append(
                ('files', (sample_file.name, open(sample_file, 'rb'), 'text/csv'))
            )
    
    if not files:
        print("No sample files found!")
        return False
    
    response = requests.post(
        f"{BASE_URL}/upload-multiple",
        files=files,
        params={"user_id": USER_ID},
        headers=headers
    )
    
    # Close file handles
    for _, (_, f, _) in files:
        f.close()
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2))
    return response.status_code == 200

def test_search():
    """Test document search"""
    print("\n=== Testing Document Search ===")
    
    response = requests.post(
        f"{BASE_URL}/search",
        params={
            "query": "What are the total transactions?",
            "user_id": USER_ID,
            "top_k": 3
        },
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2))
    return response.status_code == 200

def test_generate_report():
    """Test report generation"""
    print("\n=== Testing Report Generation ===")
    
    response = requests.post(
        f"{BASE_URL}/generate-report",
        params={"user_id": USER_ID},
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    
    if "text_report" in result:
        print("\n--- Text Report ---")
        print(result["text_report"])
    else:
        print(json.dumps(result, indent=2))
    
    return response.status_code == 200

def test_chat():
    """Test chat with data"""
    print("\n=== Testing Chat with Data ===")
    
    questions = [
        "What documents have I uploaded?",
        "Show me the bank statement data",
        "What's my checklist status?"
    ]
    
    session_id = None
    
    for question in questions:
        print(f"\nQ: {question}")
        
        params = {
            "message": question,
            "user_id": USER_ID
        }
        if session_id:
            params["session_id"] = session_id
        
        response = requests.post(
            f"{BASE_URL}/chat",
            params=params,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()
            session_id = result.get("session_id")
            print(f"A: {result.get('response')}")
        else:
            print(f"Error: {response.status_code}")
            return False
    
    return True

def test_checklist():
    """Test checklist endpoint"""
    print("\n=== Testing Checklist ===")
    
    response = requests.get(
        f"{BASE_URL}/checklist/{USER_ID}",
        headers=headers
    )
    
    print(f"Status: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2))
    return response.status_code == 200

def run_all_tests():
    """Run all tests in sequence"""
    print("=" * 60)
    print("COMPLETE WORKFLOW TEST")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health),
        ("Single Upload", test_single_upload),
        ("Multiple Upload", test_multiple_upload),
        ("Checklist", test_checklist),
        ("Search Documents", test_search),
        ("Generate Report", test_generate_report),
        ("Chat with Data", test_chat),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ {name} failed with error: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")

if __name__ == "__main__":
    run_all_tests()
