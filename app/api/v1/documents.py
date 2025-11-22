from datetime import datetime
import os
from typing import List, Optional

from beanie import PydanticObjectId
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.v1.auth import get_current_user
from app.core.mongo import get_mongo_db
from app.models.enums import (
    DocumentCategory,
    DocumentStatus,
    DocumentType,
    UserRole,
)
from app.models.mongo_models import (
    DocumentAccessLogDocument,
    DocumentDocument,
    UserDocument,
)
from app.schemas.document import DocumentResponse, DocumentUpdate

router = APIRouter()

UPLOAD_DIR = "uploads/documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".txt",
    ".zip",
    ".rar",
}


def _parse_object_id(value: str, field_name: str) -> PydanticObjectId:
    try:
        return PydanticObjectId(value)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{field_name} not found",
        )


def _stringify(value: Optional[PydanticObjectId]) -> Optional[str]:
    return str(value) if value else None


def _map_category(category: Optional[str]) -> Optional[DocumentCategory]:
    if not category:
        return None
    normalized = category.upper()
    try:
        return DocumentCategory(normalized)
    except ValueError:
        category_mapping = {
            "POLICY": DocumentCategory.HR,
            "TRAINING": DocumentCategory.TRAINING,
            "REPORTS": DocumentCategory.FINANCIAL,
            "BRANDING": DocumentCategory.OTHER,
            "OTHER": DocumentCategory.OTHER,
        }
        mapped = category_mapping.get(normalized)
        if not mapped:
            raise HTTPException(status_code=400, detail="Invalid document category")
        return mapped


def _can_view_documents(user: UserDocument) -> bool:
    return user.role in [
        UserRole.SUPER_ADMIN,
        UserRole.ORG_ADMIN,
        UserRole.HR,
        UserRole.MANAGER,
        UserRole.DIRECTOR,
        UserRole.PAYROLL,
        UserRole.EMPLOYEE,
    ]


def _can_manage_documents(user: UserDocument) -> bool:
    return user.role in [
        UserRole.SUPER_ADMIN,
        UserRole.ORG_ADMIN,
        UserRole.HR,
        UserRole.MANAGER,
    ]


def _document_to_response(document: DocumentDocument) -> DocumentResponse:
    return DocumentResponse(
        id=str(document.id),
        organization_id=str(document.organization_id),
        title=document.title,
        description=document.description,
        category=document.category,
        document_type=document.document_type,
        status=document.status,
        is_public=document.is_public,
        requires_approval=document.requires_approval,
        file_name=document.file_name,
        file_path=document.file_path,
        file_size=document.file_size,
        mime_type=document.mime_type,
        file_extension=document.file_extension,
        version=document.version,
        is_latest_version=document.is_latest_version,
        parent_document_id=_stringify(document.parent_document_id),
        uploaded_by=_stringify(document.uploaded_by),
        approved_by=_stringify(document.approved_by),
        approved_at=document.approved_at,
        employee_id=_stringify(document.employee_id),
        department_id=_stringify(document.department_id),
        expiry_date=document.expiry_date,
        retention_period_years=document.retention_period_years,
        tags=document.tags,
        document_metadata=document.document_metadata,
        created_at=document.created_at,
        updated_at=document.updated_at,
    )


