import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.v1.auth import get_current_user
from app.core.mongo import get_mongo_db
from app.models.enums import ExpenseStatus, ExpenseType, PaymentMethod, UserRole
from app.models.mongo_models import (
    EmployeeDocument,
    ExpenseDocument,
    ExpenseItemDocument,
    UserDocument,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _require_org(user: UserDocument) -> PydanticObjectId:
    if not user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not associated with an organization",
        )
    return user.organization_id


def _parse_object_id(value: str, label: str) -> PydanticObjectId:
    try:
        return PydanticObjectId(value)
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")


def _parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")


def _map_expense_type(value: str) -> ExpenseType:
    try:
        return ExpenseType(value.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid expense category")


def _map_status(value: str) -> ExpenseStatus:
    normalized = value.upper()
    if normalized == "PENDING":
        normalized = "PENDING_APPROVAL"
    try:
        return ExpenseStatus(normalized)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid expense status")


def _map_payment_method(value: Optional[str]) -> PaymentMethod:
    method = (value or "CASH").upper()
    try:
        return PaymentMethod(method)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payment method")


def _can_view_items(user: UserDocument) -> bool:
    return user.role in [
        UserRole.SUPER_ADMIN,
        UserRole.ORG_ADMIN,
        UserRole.HR,
        UserRole.MANAGER,
        UserRole.DIRECTOR,
    ]


def _can_edit_items(user: UserDocument) -> bool:
    return user.role in [
        UserRole.SUPER_ADMIN,
        UserRole.ORG_ADMIN,
        UserRole.HR,
        UserRole.MANAGER,
    ]


def _stringify(value: Optional[PydanticObjectId]) -> Optional[str]:
    return str(value) if value else None


def _build_item_response(
    item: ExpenseItemDocument,
    employee_map: Dict[PydanticObjectId, EmployeeDocument],
) -> Dict[str, Any]:
    employee = employee_map.get(item.employee_id)
    employee_name = (
        f"{employee.first_name} {employee.last_name}"
        if employee
        else "Unknown Employee"
    )
    return {
        "id": str(item.id),
        "description": item.description,
        "amount": float(item.amount or 0),
        "category": item.expense_type.value,
        "date": item.expense_date.isoformat() if item.expense_date else None,
        "receipt": item.receipt_number,
        "status": item.status.value,
        "employee_name": employee_name,
        "expense_id": str(item.expense_id),
    }


async def _get_employee_for_user(user: UserDocument) -> EmployeeDocument:
    employee = await EmployeeDocument.find_one(EmployeeDocument.user_id == user.id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    return employee


@router.get("/items")
async def get_expense_items(
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
):
    """List expense items with optional filters."""
    if not _can_view_items(current_user):
        raise HTTPException(status_code=403, detail="Not authorized to view expense items")

    query: Dict[str, Any] = {}
    if current_user.role != UserRole.SUPER_ADMIN:
        query["organization_id"] = _require_org(current_user)

    if category:
        query["expense_type"] = _map_expense_type(category)

    if status_filter:
        query["status"] = _map_status(status_filter)

    total = await ExpenseItemDocument.find(query).count()
    items = (
        await ExpenseItemDocument.find(query)
        .sort("-expense_date")
        .skip(skip)
        .limit(limit)
        .to_list()
    )

    employee_ids = {item.employee_id for item in items if item.employee_id}
    employee_map: Dict[PydanticObjectId, EmployeeDocument] = {}
    if employee_ids:
        employees = await EmployeeDocument.find({"_id": {"$in": list(employee_ids)}}).to_list()
        employee_map = {employee.id: employee for employee in employees}

    return {
        "items": [_build_item_response(item, employee_map) for item in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/items")
async def create_expense_item(
    item_data: Dict[str, Any],
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Create an expense entry with a single item."""
    if not _can_edit_items(current_user):
        raise HTTPException(status_code=403, detail="Not authorized to create expense items")

    try:
        employee = await _get_employee_for_user(current_user)
        organization_id = _require_org(current_user)
        amount = Decimal(str(item_data.get("amount", 0)))
        expense_type = _map_expense_type(item_data.get("category", "OTHER"))
        payment_method = _map_payment_method(item_data.get("payment_method"))
        expense_date = _parse_date(item_data.get("date", datetime.utcnow().date().isoformat()))

        expense = ExpenseDocument(
            employee_id=employee.id,
            organization_id=organization_id,
            title=item_data.get("title", "Individual Expense Item"),
            description=item_data.get("description", ""),
            expense_type=expense_type,
            amount=amount,
            currency=item_data.get("currency", "USD"),
            expense_date=expense_date,
            location=item_data.get("location"),
            vendor=item_data.get("vendor"),
            payment_method=payment_method,
            receipt_number=item_data.get("receipt_number"),
            status=ExpenseStatus.DRAFT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        await expense.insert()

        expense_item = ExpenseItemDocument(
            expense_id=expense.id,
            organization_id=organization_id,
            employee_id=employee.id,
            description=item_data.get("description", ""),
            expense_type=expense_type,
            amount=amount,
            expense_date=expense_date,
            receipt_number=item_data.get("receipt_number"),
            status=expense.status,
        )
        await expense_item.insert()

        return _build_item_response(expense_item, {employee.id: employee})
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error creating expense item")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating expense item: {exc}",
        ) from exc


@router.put("/items/{item_id}")
async def update_expense_item(
    item_id: str,
    item_data: Dict[str, Any],
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Update an expense item."""
    if not _can_edit_items(current_user):
        raise HTTPException(status_code=403, detail="Not authorized to update expense items")

    try:
        item_obj_id = _parse_object_id(item_id, "Expense item")
        expense_item = await ExpenseItemDocument.get(item_obj_id)
        if not expense_item:
            raise HTTPException(status_code=404, detail="Expense item not found")

        if current_user.role != UserRole.SUPER_ADMIN:
            org_id = _require_org(current_user)
            if expense_item.organization_id != org_id:
                raise HTTPException(status_code=403, detail="Access denied to this expense item")

        expense = await ExpenseDocument.get(expense_item.expense_id)
        if not expense:
            raise HTTPException(status_code=404, detail="Parent expense not found")

        if "description" in item_data:
            expense_item.description = item_data["description"]
            expense.description = item_data["description"]
        if "amount" in item_data:
            amount = Decimal(str(item_data["amount"]))
            expense_item.amount = amount
            expense.amount = amount
        if "category" in item_data:
            expense_type = _map_expense_type(item_data["category"])
            expense_item.expense_type = expense_type
            expense.expense_type = expense_type
        if "date" in item_data:
            expense_item.expense_date = _parse_date(item_data["date"])
            expense.expense_date = expense_item.expense_date
        if "receipt_number" in item_data:
            expense_item.receipt_number = item_data["receipt_number"]
            expense.receipt_number = item_data["receipt_number"]

        expense.updated_at = datetime.utcnow()
        expense_item.status = expense.status

        await expense.save()
        await expense_item.save()

        employee = await EmployeeDocument.get(expense_item.employee_id) if expense_item.employee_id else None
        employee_map = {expense_item.employee_id: employee} if employee else {}
        return _build_item_response(expense_item, employee_map)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error updating expense item")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating expense item: {exc}",
        ) from exc


@router.delete("/items/{item_id}")
async def delete_expense_item(
    item_id: str,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Delete an expense item (and parent expense if now empty)."""
    if not _can_edit_items(current_user):
        raise HTTPException(status_code=403, detail="Not authorized to delete expense items")

    try:
        item_obj_id = _parse_object_id(item_id, "Expense item")
        expense_item = await ExpenseItemDocument.get(item_obj_id)
        if not expense_item:
            raise HTTPException(status_code=404, detail="Expense item not found")

        if current_user.role != UserRole.SUPER_ADMIN:
            org_id = _require_org(current_user)
            if expense_item.organization_id != org_id:
                raise HTTPException(status_code=403, detail="Access denied to this expense item")

        expense_id = expense_item.expense_id
        await expense_item.delete()

        remaining = await ExpenseItemDocument.find({"expense_id": expense_id}).count()
        if remaining == 0:
            expense = await ExpenseDocument.get(expense_id)
            if expense:
                await expense.delete()

        return {"message": "Expense item deleted successfully"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error deleting expense item")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting expense item: {exc}",
        ) from exc


@router.get("/reports")
async def get_expense_reports(
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None, alias="status"),
):
    """Return expense summaries (reports) for the organization."""
    if not _can_view_items(current_user):
        raise HTTPException(status_code=403, detail="Not authorized to view expense reports")

    query: Dict[str, Any] = {}
    if current_user.role != UserRole.SUPER_ADMIN:
        query["organization_id"] = _require_org(current_user)

    if status_filter:
        query["status"] = _map_status(status_filter)

    total = await ExpenseDocument.find(query).count()
    expenses = (
        await ExpenseDocument.find(query)
        .sort("-created_at")
        .skip(skip)
        .limit(limit)
        .to_list()
    )

    expense_ids = [expense.id for expense in expenses]
    item_counts: Dict[PydanticObjectId, int] = {}
    if expense_ids:
        items = await ExpenseItemDocument.find({"expense_id": {"$in": expense_ids}}).to_list()
        for item in items:
            item_counts[item.expense_id] = item_counts.get(item.expense_id, 0) + 1

    employee_ids = {expense.employee_id for expense in expenses if expense.employee_id}
    employee_map: Dict[PydanticObjectId, EmployeeDocument] = {}
    if employee_ids:
        employees = await EmployeeDocument.find({"_id": {"$in": list(employee_ids)}}).to_list()
        employee_map = {employee.id: employee for employee in employees}

    reports = []
    for expense in expenses:
        employee = employee_map.get(expense.employee_id)
        employee_name = (
            f"{employee.first_name} {employee.last_name}"
            if employee
            else "Unknown Employee"
        )
        reports.append(
            {
                "id": str(expense.id),
                "employee": employee_name,
                "title": expense.title,
                "total_amount": float(expense.amount or 0),
                "status": expense.status.value,
                "submitted_date": expense.submitted_at.isoformat() if expense.submitted_at else None,
                "approved_date": expense.approved_at.isoformat() if expense.approved_at else None,
                "items": item_counts.get(expense.id, 0),
                "category": expense.expense_type.value,
            }
        )

    return {
        "reports": reports,
        "total": total,
        "skip": skip,
        "limit": limit,
    }
