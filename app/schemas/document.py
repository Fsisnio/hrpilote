from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.models.enums import DocumentType, DocumentStatus, DocumentCategory

class DocumentBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: DocumentCategory
    document_type: Optional[DocumentType] = None
    status: Optional[DocumentStatus] = DocumentStatus.DRAFT
    is_public: Optional[bool] = False
    requires_approval: Optional[bool] = False

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[DocumentCategory] = None
    status: Optional[DocumentStatus] = None
    is_public: Optional[bool] = None
    requires_approval: Optional[bool] = None

class DocumentResponse(DocumentBase):
    id: str
    organization_id: str
    file_name: str
    file_path: str
    file_size: int
    mime_type: Optional[str] = None
    file_extension: Optional[str] = None
    version: str
    is_latest_version: bool
    parent_document_id: Optional[str] = None
    uploaded_by: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    employee_id: Optional[str] = None
    department_id: Optional[str] = None
    expiry_date: Optional[datetime] = None
    retention_period_years: int
    tags: Optional[list[str]] = None
    document_metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 