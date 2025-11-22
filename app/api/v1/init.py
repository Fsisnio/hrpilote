from fastapi import APIRouter, HTTPException, status

from scripts.init_render_db import init_render_database

router = APIRouter()


@router.post("/init-database")
async def initialize_database():
    """
    Initialize the Mongo database with test users.
    This endpoint can be called to create the necessary test users on Render.
    """
    try:
        success = await init_render_database()
        if success:
            return {
                "success": True,
                "message": "Database initialized successfully with test users",
                "credentials": {
                    "superadmin": "superadmin@hrpilot.com / Jesus1993@",
                    "orgadmin": "sal@gmail.com / Jesus1993@",
                    "testuser": "testa@gmail.com / testa123",
                    "employee": "newuser@example.com / Jesus1993@",
                },
            }
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize database",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initializing database: {str(e)}",
        )
