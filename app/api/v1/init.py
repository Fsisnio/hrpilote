from fastapi import APIRouter, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from scripts.init_render_db import init_render_database

router = APIRouter()

@router.post("/init-database")
async def initialize_database(db: Session = Depends(get_db)):
    """
    Initialize the database with test users
    This endpoint can be called to create the necessary test users on Render
    """
    try:
        success = init_render_database()
        if success:
            return {
                "success": True,
                "message": "Database initialized successfully with test users",
                "credentials": {
                    "superadmin": "superadmin@hrpilot.com / Password123!",
                    "orgadmin": "orgadmin@hrpilot.com / Password123!",
                    "hr": "hr@hrpilot.com / Password123!",
                    "employee": "employee@hrpilot.com / Password123!"
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initialize database"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initializing database: {str(e)}"
        )
