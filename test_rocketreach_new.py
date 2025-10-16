#!/usr/bin/env python3
"""
Test the updated RocketReach API integration with correct endpoints.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to the sys.path to allow importing newsplease
sys.path.append(str(Path(__file__).resolve().parent))

from integrations.rocketreach import RocketReachAPI

# Load environment variables
load_dotenv()

def test_rocketreach_api():
    """Test the RocketReach API with correct endpoints."""
    print("=== ROCKETREACH API TEST (UPDATED) ===")
    
    # Check API key
    api_key = os.getenv('ROCKETREACH_API_KEY')
    if not api_key:
        print("❌ ERROR: ROCKETREACH_API_KEY not found in environment variables")
        return
    
    print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        # Initialize the API
        api = RocketReachAPI()
        print("✅ RocketReach API initialized successfully")
        
        # Test with a sample lookup
        test_name = "John Doe"
        test_domain = "example.com"
        
        print(f"\n🔍 Testing lookup: {test_name} at {test_domain}")
        result = api.lookup_email_by_name_and_domain(test_name, test_domain)
        
        if result:
            print("✅ SUCCESS! Found contact:")
            print(f"   Name: {result.get('full_name', 'N/A')}")
            print(f"   Email: {result.get('email', 'N/A')}")
            print(f"   Confidence: {result.get('confidence', 'N/A')}")
            print(f"   Title: {result.get('title', 'N/A')}")
            print(f"   Company: {result.get('company', 'N/A')}")
        else:
            print("❌ No contact found (this might be expected for test data)")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rocketreach_api()
