from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import List, Optional

from beanie import Document, Indexed, PydanticObjectId
from pymongo import IndexModel
from pydantic import Field

from app.models.enums import (
    OrganizationStatus,
    DepartmentStatus,
    UserRole,
    UserStatus,
    EmployeeStatus,
    EmploymentType,
    Gender,
    AttendanceType,
    AttendanceStatus,
    BreakType,
    TimeOffStatus,
    LeaveType,
    LeaveStatus,
    PayrollStatus,
    SalaryComponentType,
    DocumentType,
    DocumentStatus,
    DocumentCategory,
    ExpenseType,
    ExpenseStatus,
    PaymentMethod,
    CourseType,
    CourseStatus,
    EnrollmentStatus,
    AssessmentType,
)


class OrganizationDocument(Document):
    name: Indexed(str)
    code: Indexed(str)
    description: Optional[str] = None
    status: OrganizationStatus = OrganizationStatus.ACTIVE

    email: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None

    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

    industry: Optional[str] = None
    size: Optional[str] = None
    founded_year: Optional[int] = None
    tax_id: Optional[str] = None

    timezone: str = "UTC"
    currency: str = "USD"
    language: str = "en"

    enable_attendance: bool = True
    enable_leave_management: bool = True
    enable_payroll: bool = True
    enable_training: bool = True
    enable_expenses: bool = True
    enable_documents: bool = True

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "organizations"
        indexes = [
            "code",
            [("name", 1)],
        ]


class DepartmentDocument(Document):
    name: Indexed(str)
    code: Indexed(str)
    description: Optional[str] = None
    status: DepartmentStatus = DepartmentStatus.ACTIVE

    organization_id: PydanticObjectId
    parent_department_id: Optional[PydanticObjectId] = None

    budget: Optional[int] = None
    location: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

    max_employees: Optional[int] = None
    allow_remote_work: bool = True
    working_hours_start: str = "09:00"
    working_hours_end: str = "17:00"

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "departments"
        indexes = [
            [("organization_id", 1), ("code", 1)],
            [("organization_id", 1), ("name", 1)],
        ]


class UserDocument(Document):
    email: Indexed(str)
    username: Indexed(str, unique=True)
    hashed_password: str
    first_name: str
    last_name: str
    role: UserRole = UserRole.EMPLOYEE
    status: UserStatus = UserStatus.PENDING

    organization_id: Optional[PydanticObjectId] = None
    department_id: Optional[PydanticObjectId] = None
    manager_id: Optional[PydanticObjectId] = None

    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    profile_picture: Optional[str] = None

    is_email_verified: bool = False
    is_active: bool = True
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
        indexes = [
            IndexModel("email"),
            IndexModel([("organization_id", 1), ("email", 1)], unique=True),
        ]


class EmployeeDocument(Document):
    employee_id: str
    user_id: PydanticObjectId
    organization_id: PydanticObjectId
    department_id: Optional[PydanticObjectId] = None

    first_name: str
    last_name: str
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

    status: EmployeeStatus = EmployeeStatus.ACTIVE
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    position: str
    job_title: str
    hire_date: date
    termination_date: Optional[date] = None
    probation_end_date: Optional[date] = None

    base_salary: Optional[float] = None
    hourly_rate: Optional[float] = None
    currency: str = "USD"

    working_hours_per_week: int = 40
    work_schedule: Optional[str] = None
    timezone: str = "UTC"

    benefits_package: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_policy_number: Optional[str] = None

    id_document_type: Optional[str] = None
    id_document_number: Optional[str] = None
    id_document_expiry: Optional[date] = None

    hr_manager_id: Optional[PydanticObjectId] = None
    direct_manager_id: Optional[PydanticObjectId] = None
    hr_notes: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "employees"
        indexes = [
            IndexModel([("organization_id", 1), ("employee_id", 1)], unique=True),
            IndexModel("user_id", unique=True),
        ]


