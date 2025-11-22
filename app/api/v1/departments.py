from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from pydantic import BaseModel
from beanie import PydanticObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.mongo import get_mongo_db
from app.api.v1.auth import get_current_user
from app.models.enums import UserRole, DepartmentStatus, EmployeeStatus
from app.models.mongo_models import DepartmentDocument, EmployeeDocument, UserDocument

router = APIRouter()

# Response models
class DepartmentResponse(BaseModel):
    id: str
    name: str
    code: str
    description: Optional[str]
    status: DepartmentStatus
    organization_id: str
    parent_department_id: Optional[str]
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
    parent_department_id: Optional[str] = None
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
    parent_department_id: Optional[str] = None
    budget: Optional[int] = None
    location: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    max_employees: Optional[int] = None
    allow_remote_work: Optional[bool] = None
    working_hours_start: Optional[str] = None
    working_hours_end: Optional[str] = None

def _department_to_response(dept: DepartmentDocument, employees_count: int = 0, active_employees_count: int = 0) -> DepartmentResponse:
    return DepartmentResponse(
        id=str(dept.id),
        name=dept.name,
        code=dept.code,
        description=dept.description,
        status=dept.status,
        organization_id=str(dept.organization_id),
        parent_department_id=str(dept.parent_department_id) if dept.parent_department_id else None,
        budget=dept.budget,
        location=dept.location,
        contact_email=dept.contact_email,
        contact_phone=dept.contact_phone,
        max_employees=dept.max_employees,
        allow_remote_work=dept.allow_remote_work,
        working_hours_start=dept.working_hours_start,
        working_hours_end=dept.working_hours_end,
        employees_count=employees_count,
        active_employees_count=active_employees_count,
        created_at=dept.created_at.isoformat() if dept.created_at else "",
        updated_at=dept.updated_at.isoformat() if dept.updated_at else None,
    )


@router.get("/", response_model=List[DepartmentResponse])
async def get_departments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    status_filter: Optional[DepartmentStatus] = None,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get all departments for the user's organization"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.DIRECTOR, UserRole.EMPLOYEE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view departments"
        )
    
    query = {}
    if current_user.role != UserRole.SUPER_ADMIN:
        query["organization_id"] = current_user.organization_id

    if status_filter:
        query["status"] = status_filter

    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]

    departments = await DepartmentDocument.find(query).skip(skip).limit(limit).to_list()

    department_ids = [dept.id for dept in departments]
    employee_counts = {}
    if department_ids:
        pipeline = [
            {"$match": {"department_id": {"$in": department_ids}}},
            {
                "$group": {
                    "_id": "$department_id",
                    "total": {"$sum": 1},
                    "active": {
                        "$sum": {
                            "$cond": [{"$eq": ["$status", EmployeeStatus.ACTIVE.value]}, 1, 0]
                        }
                    },
                }
            },
        ]
        collection_name = EmployeeDocument.Settings.name
        async for doc in db[collection_name].aggregate(pipeline):
            employee_counts[doc["_id"]] = (doc["total"], doc["active"])

    result = []
    for dept in departments:
        total, active = employee_counts.get(dept.id, (0, 0))
        result.append(_department_to_response(dept, total, active))

    return result

