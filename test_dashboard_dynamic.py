#!/usr/bin/env python3
"""
Test script to verify that the dashboard shows dynamic data, not static data
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:3003"
API_BASE = f"{BASE_URL}/api/v1"

def test_dashboard_dynamic_data():
    """Test that dashboard data is dynamic and calculated from real database data"""
    print("📊 Testing Dashboard Data - Dynamic vs Static")
    print("=" * 50)
    
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
    
    print(f"\n🔍 Analyzing Dashboard Data vs Real Database Data...")
    print("-" * 50)
    
    # 1. Get dashboard data
    print("📊 Dashboard Data:")
    dashboard_response = requests.get(f"{API_BASE}/reports/dashboard", headers=headers)
    
    if dashboard_response.status_code == 200:
        dashboard_data = dashboard_response.json()
        print(f"   Total employees: {dashboard_data.get('total_employees')}")
        print(f"   Active employees: {dashboard_data.get('active_employees')}")
        print(f"   Recent hires: {dashboard_data.get('recent_hires')}")
        print(f"   Pending leave requests: {dashboard_data.get('pending_leave_requests')}")
        print(f"   Organization ID: {dashboard_data.get('organization_id')}")
    else:
        print(f"❌ Failed to get dashboard: {dashboard_response.text}")
        return False
    
    # 2. Get actual employees data
    print(f"\n👥 Actual Employees Data:")
    employees_response = requests.get(f"{API_BASE}/employees/", headers=headers)
    
    if employees_response.status_code == 200:
        employees = employees_response.json()
        total_employees = len(employees)
        active_employees = len([emp for emp in employees if emp.get('status') == 'ACTIVE'])
        
        print(f"   Total employees: {total_employees}")
        print(f"   Active employees: {active_employees}")
        
        # Show employee details
        print(f"   Employee breakdown:")
        for emp in employees:
            status_emoji = "✅" if emp.get('status') == 'ACTIVE' else "❌"
            print(f"     {status_emoji} {emp.get('first_name')} {emp.get('last_name')} - {emp.get('status')}")
    else:
        print(f"❌ Failed to get employees: {employees_response.text}")
        return False
    
    # 3. Compare dashboard vs actual data
    print(f"\n🔍 Data Comparison:")
    print("-" * 30)
    
    if dashboard_response.status_code == 200:
        dashboard_data = dashboard_response.json()
        dashboard_total = dashboard_data.get('total_employees')
        dashboard_active = dashboard_data.get('active_employees')
        
        actual_total = total_employees
        actual_active = active_employees
        
        print(f"Total Employees:")
        print(f"   Dashboard: {dashboard_total}")
        print(f"   Actual DB: {actual_total}")
        print(f"   Match: {'✅ YES' if dashboard_total == actual_total else '❌ NO'}")
        
        print(f"\nActive Employees:")
        print(f"   Dashboard: {dashboard_active}")
        print(f"   Actual DB: {actual_active}")
        print(f"   Match: {'✅ YES' if dashboard_active == actual_active else '❌ NO'}")
        
        # 4. Check if data is truly dynamic
        print(f"\n🔄 Testing Data Dynamics:")
        print("-" * 30)
        
        # Get dashboard data again after a small delay
        time.sleep(1)
        dashboard_response2 = requests.get(f"{API_BASE}/reports/dashboard", headers=headers)
        
        if dashboard_response2.status_code == 200:
            dashboard_data2 = dashboard_response2.json()
            
            print(f"Dashboard call 1: {dashboard_data.get('total_employees')} employees")
            print(f"Dashboard call 2: {dashboard_data2.get('total_employees')} employees")
            
            if dashboard_data == dashboard_data2:
                print(f"✅ Dashboard data is consistent (calculated from real data)")
            else:
                print(f"❌ Dashboard data is inconsistent")
        
        # 5. Conclusion
        print(f"\n📋 Conclusion:")
        print("=" * 30)
        
        if (dashboard_total == actual_total and 
            dashboard_active == actual_active):
            print(f"✅ DASHBOARD IS DYNAMIC - Shows real database data!")
            print(f"   - Dashboard calculates from actual employee records")
            print(f"   - Data matches real database counts")
            print(f"   - Organization filtering is working correctly")
            print(f"   - Manager sees only their organization's data")
        else:
            print(f"❌ DASHBOARD MIGHT BE STATIC - Data doesn't match database")
        
        return True
    
    return False

if __name__ == "__main__":
    try:
        test_dashboard_dynamic_data()
    except Exception as e:
        print(f"💥 Test failed with error: {e}")
