#!/usr/bin/env python3
"""
Test script to verify that org admins can access users from their organization.
This script tests the users API endpoints with org admin authentication.
"""

import requests
import json
import sys
from typing import Dict, Any, List, Optional

# Configuration
BASE_URL = "http://localhost:3003"  # Adjust port if needed
API_BASE = f"{BASE_URL}/api/v1"

class TestOrgAdminUsersAccess:
    def __init__(self):
        self.session = requests.Session()
        self.token: Optional[str] = None
        self.user_data: Optional[Dict[str, Any]] = None
        
    def login(self, email: str, password: str) -> bool:
        """Login and get access token"""
        print(f"🔐 Logging in as: {email}")
        
        response = self.session.post(f"{API_BASE}/auth/login", json={
            "email": email,
            "password": password
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.user_data = data["user"]
            
            # Set authorization header for future requests
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            
            print(f"✅ Logged in successfully!")
            print(f"   Name: {self.user_data['first_name']} {self.user_data['last_name']}")
            print(f"   Role: {self.user_data['role']}")
            print(f"   Organization ID: {self.user_data.get('organization_id', 'None')}")
            return True
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return False
    
    def test_get_users_list(self) -> bool:
        """Test that org admin can get list of users"""
        print("\n📋 Test 1: Getting list of users...")
        
        response = self.session.get(f"{API_BASE}/users/")
        
        if response.status_code == 200:
            users = response.json()
            print(f"   ✅ Successfully retrieved {len(users)} users")
            
            # Verify all users belong to the org admin's organization
            org_id = self.user_data.get("organization_id")
            if not org_id:
                print(f"   ⚠️  Warning: Org admin has no organization_id")
                return len(users) == 0
            
            print(f"   🔍 Verifying users belong to organization: {org_id}")
            
            for user in users:
                user_org_id = user.get("organization_id")
                if user_org_id != org_id:
                    print(f"   ❌ User {user.get('email')} belongs to org {user_org_id}, not {org_id}")
                    return False
                print(f"      ✅ {user.get('email')} ({user.get('role')}) - Correct org")
            
            return True
        else:
            print(f"   ❌ Failed to get users: {response.status_code} - {response.text}")
            return False
    
    def test_get_specific_user(self) -> bool:
        """Test that org admin can get a specific user from their organization"""
        print("\n👤 Test 2: Getting a specific user...")
        
        # First, get the list of users to find a user ID
        response = self.session.get(f"{API_BASE}/users/")
        
        if response.status_code != 200:
            print(f"   ❌ Cannot get users list: {response.status_code}")
            return False
        
        users = response.json()
        if len(users) == 0:
            print(f"   ⚠️  No users found in organization, skipping test")
            return True
        
        # Test with the first user
        test_user = users[0]
        user_id = test_user.get("id")
        
        print(f"   Testing with user ID: {user_id} ({test_user.get('email')})")
        
        response = self.session.get(f"{API_BASE}/users/{user_id}")
        
        if response.status_code == 200:
            user = response.json()
            print(f"   ✅ Successfully retrieved user: {user.get('email')}")
            
            # Verify the user belongs to the org admin's organization
            org_id = self.user_data.get("organization_id")
            user_org_id = user.get("organization_id")
            
            if user_org_id == org_id:
                print(f"   ✅ User belongs to correct organization")
                return True
            else:
                print(f"   ❌ User belongs to org {user_org_id}, not {org_id}")
                return False
        else:
            print(f"   ❌ Failed to get user: {response.status_code} - {response.text}")
            return False
    
    def test_get_organizations(self) -> bool:
        """Test that org admin can only see their own organization"""
        print("\n🏢 Test 3: Getting organizations...")
        
        response = self.session.get(f"{API_BASE}/organizations/")
        
        if response.status_code == 200:
            orgs = response.json()
            print(f"   ✅ Successfully retrieved {len(orgs)} organizations")
            
            org_id = self.user_data.get("organization_id")
            
            if self.user_data.get("role") == "SUPER_ADMIN":
                print(f"   ✅ Super Admin can see all {len(orgs)} organizations")
                return True
            elif len(orgs) == 1 and orgs[0].get("id") == org_id:
                print(f"   ✅ Org Admin can only see their own organization")
                print(f"      Organization: {orgs[0].get('name')} ({orgs[0].get('code')})")
                return True
            else:
                print(f"   ❌ Org Admin can see {len(orgs)} organizations, expected 1")
                if orgs:
                    print(f"      Found: {[org.get('name') for org in orgs]}")
                return False
        else:
            print(f"   ❌ Failed to get organizations: {response.status_code} - {response.text}")
            return False
    
    def test_users_filtering(self) -> bool:
        """Test that org admin can filter users by role and status"""
        print("\n🔍 Test 4: Filtering users by role and status...")
        
        org_id = self.user_data.get("organization_id")
        if not org_id:
            print(f"   ⚠️  Org admin has no organization_id, skipping filter test")
            return True
        
        # Test filtering by role
        print(f"   Testing role filter...")
        response = self.session.get(f"{API_BASE}/users/?role=EMPLOYEE")
        
        if response.status_code == 200:
            users = response.json()
            print(f"   ✅ Found {len(users)} employees")
            
            # Verify all are employees and belong to the org
            for user in users:
                if user.get("role") != "EMPLOYEE":
                    print(f"   ❌ User {user.get('email')} is not an EMPLOYEE")
                    return False
                if user.get("organization_id") != org_id:
                    print(f"   ❌ User {user.get('email')} doesn't belong to org {org_id}")
                    return False
        else:
            print(f"   ⚠️  Role filter test failed: {response.status_code}")
        
        # Test filtering by status
        print(f"   Testing status filter...")
        response = self.session.get(f"{API_BASE}/users/?status=ACTIVE")
        
        if response.status_code == 200:
            users = response.json()
            print(f"   ✅ Found {len(users)} active users")
            
            # Verify all are active and belong to the org
            for user in users:
                if user.get("status") != "ACTIVE":
                    print(f"   ❌ User {user.get('email')} is not ACTIVE")
                    return False
                if user.get("organization_id") != org_id:
                    print(f"   ❌ User {user.get('email')} doesn't belong to org {org_id}")
                    return False
        else:
            print(f"   ⚠️  Status filter test failed: {response.status_code}")
        
        return True
    
    def run_tests(self, email: str, password: str) -> bool:
        """Run all tests"""
        print("=" * 60)
        print("🧪 Testing Org Admin Users Access")
        print("=" * 60)
        
        # Login
        if not self.login(email, password):
            print("\n❌ Cannot proceed without login")
            return False
        
        # Verify we're testing with an org admin
        if self.user_data.get("role") != "ORG_ADMIN":
            print(f"\n⚠️  Warning: User role is {self.user_data.get('role')}, not ORG_ADMIN")
            print("   Continuing with tests anyway...")
        
        # Run tests
        tests = [
            ("Get Users List", self.test_get_users_list),
            ("Get Specific User", self.test_get_specific_user),
            ("Get Organizations", self.test_get_organizations),
            ("Filter Users", self.test_users_filtering),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"\n   ❌ Test '{test_name}' failed with exception: {e}")
                import traceback
                traceback.print_exc()
                results.append((test_name, False))
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)
        
        all_passed = True
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {status}: {test_name}")
            if not result:
                all_passed = False
        
        print("=" * 60)
        if all_passed:
            print("🎉 All tests passed! Org admin can access users correctly.")
        else:
            print("❌ Some tests failed. Check the implementation.")
        
        return all_passed

def check_server_health() -> bool:
    """Check if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def main():
    """Main function"""
    print("Org Admin Users Access Test")
    print("==========================")
    print("This script tests that org admins can access users from their organization.")
    print(f"Make sure the backend server is running on {BASE_URL}")
    print()
    
    # Check if server is running
    print("🔍 Checking if server is running...")
    if not check_server_health():
        print(f"❌ Server is not responding at {BASE_URL}")
        print("\n💡 Please start the backend server first:")
        print("   python start_backend.py")
        print("   or")
        print("   uvicorn app.main:app --host 0.0.0.0 --port 3016")
        print("\n💡 If the database is not initialized, run:")
        print(f"   curl -X POST {API_BASE}/init-database")
        sys.exit(1)
    print("✅ Server is running")
    print()
    
    # Default test credentials - adjust as needed
    # You can also pass credentials as command line arguments
    if len(sys.argv) >= 3:
        email = sys.argv[1]
        password = sys.argv[2]
    else:
        # Default test credentials
        email = "orgadmin@test.com"
        password = "Admin123!"
        print(f"Using default credentials: {email}")
        print("To use custom credentials: python test_org_admin_users_access.py <email> <password>")
        print()
        print("💡 Note: If login fails, you may need to initialize the database first:")
        print(f"   curl -X POST {API_BASE}/init-database")
        print()
    
    tester = TestOrgAdminUsersAccess()
    
    try:
        success = tester.run_tests(email, password)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

