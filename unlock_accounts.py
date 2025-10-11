#!/usr/bin/env python3
"""
Quick unlock script for locked accounts on Render
Run this if accounts are locked due to failed login attempts
"""

import sys
import os

# Setup paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
import traceback

def unlock_accounts():
    """Unlock all locked accounts"""
    print("\n" + "="*60)
    print("UNLOCK LOCKED ACCOUNTS")
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
        # Find all users
        users = db.query(User).all()
        
        unlocked = 0
        for user in users:
            if user.failed_login_attempts > 0 or user.locked_until:
                user.failed_login_attempts = 0
                user.locked_until = None
                print(f"✅ Unlocked: {user.email}")
                unlocked += 1
        
        if unlocked > 0:
            db.commit()
            print(f"\n✅ Successfully unlocked {unlocked} accounts!")
            print("\nYou can now try logging in again.")
            return True
        else:
            print("\n✅ No locked accounts found.")
            return True
            
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
        success = unlock_accounts()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)
