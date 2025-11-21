from pydantic_settings import BaseSettings
from typing import List, Optional, Union
import os
import json


class Settings(BaseSettings):
    # Database
    # Use local database in development, production database in production
    database_url: str = os.getenv("DATABASE_URL", "postgresql://spero@localhost:5432/hrpilot_test_db")
    database_test_url: str = "postgresql://spero@localhost:5432/hrpilot_test_db"
    database_ssl_mode: Optional[str] = os.getenv("DATABASE_SSL_MODE")
    database_ssl_root_cert: Optional[str] = os.getenv("DATABASE_SSL_ROOT_CERT")
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "your-super-secret-key-here-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # JWT
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-jwt-secret-key-here")
    jwt_algorithm: str = "HS256"
    
    # Email
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: str = "noreply@hrpilot.com"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # File Upload
    upload_dir: str = "uploads"
    max_file_size: int = 10485760  # 10MB
    
    # Application
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    environment: str = os.getenv("ENVIRONMENT", "production")
    cors_origins: Union[List[str], str] = [
        # Development URLs
        "http://localhost:3000", 
        "http://localhost:3001", 
        "http://localhost:3002", 
        "http://localhost:3003", 
        "http://localhost:3005",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001", 
        "http://127.0.0.1:3002",
        "http://127.0.0.1:3003",
        "http://127.0.0.1:3005",
        "http://127.0.0.1:8000",
        # Production URLs
        "https://hrpilotefront.onrender.com",
        "https://hrpiloteback.onrender.com",
        "https://hrpilotefront.onrender.com/",
        "https://hrpiloteback.onrender.com/"
    ]
    
    # Password Policy
    min_password_length: int = 8
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special_chars: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Override CORS origins from environment variable if set
        env_cors_origins = os.getenv("CORS_ORIGINS")
        if env_cors_origins:
            if isinstance(env_cors_origins, str):
                try:
                    # Try to parse as JSON array
                    self.cors_origins = json.loads(env_cors_origins)
                except json.JSONDecodeError:
                    # If not JSON, split by comma
                    self.cors_origins = [origin.strip() for origin in env_cors_origins.split(',')]
            else:
                self.cors_origins = env_cors_origins
        else:
            # Handle CORS_ORIGINS as either string or list
            if isinstance(self.cors_origins, str):
                try:
                    # Try to parse as JSON array
                    self.cors_origins = json.loads(self.cors_origins)
                except json.JSONDecodeError:
                    # If not JSON, split by comma
                    self.cors_origins = [origin.strip() for origin in self.cors_origins.split(',')]


# Create settings instance
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True) 