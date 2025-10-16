"""
Email validation utilities with syntax, MX, and optional SMTP checks.
"""
import logging
import smtplib
import socket
from typing import Dict, Optional
from email_validator import validate_email, EmailNotValidError
import dns.resolver
import dns.exception

logger = logging.getLogger(__name__)


def validate_email_syntax(email: str) -> bool:
    """Validate email syntax using email-validator."""
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False


def validate_mx_record(domain: str) -> bool:
    """Validate MX record exists for domain."""
    try:
        mx_records = dns.resolver.resolve(domain, 'MX')
        return len(mx_records) > 0
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.DNSException):
        return False


def validate_smtp(email: str, timeout: int = 10) -> Optional[bool]:
    """
    Validate email via SMTP (optional, can be slow).
    
    Args:
        email: Email address to validate
        timeout: SMTP timeout in seconds
        
    Returns:
        True if valid, False if invalid, None if check failed
    """
    try:
        domain = email.split('@')[1]
        
        # Get MX record
        mx_records = dns.resolver.resolve(domain, 'MX')
        mx_hosts = [str(record.exchange) for record in mx_records]
        
        if not mx_hosts:
            return False
        
        # Try to connect to the first MX host
        mx_host = mx_hosts[0]
        
        # Connect to SMTP server
        server = smtplib.SMTP(timeout=timeout)
        server.set_debuglevel(0)
        
        try:
            server.connect(mx_host, 25)
            server.helo('localhost')
            server.mail('test@example.com')
            
            # Try to verify the email
            code, message = server.rcpt(email)
            server.quit()
            
            return code == 250
            
        except (smtplib.SMTPException, socket.error, socket.timeout) as e:
            logger.debug(f"SMTP validation failed for {email}: {e}")
            return None
            
    except Exception as e:
        logger.debug(f"SMTP validation error for {email}: {e}")
        return None


def validate_email_full(email: str, smtp: bool = False) -> Dict:
    """
    Comprehensive email validation.
    
    Args:
        email: Email address to validate
        smtp: Whether to perform SMTP validation (slow, optional)
        
    Returns:
        Dict with validation results
    """
    if not email or not isinstance(email, str):
        return {
            "syntax_valid": False,
            "mx_valid": False,
            "smtp_valid": None,
            "valid": False,
            "error": "Invalid email format"
        }
    
    # Clean email
    email = email.strip().lower()
    
    # Syntax validation
    syntax_valid = validate_email_syntax(email)
    
    # MX validation
    mx_valid = False
    if syntax_valid:
        domain = email.split('@')[1]
        mx_valid = validate_mx_record(domain)
    
    # SMTP validation (optional)
    smtp_valid = None
    if smtp and syntax_valid and mx_valid:
        smtp_valid = validate_smtp(email)
    
    # Overall validity
    valid = syntax_valid and mx_valid and (smtp_valid is not False if smtp else True)
    
    result = {
        "syntax_valid": syntax_valid,
        "mx_valid": mx_valid,
        "smtp_valid": smtp_valid,
        "valid": valid
    }
    
    if not valid:
        if not syntax_valid:
            result["error"] = "Invalid email syntax"
        elif not mx_valid:
            result["error"] = "No MX record found"
        elif smtp and smtp_valid is False:
            result["error"] = "SMTP validation failed"
    
    return result


def validate_emails_batch(emails: list, smtp: bool = False) -> Dict[str, Dict]:
    """
    Validate multiple emails in batch.
    
    Args:
        emails: List of email addresses
        smtp: Whether to perform SMTP validation
        
    Returns:
        Dict mapping email to validation results
    """
    results = {}
    
    for email in emails:
        if email:  # Skip empty emails
            results[email] = validate_email_full(email, smtp)
    
    return results
