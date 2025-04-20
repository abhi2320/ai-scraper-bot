# extractor/ai_parser.py
from openai import OpenAI
import json
from utils.logger import get_logger
from config import OPENAI_API_KEY, COMPLETION_MODEL
from extractor.text_cleaner import clean_text

logger = get_logger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

def parse_with_ai(data):
    """
    Parse the scraped content using AI to extract structured information
    """
    if not data:
        logger.warning("Empty data provided to AI parser")
        return {}
        
    # Extract text content from raw data
    content = data.get("content", "")
    title = data.get("title", "")
    
    # Clean the content
    clean_content = clean_text(content)
    
    # Prepare the prompt
    system_prompt = """
    You are an AI assistant specialized in parsing web content. Extract the most important information from the given text.
    Your task is to create a structured JSON output with the following fields:
    - title: The main title or subject of the content
    - summary: A concise summary (max 8 sentences)
    - main_topics: An array of the main topics/themes covered (max 5)
    - key_points: An array of key points or important information (max 10)
    - entities: An object containing identified entities like people, organizations, locations, etc.
    
    Do not include any explanations, just return the valid JSON.
    """
    
    try:
        # Prepare a concise version of the content if it's too long
        max_tokens = 8000  # Limit input tokens to avoid exceeding model limits
        if len(clean_content) > max_tokens * 4:  # Approximation
            logger.info("Content too long, truncating for AI processing")
            # Keep first and last parts and indicate truncation
            content_start = clean_content[:max_tokens * 2]
            content_end = clean_content[-max_tokens:]
            clean_content = f"{content_start}\n\n[...content truncated...]\n\n{content_end}"
            
        # Call OpenAI API
        response = client.chat.completions.create(
            model=COMPLETION_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Title: {title}\n\nContent: {clean_content}"}
            ],
            # response_format={"type": "json_object"}
        )
        
        # Extract and parse the response
        result = response.choices[0].message.content
        parsed_data = json.loads(result)
        
        logger.info(f"Successfully parsed content with AI: extracted {len(parsed_data)} fields")
        return parsed_data
        
    except Exception as e:
        logger.error(f"Error parsing with AI: {e}")
        # Return a minimal structure in case of failure
        return {
            "title": title,
            "summary": "Failed to generate summary with AI.",
            "error": str(e)
        }


def ai_extract(raw_data):
    """Legacy method for compatibility"""
    return parse_with_ai(raw_data)