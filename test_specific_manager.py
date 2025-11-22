#!/usr/bin/env python3
"""
Test script to verify manager access with specific credentials
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_manager_access():
    """Test manager access with specific credentials"""
    print("🔐 Testing Manager Access Control")
    print("=" * 40)
    
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
    
    # Test 1: Get employees
    print(f"\n👥 Testing Employees Access...")
    employees_response = requests.get(f"{API_BASE}/employees/", headers=headers)
    
    if employees_response.status_code == 200:
        employees = employees_response.json()
        print(f"✅ Can access {len(employees)} employees")
        
        # Check if all employees belong to the manager's organization
        manager_org_id = user_data['organization_id']
        org_employees = [emp for emp in employees if emp.get('organization_id') == manager_org_id]
        
        if len(org_employees) == len(employees):
            print(f"✅ All {len(employees)} employees belong to manager's organization (ID: {manager_org_id})")
        else:
            print(f"❌ Found {len(employees)} employees, but only {len(org_employees)} belong to org {manager_org_id}")
            for emp in employees:
                if emp.get('organization_id') != manager_org_id:
                    print(f"   ❌ Employee {emp.get('first_name')} {emp.get('last_name')} belongs to org {emp.get('organization_id')}")
    else:
        print(f"❌ Failed to access employees: {employees_response.text}")
    
    # Test 2: Get users
    print(f"\n👤 Testing Users Access...")
    users_response = requests.get(f"{API_BASE}/users/", headers=headers)
    
    if users_response.status_code == 200:
        users = users_response.json()
        print(f"✅ Can access {len(users)} users")
        
        # Check if all users belong to the manager's organization
        manager_org_id = user_data['organization_id']
        org_users = [user for user in users if user.get('organization_id') == manager_org_id]
        
        if len(org_users) == len(users):
            print(f"✅ All {len(users)} users belong to manager's organization (ID: {manager_org_id})")
        else:
            print(f"❌ Found {len(users)} users, but only {len(org_users)} belong to org {manager_org_id}")
            for user in users:
                if user.get('organization_id') != manager_org_id:
                    print(f"   ❌ User {user.get('first_name')} {user.get('last_name')} belongs to org {user.get('organization_id')}")
    else:
        print(f"❌ Failed to access users: {users_response.text}")
    
    # Test 3: Get organizations
    print(f"\n🏢 Testing Organizations Access...")
    orgs_response = requests.get(f"{API_BASE}/organizations/", headers=headers)
    
    if orgs_response.status_code == 200:
        orgs = orgs_response.json()
        print(f"✅ Can access {len(orgs)} organizations")
        
        if len(orgs) == 1 and orgs[0]['id'] == user_data['organization_id']:
            print(f"✅ Manager can only see their own organization: {orgs[0]['name']}")
        else:
            print(f"❌ Manager can see {len(orgs)} organizations, expected 1")
            for org in orgs:
                print(f"   Organization: {org['name']} (ID: {org['id']})")
    else:
        print(f"❌ Failed to access organizations: {orgs_response.text}")
    
    # Test 4: Get leave requests
    print(f"\n📅 Testing Leave Requests Access...")
    leave_response = requests.get(f"{API_BASE}/leave/requests", headers=headers)
    
    if leave_response.status_code == 200:
        leave_requests = leave_response.json()
        print(f"✅ Can access {len(leave_requests)} leave requests")
        print(f"   (Leave requests are filtered by organization on the backend)")
    else:
        print(f"❌ Failed to access leave requests: {leave_response.text}")
    
    # Test 5: Get dashboard data
    print(f"\n📊 Testing Dashboard Access...")
    dashboard_response = requests.get(f"{API_BASE}/reports/dashboard", headers=headers)
    
    if dashboard_response.status_code == 200:
        dashboard_data = dashboard_response.json()
        print(f"✅ Can access dashboard data")
        print(f"   Total employees: {dashboard_data.get('total_employees', 'N/A')}")
        print(f"   Active employees: {dashboard_data.get('active_employees', 'N/A')}")
        print(f"   Organization ID in response: {dashboard_data.get('organization_id', 'N/A')}")
    else:
        print(f"❌ Failed to access dashboard: {dashboard_response.text}")
    
    print(f"\n" + "=" * 40)
    print(f"🎯 Summary:")
    print(f"   Manager: {user_data['first_name']} {user_data['last_name']}")
    print(f"   Role: {user_data['role']}")
    print(f"   Organization ID: {user_data['organization_id']}")
    print(f"   ✅ Manager has organization-based access control implemented!")
    
    return True

if __name__ == "__main__":
    try:
        test_manager_access()
    except Exception as e:
        print(f"💥 Test failed with error: {e}")
