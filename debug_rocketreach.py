#!/usr/bin/env python3
"""
Debug script to test RocketReach API connection and show detailed error information.
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_rocketreach_connection():
    """Test RocketReach API connection with detailed error reporting."""
    
    print("=== ROCKETREACH API DEBUG ===")
    
    # Check API key
    api_key = os.getenv('ROCKETREACH_API_KEY')
    if not api_key:
        print("❌ ERROR: ROCKETREACH_API_KEY not found in environment variables")
        print("Make sure you have a .env file with: ROCKETREACH_API_KEY=your_key_here")
        return
    
    print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]}")
    
    # Test API endpoint
    base_url = "https://api.rocketreach.co/v2"
    endpoint = "api/lookup"
    url = f"{base_url}/{endpoint}"
    
    print(f"🌐 Testing URL: {url}")
    
    # Prepare headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test data
    test_data = {
        "name": "John Doe",
        "company_domain": "example.com"
    }
    
    print(f"📤 Request headers: {headers}")
    print(f"📤 Request data: {test_data}")
    
    try:
        print("\n🚀 Making API request...")
        response = requests.post(url, json=test_data, headers=headers, timeout=30)
        
        print(f"📊 Response Status Code: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: API connected successfully!")
            print(f"📄 Response: {response.json()}")
        else:
            print(f"❌ ERROR: API returned status {response.status_code}")
            print(f"📄 Response Text: {response.text}")
            
            # Try to parse as JSON for more details
            try:
                error_json = response.json()
                print(f"📄 Response JSON: {error_json}")
            except:
                print("📄 Response is not valid JSON")
                
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ ERROR: Connection error - {e}")
    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Request failed - {e}")
    except Exception as e:
        print(f"❌ ERROR: Unexpected error - {e}")

if __name__ == "__main__":
    test_rocketreach_connection()
