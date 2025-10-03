from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.schemas.organization import OrganizationCreate, OrganizationResponse, OrganizationUpdate
from pydantic import BaseModel
from app.api.v1.auth import get_current_user

router = APIRouter()

# Schema for organization creation response with admin info
class OrganizationCreateResponse(BaseModel):
    organization: OrganizationResponse
    admin_user: dict
    message: str


@router.get("/", response_model=list[OrganizationResponse])
async def get_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get organizations
    """
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admin can see all organizations
        organizations = db.query(Organization).all()
    else:
        # Other users can only see their organization
        if current_user.organization_id:
            organizations = db.query(Organization).filter(Organization.id == current_user.organization_id).all()
        else:
            organizations = []
    
    return organizations


@router.post("/", response_model=OrganizationCreateResponse)
async def create_organization(
    organization: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new organization with admin user
    """
    # Only SUPER_ADMIN can create organizations
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super administrators can create organizations"
        )
    
    # Check if organization code already exists
    existing_org = db.query(Organization).filter(Organization.code == organization.code).first()
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization code already exists"
        )
    
    # Create new organization
    db_organization = Organization(**organization.dict())
    db.add(db_organization)
    db.commit()
    db.refresh(db_organization)
    
    # Create admin user for the organization
    from app.core.security import get_password_hash
    from app.models.user import UserStatus
    
    admin_email = f"admin@{organization.code.lower()}.com"
    admin_username = f"admin_{organization.code.lower()}"
    
    # Check if admin user already exists
    existing_admin = db.query(User).filter(User.email == admin_email).first()
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin user already exists for this organization"
        )
    
    # Create admin user
    admin_user = User(
        email=admin_email,
        username=admin_username,
        hashed_password=get_password_hash("Admin123!"),  # Default password
        first_name="Organization",
        last_name="Admin",
        role=UserRole.ORG_ADMIN,
        status=UserStatus.ACTIVE,
        organization_id=db_organization.id,
        is_email_verified=True,
        is_active=True
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    # Return organization with admin info
    return {
        "organization": db_organization,
        "admin_user": {
            "email": admin_email,
            "username": admin_username,
            "password": "Admin123!",
            "role": UserRole.ORG_ADMIN.value
        },
        "message": f"Organization '{db_organization.name}' created successfully with admin user: {admin_email}"
    }


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get specific organization
    """
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Check access permissions
    if current_user.role != UserRole.SUPER_ADMIN and current_user.organization_id != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return organization


@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: int,
    organization_update: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update organization
    """
    # Only SUPER_ADMIN can update organizations
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super administrators can update organizations"
        )
    
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Update organization fields
    update_data = organization_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(organization, field, value)
    
    db.commit()
    db.refresh(organization)
    
    return organization


@router.delete("/{org_id}")
async def delete_organization(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete organization
    """
    # Only SUPER_ADMIN can delete organizations
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super administrators can delete organizations"
        )
    
    organization = db.query(Organization).filter(Organization.id == org_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    db.delete(organization)
    db.commit()
    
    return {"message": "Organization deleted successfully"} 