#!/usr/bin/env python3
"""
Test different RocketReach API endpoints to find the correct one.
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_endpoint(url, method="GET", data=None):
    """Test a specific endpoint."""
    api_key = os.getenv('ROCKETREACH_API_KEY')
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    print(f"\n🔍 Testing: {method} {url}")
    print(f"📤 Headers: {headers}")
    if data:
        print(f"📤 Data: {data}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        
        print(f"📊 Status: {response.status_code}")
        print(f"📊 Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ SUCCESS!")
            try:
                print(f"📄 JSON Response: {response.json()}")
            except:
                print(f"📄 Text Response: {response.text[:200]}...")
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"📄 Response: {response.text[:500]}...")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")

def main():
    """Test various RocketReach API endpoints."""
    print("=== ROCKETREACH API ENDPOINT TESTING ===")
    
    # Test data
    test_data = {
        "name": "John Doe",
        "company_domain": "example.com"
    }
    
    # Different possible endpoints to test
    endpoints = [
        # V1 endpoints
        ("https://api.rocketreach.co/v1/lookup", "POST", test_data),
        ("https://api.rocketreach.co/v1/api/lookup", "POST", test_data),
        ("https://api.rocketreach.co/v1/search", "POST", test_data),
        
        # V2 endpoints
        ("https://api.rocketreach.co/v2/lookup", "POST", test_data),
        ("https://api.rocketreach.co/v2/api/lookup", "POST", test_data),
        ("https://api.rocketreach.co/v2/search", "POST", test_data),
        
        # Alternative base URLs
        ("https://rocketreach.co/api/v1/lookup", "POST", test_data),
        ("https://rocketreach.co/api/v2/lookup", "POST", test_data),
        
        # Simple GET endpoints to test connectivity
        ("https://api.rocketreach.co/v1/", "GET", None),
        ("https://api.rocketreach.co/v2/", "GET", None),
        ("https://api.rocketreach.co/", "GET", None),
    ]
    
    for url, method, data in endpoints:
        test_endpoint(url, method, data)
        print("-" * 80)

if __name__ == "__main__":
    main()
