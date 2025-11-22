#!/usr/bin/env python3
"""
Production Configuration Checker
Verifies that all required environment variables and configurations are set correctly
"""

import os
import sys
import requests
from typing import Dict, List, Tuple

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.ENDC}\n")

def print_success(text: str):
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def print_error(text: str):
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")

def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")

def check_backend_health(backend_url: str) -> bool:
    """Check if backend is healthy"""
    try:
        response = requests.get(f"{backend_url.rstrip('/api/v1')}/health", timeout=10)
        if response.status_code == 200:
            print_success(f"Backend health check passed: {backend_url}")
            return True
        else:
            print_error(f"Backend health check failed with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"Cannot reach backend: {e}")
        return False

def check_cors(backend_url: str) -> bool:
    """Check CORS configuration"""
    try:
        response = requests.get(f"{backend_url.rstrip('/api/v1')}/cors-test", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_success("CORS endpoint accessible")
            print(f"  Allowed origins: {data.get('allowed_origins', [])}")
            return True
        else:
            print_error(f"CORS check failed with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"Cannot check CORS: {e}")
        return False

def check_login(backend_url: str, email: str, password: str) -> bool:
    """Test login endpoint"""
    try:
        response = requests.post(
            f"{backend_url}/auth/login",
            json={"email": email, "password": password},
            timeout=10
        )
        if response.status_code == 200:
            print_success(f"Login successful for {email}")
            data = response.json()
            if 'access_token' in data:
                print_success("  Access token received")
            return True
        else:
            print_error(f"Login failed with status {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
    except requests.exceptions.RequestException as e:
        print_error(f"Cannot test login: {e}")
        return False

def main():
    print_header("HR PILOT PRODUCTION CONFIGURATION CHECKER")
    
    # Configuration
    PRODUCTION_BACKEND = "https://hrpiloteback.onrender.com/api/v1"
    PRODUCTION_FRONTEND = "https://hrpilotefront.onrender.com"
    ADMIN_EMAIL = "fala@gmail.com"
    ADMIN_PASSWORD = "Jesus1993@"
    
    print(f"Backend URL: {PRODUCTION_BACKEND}")
    print(f"Frontend URL: {PRODUCTION_FRONTEND}")
    print()
    
    all_passed = True
    
    # Test 1: Backend Health
    print_header("TEST 1: Backend Health Check")
    if not check_backend_health(PRODUCTION_BACKEND):
        all_passed = False
        print_error("Backend is not responding. Check Render deployment logs.")
    
    # Test 2: CORS Configuration
    print_header("TEST 2: CORS Configuration")
    if not check_cors(PRODUCTION_BACKEND):
        all_passed = False
        print_warning("CORS endpoint not available or misconfigured")
    
    # Test 3: Login Test
    print_header("TEST 3: Login Endpoint")
    if not check_login(PRODUCTION_BACKEND, ADMIN_EMAIL, ADMIN_PASSWORD):
        all_passed = False
        print_error("Login test failed. Check credentials and database.")
    
    # Test 4: Frontend Configuration Check
    print_header("TEST 4: Frontend Configuration Checklist")
    print("\n⚠️  Manual checks required:\n")
    
    checks = [
        "✓ Is REACT_APP_API_BASE_URL set on Render frontend service?",
        f"✓ Does it point to: {PRODUCTION_BACKEND}?",
        "✓ Was frontend rebuilt after setting environment variables?",
        "✓ Are browser DevTools showing requests to localhost (BAD)?",
        "✓ Are browser DevTools showing CORS errors?",
    ]
    
    for check in checks:
        print(f"  [ ] {check}")
    
    # Summary
    print_header("SUMMARY")
    
    if all_passed:
        print_success("All automated tests passed! ✓")
        print("\nIf login still fails in browser:")
        print("  1. Check browser console for errors")
        print("  2. Verify REACT_APP_API_BASE_URL is set on Render")
        print("  3. Rebuild frontend after setting environment variables")
        print("  4. Clear browser cache and try again")
    else:
        print_error("Some tests failed! ✗")
        print("\nNext steps:")
        print("  1. Fix the failing tests above")
        print("  2. Check Render deployment logs for errors")
        print("  3. Verify all environment variables are set")
    
    print()
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())


