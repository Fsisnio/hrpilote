from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from app.models.enums import UserRole, UserStatus


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class UserProfile(BaseModel):
    id: str  # MongoDB ObjectId as string
    email: str
    username: str
    first_name: str
    last_name: str
    role: UserRole
    status: UserStatus
    organization_id: Optional[str] = None  # MongoDB ObjectId as string
    department_id: Optional[str] = None  # MongoDB ObjectId as string
    manager_id: Optional[str] = None  # MongoDB ObjectId as string
    phone: Optional[str] = None
    address: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    profile_picture: Optional[str] = None
    is_email_verified: bool
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class TokenData(BaseModel):
    user_id: Optional[str] = None  # MongoDB ObjectId as string
    email: Optional[str] = None
    role: Optional[UserRole] = None
    organization_id: Optional[str] = None  # MongoDB ObjectId as string


class AuthResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None 