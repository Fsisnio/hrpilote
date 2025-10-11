#!/usr/bin/env python3
"""
Quick fix for Render production passwords
Run this directly on Render shell or as a job
"""

import sys
import os

# Setup paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.security import get_password_hash
from app.models.user import User
import traceback

def fix_passwords():
    """Fix production passwords on Render"""
    print("\n" + "="*60)
    print("RENDER PASSWORD FIX - Quick Reset")
    print("="*60 + "\n")
    
    # Get database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment!")
        return False
    
    print(f"✅ Database URL found")
    
    # Fix postgres:// to postgresql:// for SQLAlchemy
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # Create engine and session
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Admin emails to reset
        admin_emails = [
            'superadmin@hrpilot.com',
            'admin@hrpilot.com',
            'test@hrpilot.com',
            'orgadmin@hrpilot.com',
            'hr@hrpilot.com',
            'hr.manager@hrpilot.com',
            'manager@hrpilot.com',
            'director@hrpilot.com',
            'payroll@hrpilot.com',
            'employee@hrpilot.com'
        ]
        
        default_password = "Password123!"
        print(f"Resetting passwords to: {default_password}\n")
        
        updated = 0
        for email in admin_emails:
            user = db.query(User).filter(User.email == email).first()
            if user:
                try:
                    new_hash = get_password_hash(default_password)
                    user.hashed_password = new_hash
                    user.failed_login_attempts = 0
                    user.locked_until = None
                    print(f"✅ Reset & Unlocked: {email}")
                    updated += 1
                except Exception as e:
                    print(f"❌ Failed: {email} - {e}")
        
        if updated > 0:
            db.commit()
            print(f"\n✅ Successfully reset {updated} admin passwords!")
            print("\n" + "="*60)
            print("Login credentials for all admin accounts:")
            print(f"   Password: {default_password}")
            print("="*60)
            print("\nYou can now login to production!")
            print("   Email: superadmin@hrpilot.com")
            print(f"   Password: {default_password}")
            print("\n⚠️  Change these default passwords after login!\n")
            return True
        else:
            print("\n❌ No accounts were updated")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()
        engine.dispose()

if __name__ == "__main__":
    try:
        success = fix_passwords()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)

