from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum, Numeric, Date, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class EmployeeStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    TERMINATED = "TERMINATED"
    ON_LEAVE = "ON_LEAVE"
    PROBATION = "PROBATION"


class EmploymentType(str, enum.Enum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"
    INTERN = "INTERN"
    FREELANCE = "FREELANCE"


class Gender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"
    PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY"


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (
        UniqueConstraint('employee_id', 'organization_id', name='uq_employee_id_organization'),
    )

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, index=True, nullable=False)  # Company employee ID (unique per organization)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    
    # Personal Information
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    middle_name = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(Enum(Gender), nullable=True)
    nationality = Column(String, nullable=True)
    marital_status = Column(String, nullable=True)
    
    # Contact Information
    personal_email = Column(String, nullable=True)
    personal_phone = Column(String, nullable=True)
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_phone = Column(String, nullable=True)
    emergency_contact_relationship = Column(String, nullable=True)
    
    # Address
    address_line1 = Column(String, nullable=True)
    address_line2 = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    country = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    
    # Employment Details
    status = Column(Enum(EmployeeStatus), nullable=False, default=EmployeeStatus.ACTIVE)
    employment_type = Column(Enum(EmploymentType), nullable=False, default=EmploymentType.FULL_TIME)
    position = Column(String, nullable=False)
    job_title = Column(String, nullable=False)
    hire_date = Column(Date, nullable=False)
    termination_date = Column(Date, nullable=True)
    probation_end_date = Column(Date, nullable=True)
    
    # Salary Information
    base_salary = Column(Numeric(10, 2), nullable=True)  # Annual salary
    hourly_rate = Column(Numeric(8, 2), nullable=True)   # Hourly rate for part-time
    currency = Column(String, default="USD")
    
    # Work Schedule
    working_hours_per_week = Column(Integer, default=40)
    work_schedule = Column(String, nullable=True)  # JSON string for flexible schedules
    timezone = Column(String, default="UTC")
    
    # Benefits
    benefits_package = Column(String, nullable=True)  # JSON string
    insurance_provider = Column(String, nullable=True)
    insurance_policy_number = Column(String, nullable=True)
    
    # Documents
    id_document_type = Column(String, nullable=True)  # Passport, Driver's License, etc.
    id_document_number = Column(String, nullable=True)
    id_document_expiry = Column(Date, nullable=True)
    
    # HR Information
    hr_manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    direct_manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    hr_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="employee", foreign_keys=[user_id])
    organization = relationship("Organization", back_populates="employees")
    department = relationship("Department", back_populates="employees")
    hr_manager = relationship("User", foreign_keys=[hr_manager_id], remote_side="User.id")
    direct_manager = relationship("User", foreign_keys=[direct_manager_id], remote_side="User.id")
    
    # Related records
    attendance_records = relationship("Attendance", back_populates="employee")
    leave_requests = relationship("LeaveRequest", foreign_keys="LeaveRequest.employee_id")
    payroll_records = relationship("PayrollRecord", foreign_keys="PayrollRecord.employee_id")
    course_enrollments = relationship("CourseEnrollment", foreign_keys="CourseEnrollment.employee_id")
    expenses = relationship("Expense", foreign_keys="Expense.employee_id")
    expense_reports = relationship("ExpenseReport", foreign_keys="ExpenseReport.employee_id")
    travel_requests = relationship("TravelRequest", foreign_keys="TravelRequest.employee_id")
    advance_requests = relationship("AdvanceRequest", foreign_keys="AdvanceRequest.employee_id")
    skills = relationship("EmployeeSkill", foreign_keys="EmployeeSkill.employee_id")
    documents = relationship("Document", foreign_keys="Document.employee_id")
    
    def __repr__(self):
        return f"<Employee(id={self.id}, employee_id='{self.employee_id}', name='{self.full_name}')>"
    
    @property
    def full_name(self) -> str:
        """Get employee's full name"""
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_address(self) -> str:
        """Get full address as string"""
        address_parts = []
        if self.address_line1:
            address_parts.append(self.address_line1)
        if self.address_line2:
            address_parts.append(self.address_line2)
        if self.city:
            address_parts.append(self.city)
        if self.state:
            address_parts.append(self.state)
        if self.postal_code:
            address_parts.append(self.postal_code)
        if self.country:
            address_parts.append(self.country)
        return ", ".join(address_parts) if address_parts else ""
    
    @property
    def age(self) -> int:
        """Calculate employee age"""
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
    
    @property
    def years_of_service(self) -> float:
        """Calculate years of service"""
        from datetime import date
        today = date.today()
        end_date = self.termination_date or today
        return (end_date - self.hire_date).days / 365.25
    
    @property
    def is_on_probation(self) -> bool:
        """Check if employee is on probation"""
        if not self.probation_end_date:
            return False
        from datetime import date
        return date.today() <= self.probation_end_date
    
    @property
    def is_terminated(self) -> bool:
        """Check if employee is terminated"""
        return self.status == EmployeeStatus.TERMINATED
    
    @property
    def is_active(self) -> bool:
        """Check if employee is active"""
        return self.status == EmployeeStatus.ACTIVE 