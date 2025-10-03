from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date, time
from decimal import Decimal
from enum import Enum


class AttendanceType(str, Enum):
    REGULAR = "REGULAR"
    OVERTIME = "OVERTIME"
    HOLIDAY = "HOLIDAY"
    SICK_LEAVE = "SICK_LEAVE"
    VACATION = "VACATION"
    REMOTE = "REMOTE"
    BUSINESS_TRIP = "BUSINESS_TRIP"


class AttendanceStatus(str, Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LATE = "LATE"
    HALF_DAY = "HALF_DAY"
    ON_LEAVE = "ON_LEAVE"
    REMOTE = "REMOTE"


class BreakType(str, Enum):
    LUNCH = "LUNCH"
    COFFEE = "COFFEE"
    REST = "REST"
    MEETING = "MEETING"
    OTHER = "OTHER"


# Base schemas
class AttendanceBase(BaseModel):
    location: Optional[str] = None
    ip_address: Optional[str] = None
    notes: Optional[str] = None


class AttendanceBreakBase(BaseModel):
    break_type: BreakType
    location: Optional[str] = None
    notes: Optional[str] = None


class WorkScheduleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    start_time: time
    end_time: time
    break_start: Optional[time] = None
    break_end: Optional[time] = None
    working_days: int = Field(default=31, ge=1, le=127)  # Bitmap for days
    overtime_threshold_hours: float = Field(default=8.0, ge=0)
    overtime_rate_multiplier: float = Field(default=1.5, ge=1.0)
    allow_flexible_hours: bool = False
    grace_period_minutes: int = Field(default=15, ge=0)


class TimeOffRequestBase(BaseModel):
    request_type: AttendanceType
    start_date: date
    end_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    total_hours: Optional[float] = Field(None, ge=0)
    reason: str = Field(..., min_length=1)
    notes: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    handover_to: Optional[int] = None
    handover_notes: Optional[str] = None


# Create schemas
class AttendanceCreate(AttendanceBase):
    pass


class AttendanceBreakCreate(AttendanceBreakBase):
    pass


class WorkScheduleCreate(WorkScheduleBase):
    department_id: Optional[int] = None
    employee_id: Optional[int] = None


class TimeOffRequestCreate(TimeOffRequestBase):
    pass


# Update schemas
class AttendanceUpdate(BaseModel):
    notes: Optional[str] = None
    is_approved: Optional[bool] = None


class AttendanceBreakUpdate(BaseModel):
    notes: Optional[str] = None


class WorkScheduleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    break_start: Optional[time] = None
    break_end: Optional[time] = None
    working_days: Optional[int] = Field(None, ge=1, le=127)
    overtime_threshold_hours: Optional[float] = Field(None, ge=0)
    overtime_rate_multiplier: Optional[float] = Field(None, ge=1.0)
    allow_flexible_hours: Optional[bool] = None
    grace_period_minutes: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class TimeOffRequestUpdate(BaseModel):
    reason: Optional[str] = Field(None, min_length=1)
    notes: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    handover_to: Optional[int] = None
    handover_notes: Optional[str] = None


# Response schemas
class AttendanceBreakResponse(AttendanceBreakBase):
    id: int
    attendance_id: int
    break_start: datetime
    break_end: Optional[datetime] = None
    duration_minutes: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AttendanceResponse(AttendanceBase):
    id: int
    employee_id: int
    organization_id: int
    date: date
    clock_in_time: Optional[datetime] = None
    clock_out_time: Optional[datetime] = None
    expected_clock_in: Optional[time] = None
    expected_clock_out: Optional[time] = None
    total_hours: float = 0.0
    regular_hours: float = 0.0
    overtime_hours: float = 0.0
    status: AttendanceStatus
    attendance_type: AttendanceType
    clock_in_location: Optional[str] = None
    clock_out_location: Optional[str] = None
    clock_in_ip: Optional[str] = None
    clock_out_ip: Optional[str] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    is_approved: bool = False
    created_at: datetime
    updated_at: datetime
    breaks: List[AttendanceBreakResponse] = []

    class Config:
        from_attributes = True


class WorkScheduleResponse(WorkScheduleBase):
    id: int
    organization_id: int
    department_id: Optional[int] = None
    employee_id: Optional[int] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TimeOffRequestResponse(TimeOffRequestBase):
    id: int
    employee_id: int
    organization_id: int
    total_days: float = 0.0
    status: str = "PENDING"
    requested_by: int
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Summary and Report schemas
class AttendanceSummary(BaseModel):
    month: int
    year: int
    total_days: int
    present_days: int
    absent_days: int
    late_days: int
    total_hours: float
    regular_hours: float
    overtime_hours: float


class AttendanceReport(BaseModel):
    employee_id: int
    employee_name: str
    department_name: Optional[str] = None
    date_range: str
    total_days: int
    present_days: int
    absent_days: int
    late_days: int
    total_hours: float
    regular_hours: float
    overtime_hours: float
    attendance_rate: float
    average_hours_per_day: float


# List response schemas
class AttendanceListResponse(BaseModel):
    items: List[AttendanceResponse]
    total: int
    page: int
    size: int
    pages: int


class WorkScheduleListResponse(BaseModel):
    items: List[WorkScheduleResponse]
    total: int
    page: int
    size: int
    pages: int


class TimeOffRequestListResponse(BaseModel):
    items: List[TimeOffRequestResponse]
    total: int
    page: int
    size: int
    pages: int 