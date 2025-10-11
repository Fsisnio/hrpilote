from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.employee import Employee, EmployeeStatus, EmploymentType, Gender
from app.models.organization import Organization
from app.models.department import Department
from app.api.v1.auth import get_current_user

router = APIRouter()

# Schema for creating a new employee
class CreateEmployeeRequest(BaseModel):
    employee_id: str
    user_id: int
    first_name: str
    last_name: str
    position: str
    job_title: str
    organization_id: Optional[int] = None
    department_id: Optional[int] = None
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    status: EmployeeStatus = EmployeeStatus.ACTIVE
    hire_date: date
    base_salary: Optional[Decimal] = None
    working_hours_per_week: int = 40
    personal_email: Optional[str] = None
    personal_phone: Optional[str] = None
    direct_manager_id: Optional[int] = None
    hr_manager_id: Optional[int] = None

# Schema for updating an employee
class UpdateEmployeeRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    nationality: Optional[str] = None
    marital_status: Optional[str] = None
    personal_email: Optional[str] = None
    personal_phone: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    employment_type: Optional[EmploymentType] = None
    position: Optional[str] = None
    job_title: Optional[str] = None
    hire_date: Optional[date] = None
    termination_date: Optional[date] = None
    probation_end_date: Optional[date] = None
    base_salary: Optional[Decimal] = None
    hourly_rate: Optional[Decimal] = None
    currency: Optional[str] = None
    working_hours_per_week: Optional[int] = None
    work_schedule: Optional[str] = None
    timezone: Optional[str] = None
    benefits_package: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_policy_number: Optional[str] = None
    id_document_type: Optional[str] = None
    id_document_number: Optional[str] = None
    id_document_expiry: Optional[date] = None
    department_id: Optional[int] = None
    direct_manager_id: Optional[int] = None
    hr_manager_id: Optional[int] = None
    hr_notes: Optional[str] = None

