from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings
import re
import hashlib
import base64

# Password hashing context - more robust configuration
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto", 
    bcrypt__default_rounds=12,
    bcrypt__min_rounds=10,
    bcrypt__max_rounds=15
)

def _pre_hash_password(password: str) -> str:
    """
    Pre-hash password with SHA-256 to handle passwords of any length.
    This allows bcrypt to work with passwords longer than 72 bytes.
    Returns a base64-encoded SHA-256 hash.
    """
    # Hash the password with SHA-256
    sha_hash = hashlib.sha256(password.encode('utf-8')).digest()
    # Encode as base64 for a consistent format (44 characters, well under 72 bytes)
    return base64.b64encode(sha_hash).decode('utf-8')


def needs_password_rehash(plain_password: str, hashed_password: str) -> bool:
    """
    Check if a password was hashed with the old method (without SHA-256 pre-hashing)
    and needs to be re-hashed with the new method.
    """
    try:
        # Try to verify with new method
        pre_hashed = _pre_hash_password(plain_password)
        if pwd_context.verify(pre_hashed, hashed_password):
            # Already using new method
            return False
        
        # Check if it verifies with old method (needs rehashing)
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) <= 72:
            if pwd_context.verify(plain_password, hashed_password):
                # Using old method, needs rehashing
                return True
        
        return False
    except Exception:
        return False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash using SHA-256 pre-hashing + bcrypt.
    This handles passwords of any length.
    
    For backward compatibility, if the new method fails, it tries the old method
    (direct bcrypt without pre-hashing) for existing users.
    """
    try:
        # First try the new method (SHA-256 + bcrypt)
        pre_hashed = _pre_hash_password(plain_password)
        if pwd_context.verify(pre_hashed, hashed_password):
            return True
        
        # For backward compatibility: try old method (direct bcrypt)
        # This allows existing users to log in
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) <= 72:
            # Only try old method if password is within bcrypt limits
            if pwd_context.verify(plain_password, hashed_password):
                print(f"⚠️ Password verified with legacy method - should be re-hashed")
                return True
        
        return False
        
    except Exception as e:
        print(f"Password verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password using SHA-256 pre-hashing + bcrypt.
    This handles passwords of any length securely.
    """
    try:
        # Validate password input
        if not password or not isinstance(password, str):
            raise ValueError("Password must be a non-empty string")
        
        # Pre-hash the password with SHA-256 to handle any length
        pre_hashed = _pre_hash_password(password)
        
        # Generate bcrypt hash (pre-hashed password is only 44 characters, well under 72 bytes)
        hashed = pwd_context.hash(pre_hashed)
        
        # Validate the generated hash
        if not hashed or not hashed.startswith('$2b$'):
            raise ValueError(f"Generated invalid hash format")
        
        return hashed
        
    except Exception as e:
        print(f"❌ Password hashing error: {e}")
        raise ValueError(f"Failed to hash password: {str(e)}")


def validate_password(password: str) -> dict:
    """
    Validate password against policy requirements
    """
    errors = []
    
    if len(password) < settings.min_password_length:
        errors.append(f"Password must be at least {settings.min_password_length} characters long")
    
    if settings.require_uppercase and not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if settings.require_lowercase and not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if settings.require_numbers and not re.search(r'\d', password):
        errors.append("Password must contain at least one number")
    
    if settings.require_special_chars and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """
    Verify and decode JWT token
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None


def get_token_expiration(token: str) -> Optional[datetime]:
    """
    Get token expiration time
    """
    payload = verify_token(token)
    if payload and "exp" in payload:
        return datetime.fromtimestamp(payload["exp"])
    return None


def is_token_expired(token: str) -> bool:
    """
    Check if token is expired
    """
    exp_time = get_token_expiration(token)
    if exp_time:
        return datetime.utcnow() > exp_time
    return True


def is_valid_password_hash(password_hash: str) -> bool:
    """
    Check if a password hash is valid (bcrypt format)
    """
    if not password_hash or not isinstance(password_hash, str):
        return False
    
    # Check if it's a valid bcrypt hash
    if not password_hash.startswith('$2b$'):
        return False
    
    # Check if it has the right structure
    parts = password_hash.split('$')
    if len(parts) != 4:
        return False
    
    # Check if it has the right length (bcrypt hashes are 60 characters)
    if len(password_hash) != 60:
        return False
    
    return True


def fix_invalid_password_hash(user_id: int, new_password: str, db) -> bool:
    """
    Fix a user's invalid password hash
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        # Generate new valid hash
        new_hash = get_password_hash(new_password)
        
        # Update user
        user.hashed_password = new_hash
        user.failed_login_attempts = 0
        user.locked_until = None
        
        db.commit()
        print(f"✅ Fixed password hash for user {user.email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to fix password hash for user {user_id}: {e}")
        db.rollback()
        return False 