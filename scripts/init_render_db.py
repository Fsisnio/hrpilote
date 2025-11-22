#!/usr/bin/env python3
"""
Initialize the Mongo database with test users.

This script/endpoint seeds the core organization, department, and user records
needed for smoke testing (matching the legacy SQL bootstrap).
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.mongo import init_mongo  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.models.enums import (  # noqa: E402
    OrganizationStatus,
    DepartmentStatus,
    UserRole,
    UserStatus,
)
from app.models.mongo_models import (  # noqa: E402
    ALL_DOCUMENT_MODELS,
    OrganizationDocument,
    DepartmentDocument,
    UserDocument,
)


async def _ensure_seed_data() -> bool:
    """Create the baseline organization, department, and users if missing."""
    await init_mongo(document_models=ALL_DOCUMENT_MODELS)

    existing_users = await UserDocument.find({}).count()
    if existing_users > 0:
        superadmin = await UserDocument.find_one(UserDocument.email == "superadmin@hrpilot.com")
        if superadmin:
            print("✅ Super admin user already exists; skipping seed.")
            return True
        print("⚠️ Users exist but super admin missing. Continuing to seed...")
    else:
        print("📝 No users found, creating seed data...")

    organization = await OrganizationDocument.find_one(OrganizationDocument.code == "TEST_ORG")
    if not organization:
        organization = OrganizationDocument(
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
            status=OrganizationStatus.ACTIVE,
        )
        await organization.insert()
        print("✅ Organization created")
    else:
        print("ℹ️ Organization already exists")

    department = await DepartmentDocument.find_one(
        (DepartmentDocument.code == "HR") & (DepartmentDocument.organization_id == organization.id)
    )
    if not department:
        department = DepartmentDocument(
            name="Human Resources",
            code="HR",
            description="HR Department",
            organization_id=organization.id,
            status=DepartmentStatus.ACTIVE,
        )
        await department.insert()
        print("✅ Department created")
    else:
        print("ℹ️ Department already exists")

    test_users: List[Dict[str, Any]] = [
        {
            "email": "superadmin@hrpilot.com",
            "username": "superadmin",
            "password": "Jesus1993@",
            "first_name": "Super",
            "last_name": "Admin",
            "role": UserRole.SUPER_ADMIN,
            "status": UserStatus.ACTIVE,
            "is_active": True,
            "is_email_verified": True,
        },
        {
            "email": "orgadmin@hrpilot.com",
            "username": "orgadmin",
            "password": "Jesus1993@",
            "first_name": "Org",
            "last_name": "Admin",
            "role": UserRole.ORG_ADMIN,
            "status": UserStatus.ACTIVE,
            "organization_id": organization.id,
            "is_active": True,
            "is_email_verified": True,
        },
        {
            "email": "hr@hrpilot.com",
            "username": "hr",
            "password": "Jesus1993@",
            "first_name": "HR",
            "last_name": "Manager",
            "role": UserRole.HR,
            "status": UserStatus.ACTIVE,
            "organization_id": organization.id,
            "department_id": department.id,
            "is_active": True,
            "is_email_verified": True,
        },
        {
            "email": "employee@hrpilot.com",
            "username": "employee",
            "password": "Jesus1993@",
            "first_name": "Regular",
            "last_name": "Employee",
            "role": UserRole.EMPLOYEE,
            "status": UserStatus.ACTIVE,
            "organization_id": organization.id,
            "department_id": department.id,
            "is_active": True,
            "is_email_verified": True,
        },
    ]

    created_users: List[str] = []
    for record in test_users:
        email = record["email"]
        existing_user = await UserDocument.find_one(UserDocument.email == email)
        if existing_user:
            print(f"✅ User {email} already exists")
            continue

        payload = record.copy()
        password = payload.pop("password")
        user_doc = UserDocument(
            **payload,
            hashed_password=get_password_hash(password),
            last_login=datetime.utcnow(),
        )
        await user_doc.insert()
        created_users.append(email)

    if created_users:
        print("✅ New test users created:")
        for email in created_users:
            print(f"   • {email}")
    else:
        print("✅ All seed users already exist")

    print("\n🔑 Default password for all accounts: Jesus1993@")
    print("✅ Mongo database initialization completed!")
    return True


async def init_render_database() -> bool:
    """Public entrypoint used by both FastAPI and CLI."""
    print("🌱 Initializing Mongo database...")
    try:
        return await _ensure_seed_data()
    except Exception as exc:
        print(f"❌ Error initializing database: {exc}")
        return False


def main() -> None:
    success = asyncio.run(init_render_database())
    if success:
        print("\n🎉 Database initialization successful!")
        sys.exit(0)
    else:
        print("\n💥 Database initialization failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
