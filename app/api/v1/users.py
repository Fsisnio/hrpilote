from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.user import User, UserRole, UserStatus
from app.schemas.auth import UserProfile
from app.api.v1.auth import get_current_user
from app.core.security import get_password_hash
from pydantic import BaseModel

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
    organization_id: Optional[int] = None
    
    model_config = {"from_attributes": True}

class UserUpdate(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    phone: Optional[str] = None
    organization_id: Optional[int] = None
    
    model_config = {"from_attributes": True}

router = APIRouter()


@router.get("/", response_model=List[UserProfile])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    organization_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of users with filtering options
    """
    # Check permissions
    if not current_user.can_manage_users and current_user.role not in [UserRole.MANAGER, UserRole.DIRECTOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view users"
        )
    
    # Build query
    query = db.query(User)
    
    # Apply filters based on user role
    if current_user.role == UserRole.SUPER_ADMIN:
        # Super admin can see all users
        pass
    elif current_user.role == UserRole.ORG_ADMIN:
        # Org admin can only see users in their organization
        query = query.filter(User.organization_id == current_user.organization_id)
    else:
        # HR, Manager, Director, and other roles can only see users in their organization
        query = query.filter(User.organization_id == current_user.organization_id)
    
    # Apply additional filters
    if role:
        query = query.filter(User.role == role)
    if status:
        query = query.filter(User.status == status)
    if organization_id and current_user.role == UserRole.SUPER_ADMIN:
        query = query.filter(User.organization_id == organization_id)
    
    # Apply pagination
    users = query.offset(skip).limit(limit).all()
    
    return users


@router.get("/{user_id}", response_model=UserProfile)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get specific user by ID
    """
    # Check permissions
    if not current_user.can_manage_users and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
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
    
    return user


@router.post("/")
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new user
    """
    try:
        # Check permissions
        if not current_user.can_manage_users:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create users"
            )
        
        # Set organization_id based on current user's role
        organization_id = user_data.organization_id
        if current_user.role == UserRole.ORG_ADMIN:
            organization_id = current_user.organization_id
        elif current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create users"
            )
        
        # Check if email already exists within the same organization
        existing_user = db.query(User).filter(
            User.email == user_data.email,
            User.organization_id == organization_id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered in this organization"
            )
        
        # Check if username already exists
        existing_username = db.query(User).filter(User.username == user_data.username).first()
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create new user with validated password hash
        try:
            hashed_password = get_password_hash(user_data.password)
            
            # Validate the generated hash
            from app.core.security import is_valid_password_hash
            if not is_valid_password_hash(hashed_password):
                raise ValueError(f"Generated invalid password hash: {hashed_password[:20]}...")
            
            print(f"✅ Creating user {user_data.email} with valid password hash")
            
        except Exception as e:
            print(f"❌ Password hashing failed for user {user_data.email}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to hash password: {str(e)}"
            )
        
        new_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role,
            status=user_data.status,
            phone=user_data.phone,
            organization_id=organization_id,
            is_email_verified=True,  # Admin created users are considered verified
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Return simple response first
        return {
            "id": new_user.id,
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
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
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
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user information
    """
    # Check permissions
    if not current_user.can_manage_users and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update users"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
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
    
    db.commit()
    db.refresh(user)
    
    return user


@router.put("/{user_id}/status")
async def update_user_status(
    user_id: int,
    new_status: UserStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user status
    """
    # Check permissions
    if not current_user.can_manage_users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update user status"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
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
    db.commit()
    db.refresh(user)
    
    return {"message": f"User status updated to {new_status.value}"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete user (soft delete by setting status to INACTIVE)
    """
    # Check permissions
    if not current_user.can_manage_users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete users"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
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
    db.commit()
    
    return {"message": "User deleted successfully"} 