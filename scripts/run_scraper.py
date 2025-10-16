#!/usr/bin/env python3
"""
News scraper with email enrichment pipeline.
"""
import os
import sys
import argparse
import logging
import time
from typing import List, Dict, Optional
from urllib.parse import urlparse
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from newsplease import NewsPlease
from integrations.rocketreach import lookup_email_by_name_and_domain
from utils.email_validation import validate_email_full
from utils.exporters import write_articles_csv, write_contacts_csv, write_joined_csv, write_summary_report


def setup_logging(output_dir: str) -> None:
    """Setup logging configuration."""
    os.makedirs(output_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(output_dir, 'run.log')),
            logging.StreamHandler()
        ]
    )


def load_urls_from_file(file_path: str) -> List[str]:
    """Load URLs from text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        return urls
    except Exception as e:
        logging.error(f"Failed to load URLs from {file_path}: {e}")
        return []


def normalize_url(url: str) -> str:
    """Normalize URL for processing."""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url


def extract_domain_from_url(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        return domain
    except Exception:
        return ''


def extract_article_data(url: str) -> Optional[Dict]:
    """
    Extract article data using NewsPlease.
    
    Args:
        url: Article URL
        
    Returns:
        Article data dict or None if extraction failed
    """
    try:
        logging.info(f"Extracting article from: {url}")
        article = NewsPlease.from_url(url)
        
        if not article:
            logging.warning(f"Failed to extract article from {url}")
            return None
        
        # Extract basic article data
        article_data = {
            'url': url,
            'title': getattr(article, 'title', '') or '',
            'author': getattr(article, 'authors', []) or [],
            'source_domain': getattr(article, 'source_domain', '') or '',
            'date_publish': getattr(article, 'date_publish', '') or '',
            'language': getattr(article, 'language', '') or '',
            'description': getattr(article, 'description', '') or ''
        }
        
        # Convert author list to string
        if isinstance(article_data['author'], list):
            article_data['author'] = ', '.join(article_data['author'])
        
        return article_data
        
    except Exception as e:
        logging.error(f"Error extracting article from {url}: {e}")
        return None


def enrich_with_emails(articles: List[Dict], smtp_check: bool = False) -> List[Dict]:
    """
    Enrich articles with email data using RocketReach.
    
    Args:
        articles: List of article dictionaries
        smtp_check: Whether to perform SMTP validation
        
    Returns:
        List of contact dictionaries
    """
    contacts = []
    processed_authors = set()
    
    logging.info("Starting email enrichment...")
    
    for article in tqdm(articles, desc="Enriching with emails"):
        author = article.get('author', '').strip()
        domain = article.get('source_domain', '').strip()
        
        if not author or not domain:
            continue
            
        # Skip if we've already processed this author
        author_key = f"{author}_{domain}"
        if author_key in processed_authors:
            continue
            
        processed_authors.add(author_key)
        
        # Look up email using RocketReach
        contact_info = lookup_email_by_name_and_domain(author, domain)
        
        if contact_info:
            # Validate email if found
            email = contact_info.get('email', '')
            if email and email != 'not found':
                validation_result = validate_email_full(email, smtp_check)
                contact_info.update({
                    'syntax_valid': validation_result.get('syntax_valid', False),
                    'mx_valid': validation_result.get('mx_valid', False)
                })
            
            contacts.append(contact_info)
            logging.info(f"Found contact for {author} at {domain}")
        else:
            logging.debug(f"No contact found for {author} at {domain}")
    
    return contacts


def main():
    """Main pipeline function."""
    parser = argparse.ArgumentParser(description='News scraper with email enrichment')
    parser.add_argument('--urls', type=str, help='Comma-separated list of URLs')
    parser.add_argument('--urls-file', type=str, help='File containing URLs (one per line)')
    parser.add_argument('--no-enrich', action='store_true', help='Disable email enrichment (enabled by default)')
    parser.add_argument('--smtp-check', action='store_true', help='Enable SMTP email validation')
    parser.add_argument('--output-dir', type=str, default='./output', help='Output directory')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.output_dir)
    
    # Load URLs
    urls = []
    if args.urls:
        urls = [normalize_url(url.strip()) for url in args.urls.split(',')]
    elif args.urls_file:
        urls = load_urls_from_file(args.urls_file)
    else:
        logging.error("Must provide either --urls or --urls-file")
        return 1
    
    if not urls:
        logging.error("No valid URLs provided")
        return 1
    
    logging.info(f"Processing {len(urls)} URLs")
    
    # Extract articles
    articles = []
    for url in tqdm(urls, desc="Extracting articles"):
        article_data = extract_article_data(url)
        if article_data:
            articles.append(article_data)
    
    logging.info(f"Successfully extracted {len(articles)} articles")
    
    # Email enrichment (enabled by default unless --no-enrich is specified)
    contacts = []
    if not args.no_enrich:
        contacts = enrich_with_emails(articles, args.smtp_check)
        logging.info(f"Found {len(contacts)} contacts")
    else:
        logging.info("Email enrichment disabled")
    
    # Write single complete CSV with contact data columns (always included)
    enriched_articles = []
    for article in articles:
        # Find matching contact for this article
        article_author = article.get('author', '').strip()
        article_domain = article.get('source_domain', '').strip()
        
        matching_contact = None
        if contacts:
            for contact in contacts:
                if (contact.get('full_name', '').strip() == article_author and 
                    contact.get('domain', '').strip() == article_domain):
                    matching_contact = contact
                    break
        
        # Merge article data with contact data (always include contact columns)
        enriched_article = article.copy()
        
        # Check if RocketReach was used (if we have any contacts, it was connected)
        rocketreach_connected = len(contacts) > 0
        
        if matching_contact:
            # Convert confidence to percentage
            confidence_raw = matching_contact.get('confidence', 0)
            confidence_percent = f"{int(confidence_raw * 100)}%" if confidence_raw > 0 else "0%"
            
            enriched_article.update({
                'full_name': matching_contact.get('full_name', 'not found'),
                'email': matching_contact.get('email', 'not found'),
                'confidence': confidence_percent,
                'contact_title': matching_contact.get('title', 'not found'),
                'email_syntax_valid': matching_contact.get('syntax_valid', False),
                'email_mx_valid': matching_contact.get('mx_valid', False),
                'rocketreach_connected': rocketreach_connected
            })
        else:
            # No contact found, add "not found" fields
            enriched_article.update({
                'full_name': 'not found',
                'email': 'not found',
                'confidence': '0%',
                'contact_title': 'not found',
                'email_syntax_valid': False,
                'email_mx_valid': False,
                'rocketreach_connected': rocketreach_connected
            })
        
        enriched_articles.append(enriched_article)
    
    # Write single enriched CSV (always with contact columns)
    enriched_path = os.path.join(args.output_dir, 'enriched_articles.csv')
    write_articles_csv(enriched_articles, enriched_path)
    
    # Write summary report
    write_summary_report(articles, contacts, args.output_dir)
    
    logging.info(f"Pipeline completed. Output saved to {args.output_dir}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
