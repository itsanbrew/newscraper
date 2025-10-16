"""
CSV export utilities for articles and contacts data.
"""
import os
import logging
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def write_articles_csv(records: List[Dict], path: str = "articles.csv") -> bool:
    """
    Write articles data to CSV.
    
    Args:
        records: List of article dictionaries
        path: Output file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not records:
            logger.warning("No article records to write")
            return False
        
        # Create DataFrame
        df = pd.DataFrame(records)
        
        # Ensure required columns exist
        required_columns = ['url', 'title', 'author', 'source_domain']
        for col in required_columns:
            if col not in df.columns:
                df[col] = ''
        
        # Select and order columns (include contact data if present)
        base_columns = ['url', 'title', 'author', 'source_domain', 'date_publish', 'language']
        contact_columns = ['full_name', 'email', 'confidence', 'contact_title', 
                          'email_syntax_valid', 'email_mx_valid', 'rocketreach_connected']
        
        # Start with base columns
        columns = base_columns.copy()
        
        # Add contact columns if they exist in the data
        for col in contact_columns:
            if col in df.columns:
                columns.append(col)
        
        # Use only available columns
        available_columns = [col for col in columns if col in df.columns]
        df = df[available_columns]
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Write CSV
        df.to_csv(path, index=False, encoding='utf-8')
        logger.info(f"Wrote {len(records)} articles to {path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to write articles CSV: {e}")
        return False


def append_articles_csv(records: List[Dict], path: str = "articles.csv") -> bool:
    """
    Append articles data to existing CSV file, or create new file if it doesn't exist.
    
    Args:
        records: List of article dictionaries
        path: Output file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not records:
            logger.warning("No article records to append")
            return False
        
        # Create DataFrame from new records
        new_df = pd.DataFrame(records)
        
        # Ensure required columns exist
        required_columns = ['url', 'title', 'author', 'source_domain']
        for col in required_columns:
            if col not in new_df.columns:
                new_df[col] = ''
        
        # Define column order (include contact data if present)
        base_columns = ['url', 'title', 'author', 'source_domain', 'date_publish', 'language']
        contact_columns = ['full_name', 'email', 'confidence', 'contact_title', 
                          'email_syntax_valid', 'email_mx_valid', 'rocketreach_connected']
        
        # Start with base columns
        columns = base_columns.copy()
        
        # Add contact columns if they exist in the data
        for col in contact_columns:
            if col in new_df.columns:
                columns.append(col)
        
        # Use only available columns
        available_columns = [col for col in columns if col in new_df.columns]
        new_df = new_df[available_columns]
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Check if file exists
        if os.path.exists(path):
            # Read existing data
            try:
                existing_df = pd.read_csv(path)
                
                # Ensure both DataFrames have the same columns
                all_columns = list(set(existing_df.columns.tolist() + new_df.columns.tolist()))
                
                # Add missing columns to both DataFrames
                for col in all_columns:
                    if col not in existing_df.columns:
                        existing_df[col] = ''
                    if col not in new_df.columns:
                        new_df[col] = ''
                
                # Reorder columns to match
                existing_df = existing_df[all_columns]
                new_df = new_df[all_columns]
                
                # Combine DataFrames
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                
                # Remove duplicates based on URL (keep first occurrence)
                combined_df = combined_df.drop_duplicates(subset=['url'], keep='first')
                
                logger.info(f"Appending {len(records)} new articles to existing {len(existing_df)} articles")
                
            except Exception as e:
                logger.warning(f"Could not read existing CSV file: {e}. Creating new file.")
                combined_df = new_df
        else:
            # File doesn't exist, create new one
            combined_df = new_df
            logger.info(f"Creating new CSV file with {len(records)} articles")
        
        # Write combined CSV
        combined_df.to_csv(path, index=False, encoding='utf-8')
        logger.info(f"Total articles in CSV: {len(combined_df)}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to append articles CSV: {e}")
        return False


