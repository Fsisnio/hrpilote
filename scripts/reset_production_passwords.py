#!/usr/bin/env python3
"""
Reset admin passwords in production with the new SHA-256 + bcrypt method.
Run this script on Render or any production environment.

This ensures all admin accounts use the new password hashing method.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.core.security import get_password_hash, verify_password
from app.models.user import User, UserRole

def reset_production_passwords():
    """Reset all admin passwords to ensure they use the new hashing method"""
    print("\n" + "="*70)
    print("PRODUCTION PASSWORD RESET - SHA-256 + bcrypt Migration")
    print("="*70 + "\n")
    
    db = SessionLocal()
    
    try:
        # Define admin accounts to reset
        admin_accounts = [
            {"email": "superadmin@hrpilot.com", "password": "Password123!"},
            {"email": "admin@hrpilot.com", "password": "Password123!"},
            {"email": "test@hrpilot.com", "password": "Password123!"},
            {"email": "orgadmin@hrpilot.com", "password": "Password123!"},
            {"email": "hr@hrpilot.com", "password": "Password123!"},
            {"email": "hr.manager@hrpilot.com", "password": "Password123!"},
            {"email": "manager@hrpilot.com", "password": "Password123!"},
            {"email": "director@hrpilot.com", "password": "Password123!"},
            {"email": "payroll@hrpilot.com", "password": "Password123!"},
        ]
        
        updated_count = 0
        not_found_count = 0
        already_working_count = 0
        
        print("Checking and updating admin accounts...\n")
        
        for account in admin_accounts:
            email = account["email"]
            password = account["password"]
            
            # Find user
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                print(f"⚠️  {email:<35} - Not found")
                not_found_count += 1
                continue
            
            # Check if password already works
            try:
                if verify_password(password, user.hashed_password):
                    print(f"✅ {email:<35} - Already working (skipping)")
                    already_working_count += 1
                    continue
            except Exception as e:
                print(f"⚠️  {email:<35} - Verification error, resetting...")
            
            # Reset password with new hashing method
            try:
                new_hash = get_password_hash(password)
                user.hashed_password = new_hash
                user.failed_login_attempts = 0
                user.locked_until = None
                
                # Verify new hash works
                if verify_password(password, new_hash):
                    print(f"✅ {email:<35} - Password reset successfully")
                    updated_count += 1
                else:
                    print(f"❌ {email:<35} - Reset failed (verification error)")
                    
            except Exception as e:
                print(f"❌ {email:<35} - Reset failed: {e}")
        
        # Commit all changes
        if updated_count > 0:
            db.commit()
            print(f"\n✅ Database changes committed")
        
        # Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print(f"✅ Already working:  {already_working_count}")
        print(f"✅ Updated:          {updated_count}")
        print(f"⚠️  Not found:        {not_found_count}")
        print(f"📊 Total processed:  {len(admin_accounts)}")
        
        if updated_count > 0 or already_working_count > 0:
            print("\n" + "="*70)
            print("SUCCESS! Admin passwords are now using SHA-256 + bcrypt")
            print("="*70)
            print("\nAll admin accounts use password: Password123!")
            print("\n⚠️  IMPORTANT: Change these default passwords after login!")
            print("="*70 + "\n")
            return True
        else:
            print("\n⚠️  No accounts were updated. Please check the database.")
            return False
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
        
    finally:
        db.close()


def verify_all_admin_logins():
    """Verify all admin accounts can login with default password"""
    print("\n" + "="*70)
    print("VERIFICATION - Testing all admin logins")
    print("="*70 + "\n")
    
    db = SessionLocal()
    
    admin_emails = [
        "superadmin@hrpilot.com",
        "admin@hrpilot.com",
        "orgadmin@hrpilot.com",
        "hr@hrpilot.com",
        "manager@hrpilot.com",
    ]
    
    default_password = "Password123!"
    working = 0
    not_working = 0
    
    try:
        for email in admin_emails:
            user = db.query(User).filter(User.email == email).first()
            if user:
                if verify_password(default_password, user.hashed_password):
                    print(f"✅ {email:<35} - Login working")
                    working += 1
                else:
                    print(f"❌ {email:<35} - Login NOT working")
                    not_working += 1
            else:
                print(f"⚠️  {email:<35} - User not found")
        
        print(f"\n✅ Working: {working} | ❌ Not working: {not_working}")
        print("="*70 + "\n")
        
        return not_working == 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    print("\n🔐 Production Password Reset Tool")
    print("This will update admin passwords to use the new SHA-256 + bcrypt method\n")
    
    # Reset passwords
    success = reset_production_passwords()
    
    if success:
        print("\n" + "="*70)
        print("Verifying all admin accounts...")
        print("="*70)
        verify_all_admin_logins()
        
        print("\n✅ Production passwords updated successfully!")
        print("\nYou can now login with:")
        print("   Email: superadmin@hrpilot.com")
        print("   Password: Password123!\n")
        sys.exit(0)
    else:
        print("\n❌ Production password reset failed!")
        sys.exit(1)

