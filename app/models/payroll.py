from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, Enum, Date, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
from enum import Enum as PyEnum
from decimal import Decimal
from app.core.database import Base


class PayPeriodType(PyEnum):
    WEEKLY = "WEEKLY"
    BI_WEEKLY = "BI_WEEKLY"
    SEMI_MONTHLY = "SEMI_MONTHLY"
    MONTHLY = "MONTHLY"


class PayrollStatus(PyEnum):
    DRAFT = "DRAFT"
    PROCESSING = "PROCESSING"
    APPROVED = "APPROVED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class SalaryComponentType(PyEnum):
    BASIC = "BASIC"
    ALLOWANCE = "ALLOWANCE"
    BONUS = "BONUS"
    OVERTIME = "OVERTIME"
    COMMISSION = "COMMISSION"
    
    # Additional Allocation Types
    HOUSING_ALLOWANCE = "HOUSING_ALLOWANCE"
    TRANSPORT_ALLOWANCE = "TRANSPORT_ALLOWANCE"
    MEDICAL_ALLOWANCE = "MEDICAL_ALLOWANCE"
    MEAL_ALLOWANCE = "MEAL_ALLOWANCE"
    
    # Deduction Types
    DEDUCTION = "DEDUCTION"
    TAX = "TAX"
    INSURANCE = "INSURANCE"
    PENSION = "PENSION"
    
    # Additional Deduction Types
    LOAN_DEDUCTION = "LOAN_DEDUCTION"
    ADVANCE_DEDUCTION = "ADVANCE_DEDUCTION"
    UNIFORM_DEDUCTION = "UNIFORM_DEDUCTION"
    PARKING_DEDUCTION = "PARKING_DEDUCTION"
    LATE_PENALTY = "LATE_PENALTY"
    
    OTHER = "OTHER"


class PayrollPeriod(Base):
    __tablename__ = "payroll_periods"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Period details
    name = Column(String(100), nullable=False)
    period_type = Column(Enum(PayPeriodType), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Processing dates
    pay_date = Column(Date, nullable=False)
    processing_date = Column(Date, nullable=True)
    
    # Status
    status = Column(Enum(PayrollStatus), default=PayrollStatus.DRAFT)
    is_active = Column(Boolean, default=True)
    
    # Totals
    total_gross_pay = Column(Numeric(15, 2), default=0)
    total_net_pay = Column(Numeric(15, 2), default=0)
    total_deductions = Column(Numeric(15, 2), default=0)
    total_taxes = Column(Numeric(15, 2), default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")
    payroll_records = relationship("PayrollRecord", back_populates="payroll_period")


class PayrollRecord(Base):
    __tablename__ = "payroll_records"
    
    id = Column(Integer, primary_key=True, index=True)
    payroll_period_id = Column(Integer, ForeignKey("payroll_periods.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Basic salary info
    base_salary = Column(Numeric(15, 2), nullable=False)
    basic_salary = Column(Numeric(15, 2), default=0)
    
    # Earnings
    total_earnings = Column(Numeric(15, 2), default=0)
    total_allowances = Column(Numeric(15, 2), default=0)
    total_bonuses = Column(Numeric(15, 2), default=0)
    total_overtime = Column(Numeric(15, 2), default=0)
    total_commission = Column(Numeric(15, 2), default=0)
    
    # Deductions
    total_deductions = Column(Numeric(15, 2), default=0)
    total_taxes = Column(Numeric(15, 2), default=0)
    total_insurance = Column(Numeric(15, 2), default=0)
    total_pension = Column(Numeric(15, 2), default=0)
    
    # Final amounts
    gross_pay = Column(Numeric(15, 2), default=0)
    net_pay = Column(Numeric(15, 2), default=0)
    
    # Work hours
    regular_hours = Column(Float, default=0.0)
    overtime_hours = Column(Float, default=0.0)
    total_hours = Column(Float, default=0.0)
    
    # Status
    status = Column(Enum(PayrollStatus), default=PayrollStatus.DRAFT)
    is_approved = Column(Boolean, default=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    payroll_period = relationship("PayrollPeriod", back_populates="payroll_records")
    employee = relationship("Employee", overlaps="payroll_records")
    organization = relationship("Organization")
    approver = relationship("User", foreign_keys=[approved_by])
    components = relationship("PayrollComponent", back_populates="payroll_record", cascade="all, delete-orphan")


class PayrollComponent(Base):
    __tablename__ = "payroll_components"
    
    id = Column(Integer, primary_key=True, index=True)
    payroll_record_id = Column(Integer, ForeignKey("payroll_records.id"), nullable=False)
    
    # Component details
    name = Column(String(100), nullable=False)
    component_type = Column(Enum(SalaryComponentType), nullable=False)
    description = Column(Text, nullable=True)
    
    # Amounts
    amount = Column(Numeric(15, 2), nullable=False)
    percentage = Column(Float, default=0.0)
    is_taxable = Column(Boolean, default=True)
    
    # Calculation basis
    calculation_basis = Column(String(50), nullable=True)  # BASIC, GROSS, etc.
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    payroll_record = relationship("PayrollRecord", back_populates="components")


class SalaryStructure(Base):
    __tablename__ = "salary_structures"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Structure details
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Basic salary
    basic_salary_percentage = Column(Float, default=60.0)  # Percentage of total CTC
    
    # Allowances
    hra_percentage = Column(Float, default=0.0)
    da_percentage = Column(Float, default=0.0)
    conveyance_allowance = Column(Numeric(15, 2), default=0)
    medical_allowance = Column(Numeric(15, 2), default=0)
    special_allowance = Column(Numeric(15, 2), default=0)
    
    # Benefits
    provident_fund_percentage = Column(Float, default=12.0)
    esi_percentage = Column(Float, default=0.0)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")


class PayrollSettings(Base):
    __tablename__ = "payroll_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, unique=True)
    
    # Payroll cycle settings
    payroll_cycle = Column(String(50), default="Monthly")  # Monthly, Bi-weekly, Weekly
    pay_day = Column(String(100), default="Last day of month")  # Last day of month, 1st of month, etc.
    
    # Currency settings
    currency = Column(String(100), default="USD ($)")  # USD ($), EUR (€), MAD (د.م.) - Moroccan Dirham, etc.
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")


class TaxSlab(Base):
    __tablename__ = "tax_slabs"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Slab details
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Income range
    min_income = Column(Numeric(15, 2), nullable=False)
    max_income = Column(Numeric(15, 2), nullable=True)
    
    # Tax rates
    tax_percentage = Column(Float, nullable=False)
    surcharge_percentage = Column(Float, default=0.0)
    cess_percentage = Column(Float, default=0.0)
    
    # Year
    tax_year = Column(Integer, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")


class Benefit(Base):
    __tablename__ = "benefits"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Benefit details
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    benefit_type = Column(Enum(SalaryComponentType), nullable=False)
    
    # Amount/Percentage
    amount = Column(Numeric(15, 2), default=0)
    percentage = Column(Float, default=0.0)
    
    # Eligibility
    is_mandatory = Column(Boolean, default=False)
    min_service_months = Column(Integer, default=0)
    
    # Tax implications
    is_taxable = Column(Boolean, default=True)
    tax_exemption_limit = Column(Numeric(15, 2), default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization") 