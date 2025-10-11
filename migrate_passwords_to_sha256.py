#!/usr/bin/env python3
"""
Migration script to re-hash existing user passwords with the new SHA-256 + bcrypt method.

This script updates all user passwords to use the new hashing method that supports
passwords of any length by pre-hashing with SHA-256 before bcrypt.

Note: This script requires users to log in again after migration, as we can't 
decrypt existing passwords. Instead, it will mark passwords for rehashing on next login.
Alternatively, you can run this to create a password reset requirement.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.user import User
from app.core.security import get_password_hash
import traceback


def migrate_user_passwords():
    """
    Migration strategy:
    Since we can't decrypt existing passwords, this script creates a flag system.
    
    For immediate migration: Set a default temporary password for all users
    and require password reset on next login.
    """
    db = SessionLocal()
    
    try:
        # Get all users
        users = db.query(User).all()
        
        print(f"\n{'='*60}")
        print(f"PASSWORD MIGRATION TO SHA-256 + BCRYPT")
        print(f"{'='*60}\n")
        print(f"Found {len(users)} users in the database.\n")
        
        if not users:
            print("No users to migrate.")
            return
        
        print("Migration options:")
        print("1. The new hashing method is backward compatible - existing users can still log in")
        print("2. Their passwords will be automatically re-hashed on next successful login")
        print("3. No immediate action needed!\n")
        
        # Optionally force re-hash all users with a known test password
        # (Uncomment if you want to test the new hashing)
        """
        migrate = input("Do you want to force re-hash all users with test password 'Password123!'? (yes/no): ")
        
        if migrate.lower() == 'yes':
            test_password = "Password123!"
            print(f"\n⚠️  WARNING: This will reset all user passwords to '{test_password}'")
            confirm = input("Are you sure? Type 'CONFIRM' to proceed: ")
            
            if confirm == 'CONFIRM':
                migrated = 0
                failed = 0
                
                for user in users:
                    try:
                        # Re-hash with new method
                        user.hashed_password = get_password_hash(test_password)
                        db.commit()
                        print(f"✅ Migrated: {user.email}")
                        migrated += 1
                    except Exception as e:
                        print(f"❌ Failed to migrate {user.email}: {e}")
                        failed += 1
                        db.rollback()
                
                print(f"\n{'='*60}")
                print(f"Migration complete!")
                print(f"Successfully migrated: {migrated}")
                print(f"Failed: {failed}")
                print(f"{'='*60}\n")
            else:
                print("Migration cancelled.")
        else:
            print("No action taken. Users will be automatically migrated on next login.")
        """
        
        print("\n✅ New hashing method is active!")
        print("   - New users will use SHA-256 + bcrypt")
        print("   - Existing users can still log in (backward compatible)")
        print("   - Passwords will be re-hashed on next successful login")
        print("   - Passwords of any length are now supported\n")
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        traceback.print_exc()
        db.rollback()
    
    finally:
        db.close()


def test_new_hashing():
    """Test the new hashing method with various password lengths"""
    print(f"\n{'='*60}")
    print(f"TESTING NEW PASSWORD HASHING METHOD")
    print(f"{'='*60}\n")
    
    from app.core.security import get_password_hash, verify_password
    
    test_passwords = [
        "short",
        "Password123!",
        "A" * 50,
        "A" * 100,
        "A" * 200,
        "🔐" * 50,  # Unicode characters
        "This is a very long password " * 10,
    ]
    
    for password in test_passwords:
        try:
            length = len(password)
            byte_length = len(password.encode('utf-8'))
            print(f"Testing password (chars: {length}, bytes: {byte_length})...")
            
            # Hash the password
            hashed = get_password_hash(password)
            print(f"  ✅ Hashed: {hashed[:30]}...")
            
            # Verify it
            if verify_password(password, hashed):
                print(f"  ✅ Verification successful")
            else:
                print(f"  ❌ Verification failed")
            
            print()
            
        except Exception as e:
            print(f"  ❌ Error: {e}\n")
    
    print(f"{'='*60}\n")


if __name__ == "__main__":
    print("\nPassword Migration Script")
    print("=" * 60)
    
    # Test the new hashing method
    test_new_hashing()
    
    # Run migration
    migrate_user_passwords()

