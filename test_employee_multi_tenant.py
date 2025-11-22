#!/usr/bin/env python3
"""
Test script to verify multi-tenant employee creation using Mongo.
"""

import asyncio
import os
import sys
from datetime import date
from typing import Tuple

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.core.mongo import init_mongo  # noqa: E402
from app.core.security import get_password_hash  # noqa: E402
from app.models.enums import OrganizationStatus, UserRole, EmployeeStatus  # noqa: E402
from app.models.mongo_models import (  # noqa: E402
    ALL_DOCUMENT_MODELS,
    OrganizationDocument,
    UserDocument,
    EmployeeDocument,
)

EMPLOYEE_ID = "EMP001"


async def _ensure_orgs_and_users() -> Tuple[Tuple[OrganizationDocument, UserDocument], Tuple[OrganizationDocument, UserDocument]]:
    await UserDocument.find(
        {"email": {"$in": ["test1@example.com", "test2@example.com"]}}
    ).delete()

    org1 = await OrganizationDocument.find_one(OrganizationDocument.code == "TEST1")
    if not org1:
        org1 = OrganizationDocument(
            name="Test Org 1",
            code="TEST1",
            description="Test organization 1",
            status=OrganizationStatus.ACTIVE,
        )
        await org1.insert()
        print(f"✅ Created organization: {org1.name}")

    org2 = await OrganizationDocument.find_one(OrganizationDocument.code == "TEST2")
    if not org2:
        org2 = OrganizationDocument(
            name="Test Org 2",
            code="TEST2",
            description="Test organization 2",
            status=OrganizationStatus.ACTIVE,
        )
        await org2.insert()
        print(f"✅ Created organization: {org2.name}")

    user1 = await UserDocument.find_one(UserDocument.email == "test1@example.com")
    if not user1:
        user1 = UserDocument(
            email="test1@example.com",
            username="emp_testuser1",
            hashed_password=get_password_hash("password123"),
            first_name="Test",
            last_name="User1",
            role=UserRole.EMPLOYEE,
            organization_id=org1.id,
        )
        await user1.insert()
        print(f"✅ Created user: {user1.email}")

    user2 = await UserDocument.find_one(UserDocument.email == "test2@example.com")
    if not user2:
        user2 = UserDocument(
            email="test2@example.com",
            username="emp_testuser2",
            hashed_password=get_password_hash("password123"),
            first_name="Test",
            last_name="User2",
            role=UserRole.EMPLOYEE,
            organization_id=org2.id,
        )
        await user2.insert()
        print(f"✅ Created user: {user2.email}")

    return (org1, user1), (org2, user2)


async def test_multi_tenant_employee_creation() -> bool:
    await init_mongo(document_models=ALL_DOCUMENT_MODELS)
    print("🧪 Testing multi-tenant employee creation (Mongo)...")

    (org1, user1), (org2, user2) = await _ensure_orgs_and_users()

    await EmployeeDocument.find(EmployeeDocument.employee_id == EMPLOYEE_ID).delete()
    print("🧹 Cleared existing test employees")

    print("\n📝 Test 1: Creating employee in organization 1...")
    emp1 = EmployeeDocument(
        employee_id=EMPLOYEE_ID,
        user_id=user1.id,
        organization_id=org1.id,
        first_name="John",
        last_name="Doe",
        position="Developer",
        job_title="Software Engineer",
        hire_date=date.today(),
        status=EmployeeStatus.ACTIVE,
    )
    await emp1.insert()
    print(f"✅ Successfully created employee {emp1.employee_id} in {org1.name}")

    print("\n📝 Test 2: Creating employee with same ID in organization 2...")
    emp2 = EmployeeDocument(
        employee_id=EMPLOYEE_ID,
        user_id=user2.id,
        organization_id=org2.id,
        first_name="Jane",
        last_name="Smith",
        position="Manager",
        job_title="Project Manager",
        hire_date=date.today(),
        status=EmployeeStatus.ACTIVE,
    )
    await emp2.insert()
    print(f"✅ Successfully created employee {emp2.employee_id} in {org2.name}")

    print("\n📝 Test 3: Attempting duplicate in organization 1 (should fail)...")
    duplicate = EmployeeDocument(
        employee_id=EMPLOYEE_ID,
        user_id=user1.id,
        organization_id=org1.id,
        first_name="Duplicate",
        last_name="Employee",
        position="Tester",
        job_title="QA Engineer",
        hire_date=date.today(),
        status=EmployeeStatus.ACTIVE,
    )
    try:
        await duplicate.insert()
        print("❌ ERROR: Duplicate employee_id was allowed in same organization!")
        return False
    except Exception as exc:
        print(f"✅ Correctly prevented duplicate employee_id in same organization: {exc}")

    emp1_check = await EmployeeDocument.find_one(
        {"employee_id": EMPLOYEE_ID, "organization_id": org1.id}
    )
    emp2_check = await EmployeeDocument.find_one(
        {"employee_id": EMPLOYEE_ID, "organization_id": org2.id}
    )
    if emp1_check and emp2_check:
        print(f"✅ Employee 1: {emp1_check.employee_id} in {org1.name}")
        print(f"✅ Employee 2: {emp2_check.employee_id} in {org2.name}")
        print("\n🎉 Multi-tenant employee creation test PASSED!")
        return True

    print("❌ Employees not found in database")
    return False


async def cleanup_test_data() -> None:
    await init_mongo(document_models=ALL_DOCUMENT_MODELS)
    print("\n🧹 Cleaning up test data...")
    await EmployeeDocument.find(EmployeeDocument.employee_id == EMPLOYEE_ID).delete()
    await UserDocument.find(UserDocument.email.in_(["test1@example.com", "test2@example.com"])).delete()
    await OrganizationDocument.find(OrganizationDocument.code.in_(["TEST1", "TEST2"])).delete()
    print("✅ Test data cleaned up")


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        asyncio.run(cleanup_test_data())
    else:
        success = asyncio.run(test_multi_tenant_employee_creation())
        if success:
            print("\n✅ All tests passed! Multi-tenant employee creation is working correctly.")
        else:
            print("\n❌ Tests failed! Please check the implementation.")
            sys.exit(1)


if __name__ == "__main__":
    main()
