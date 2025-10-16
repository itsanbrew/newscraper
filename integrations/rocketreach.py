"""
RocketReach API integration for email lookup by name and domain.
"""
import os
import time
import logging
import requests
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class RocketReachAPI:
    """RocketReach API client for email lookup."""
    
    def __init__(self):
        self.api_key = os.getenv('ROCKETREACH_API_KEY')
        if not self.api_key:
            raise ValueError("ROCKETREACH_API_KEY environment variable not set")

        self.base_url = "https://api.rocketreach.co/api/v2"
        self.session = requests.Session()
        self.session.headers.update({
            "Api-Key": self.api_key,
            "Content-Type": "application/json"
        })
    
    def _handle_rate_limit(self, response: requests.Response) -> bool:
        """Handle rate limiting with exponential backoff."""
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            
            # If rate limit is too long (> 1 hour), don't wait
            if retry_after > 3600:  # 1 hour
                logger.warning(f"Rate limited with very long wait time ({retry_after} seconds). Skipping wait.")
                return False  # Don't retry
            
            # Cap the wait time to maximum 5 minutes to prevent hanging
            max_wait = 300  # 5 minutes
            wait_time = min(retry_after, max_wait)
            
            if retry_after > max_wait:
                logger.warning(f"Rate limited. Retry-After is {retry_after} seconds, capping to {wait_time} seconds")
            else:
                logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
            
            time.sleep(wait_time)
            return True
        return False
    
    def _make_request(self, endpoint: str, params: Dict = None, data: Dict = None) -> Optional[Dict]:
        """Make API request with rate limit handling."""
        url = f"{self.base_url}/{endpoint}"
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                if data:
                    # POST request for search endpoints
                    response = self.session.post(url, json=data, timeout=30)
                else:
                    # GET request for lookup endpoints
                    response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    return response.json()
                elif self._handle_rate_limit(response):
                    continue
                else:
                    logger.error(f"API request failed: {response.status_code} - {response.text}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return None
        
        return None
    
    def lookup_email_by_name_and_domain(self, full_name: str, domain: str) -> Optional[Dict]:
        """
        Lookup email by name and domain using RocketReach People Lookup API.
        
        Args:
            full_name: Full name of the person
            domain: Company domain (e.g., 'nytimes.com')
            
        Returns:
            Dict with email info or None if not found
        """
        if not full_name or not domain:
            logger.warning("Missing name or domain for lookup")
            return None
        
        # Clean domain (remove www, protocol, etc.)
        clean_domain = domain.replace('www.', '').replace('http://', '').replace('https://', '')
        
        # Use People Lookup API with GET request and query parameters
        params = {
            "name": full_name,
            "current_employer": clean_domain
        }
        
        logger.info(f"Looking up email for {full_name} at {clean_domain}")
        
        # Use the People Lookup API endpoint
        result = self._make_request("profile-company/lookup", params=params)
        
        if not result:
            logger.warning(f"No result for {full_name} at {clean_domain}")
            # Return a contact object indicating RocketReach was connected but no person found
            return {
                "full_name": full_name,
                "email": "not found",
                "confidence": 0.0,
                "source": "rocketreach",
                "domain": clean_domain,
                "title": "not found",
                "company": "not found"
            }
        
        # Process results based on RocketReach API response structure
        if 'person' in result and result['person']:
            person = result['person']
            
            # Get email information
            email = ''
            confidence = 0.0
            if 'emails' in person and person['emails']:
                # Get the first email (usually the best match)
                email_info = person['emails'][0]
                email = email_info.get('email', '')
                confidence = email_info.get('confidence', 0.0)
            
            return {
                "full_name": full_name,
                "email": email,
                "confidence": confidence,
                "source": "rocketreach",
                "domain": clean_domain,
                "title": person.get('current_title', ''),
                "company": person.get('current_company', '')
            }
        
        logger.warning(f"No email found for {full_name} at {clean_domain}")
        # Return a contact object indicating RocketReach was connected but no person found
        return {
            "full_name": full_name,
            "email": "not found",
            "confidence": 0.0,
            "source": "rocketreach",
            "domain": clean_domain,
            "title": "not found",
            "company": "not found"
        }


def lookup_email_by_name_and_domain(full_name: str, domain: str) -> Optional[Dict]:
    """
    Convenience function for email lookup.
    
    Args:
        full_name: Full name of the person
        domain: Company domain
        
    Returns:
        Dict with email info or None if not found
    """
    try:
        api = RocketReachAPI()
        return api.lookup_email_by_name_and_domain(full_name, domain)
    except ValueError as e:
        logger.error(f"RocketReach API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in email lookup: {e}")
        return None
