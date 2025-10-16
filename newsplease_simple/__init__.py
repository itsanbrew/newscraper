"""
Simplified news-please for Vercel deployment.
Only includes the core functionality needed for URL-based scraping.
"""
from .NewsArticle import NewsArticle
from .single_crawler import from_url, from_urls

__version__ = "1.5.0"
__all__ = ['NewsArticle', 'from_url', 'from_urls']
