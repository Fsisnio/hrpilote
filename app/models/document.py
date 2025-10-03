from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Text, ForeignKey, Enum, Date, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
from enum import Enum as PyEnum
from app.core.database import Base


class DocumentType(PyEnum):
    CONTRACT = "CONTRACT"
    POLICY = "POLICY"
    FORM = "FORM"
    CERTIFICATE = "CERTIFICATE"
    ID_DOCUMENT = "ID_DOCUMENT"
    RESUME = "RESUME"
    PERFORMANCE_REVIEW = "PERFORMANCE_REVIEW"
    TRAINING_CERTIFICATE = "TRAINING_CERTIFICATE"
    EXPENSE_RECEIPT = "EXPENSE_RECEIPT"
    INVOICE = "INVOICE"
    REPORT = "REPORT"
    OTHER = "OTHER"


class DocumentStatus(PyEnum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    ARCHIVED = "ARCHIVED"


class DocumentCategory(PyEnum):
    EMPLOYEE = "EMPLOYEE"
    ORGANIZATION = "ORGANIZATION"
    DEPARTMENT = "DEPARTMENT"
    LEGAL = "LEGAL"
    FINANCIAL = "FINANCIAL"
    HR = "HR"
    TRAINING = "TRAINING"
    EXPENSE = "EXPENSE"
    OTHER = "OTHER"


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Document details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    document_type = Column(Enum(DocumentType), nullable=False)
    category = Column(Enum(DocumentCategory), nullable=False)
    
    # File information
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0)  # in bytes
    mime_type = Column(String(100), nullable=True)
    file_extension = Column(String(20), nullable=True)
    
    # Version control
    version = Column(String(20), default="1.0")
    is_latest_version = Column(Boolean, default=True)
    parent_document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    
    # Status and approval
    status = Column(Enum(DocumentStatus), default=DocumentStatus.DRAFT)
    is_public = Column(Boolean, default=False)
    requires_approval = Column(Boolean, default=False)
    
    # Ownership and access
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Related entities
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    
    # Expiry and retention
    expiry_date = Column(Date, nullable=True)
    retention_period_years = Column(Integer, default=7)
    
    # Tags and metadata
    tags = Column(Text, nullable=True)  # JSON array of tags
    document_metadata = Column(Text, nullable=True)  # JSON object for additional data
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")
    uploaded_user = relationship("User", foreign_keys=[uploaded_by])
    approved_user = relationship("User", foreign_keys=[approved_by])
    employee = relationship("Employee")
    department = relationship("Department")
    parent_document = relationship("Document", remote_side=[id])
    versions = relationship("Document", back_populates="parent_document")
    access_logs = relationship("DocumentAccessLog", back_populates="document", cascade="all, delete-orphan")


class DocumentAccessLog(Base):
    __tablename__ = "document_access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Access details
    action = Column(String(50), nullable=False)  # VIEW, DOWNLOAD, EDIT, DELETE
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Timestamps
    accessed_at = Column(DateTime, default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="access_logs")
    user = relationship("User")


class DocumentTemplate(Base):
    __tablename__ = "document_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Template details
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    template_type = Column(Enum(DocumentType), nullable=False)
    
    # Template content
    template_content = Column(Text, nullable=False)  # HTML or template content
    variables = Column(Text, nullable=True)  # JSON array of variable names
    
    # File template
    file_template_path = Column(String(500), nullable=True)
    file_template_name = Column(String(255), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_system_template = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")


class DocumentFolder(Base):
    __tablename__ = "document_folders"
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    
    # Folder details
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    parent_folder_id = Column(Integer, ForeignKey("document_folders.id"), nullable=True)
    
    # Access control
    is_public = Column(Boolean, default=False)
    requires_permission = Column(Boolean, default=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    organization = relationship("Organization")
    parent_folder = relationship("DocumentFolder", remote_side=[id])
    sub_folders = relationship("DocumentFolder", back_populates="parent_folder")


class DocumentPermission(Base):
    __tablename__ = "document_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    role_id = Column(String(50), nullable=True)  # UserRole enum value
    
    # Permission details
    can_view = Column(Boolean, default=False)
    can_download = Column(Boolean, default=False)
    can_edit = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_share = Column(Boolean, default=False)
    
    # Grant details
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    granted_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    document = relationship("Document")
    user = relationship("User", foreign_keys=[user_id])
    granted_user = relationship("User", foreign_keys=[granted_by]) 