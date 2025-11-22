#!/usr/bin/env python3
"""
Check payroll components in the database
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:3003"
API_BASE = f"{BASE_URL}/api/v1"

def check_payroll_components():
    """Check payroll components in the database"""
    print("🔍 Checking Payroll Components")
    print("=" * 50)
    
    # Step 1: Login
    print("\n1️⃣ Logging in...")
    login_data = {
        "email": "hr@techcorp.com",
        "password": "Jesus1993@"
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
    
    # Step 2: Get payroll records
    print("\n2️⃣ Getting payroll records...")
    try:
        response = requests.get(f"{API_BASE}/payroll/records", headers=headers)
        response.raise_for_status()
        
        data = response.json()
        records = data.get("records", [])
        print(f"✅ Found {len(records)} payroll records")
        
        if records:
            record = records[0]
            record_id = record.get('id')
            print(f"📋 Record ID: {record_id}")
            print(f"📋 Employee: {record.get('employee')}")
            print(f"📋 Basic Salary: ${record.get('basic_salary', 0):.2f}")
            print(f"📋 Net Salary: ${record.get('net_salary', 0):.2f}")
            
            # Check individual components
            print(f"\n💰 Allowance Components:")
            print(f"   Housing Allowance: ${record.get('housing_allowance', 0):.2f}")
            print(f"   Transport Allowance: ${record.get('transport_allowance', 0):.2f}")
            print(f"   Medical Allowance: ${record.get('medical_allowance', 0):.2f}")
            print(f"   Meal Allowance: ${record.get('meal_allowance', 0):.2f}")
            
            print(f"\n💸 Deduction Components:")
            print(f"   Loan Deduction: ${record.get('loan_deduction', 0):.2f}")
            print(f"   Advance Deduction: ${record.get('advance_deduction', 0):.2f}")
            print(f"   Uniform Deduction: ${record.get('uniform_deduction', 0):.2f}")
            print(f"   Parking Deduction: ${record.get('parking_deduction', 0):.2f}")
            print(f"   Late Penalty: ${record.get('late_penalty', 0):.2f}")
            
            print(f"\n📊 Totals:")
            print(f"   Total Allowances: ${record.get('allowances', 0):.2f}")
            print(f"   Total Deductions: ${record.get('deductions', 0):.2f}")
            
    except Exception as e:
        print(f"❌ Failed to get payroll records: {e}")
        return False
    
    print("\n🎉 Component check completed!")
    return True

if __name__ == "__main__":
    check_payroll_components()