class AttendanceDocument(Document):
    employee_id: PydanticObjectId
    organization_id: PydanticObjectId
    date: date

    clock_in_time: Optional[datetime] = None
    clock_out_time: Optional[datetime] = None
    expected_clock_in: Optional[time] = None
    expected_clock_out: Optional[time] = None

    total_hours: float = 0.0
    regular_hours: float = 0.0
    overtime_hours: float = 0.0

    status: AttendanceStatus = AttendanceStatus.ABSENT
    attendance_type: AttendanceType = AttendanceType.REGULAR

    clock_in_location: Optional[str] = None
    clock_out_location: Optional[str] = None
    clock_in_ip: Optional[str] = None
    clock_out_ip: Optional[str] = None

    notes: Optional[str] = None
    approved_by: Optional[PydanticObjectId] = None
    approved_at: Optional[datetime] = None
    is_approved: bool = False

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "attendance"
        indexes = [
            [("employee_id", 1), ("date", 1)],
            [("organization_id", 1), ("date", 1)],
        ]


class AttendanceBreakDocument(Document):
    attendance_id: PydanticObjectId
    break_type: BreakType
    break_start: datetime
    break_end: Optional[datetime] = None
    duration_minutes: int = 0
    location: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "attendance_breaks"
        indexes = [
            [("attendance_id", 1)],
        ]


class WorkScheduleDocument(Document):
    organization_id: PydanticObjectId
    department_id: Optional[PydanticObjectId] = None
    employee_id: Optional[PydanticObjectId] = None

    name: str
    description: Optional[str] = None
    start_time: time
    end_time: time
    break_start: Optional[time] = None
    break_end: Optional[time] = None
    working_days: int = 31
    overtime_threshold_hours: float = 8.0
    overtime_rate_multiplier: float = 1.5
    allow_flexible_hours: bool = False
    grace_period_minutes: int = 15
    is_active: bool = True

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "work_schedules"
        indexes = [
            [("organization_id", 1)],
            [("organization_id", 1), ("employee_id", 1)],
        ]


class TimeOffRequestDocument(Document):
    employee_id: PydanticObjectId
    organization_id: PydanticObjectId
    request_type: AttendanceType
    start_date: date
    end_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    total_days: float = 0.0
    total_hours: float = 0.0
    status: TimeOffStatus = TimeOffStatus.PENDING
    requested_by: PydanticObjectId
    approved_by: Optional[PydanticObjectId] = None
    approved_at: Optional[datetime] = None
    reason: str
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    handover_to: Optional[str] = None
    handover_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "time_off_requests"
        indexes = [
            [("employee_id", 1), ("start_date", 1)],
            [("organization_id", 1), ("status", 1)],
        ]


class LeaveRequestDocument(Document):
    employee_id: PydanticObjectId
    organization_id: PydanticObjectId
    leave_type: LeaveType
    start_date: date
    end_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    total_days: float = 0.0
    total_hours: float = 0.0
    is_half_day: bool = False
    status: LeaveStatus = LeaveStatus.PENDING
    requested_by: PydanticObjectId
    approved_by: Optional[PydanticObjectId] = None
    approved_at: Optional[datetime] = None
    reason: str
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    handover_to: Optional[PydanticObjectId] = None
    handover_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "leave_requests"
        indexes = [
            [("employee_id", 1), ("start_date", 1)],
            [("organization_id", 1), ("status", 1)],
        ]


class LeaveBalanceDocument(Document):
    employee_id: PydanticObjectId
    organization_id: PydanticObjectId
    leave_type: LeaveType
    year: int
    total_entitled: float = 0.0
    total_taken: float = 0.0
    total_remaining: float = 0.0
    total_carried_forward: float = 0.0
    max_carry_forward: float = 0.0
    expires_at: Optional[date] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "leave_balances"
        indexes = [
            [("employee_id", 1), ("year", 1), ("leave_type", 1)],
            [("organization_id", 1), ("year", 1)],
        ]


class LeavePolicyDocument(Document):
    organization_id: PydanticObjectId
    leave_type: LeaveType
    name: str
    description: Optional[str] = None
    days_per_year: float = 0.0
    hours_per_year: float = 0.0
    min_service_months: int = 0
    max_consecutive_days: int = 0
    min_notice_days: int = 0
    requires_approval: bool = True
    approval_levels: int = 1
    auto_approve: bool = False
    allow_carry_forward: bool = False
    max_carry_forward_days: float = 0.0
    carry_forward_expiry_months: int = 12
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "leave_policies"
        indexes = [
            [("organization_id", 1), ("leave_type", 1)],
        ]


