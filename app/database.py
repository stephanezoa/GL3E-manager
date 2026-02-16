"""
Database configuration and session management
"""
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings


def _resolve_database_url(url: str) -> str:
    """
    Resolve relative SQLite URLs to absolute project paths.
    Prevents using different DB files when process CWD changes.
    """
    if url.startswith("sqlite:///./"):
        project_root = Path(__file__).resolve().parent.parent
        db_file = url.replace("sqlite:///./", "", 1)
        return f"sqlite:///{(project_root / db_file).as_posix()}"
    return url


resolved_database_url = _resolve_database_url(settings.DATABASE_URL)

# Create database engine
engine = create_engine(
    resolved_database_url,
    connect_args={"check_same_thread": False} if "sqlite" in resolved_database_url else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency to get database session
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    # Ensure all models are imported so SQLAlchemy metadata is fully populated.
    # Without this, create_all may run with an incomplete table registry.
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
