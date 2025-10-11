from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, extract
from typing import List, Optional
from datetime import datetime, date
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.leave import LeaveRequest, LeaveBalance, LeavePolicy, LeaveType, LeaveStatus
from app.models.employee import Employee
from app.api.v1.auth import get_current_user
from pydantic import BaseModel

router = APIRouter()


# Pydantic models for request/response
class LeaveRequestCreate(BaseModel):
    employee_id: int
    leave_type: LeaveType
    start_date: date
    end_date: date
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    reason: str
    notes: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    handover_to: Optional[int] = None
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
    handover_to: Optional[int] = None
    handover_notes: Optional[str] = None

class LeaveRequestResponse(BaseModel):
    id: int
    employee_id: int
    employee_name: str
    leave_type: str
    start_date: date
    end_date: date
    total_days: float
    status: str
    reason: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class LeaveBalanceResponse(BaseModel):
    type: str
    total: float
    used: float
    remaining: float
    
    class Config:
        from_attributes = True


@router.get("/requests", response_model=List[LeaveRequestResponse])
async def get_leave_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None),
    leave_type: Optional[str] = Query(None),
    employee_id: Optional[int] = Query(None)
):
    """
    Get leave requests with optional filtering
    """
    # Build base query with proper join
    query = db.query(LeaveRequest).join(Employee, LeaveRequest.employee_id == Employee.id)
    
    # Apply filters based on user role
    if current_user.role == UserRole.EMPLOYEE:
        # Employees can only see their own requests
        employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Please, use your employee profile")
        query = query.filter(LeaveRequest.employee_id == employee.id)
    elif current_user.role == UserRole.MANAGER:
        # Managers can see requests from their organization
        employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if employee:
            query = query.filter(Employee.organization_id == employee.organization_id)
    elif current_user.role in [UserRole.HR, UserRole.ORG_ADMIN]:
        # HR and Org Admins can see requests from their organization
        employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if employee:
            query = query.filter(Employee.organization_id == employee.organization_id)
    
    # Apply additional filters
    if status:
        query = query.filter(LeaveRequest.status == status)
    if leave_type:
        query = query.filter(LeaveRequest.leave_type == leave_type)
    if employee_id:
        query = query.filter(LeaveRequest.employee_id == employee_id)
    
    leave_requests = query.order_by(LeaveRequest.created_at.desc()).all()
    
    # Convert to response format
    result = []
    for request in leave_requests:
        employee = db.query(Employee).filter(Employee.id == request.employee_id).first()
        result.append(LeaveRequestResponse(
            id=request.id,
            employee_id=request.employee_id,
            employee_name=f"{employee.first_name} {employee.last_name}" if employee else "Unknown",
            leave_type=request.leave_type.value,
            start_date=request.start_date,
            end_date=request.end_date,
            total_days=request.total_days,
            status=request.status.value,
            reason=request.reason,
            created_at=request.created_at
        ))
    
    return result