class HolidayDocument(Document):
    organization_id: PydanticObjectId
    name: str
    description: Optional[str] = None
    date: date
    is_public_holiday: bool = True
    is_optional: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "holidays"
        indexes = [
            [("organization_id", 1), ("date", 1)],
        ]


class PayrollPeriodDocument(Document):
    organization_id: PydanticObjectId
    name: str
    period_type: str = "MONTHLY"
    start_date: date
    end_date: date
    pay_date: date
    processing_date: date
    status: PayrollStatus = PayrollStatus.PROCESSING
    total_gross_pay: Decimal = Decimal("0")
    total_net_pay: Decimal = Decimal("0")
    total_deductions: Decimal = Decimal("0")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "payroll_periods"
        indexes = [
            [("organization_id", 1), ("start_date", 1)],
        ]


class PayrollComponentDocument(Document):
    payroll_record_id: PydanticObjectId
    name: str
    component_type: SalaryComponentType
    amount: Decimal
    is_taxable: bool = True
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "payroll_components"
        indexes = [
            [("payroll_record_id", 1)],
        ]


class PayrollRecordDocument(Document):
    payroll_period_id: PydanticObjectId
    employee_id: PydanticObjectId
    organization_id: PydanticObjectId
    base_salary: Decimal
    basic_salary: Decimal
    total_earnings: Decimal
    total_allowances: Decimal
    total_bonuses: Decimal
    total_overtime: Decimal
    total_commission: Decimal
    total_deductions: Decimal
    total_taxes: Decimal
    total_insurance: Decimal
    total_pension: Decimal
    gross_pay: Decimal
    net_pay: Decimal
    regular_hours: float = 0.0
    overtime_hours: float = 0.0
    total_hours: float = 0.0
    status: PayrollStatus = PayrollStatus.PROCESSING
    is_approved: bool = False
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "payroll_records"
        indexes = [
            [("employee_id", 1), ("created_at", 1)],
            [("organization_id", 1), ("status", 1)],
        ]


class PayrollSettingsDocument(Document):
    organization_id: PydanticObjectId
    payroll_cycle: str = "Monthly"
    pay_day: str = "Last day of month"
    currency: str = "USD ($)"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "payroll_settings"
        indexes = [
            [("organization_id", 1)],
        ]


ALL_DOCUMENT_MODELS: List[type[Document]] = [
    OrganizationDocument,
    DepartmentDocument,
    UserDocument,
    EmployeeDocument,
    AttendanceDocument,
    AttendanceBreakDocument,
    WorkScheduleDocument,
    TimeOffRequestDocument,
    LeaveRequestDocument,
    LeaveBalanceDocument,
    LeavePolicyDocument,
    HolidayDocument,
    PayrollPeriodDocument,
    PayrollRecordDocument,
    PayrollComponentDocument,
    PayrollSettingsDocument,
]


class DocumentDocument(Document):
    organization_id: PydanticObjectId
    title: str
    description: Optional[str] = None
    document_type: DocumentType = DocumentType.OTHER
    category: DocumentCategory = DocumentCategory.OTHER
    file_name: str
    file_path: str
    file_size: int = 0
    mime_type: Optional[str] = None
    file_extension: Optional[str] = None
    version: str = "1.0"
    is_latest_version: bool = True
    parent_document_id: Optional[PydanticObjectId] = None
    status: DocumentStatus = DocumentStatus.DRAFT
    is_public: bool = False
    requires_approval: bool = False
    uploaded_by: PydanticObjectId
    approved_by: Optional[PydanticObjectId] = None
    approved_at: Optional[datetime] = None
    employee_id: Optional[PydanticObjectId] = None
    department_id: Optional[PydanticObjectId] = None
    expiry_date: Optional[date] = None
    retention_period_years: int = 7
    tags: Optional[List[str]] = None
    document_metadata: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "documents"
        indexes = [
            [("organization_id", 1)],
            [("organization_id", 1), ("category", 1)],
            [("title", "text"), ("description", "text")],
        ]


