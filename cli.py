# cli.py
import typer
from rich.console import Console
from rich.table import Table
from scraper.static_scraper import scrape_static
from scraper.dynamic_scraper import scrape_dynamic
from scraper.detector import detect_type
from extractor.ai_parser import parse_with_ai
from storage.mcp_handler import process_and_store, vector_search
from storage.db_handler import init_db, get_db_session, ScrapedPage
from utils.logger import get_logger
import json

logger = get_logger(__name__)
console = Console()
app = typer.Typer(help="AI Scraper Bot CLI")


@app.command()
def init():
    """Initialize the database"""
    console.print("Initializing database...", style="bold blue")
    init_db()
    console.print(" Database initialized successfully", style="bold green")


@app.command()
def scrape(url: str, dynamic: bool = typer.Option(False, "--dynamic", "-d", help="Force dynamic scraping")):
    """
    Scrape a URL, parse with AI, and store with vector embeddings
    """
    try:
        console.print(f" Scraping: {url}", style="bold blue")
        
        # Detect content type if not forcing dynamic
        if not dynamic:
            content_type = detect_type(url)
            console.print(f" Content type: {content_type}")
            
            # Choose scraper based on content type
            if "text/html" in content_type or "application/xhtml+xml" in content_type:
                data = scrape_static(url)
            else:
                console.print("Using dynamic scraper for non-HTML content", style="yellow")
                data = scrape_dynamic(url)
        else:
            console.print("Forced dynamic scraping", style="yellow")
            data = scrape_dynamic(url)
        
        console.print(" Scraping complete", style="green")
        
        # Parse with AI
        console.print(" Parsing with AI...", style="bold blue")
        metadata = parse_with_ai(data)
        console.print(" AI parsing complete", style="green")
        
        # Store with embeddings
        console.print(" Storing data with embeddings...", style="bold blue")
        page = process_and_store(
            url=url, 
            title=data.get("title", ""), 
            content=data.get("content", ""), 
            page_metadata={ # This is passed to process_and_store which uses page_metadata internally
                "ai_parsed": metadata,
                "meta_tags": data.get("meta_tags", {})
            }
        )
        console.print(f" Stored page ID: {page.id}", style="bold green")
        
        # Show summary
        console.print("\n Summary:", style="bold")
        console.print(f"Title: {data.get('title', 'N/A')}")
        if metadata.get("summary"):
            console.print(f"Summary: {metadata.get('summary')}")
        
        return page
    except Exception as e:
        console.print(f" Error: {str(e)}", style="bold red")
        logger.error(f"Error in scrape command: {e}", exc_info=True)
        raise typer.Exit(code=1)


@app.command()
def search(query: str, limit: int = typer.Option(5, "--limit", "-l", help="Number of results")):
    """
    Search scraped pages using vector similarity
    """
    try:
        console.print(f" Searching for: \"{query}\"", style="bold blue")
        
        # Perform vector search
        results = vector_search(query, limit)
        
        if not results:
            console.print("No results found", style="yellow")
            return
        
        # Display results
        table = Table(title=f"Search Results for '{query}'")
        table.add_column("ID", style="dim")
        table.add_column("Title", style="bold")
        table.add_column("URL")
        table.add_column("Similarity", justify="right")
        
        for page, distance in results:
            # Convert distance to similarity (1 - distance for cosine)
            similarity = round((1 - distance) * 100, 2)
            table.add_row(
                str(page.id),
                page.title or "No title",
                page.url,
                f"{similarity}%"
            )
        
        console.print(table)
        return results
    except Exception as e:
        console.print(f" Error: {str(e)}", style="bold red")
        logger.error(f"Error in search command: {e}", exc_info=True)
        raise typer.Exit(code=1)


@app.command()
def view(id: int):
    """View details of a specific scraped page"""
    try:
        session = get_db_session()
        page = session.query(ScrapedPage).filter_by(id=id).first()
        
        if not page:
            console.print(f" Page with ID {id} not found", style="bold red")
            return
        
        console.print(f" Page #{page.id}", style="bold blue")
        console.print(f"Title: {page.title or 'No title'}")
        console.print(f"URL: {page.url}")
        console.print(f"Created: {page.created_at}")
        console.print(f"Updated: {page.updated_at}")
        
        if page.metadata and page.metadata.get("ai_parsed"):
            console.print("\n AI Analysis:", style="bold")
            
            ai_data = page.metadata["ai_parsed"]
            if "summary" in ai_data:
                console.print(f"Summary: {ai_data['summary']}")
                
            if "main_topics" in ai_data and ai_data["main_topics"]:
                console.print("\nMain Topics:", style="bold")
                for topic in ai_data["main_topics"]:
                    console.print(f"• {topic}")
                    
            if "key_points" in ai_data and ai_data["key_points"]:
                console.print("\nKey Points:", style="bold")
                for point in ai_data["key_points"]:
                    console.print(f"• {point}")
        
        # Ask if user wants to see full content
        if typer.confirm("Show full content?"):
            console.print("\n Content:", style="bold")
            console.print(page.content[:2000] + ("..." if len(page.content) > 2000 else ""))
            
            if len(page.content) > 2000 and typer.confirm("Show more content?"):
                console.print(page.content)
    
    except Exception as e:
        console.print(f" Error: {str(e)}", style="bold red")
        logger.error(f"Error in view command: {e}")
    finally:
        session.close()


@app.command()
def list(limit: int = typer.Option(10, "--limit", "-l", help="Number of pages to show")):
    """List all scraped pages"""
    try:
        session = get_db_session()
        pages = session.query(ScrapedPage).order_by(ScrapedPage.created_at.desc()).limit(limit).all()
        
        if not pages:
            console.print("No pages found in database", style="yellow")
            return
        
        table = Table(title="Scraped Pages")
        table.add_column("ID", style="dim")
        table.add_column("Title", style="bold")
        table.add_column("URL")
        table.add_column("Created At")
        
        for page in pages:
            table.add_row(
                str(page.id),
                page.title or "No title",
                page.url,
                str(page.created_at)
            )
        
        console.print(table)
    except Exception as e:
        console.print(f" Error: {str(e)}", style="bold red")
        logger.error(f"Error listing pages: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    app()