from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class DepartmentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    code = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(DepartmentStatus), nullable=False, default=DepartmentStatus.ACTIVE)
    
    # Organization and hierarchy
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    parent_department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    
    # Department details
    budget = Column(Integer, nullable=True)  # Annual budget in cents
    location = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    
    # Settings
    max_employees = Column(Integer, nullable=True)
    allow_remote_work = Column(Boolean, default=True)
    working_hours_start = Column(String, default="09:00")  # HH:MM format
    working_hours_end = Column(String, default="17:00")   # HH:MM format
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="departments")
    parent_department = relationship("Department", remote_side=[id], back_populates="sub_departments")
    sub_departments = relationship("Department", back_populates="parent_department")
    users = relationship("User", back_populates="department")
    employees = relationship("Employee", back_populates="department")
    
    def __repr__(self):
        return f"<Department(id={self.id}, name='{self.name}', organization_id={self.organization_id})>"
    
    @property
    def full_name(self) -> str:
        """Get department full name with organization"""
        return f"{self.name} - {self.organization.name}"
    
    @property
    def employees_count(self) -> int:
        """Get count of employees in department"""
        return len(self.employees)
    
    @property
    def active_employees_count(self) -> int:
        """Get count of active employees in department"""
        return len([emp for emp in self.employees if emp.status.value == "ACTIVE"])
    
    @property
    def hierarchy_path(self) -> str:
        """Get department hierarchy path"""
        path = [self.name]
        current = self.parent_department
        while current:
            path.append(current.name)
            current = current.parent_department
        return " > ".join(reversed(path)) 