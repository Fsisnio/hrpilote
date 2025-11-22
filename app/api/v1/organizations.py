from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from motor.motor_asyncio import AsyncIOMotorDatabase
from beanie import PydanticObjectId
from pydantic import BaseModel

from app.core.mongo import get_mongo_db
from app.api.v1.auth import get_current_user
from app.models.mongo_models import OrganizationDocument, UserDocument
from app.models.enums import UserRole, UserStatus
from app.schemas.organization import OrganizationCreate, OrganizationResponse, OrganizationUpdate
from app.core.security import get_password_hash

router = APIRouter()


class OrganizationCreateResponse(BaseModel):
    organization: OrganizationResponse
    admin_user: dict
    message: str


def _organization_to_response(doc: OrganizationDocument) -> OrganizationResponse:
    data = doc.model_dump()
    data["id"] = str(doc.id)
    return OrganizationResponse(**jsonable_encoder(data))


@router.get("/", response_model=list[OrganizationResponse])
async def get_organizations(
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Get organizations
    """
    try:
        if current_user.role == UserRole.SUPER_ADMIN:
            organizations = await OrganizationDocument.find_all().to_list()
        else:
            if current_user.organization_id:
                # Use get() for single organization lookup
                organization = await OrganizationDocument.get(current_user.organization_id)
                organizations = [organization] if organization else []
            else:
                organizations = []

        # Convert organizations to responses with error handling
        org_responses = []
        for org in organizations:
            try:
                response = _organization_to_response(org)
                org_responses.append(response)
            except Exception as e:
                print(f"Error converting organization {org.id} to response: {str(e)}")
                import traceback
                traceback.print_exc()
                raise
        
        return org_responses
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error fetching organizations: {str(e)}")
        print(f"Traceback: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching organizations: {str(e)}"
        )


@router.post("/", response_model=OrganizationCreateResponse)
async def create_organization(
    organization: OrganizationCreate,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Create a new organization with admin user
    """
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super administrators can create organizations",
        )

    existing_org = await OrganizationDocument.find_one(OrganizationDocument.code == organization.code)
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization code already exists",
        )

    db_organization = OrganizationDocument(**organization.dict())
    await db_organization.insert()

    admin_email = f"admin@{organization.code.lower()}.com"
    admin_username = f"admin_{organization.code.lower()}"

    existing_admin = await UserDocument.find_one(UserDocument.email == admin_email)
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin user already exists for this organization",
        )

    admin_user = UserDocument(
        email=admin_email,
        username=admin_username,
        hashed_password=get_password_hash("Admin123!"),
        first_name="Organization",
        last_name="Admin",
        role=UserRole.ORG_ADMIN,
        status=UserStatus.ACTIVE,
        organization_id=db_organization.id,
        is_email_verified=True,
        is_active=True,
    )

    await admin_user.insert()

    return {
        "organization": _organization_to_response(db_organization),
        "admin_user": {
            "email": admin_email,
            "username": admin_username,
            "password": "Admin123!",
            "role": UserRole.ORG_ADMIN.value,
        },
        "message": f"Organization '{db_organization.name}' created successfully with admin user: {admin_email}",
    }


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Get specific organization
    """
    try:
        doc_id = PydanticObjectId(org_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    organization = await OrganizationDocument.get(doc_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    if current_user.role != UserRole.SUPER_ADMIN and current_user.organization_id != organization.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return _organization_to_response(organization)


@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    organization_update: OrganizationUpdate,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Update organization
    """
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super administrators can update organizations",
        )

    try:
        doc_id = PydanticObjectId(org_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    organization = await OrganizationDocument.get(doc_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    update_data = organization_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(organization, field, value)

    await organization.save()

    return _organization_to_response(organization)


@router.delete("/{org_id}")
async def delete_organization(
    org_id: str,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Delete organization
    """
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super administrators can delete organizations",
        )

    try:
        doc_id = PydanticObjectId(org_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    organization = await OrganizationDocument.get(doc_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    await organization.delete()

    return {"message": "Organization deleted successfully"}