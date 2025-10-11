from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User, UserRole
from app.models.department import Department, DepartmentStatus
from app.models.employee import Employee, EmployeeStatus
from app.models.organization import Organization

router = APIRouter()

# Response models
class DepartmentResponse(BaseModel):
    id: int
    name: str
    code: str
    description: Optional[str]
    status: DepartmentStatus
    organization_id: int
    parent_department_id: Optional[int]
    budget: Optional[int]
    location: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    max_employees: Optional[int]
    allow_remote_work: bool
    working_hours_start: Optional[str]
    working_hours_end: Optional[str]
    employees_count: int
    active_employees_count: int
    created_at: str
    updated_at: Optional[str]
    
    class Config:
        from_attributes = True

class DepartmentSummary(BaseModel):
    total_departments: int
    total_employees: int
    total_budget: int
    average_budget: int

class DepartmentCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    parent_department_id: Optional[int] = None
    budget: Optional[int] = None
    location: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    max_employees: Optional[int] = None
    allow_remote_work: bool = True
    working_hours_start: str = "09:00"
    working_hours_end: str = "17:00"

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    status: Optional[DepartmentStatus] = None
    parent_department_id: Optional[int] = None
    budget: Optional[int] = None
    location: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    max_employees: Optional[int] = None
    allow_remote_work: Optional[bool] = None
    working_hours_start: Optional[str] = None
    working_hours_end: Optional[str] = None

@router.get("/", response_model=List[DepartmentResponse])
async def get_departments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    status_filter: Optional[DepartmentStatus] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all departments for the user's organization"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.DIRECTOR, UserRole.EMPLOYEE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view departments"
        )
    
    # Set organization filter
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admin can see all departments
        query = db.query(Department)
    else:
        # Other roles can only see departments from their organization
        query = db.query(Department).filter(Department.organization_id == current_user.organization_id)
    
    # Apply filters
    if status_filter:
        query = query.filter(Department.status == status_filter)
    
    # Search functionality
    if search:
        query = query.filter(
            (Department.name.ilike(f"%{search}%")) |
            (Department.code.ilike(f"%{search}%")) |
            (Department.description.ilike(f"%{search}%"))
        )
    
    departments = query.offset(skip).limit(limit).all()
    
    # Add employee counts to each department
    result = []
    for dept in departments:
        dept_dict = {
            "id": dept.id,
            "name": dept.name,
            "code": dept.code,
            "description": dept.description,
            "status": dept.status,
            "organization_id": dept.organization_id,
            "parent_department_id": dept.parent_department_id,
            "budget": dept.budget,
            "location": dept.location,
            "contact_email": dept.contact_email,
            "contact_phone": dept.contact_phone,
            "max_employees": dept.max_employees,
            "allow_remote_work": dept.allow_remote_work,
            "working_hours_start": dept.working_hours_start,
            "working_hours_end": dept.working_hours_end,
            "employees_count": dept.active_employees_count,
            "active_employees_count": dept.active_employees_count,
            "created_at": dept.created_at.isoformat() if dept.created_at else "",
            "updated_at": dept.updated_at.isoformat() if dept.updated_at else None
        }
        result.append(dept_dict)
    
    return result

@router.get("/summary", response_model=DepartmentSummary)
async def get_departments_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get departments summary statistics"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.DIRECTOR, UserRole.EMPLOYEE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view departments summary"
        )
    
    # Set organization filter
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admin can see all departments
        query = db.query(Department)
    else:
        # Other roles can only see departments from their organization
        query = db.query(Department).filter(Department.organization_id == current_user.organization_id)
    
    # Get active departments
    active_departments = query.filter(Department.status == DepartmentStatus.ACTIVE).all()
    
    total_departments = len(active_departments)
    total_employees = sum(dept.active_employees_count for dept in active_departments)
    total_budget = sum(dept.budget or 0 for dept in active_departments)
    average_budget = total_budget // total_departments if total_departments > 0 else 0
    
    return DepartmentSummary(
        total_departments=total_departments,
        total_employees=total_employees,
        total_budget=total_budget,
        average_budget=average_budget
    )

