"""
Tests for the main pipeline functionality.
"""
import unittest
import tempfile
import os
from unittest.mock import patch, MagicMock
from scripts.run_scraper import extract_article_data, normalize_url, extract_domain_from_url


class TestPipeline(unittest.TestCase):
    
    def test_normalize_url(self):
        """Test URL normalization."""
        from scripts.run_scraper import normalize_url
        
        # Test adding https
        self.assertEqual(normalize_url("example.com"), "https://example.com")
        self.assertEqual(normalize_url("www.example.com"), "https://www.example.com")
        
        # Test keeping existing protocol
        self.assertEqual(normalize_url("http://example.com"), "http://example.com")
        self.assertEqual(normalize_url("https://example.com"), "https://example.com")
    
    def test_extract_domain_from_url(self):
        """Test domain extraction from URL."""
        from scripts.run_scraper import extract_domain_from_url
        
        self.assertEqual(extract_domain_from_url("https://www.example.com/article"), "example.com")
        self.assertEqual(extract_domain_from_url("http://example.com/path"), "example.com")
        self.assertEqual(extract_domain_from_url("https://subdomain.example.com"), "subdomain.example.com")
        self.assertEqual(extract_domain_from_url("invalid-url"), "")
    
    @patch('scripts.run_scraper.NewsPlease')
    def test_extract_article_data_success(self, mock_newsplease):
        """Test successful article extraction."""
        # Mock article object
        mock_article = MagicMock()
        mock_article.title = "Test Article"
        mock_article.authors = ["John Doe"]
        mock_article.source_domain = "example.com"
        mock_article.date_publish = "2023-01-01"
        mock_article.language = "en"
        mock_article.description = "Test description"
        
        mock_newsplease.from_url.return_value = mock_article
        
        result = extract_article_data("https://example.com/article")
        
        self.assertIsNotNone(result)
        self.assertEqual(result['url'], "https://example.com/article")
        self.assertEqual(result['title'], "Test Article")
        self.assertEqual(result['author'], "John Doe")
        self.assertEqual(result['source_domain'], "example.com")
    
    @patch('scripts.run_scraper.NewsPlease')
    def test_extract_article_data_failure(self, mock_newsplease):
        """Test article extraction failure."""
        mock_newsplease.from_url.return_value = None
        
        result = extract_article_data("https://example.com/article")
        
        self.assertIsNone(result)
    
    @patch('scripts.run_scraper.NewsPlease')
    def test_extract_article_data_exception(self, mock_newsplease):
        """Test article extraction with exception."""
        mock_newsplease.from_url.side_effect = Exception("Network error")
        
        result = extract_article_data("https://example.com/article")
        
        self.assertIsNone(result)


class TestCSVExport(unittest.TestCase):
    
    def setUp(self):
        """Set up test data."""
        self.test_articles = [
            {
                'url': 'https://example.com/article1',
                'title': 'Test Article 1',
                'author': 'John Doe',
                'source_domain': 'example.com',
                'date_publish': '2023-01-01',
                'language': 'en'
            },
            {
                'url': 'https://example.com/article2',
                'title': 'Test Article 2',
                'author': 'Jane Smith',
                'source_domain': 'example.com',
                'date_publish': '2023-01-02',
                'language': 'en'
            }
        ]
        
        self.test_contacts = [
            {
                'full_name': 'John Doe',
                'email': 'john@example.com',
                'domain': 'example.com',
                'confidence': 0.95,
                'source': 'rocketreach',
                'syntax_valid': True,
                'mx_valid': True,
                'valid': True
            }
        ]
    
    def test_write_articles_csv(self):
        """Test writing articles CSV."""
        from utils.exporters import write_articles_csv
        
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = os.path.join(temp_dir, 'test_articles.csv')
            result = write_articles_csv(self.test_articles, csv_path)
            
            self.assertTrue(result)
            self.assertTrue(os.path.exists(csv_path))
    
    def test_write_contacts_csv(self):
        """Test writing contacts CSV."""
        from utils.exporters import write_contacts_csv
        
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = os.path.join(temp_dir, 'test_contacts.csv')
            result = write_contacts_csv(self.test_contacts, csv_path)
            
            self.assertTrue(result)
            self.assertTrue(os.path.exists(csv_path))
    
    def test_write_joined_csv(self):
        """Test writing joined CSV."""
        from utils.exporters import write_joined_csv
        
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = os.path.join(temp_dir, 'test_joined.csv')
            result = write_joined_csv(self.test_articles, self.test_contacts, csv_path)
            
            self.assertTrue(result)
            self.assertTrue(os.path.exists(csv_path))


if __name__ == '__main__':
    unittest.main()
