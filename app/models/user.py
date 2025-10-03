from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ORG_ADMIN = "ORG_ADMIN"
    HR = "HR"
    MANAGER = "MANAGER"
    DIRECTOR = "DIRECTOR"
    PAYROLL = "PAYROLL"
    EMPLOYEE = "EMPLOYEE"


class UserStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    PENDING = "PENDING"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint('email', 'organization_id', name='uq_user_email_organization'),
    )

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False)  # Unique per organization
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.EMPLOYEE)
    status = Column(Enum(UserStatus), nullable=False, default=UserStatus.PENDING)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Profile fields
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    profile_picture = Column(String, nullable=True)
    
    # Security fields
    is_email_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    department = relationship("Department", back_populates="users")
    manager = relationship("User", remote_side=[id], back_populates="subordinates")
    subordinates = relationship("User", back_populates="manager")
    
    # Employee relationship (if user is an employee)
    employee = relationship("Employee", back_populates="user", uselist=False, foreign_keys="Employee.user_id", primaryjoin="User.id == Employee.user_id")
    
    # Audit relationships (commented out until AuditLog model is created)
    # created_audit_logs = relationship("AuditLog", foreign_keys="AuditLog.created_by_id", back_populates="created_by")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_super_admin(self) -> bool:
        """Check if user is super admin"""
        return self.role == UserRole.SUPER_ADMIN
    
    @property
    def is_org_admin(self) -> bool:
        """Check if user is organization admin"""
        return self.role == UserRole.ORG_ADMIN
    
    @property
    def can_manage_organization(self) -> bool:
        """Check if user can manage organization"""
        return self.role in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN]
    
    @property
    def can_manage_users(self) -> bool:
        """Check if user can manage users"""
        return self.role in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR]
    
    @property
    def can_approve_leave(self) -> bool:
        """Check if user can approve leave"""
        return self.role in [UserRole.MANAGER, UserRole.DIRECTOR, UserRole.HR, UserRole.ORG_ADMIN]
    
    @property
    def can_manage_payroll(self) -> bool:
        """Check if user can manage payroll"""
        return self.role in [UserRole.PAYROLL, UserRole.HR, UserRole.ORG_ADMIN, UserRole.SUPER_ADMIN] 