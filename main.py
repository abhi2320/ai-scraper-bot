# main.py
import typer
from scraper.detector import detect_type
from scraper.static_scraper import scrape_static
from scraper.dynamic_scraper import scrape_dynamic
from extractor.ai_parser import parse_with_ai
from storage.mcp_handler import process_and_store
from storage.db_handler import init_db
from utils.logger import get_logger

logger = get_logger(__name__)
app = typer.Typer(help="AI Scraper Bot")

@app.command()
def scrape(url: str):
    """Scrape a URL, parse with AI, and store with embeddings"""
    try:
        logger.info(f"Starting scrape process for URL: {url}")
        
        # Initialize database
        init_db()
        
        # Detect content type
        content_type = detect_type(url)
        logger.info(f"Detected content type: {content_type}")
        
        # Scrape content based on content type
        if "text/html" in content_type or "application/xhtml+xml" in content_type:
            # Try static scraping first
            try:
                logger.info("Attempting static scraping")
                data = scrape_static(url)
            except Exception as e:
                logger.warning(f"Static scraping failed: {e}. Falling back to dynamic scraping.")
                data = scrape_dynamic(url)
        else:
            # Use dynamic scraping for non-HTML content
            logger.info("Using dynamic scraping for non-HTML content")
            data = scrape_dynamic(url)
        
        # Extract with AI
        logger.info("Parsing content with AI")
        parsed_data = parse_with_ai(data)
        
        # Store data with embeddings
        logger.info("Storing parsed data with embeddings")
        page = process_and_store(
            url=url,
            title=data.get("title", ""),
            content=data.get("content", ""),
            page_metadata={
                "ai_parsed": parsed_data,
                "meta_tags": data.get("meta_tags", {})
            }
        )
        
        logger.info(f"Successfully processed and stored URL: {url}")
        return page
    except Exception as e:
        logger.error(f"Error processing URL {url}: {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()