#!/usr/bin/env python3
"""
Test creating a new payroll record with allowances and deductions
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:3003"
API_BASE = f"{BASE_URL}/api/v1"

def test_create_payroll_record():
    """Test creating a new payroll record with allowances and deductions"""
    print("🧪 Testing Payroll Record Creation")
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
    
    # Step 2: Get employees
    print("\n2️⃣ Getting employees...")
    try:
        response = requests.get(f"{API_BASE}/employees", headers=headers)
        response.raise_for_status()
        
        data = response.json()
        print(f"📊 Employees API response: {json.dumps(data, indent=2)}")
        
        # Handle different response formats
        if isinstance(data, list):
            employees = data
        else:
            employees = data.get("employees", [])
        
        print(f"✅ Found {len(employees)} employees")
        
        if not employees:
            print("❌ No employees found")
            return False
        
        employee = employees[0]
        employee_id = employee.get('id')
        print(f"👤 Using employee: {employee.get('full_name')} (ID: {employee_id})")
        
    except Exception as e:
        print(f"❌ Failed to get employees: {e}")
        return False
    
    # Step 3: Create new payroll record
    print("\n3️⃣ Creating new payroll record...")
    payroll_data = {
        "employee_id": employee_id,
        "basic_salary": 4000.00,
        "status": "PROCESSING",
        "housing_allowance": 800.00,
        "transport_allowance": 400.00,
        "medical_allowance": 200.00,
        "meal_allowance": 150.00,
        "loan_deduction": 600.00,
        "advance_deduction": 150.00,
        "uniform_deduction": 75.00,
        "parking_deduction": 40.00,
        "late_penalty": 0.00,
        "notes": "Test payroll record with allowances and deductions"
    }
    
    print(f"📤 Sending payroll data: {json.dumps(payroll_data, indent=2)}")
    
    try:
        response = requests.post(f"{API_BASE}/payroll/records", 
                                json=payroll_data, 
                                headers=headers)
        
        print(f"📥 Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Payroll record created successfully!")
            print(f"📊 Response data: {json.dumps(data, indent=2)}")
            
            # Check if the components are properly stored
            created_record = data.get('created_record', {})
            print(f"\n🔍 Component Verification:")
            print(f"   Basic Salary: ${created_record.get('basic_salary', 0):.2f}")
            print(f"   Housing Allowance: ${created_record.get('housing_allowance', 0):.2f}")
            print(f"   Transport Allowance: ${created_record.get('transport_allowance', 0):.2f}")
            print(f"   Medical Allowance: ${created_record.get('medical_allowance', 0):.2f}")
            print(f"   Meal Allowance: ${created_record.get('meal_allowance', 0):.2f}")
            print(f"   Loan Deduction: ${created_record.get('loan_deduction', 0):.2f}")
            print(f"   Advance Deduction: ${created_record.get('advance_deduction', 0):.2f}")
            print(f"   Uniform Deduction: ${created_record.get('uniform_deduction', 0):.2f}")
            print(f"   Parking Deduction: ${created_record.get('parking_deduction', 0):.2f}")
            print(f"   Late Penalty: ${created_record.get('late_penalty', 0):.2f}")
            print(f"   Total Allowances: ${created_record.get('allowances', 0):.2f}")
            print(f"   Total Deductions: ${created_record.get('deductions', 0):.2f}")
            print(f"   Net Salary: ${created_record.get('net_salary', 0):.2f}")
            
            return True
        else:
            print(f"❌ Payroll record creation failed with status {response.status_code}")
            print(f"📥 Response text: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Payroll record creation failed: {e}")
        return False

if __name__ == "__main__":
    test_create_payroll_record()
