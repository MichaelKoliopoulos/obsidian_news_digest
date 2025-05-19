"""
Unit tests for the formatter module.
"""
from unittest.mock import patch
from formatter import format_digest, get_digest_filename


def test_format_digest_with_articles():
    """Test formatting digest with sample articles."""
    # Setup test data
    test_articles = [
        {"summary": "## Article 1\n\nSummary for article 1.\n\n---\n"},
        {"summary": "## Article 2\n\nSummary for article 2.\n\n---\n"}
    ]
    
    # Execute the function
    result = format_digest(test_articles)
    
    # Verify the results
    assert "## Article 1" in result
    assert "## Article 2" in result
    assert "Summary for article 1" in result
    assert "Summary for article 2" in result


def test_format_digest_with_no_articles():
    """Test formatting digest with no articles."""
    # Setup test data - empty list
    test_articles = []
    
    # Execute the function
    result = format_digest(test_articles)
    
    # Verify the results
    assert result == "No major news today."


class MockDateTime:
    """Mock datetime class that returns a fixed date string for strftime."""
    
    @staticmethod
    def now():
        """Return a mock datetime with fixed strftime implementation."""
        return MockDateTime()
    
    def strftime(self, format_string):
        """Always return fixed date string regardless of format."""
        return "15 May 2023"


def test_get_digest_filename():
    """Test generating digest filename with a mocked date."""
    # The expected date string and resulting filename
    date_string = "15 May 2023"
    expected_filename = f"Global News Digest – {date_string}.md"
    
    # Patch the datetime class with our mock implementation
    with patch('formatter.datetime', MockDateTime):
        # Execute the function
        result = get_digest_filename()
        
        # Verify the results
        assert result == expected_filename 