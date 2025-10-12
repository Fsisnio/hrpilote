#!/usr/bin/env python3
"""
Production Admin Setup Script
This script creates the production super admin user if it doesn't exist.
Run this after deploying to production to ensure admin access.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.user import User, UserRole, UserStatus
from app.core.security import get_password_hash
from datetime import datetime

def setup_production_admin():
    """Create production super admin user"""
    print("\n" + "="*70)
    print("PRODUCTION ADMIN SETUP")
    print("="*70)
    
    db = SessionLocal()
    
    try:
        # Production admin credentials
        admin_email = "fala@gmail.com"
        admin_password = "Jesus1993."
        
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.email == admin_email).first()
        
        if existing_admin:
            print(f"✅ Production admin already exists:")
            print(f"   - Email: {existing_admin.email}")
            print(f"   - Role: {existing_admin.role}")
            print(f"   - Status: {existing_admin.status}")
            
            # Update password to ensure it's correct
            existing_admin.hashed_password = get_password_hash(admin_password)
            existing_admin.updated_at = datetime.utcnow()
            db.commit()
            print(f"✅ Password updated successfully")
            
        else:
            print(f"🔧 Creating production super admin...")
            
            # Create production super admin
            admin_user = User(
                email=admin_email,
                username="fala",
                first_name="Fala",
                last_name="Admin",
                hashed_password=get_password_hash(admin_password),
                role=UserRole.SUPER_ADMIN,
                status=UserStatus.ACTIVE,
                organization_id=None,  # Super admin can access all organizations
                department_id=None,
                manager_id=None,
                is_email_verified=True,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                last_login=None,
                failed_login_attempts=0,
                locked_until=None
            )
            
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            
            print(f"✅ Production super admin created successfully:")
            print(f"   - ID: {admin_user.id}")
            print(f"   - Email: {admin_user.email}")
            print(f"   - Role: {admin_user.role}")
            print(f"   - Status: {admin_user.status}")
            print(f"   - Organization: All (Super Admin)")
        
        print("\n" + "="*70)
        print("PRODUCTION ADMIN CREDENTIALS")
        print("="*70)
        print(f"Email: {admin_email}")
        print(f"Password: {admin_password}")
        print(f"Role: SUPER_ADMIN (Full System Access)")
        print("="*70)
        print("\n✅ Production admin setup completed successfully!")
        print("\n⚠️  IMPORTANT: Change the password after first login!")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error setting up production admin: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()

def test_admin_login():
    """Test if admin can login"""
    print("\n🔍 Testing admin login...")
    
    try:
        import requests
        
        # Try to login (this will work if backend is running)
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            json={
                "email": "fala@gmail.com",
                "password": "Jesus1993."
            },
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Admin login test successful!")
            user_data = response.json().get('user', {})
            print(f"   - User ID: {user_data.get('id')}")
            print(f"   - Role: {user_data.get('role')}")
            print(f"   - Status: {user_data.get('status')}")
        else:
            print(f"⚠️  Admin login test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"⚠️  Could not test login (backend may not be running): {str(e)}")

if __name__ == "__main__":
    print("\n🔐 Production Admin Setup Tool")
    print("This will create the production super admin user\n")
    
    # Setup admin
    success = setup_production_admin()
    
    if success:
        # Test login if possible
        test_admin_login()
        
        print("\n✅ Production admin setup completed!")
        print("\nYou can now:")
        print("1. Deploy this to production")
        print("2. Run this script on production: python scripts/setup_production_admin.py")
        print("3. Login with: fala@gmail.com / Jesus1993.")
        
        sys.exit(0)
    else:
        print("\n❌ Production admin setup failed!")
        sys.exit(1)
