#!/usr/bin/env python3
"""
Test script to verify multi-tenant user creation using Mongo.
"""

import asyncio
import os
import sys
from typing import Tuple

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.core.mongo import init_mongo  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.models.mongo_models import (  # noqa: E402
    ALL_DOCUMENT_MODELS,
    OrganizationDocument,
    UserDocument,
)
from app.models.enums import UserRole, UserStatus, OrganizationStatus  # noqa: E402

TEST_EMAIL = "test@example.com"


async def _ensure_organizations() -> Tuple[OrganizationDocument, OrganizationDocument]:
    org1 = await OrganizationDocument.find_one(OrganizationDocument.code == "EMAIL1")
    if not org1:
        org1 = OrganizationDocument(
            name="Test Email Org 1",
            code="EMAIL1",
            description="Test organization for email testing 1",
            status=OrganizationStatus.ACTIVE,
        )
        await org1.insert()
        print(f"✅ Created organization: {org1.name}")

    org2 = await OrganizationDocument.find_one(OrganizationDocument.code == "EMAIL2")
    if not org2:
        org2 = OrganizationDocument(
            name="Test Email Org 2",
            code="EMAIL2",
            description="Test organization for email testing 2",
            status=OrganizationStatus.ACTIVE,
        )
        await org2.insert()
        print(f"✅ Created organization: {org2.name}")

    return org1, org2


async def test_multi_tenant_user_creation() -> bool:
    await init_mongo(document_models=ALL_DOCUMENT_MODELS)
    print("🧪 Testing multi-tenant user creation (Mongo)...")

    org1, org2 = await _ensure_organizations()

    await UserDocument.find(UserDocument.email == TEST_EMAIL).delete()
    print("🧹 Cleared existing test users")

    print("\n📝 Test 1: Creating user in organization 1...")
    user1 = UserDocument(
        email=TEST_EMAIL,
        username="testuser1",
        hashed_password=get_password_hash("password123"),
        first_name="Test",
        last_name="User1",
        role=UserRole.EMPLOYEE,
        status=UserStatus.ACTIVE,
        organization_id=org1.id,
        is_email_verified=True,
        is_active=True,
    )
    await user1.insert()
    print(f"✅ Successfully created user {user1.email} in {org1.name}")

    print("\n📝 Test 2: Creating user with same email in organization 2...")
    user2 = UserDocument(
        email=TEST_EMAIL,
        username="testuser2",
        hashed_password=get_password_hash("password123"),
        first_name="Test",
        last_name="User2",
        role=UserRole.EMPLOYEE,
        status=UserStatus.ACTIVE,
        organization_id=org2.id,
        is_email_verified=True,
        is_active=True,
    )
    await user2.insert()
    print(f"✅ Successfully created user {user2.email} in {org2.name}")

    print("\n📝 Test 3: Attempting to create duplicate in organization 1 (should fail)...")
    duplicate = UserDocument(
        email=TEST_EMAIL,
        username="testuser3",
        hashed_password=get_password_hash("password123"),
        first_name="Duplicate",
        last_name="User",
        role=UserRole.EMPLOYEE,
        status=UserStatus.ACTIVE,
        organization_id=org1.id,
        is_email_verified=True,
        is_active=True,
    )
    try:
        await duplicate.insert()
        print("❌ ERROR: Duplicate email was allowed in same organization!")
        return False
    except Exception as exc:
        print(f"✅ Correctly prevented duplicate email in same organization: {exc}")

    user1_check = await UserDocument.find_one(
        {"email": TEST_EMAIL, "organization_id": org1.id}
    )
    user2_check = await UserDocument.find_one(
        {"email": TEST_EMAIL, "organization_id": org2.id}
    )
    if user1_check and user2_check:
        print(f"✅ User 1: {user1_check.email} in {org1.name}")
        print(f"✅ User 2: {user2_check.email} in {org2.name}")
        print("\n🎉 Multi-tenant user creation test PASSED!")
        return True

    print("❌ Users not found in database")
    return False


async def cleanup_test_data() -> None:
    await init_mongo(document_models=ALL_DOCUMENT_MODELS)
    print("\n🧹 Cleaning up test data...")
    await UserDocument.find(UserDocument.email == TEST_EMAIL).delete()
    await OrganizationDocument.find(
        OrganizationDocument.code.in_(["EMAIL1", "EMAIL2"])
    ).delete()
    print("✅ Test data cleaned up")


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        asyncio.run(cleanup_test_data())
    else:
        success = asyncio.run(test_multi_tenant_user_creation())
        if success:
            print("\n✅ All tests passed! Multi-tenant user creation is working correctly.")
        else:
            print("\n❌ Tests failed! Please check the implementation.")
            sys.exit(1)


if __name__ == "__main__":
    main()
