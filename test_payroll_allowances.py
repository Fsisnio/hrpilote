#!/usr/bin/env python3
"""
Test script to add allowance and reduction components to payroll records
This script will test the payroll functionality with various allowance and deduction amounts
"""

import requests
import json
import sys
from decimal import Decimal

# Configuration
BASE_URL = "http://localhost:3003"
API_BASE = f"{BASE_URL}/api/v1"

def login_and_get_token():
    """Login and get authentication token"""
    login_data = {
        "email": "directadmin@hrpilot.org",
        "password": "admin123"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        response.raise_for_status()
        
        data = response.json()
        token = data.get("access_token")
        if not token:
            raise Exception("No access token received")
            
        print("✅ Successfully logged in")
        return token
    except Exception as e:
        print(f"❌ Login failed: {e}")
        sys.exit(1)

def get_headers(token):
    """Get headers with authentication token"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def get_employees(token):
    """Get list of employees"""
    try:
        response = requests.get(f"{API_BASE}/employees", headers=get_headers(token))
        response.raise_for_status()
        
        data = response.json()
        employees = data.get("employees", [])
        print(f"📋 Found {len(employees)} employees")
        return employees
    except Exception as e:
        print(f"❌ Failed to get employees: {e}")
        return []

def get_payroll_records(token):
    """Get existing payroll records"""
    try:
        response = requests.get(f"{API_BASE}/payroll/records", headers=get_headers(token))
        response.raise_for_status()
        
        data = response.json()
        records = data.get("records", [])
        print(f"📊 Found {len(records)} payroll records")
        return records
    except Exception as e:
        print(f"❌ Failed to get payroll records: {e}")
        return []

def create_test_payroll_record(token, employee_id):
    """Create a new payroll record with test allowances and deductions"""
    test_data = {
        "employee_id": employee_id,
        "basic_salary": 5000.00,
        "status": "PROCESSING",
        "housing_allowance": 1000.00,
        "transport_allowance": 500.00,
        "medical_allowance": 300.00,
        "meal_allowance": 200.00,
        "loan_deduction": 800.00,
        "advance_deduction": 200.00,
        "uniform_deduction": 100.00,
        "parking_deduction": 50.00,
        "late_penalty": 0.00,
        "notes": "Test payroll record with allowances and deductions"
    }
    
    try:
        response = requests.post(f"{API_BASE}/payroll/records", 
                               json=test_data, 
                               headers=get_headers(token))
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Created payroll record: {data.get('record_id')}")
        return data.get('record_id')
    except Exception as e:
        print(f"❌ Failed to create payroll record: {e}")
        return None

def update_payroll_record(token, record_id, test_scenario):
    """Update payroll record with different test scenarios"""
    scenarios = {
        "high_allowances": {
            "basic_salary": 6000.00,
            "housing_allowance": 1500.00,
            "transport_allowance": 800.00,
            "medical_allowance": 500.00,
            "meal_allowance": 400.00,
            "loan_deduction": 500.00,
            "advance_deduction": 100.00,
            "uniform_deduction": 50.00,
            "parking_deduction": 25.00,
            "late_penalty": 0.00
        },
        "high_deductions": {
            "basic_salary": 5000.00,
            "housing_allowance": 800.00,
            "transport_allowance": 400.00,
            "medical_allowance": 200.00,
            "meal_allowance": 150.00,
            "loan_deduction": 1200.00,
            "advance_deduction": 500.00,
            "uniform_deduction": 200.00,
            "parking_deduction": 100.00,
            "late_penalty": 100.00
        },
        "balanced": {
            "basic_salary": 5500.00,
            "housing_allowance": 1200.00,
            "transport_allowance": 600.00,
            "medical_allowance": 400.00,
            "meal_allowance": 300.00,
            "loan_deduction": 700.00,
            "advance_deduction": 300.00,
            "uniform_deduction": 150.00,
            "parking_deduction": 75.00,
            "late_penalty": 0.00
        }
    }
    
    if test_scenario not in scenarios:
        print(f"❌ Unknown test scenario: {test_scenario}")
        return None
    
    test_data = scenarios[test_scenario]
    
    try:
        response = requests.put(f"{API_BASE}/payroll/records/{record_id}", 
                              json=test_data, 
                              headers=get_headers(token))
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Updated payroll record with {test_scenario} scenario")
        return data.get('updated_record')
    except Exception as e:
        print(f"❌ Failed to update payroll record: {e}")
        return None

def calculate_expected_totals(data):
    """Calculate expected totals for verification"""
    basic_salary = data.get('basic_salary', 0)
    
    # Total allowances
    allowances = (
        data.get('housing_allowance', 0) +
        data.get('transport_allowance', 0) +
        data.get('medical_allowance', 0) +
        data.get('meal_allowance', 0)
    )
    
    # Total deductions
    deductions = (
        data.get('loan_deduction', 0) +
        data.get('advance_deduction', 0) +
        data.get('uniform_deduction', 0) +
        data.get('parking_deduction', 0) +
        data.get('late_penalty', 0)
    )
    
    gross_pay = basic_salary + allowances
    net_pay = gross_pay - deductions
    
    return {
        'basic_salary': basic_salary,
        'total_allowances': allowances,
        'total_deductions': deductions,
        'gross_pay': gross_pay,
        'net_pay': net_pay
    }

def verify_calculations(record_data, expected):
    """Verify that calculations are correct"""
    print("\n🔍 Verifying calculations:")
    print(f"   Basic Salary: ${record_data.get('basic_salary', 0):.2f}")
    print(f"   Total Allowances: ${record_data.get('allowances', 0):.2f}")
    print(f"   Total Deductions: ${record_data.get('deductions', 0):.2f}")
    print(f"   Net Salary: ${record_data.get('net_salary', 0):.2f}")
    
    print(f"\n📊 Expected vs Actual:")
    print(f"   Expected Gross: ${expected['gross_pay']:.2f}")
    print(f"   Expected Net: ${expected['net_pay']:.2f}")
    
    # Check if calculations match
    actual_net = record_data.get('net_salary', 0)
    expected_net = expected['net_pay']
    
    if abs(actual_net - expected_net) < 0.01:  # Allow for small floating point differences
        print("✅ Calculations are correct!")
        return True
    else:
        print(f"❌ Calculation mismatch! Expected: ${expected_net:.2f}, Got: ${actual_net:.2f}")
        return False

def main():
    """Main test function"""
    print("🧪 Starting Payroll Allowance and Deduction Test")
    print("=" * 60)
    
    # Step 1: Login
    print("\n1️⃣ Logging in...")
    token = login_and_get_token()
    
    # Step 2: Get employees
    print("\n2️⃣ Getting employees...")
    employees = get_employees(token)
    if not employees:
        print("❌ No employees found. Cannot proceed with test.")
        return
    
    # Use first employee for testing
    test_employee = employees[0]
    print(f"👤 Using employee: {test_employee.get('full_name')} (ID: {test_employee.get('id')})")
    
    # Step 3: Check existing payroll records
    print("\n3️⃣ Checking existing payroll records...")
    existing_records = get_payroll_records(token)
    
    record_id = None
    if existing_records:
        # Use existing record
        record_id = existing_records[0].get('id')
        print(f"📋 Using existing payroll record: {record_id}")
    else:
        # Create new record
        print("\n4️⃣ Creating new payroll record...")
        record_id = create_test_payroll_record(token, test_employee.get('id'))
        if not record_id:
            print("❌ Failed to create payroll record. Cannot proceed.")
            return
    
    # Step 5: Test different scenarios
    test_scenarios = [
        ("high_allowances", "High Allowances Scenario"),
        ("high_deductions", "High Deductions Scenario"), 
        ("balanced", "Balanced Scenario")
    ]
    
    for scenario, description in test_scenarios:
        print(f"\n5️⃣ Testing {description}...")
        print("-" * 40)
        
        # Update the record
        updated_record = update_payroll_record(token, record_id, scenario)
        if not updated_record:
            print(f"❌ Failed to update record for {scenario}")
            continue
        
        # Calculate expected values
        expected = calculate_expected_totals(updated_record)
        
        # Verify calculations
        is_correct = verify_calculations(updated_record, expected)
        
        if is_correct:
            print(f"✅ {description} test passed!")
        else:
            print(f"❌ {description} test failed!")
    
    print("\n🎉 Payroll allowance and deduction testing completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
