#!/usr/bin/env python3
"""
Test script to verify that users can be created with the same email in different organizations.
"""

import sys
import os
from sqlalchemy.orm import Session
from app.core.database import get_db, SessionLocal
from app.models.user import User, UserRole, UserStatus
from app.models.organization import Organization
from app.core.security import get_password_hash

def test_multi_tenant_user_creation():
    """Test creating users with same email in different organizations"""
    
    db = SessionLocal()
    
    try:
        print("🧪 Testing multi-tenant user creation...")
        
        # Create two test organizations if they don't exist
        org1 = db.query(Organization).filter(Organization.name == "Test Email Org 1").first()
        if not org1:
            org1 = Organization(
                name="Test Email Org 1",
                code="EMAIL1",
                description="Test organization for email testing 1"
            )
            db.add(org1)
            db.commit()
            db.refresh(org1)
            print(f"✅ Created organization: {org1.name}")
        
        org2 = db.query(Organization).filter(Organization.name == "Test Email Org 2").first()
        if not org2:
            org2 = Organization(
                name="Test Email Org 2", 
                code="EMAIL2",
                description="Test organization for email testing 2"
            )
            db.add(org2)
            db.commit()
            db.refresh(org2)
            print(f"✅ Created organization: {org2.name}")
        
        # Clean up any existing test users
        db.query(User).filter(User.email == "test@example.com").delete()
        db.commit()
        
        # Test 1: Create user in organization 1
        print("\n📝 Test 1: Creating user test@example.com in organization 1...")
        user1 = User(
            email="test@example.com",
            username="testuser1",
            hashed_password=get_password_hash("password123"),
            first_name="Test",
            last_name="User1",
            role=UserRole.EMPLOYEE,
            status=UserStatus.ACTIVE,
            organization_id=org1.id,
            is_email_verified=True,
            is_active=True
        )
        db.add(user1)
        db.commit()
        db.refresh(user1)
        print(f"✅ Successfully created user {user1.email} in {org1.name}")
        
        # Test 2: Create user with same email in organization 2
        print("\n📝 Test 2: Creating user test@example.com in organization 2...")
        user2 = User(
            email="test@example.com",  # Same email
            username="testuser2",
            hashed_password=get_password_hash("password123"),
            first_name="Test",
            last_name="User2",
            role=UserRole.EMPLOYEE,
            status=UserStatus.ACTIVE,
            organization_id=org2.id,  # Different organization
            is_email_verified=True,
            is_active=True
        )
        db.add(user2)
        db.commit()
        db.refresh(user2)
        print(f"✅ Successfully created user {user2.email} in {org2.name}")
        
        # Test 3: Try to create duplicate email in same organization (should fail)
        print("\n📝 Test 3: Attempting to create duplicate test@example.com in organization 1 (should fail)...")
        try:
            user3 = User(
                email="test@example.com",  # Same email
                username="testuser3",
                hashed_password=get_password_hash("password123"),
                first_name="Duplicate",
                last_name="User",
                role=UserRole.EMPLOYEE,
                status=UserStatus.ACTIVE,
                organization_id=org1.id,  # Same organization
                is_email_verified=True,
                is_active=True
            )
            db.add(user3)
            db.commit()
            print("❌ ERROR: Duplicate email was allowed in same organization!")
            return False
        except Exception as e:
            print(f"✅ Correctly prevented duplicate email in same organization: {e}")
        
        # Verify the users exist
        print("\n🔍 Verifying users...")
        user1_check = db.query(User).filter(
            User.email == "test@example.com",
            User.organization_id == org1.id
        ).first()
        
        user2_check = db.query(User).filter(
            User.email == "test@example.com", 
            User.organization_id == org2.id
        ).first()
        
        if user1_check and user2_check:
            print(f"✅ User 1: {user1_check.email} in {org1.name}")
            print(f"✅ User 2: {user2_check.email} in {org2.name}")
            print("\n🎉 Multi-tenant user creation test PASSED!")
            return True
        else:
            print("❌ Users not found in database")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        db.close()

def cleanup_test_data():
    """Clean up test data"""
    db = SessionLocal()
    try:
        print("\n🧹 Cleaning up test data...")
        
        # Delete test users
        db.query(User).filter(User.email == "test@example.com").delete()
        
        # Delete test organizations
        db.query(Organization).filter(Organization.name.in_(["Test Email Org 1", "Test Email Org 2"])).delete()
        
        db.commit()
        print("✅ Test data cleaned up")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        cleanup_test_data()
    else:
        success = test_multi_tenant_user_creation()
        if success:
            print("\n✅ All tests passed! The multi-tenant user creation is working correctly.")
        else:
            print("\n❌ Tests failed! Please check the implementation.")
            sys.exit(1)
