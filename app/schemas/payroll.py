from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime
from app.models.payroll import PayrollStatus


class PayrollRecordCreate(BaseModel):
    """Schema for creating payroll records"""
    employee_id: int = Field(..., description="Employee ID")
    basic_salary: float = Field(..., ge=0, description="Basic salary amount")
    status: PayrollStatus = Field(default=PayrollStatus.PROCESSING, description="Payroll status")
    
    # Allowance fields
    housing_allowance: Optional[float] = Field(0, ge=0, description="Housing allowance amount")
    transport_allowance: Optional[float] = Field(0, ge=0, description="Transport allowance amount")
    medical_allowance: Optional[float] = Field(0, ge=0, description="Medical allowance amount")
    meal_allowance: Optional[float] = Field(0, ge=0, description="Meal allowance amount")
    
    # Deduction fields
    loan_deduction: Optional[float] = Field(0, ge=0, description="Loan deduction amount")
    advance_deduction: Optional[float] = Field(0, ge=0, description="Advance deduction amount")
    uniform_deduction: Optional[float] = Field(0, ge=0, description="Uniform deduction amount")
    parking_deduction: Optional[float] = Field(0, ge=0, description="Parking deduction amount")
    late_penalty: Optional[float] = Field(0, ge=0, description="Late penalty amount")
    
    # Additional fields
    notes: Optional[str] = Field(None, description="Additional notes")

    class Config:
        from_attributes = True


class PayrollRecordUpdate(BaseModel):
    """Schema for updating payroll records"""
    basic_salary: Optional[float] = Field(None, ge=0, description="Basic salary amount")
    status: Optional[PayrollStatus] = Field(None, description="Payroll status")
    
    # Allowance fields
    housing_allowance: Optional[float] = Field(None, ge=0, description="Housing allowance amount")
    transport_allowance: Optional[float] = Field(None, ge=0, description="Transport allowance amount")
    medical_allowance: Optional[float] = Field(None, ge=0, description="Medical allowance amount")
    meal_allowance: Optional[float] = Field(None, ge=0, description="Meal allowance amount")
    
    # Deduction fields
    loan_deduction: Optional[float] = Field(None, ge=0, description="Loan deduction amount")
    advance_deduction: Optional[float] = Field(None, ge=0, description="Advance deduction amount")
    uniform_deduction: Optional[float] = Field(None, ge=0, description="Uniform deduction amount")
    parking_deduction: Optional[float] = Field(None, ge=0, description="Parking deduction amount")
    late_penalty: Optional[float] = Field(None, ge=0, description="Late penalty amount")

    class Config:
        from_attributes = True


class PayrollSettingsBase(BaseModel):
    """Base schema for payroll settings"""
    payroll_cycle: str = Field(..., description="Payroll cycle (Monthly, Bi-weekly, Weekly)")
    pay_day: str = Field(..., description="Pay day setting")
    currency: str = Field(..., description="Currency setting")


class PayrollSettingsCreate(PayrollSettingsBase):
    """Schema for creating payroll settings"""
    pass


class PayrollSettingsUpdate(BaseModel):
    """Schema for updating payroll settings"""
    payroll_cycle: Optional[str] = Field(None, description="Payroll cycle")
    pay_day: Optional[str] = Field(None, description="Pay day setting")
    currency: Optional[str] = Field(None, description="Currency setting")


class PayrollSettingsResponse(PayrollSettingsBase):
    """Schema for payroll settings response"""
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
