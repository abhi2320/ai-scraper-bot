# scraper/static_scraper.py
import requests
from bs4 import BeautifulSoup
from config import USER_AGENT, REQUEST_TIMEOUT
from utils.logger import get_logger

logger = get_logger(__name__)

def scrape_static(url: str) -> dict:
    """
    Scrape static website content using requests and BeautifulSoup
    Returns a dictionary containing title, content, and metadata
    """
    headers = {"User-Agent": USER_AGENT}
    
    try:
        logger.info(f"Scraping static content from: {url}")
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()  # Raise exception for bad status codes
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract title
        title = soup.title.string if soup.title else ""
        
        # Extract main content (this is a basic extraction - might need refinement)
        # Remove script and style elements
        for script_or_style in soup(["script", "style", "nav", "footer", "header"]):
            script_or_style.decompose()
            
        # Get text content
        content = soup.get_text(separator="\n").strip()
        
        # Extract meta tags
        meta_tags = {}
        for meta in soup.find_all("meta"):
            if meta.get("name"):
                meta_tags[meta.get("name")] = meta.get("content", "")
            elif meta.get("property"):
                meta_tags[meta.get("property")] = meta.get("content", "")
        
        # Return scraped data
        return {
            "title": title,
            "content": content,
            "meta_tags": meta_tags,
            "html": response.text  # Store raw HTML for potential further processing
        }
    
    except requests.RequestException as e:
        logger.error(f"Error scraping {url}: {e}")
        raise