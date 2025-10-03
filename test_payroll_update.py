#!/usr/bin/env python3
"""
Test script to update payroll records with allowances and deductions
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:3003"
API_BASE = f"{BASE_URL}/api/v1"

def test_payroll_update():
    """Test updating payroll records with allowances and deductions"""
    print("🧪 Testing Payroll Update with Allowances and Deductions")
    print("=" * 60)
    
    # Step 1: Login as HR user
    print("\n1️⃣ Logging in as HR user...")
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
            
        print("✅ Successfully logged in as HR user")
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
            print("❌ No payroll records found to update")
            return False
        
        # Use first record
        record = records[0]
        record_id = record.get('id')
        print(f"📋 Using record ID: {record_id} for employee: {record.get('employee')}")
        
    except Exception as e:
        print(f"❌ Failed to get payroll records: {e}")
        return False
    
    # Step 3: Test different allowance and deduction scenarios
    test_scenarios = [
        {
            "name": "High Allowances Scenario",
            "data": {
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
            }
        },
        {
            "name": "High Deductions Scenario",
            "data": {
                "basic_salary": 5500.00,
                "housing_allowance": 800.00,
                "transport_allowance": 400.00,
                "medical_allowance": 200.00,
                "meal_allowance": 150.00,
                "loan_deduction": 1200.00,
                "advance_deduction": 500.00,
                "uniform_deduction": 200.00,
                "parking_deduction": 100.00,
                "late_penalty": 100.00
            }
        },
        {
            "name": "Balanced Scenario",
            "data": {
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
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i + 2}️⃣ Testing {scenario['name']}...")
        print("-" * 50)
        
        try:
            # Update the payroll record
            response = requests.put(f"{API_BASE}/payroll/records/{record_id}", 
                                 json=scenario['data'], 
                                 headers=headers)
            response.raise_for_status()
            
            data = response.json()
            updated_record = data.get('updated_record', {})
            
            print("✅ Payroll record updated successfully")
            
            # Show the updated values
            print(f"\n📊 Updated Values:")
            print(f"   Basic Salary: ${updated_record.get('basic_salary', 0):.2f}")
            print(f"   Total Allowances: ${updated_record.get('allowances', 0):.2f}")
            print(f"   Total Deductions: ${updated_record.get('deductions', 0):.2f}")
            print(f"   Net Salary: ${updated_record.get('net_salary', 0):.2f}")
            
            # Show breakdown
            print(f"\n💰 Allowance Breakdown:")
            print(f"   Housing Allowance: ${updated_record.get('housing_allowance', 0):.2f}")
            print(f"   Transport Allowance: ${updated_record.get('transport_allowance', 0):.2f}")
            print(f"   Medical Allowance: ${updated_record.get('medical_allowance', 0):.2f}")
            print(f"   Meal Allowance: ${updated_record.get('meal_allowance', 0):.2f}")
            
            print(f"\n💸 Deduction Breakdown:")
            print(f"   Loan Deduction: ${updated_record.get('loan_deduction', 0):.2f}")
            print(f"   Advance Deduction: ${updated_record.get('advance_deduction', 0):.2f}")
            print(f"   Uniform Deduction: ${updated_record.get('uniform_deduction', 0):.2f}")
            print(f"   Parking Deduction: ${updated_record.get('parking_deduction', 0):.2f}")
            print(f"   Late Penalty: ${updated_record.get('late_penalty', 0):.2f}")
            
            # Verify calculations
            expected_allowances = (
                updated_record.get('housing_allowance', 0) +
                updated_record.get('transport_allowance', 0) +
                updated_record.get('medical_allowance', 0) +
                updated_record.get('meal_allowance', 0)
            )
            
            expected_deductions = (
                updated_record.get('loan_deduction', 0) +
                updated_record.get('advance_deduction', 0) +
                updated_record.get('uniform_deduction', 0) +
                updated_record.get('parking_deduction', 0) +
                updated_record.get('late_penalty', 0)
            )
            
            expected_net = updated_record.get('basic_salary', 0) + expected_allowances - expected_deductions
            actual_net = updated_record.get('net_salary', 0)
            
            print(f"\n🔍 Calculation Verification:")
            print(f"   Expected Net: ${expected_net:.2f}")
            print(f"   Actual Net: ${actual_net:.2f}")
            
            if abs(expected_net - actual_net) < 0.01:
                print("✅ Calculations are correct!")
            else:
                print("❌ Calculation mismatch!")
            
        except Exception as e:
            print(f"❌ Failed to update payroll record: {e}")
            continue
    
    print("\n🎉 Payroll allowance and deduction testing completed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_payroll_update()
