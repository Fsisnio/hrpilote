#!/usr/bin/env python3
"""
Seed script to populate the database with initial data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, create_tables
from app.core.security import get_password_hash
from app.models.user import User, UserRole, UserStatus
from app.models.organization import Organization, OrganizationStatus
from app.models.department import Department, DepartmentStatus
from datetime import datetime

def create_test_data():
    """Create test data for the application"""
    db = SessionLocal()
    
    try:
        # Check if organization already exists
        organization = db.query(Organization).filter(Organization.code == "TEST_ORG").first()
        if not organization:
            # Create organization
            organization = Organization(
                name="Test Organization",
                code="TEST_ORG",
                description="A test organization for development",
                address_line1="123 Test Street",
                city="Test City",
                state="Test State",
                country="Test Country",
                postal_code="12345",
                phone="+1234567890",
                email="contact@testorg.com",
                website="https://testorg.com",
                status=OrganizationStatus.ACTIVE
            )
            db.add(organization)
            db.commit()
            db.refresh(organization)
            print("✅ Organization created")
        else:
            print("✅ Organization already exists")
        
        # Check if department already exists
        department = db.query(Department).filter(
            Department.code == "HR",
            Department.organization_id == organization.id
        ).first()
        if not department:
            # Create department
            department = Department(
                name="Human Resources",
                code="HR",
                description="HR Department",
                organization_id=organization.id,
                status=DepartmentStatus.ACTIVE
            )
            db.add(department)
            db.commit()
            db.refresh(department)
            print("✅ Department created")
        else:
            print("✅ Department already exists")
        
        # Create test users
        test_users = [
            {
                "email": "superadmin@hrpilot.com",
                "username": "superadmin",
                "password": "Password123!",
                "first_name": "Super",
                "last_name": "Admin",
                "role": UserRole.SUPER_ADMIN,
                "status": UserStatus.ACTIVE,
                "is_active": True,
                "is_email_verified": True
            },
            {
                "email": "orgadmin@hrpilot.com",
                "username": "orgadmin",
                "password": "Password123!",
                "first_name": "Org",
                "last_name": "Admin",
                "role": UserRole.ORG_ADMIN,
                "status": UserStatus.ACTIVE,
                "organization_id": organization.id,
                "is_active": True,
                "is_email_verified": True
            },
            {
                "email": "hr@hrpilot.com",
                "username": "hr",
                "password": "Password123!",
                "first_name": "HR",
                "last_name": "Manager",
                "role": UserRole.HR,
                "status": UserStatus.ACTIVE,
                "organization_id": organization.id,
                "department_id": department.id,
                "is_active": True,
                "is_email_verified": True
            },
            {
                "email": "manager@hrpilot.com",
                "username": "manager",
                "password": "Password123!",
                "first_name": "Team",
                "last_name": "Manager",
                "role": UserRole.MANAGER,
                "status": UserStatus.ACTIVE,
                "organization_id": organization.id,
                "department_id": department.id,
                "is_active": True,
                "is_email_verified": True
            },
            {
                "email": "director@hrpilot.com",
                "username": "director",
                "password": "Password123!",
                "first_name": "Department",
                "last_name": "Director",
                "role": UserRole.DIRECTOR,
                "status": UserStatus.ACTIVE,
                "organization_id": organization.id,
                "department_id": department.id,
                "is_active": True,
                "is_email_verified": True
            },
            {
                "email": "payroll@hrpilot.com",
                "username": "payroll",
                "password": "Password123!",
                "first_name": "Payroll",
                "last_name": "Specialist",
                "role": UserRole.PAYROLL,
                "status": UserStatus.ACTIVE,
                "organization_id": organization.id,
                "department_id": department.id,
                "is_active": True,
                "is_email_verified": True
            },
            {
                "email": "employee@hrpilot.com",
                "username": "employee",
                "password": "Password123!",
                "first_name": "Regular",
                "last_name": "Employee",
                "role": UserRole.EMPLOYEE,
                "status": UserStatus.ACTIVE,
                "organization_id": organization.id,
                "department_id": department.id,
                "is_active": True,
                "is_email_verified": True
            }
        ]
        
        created_users = []
        for user_data in test_users:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == user_data['email']).first()
            if not existing_user:
                password = user_data.pop("password")
                user = User(
                    **user_data,
                    hashed_password=get_password_hash(password),
                    last_login=datetime.utcnow()
                )
                db.add(user)
                created_users.append(user_data)
            else:
                print(f"✅ User {user_data['email']} already exists")
        
        if created_users:
            db.commit()
            print("✅ New test users created successfully!")
            print("\n📋 New test accounts created:")
            for user_data in created_users:
                print(f"   • {user_data['email']} (Role: {user_data['role']})")
        else:
            print("✅ All test users already exist")
        
        print("\n🔑 All accounts use password: Password123!")
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🌱 Creating test data...")
    create_tables()
    create_test_data()
    print("✅ Database seeding completed!")
