#!/usr/bin/env python3
"""
Script to create test users for all roles to verify functionality (Mongo edition).
"""

import asyncio
import os
import sys
from typing import Dict, Any, List

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.core.mongo import init_mongo  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.models.enums import UserRole, UserStatus  # noqa: E402
from app.models.mongo_models import (  # noqa: E402
    ALL_DOCUMENT_MODELS,
    UserDocument,
    OrganizationDocument,
)

TEST_USERS: List[Dict[str, Any]] = [
    {
        "email": "superadmin@test.com",
        "username": "superadmin_test",
        "first_name": "Super",
        "last_name": "Admin",
        "role": UserRole.SUPER_ADMIN,
        "organization_required": False,
    },
    {
        "email": "orgadmin@test.com",
        "username": "orgadmin_test",
        "first_name": "Org",
        "last_name": "Admin",
        "role": UserRole.ORG_ADMIN,
        "organization_required": True,
    },
    {
        "email": "hr@test.com",
        "username": "hr_test",
        "first_name": "HR",
        "last_name": "Manager",
        "role": UserRole.HR,
        "organization_required": True,
    },
    {
        "email": "manager@test.com",
        "username": "manager_test",
        "first_name": "Team",
        "last_name": "Manager",
        "role": UserRole.MANAGER,
        "organization_required": True,
    },
    {
        "email": "director@test.com",
        "username": "director_test",
        "first_name": "Department",
        "last_name": "Director",
        "role": UserRole.DIRECTOR,
        "organization_required": True,
    },
    {
        "email": "payroll@test.com",
        "username": "payroll_test",
        "first_name": "Payroll",
        "last_name": "Specialist",
        "role": UserRole.PAYROLL,
        "organization_required": True,
    },
    {
        "email": "employee@test.com",
        "username": "employee_test",
        "first_name": "Regular",
        "last_name": "Employee",
        "role": UserRole.EMPLOYEE,
        "organization_required": True,
    },
]

DEFAULT_PASSWORD = "Admin123!"


async def create_test_users() -> None:
    """Create test users for all roles using MongoDB."""
    print("🔧 Creating test users for all roles (Mongo)...")
    await init_mongo(document_models=ALL_DOCUMENT_MODELS)

    organization = await OrganizationDocument.find_one({}) if TEST_USERS else None
    if not organization:
        print("❌ No organization found. Seed an organization first (e.g., via init endpoint).")
        return

    created_count = 0
    skipped_count = 0

    for record in TEST_USERS:
        email = record["email"]
        existing_user = await UserDocument.find_one(UserDocument.email == email)
        if existing_user:
            print(f"⚠️ User {email} already exists, skipping...")
            skipped_count += 1
            continue

        payload = {
            "email": record["email"],
            "username": record["username"],
            "hashed_password": get_password_hash(DEFAULT_PASSWORD),
            "first_name": record["first_name"],
            "last_name": record["last_name"],
            "role": record["role"],
            "status": UserStatus.ACTIVE,
            "is_email_verified": True,
            "is_active": True,
            "failed_login_attempts": 0,
            "locked_until": None,
        }

        if record["organization_required"]:
            payload["organization_id"] = organization.id

        await UserDocument(**payload).insert()
        print(f"✅ Created {record['role'].value} user: {email}")
        created_count += 1

    print(f"\n🎉 Successfully created {created_count} test users")
    if skipped_count:
        print(f"⚠️ Skipped {skipped_count} existing users")

    print("\n📋 Login Credentials for Testing:")
    print("=" * 50)
    for record in TEST_USERS:
        print(f"Role: {record['role'].value}")
        print(f"Email: {record['email']}")
        print(f"Password: {DEFAULT_PASSWORD}")
        print("-" * 30)


def main() -> None:
    """Entry point when running as a script."""
    print("👥 HR Pilot Test User Creation Script (Mongo)")
    print("=" * 40)

    try:
        asyncio.run(create_test_users())
        print("\n✅ Test users created successfully!")
        print("\n💡 You can now run the comprehensive test suite.")
    except Exception as exc:
        print(f"❌ Failed to create test users: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()





