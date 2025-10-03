from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class OrganizationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    PENDING = "PENDING"


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    code = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(OrganizationStatus), nullable=False, default=OrganizationStatus.ACTIVE)
    
    # Contact Information
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    
    # Address
    address_line1 = Column(String, nullable=True)
    address_line2 = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    country = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    
    # Organization Details
    industry = Column(String, nullable=True)
    size = Column(String, nullable=True)  # Small, Medium, Large
    founded_year = Column(Integer, nullable=True)
    tax_id = Column(String, nullable=True)
    
    # Settings
    timezone = Column(String, default="UTC")
    currency = Column(String, default="USD")
    language = Column(String, default="en")
    
    # Features
    enable_attendance = Column(Boolean, default=True)
    enable_leave_management = Column(Boolean, default=True)
    enable_payroll = Column(Boolean, default=True)
    enable_training = Column(Boolean, default=True)
    enable_expenses = Column(Boolean, default=True)
    enable_documents = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    users = relationship("User", back_populates="organization")
    departments = relationship("Department", back_populates="organization")
    employees = relationship("Employee", back_populates="organization")
    # attendance_records = relationship("AttendanceRecord", back_populates="organization")
    # leave_requests = relationship("LeaveRequest", back_populates="organization")
    # payroll_records = relationship("PayrollRecord", back_populates="organization")
    # documents = relationship("Document", back_populates="organization")
    # training_courses = relationship("TrainingCourse", back_populates="organization")
    # expense_requests = relationship("ExpenseRequest", back_populates="organization")
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name='{self.name}', code='{self.code}')>"
    
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
    def active_users_count(self) -> int:
        """Get count of active users"""
        return len([user for user in self.users if user.is_active and user.status.value == "ACTIVE"])
    
    @property
    def total_employees_count(self) -> int:
        """Get total count of employees"""
        return len(self.employees) 