# Schema for employee response
class EmployeeResponse(BaseModel):
    id: int
    employee_id: str
    user_id: int
    organization_id: int
    department_id: Optional[int]
    first_name: str
    last_name: str
    middle_name: Optional[str]
    date_of_birth: Optional[date]
    gender: Optional[Gender]
    nationality: Optional[str]
    marital_status: Optional[str]
    personal_email: Optional[str]
    personal_phone: Optional[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    emergency_contact_relationship: Optional[str]
    address_line1: Optional[str]
    address_line2: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    postal_code: Optional[str]
    status: EmployeeStatus
    employment_type: EmploymentType
    position: str
    job_title: str
    hire_date: date
    termination_date: Optional[date]
    probation_end_date: Optional[date]
    base_salary: Optional[Decimal]
    hourly_rate: Optional[Decimal]
    currency: Optional[str]
    working_hours_per_week: Optional[int]
    work_schedule: Optional[str]
    timezone: Optional[str]
    benefits_package: Optional[str]
    insurance_provider: Optional[str]
    insurance_policy_number: Optional[str]
    id_document_type: Optional[str]
    id_document_number: Optional[str]
    id_document_expiry: Optional[date]
    hr_manager_id: Optional[int]
    direct_manager_id: Optional[int]
    hr_notes: Optional[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

@router.post("/", response_model=EmployeeResponse)
async def create_employee(
    employee_data: CreateEmployeeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new employee
    """
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create employees"
        )
    
    # Set organization_id based on current user's role
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admin can create employees for any organization
        organization_id = employee_data.organization_id or current_user.organization_id
    else:
        # Other roles can only create employees in their organization
        organization_id = current_user.organization_id
    
    # Check if employee_id already exists within the same organization
    existing_employee = db.query(Employee).filter(
        Employee.employee_id == employee_data.employee_id,
        Employee.organization_id == organization_id
    ).first()
    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee ID already exists in this organization"
        )
    
    # Check if user exists and is not already an employee
    user = db.query(User).filter(User.id == employee_data.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    existing_employee_user = db.query(Employee).filter(
        Employee.user_id == employee_data.user_id,
        Employee.organization_id == organization_id
    ).first()
    if existing_employee_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already an employee in this organization"
        )
    
    # Verify organization exists
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization not found"
        )
    
    # Verify department exists if provided
    if employee_data.department_id:
        department = db.query(Department).filter(Department.id == employee_data.department_id).first()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department not found"
            )
    
    # Create new employee
    new_employee = Employee(
        employee_id=employee_data.employee_id,
        user_id=employee_data.user_id,
        organization_id=organization_id,
        department_id=employee_data.department_id,
        first_name=employee_data.first_name,
        last_name=employee_data.last_name,
        position=employee_data.position,
        job_title=employee_data.job_title,
        employment_type=employee_data.employment_type,
        status=employee_data.status,
        hire_date=employee_data.hire_date,
        base_salary=employee_data.base_salary,
        working_hours_per_week=employee_data.working_hours_per_week,
        personal_email=employee_data.personal_email,
        personal_phone=employee_data.personal_phone,
        direct_manager_id=employee_data.direct_manager_id,
        hr_manager_id=employee_data.hr_manager_id,
        currency="USD"
    )
    
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)
    
    return new_employee

@router.get("/users-without-employee-record")
async def get_users_without_employee_record(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get users who have EMPLOYEE role but no corresponding employee record
    """
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this information"
        )
    
    # Get users with EMPLOYEE role but no employee record
    query = db.query(User).filter(User.role == UserRole.EMPLOYEE)
    
    # Filter by organization if not super admin
    if current_user.role != UserRole.SUPER_ADMIN:
        query = query.filter(User.organization_id == current_user.organization_id)
    
    users_with_employee_role = query.all()
    
    # Filter out users who already have employee records
    users_without_employee_record = []
    for user in users_with_employee_role:
        existing_employee = db.query(Employee).filter(Employee.user_id == user.id).first()
        if not existing_employee:
            users_without_employee_record.append({
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.value,
                "status": user.status.value,
                "organization_id": user.organization_id,
                "created_at": user.created_at
            })
    
    return {
        "users_without_employee_record": users_without_employee_record,
        "count": len(users_without_employee_record)
    }

@router.get("/", response_model=List[EmployeeResponse])
async def get_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    employee_status: Optional[EmployeeStatus] = None,
    employment_type: Optional[EmploymentType] = None,
    organization_id: Optional[int] = None,
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of employees with filtering options
    """
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.DIRECTOR, UserRole.EMPLOYEE, UserRole.PAYROLL]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view employees"
        )
    
    # Build query
    query = db.query(Employee)
    
    # Apply filters based on user role
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admin can see all employees
        pass
    elif current_user.role == UserRole.ORG_ADMIN:
        # Org admin can only see employees in their organization
        query = query.filter(Employee.organization_id == current_user.organization_id)
    elif current_user.role == UserRole.EMPLOYEE:
        # Employees can only see their own record
        employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="Please, use your employee profile")
        query = query.filter(Employee.id == employee.id)
    else:
        # Manager, HR, Director, and other roles can only see employees in their organization
        query = query.filter(Employee.organization_id == current_user.organization_id)
    
    # Apply additional filters
    if employee_status:
        query = query.filter(Employee.status == employee_status)
    if employment_type:
        query = query.filter(Employee.employment_type == employment_type)
    if organization_id and current_user.role == UserRole.SUPER_ADMIN:
        query = query.filter(Employee.organization_id == organization_id)
    if department_id:
        query = query.filter(Employee.department_id == department_id)
    
    # Apply pagination
    employees = query.offset(skip).limit(limit).all()
    
    return employees

@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get specific employee by ID
    """
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.DIRECTOR, UserRole.EMPLOYEE, UserRole.PAYROLL]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view employees"
        )
    
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Check organization access and employee access
    if current_user.role == UserRole.EMPLOYEE:
        # Employees can only view their own record
        current_employee = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        if not current_employee or employee.id != current_employee.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this employee"
            )
    elif current_user.role != UserRole.SUPER_ADMIN:
        if employee.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this employee"
            )
    
    return employee

@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int,
    employee_data: UpdateEmployeeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update employee information
    """
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update employees"
        )
    
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Check organization access
    if current_user.role != UserRole.SUPER_ADMIN:
        if employee.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this employee"
            )
    
    # Update fields
    update_data = employee_data.dict(exclude_unset=True)
    
    # Validate department if provided
    if 'department_id' in update_data and update_data['department_id']:
        department = db.query(Department).filter(
            Department.id == update_data['department_id'],
            Department.organization_id == employee.organization_id
        ).first()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department not found or not in the same organization"
            )
    
    # Update employee
    for field, value in update_data.items():
        setattr(employee, field, value)
    
    db.commit()
    db.refresh(employee)
    
    return employee

@router.put("/{employee_id}/status")
async def update_employee_status(
    employee_id: int,
    new_status: EmployeeStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update employee status
    """
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update employee status"
        )
    
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Check organization access
    if current_user.role != UserRole.SUPER_ADMIN:
        if employee.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this employee"
            )
    
    employee.status = new_status
    db.commit()
    db.refresh(employee)
    
    return {"message": f"Employee status updated to {new_status.value}"}

@router.delete("/{employee_id}")
async def delete_employee(
    employee_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete employee (soft delete by setting status to TERMINATED)
    """
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete employees"
        )
    
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Check organization access
    if current_user.role != UserRole.SUPER_ADMIN:
        if employee.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this employee"
            )
    
    # Soft delete
    employee.status = EmployeeStatus.TERMINATED
    employee.termination_date = date.today()
    db.commit()
    
    return {"message": "Employee deleted successfully"} 