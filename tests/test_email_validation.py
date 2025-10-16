"""
Tests for email validation utilities.
"""
import unittest
from utils.email_validation import validate_email_full, validate_email_syntax, validate_mx_record


class TestEmailValidation(unittest.TestCase):
    
    def test_validate_email_syntax(self):
        """Test email syntax validation."""
        # Valid emails
        self.assertTrue(validate_email_syntax("test@example.com"))
        self.assertTrue(validate_email_syntax("user.name@domain.co.uk"))
        self.assertTrue(validate_email_syntax("test+tag@example.org"))
        
        # Invalid emails
        self.assertFalse(validate_email_syntax("invalid-email"))
        self.assertFalse(validate_email_syntax("@example.com"))
        self.assertFalse(validate_email_syntax("test@"))
        self.assertFalse(validate_email_syntax(""))
    
    def test_validate_email_full(self):
        """Test comprehensive email validation."""
        # Test valid email
        result = validate_email_full("test@example.com")
        self.assertTrue(result['syntax_valid'])
        self.assertTrue(result['valid'])
        
        # Test invalid syntax
        result = validate_email_full("invalid-email")
        self.assertFalse(result['syntax_valid'])
        self.assertFalse(result['valid'])
        self.assertIn('error', result)
        
        # Test empty email
        result = validate_email_full("")
        self.assertFalse(result['syntax_valid'])
        self.assertFalse(result['valid'])
    
    def test_validate_mx_record(self):
        """Test MX record validation."""
        # Test known domains (these might change, so we're lenient)
        # We just test that the function doesn't crash
        result = validate_mx_record("example.com")
        self.assertIsInstance(result, bool)
        
        # Test invalid domain
        result = validate_mx_record("this-domain-should-not-exist-12345.com")
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
