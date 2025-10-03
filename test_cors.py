#!/usr/bin/env python3
"""
Test script to verify CORS configuration is working properly.
"""

import requests
import json

def test_cors_configuration():
    """Test CORS configuration by making requests from different origins"""
    
    # Test URLs
    base_url = "http://localhost:3003"
    cors_test_url = f"{base_url}/cors-test"
    employees_url = f"{base_url}/api/v1/employees"
    
    print("🧪 Testing CORS Configuration...")
    print(f"Backend URL: {base_url}")
    print()
    
    # Test 1: Check if backend is running
    print("1️⃣ Testing backend connectivity...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Is it running on port 3003?")
        print("   Try running: uvicorn app.main:app --host 0.0.0.0 --port 3003 --reload")
        return False
    except Exception as e:
        print(f"❌ Error connecting to backend: {e}")
        return False
    
    # Test 2: Test CORS configuration
    print("\n2️⃣ Testing CORS configuration...")
    try:
        headers = {
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'GET',
            'Access-Control-Request-Headers': 'Content-Type,Authorization'
        }
        
        # Test preflight request
        response = requests.options(cors_test_url, headers=headers, timeout=5)
        print(f"   Preflight response status: {response.status_code}")
        print(f"   CORS headers: {dict(response.headers)}")
        
        if 'Access-Control-Allow-Origin' in response.headers:
            print("✅ CORS headers are present")
        else:
            print("❌ CORS headers are missing")
            
    except Exception as e:
        print(f"❌ Error testing CORS: {e}")
    
    # Test 3: Test actual request with Origin header
    print("\n3️⃣ Testing actual request with Origin header...")
    try:
        headers = {
            'Origin': 'http://localhost:3000',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(cors_test_url, headers=headers, timeout=5)
        print(f"   Response status: {response.status_code}")
        print(f"   Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ CORS request successful")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ CORS request failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error making CORS request: {e}")
    
    # Test 4: Test employees endpoint
    print("\n4️⃣ Testing employees endpoint...")
    try:
        headers = {
            'Origin': 'http://localhost:3000',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(employees_url, headers=headers, timeout=5)
        print(f"   Employees endpoint status: {response.status_code}")
        
        if response.status_code in [200, 401, 403]:  # 401/403 are expected without auth
            print("✅ Employees endpoint is accessible (auth required)")
        else:
            print(f"❌ Employees endpoint returned unexpected status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing employees endpoint: {e}")
    
    print("\n🎯 CORS Test Summary:")
    print("   - If you see CORS errors in the browser, the issue might be:")
    print("     1. Backend not running on port 3003")
    print("     2. CORS middleware not properly configured")
    print("     3. Browser cache issues")
    print("   - Try clearing browser cache and restarting both frontend and backend")
    
    return True

if __name__ == "__main__":
    test_cors_configuration()