class DocumentAccessLogDocument(Document):
    document_id: PydanticObjectId
    user_id: PydanticObjectId
    action: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    accessed_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "document_access_logs"
        indexes = [
            [("document_id", 1)],
            [("user_id", 1)],
        ]


class ExpenseDocument(Document):
    organization_id: PydanticObjectId
    employee_id: PydanticObjectId
    title: str
    description: Optional[str] = None
    expense_type: ExpenseType = ExpenseType.OTHER
    amount: Decimal = Decimal("0")
    currency: str = "USD"
    expense_date: date
    location: Optional[str] = None
    vendor: Optional[str] = None
    payment_method: PaymentMethod = PaymentMethod.CASH
    receipt_number: Optional[str] = None
    status: ExpenseStatus = ExpenseStatus.DRAFT
    submitted_at: Optional[datetime] = None
    approved_by: Optional[PydanticObjectId] = None
    approved_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "expenses"
        indexes = [
            [("organization_id", 1)],
            [("employee_id", 1)],
            [("expense_type", 1)],
            [("status", 1)],
        ]


class ExpenseItemDocument(Document):
    expense_id: PydanticObjectId
    organization_id: PydanticObjectId
    employee_id: Optional[PydanticObjectId] = None
    description: str
    expense_type: ExpenseType = ExpenseType.OTHER
    amount: Decimal = Decimal("0")
    expense_date: date
    receipt_number: Optional[str] = None
    status: ExpenseStatus = ExpenseStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "expense_items"
        indexes = [
            [("expense_id", 1)],
            [("organization_id", 1)],
            [("expense_type", 1)],
            [("status", 1)],
        ]

class CourseDocument(Document):
    organization_id: PydanticObjectId
    instructor_id: Optional[PydanticObjectId] = None
    title: str
    description: Optional[str] = None
    course_type: CourseType = CourseType.ONLINE
    category: Optional[str] = None
    duration_hours: float = 0.0
    duration_weeks: int = 0
    max_enrollment: int = 0
    min_enrollment: int = 1
    prerequisites: Optional[str] = None
    requirements: Optional[str] = None
    target_audience: Optional[str] = None
    course_content: Optional[str] = None
    materials: Optional[str] = None
    syllabus: Optional[str] = None
    instructor_name: Optional[str] = None
    instructor_bio: Optional[str] = None
    cost: Decimal = Decimal("0")
    currency: str = "USD"
    is_free: bool = True
    is_featured: bool = False
    is_mandatory: bool = False
    status: CourseStatus = CourseStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "courses"
        indexes = [
            [("organization_id", 1)],
            [("category", 1)],
            [("status", 1)],
        ]


class CourseEnrollmentDocument(Document):
    organization_id: PydanticObjectId
    course_id: PydanticObjectId
    employee_id: PydanticObjectId
    enrollment_date: datetime = Field(default_factory=datetime.utcnow)
    start_date: Optional[date] = None
    completion_date: Optional[date] = None
    notes: Optional[str] = None
    status: EnrollmentStatus = EnrollmentStatus.ENROLLED
    final_score: float = 0.0
    grade: Optional[str] = None
    certificate_issued: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "course_enrollments"
        indexes = [
            [("organization_id", 1)],
            [("course_id", 1)],
            [("employee_id", 1)],
            [("status", 1)],
        ]


class AssessmentDocument(Document):
    organization_id: PydanticObjectId
    course_id: PydanticObjectId
    title: str
    description: Optional[str] = None
    assessment_type: AssessmentType = AssessmentType.QUIZ
    total_points: float = 100.0
    passing_score: float = 70.0
    weight_percentage: float = 100.0
    duration_minutes: int = 0
    due_date: Optional[datetime] = None
    instructions: Optional[str] = None
    content: Optional[str] = None
    allow_retakes: bool = False
    max_attempts: int = 1
    is_required: bool = True
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "assessments"
        indexes = [
            [("organization_id", 1)],
            [("course_id", 1)],
            [("assessment_type", 1)],
        ]


