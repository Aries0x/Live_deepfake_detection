"""
Database connection and session lifecycle management.
Supports both PostgreSQL (asyncpg) and SQLite (aiosqlite) with automated initialization.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from backend.app.config import settings
from backend.app.logging_config import get_logger

logger = get_logger("database")
Base = declarative_base()

# Configure engine with connection pooling where supported
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args=connect_args,
    future=True,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db():
    """Create all database tables on application startup."""
    try:
        async with engine.begin() as conn:
            # Import models to ensure all are registered on Base.metadata
            import backend.app.models.models  # noqa: F401
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully", db_url=settings.DATABASE_URL.split("@")[-1])
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise e


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing database session to FastAPI route handlers."""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
