# scraper/static_scraper.py
import requests
import asyncio
from playwright.async_api import async_playwright
from utils.logger import get_logger
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
    
async def _scrape_dynamic_async(url: str) -> dict:
    """Internal async function to scrape dynamic content using Playwright"""
    logger.info(f"Scraping dynamic content from: {url}")
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        
        try:
            # Create a new context with custom user agent
            context = await browser.new_context(user_agent=USER_AGENT)
            page = await context.new_page()
            
            # Navigate to the URL with timeout
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Wait for content to load (adjust selectors as needed)
            await page.wait_for_selector("body", timeout=5000)
            
            # Get page title
            title = await page.title()
            
            # Get page content
            content = await page.content()
            
            # Extract text content
            text_content = await page.evaluate('''() => {
                // Remove script and style elements
                const scripts = document.querySelectorAll('script, style, nav, footer, header');
                scripts.forEach(script => script.remove());
                
                // Get the text content
                return document.body.innerText;
            }''')
            
            # Extract meta tags
            meta_tags = await page.evaluate('''() => {
                const metaTags = {};
                document.querySelectorAll('meta').forEach(meta => {
                    if (meta.getAttribute('name')) {
                        metaTags[meta.getAttribute('name')] = meta.getAttribute('content') || '';
                    } else if (meta.getAttribute('property')) {
                        metaTags[meta.getAttribute('property')] = meta.getAttribute('content') || '';
                    }
                });
                return metaTags;
            }''')
            
            return {
                "title": title,
                "content": text_content,
                "meta_tags": meta_tags,
                "html": content  # Store raw HTML for potential further processing
            }
            
        finally:
            await browser.close()
    

def scrape_dynamic(url: str) -> dict:
    """
    Scrape dynamic website content using Playwright
    Returns a dictionary with title, content and metadata
    """
    try:
        # Run the async function
        return asyncio.run(_scrape_dynamic_async(url))
    except Exception as e:
        logger.error(f"Error in dynamic scraping for {url}: {e}")
        raise