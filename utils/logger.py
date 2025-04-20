# utils/logger.py
import logging
import sys
from config import LOG_LEVEL

# Configure logger
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("app.log")
    ]
)

def get_logger(name):
    """Get a logger instance with the given name"""
    return logging.getLogger(name)