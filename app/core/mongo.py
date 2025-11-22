from typing import Optional, AsyncGenerator

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings
# NOTE: Models will be registered with Beanie during init_mongo().

mongodb_client: Optional[AsyncIOMotorClient] = None
mongodb_db: Optional[AsyncIOMotorDatabase] = None


async def init_mongo(document_models: Optional[list] = None) -> None:
    """
    Initialize the MongoDB client and register Beanie document models.

    Args:
        document_models: Optional list of Beanie document classes to register.
            If omitted, the caller must call init_beanie manually later.
    """
    global mongodb_client, mongodb_db

    if mongodb_client:
        return

    mongodb_client = AsyncIOMotorClient(settings.mongodb_uri)
    mongodb_db = mongodb_client[settings.mongodb_db_name]

    if document_models:
        await init_beanie(
            database=mongodb_db,
            document_models=document_models,
            allow_index_dropping=True,
        )


async def close_mongo() -> None:
    """Close the MongoDB client if it exists."""
    global mongodb_client, mongodb_db

    if mongodb_client:
        mongodb_client.close()

    mongodb_client = None
    mongodb_db = None


async def get_mongo_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """
    Dependency for FastAPI routes to access the Mongo database.
    Ensures the client is initialized before yielding the database.
    """
    if mongodb_db is None:
        await init_mongo()

    assert mongodb_db is not None  # For type checkers
    yield mongodb_db

