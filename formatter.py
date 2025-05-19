"""
Formatter component for the Obsidian News Digest application.
Creates formatted markdown output from summarized articles.
"""
from typing import List, Dict, Any
from datetime import datetime


def format_digest(summarized_articles: List[Dict[str, Any]]) -> str:
    """
    Format summarized articles into a complete markdown digest.
    
    Args:
        summarized_articles: List of article dictionaries with summaries
        
    Returns:
        Formatted markdown string of the complete digest
    """
    # Handle case with no articles
    if not summarized_articles:
        return f"No major news today."
    
    # Combine all article summaries
    digest = "\n".join([article["summary"] for article in summarized_articles])
    
    return digest


def get_digest_filename() -> str:
    """
    Generate a filename for the digest based on the current date.
    
    Returns:
        Filename string with date
    """
    # Get today's date for the filename
    today = datetime.now().strftime("%d %b %Y")
    
    # Create file name with a clear descriptive name
    file_name = f"Global News Digest – {today}.md"
    
    return file_name