async def _get_document_or_404(
    document_id: str,
    current_user: UserDocument,
) -> DocumentDocument:
    doc_object_id = _parse_object_id(document_id, "Document")
    document = await DocumentDocument.get(doc_object_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if current_user.role != UserRole.SUPER_ADMIN:
        if not current_user.organization_id or document.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Access denied")

    return document


async def _log_access(
    document: DocumentDocument,
    user: UserDocument,
    action: str,
) -> None:
    log = DocumentAccessLogDocument(
        document_id=document.id,
        user_id=user.id,
        action=action,
    )
    await log.insert()


def _ensure_upload_directory() -> None:
    os.makedirs(UPLOAD_DIR, exist_ok=True)


async def _ensure_user_has_org(user: UserDocument) -> PydanticObjectId:
    if not user.organization_id:
        raise HTTPException(
            status_code=400,
            detail="User is not associated with an organization",
        )
    return user.organization_id


@router.get("/", response_model=List[DocumentResponse])
async def get_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = None,
    search: Optional[str] = None,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get all documents with optional filtering."""
    if not _can_view_documents(current_user):
        raise HTTPException(status_code=403, detail="Not authorized to view documents")

    query: Dict[str, Any] = {}
    if current_user.role != UserRole.SUPER_ADMIN:
        query["organization_id"] = current_user.organization_id

    if category:
        query["category"] = _map_category(category)

    criteria = []
    if search:
        regex = {"$regex": search, "$options": "i"}
        criteria.append({"title": regex})
        criteria.append({"description": regex})

    if criteria:
        query["$or"] = criteria

    documents = (
        await DocumentDocument.find(query)
        .sort("-created_at")
        .skip(skip)
        .limit(limit)
        .to_list()
    )
    return [_document_to_response(doc) for doc in documents]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get a document by ID."""
    if not _can_view_documents(current_user):
        raise HTTPException(status_code=403, detail="Not authorized to view documents")

    document = await _get_document_or_404(document_id, current_user)
    await _log_access(document, current_user, "VIEW")
    return _document_to_response(document)


@router.post("/", response_model=DocumentResponse)
async def create_document(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    category: str = Form(...),
    file: UploadFile = File(...),
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Upload a new document."""
    if not _can_view_documents(current_user):
        raise HTTPException(status_code=403, detail="Not authorized to upload documents")

    organization_id = await _ensure_user_has_org(current_user)
    category_enum = _map_category(category) or DocumentCategory.OTHER

    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="File type not allowed")

    content = await file.read()
    file_size = len(content)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 50MB")

    _ensure_upload_directory()
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename.replace(' ', '_')}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    with open(file_path, "wb") as buffer:
        buffer.write(content)

    document = DocumentDocument(
        title=title,
        description=description,
        category=category_enum,
        document_type=DocumentType.OTHER,
        file_name=file.filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=file.content_type,
        file_extension=file_extension,
        uploaded_by=current_user.id,
        organization_id=organization_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    await document.insert()

    return _document_to_response(document)


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    document_update: DocumentUpdate,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Update an existing document."""
    if not _can_manage_documents(current_user):
        raise HTTPException(status_code=403, detail="Not authorized to update documents")

    document = await _get_document_or_404(document_id, current_user)

    if document.uploaded_by != current_user.id and current_user.role not in [
        UserRole.SUPER_ADMIN,
        UserRole.ORG_ADMIN,
        UserRole.HR,
    ]:
        raise HTTPException(status_code=403, detail="Not authorized to edit this document")

    update_data = document_update.dict(exclude_unset=True)

    if "category" in update_data and update_data["category"]:
        update_data["category"] = _map_category(update_data["category"].value if isinstance(update_data["category"], DocumentCategory) else update_data["category"])

    if "status" in update_data and update_data["status"]:
        if isinstance(update_data["status"], DocumentStatus):
            update_data["status"] = update_data["status"]
        else:
            try:
                update_data["status"] = DocumentStatus(update_data["status"])
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid document status")

    for field, value in update_data.items():
        setattr(document, field, value)

    document.updated_at = datetime.utcnow()
    await document.save()

    return _document_to_response(document)


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Delete a document."""
    if not _can_manage_documents(current_user):
        raise HTTPException(status_code=403, detail="Not authorized to delete documents")

    document = await _get_document_or_404(document_id, current_user)

    if document.uploaded_by != current_user.id and current_user.role not in [
        UserRole.SUPER_ADMIN,
        UserRole.ORG_ADMIN,
        UserRole.HR,
    ]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this document")

    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    await document.delete()

    return {"message": "Document deleted successfully"}


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Download a document file."""
    if not _can_view_documents(current_user):
        raise HTTPException(status_code=403, detail="Not authorized to download documents")

    document = await _get_document_or_404(document_id, current_user)

    if not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")

    await _log_access(document, current_user, "DOWNLOAD")

    return FileResponse(
        path=document.file_path,
        filename=document.file_name,
        media_type=document.mime_type or "application/octet-stream",
    )