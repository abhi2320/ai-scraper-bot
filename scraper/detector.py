# scraper/detector.py
import requests
from urllib.parse import urlparse
from utils.logger import get_logger
from utils.content_type import guess_content_type
from config import USER_AGENT

logger = get_logger(__name__)

def detect_type(url: str) -> str:
    """
    Detect content type of URL.
    Returns the content type as a string.
    """
    try:
        logger.info(f"Detecting content type for: {url}")
        
        # First try HEAD request to get content type header
        headers = {"User-Agent": USER_AGENT}
        response = requests.head(url, headers=headers, allow_redirects=True, timeout=10)
        
        # Check if we got a valid response with content type
        if response.status_code == 200 and 'content-type' in response.headers:
            content_type = response.headers['content-type']
            logger.info(f"Detected content type: {content_type}")
            return content_type
        
        # If HEAD request fails or doesn't return content type, guess from URL
        content_type = guess_content_type(url)
        logger.info(f"Guessed content type from URL: {content_type}")
        return content_type
        
    except requests.RequestException as e:
        logger.warning(f"Error detecting content type: {e}, falling back to URL-based detection")
        return guess_content_type(url)