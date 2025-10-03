from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, Enum, Date, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, time
from enum import Enum as PyEnum
from app.core.database import Base


class AttendanceType(PyEnum):
    REGULAR = "REGULAR"
    OVERTIME = "OVERTIME"
    HOLIDAY = "HOLIDAY"
    SICK_LEAVE = "SICK_LEAVE"
    VACATION = "VACATION"
    REMOTE = "REMOTE"
    BUSINESS_TRIP = "BUSINESS_TRIP"


class AttendanceStatus(PyEnum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    HALF_DAY = "HALF_DAY"
    ON_LEAVE = "ON_LEAVE"
    REMOTE = "REMOTE"


class BreakType(PyEnum):
    LUNCH = "LUNCH"
    COFFEE = "COFFEE"
    REST = "REST"
    MEETING = "MEETING"
    OTHER = "OTHER"


class Attendance(Base):
    __tablename__ = "attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    date = Column(Date, nullable=False, default=func.current_date())
    
    # Clock in/out times
    clock_in_time = Column(DateTime, nullable=True)
    clock_out_time = Column(DateTime, nullable=True)
    expected_clock_in = Column(Time, nullable=True)
    expected_clock_out = Column(Time, nullable=True)
    
    # Work hours
    total_hours = Column(Float, default=0.0)
    regular_hours = Column(Float, default=0.0)
    overtime_hours = Column(Float, default=0.0)
    
    # Status and type
    status = Column(Enum(AttendanceStatus), default=AttendanceStatus.ABSENT)
    attendance_type = Column(Enum(AttendanceType), default=AttendanceType.REGULAR)
    
    # Location tracking
    clock_in_location = Column(String(255), nullable=True)
    clock_out_location = Column(String(255), nullable=True)
    clock_in_ip = Column(String(45), nullable=True)  # IPv6 compatible
    clock_out_ip = Column(String(45), nullable=True)
    
    # Notes and approval
    notes = Column(Text, nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    is_approved = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    employee = relationship("Employee", back_populates="attendance_records")
    organization = relationship("Organization")
    approver = relationship("User", foreign_keys=[approved_by])
    breaks = relationship("AttendanceBreak", back_populates="attendance", cascade="all, delete-orphan")


class AttendanceBreak(Base):
    __tablename__ = "attendance_breaks"
    
    id = Column(Integer, primary_key=True, index=True)
    attendance_id = Column(Integer, ForeignKey("attendance.id"), nullable=False)
    break_type = Column(Enum(BreakType), nullable=False)
    
    # Break times
    break_start = Column(DateTime, nullable=False)
    break_end = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, default=0)
    
    # Location and notes
    location = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    attendance = relationship("Attendance", back_populates="breaks")


class WorkSchedule(Base):
    __tablename__ = "work_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    
    # Schedule details
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Working hours
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    break_start = Column(Time, nullable=True)
    break_end = Column(Time, nullable=True)
    
    # Days of week (bitmap: 1=Monday, 2=Tuesday, etc.)
    working_days = Column(Integer, default=31)  # Monday to Friday by default
    
    # Overtime settings
    overtime_threshold_hours = Column(Float, default=8.0)
    overtime_rate_multiplier = Column(Float, default=1.5)
    
    # Flexibility settings
    allow_flexible_hours = Column(Boolean, default=False)
    grace_period_minutes = Column(Integer, default=15)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")
    department = relationship("Department")
    employee = relationship("Employee")


class TimeOffRequest(Base):
    __tablename__ = "time_off_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Request details
    request_type = Column(Enum(AttendanceType), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    
    # Duration
    total_days = Column(Float, default=0.0)
    total_hours = Column(Float, default=0.0)
    
    # Status and approval
    status = Column(String(20), default="PENDING")  # PENDING, APPROVED, REJECTED, CANCELLED
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Reason and notes
    reason = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    employee = relationship("Employee")
    organization = relationship("Organization")
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by]) 