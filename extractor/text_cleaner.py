# extractor/text_cleaner.py
import re
from bs4 import BeautifulSoup
from utils.logger import get_logger

logger = get_logger(__name__)

def clean_text(text):
    """Clean and normalize text content"""
    if not text:
        return ""
        
    # Remove excess whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove UTF-8 control characters
    text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
    
    # Normalize whitespace
    text = text.strip()
    
    return text


def extract_clean_text_from_html(html):
    """Extract clean text from HTML content"""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script, style elements that contain JavaScript/CSS
        for script_or_style in soup(['script', 'style', 'nav', 'footer', 'header']):
            script_or_style.decompose()
            
        # Get text from HTML
        text = soup.get_text(separator='\n')
        
        # Clean the text
        return clean_text(text)
    except Exception as e:
        logger.error(f"Error cleaning HTML: {e}")
        return ""