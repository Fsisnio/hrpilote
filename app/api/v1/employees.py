from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel
from beanie import PydanticObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.mongo import get_mongo_db
from app.api.v1.auth import get_current_user
from app.models.enums import (
    UserRole,
    EmployeeStatus,
    EmploymentType,
    Gender,
)
from app.models.mongo_models import (
    UserDocument,
    EmployeeDocument,
    DepartmentDocument,
    OrganizationDocument,
)

router = APIRouter()

# Schema for creating a new employee
class CreateEmployeeRequest(BaseModel):
    employee_id: str
    user_id: str
    first_name: str
    last_name: str
    position: str
    job_title: str
    organization_id: Optional[str] = None
    department_id: Optional[str] = None
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    status: EmployeeStatus = EmployeeStatus.ACTIVE
    hire_date: date
    base_salary: Optional[Decimal] = None
    working_hours_per_week: int = 40
    personal_email: Optional[str] = None
    personal_phone: Optional[str] = None
    direct_manager_id: Optional[str] = None
    hr_manager_id: Optional[str] = None

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
    department_id: Optional[str] = None
    direct_manager_id: Optional[str] = None
    hr_manager_id: Optional[str] = None
    hr_notes: Optional[str] = None

# Schema for employee response
class EmployeeResponse(BaseModel):
    id: str
    employee_id: str
    user_id: str
    organization_id: str
    department_id: Optional[str]
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
    hr_manager_id: Optional[str]
    direct_manager_id: Optional[str]
    hr_notes: Optional[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

def _employee_to_response(employee: EmployeeDocument) -> EmployeeResponse:
    return EmployeeResponse(
        id=str(employee.id),
        employee_id=employee.employee_id,
        user_id=str(employee.user_id),
        organization_id=str(employee.organization_id),
        department_id=str(employee.department_id) if employee.department_id else None,
        first_name=employee.first_name,
        last_name=employee.last_name,
        middle_name=employee.middle_name,
        date_of_birth=employee.date_of_birth,
        gender=employee.gender,
        nationality=employee.nationality,
        marital_status=employee.marital_status,
        personal_email=employee.personal_email,
        personal_phone=employee.personal_phone,
        emergency_contact_name=employee.emergency_contact_name,
        emergency_contact_phone=employee.emergency_contact_phone,
        emergency_contact_relationship=employee.emergency_contact_relationship,
        address_line1=employee.address_line1,
        address_line2=employee.address_line2,
        city=employee.city,
        state=employee.state,
        country=employee.country,
        postal_code=employee.postal_code,
        status=employee.status,
        employment_type=employee.employment_type,
        position=employee.position,
        job_title=employee.job_title,
        hire_date=employee.hire_date,
        termination_date=employee.termination_date,
        probation_end_date=employee.probation_end_date,
        base_salary=employee.base_salary,
        hourly_rate=employee.hourly_rate,
        currency=employee.currency,
        working_hours_per_week=employee.working_hours_per_week,
        work_schedule=employee.work_schedule,
        timezone=employee.timezone,
        benefits_package=employee.benefits_package,
        insurance_provider=employee.insurance_provider,
        insurance_policy_number=employee.insurance_policy_number,
        id_document_type=employee.id_document_type,
        id_document_number=employee.id_document_number,
        id_document_expiry=employee.id_document_expiry,
        hr_manager_id=str(employee.hr_manager_id) if employee.hr_manager_id else None,
        direct_manager_id=str(employee.direct_manager_id) if employee.direct_manager_id else None,
        hr_notes=employee.hr_notes,
        created_at=employee.created_at,
        updated_at=employee.updated_at,
    )


@router.post("/", response_model=EmployeeResponse)
async def create_employee(
    employee_data: CreateEmployeeRequest,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
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
        target_org_id = employee_data.organization_id or (str(current_user.organization_id) if current_user.organization_id else None)
    else:
        target_org_id = str(current_user.organization_id) if current_user.organization_id else None

    if not target_org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization context missing",
        )

    try:
        organization_obj_id = PydanticObjectId(target_org_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid organization ID",
        )
    
    # Check if employee_id already exists within the same organization
    existing_employee = await EmployeeDocument.find_one(
        {
            "employee_id": employee_data.employee_id,
            "organization_id": organization_obj_id,
        }
    )
    if existing_employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee ID already exists in this organization"
        )
    
    # Check if user exists and is not already an employee
    try:
        user_obj_id = PydanticObjectId(employee_data.user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")

    user = await UserDocument.get(user_obj_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    existing_employee_user = await EmployeeDocument.find_one(
        {
            "user_id": user_obj_id,
            "organization_id": organization_obj_id,
        }
    )
    if existing_employee_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already an employee in this organization"
        )
    
    # Verify organization exists
    organization = await OrganizationDocument.get(organization_obj_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization not found"
        )
    
    # Verify department exists if provided
    department_id = None
    if employee_data.department_id:
        try:
            department_obj_id = PydanticObjectId(employee_data.department_id)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid department ID")

        department = await DepartmentDocument.get(department_obj_id)
        if not department:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department not found"
            )
        if department.organization_id != organization_obj_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department not in the same organization",
            )
        department_id = department_obj_id
    
    # Create new employee
    direct_manager_id = None
    if employee_data.direct_manager_id:
        try:
            direct_manager_id = PydanticObjectId(employee_data.direct_manager_id)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid direct manager ID")

    hr_manager_id = None
    if employee_data.hr_manager_id:
        try:
            hr_manager_id = PydanticObjectId(employee_data.hr_manager_id)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid HR manager ID")

    new_employee = EmployeeDocument(
        employee_id=employee_data.employee_id,
        user_id=user_obj_id,
        organization_id=organization_obj_id,
        department_id=department_id,
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
        direct_manager_id=direct_manager_id,
        hr_manager_id=hr_manager_id,
        currency="USD",
    )

    await new_employee.insert()

    return _employee_to_response(new_employee)

