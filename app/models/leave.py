from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, Enum, Date, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
from enum import Enum as PyEnum
from app.core.database import Base


class LeaveType(PyEnum):
    ANNUAL = "ANNUAL"
    SICK = "SICK"
    PERSONAL = "PERSONAL"
    MATERNITY = "MATERNITY"
    PATERNITY = "PATERNITY"
    BEREAVEMENT = "BEREAVEMENT"
    UNPAID = "UNPAID"
    COMPENSATORY = "COMPENSATORY"
    STUDY = "STUDY"
    OTHER = "OTHER"


class LeaveStatus(PyEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Request details
    leave_type = Column(Enum(LeaveType), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    
    # Duration
    total_days = Column(Float, default=0.0)
    total_hours = Column(Float, default=0.0)
    is_half_day = Column(Boolean, default=False)
    
    # Status and approval
    status = Column(Enum(LeaveStatus), default=LeaveStatus.PENDING)
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Reason and notes
    reason = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Emergency contact
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    
    # Handover details
    handover_to = Column(Integer, ForeignKey("employees.id"), nullable=True)
    handover_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    employee = relationship("Employee", foreign_keys=[employee_id], overlaps="leave_requests")
    organization = relationship("Organization")
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by])
    handover_employee = relationship("Employee", foreign_keys=[handover_to])


class LeaveBalance(Base):
    __tablename__ = "leave_balances"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    leave_type = Column(Enum(LeaveType), nullable=False)
    year = Column(Integer, nullable=False)
    
    # Balance details
    total_entitled = Column(Float, default=0.0)
    total_taken = Column(Float, default=0.0)
    total_remaining = Column(Float, default=0.0)
    total_carried_forward = Column(Float, default=0.0)
    
    # Policy details
    max_carry_forward = Column(Float, default=0.0)
    expires_at = Column(Date, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    employee = relationship("Employee")
    organization = relationship("Organization")


class LeavePolicy(Base):
    __tablename__ = "leave_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    leave_type = Column(Enum(LeaveType), nullable=False)
    
    # Policy details
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Entitlement
    days_per_year = Column(Float, default=0.0)
    hours_per_year = Column(Float, default=0.0)
    
    # Eligibility
    min_service_months = Column(Integer, default=0)
    max_consecutive_days = Column(Integer, default=0)
    min_notice_days = Column(Integer, default=0)
    
    # Approval settings
    requires_approval = Column(Boolean, default=True)
    approval_levels = Column(Integer, default=1)
    auto_approve = Column(Boolean, default=False)
    
    # Carry forward settings
    allow_carry_forward = Column(Boolean, default=False)
    max_carry_forward_days = Column(Float, default=0.0)
    carry_forward_expiry_months = Column(Integer, default=12)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")


class Holiday(Base):
    __tablename__ = "holidays"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Holiday details
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(Date, nullable=False)
    
    # Type and status
    is_public_holiday = Column(Boolean, default=True)
    is_optional = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization") 