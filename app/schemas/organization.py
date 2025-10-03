from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.models.organization import OrganizationStatus


class OrganizationBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    status: OrganizationStatus = OrganizationStatus.ACTIVE
    
    # Contact Information
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    
    # Address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    
    # Organization Details
    industry: Optional[str] = None
    size: Optional[str] = None
    founded_year: Optional[int] = None
    tax_id: Optional[str] = None
    
    # Settings
    timezone: str = "UTC"
    currency: str = "USD"
    language: str = "en"
    
    # Features
    enable_attendance: bool = True
    enable_leave_management: bool = True
    enable_payroll: bool = True
    enable_training: bool = True
    enable_expenses: bool = True
    enable_documents: bool = True


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    status: Optional[OrganizationStatus] = None
    
    # Contact Information
    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    
    # Address
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    
    # Organization Details
    industry: Optional[str] = None
    size: Optional[str] = None
    founded_year: Optional[int] = None
    tax_id: Optional[str] = None
    
    # Settings
    timezone: Optional[str] = None
    currency: Optional[str] = None
    language: Optional[str] = None
    
    # Features
    enable_attendance: Optional[bool] = None
    enable_leave_management: Optional[bool] = None
    enable_payroll: Optional[bool] = None
    enable_training: Optional[bool] = None
    enable_expenses: Optional[bool] = None
    enable_documents: Optional[bool] = None


class OrganizationResponse(OrganizationBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class OrganizationList(BaseModel):
    organizations: list[OrganizationResponse]
    total: int
    page: int
    size: int 