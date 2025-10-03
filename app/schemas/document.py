from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.document import DocumentType, DocumentStatus, DocumentCategory

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
    id: int
    organization_id: int
    file_name: str
    file_path: str
    file_size: int
    mime_type: Optional[str] = None
    file_extension: Optional[str] = None
    version: str
    is_latest_version: bool
    parent_document_id: Optional[int] = None
    uploaded_by: int
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    employee_id: Optional[int] = None
    department_id: Optional[int] = None
    expiry_date: Optional[datetime] = None
    retention_period_years: int
    tags: Optional[str] = None
    document_metadata: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 