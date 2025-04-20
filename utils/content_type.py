# utils/content_type.py
import mimetypes
from urllib.parse import urlparse

def guess_content_type(url):
    """
    Guess content type from URL path
    """
    path = urlparse(url).path
    content_type, _ = mimetypes.guess_type(path)
    return content_type or "text/html"  # Default to html if unknown