@router.get("/users-without-employee-record")
async def get_users_without_employee_record(
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
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
    user_query = UserDocument.find(UserDocument.role == UserRole.EMPLOYEE)

    if current_user.role != UserRole.SUPER_ADMIN:
        user_query = user_query.find(UserDocument.organization_id == current_user.organization_id)

    users_with_employee_role = await user_query.to_list()

    users_without_employee_record = []
    for user in users_with_employee_role:
        existing_employee = await EmployeeDocument.find_one(EmployeeDocument.user_id == user.id)
        if not existing_employee:
            users_without_employee_record.append({
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.value,
                "status": user.status.value,
                "organization_id": str(user.organization_id) if user.organization_id else None,
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
    organization_id: Optional[str] = None,
    department_id: Optional[str] = None,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
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
    query = {}

    if current_user.role == UserRole.SUPER_ADMIN:
        pass
    elif current_user.role == UserRole.EMPLOYEE:
        employee = await EmployeeDocument.find_one(EmployeeDocument.user_id == current_user.id)
        if not employee:
            raise HTTPException(status_code=404, detail="Use your employee credential to have access to this feature")
        query["_id"] = employee.id
    else:
        query["organization_id"] = current_user.organization_id

    if employee_status:
        query["status"] = employee_status
    if employment_type:
        query["employment_type"] = employment_type
    if organization_id and current_user.role == UserRole.SUPER_ADMIN:
        try:
            query["organization_id"] = PydanticObjectId(organization_id)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid organization ID")
    if department_id:
        try:
            query["department_id"] = PydanticObjectId(department_id)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid department ID")

    employees = await EmployeeDocument.find(query).skip(skip).limit(limit).to_list()

    return [_employee_to_response(emp) for emp in employees]

@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: str,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
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
    
    try:
        doc_id = PydanticObjectId(employee_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    employee = await EmployeeDocument.get(doc_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )
    
    # Check organization access and employee access
    if current_user.role == UserRole.EMPLOYEE:
        current_employee = await EmployeeDocument.find_one(EmployeeDocument.user_id == current_user.id)
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
    
    return _employee_to_response(employee)

@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: str,
    employee_data: UpdateEmployeeRequest,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
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
    
    try:
        doc_id = PydanticObjectId(employee_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    employee = await EmployeeDocument.get(doc_id)
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

    if 'department_id' in update_data and update_data['department_id']:
        try:
            department_obj_id = PydanticObjectId(update_data['department_id'])
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid department ID")

        department = await DepartmentDocument.get(department_obj_id)
        if not department or department.organization_id != employee.organization_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department not found or not in the same organization"
            )
        update_data['department_id'] = department_obj_id

    for field, value in update_data.items():
        setattr(employee, field, value)

    await employee.save()

    return _employee_to_response(employee)

@router.put("/{employee_id}/status")
async def update_employee_status(
    employee_id: str,
    new_status: EmployeeStatus,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
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
    
    try:
        doc_id = PydanticObjectId(employee_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    employee = await EmployeeDocument.get(doc_id)
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
    await employee.save()
    
    return {"message": f"Employee status updated to {new_status.value}"}

@router.delete("/{employee_id}")
async def delete_employee(
    employee_id: str,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
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
    
    try:
        doc_id = PydanticObjectId(employee_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    employee = await EmployeeDocument.get(doc_id)
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
    await employee.save()
    
    return {"message": "Employee deleted successfully"} 