def write_contacts_csv(records: List[Dict], path: str = "contacts.csv") -> bool:
    """
    Write contacts data to CSV.
    
    Args:
        records: List of contact dictionaries
        path: Output file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not records:
            logger.warning("No contact records to write")
            return False
        
        # Create DataFrame
        df = pd.DataFrame(records)
        
        # Ensure required columns exist
        required_columns = ['full_name', 'email', 'domain', 'confidence', 'source']
        for col in required_columns:
            if col not in df.columns:
                df[col] = ''
        
        # Select and order columns
        columns = ['full_name', 'email', 'domain', 'confidence', 'source', 'title', 'company', 'syntax_valid', 'mx_valid', 'smtp_valid', 'valid']
        available_columns = [col for col in columns if col in df.columns]
        df = df[available_columns]
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Write CSV
        df.to_csv(path, index=False, encoding='utf-8')
        logger.info(f"Wrote {len(records)} contacts to {path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to write contacts CSV: {e}")
        return False


def write_joined_csv(articles: List[Dict], contacts: List[Dict], path: str = "articles_with_contacts.csv") -> bool:
    """
    Write joined articles and contacts data to CSV.
    
    Args:
        articles: List of article dictionaries
        contacts: List of contact dictionaries
        path: Output file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not articles:
            logger.warning("No article records to join")
            return False
        
        # Create DataFrames
        articles_df = pd.DataFrame(articles)
        contacts_df = pd.DataFrame(contacts) if contacts else pd.DataFrame()
        
        # Prepare for joining
        if not contacts_df.empty:
            # Create join key from author and domain
            articles_df['join_key'] = articles_df['author'].astype(str) + '|' + articles_df['source_domain'].astype(str)
            contacts_df['join_key'] = contacts_df['full_name'].astype(str) + '|' + contacts_df['domain'].astype(str)
            
            # Left join
            joined_df = articles_df.merge(contacts_df, on='join_key', how='left', suffixes=('', '_contact'))
            
            # Clean up join key
            joined_df = joined_df.drop('join_key', axis=1)
        else:
            joined_df = articles_df
            logger.warning("No contacts to join with articles")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Write CSV
        joined_df.to_csv(path, index=False, encoding='utf-8')
        logger.info(f"Wrote {len(joined_df)} joined records to {path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to write joined CSV: {e}")
        return False


def write_summary_report(articles: List[Dict], contacts: List[Dict], output_dir: str = "./out") -> bool:
    """
    Write a summary report of the scraping session.
    
    Args:
        articles: List of article dictionaries
        contacts: List of contact dictionaries
        output_dir: Output directory
        
    Returns:
        True if successful, False otherwise
    """
    try:
        report_path = os.path.join(output_dir, "scraping_report.txt")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("News Scraping Report\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write(f"Articles processed: {len(articles)}\n")
            f.write(f"Contacts found: {len(contacts)}\n\n")
            
            # Article sources
            if articles:
                sources = {}
                for article in articles:
                    domain = article.get('source_domain', 'Unknown')
                    sources[domain] = sources.get(domain, 0) + 1
                
                f.write("Articles by source:\n")
                for domain, count in sorted(sources.items(), key=lambda x: x[1], reverse=True):
                    f.write(f"  {domain}: {count}\n")
                f.write("\n")
            
            # Contact confidence distribution
            if contacts:
                confidences = [c.get('confidence', 0) for c in contacts if c.get('confidence')]
                if confidences:
                    avg_confidence = sum(confidences) / len(confidences)
                    f.write(f"Average contact confidence: {avg_confidence:.2f}\n")
                    f.write(f"High confidence contacts (>0.8): {sum(1 for c in confidences if c > 0.8)}\n")
                    f.write(f"Medium confidence contacts (0.5-0.8): {sum(1 for c in confidences if 0.5 <= c <= 0.8)}\n")
                    f.write(f"Low confidence contacts (<0.5): {sum(1 for c in confidences if c < 0.5)}\n")
        
        logger.info(f"Wrote summary report to {report_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to write summary report: {e}")
        return False
