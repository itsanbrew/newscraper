"""
Tests for RocketReach API integration.
"""
import unittest
from unittest.mock import patch, MagicMock
import os
from integrations.rocketreach import RocketReachAPI, lookup_email_by_name_and_domain


class TestRocketReachAPI(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment."""
        # Mock environment variable
        with patch.dict(os.environ, {'ROCKETREACH_API_KEY': 'test-key'}):
            self.api = RocketReachAPI()
    
    def test_init_without_api_key(self):
        """Test initialization without API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                RocketReachAPI()
    
    @patch('integrations.rocketreach.requests.Session.post')
    def test_lookup_email_success(self, mock_post):
        """Test successful email lookup."""
        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [{
                'email': 'john@example.com',
                'confidence': 0.95,
                'title': 'Journalist',
                'company': 'Example News'
            }]
        }
        mock_post.return_value = mock_response
        
        result = self.api.lookup_email_by_name_and_domain('John Doe', 'example.com')
        
        self.assertIsNotNone(result)
        self.assertEqual(result['email'], 'john@example.com')
        self.assertEqual(result['confidence'], 0.95)
        self.assertEqual(result['full_name'], 'John Doe')
        self.assertEqual(result['domain'], 'example.com')
    
    @patch('integrations.rocketreach.requests.Session.post')
    def test_lookup_email_no_results(self, mock_post):
        """Test email lookup with no results."""
        # Mock empty API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'results': []}
        mock_post.return_value = mock_response
        
        result = self.api.lookup_email_by_name_and_domain('John Doe', 'example.com')
        
        self.assertIsNone(result)
    
    @patch('integrations.rocketreach.requests.Session.post')
    def test_lookup_email_rate_limit(self, mock_post):
        """Test rate limit handling."""
        # Mock rate limit response
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '1'}
        mock_post.return_value = mock_response
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = self.api.lookup_email_by_name_and_domain('John Doe', 'example.com')
        
        # Should return None due to rate limiting
        self.assertIsNone(result)
    
    def test_lookup_email_invalid_input(self):
        """Test lookup with invalid input."""
        result = self.api.lookup_email_by_name_and_domain('', 'example.com')
        self.assertIsNone(result)
        
        result = self.api.lookup_email_by_name_and_domain('John Doe', '')
        self.assertIsNone(result)


class TestRocketReachConvenienceFunction(unittest.TestCase):
    
    @patch('integrations.rocketreach.RocketReachAPI')
    def test_lookup_email_by_name_and_domain_success(self, mock_api_class):
        """Test convenience function with successful lookup."""
        # Mock API instance
        mock_api = MagicMock()
        mock_api.lookup_email_by_name_and_domain.return_value = {
            'email': 'test@example.com',
            'confidence': 0.9
        }
        mock_api_class.return_value = mock_api
        
        result = lookup_email_by_name_and_domain('John Doe', 'example.com')
        
        self.assertIsNotNone(result)
        self.assertEqual(result['email'], 'test@example.com')
        mock_api.lookup_email_by_name_and_domain.assert_called_once_with('John Doe', 'example.com')
    
    @patch('integrations.rocketreach.RocketReachAPI')
    def test_lookup_email_by_name_and_domain_error(self, mock_api_class):
        """Test convenience function with API error."""
        mock_api_class.side_effect = ValueError("API key not set")
        
        result = lookup_email_by_name_and_domain('John Doe', 'example.com')
        
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
