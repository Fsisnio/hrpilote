from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase
from beanie import PydanticObjectId

from app.core.mongo import get_mongo_db
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    validate_password,
    get_password_hash,
    needs_password_rehash,
    is_valid_password_hash,
)
from app.core.config import settings
from app.models.mongo_models import UserDocument
from app.models.enums import UserStatus
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UserProfile,
    AuthResponse,
)

router = APIRouter()
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
) -> UserDocument:
    """
    Get current authenticated user from JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception

        user_id = payload.get("user_id")
        if user_id is None:
            raise credentials_exception

    except Exception:
        raise credentials_exception

    try:
        document_id = PydanticObjectId(user_id)
    except Exception:
        raise credentials_exception

    user = await UserDocument.get(document_id)
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    return user


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Authenticate user and return access token
    """
    print(f"Login attempt for email: {login_data.email}")
    print(f"Password length: {len(login_data.password)}")

    user = await UserDocument.find_one(UserDocument.email == login_data.email)
    if not user:
        print("User not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    print(f"User found: {user.email}")

    if not user.is_active:
        print("User is inactive")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is deactivated",
        )

    if user.locked_until and user.locked_until > datetime.utcnow():
        print("User is locked")
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked",
        )

    if not is_valid_password_hash(user.hashed_password):
        print(f"❌ Invalid password hash detected for user {user.email}")
        print(f"   Hash: {user.hashed_password[:30]}...")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User account has invalid password hash. Please contact administrator.",
        )

    print("Attempting password verification...")
    try:
        password_valid = verify_password(login_data.password, user.hashed_password)
        print(f"Password verification result: {password_valid}")
    except Exception as e:
        print(f"Password verification error: {e}")
        password_valid = False

    if not password_valid:
        print("Password verification failed")
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=30)

        await user.save()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    user.failed_login_attempts = 0
    user.last_login = datetime.utcnow()

    if needs_password_rehash(login_data.password, user.hashed_password):
        print(f"🔄 Re-hashing password for {user.email} with new SHA-256 + bcrypt method")
        user.hashed_password = get_password_hash(login_data.password)

    await user.save()

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "organization_id": str(user.organization_id) if user.organization_id else None,
        },
        expires_delta=access_token_expires,
    )

    refresh_token = create_refresh_token(
        data={"user_id": str(user.id), "email": user.email}
    )

    user_data = {
        "id": str(user.id),
        "email": user.email,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role.value,
        "status": user.status.value if isinstance(user.status, UserStatus) else user.status,
        "organization_id": str(user.organization_id) if user.organization_id else None,
        "department_id": str(user.department_id) if user.department_id else None,
        "manager_id": str(user.manager_id) if user.manager_id else None,
        "is_email_verified": user.is_email_verified,
        "is_active": user.is_active,
    }

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=user_data,
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Refresh access token using refresh token
    """
    try:
        payload = verify_token(refresh_data.refresh_token)
        if payload is None or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        try:
            document_id = PydanticObjectId(user_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        user = await UserDocument.get(document_id)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={
                "user_id": str(user.id),
                "email": user.email,
                "role": user.role.value,
                "organization_id": str(user.organization_id) if user.organization_id else None,
            },
            expires_delta=access_token_expires,
        )

        return RefreshTokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


@router.post("/logout", response_model=AuthResponse)
async def logout(
    current_user: UserDocument = Depends(get_current_user),
):
    """
    Logout user (client should discard tokens)
    """
    return AuthResponse(
        success=True,
        message="Successfully logged out",
    )


@router.post("/logout-no-auth", response_model=AuthResponse)
async def logout_no_auth():
    """
    Logout endpoint that doesn't require authentication
    Useful for client-side logout when token is invalid
    """
    return AuthResponse(
        success=True,
        message="Successfully logged out",
    )


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: UserDocument = Depends(get_current_user),
):
    """
    Get current user profile
    """
    return UserProfile(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role=current_user.role,
        status=current_user.status,
        organization_id=str(current_user.organization_id) if current_user.organization_id else None,
        department_id=str(current_user.department_id) if current_user.department_id else None,
        manager_id=str(current_user.manager_id) if current_user.manager_id else None,
        phone=current_user.phone,
        address=current_user.address,
        date_of_birth=current_user.date_of_birth,
        profile_picture=current_user.profile_picture,
        is_email_verified=current_user.is_email_verified,
        is_active=current_user.is_active,
        last_login=current_user.last_login,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.post("/change-password", response_model=AuthResponse)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: UserDocument = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Change user password
    """
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    password_validation = validate_password(password_data.new_password)
    if not password_validation["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password validation failed: {', '.join(password_validation['errors'])}",
        )

    current_user.hashed_password = get_password_hash(password_data.new_password)
    await current_user.save()

    return AuthResponse(
        success=True,
        message="Password changed successfully",
    )


@router.post("/forgot-password", response_model=AuthResponse)
async def forgot_password(
    forgot_data: ForgotPasswordRequest,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Send password reset email
    """
    user = await UserDocument.find_one(UserDocument.email == forgot_data.email)
    if user:
        # TODO: Implement email sending logic
        pass

    return AuthResponse(
        success=True,
        message="If the email exists, a password reset link has been sent",
    )


@router.post("/reset-password", response_model=AuthResponse)
async def reset_password(
    reset_data: ResetPasswordRequest,
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Reset password using reset token
    """
    # TODO: Implement token verification and password reset logic
    return AuthResponse(
        success=True,
        message="Password reset successfully",
    )