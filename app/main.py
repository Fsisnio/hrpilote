from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from importlib import import_module
from app.core.config import settings
from app.core.mongo import init_mongo, close_mongo
from app.models.mongo_models import ALL_DOCUMENT_MODELS, UserDocument
from app.models.enums import UserRole, UserStatus
from app.core.security import get_password_hash
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def _ensure_super_admin() -> None:
    """Ensure the default super admin exists in Mongo."""
    email = "fala@gmail.com"
    password = "Jesus1993@"
    existing = await UserDocument.find_one(UserDocument.email == email)
    if existing:
        existing.hashed_password = get_password_hash(password)
        await existing.save()
        logger.info("✅ Production super admin password updated: %s", email)
        return

    super_admin = UserDocument(
        email=email,
        username="fala",
        first_name="Fala",
        last_name="Admin",
        hashed_password=get_password_hash(password),
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
        organization_id=None,
        department_id=None,
        manager_id=None,
        is_email_verified=True,
        is_active=True,
    )
    await super_admin.insert()
    logger.info("✅ Production super admin created: %s", email)


async def _ensure_test_user() -> None:
    """Ensure the test production user exists in Mongo."""
    email = "test@gmail.com"
    password = "Test2025"
    existing = await UserDocument.find_one(UserDocument.email == email)
    if existing:
        existing.hashed_password = get_password_hash(password)
        await existing.save()
        logger.info("✅ Production test user password updated: %s", email)
        return

    test_user = UserDocument(
        email=email,
        username="test",
        first_name="Test",
        last_name="User",
        hashed_password=get_password_hash(password),
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.ACTIVE,
        organization_id=None,
        department_id=None,
        manager_id=None,
        is_email_verified=True,
        is_active=True,
    )
    await test_user.insert()
    logger.info("✅ Production test user created: %s", email)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting HR Pilot application...")
    try:
        await init_mongo(document_models=ALL_DOCUMENT_MODELS)
        logger.info("MongoDB connection initialized")
        await _ensure_super_admin()
        await _ensure_test_user()
    except Exception as e:
        logger.error("Failed to initialize database: %s", e)
        logger.warning(
            "Server will continue to run, but database operations may fail until connection is restored."
        )
    
    yield
    
    # Shutdown
    logger.info("Shutting down HR Pilot application...")
    await close_mongo()


# Create FastAPI app
app = FastAPI(
    title="HR Pilot - Multi-Organization HR Management System",
    description="A comprehensive HR management system supporting multiple organizations with role-based access control",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
    expose_headers=["*"],
)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.debug else ["*"]  # Allow all hosts in production for now
)


# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "HR Pilot API is running",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z"
    }

@app.get("/cors-test")
async def cors_test():
    return {
        "message": "CORS is working!",
        "allowed_origins": settings.cors_origins,
        "debug": settings.debug
    }


# Include API routers with error handling per-module
ROUTERS = [
    ("app.api.v1.auth", "/api/v1/auth", ["Authentication"]),
    ("app.api.v1.organizations", "/api/v1/organizations", ["Organizations"]),
    ("app.api.v1.employees", "/api/v1/employees", ["Employees"]),
    ("app.api.v1.training", "/api/v1/training", ["Training"]),
    ("app.api.v1.expenses", "/api/v1/expenses", ["Expenses"]),
    ("app.api.v1.departments", "/api/v1/departments", ["Departments"]),
    ("app.api.v1.attendance", "/api/v1/attendance", ["Attendance"]),
    ("app.api.v1.leave", "/api/v1/leave", ["Leave Management"]),
    ("app.api.v1.payroll", "/api/v1/payroll", ["Payroll"]),
    ("app.api.v1.reports", "/api/v1/reports", ["Reports"]),
    ("app.api.v1.documents", "/api/v1/documents", ["Documents"]),
    ("app.api.v1.users", "/api/v1/users", ["Users"]),
    ("app.api.v1.init", "/api/v1", ["Database Initialization"]),
]

for module_path, prefix, tags in ROUTERS:
    try:
        module = import_module(module_path)
        router = getattr(module, "router", None)
        if router is None:
            logger.warning("Module %s has no router attribute; skipping", module_path)
            continue
        app.include_router(router, prefix=prefix, tags=tags)
        logger.info("Loaded router: %s", module_path)
    except ImportError as e:
        logger.warning("Skipping router %s due to import error: %s", module_path, e)
    except Exception as e:
        logger.error("Failed to include router %s: %s", module_path, e)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    from fastapi.responses import JSONResponse

    logger.error(f"Global exception: {exc}")
    logger.error(traceback.format_exc())

    response = JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error. Please try again later.",
            "error_type": "internal_error",
        },
    )

    origin = request.headers.get("origin")
    if origin and origin in settings.cors_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers[
            "Access-Control-Allow-Headers"
        ] = "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers"

    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    ) 