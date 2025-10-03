#!/usr/bin/env python3
"""
Test script to verify that employees can be created with the same employee_id in different organizations.
"""

import sys
import os
from sqlalchemy.orm import Session
from app.core.database import get_db, SessionLocal
from app.models.employee import Employee
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.department import Department
from datetime import date

def test_multi_tenant_employee_creation():
    """Test creating employees with same employee_id in different organizations"""
    
    db = SessionLocal()
    
    try:
        print("🧪 Testing multi-tenant employee creation...")
        
        # Create two test organizations if they don't exist
        org1 = db.query(Organization).filter(Organization.name == "Test Org 1").first()
        if not org1:
            org1 = Organization(
                name="Test Org 1",
                code="TEST1",
                description="Test organization 1"
            )
            db.add(org1)
            db.commit()
            db.refresh(org1)
            print(f"✅ Created organization: {org1.name}")
        
        org2 = db.query(Organization).filter(Organization.name == "Test Org 2").first()
        if not org2:
            org2 = Organization(
                name="Test Org 2", 
                code="TEST2",
                description="Test organization 2"
            )
            db.add(org2)
            db.commit()
            db.refresh(org2)
            print(f"✅ Created organization: {org2.name}")
        
        # Create test users if they don't exist
        user1 = db.query(User).filter(User.email == "test1@example.com").first()
        if not user1:
            user1 = User(
                email="test1@example.com",
                username="testuser1",
                first_name="Test",
                last_name="User1",
                role=UserRole.EMPLOYEE,
                organization_id=org1.id,
                status="ACTIVE"
            )
            db.add(user1)
            db.commit()
            db.refresh(user1)
            print(f"✅ Created user: {user1.email}")
        
        user2 = db.query(User).filter(User.email == "test2@example.com").first()
        if not user2:
            user2 = User(
                email="test2@example.com",
                username="testuser2", 
                first_name="Test",
                last_name="User2",
                role=UserRole.EMPLOYEE,
                organization_id=org2.id,
                status="ACTIVE"
            )
            db.add(user2)
            db.commit()
            db.refresh(user2)
            print(f"✅ Created user: {user2.email}")
        
        # Clean up any existing test employees
        db.query(Employee).filter(Employee.employee_id == "EMP001").delete()
        db.commit()
        
        # Test 1: Create employee in organization 1
        print("\n📝 Test 1: Creating employee EMP001 in organization 1...")
        employee1 = Employee(
            employee_id="EMP001",
            user_id=user1.id,
            organization_id=org1.id,
            first_name="John",
            last_name="Doe",
            position="Developer",
            job_title="Software Engineer",
            hire_date=date.today(),
            status="ACTIVE"
        )
        db.add(employee1)
        db.commit()
        db.refresh(employee1)
        print(f"✅ Successfully created employee {employee1.employee_id} in {org1.name}")
        
        # Test 2: Create employee with same employee_id in organization 2
        print("\n📝 Test 2: Creating employee EMP001 in organization 2...")
        employee2 = Employee(
            employee_id="EMP001",  # Same employee_id
            user_id=user2.id,
            organization_id=org2.id,  # Different organization
            first_name="Jane",
            last_name="Smith", 
            position="Manager",
            job_title="Project Manager",
            hire_date=date.today(),
            status="ACTIVE"
        )
        db.add(employee2)
        db.commit()
        db.refresh(employee2)
        print(f"✅ Successfully created employee {employee2.employee_id} in {org2.name}")
        
        # Test 3: Try to create duplicate employee_id in same organization (should fail)
        print("\n📝 Test 3: Attempting to create duplicate EMP001 in organization 1 (should fail)...")
        try:
            employee3 = Employee(
                employee_id="EMP001",  # Same employee_id
                user_id=user1.id,
                organization_id=org1.id,  # Same organization
                first_name="Duplicate",
                last_name="Employee",
                position="Tester",
                job_title="QA Engineer",
                hire_date=date.today(),
                status="ACTIVE"
            )
            db.add(employee3)
            db.commit()
            print("❌ ERROR: Duplicate employee_id was allowed in same organization!")
            return False
        except Exception as e:
            print(f"✅ Correctly prevented duplicate employee_id in same organization: {e}")
        
        # Verify the employees exist
        print("\n🔍 Verifying employees...")
        emp1_check = db.query(Employee).filter(
            Employee.employee_id == "EMP001",
            Employee.organization_id == org1.id
        ).first()
        
        emp2_check = db.query(Employee).filter(
            Employee.employee_id == "EMP001", 
            Employee.organization_id == org2.id
        ).first()
        
        if emp1_check and emp2_check:
            print(f"✅ Employee 1: {emp1_check.employee_id} in {org1.name}")
            print(f"✅ Employee 2: {emp2_check.employee_id} in {org2.name}")
            print("\n🎉 Multi-tenant employee creation test PASSED!")
            return True
        else:
            print("❌ Employees not found in database")
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
        
        # Delete test employees
        db.query(Employee).filter(Employee.employee_id == "EMP001").delete()
        
        # Delete test users
        db.query(User).filter(User.email.in_(["test1@example.com", "test2@example.com"])).delete()
        
        # Delete test organizations
        db.query(Organization).filter(Organization.name.in_(["Test Org 1", "Test Org 2"])).delete()
        
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
        success = test_multi_tenant_employee_creation()
        if success:
            print("\n✅ All tests passed! The multi-tenant employee creation is working correctly.")
        else:
            print("\n❌ Tests failed! Please check the implementation.")
            sys.exit(1)
