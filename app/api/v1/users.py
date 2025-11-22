from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from beanie import PydanticObjectId
from pydantic import BaseModel

from app.core.mongo import get_mongo_db
from app.models.mongo_models import UserDocument
from app.models.enums import UserRole, UserStatus
from app.schemas.auth import UserProfile
from app.api.v1.auth import get_current_user
from app.core.security import get_password_hash, is_valid_password_hash

# Request/Response models
class UserCreate(BaseModel):
    email: str
    username: str
    password: str
    first_name: str
    last_name: str
    role: UserRole
    status: UserStatus = UserStatus.ACTIVE
    phone: Optional[str] = None
    organization_id: Optional[str] = None
    
    model_config = {"from_attributes": True}
    
    def model_post_init(self, __context) -> None:
        """Validate password length after model initialization"""
        if self.password:
            password_bytes = self.password.encode('utf-8')
            if len(password_bytes) > 72:
                raise ValueError("Password cannot be longer than 72 bytes (approximately 72 characters for ASCII, fewer for Unicode characters like emojis)")

class UserUpdate(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    phone: Optional[str] = None
    organization_id: Optional[str] = None
    
    model_config = {"from_attributes": True}
    
    def model_post_init(self, __context) -> None:
        """Validate password length after model initialization"""
        if self.password:
            password_bytes = self.password.encode('utf-8')
            if len(password_bytes) > 72:
                raise ValueError("Password cannot be longer than 72 bytes (approximately 72 characters for ASCII, fewer for Unicode characters like emojis)")

router = APIRouter()


def _can_manage_users(user: UserDocument) -> bool:
    """Check if user has permission to manage users"""
    return user.role in [
        UserRole.SUPER_ADMIN,
        UserRole.ORG_ADMIN,
        UserRole.HR,
    ]


def _user_to_profile(user: UserDocument) -> UserProfile:
    return UserProfile(
        id=str(user.id),
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        status=user.status,
        organization_id=str(user.organization_id) if user.organization_id else None,
        department_id=str(user.department_id) if user.department_id else None,
        manager_id=str(user.manager_id) if user.manager_id else None,
        phone=user.phone,
        address=user.address,
        date_of_birth=user.date_of_birth,
        profile_picture=user.profile_picture,
        is_email_verified=user.is_email_verified,
        is_active=user.is_active,
        last_login=user.last_login,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("/", response_model=List[UserProfile])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    organization_id: Optional[str] = None,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Get list of users with filtering options
    """
    try:
        # Check permissions - allow users who can manage users, or managers/directors to view users
        if not _can_manage_users(current_user) and current_user.role not in [UserRole.MANAGER, UserRole.DIRECTOR]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view users"
            )
        
        # Build query
        query = {}

        if current_user.role == UserRole.SUPER_ADMIN:
            pass
        else:
            if current_user.organization_id:
                query["organization_id"] = current_user.organization_id
            else:
                # If user has no organization, return empty list
                # This can happen if org admin was created without organization_id
                print(f"Warning: User {current_user.email} (role: {current_user.role.value}) has no organization_id")
                return []

        if role:
            query["role"] = role
        if status:
            query["status"] = status
        if organization_id and current_user.role == UserRole.SUPER_ADMIN:
            try:
                query["organization_id"] = PydanticObjectId(organization_id)
            except Exception:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid organization ID")

        users = await UserDocument.find(query).skip(skip).limit(limit).to_list()
        
        # Convert users to profiles with error handling
        user_profiles = []
        for user in users:
            try:
                profile = _user_to_profile(user)
                user_profiles.append(profile)
            except Exception as e:
                print(f"Error converting user {user.id} to profile: {str(e)}")
                import traceback
                traceback.print_exc()
                raise

        return user_profiles
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error fetching users: {str(e)}")
        print(f"Traceback: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching users: {str(e)}"
        )


@router.get("/{user_id}", response_model=UserProfile)
async def get_user(
    user_id: str,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Get specific user by ID
    """
    try:
        # Check permissions - allow users who can manage users, or users viewing their own profile
        if not _can_manage_users(current_user) and str(current_user.id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this user"
            )
        
        try:
            doc_id = PydanticObjectId(user_id)
        except Exception:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user = await UserDocument.get(doc_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check organization access
        if current_user.role != UserRole.SUPER_ADMIN:
            if user.organization_id != current_user.organization_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this user"
                )
        
        return _user_to_profile(user)
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error fetching user: {str(e)}")
        print(f"Traceback: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user: {str(e)}"
        )


@router.post("/")
async def create_user(
    user_data: UserCreate,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Create a new user
    """
    try:
        # Check permissions
        if not _can_manage_users(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create users"
            )
        
        # Set organization_id based on current user's role
        organization_id = user_data.organization_id
        target_org_id: Optional[PydanticObjectId] = None

        if current_user.role == UserRole.ORG_ADMIN:
            if not current_user.organization_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Organization context missing for admin user",
                )
            target_org_id = current_user.organization_id
        elif current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create users"
            )
        elif organization_id:
            try:
                target_org_id = PydanticObjectId(organization_id)
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid organization ID",
                )
        
        # Check if email already exists within the same organization
        existing_user = await UserDocument.find_one(
            {
                "email": user_data.email,
                "organization_id": target_org_id if target_org_id else current_user.organization_id,
            }
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered in this organization"
            )
        
        # Check if username already exists
        existing_username = await UserDocument.find_one(UserDocument.username == user_data.username)
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create new user with validated password hash
        try:
            hashed_password = get_password_hash(user_data.password)

            if not is_valid_password_hash(hashed_password):
                raise ValueError(f"Generated invalid password hash: {hashed_password[:20]}...")
            
            print(f"✅ Creating user {user_data.email} with valid password hash")
            
        except Exception as e:
            print(f"❌ Password hashing failed for user {user_data.email}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to hash password: {str(e)}"
            )
        
        new_user = UserDocument(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role,
            status=user_data.status,
            phone=user_data.phone,
            organization_id=target_org_id,
            is_email_verified=True,  # Admin created users are considered verified
            is_active=True
        )
        
        await new_user.insert()
        
        # Return simple response first
        return {
            "id": str(new_user.id),
            "email": new_user.email,
            "username": new_user.username,
            "first_name": new_user.first_name,
            "last_name": new_user.last_name,
            "role": new_user.role.value,
            "status": new_user.status.value,
            "organization_id": new_user.organization_id,
            "message": "User created successfully"
        }
        
    except HTTPException:
        # Re-raise HTTPExceptions (like validation errors) as-is
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"User creation error: {str(e)}")
        print(f"Traceback: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating user: {str(e)}"
        )


@router.put("/{user_id}", response_model=UserProfile)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Update user information
    """
    # Check permissions - allow users who can manage users, or users updating their own profile
    if not _can_manage_users(current_user) and str(current_user.id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update users"
        )
    
    try:
        doc_id = PydanticObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user = await UserDocument.get(doc_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check organization access
    if current_user.role != UserRole.SUPER_ADMIN:
        if user.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this user"
            )
    
    # Update fields
    update_data = user_data.model_dump(exclude_unset=True)
    
    # Handle password update
    if 'password' in update_data and update_data['password']:
        update_data['hashed_password'] = get_password_hash(update_data['password'])
        del update_data['password']
    
    # Update user
    for field, value in update_data.items():
        setattr(user, field, value)

    await user.save()

    return _user_to_profile(user)


@router.put("/{user_id}/status")
async def update_user_status(
    user_id: str,
    new_status: UserStatus,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Update user status
    """
    # Check permissions
    if not _can_manage_users(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update user status"
        )
    
    try:
        doc_id = PydanticObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user = await UserDocument.get(doc_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check organization access
    if current_user.role != UserRole.SUPER_ADMIN:
        if user.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this user"
            )
    
    # Prevent self-deactivation
    if user.id == current_user.id and new_status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    user.status = new_status
    await user.save()
    
    return {"message": f"User status updated to {new_status.value}"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Delete user (soft delete by setting status to INACTIVE)
    """
    # Check permissions
    if not _can_manage_users(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete users"
        )
    
    try:
        doc_id = PydanticObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user = await UserDocument.get(doc_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check organization access
    if current_user.role != UserRole.SUPER_ADMIN:
        if user.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this user"
            )
    
    # Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Soft delete
    user.status = UserStatus.INACTIVE
    user.is_active = False
    await user.save()
    
    return {"message": "User deleted successfully"} 