@router.get("/{department_id}", response_model=DepartmentResponse)
async def get_department(
    department_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific department by ID"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.DIRECTOR, UserRole.EMPLOYEE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view departments"
        )
    
    # Set organization filter
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admin can see all departments
        department = db.query(Department).filter(Department.id == department_id).first()
    else:
        # Other roles can only see departments from their organization
        department = db.query(Department).filter(
            and_(
                Department.id == department_id,
                Department.organization_id == current_user.organization_id
            )
        ).first()
    
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    return DepartmentResponse(
        id=department.id,
        name=department.name,
        code=department.code,
        description=department.description,
        status=department.status,
        organization_id=department.organization_id,
        parent_department_id=department.parent_department_id,
        budget=department.budget,
        location=department.location,
        contact_email=department.contact_email,
        contact_phone=department.contact_phone,
        max_employees=department.max_employees,
        allow_remote_work=department.allow_remote_work,
        working_hours_start=department.working_hours_start,
        working_hours_end=department.working_hours_end,
        employees_count=department.active_employees_count,
        active_employees_count=department.active_employees_count,
        created_at=department.created_at.isoformat() if department.created_at else "",
        updated_at=department.updated_at.isoformat() if department.updated_at else None
    )

@router.post("/", response_model=DepartmentResponse)
async def create_department(
    department_data: DepartmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new department"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create departments"
        )
    
    # Check if department code already exists in the organization
    existing_dept = db.query(Department).filter(
        and_(
            Department.code == department_data.code,
            Department.organization_id == current_user.organization_id
        )
    ).first()
    
    if existing_dept:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department code already exists in this organization"
        )
    
    # Create new department
    department = Department(
        name=department_data.name,
        code=department_data.code,
        description=department_data.description,
        organization_id=current_user.organization_id,
        parent_department_id=department_data.parent_department_id,
        budget=department_data.budget,
        location=department_data.location,
        contact_email=department_data.contact_email,
        contact_phone=department_data.contact_phone,
        max_employees=department_data.max_employees,
        allow_remote_work=department_data.allow_remote_work,
        working_hours_start=department_data.working_hours_start,
        working_hours_end=department_data.working_hours_end
    )
    
    db.add(department)
    db.commit()
    db.refresh(department)
    
    return DepartmentResponse(
        id=department.id,
        name=department.name,
        code=department.code,
        description=department.description,
        status=department.status,
        organization_id=department.organization_id,
        parent_department_id=department.parent_department_id,
        budget=department.budget,
        location=department.location,
        contact_email=department.contact_email,
        contact_phone=department.contact_phone,
        max_employees=department.max_employees,
        allow_remote_work=department.allow_remote_work,
        working_hours_start=department.working_hours_start,
        working_hours_end=department.working_hours_end,
        employees_count=department.active_employees_count,
        active_employees_count=department.active_employees_count,
        created_at=department.created_at.isoformat() if department.created_at else "",
        updated_at=department.updated_at.isoformat() if department.updated_at else None
    )

@router.put("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: int,
    department_data: DepartmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a department"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update departments"
        )
    
    # Find department
    if current_user.role == UserRole.SUPER_ADMIN:
        department = db.query(Department).filter(Department.id == department_id).first()
    else:
        department = db.query(Department).filter(
            and_(
                Department.id == department_id,
                Department.organization_id == current_user.organization_id
            )
        ).first()
    
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    # Check if code is being changed and if it conflicts
    if department_data.code and department_data.code != department.code:
        existing_dept = db.query(Department).filter(
            and_(
                Department.code == department_data.code,
                Department.organization_id == current_user.organization_id,
                Department.id != department_id
            )
        ).first()
        
        if existing_dept:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department code already exists in this organization"
            )
    
    # Update department
    update_data = department_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(department, field, value)
    
    db.commit()
    db.refresh(department)
    
    return DepartmentResponse(
        id=department.id,
        name=department.name,
        code=department.code,
        description=department.description,
        status=department.status,
        organization_id=department.organization_id,
        parent_department_id=department.parent_department_id,
        budget=department.budget,
        location=department.location,
        contact_email=department.contact_email,
        contact_phone=department.contact_phone,
        max_employees=department.max_employees,
        allow_remote_work=department.allow_remote_work,
        working_hours_start=department.working_hours_start,
        working_hours_end=department.working_hours_end,
        employees_count=department.active_employees_count,
        active_employees_count=department.active_employees_count,
        created_at=department.created_at.isoformat() if department.created_at else "",
        updated_at=department.updated_at.isoformat() if department.updated_at else None
    )

@router.delete("/{department_id}")
async def delete_department(
    department_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a department (soft delete by setting status to INACTIVE)"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete departments"
        )
    
    # Find department
    if current_user.role == UserRole.SUPER_ADMIN:
        department = db.query(Department).filter(Department.id == department_id).first()
    else:
        department = db.query(Department).filter(
            and_(
                Department.id == department_id,
                Department.organization_id == current_user.organization_id
            )
        ).first()
    
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    # Check if department has active employees
    if department.active_employees_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete department with active employees. Please reassign employees first."
        )
    
    # Soft delete by setting status to INACTIVE
    department.status = DepartmentStatus.INACTIVE
    db.commit()
    
    return {"message": "Department deleted successfully"}
