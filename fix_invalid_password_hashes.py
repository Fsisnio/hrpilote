#!/usr/bin/env python3
"""
Fix all users with invalid password hashes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.core.security import is_valid_password_hash, fix_invalid_password_hash
from app.models.user import User

def fix_all_invalid_hashes():
    """Find and fix all users with invalid password hashes"""
    print("🔧 Fixing Invalid Password Hashes")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        # Find all users with invalid hashes
        all_users = db.query(User).all()
        invalid_users = []
        
        for user in all_users:
            if not is_valid_password_hash(user.hashed_password):
                invalid_users.append(user)
                print(f"❌ Invalid hash found: {user.email}")
                print(f"   Hash: {user.hashed_password[:30]}...")
        
        if not invalid_users:
            print("✅ All users have valid password hashes!")
            return True
        
        print(f"\n📊 Found {len(invalid_users)} users with invalid hashes")
        
        # Fix each user
        fixed_count = 0
        for user in invalid_users:
            print(f"\n🔧 Fixing user: {user.email}")
            
            # Generate a temporary password
            temp_password = f"TempPassword{user.id}!"
            
            if fix_invalid_password_hash(user.id, temp_password, db):
                print(f"✅ Fixed user {user.email} with temporary password: {temp_password}")
                fixed_count += 1
            else:
                print(f"❌ Failed to fix user {user.email}")
        
        print(f"\n🎉 Fixed {fixed_count}/{len(invalid_users)} users")
        print("\n⚠️  IMPORTANT: Users with fixed hashes need to reset their passwords!")
        print("   They can use the 'Forgot Password' feature or contact an administrator.")
        
        return fixed_count == len(invalid_users)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

def check_hash_status():
    """Check the status of all password hashes"""
    print("🔍 Checking Password Hash Status")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        all_users = db.query(User).all()
        valid_count = 0
        invalid_count = 0
        
        for user in all_users:
            if is_valid_password_hash(user.hashed_password):
                valid_count += 1
            else:
                invalid_count += 1
                print(f"❌ {user.email}: {user.hashed_password[:30]}...")
        
        print(f"\n📊 Summary:")
        print(f"   Valid hashes: {valid_count}")
        print(f"   Invalid hashes: {invalid_count}")
        print(f"   Total users: {len(all_users)}")
        
        return invalid_count == 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Password Hash Maintenance Tool")
    print("=" * 60)
    
    # Check current status
    all_valid = check_hash_status()
    
    if not all_valid:
        print("\n" + "=" * 60)
        response = input("Fix invalid hashes? (y/N): ").strip().lower()
        
        if response == 'y':
            success = fix_all_invalid_hashes()
            if success:
                print("\n🎉 All invalid hashes have been fixed!")
            else:
                print("\n💥 Some hashes could not be fixed!")
        else:
            print("Skipped fixing hashes.")
    else:
        print("\n🎉 All password hashes are valid!")
    
    print("\n" + "=" * 60)
    print("✅ Password hash check completed!")
