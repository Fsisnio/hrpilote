from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Configure optional SSL settings for production environments like Render.
engine_kwargs = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "echo": settings.debug,
}

connect_args = {}
if settings.database_ssl_mode:
    connect_args["sslmode"] = settings.database_ssl_mode
if settings.database_ssl_root_cert:
    connect_args["sslrootcert"] = settings.database_ssl_root_cert

if connect_args:
    engine_kwargs["connect_args"] = connect_args

# Create database engine
engine = create_engine(
    settings.database_url,
    **engine_kwargs
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Create all tables in the database
    """
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """
    Drop all tables in the database
    """
    Base.metadata.drop_all(bind=engine) 