@router.get("/requests/{request_id}", response_model=LeaveRequestResponse)
async def get_leave_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific leave request
    """
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    # Check permissions
    if current_user.role == UserRole.EMPLOYEE:
        employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not employee or leave_request.employee_id != employee.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this request")
    
    employee = db.query(Employee).filter(Employee.id == leave_request.employee_id).first()
    return LeaveRequestResponse(
        id=leave_request.id,
        employee_id=leave_request.employee_id,
        employee_name=f"{employee.first_name} {employee.last_name}" if employee else "Unknown",
        leave_type=leave_request.leave_type.value,
        start_date=leave_request.start_date,
        end_date=leave_request.end_date,
        total_days=leave_request.total_days,
        status=leave_request.status.value,
        reason=leave_request.reason,
        created_at=leave_request.created_at
    )


@router.post("/requests", response_model=LeaveRequestResponse)
async def create_leave_request(
    leave_data: LeaveRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new leave request
    """
    # Validate employee exists
    employee = db.query(Employee).filter(Employee.id == leave_data.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check permissions
    if current_user.role == UserRole.EMPLOYEE:
        current_employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not current_employee or leave_data.employee_id != current_employee.id:
            raise HTTPException(status_code=403, detail="Not authorized to create request for this employee")
    
    # Calculate total days
    delta = leave_data.end_date - leave_data.start_date
    total_days = delta.days + 1
    
    # Create leave request
    leave_request = LeaveRequest(
        employee_id=leave_data.employee_id,
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
        handover_to=leave_data.handover_to,
        handover_notes=leave_data.handover_notes,
        requested_by=current_user.id,
        status=LeaveStatus.PENDING
    )
    
    db.add(leave_request)
    db.commit()
    db.refresh(leave_request)
    
    return LeaveRequestResponse(
        id=leave_request.id,
        employee_id=leave_request.employee_id,
        employee_name=f"{employee.first_name} {employee.last_name}",
        leave_type=leave_request.leave_type.value,
        start_date=leave_request.start_date,
        end_date=leave_request.end_date,
        total_days=leave_request.total_days,
        status=leave_request.status.value,
        reason=leave_request.reason,
        created_at=leave_request.created_at
    )


@router.put("/requests/{request_id}/approve")
async def approve_leave_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Approve a leave request
    """
    # Check permissions (allow Manager, HR, Org Admin, Director, Super Admin)
    if current_user.role not in [UserRole.MANAGER, UserRole.HR, UserRole.ORG_ADMIN, UserRole.DIRECTOR, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized to approve leave requests")
    
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    if leave_request.status != LeaveStatus.PENDING:
        raise HTTPException(status_code=400, detail="Leave request is not pending")
    
    leave_request.status = LeaveStatus.APPROVED
    leave_request.approved_by = current_user.id
    leave_request.approved_at = datetime.now()
    
    db.commit()
    
    return {"message": f"Leave request {request_id} approved successfully"}


class RejectRequest(BaseModel):
    reason: str

@router.put("/requests/{request_id}/reject")
async def reject_leave_request(
    request_id: int,
    reject_data: RejectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reject a leave request
    """
    # Check permissions
    if current_user.role not in [UserRole.MANAGER, UserRole.HR, UserRole.SUPER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized to reject leave requests")
    
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    if leave_request.status != LeaveStatus.PENDING:
        raise HTTPException(status_code=400, detail="Leave request is not pending")
    
    leave_request.status = LeaveStatus.REJECTED
    leave_request.rejection_reason = reject_data.reason
    leave_request.approved_by = current_user.id
    leave_request.approved_at = datetime.now()
    
    db.commit()
    
    return {"message": f"Leave request {request_id} rejected successfully"}


@router.get("/balances", response_model=List[LeaveBalanceResponse])
async def get_leave_balances(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    employee_id: Optional[int] = Query(None)
):
    """
    Get leave balances for an employee
    """
    # Determine which employee's balances to get
    target_employee_id = employee_id
    if current_user.role == UserRole.EMPLOYEE:
        employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Please, use your employee profile")
        target_employee_id = employee.id
    elif not target_employee_id:
        raise HTTPException(status_code=400, detail="Employee ID is required")
    
    # Check permissions for other roles
    if current_user.role in [UserRole.MANAGER, UserRole.HR, UserRole.SUPER_ADMIN] and target_employee_id:
        # Managers can only see their organization's employees
        if current_user.role == UserRole.MANAGER:
            current_employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
            target_employee = db.query(Employee).filter(Employee.id == target_employee_id).first()
            if not current_employee or not target_employee or current_employee.organization_id != target_employee.organization_id:
                raise HTTPException(status_code=403, detail="Not authorized to view this employee's balances")
    
    # Get current year
    current_year = datetime.now().year
    
    # Get leave balances for the employee
    balances = db.query(LeaveBalance).filter(
        and_(
            LeaveBalance.employee_id == target_employee_id,
            LeaveBalance.year == current_year
        )
    ).all()
    
    # If no balances exist, create default ones
    if not balances:
        # Get organization ID
        employee = db.query(Employee).filter(Employee.id == target_employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Create default balances for common leave types
        default_balances = [
            (LeaveType.ANNUAL, 20.0),
            (LeaveType.SICK, 10.0),
            (LeaveType.PERSONAL, 5.0),
            (LeaveType.MATERNITY, 90.0),
            (LeaveType.PATERNITY, 14.0)
        ]
        
        for leave_type, total_entitled in default_balances:
            balance = LeaveBalance(
                employee_id=target_employee_id,
                organization_id=employee.organization_id,
                leave_type=leave_type,
                year=current_year,
                total_entitled=total_entitled,
                total_taken=0.0,
                total_remaining=total_entitled,
                total_carried_forward=0.0
            )
            db.add(balance)
        
        db.commit()
        db.refresh(balances)
        
        # Query again to get the newly created balances
        balances = db.query(LeaveBalance).filter(
            and_(
                LeaveBalance.employee_id == target_employee_id,
                LeaveBalance.year == current_year
            )
        ).all()
    
    # Convert to response format
    result = []
    for balance in balances:
        result.append(LeaveBalanceResponse(
            type=balance.leave_type.value.replace('_', ' ').title(),
            total=balance.total_entitled,
            used=balance.total_taken,
            remaining=balance.total_remaining
        ))
    
    return result


@router.get("/balances/summary", response_model=List[LeaveBalanceResponse])
async def get_leave_balances_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get leave balances summary for the organization (for dashboard)
    """
    # Get current year
    current_year = datetime.now().year
    
    # Get organization ID and employee ID based on user role
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admin can see all organizations
        organization_id = None
        employee_id = None
    elif current_user.role == UserRole.EMPLOYEE:
        # Employees can only see their own balances
        employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Please, use your employee profile")
        organization_id = employee.organization_id
        employee_id = employee.id
    else:
        # Other roles (HR, Manager, etc.) can see organization summary
        employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Please, use your employee profile")
        organization_id = employee.organization_id
        employee_id = None
    
    # Build query based on role
    query = db.query(LeaveBalance).filter(LeaveBalance.year == current_year)
    if organization_id:
        query = query.filter(LeaveBalance.organization_id == organization_id)
    if employee_id:
        # For employees, only show their own balances
        query = query.filter(LeaveBalance.employee_id == employee_id)
    
    balances = query.all()
    
    # Aggregate balances by leave type
    balance_summary = {}
    for balance in balances:
        leave_type = balance.leave_type.value.replace('_', ' ').title()
        if leave_type not in balance_summary:
            balance_summary[leave_type] = {
                'total': 0.0,
                'used': 0.0,
                'remaining': 0.0
            }
        balance_summary[leave_type]['total'] += balance.total_entitled
        balance_summary[leave_type]['used'] += balance.total_taken
        balance_summary[leave_type]['remaining'] += balance.total_remaining
    
    # Convert to response format
    result = []
    for leave_type, summary in balance_summary.items():
        result.append(LeaveBalanceResponse(
            type=leave_type,
            total=summary['total'],
            used=summary['used'],
            remaining=summary['remaining']
        ))
    
    return result


@router.get("/types")
async def get_leave_types():
    """
    Get all available leave types
    """
    return [{"value": lt.value, "label": lt.value.replace('_', ' ').title()} for lt in LeaveType]


@router.get("/policies")
async def get_leave_policies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get leave policies for the organization
    """
    # Get employee's organization
    employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Please, use your employee profile")
    
    policies = db.query(LeavePolicy).filter(
        and_(
            LeavePolicy.organization_id == employee.organization_id,
            LeavePolicy.is_active == True
        )
    ).all()
    
    return [
        {
            "id": policy.id,
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