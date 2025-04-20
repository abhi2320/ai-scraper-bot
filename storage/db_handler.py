# storage/db_handler.py
from sqlalchemy import create_engine, Column, Integer, String, Text, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector
import datetime
from config import DATABASE_URL
from utils.logger import get_logger

logger = get_logger(__name__)

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Keep ORM objects bound after commit
)


class ScrapedPage(Base):
    __tablename__ = "scraped_pages"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    page_metadata = Column(JSON, nullable=True)
    embedding = Column(Vector(1536))  # For OpenAI embeddings
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<ScrapedPage(id={self.id}, url='{self.url}', title='{self.title}')>"


def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


def get_db_session():
    """Get database session"""
    session = SessionLocal()
    try:
        return session
    except Exception as e:
        session.close()
        raise e


def save_data(url, title, content, page_metadata=None):
    """Save scraped data to database without embedding"""
    session = get_db_session()
    try:
        existing = session.query(ScrapedPage).filter_by(url=url).first()
        
        if existing:
            # Update existing record
            existing.title = title
            existing.content = content
            existing.page_metadata = page_metadata or {}
            existing.updated_at = datetime.datetime.utcnow()
            session.add(existing)
            session.commit()
            session.refresh(existing)
            logger.info(f"Updated existing record for URL: {url}")
            return existing
        else:
            # Create new record
            page = ScrapedPage(
                url=url,
                title=title,
                content=content,
                page_metadata=page_metadata or {}
            )
            session.add(page)
            session.commit()
            session.refresh(page) 
            logger.info(f"Created new record for URL: {url}")
            return page
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving data: {e}")
        raise
    finally:
        session.close()