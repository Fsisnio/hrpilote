from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.document import Document, DocumentType, DocumentStatus, DocumentCategory, DocumentAccessLog
from app.models.user import User, UserRole
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentResponse

router = APIRouter()

# Configure upload directory
UPLOAD_DIR = "uploads/documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/", response_model=List[DocumentResponse])
async def get_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all documents with optional filtering - organization-specific"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.DIRECTOR, UserRole.EMPLOYEE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view documents"
        )
    
    # Set organization filter
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admin can see all documents
        query = db.query(Document)
    else:
        # Other roles can only see documents from their organization
        query = db.query(Document).filter(Document.organization_id == current_user.organization_id)
    
    # Filter by category
    if category:
        query = query.filter(Document.category == category)
    
    # Search in title and description
    if search:
        query = query.filter(
            (Document.title.ilike(f"%{search}%")) |
            (Document.description.ilike(f"%{search}%"))
        )
    
    documents = query.offset(skip).limit(limit).all()
    return documents

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific document by ID - organization-specific"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.DIRECTOR, UserRole.EMPLOYEE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view documents"
        )
    
    # Set organization filter
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admin can see all documents
        document = db.query(Document).filter(Document.id == document_id).first()
    else:
        # Other roles can only see documents from their organization
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.organization_id == current_user.organization_id
        ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Log access
    access_log = DocumentAccessLog(
        document_id=document_id,
        user_id=current_user.id,
        action="VIEW"
    )
    db.add(access_log)
    db.commit()
    
    return document

@router.post("/", response_model=DocumentResponse)
async def create_document(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a new document"""
    
    # Validate file type
    allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.zip', '.rar']
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="File type not allowed")
    
    # Validate file size (50MB limit)
    if file.size > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 50MB")
    
    # Save file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Map category to valid enum value
    category_mapping = {
        'Policy': DocumentCategory.HR,
        'Training': DocumentCategory.TRAINING,
        'Reports': DocumentCategory.FINANCIAL,
        'Branding': DocumentCategory.OTHER,
        'Other': DocumentCategory.OTHER
    }
    
    # Create document record
    document = Document(
        title=title,
        description=description,
        category=category_mapping.get(category, DocumentCategory.OTHER),
        document_type=DocumentType.OTHER,  # Default to OTHER, can be enhanced later
        file_name=file.filename,
        file_path=file_path,
        file_size=file.size,
        mime_type=file.content_type,
        file_extension=file_extension,
        uploaded_by=current_user.id,
        organization_id=current_user.organization_id
    )
    
    db.add(document)
    db.commit()
    db.refresh(document)
    
    return document

@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    document_update: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a document - organization-specific"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update documents"
        )
    
    # Set organization filter
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admin can edit all documents
        document = db.query(Document).filter(Document.id == document_id).first()
    else:
        # Other roles can only edit documents from their organization
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.organization_id == current_user.organization_id
        ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check if user has permission to edit (only uploader or admin)
    if document.uploaded_by != current_user.id and current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR]:
        raise HTTPException(status_code=403, detail="Not authorized to edit this document")
    
    for field, value in document_update.dict(exclude_unset=True).items():
        setattr(document, field, value)
    
    document.updated_at = datetime.now()
    db.commit()
    db.refresh(document)
    
    return document

@router.delete("/{document_id}")
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a document - organization-specific"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete documents"
        )
    
    # Set organization filter
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admin can delete all documents
        document = db.query(Document).filter(Document.id == document_id).first()
    else:
        # Other roles can only delete documents from their organization
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.organization_id == current_user.organization_id
        ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check if user has permission to delete (only uploader or admin)
    if document.uploaded_by != current_user.id and current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this document")
    
    # Delete file from filesystem
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    # Delete from database
    db.delete(document)
    db.commit()
    
    return {"message": "Document deleted successfully"}

@router.get("/{document_id}/download")
async def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download a document file - organization-specific"""
    # Check permissions
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.ORG_ADMIN, UserRole.HR, UserRole.MANAGER, UserRole.DIRECTOR, UserRole.EMPLOYEE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to download documents"
        )
    
    # Set organization filter
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admin can download all documents
        document = db.query(Document).filter(Document.id == document_id).first()
    else:
        # Other roles can only download documents from their organization
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.organization_id == current_user.organization_id
        ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check if file exists
    if not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
    
    # Log download access
    access_log = DocumentAccessLog(
        document_id=document_id,
        user_id=current_user.id,
        action="DOWNLOAD"
    )
    db.add(access_log)
    db.commit()
    
    # Return file for download
    return FileResponse(
        path=document.file_path,
        filename=document.file_name,
        media_type=document.mime_type
    ) 