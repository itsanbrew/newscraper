"""
Simplified single crawler for Vercel deployment.
Only includes URL-based scraping functionality.
"""
import logging
from typing import List, Union, Optional
from .NewsArticle import NewsArticle

logger = logging.getLogger(__name__)

def from_url(url: str) -> Optional[NewsArticle]:
    """
    Extract article from a single URL.
    
    Args:
        url: URL to extract article from
        
    Returns:
        NewsArticle object or None if extraction failed
    """
    try:
        from newsplease import NewsPlease
        article = NewsPlease.from_url(url)
        return article
    except Exception as e:
        logger.error(f"Failed to extract article from {url}: {e}")
        return None

def from_urls(urls: List[str]) -> List[NewsArticle]:
    """
    Extract articles from multiple URLs.
    
    Args:
        urls: List of URLs to extract articles from
        
    Returns:
        List of NewsArticle objects (failed extractions are skipped)
    """
    articles = []
    for url in urls:
        article = from_url(url)
        if article:
            articles.append(article)
    return articles