@router.get("/summary", response_model=DepartmentSummary)
async def get_departments_summary(
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get departments summary statistics"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.DIRECTOR, UserRole.EMPLOYEE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view departments summary"
        )
    
    # Set organization filter
    query = {"status": DepartmentStatus.ACTIVE}
    if current_user.role != UserRole.SUPER_ADMIN:
        query["organization_id"] = current_user.organization_id

    active_departments = await DepartmentDocument.find(query).to_list()

    total_departments = len(active_departments)
    department_ids = [dept.id for dept in active_departments]

    total_employees = 0
    if department_ids:
        total_employees = await EmployeeDocument.find(
            {
                "department_id": {"$in": department_ids},
                "status": EmployeeStatus.ACTIVE,
            }
        ).count()

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
    department_id: str,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get a specific department by ID"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.DIRECTOR, UserRole.EMPLOYEE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view departments"
        )
    
    # Set organization filter
    try:
        dept_id = PydanticObjectId(department_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    department = await DepartmentDocument.get(dept_id)

    if current_user.role != UserRole.SUPER_ADMIN:
        if not department or department.organization_id != current_user.organization_id:
            department = None
    
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    total_employees = await EmployeeDocument.find(EmployeeDocument.department_id == department.id).count()
    active_employees = await EmployeeDocument.find(
        {
            "department_id": department.id,
            "status": EmployeeStatus.ACTIVE,
        }
    ).count()

    return _department_to_response(department, total_employees, active_employees)

@router.post("/", response_model=DepartmentResponse)
async def create_department(
    department_data: DepartmentCreate,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Create a new department"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create departments"
        )
    
    # Check if department code already exists in the organization
    existing_dept = await DepartmentDocument.find_one(
        {
            "code": department_data.code,
            "organization_id": current_user.organization_id,
        }
    )
    
    if existing_dept:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department code already exists in this organization"
        )
    
    # Create new department
    parent_id = None
    if department_data.parent_department_id:
        try:
            parent_id = PydanticObjectId(department_data.parent_department_id)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid parent department ID")

        parent = await DepartmentDocument.get(parent_id)
        if not parent or parent.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent department not found in this organization",
            )

    department = DepartmentDocument(
        name=department_data.name,
        code=department_data.code,
        description=department_data.description,
        organization_id=current_user.organization_id,
        parent_department_id=parent_id,
        budget=department_data.budget,
        location=department_data.location,
        contact_email=department_data.contact_email,
        contact_phone=department_data.contact_phone,
        max_employees=department_data.max_employees,
        allow_remote_work=department_data.allow_remote_work,
        working_hours_start=department_data.working_hours_start,
        working_hours_end=department_data.working_hours_end,
    )

    await department.insert()

    return _department_to_response(department, 0, 0)

@router.put("/{department_id}", response_model=DepartmentResponse)
async def update_department(
    department_id: str,
    department_data: DepartmentUpdate,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Update a department"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update departments"
        )
    
    # Find department
    try:
        dept_id = PydanticObjectId(department_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    department = await DepartmentDocument.get(dept_id)
    if department and current_user.role != UserRole.SUPER_ADMIN:
        if department.organization_id != current_user.organization_id:
            department = None
    
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    # Check if code is being changed and if it conflicts
    if department_data.code and department_data.code != department.code:
        existing_dept = await DepartmentDocument.find_one(
            {
                "code": department_data.code,
                "organization_id": department.organization_id,
                "_id": {"$ne": department.id},
            }
        )
        
        if existing_dept:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department code already exists in this organization"
            )
    
    # Update department
    update_data = department_data.dict(exclude_unset=True)

    if "parent_department_id" in update_data and update_data["parent_department_id"]:
        try:
            parent_id = PydanticObjectId(update_data["parent_department_id"])
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid parent department ID")

        parent = await DepartmentDocument.get(parent_id)
        if not parent or parent.organization_id != department.organization_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent department not found in this organization",
            )
        update_data["parent_department_id"] = parent_id

    for field, value in update_data.items():
        setattr(department, field, value)

    await department.save()

    total_employees = await EmployeeDocument.find(EmployeeDocument.department_id == department.id).count()
    active_employees = await EmployeeDocument.find(
        {"department_id": department.id, "status": EmployeeStatus.ACTIVE}
    ).count()

    return _department_to_response(department, total_employees, active_employees)

@router.delete("/{department_id}")
async def delete_department(
    department_id: str,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Delete a department (soft delete by setting status to INACTIVE)"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete departments"
        )
    
    # Find department
    try:
        dept_id = PydanticObjectId(department_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    department = await DepartmentDocument.get(dept_id)

    if department and current_user.role != UserRole.SUPER_ADMIN:
        if department.organization_id != current_user.organization_id:
            department = None
    
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    # Check if department has active employees
    active_employees_count = await EmployeeDocument.find(
        {"department_id": department.id, "status": EmployeeStatus.ACTIVE}
    ).count()
    
    if active_employees_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete department with active employees. Please reassign employees first."
        )
    
    # Soft delete by setting status to INACTIVE
    department.status = DepartmentStatus.INACTIVE
    await department.save()
    
    return {"message": "Department deleted successfully"}
