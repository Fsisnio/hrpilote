#!/usr/bin/env python3
"""
Simple API test script for payroll allowances and deductions
Tests the payroll API endpoints directly
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:3003"
API_BASE = f"{BASE_URL}/api/v1"

def test_payroll_api():
    """Test payroll API endpoints"""
    print("🧪 Testing Payroll API Endpoints")
    print("=" * 50)
    
    # Step 1: Login
    print("\n1️⃣ Testing login...")
    login_data = {
        "email": "admin@techcorp.com",
        "password": "Jesus1993@"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=login_data)
        response.raise_for_status()
        
        data = response.json()
        token = data.get("access_token")
        if not token:
            raise Exception("No access token received")
            
        print("✅ Login successful")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Step 2: Test payroll summary
    print("\n2️⃣ Testing payroll summary...")
    try:
        response = requests.get(f"{API_BASE}/payroll/summary", headers=headers)
        response.raise_for_status()
        
        data = response.json()
        print(f"✅ Payroll summary: {data}")
    except Exception as e:
        print(f"❌ Payroll summary failed: {e}")
    
    # Step 3: Test payroll records
    print("\n3️⃣ Testing payroll records...")
    try:
        response = requests.get(f"{API_BASE}/payroll/records", headers=headers)
        response.raise_for_status()
        
        data = response.json()
        records = data.get("records", [])
        print(f"✅ Found {len(records)} payroll records")
        
        if records:
            # Show first record details
            first_record = records[0]
            print(f"📋 First record details:")
            print(f"   Employee: {first_record.get('employee')}")
            print(f"   Basic Salary: ${first_record.get('basic_salary', 0):.2f}")
            print(f"   Allowances: ${first_record.get('allowances', 0):.2f}")
            print(f"   Deductions: ${first_record.get('deductions', 0):.2f}")
            print(f"   Net Salary: ${first_record.get('net_salary', 0):.2f}")
            
            # Show allowance breakdown
            print(f"   Housing Allowance: ${first_record.get('housing_allowance', 0):.2f}")
            print(f"   Transport Allowance: ${first_record.get('transport_allowance', 0):.2f}")
            print(f"   Medical Allowance: ${first_record.get('medical_allowance', 0):.2f}")
            print(f"   Meal Allowance: ${first_record.get('meal_allowance', 0):.2f}")
            
            # Show deduction breakdown
            print(f"   Loan Deduction: ${first_record.get('loan_deduction', 0):.2f}")
            print(f"   Advance Deduction: ${first_record.get('advance_deduction', 0):.2f}")
            print(f"   Uniform Deduction: ${first_record.get('uniform_deduction', 0):.2f}")
            print(f"   Parking Deduction: ${first_record.get('parking_deduction', 0):.2f}")
            print(f"   Late Penalty: ${first_record.get('late_penalty', 0):.2f}")
            
            return records[0].get('id')  # Return first record ID for testing
        else:
            print("⚠️ No payroll records found")
            return None
            
    except Exception as e:
        print(f"❌ Payroll records failed: {e}")
        return None
    
    # Step 4: Test payroll processing
    print("\n4️⃣ Testing payroll processing...")
    try:
        response = requests.post(f"{API_BASE}/payroll/process", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Payroll processing: {data}")
        elif response.status_code == 400:
            data = response.json()
            print(f"⚠️ Payroll processing: {data.get('detail', 'Already processed')}")
        else:
            print(f"❌ Payroll processing failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Payroll processing failed: {e}")
    
    return None

def test_payroll_update(record_id, token):
    """Test updating a payroll record with new allowances and deductions"""
    if not record_id:
        print("❌ No record ID provided for update test")
        return False
    
    print(f"\n5️⃣ Testing payroll record update (ID: {record_id})...")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Test data with various allowances and deductions
    test_data = {
        "basic_salary": 6000.00,
        "housing_allowance": 1200.00,
        "transport_allowance": 600.00,
        "medical_allowance": 400.00,
        "meal_allowance": 300.00,
        "loan_deduction": 800.00,
        "advance_deduction": 200.00,
        "uniform_deduction": 100.00,
        "parking_deduction": 50.00,
        "late_penalty": 0.00
    }
    
    try:
        response = requests.put(f"{API_BASE}/payroll/records/{record_id}", 
                              json=test_data, 
                              headers=headers)
        response.raise_for_status()
        
        data = response.json()
        print("✅ Payroll record updated successfully")
        
        # Show updated values
        updated_record = data.get('updated_record', {})
        print(f"📊 Updated record details:")
        print(f"   Basic Salary: ${updated_record.get('basic_salary', 0):.2f}")
        print(f"   Total Allowances: ${updated_record.get('allowances', 0):.2f}")
        print(f"   Total Deductions: ${updated_record.get('deductions', 0):.2f}")
        print(f"   Net Salary: ${updated_record.get('net_salary', 0):.2f}")
        
        # Verify calculation
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
        
        print(f"\n🔍 Calculation verification:")
        print(f"   Expected Net: ${expected_net:.2f}")
        print(f"   Actual Net: ${actual_net:.2f}")
        
        if abs(expected_net - actual_net) < 0.01:
            print("✅ Calculations are correct!")
            return True
        else:
            print("❌ Calculation mismatch!")
            return False
            
    except Exception as e:
        print(f"❌ Payroll record update failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Payroll API Test")
    print("=" * 50)
    
    # Test basic API functionality
    record_id = test_payroll_api()
    
    if record_id:
        # Get token for update test
        login_data = {
            "email": "admin@techcorp.com",
            "password": "Jesus1993@"
        }
        
        try:
            response = requests.post(f"{API_BASE}/auth/login", json=login_data)
            response.raise_for_status()
            data = response.json()
            token = data.get("access_token")
            
            # Test updating the record
            test_payroll_update(record_id, token)
            
        except Exception as e:
            print(f"❌ Failed to get token for update test: {e}")
    
    print("\n🎉 Payroll API testing completed!")
    print("=" * 50)

if __name__ == "__main__":
    main()
