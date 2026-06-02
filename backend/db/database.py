import os
import logging
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgrespassword@localhost:5432/paralegal_analysis")
SQLITE_FALLBACK_URL = "sqlite+aiosqlite:///./paralegal_analysis.db"

# Engine & Session creation
engine = None
SessionLocal = None

def get_engine():
    global engine, SessionLocal
    if engine is not None:
        return engine

    try:
        logger.info(f"Attempting to connect to database: {DATABASE_URL}")
        # Try primary Postgres engine
        engine = create_async_engine(DATABASE_URL, echo=False, future=True)
        SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        logger.info("Successfully initialized PostgreSQL database engine.")
    except Exception as e:
        logger.warning(f"Failed to connect to primary database ({e}). Falling back to SQLite...")
        engine = create_async_engine(SQLITE_FALLBACK_URL, echo=False, future=True)
        SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        logger.info(f"Initialized fallback SQLite database engine at {SQLITE_FALLBACK_URL}")
    
    return engine

Base = declarative_base()

# ==========================================
# SQLAlchemy Models
# ==========================================

class DBModelBase(Base):
    __abstract__ = True

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    content_text = Column(Text, nullable=True)  # Raw extracted text content
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    jobs = relationship("AnalysisJob", back_populates="document", cascade="all, delete-orphan")


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(String, primary_key=True, index=True)  # job_id (UUID string)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    status = Column(String, default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED
    risk_score = Column(Float, nullable=True)    # Evaluated contract risk score (1-10)
    report_markdown = Column(Text, nullable=True) # Gemini synthesized markdown report
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    document = relationship("Document", back_populates="jobs", lazy="selectin")


async def get_db():
    """Dependency for getting async database sessions"""
    global SessionLocal
    if SessionLocal is None:
        get_engine()
    
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initializes tables for SQLite or Postgres if they don't exist"""
    global engine, SessionLocal
    db_engine = get_engine()
    try:
        logger.info("Synchronizing database tables...")
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database synchronization completed.")
    except Exception as e:
        logger.warning(f"Database sync failed with primary engine ({e}). Re-initializing fallback SQLite database...")
        # Force SQLite fallback globally
        engine = create_async_engine(SQLITE_FALLBACK_URL, echo=False, future=True)
        SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        db_engine = engine
        async with db_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info(f"Fallback SQLite database successfully synchronized at {SQLITE_FALLBACK_URL}")

# Initialize engine and SessionLocal on module load
get_engine()
