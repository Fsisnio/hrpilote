#!/usr/bin/env python3
"""
Debug script to test payroll update with detailed logging
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:3003"
API_BASE = f"{BASE_URL}/api/v1"

def debug_payroll_update():
    """Debug payroll update with detailed logging"""
    print("🔍 Debugging Payroll Update")
    print("=" * 50)
    
    # Step 1: Login
    print("\n1️⃣ Logging in...")
    login_data = {
        "email": "hr@techcorp.com",
        "password": "Password123!"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        response.raise_for_status()
        
        data = response.json()
        token = data.get("access_token")
        if not token:
            raise Exception("No access token received")
            
        print("✅ Successfully logged in")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Step 2: Get existing payroll records
    print("\n2️⃣ Getting existing payroll records...")
    try:
        response = requests.get(f"{API_BASE}/payroll/records", headers=headers)
        response.raise_for_status()
        
        data = response.json()
        records = data.get("records", [])
        print(f"✅ Found {len(records)} payroll records")
        
        if not records:
            print("❌ No payroll records found")
            return False
        
        record = records[0]
        record_id = record.get('id')
        print(f"📋 Using record ID: {record_id}")
        print(f"📋 Current record data:")
        print(f"   Basic Salary: ${record.get('basic_salary', 0):.2f}")
        print(f"   Net Salary: ${record.get('net_salary', 0):.2f}")
        print(f"   Housing Allowance: ${record.get('housing_allowance', 0):.2f}")
        print(f"   Transport Allowance: ${record.get('transport_allowance', 0):.2f}")
        
    except Exception as e:
        print(f"❌ Failed to get payroll records: {e}")
        return False
    
    # Step 3: Test a simple update
    print("\n3️⃣ Testing simple payroll update...")
    test_data = {
        "basic_salary": 5000.00,
        "housing_allowance": 1000.00,
        "transport_allowance": 500.00,
        "medical_allowance": 300.00,
        "meal_allowance": 200.00,
        "loan_deduction": 800.00,
        "advance_deduction": 200.00,
        "uniform_deduction": 100.00,
        "parking_deduction": 50.00,
        "late_penalty": 0.00
    }
    
    print(f"📤 Sending update data: {json.dumps(test_data, indent=2)}")
    
    try:
        response = requests.put(f"{API_BASE}/payroll/records/{record_id}", 
                              json=test_data, 
                              headers=headers)
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Update successful!")
            print(f"📊 Response data: {json.dumps(data, indent=2)}")
        else:
            print(f"❌ Update failed with status {response.status_code}")
            print(f"📥 Response text: {response.text}")
            
    except Exception as e:
        print(f"❌ Update request failed: {e}")
    
    print("\n🎉 Debug completed!")
    return True

if __name__ == "__main__":
    debug_payroll_update()
