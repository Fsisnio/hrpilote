from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict
from datetime import datetime, date
from pydantic import BaseModel
from beanie import PydanticObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.mongo import get_mongo_db
from app.api.v1.auth import get_current_user
from app.models.mongo_models import (
    UserDocument,
    EmployeeDocument,
    LeaveRequestDocument,
    LeaveBalanceDocument,
    LeavePolicyDocument,
    HolidayDocument,
)
from app.models.enums import UserRole, LeaveType, LeaveStatus

router = APIRouter()

router = APIRouter()


# Pydantic models for request/response
class LeaveRequestCreate(BaseModel):
    employee_id: str
    leave_type: LeaveType
    start_date: date
    end_date: date
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    reason: str
    notes: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    handover_to: Optional[str] = None
    handover_notes: Optional[str] = None


class LeaveRequestUpdate(BaseModel):
    leave_type: Optional[LeaveType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    handover_to: Optional[str] = None
    handover_notes: Optional[str] = None


class LeaveRequestResponse(BaseModel):
    id: str
    employee_id: str
    employee_name: str
    leave_type: str
    start_date: date
    end_date: date
    total_days: float
    status: str
    reason: str
    created_at: datetime


class LeaveBalanceResponse(BaseModel):
    type: str
    total: float
    used: float
    remaining: float


def _parse_object_id(value: Optional[str], label: str) -> Optional[PydanticObjectId]:
    if value is None:
        return None
    try:
        return PydanticObjectId(value)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid {label}")


async def _get_employee_by_id(employee_id: str) -> EmployeeDocument:
    obj_id = _parse_object_id(employee_id, "employee_id")
    employee = await EmployeeDocument.get(obj_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return employee


async def _get_employee_for_user(user: UserDocument) -> EmployeeDocument:
    employee = await EmployeeDocument.find_one(EmployeeDocument.user_id == user.id)
    if not employee:
        role = user.role.value if hasattr(user.role, "value") else user.role
        if role == "EMPLOYEE":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee record not found. Please contact HR to set up your employee profile."
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Leave features are only available to employees. Current role: {role}"
        )
    return employee


def _leave_request_to_response(
    request: LeaveRequestDocument,
    employee_map: Dict[PydanticObjectId, EmployeeDocument]
) -> LeaveRequestResponse:
    employee = employee_map.get(request.employee_id)
    employee_name = f"{employee.first_name} {employee.last_name}" if employee else "Unknown"
    status_value = request.status.value if isinstance(request.status, LeaveStatus) else request.status
    return LeaveRequestResponse(
        id=str(request.id),
        employee_id=str(request.employee_id),
        employee_name=employee_name,
        leave_type=request.leave_type.value if hasattr(request.leave_type, "value") else request.leave_type,
        start_date=request.start_date,
        end_date=request.end_date,
        total_days=request.total_days,
        status=status_value,
        reason=request.reason,
        created_at=request.created_at,
    )


def _leave_balance_to_response(balance: LeaveBalanceDocument) -> LeaveBalanceResponse:
    return LeaveBalanceResponse(
        type=balance.leave_type.value.replace("_", " ").title(),
        total=balance.total_entitled,
        used=balance.total_taken,
        remaining=balance.total_remaining,
    )


DEFAULT_BALANCES = [
    (LeaveType.ANNUAL, 20.0),
    (LeaveType.SICK, 10.0),
    (LeaveType.PERSONAL, 5.0),
    (LeaveType.MATERNITY, 90.0),
    (LeaveType.PATERNITY, 14.0),
]


@router.get("/requests", response_model=List[LeaveRequestResponse])
async def get_leave_requests(
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    status_filter: Optional[str] = Query(None),
    leave_type: Optional[str] = Query(None),
    employee_id: Optional[str] = Query(None),
):
    """
    Get leave requests with optional filtering
    """
    query: Dict = {}

    if current_user.role == UserRole.EMPLOYEE:
        employee = await _get_employee_for_user(current_user)
        query["employee_id"] = employee.id
    else:
        employee = await EmployeeDocument.find_one(EmployeeDocument.user_id == current_user.id)
        if employee and current_user.role in [UserRole.MANAGER, UserRole.HR, UserRole.ORG_ADMIN]:
            query["organization_id"] = employee.organization_id
    if status_filter:
        try:
            query["status"] = LeaveStatus(status_filter.upper())
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status filter")
    if leave_type:
        try:
            query["leave_type"] = LeaveType(leave_type.upper())
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid leave type filter")
    if employee_id:
        query["employee_id"] = _parse_object_id(employee_id, "employee_id")

    leave_requests = await LeaveRequestDocument.find(query).sort("-created_at").to_list()

    employee_ids = {req.employee_id for req in leave_requests}
    employees = await EmployeeDocument.find({"_id": {"$in": list(employee_ids)}}).to_list()
    employee_map = {emp.id: emp for emp in employees}

    return [_leave_request_to_response(req, employee_map) for req in leave_requests]


@router.get("/requests/{request_id}", response_model=LeaveRequestResponse)
async def get_leave_request(
    request_id: str,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Get a specific leave request
    """
    request_obj_id = _parse_object_id(request_id, "request_id")
    leave_request = await LeaveRequestDocument.get(request_obj_id)
    if not leave_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")

    if current_user.role == UserRole.EMPLOYEE:
        employee = await _get_employee_for_user(current_user)
        if leave_request.employee_id != employee.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this request")

    employee = await EmployeeDocument.get(leave_request.employee_id)
    employee_map = {leave_request.employee_id: employee} if employee else {}
    return _leave_request_to_response(leave_request, employee_map)


@router.post("/requests", response_model=LeaveRequestResponse)
async def create_leave_request(
    leave_data: LeaveRequestCreate,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Create a new leave request
    """
    employee = await _get_employee_by_id(leave_data.employee_id)

    if current_user.role == UserRole.EMPLOYEE:
        current_employee = await _get_employee_for_user(current_user)
        if employee.id != current_employee.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to create this request")

    delta = leave_data.end_date - leave_data.start_date
    total_days = delta.days + 1

    handover_to = _parse_object_id(leave_data.handover_to, "handover_to") if leave_data.handover_to else None

    leave_request = LeaveRequestDocument(
        employee_id=employee.id,
        organization_id=employee.organization_id,
        leave_type=leave_data.leave_type,
        start_date=leave_data.start_date,
        end_date=leave_data.end_date,
        start_time=leave_data.start_time,
        end_time=leave_data.end_time,
        total_days=total_days,
        reason=leave_data.reason,
        notes=leave_data.notes,
        emergency_contact_name=leave_data.emergency_contact_name,
        emergency_contact_phone=leave_data.emergency_contact_phone,
        handover_to=handover_to,
        handover_notes=leave_data.handover_notes,
        requested_by=current_user.id,
        status=LeaveStatus.PENDING,
    )

    await leave_request.insert()
    employee_map = {employee.id: employee}
    return _leave_request_to_response(leave_request, employee_map)


@router.put("/requests/{request_id}/approve")
async def approve_leave_request(
    request_id: str,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Approve a leave request
    """
    if current_user.role not in [UserRole.MANAGER, UserRole.HR, UserRole.ORG_ADMIN, UserRole.DIRECTOR, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to approve leave requests")
    
    request_obj_id = _parse_object_id(request_id, "request_id")
    leave_request = await LeaveRequestDocument.get(request_obj_id)
    if not leave_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")
    
    if leave_request.status != LeaveStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Leave request is not pending")
    
    leave_request.status = LeaveStatus.APPROVED
    leave_request.approved_by = current_user.id
    leave_request.approved_at = datetime.utcnow()
    
    await leave_request.save()
    return {"message": f"Leave request {request_id} approved successfully"}


class RejectRequest(BaseModel):
    reason: str

@router.put("/requests/{request_id}/reject")
async def reject_leave_request(
    request_id: str,
    reject_data: RejectRequest,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Reject a leave request
    """
    # Check permissions
    if current_user.role not in [UserRole.MANAGER, UserRole.HR, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to reject leave requests")
    
    request_obj_id = _parse_object_id(request_id, "request_id")
    leave_request = await LeaveRequestDocument.get(request_obj_id)
    if not leave_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")
    
    if leave_request.status != LeaveStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Leave request is not pending")
    
    leave_request.status = LeaveStatus.REJECTED
    leave_request.rejection_reason = reject_data.reason
    leave_request.approved_by = current_user.id
    leave_request.approved_at = datetime.utcnow()
    
    await leave_request.save()
    
    return {"message": f"Leave request {request_id} rejected successfully"}


@router.get("/balances", response_model=List[LeaveBalanceResponse])
async def get_leave_balances(
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    employee_id: Optional[str] = Query(None),
):
    """
    Get leave balances for an employee
    """
    target_employee: Optional[EmployeeDocument] = None

    if current_user.role == UserRole.EMPLOYEE:
        target_employee = await _get_employee_for_user(current_user)
    elif employee_id:
        target_employee = await _get_employee_by_id(employee_id)
        if current_user.role == UserRole.MANAGER:
            manager_employee = await _get_employee_for_user(current_user)
            if manager_employee.organization_id != target_employee.organization_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this employee's balances")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Employee ID is required")

    current_year = datetime.utcnow().year
    balances = await LeaveBalanceDocument.find(
        {
            "employee_id": target_employee.id,
            "year": current_year,
        }
    ).to_list()

    if not balances:
        for leave_type, total_entitled in DEFAULT_BALANCES:
            balance = LeaveBalanceDocument(
                employee_id=target_employee.id,
                organization_id=target_employee.organization_id,
                leave_type=leave_type,
                year=current_year,
                total_entitled=total_entitled,
                total_taken=0.0,
                total_remaining=total_entitled,
            )
            await balance.insert()
        balances = await LeaveBalanceDocument.find(
            {
                "employee_id": target_employee.id,
                "year": current_year,
            }
        ).to_list()

    return [_leave_balance_to_response(balance) for balance in balances]


@router.get("/balances/summary", response_model=List[LeaveBalanceResponse])
async def get_leave_balances_summary(
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Get leave balances summary for the organization (for dashboard)
    """
    current_year = datetime.utcnow().year

    organization_filter = {}
    employee_filter = {}

    if current_user.role == UserRole.SUPER_ADMIN:
        pass
    else:
        employee = await _get_employee_for_user(current_user)
        organization_filter["organization_id"] = employee.organization_id
        if current_user.role == UserRole.EMPLOYEE:
            employee_filter["employee_id"] = employee.id

    query: Dict = {"year": current_year}
    query.update(organization_filter)
    query.update(employee_filter)

    balances = await LeaveBalanceDocument.find(query).to_list()

    summary: Dict[str, Dict[str, float]] = {}
    for balance in balances:
        leave_type = balance.leave_type.value.replace("_", " ").title()
        if leave_type not in summary:
            summary[leave_type] = {"total": 0.0, "used": 0.0, "remaining": 0.0}
        summary[leave_type]["total"] += balance.total_entitled
        summary[leave_type]["used"] += balance.total_taken
        summary[leave_type]["remaining"] += balance.total_remaining

    return [
        LeaveBalanceResponse(type=lt, total=data["total"], used=data["used"], remaining=data["remaining"])
        for lt, data in summary.items()
    ]


@router.get("/types")
async def get_leave_types():
    """
    Get all available leave types
    """
    return [{"value": lt.value, "label": lt.value.replace('_', ' ').title()} for lt in LeaveType]


@router.get("/policies")
async def get_leave_policies(
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db)
):
    """
    Get leave policies for the organization
    """
    # Get employee's organization
    employee = await _get_employee_for_user(current_user)
    
    policies = await LeavePolicyDocument.find(
        {
            "organization_id": employee.organization_id,
            "is_active": True,
        }
    ).to_list()
    
    return [
        {
            "id": str(policy.id),
            "name": policy.name,
            "description": policy.description,
            "leave_type": policy.leave_type.value,
            "days_per_year": policy.days_per_year,
            "min_service_months": policy.min_service_months,
            "max_consecutive_days": policy.max_consecutive_days,
            "min_notice_days": policy.min_notice_days,
            "requires_approval": policy.requires_approval,
            "allow_carry_forward": policy.allow_carry_forward
        }
        for policy in policies
    ] 