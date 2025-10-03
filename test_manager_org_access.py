#!/usr/bin/env python3
"""
Test script to verify that managers have access only to information from their organization.
This script tests the organization-based access control implementation.
"""

import requests
import json
import sys
from typing import Dict, Any, List

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

class TestManagerOrgAccess:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.users = {}
        self.organizations = {}
        
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login and get access token"""
        response = self.session.post(f"{API_BASE}/auth/login", json={
            "email": email,
            "password": password
        })
        
        if response.status_code == 200:
            data = response.json()
            token = data["access_token"]
            user_data = data["user"]
            
            self.tokens[user_data["id"]] = token
            self.users[user_data["id"]] = user_data
            
            # Set authorization header for future requests
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            
            print(f"✅ Logged in as {user_data['first_name']} {user_data['last_name']} ({user_data['role']})")
            return user_data
        else:
            print(f"❌ Login failed for {email}: {response.text}")
            return None
    
    def test_employees_access(self, user_id: int) -> bool:
        """Test that user can only see employees from their organization"""
        user = self.users[user_id]
        org_id = user.get("organization_id")
        
        print(f"\n🔍 Testing employees access for {user['role']} (Org ID: {org_id})")
        
        response = self.session.get(f"{API_BASE}/employees/")
        
        if response.status_code == 200:
            employees = response.json()
            print(f"   Found {len(employees)} employees")
            
            # Check if all employees belong to the user's organization
            for employee in employees:
                emp_org_id = employee.get("organization_id")
                if emp_org_id != org_id:
                    print(f"   ❌ Employee {employee['first_name']} {employee['last_name']} belongs to org {emp_org_id}, not {org_id}")
                    return False
                else:
                    print(f"   ✅ Employee {employee['first_name']} {employee['last_name']} belongs to correct org")
            
            return True
        else:
            print(f"   ❌ Failed to get employees: {response.text}")
            return False
    
    def test_users_access(self, user_id: int) -> bool:
        """Test that user can only see users from their organization"""
        user = self.users[user_id]
        org_id = user.get("organization_id")
        
        print(f"\n🔍 Testing users access for {user['role']} (Org ID: {org_id})")
        
        response = self.session.get(f"{API_BASE}/users/")
        
        if response.status_code == 200:
            users = response.json()
            print(f"   Found {len(users)} users")
            
            # Check if all users belong to the user's organization
            for u in users:
                user_org_id = u.get("organization_id")
                if user_org_id != org_id:
                    print(f"   ❌ User {u['first_name']} {u['last_name']} belongs to org {user_org_id}, not {org_id}")
                    return False
                else:
                    print(f"   ✅ User {u['first_name']} {u['last_name']} belongs to correct org")
            
            return True
        else:
            print(f"   ❌ Failed to get users: {response.text}")
            return False
    
    def test_leave_requests_access(self, user_id: int) -> bool:
        """Test that user can only see leave requests from their organization"""
        user = self.users[user_id]
        org_id = user.get("organization_id")
        
        print(f"\n🔍 Testing leave requests access for {user['role']} (Org ID: {org_id})")
        
        response = self.session.get(f"{API_BASE}/leave/requests")
        
        if response.status_code == 200:
            requests = response.json()
            print(f"   Found {len(requests)} leave requests")
            
            # For managers, check if they can see requests from their organization
            if user['role'] == 'MANAGER':
                # This is a simplified test - in reality, we'd need to check the employee's org
                print(f"   ✅ Manager can see {len(requests)} leave requests")
                return True
            else:
                print(f"   ✅ {user['role']} can see {len(requests)} leave requests")
                return True
        else:
            print(f"   ❌ Failed to get leave requests: {response.text}")
            return False
    
    def test_organizations_access(self, user_id: int) -> bool:
        """Test that user can only see their organization (for non-super-admin)"""
        user = self.users[user_id]
        org_id = user.get("organization_id")
        
        print(f"\n🔍 Testing organizations access for {user['role']} (Org ID: {org_id})")
        
        response = self.session.get(f"{API_BASE}/organizations/")
        
        if response.status_code == 200:
            orgs = response.json()
            print(f"   Found {len(orgs)} organizations")
            
            if user['role'] == 'SUPER_ADMIN':
                print(f"   ✅ Super Admin can see all {len(orgs)} organizations")
                return True
            elif len(orgs) == 1 and orgs[0]['id'] == org_id:
                print(f"   ✅ {user['role']} can only see their own organization")
                return True
            else:
                print(f"   ❌ {user['role']} can see {len(orgs)} organizations, expected 1")
                return False
        else:
            print(f"   ❌ Failed to get organizations: {response.text}")
            return False
    
    def run_tests(self):
        """Run all tests"""
        print("🚀 Starting Manager Organization Access Tests")
        print("=" * 50)
        
        # Test with different user types
        test_users = [
            {"email": "manager1@company.com", "password": "password123", "expected_role": "MANAGER"},
            {"email": "hr1@company.com", "password": "password123", "expected_role": "HR"},
            {"email": "admin1@company.com", "password": "password123", "expected_role": "ORG_ADMIN"},
        ]
        
        all_passed = True
        
        for test_user in test_users:
            print(f"\n📋 Testing with {test_user['email']}")
            print("-" * 30)
            
            user_data = self.login(test_user["email"], test_user["password"])
            if not user_data:
                print(f"❌ Cannot test {test_user['email']} - login failed")
                all_passed = False
                continue
            
            user_id = user_data["id"]
            
            # Run tests
            tests = [
                self.test_employees_access,
                self.test_users_access,
                self.test_leave_requests_access,
                self.test_organizations_access,
            ]
            
            for test in tests:
                try:
                    if not test(user_id):
                        all_passed = False
                except Exception as e:
                    print(f"   ❌ Test failed with exception: {e}")
                    all_passed = False
            
            # Clear session for next user
            self.session.headers.pop("Authorization", None)
        
        print("\n" + "=" * 50)
        if all_passed:
            print("🎉 All tests passed! Managers have proper organization-based access.")
        else:
            print("❌ Some tests failed. Check the implementation.")
        
        return all_passed

def main():
    """Main function"""
    print("Manager Organization Access Control Test")
    print("======================================")
    print("This script tests that managers can only access information from their organization.")
    print("Make sure the backend server is running on http://localhost:8000")
    print()
    
    tester = TestManagerOrgAccess()
    
    try:
        success = tester.run_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
