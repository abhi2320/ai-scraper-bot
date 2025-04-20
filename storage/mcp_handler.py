# storage/db_handler.py
from sqlalchemy import create_engine, Column, Integer, String, Text, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from openai import OpenAI
from config import OPENAI_API_KEY, EMBEDDING_MODEL
from storage.db_handler import get_db_session, ScrapedPage
from pgvector.sqlalchemy import Vector
import datetime
from config import DATABASE_URL
from utils.logger import get_logger

logger = get_logger(__name__)

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

client = OpenAI(api_key=OPENAI_API_KEY)


def embed_content(content: str) -> list:
    """
    Generate vector embedding for given content using OpenAI
    """
    try:
        response = client.embeddings.create(
            input=content,
            model=EMBEDDING_MODEL
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        raise


def process_and_store(url: str, title: str, content: str, page_metadata: dict) -> ScrapedPage:
    """
    Store a scraped page with its OpenAI embedding
    - Updates record if URL exists
    - Embeds content and saves to pgvector
    """
    session: Session = get_db_session()
    try:
        logger.info(f"Embedding content for URL: {url}")
        embedding = embed_content(content)

        page = session.query(ScrapedPage).filter_by(url=url).first()

        if page:
            logger.info(f"Updating existing page for URL: {url}")
            page.title = title
            page.content = content
            page.page_metadata = page_metadata
            page.embedding = embedding
        else:
            logger.info(f"Inserting new page for URL: {url}")
            page = ScrapedPage(
                url=url,
                title=title,
                content=content,
                page_metadata=page_metadata,
                embedding=embedding
            )
            session.add(page)

        session.commit()
        session.refresh(page)
        session.expunge(page) 
        return page

    except Exception as e:
        session.rollback()
        logger.error(f"Failed to process and store page: {e}", exc_info=True)
        raise
    finally:
        session.close()


def vector_search(query: str, limit: int = 5) -> list[tuple[ScrapedPage, float]]:
    """
    Search pages using pgvector similarity (cosine)
    Returns list of (ScrapedPage, distance) tuples
    """
    logger.info(f"Performing vector search for query: '{query}'")
    embedding = embed_content(query)

    session: Session = get_db_session()
    try:
        sql = text("""
            SELECT id, embedding <-> :embedding AS distance
            FROM scraped_pages
            ORDER BY embedding <-> :embedding
            LIMIT :limit
        """)

        result = session.execute(sql, {"embedding": embedding, "limit": limit}).fetchall()

        pages = []
        for row in result:
            page = session.query(ScrapedPage).get(row.id)
            if page:
                pages.append((page, row.distance))

        logger.info(f"Search returned {len(pages)} result(s)")
        return pages
    except Exception as e:
        logger.error(f"Vector search failed: {e}", exc_info=True)
        return []
    finally:
        session.close()

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
        Base.page_metadata.create_all(bind=engine)
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
            logger.info(f"Created new record for URL: {url}")
            return page
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving data: {e}")
        raise
    finally:
        session.close()