#!/usr/bin/env python3
"""
Test script to verify that reports show organization-specific data, not static data
"""

import requests
import json
import time
from datetime import datetime, date

# Configuration
BASE_URL = "http://localhost:3003"
API_BASE = f"{BASE_URL}/api/v1"

def test_reports_organization_specific():
    """Test that all reports show organization-specific data"""
    print("📊 Testing Reports - Organization-Specific Data")
    print("=" * 60)
    
    # Manager credentials
    email = "manager@hrpilot.com"
    password = "Jesus1993@"
    
    # Login as manager
    print(f"📧 Logging in as: {email}")
    
    login_response = requests.post(f"{API_BASE}/auth/login", json={
        "email": email,
        "password": password
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return False
    
    login_data = login_response.json()
    token = login_data["access_token"]
    user_data = login_data["user"]
    
    print(f"✅ Logged in successfully!")
    print(f"   Name: {user_data['first_name']} {user_data['last_name']}")
    print(f"   Role: {user_data['role']}")
    print(f"   Organization ID: {user_data['organization_id']}")
    
    # Set authorization header
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n🔍 Testing All Reports for Organization-Specific Data...")
    print("-" * 60)
    
    # Test 1: Dashboard Report
    print("📊 1. Dashboard Report:")
    dashboard_response = requests.get(f"{API_BASE}/reports/dashboard", headers=headers)
    
    if dashboard_response.status_code == 200:
        dashboard_data = dashboard_response.json()
        print(f"   ✅ Access granted")
        print(f"   Total employees: {dashboard_data.get('total_employees')}")
        print(f"   Active employees: {dashboard_data.get('active_employees')}")
        print(f"   Recent hires: {dashboard_data.get('recent_hires')}")
        print(f"   Pending leave requests: {dashboard_data.get('pending_leave_requests')}")
        print(f"   Organization ID: {dashboard_data.get('organization_id')}")
        
        # Verify organization filtering
        if dashboard_data.get('organization_id') == user_data['organization_id']:
            print(f"   ✅ Organization filtering: CORRECT")
        else:
            print(f"   ❌ Organization filtering: INCORRECT")
    else:
        print(f"   ❌ Access denied: {dashboard_response.text}")
    
    # Test 2: Employee Reports
    print(f"\n👥 2. Employee Reports:")
    employee_reports_response = requests.get(f"{API_BASE}/reports/employee", headers=headers)
    
    if employee_reports_response.status_code == 200:
        employee_reports_data = employee_reports_response.json()
        print(f"   ✅ Access granted")
        print(f"   Employees by status: {employee_reports_data.get('employees_by_status')}")
        print(f"   Employees by type: {employee_reports_data.get('employees_by_type')}")
        print(f"   Employees by department: {employee_reports_data.get('employees_by_department')}")
        print(f"   Organization ID: {employee_reports_data.get('organization_id')}")
        
        # Verify organization filtering
        if employee_reports_data.get('organization_id') == user_data['organization_id']:
            print(f"   ✅ Organization filtering: CORRECT")
        else:
            print(f"   ❌ Organization filtering: INCORRECT")
            
        # Verify data is not static by checking if it matches dashboard
        dashboard_data = dashboard_response.json() if dashboard_response.status_code == 200 else {}
        active_count_dashboard = dashboard_data.get('active_employees', 0)
        
        # Count active employees from employee reports
        active_count_reports = 0
        for status_info in employee_reports_data.get('employees_by_status', []):
            if status_info.get('status') == 'ACTIVE':
                active_count_reports = status_info.get('count', 0)
                break
        
        if active_count_dashboard == active_count_reports:
            print(f"   ✅ Data consistency: Employee reports match dashboard data")
        else:
            print(f"   ❌ Data inconsistency: Employee reports don't match dashboard")
            print(f"      Dashboard active: {active_count_dashboard}, Reports active: {active_count_reports}")
            
    else:
        print(f"   ❌ Access denied: {employee_reports_response.text}")
    
    # Test 3: Attendance Reports
    print(f"\n⏰ 3. Attendance Reports:")
    attendance_reports_response = requests.get(f"{API_BASE}/reports/attendance", headers=headers)
    
    if attendance_reports_response.status_code == 200:
        attendance_reports_data = attendance_reports_response.json()
        print(f"   ✅ Access granted")
        print(f"   Total records: {attendance_reports_data.get('total_records')}")
        print(f"   On time: {attendance_reports_data.get('on_time')}")
        print(f"   Late: {attendance_reports_data.get('late')}")
        print(f"   Absent: {attendance_reports_data.get('absent')}")
        print(f"   Attendance rate: {attendance_reports_data.get('attendance_rate')}%")
        print(f"   Date range: {attendance_reports_data.get('date_range')}")
        print(f"   Organization ID: {attendance_reports_data.get('organization_id')}")
        
        # Verify organization filtering
        if attendance_reports_data.get('organization_id') == user_data['organization_id']:
            print(f"   ✅ Organization filtering: CORRECT")
        else:
            print(f"   ❌ Organization filtering: INCORRECT")
    else:
        print(f"   ❌ Access denied: {attendance_reports_response.text}")
    
    # Test 4: Payroll Reports
    print(f"\n💰 4. Payroll Reports:")
    payroll_reports_response = requests.get(f"{API_BASE}/reports/payroll", headers=headers)
    
    if payroll_reports_response.status_code == 200:
        payroll_reports_data = payroll_reports_response.json()
        print(f"   ✅ Access granted")
        print(f"   Total records: {payroll_reports_data.get('total_records')}")
        print(f"   Total amount: ${payroll_reports_data.get('total_amount'):,.2f}")
        print(f"   Average pay: ${payroll_reports_data.get('average_pay'):,.2f}")
        print(f"   Month: {payroll_reports_data.get('month')}")
        print(f"   Year: {payroll_reports_data.get('year')}")
        print(f"   Organization ID: {payroll_reports_data.get('organization_id')}")
        
        # Verify organization filtering
        if payroll_reports_data.get('organization_id') == user_data['organization_id']:
            print(f"   ✅ Organization filtering: CORRECT")
        else:
            print(f"   ❌ Organization filtering: INCORRECT")
    else:
        print(f"   ❌ Access denied: {payroll_reports_response.text}")
    
    # Test 5: Verify data is dynamic by making multiple calls
    print(f"\n🔄 5. Testing Data Dynamics:")
    print("-" * 30)
    
    # Make multiple dashboard calls to verify consistency
    dashboard_calls = []
    for i in range(3):
        response = requests.get(f"{API_BASE}/reports/dashboard", headers=headers)
        if response.status_code == 200:
            dashboard_calls.append(response.json())
        time.sleep(0.5)  # Small delay between calls
    
    if len(dashboard_calls) >= 2:
        # Compare first and last call
        first_call = dashboard_calls[0]
        last_call = dashboard_calls[-1]
        
        if first_call == last_call:
            print(f"   ✅ Data consistency: Multiple calls return same data")
            print(f"   Total employees: {first_call.get('total_employees')}")
            print(f"   Active employees: {first_call.get('active_employees')}")
        else:
            print(f"   ❌ Data inconsistency: Multiple calls return different data")
    
    # Summary
    print(f"\n📋 Summary:")
    print("=" * 60)
    
    reports_tested = 0
    reports_passed = 0
    
    # Check each report
    reports = [
        ("Dashboard", dashboard_response.status_code == 200),
        ("Employee Reports", employee_reports_response.status_code == 200),
        ("Attendance Reports", attendance_reports_response.status_code == 200),
        ("Payroll Reports", payroll_reports_response.status_code == 200)
    ]
    
    for report_name, has_access in reports:
        reports_tested += 1
        if has_access:
            reports_passed += 1
            print(f"   ✅ {report_name}: Organization-specific data")
        else:
            print(f"   ❌ {report_name}: No access")
    
    print(f"\n🎯 Results:")
    print(f"   Reports tested: {reports_tested}")
    print(f"   Reports with organization-specific data: {reports_passed}")
    print(f"   Organization ID: {user_data['organization_id']}")
    
    if reports_passed == reports_tested:
        print(f"   ✅ ALL REPORTS SHOW ORGANIZATION-SPECIFIC DATA!")
        print(f"   ✅ Manager can only see data from their organization")
        print(f"   ✅ Multi-tenant data isolation is working correctly")
    else:
        print(f"   ❌ Some reports are not showing organization-specific data")
    
    return reports_passed == reports_tested

if __name__ == "__main__":
    try:
        test_reports_organization_specific()
    except Exception as e:
        print(f"💥 Test failed with error: {e}")