class AssessmentResultDocument(Document):
    organization_id: PydanticObjectId
    assessment_id: PydanticObjectId
    enrollment_id: PydanticObjectId
    employee_id: PydanticObjectId
    score: float = 0.0
    max_score: float = 100.0
    percentage: float = 0.0
    passed: bool = False
    attempt_number: int = 1
    submission_date: datetime = Field(default_factory=datetime.utcnow)
    graded_date: Optional[datetime] = None
    feedback: Optional[str] = None
    graded_by: Optional[PydanticObjectId] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "assessment_results"
        indexes = [
            [("organization_id", 1)],
            [("assessment_id", 1)],
            [("enrollment_id", 1)],
            [("employee_id", 1)],
        ]


class SkillDocument(Document):
    organization_id: PydanticObjectId
    name: Indexed(str)
    description: Optional[str] = None
    category: Optional[str] = None
    proficiency_levels: Optional[List[str]] = None
    is_technical: bool = False
    is_soft_skill: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "skills"
        indexes = [
            [("organization_id", 1), ("name", 1)],
            [("organization_id", 1), ("category", 1)],
        ]


class EmployeeSkillDocument(Document):
    organization_id: PydanticObjectId
    employee_id: PydanticObjectId
    skill_id: PydanticObjectId
    proficiency_level: str
    years_of_experience: float = 0.0
    is_certified: bool = False
    certification_name: Optional[str] = None
    certification_date: Optional[date] = None
    certification_expiry: Optional[date] = None
    last_assessed: Optional[date] = None
    assessed_by: Optional[PydanticObjectId] = None
    assessment_score: float = 0.0
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "employee_skills"
        indexes = [
            [("organization_id", 1), ("employee_id", 1)],
            [("organization_id", 1), ("skill_id", 1)],
        ]


class TrainingSessionDocument(Document):
    organization_id: PydanticObjectId
    course_id: PydanticObjectId
    title: str
    description: Optional[str] = None
    session_type: CourseType = CourseType.ONLINE
    start_datetime: datetime
    end_datetime: datetime
    duration_hours: float = 0.0
    location: Optional[str] = None
    room: Optional[str] = None
    max_capacity: int = 0
    current_enrollment: int = 0
    instructor_id: Optional[PydanticObjectId] = None
    instructor_name: Optional[str] = None
    status: str = "SCHEDULED"
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "training_sessions"
        indexes = [
            [("organization_id", 1)],
            [("organization_id", 1), ("course_id", 1)],
            [("organization_id", 1), ("status", 1)],
            [("organization_id", 1), ("start_datetime", 1)],
        ]


class SessionAttendanceDocument(Document):
    organization_id: PydanticObjectId
    session_id: PydanticObjectId
    employee_id: PydanticObjectId
    status: str = "REGISTERED"
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    rating: Optional[int] = None
    feedback: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "session_attendances"
        indexes = [
            [("session_id", 1)],
            [("employee_id", 1)],
            [("organization_id", 1)],
        ]
    expense_id: PydanticObjectId
    organization_id: PydanticObjectId
    employee_id: PydanticObjectId
    description: str
    expense_type: ExpenseType = ExpenseType.OTHER
    amount: Decimal = Decimal("0")
    expense_date: date
    receipt_number: Optional[str] = None
    status: ExpenseStatus = ExpenseStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "expense_items"
        indexes = [
            [("expense_id", 1)],
            [("organization_id", 1)],
            [("expense_type", 1)],
            [("status", 1)],
        ]


ALL_DOCUMENT_MODELS.extend(
    [
        DocumentDocument,
        DocumentAccessLogDocument,
        ExpenseDocument,
        ExpenseItemDocument,
        CourseDocument,
        CourseEnrollmentDocument,
        AssessmentDocument,
        AssessmentResultDocument,
        SkillDocument,
        EmployeeSkillDocument,
        TrainingSessionDocument,
        SessionAttendanceDocument,
    ]
)

