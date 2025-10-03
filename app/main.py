from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import create_tables
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting HR Pilot application...")
    try:
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down HR Pilot application...")


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


# Include API routers with error handling
try:
    from app.api.v1 import auth, users, organizations, employees, attendance, leave, payroll, reports, documents, training, expenses, init
    
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
    app.include_router(organizations.router, prefix="/api/v1/organizations", tags=["Organizations"])
    app.include_router(employees.router, prefix="/api/v1/employees", tags=["Employees"])
    app.include_router(attendance.router, prefix="/api/v1/attendance", tags=["Attendance"])
    app.include_router(leave.router, prefix="/api/v1/leave", tags=["Leave Management"])
    app.include_router(payroll.router, prefix="/api/v1/payroll", tags=["Payroll"])
    app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
    app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
    app.include_router(training.router, prefix="/api/v1/training", tags=["Training"])
    app.include_router(expenses.router, prefix="/api/v1/expenses", tags=["Expenses"])
    app.include_router(init.router, prefix="/api/v1", tags=["Database Initialization"])
    
    logger.info("All API routers loaded successfully")
except ImportError as e:
    logger.warning(f"Some API modules could not be loaded: {e}")
    logger.info("Running with limited functionality")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    logger.error(f"Global exception: {exc}")
    logger.error(traceback.format_exc())
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    ) 