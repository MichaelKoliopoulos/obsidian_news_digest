"""
Unit tests for the news_fetcher module
"""
import pytest
from unittest.mock import patch, Mock
from datetime import datetime

from news_fetcher import fetch_news


@pytest.fixture
def mock_article():
    """Create a mock Article object with test data"""
    article = Mock()
    article.title = "Test Article Title"
    article.url = "https://example.com/test-article"
    article.text = ("This is a test article with enough content to pass "
                   "the minimum length check. " * 10)
    article.publish_date = datetime.now()
    
    # Set up the download and parse methods
    article.download = Mock()
    article.parse = Mock()
    
    return article


@patch('news_fetcher.build')
@patch('news_fetcher.Article')
def test_fetch_news_successful(mock_article_class, mock_build, mock_article):
    """Test fetching news articles when everything works correctly"""
    # Set up the mock Article class to return our mock article
    mock_article_class.return_value = mock_article
    
    # Set up the mock build function
    mock_paper = Mock()
    mock_paper.article_urls.return_value = {
        "https://example.com/article1",
        "https://example.com/article2",
        "https://example.com/article3",
    }
    mock_build.return_value = mock_paper
    
    # Call the function with test data
    source_urls = ["https://example.com"]
    result = fetch_news(source_urls, max_articles_per_source=2)
    
    # Verify the results
    assert len(result) == 2
    assert result[0]["title"] == "Test Article Title"
    assert result[0]["url"] == "https://example.com/test-article"
    assert result[0]["source"] == "https://example.com"
    assert len(result[0]["text"]) <= 2000
    
    # Verify the mocks were called correctly
    mock_build.assert_called_once_with("https://example.com")
    assert mock_article_class.call_count == 2
    assert mock_article.download.call_count == 2
    assert mock_article.parse.call_count == 2


@patch('news_fetcher.build')
@patch('news_fetcher.Article')
def test_fetch_news_empty_article(mock_article_class, mock_build, mock_article):
    """Test handling of articles with insufficient content"""
    # Create a mock article with insufficient content
    empty_article = Mock()
    empty_article.title = "Empty Article"
    empty_article.url = "https://example.com/empty-article"
    empty_article.text = ""  # Empty content
    empty_article.download = Mock()
    empty_article.parse = Mock()
    
    # Create a short article
    short_article = Mock()
    short_article.title = "Short Article"
    short_article.url = "https://example.com/short-article"
    short_article.text = "Too short"  # Less than 100 chars
    short_article.download = Mock()
    short_article.parse = Mock()
    
    # Set up a good article
    good_article = mock_article
    
    # Set up the mock Article class to return our different articles in sequence
    mock_article_class.side_effect = [
        empty_article, 
        short_article, 
        good_article
    ]
    
    # Set up the mock build function
    mock_paper = Mock()
    mock_paper.article_urls.return_value = {
        "https://example.com/empty-article",
        "https://example.com/short-article",
        "https://example.com/good-article",
    }
    mock_build.return_value = mock_paper
    
    # Call the function with test data
    source_urls = ["https://example.com"]
    result = fetch_news(source_urls, max_articles_per_source=3)
    
    # Verify only the good article was included
    assert len(result) == 1
    assert result[0]["title"] == "Test Article Title"


@patch('news_fetcher.build')
def test_fetch_news_source_error(mock_build):
    """Test handling of errors when processing a news source"""
    # Make build raise an exception
    mock_build.side_effect = Exception("Test error")
    
    # Call the function with test data
    source_urls = ["https://example.com"]
    result = fetch_news(source_urls)
    
    # Verify we get an empty list when all sources fail
    assert result == []
    mock_build.assert_called_once()


@patch('news_fetcher.build')
@patch('news_fetcher.Article')
def test_fetch_news_article_error(mock_article_class, mock_build, mock_article):
    """Test handling of errors when processing individual articles"""
    # Make Article raise an exception for the first article
    mock_article_class.side_effect = [Exception("Test error"), mock_article]
    
    # Set up the mock build function
    mock_paper = Mock()
    mock_paper.article_urls.return_value = {
        "https://example.com/error-article",
        "https://example.com/good-article",
    }
    mock_build.return_value = mock_paper
    
    # Call the function with test data
    source_urls = ["https://example.com"]
    result = fetch_news(source_urls)
    
    # Verify only the good article was included
    assert len(result) == 1
    assert result[0]["title"] == "Test Article Title"


def test_fetch_news_multiple_sources():
    """Test fetching from multiple sources with complete mocking"""
    with patch('news_fetcher.build') as mock_build:
        # Set up the first source
        source1_paper = Mock()
        source1_paper.article_urls.return_value = {"https://source1.com/article1"}
        
        # Set up the second source
        source2_paper = Mock()
        source2_paper.article_urls.return_value = {"https://source2.com/article1"}
        
        # Configure build to return different papers based on URL
        mock_build.side_effect = [source1_paper, source2_paper]
        
        with patch('news_fetcher.Article') as mock_article_class:
            # Create mock articles for each source
            source1_article = Mock()
            source1_article.title = "Source 1 Article"
            source1_article.url = "https://source1.com/article1"
            source1_article.text = "This is content from source 1. " * 10
            source1_article.publish_date = datetime.now()
            
            source2_article = Mock()
            source2_article.title = "Source 2 Article"
            source2_article.url = "https://source2.com/article1"
            source2_article.text = "This is content from source 2. " * 10
            source2_article.publish_date = datetime.now()
            
            # Configure mock articles
            for article in [source1_article, source2_article]:
                article.download = Mock()
                article.parse = Mock()
            
            # Set up the Article constructor to return our mock articles
            mock_article_class.side_effect = [
                source1_article, 
                source2_article
            ]
            
            # Call the function with multiple sources
            source_urls = ["https://source1.com", "https://source2.com"]
            result = fetch_news(source_urls, max_articles_per_source=1)
            
            # Verify the results
            assert len(result) == 2
            assert result[0]["title"] == "Source 1 Article"
            assert result[0]["source"] == "https://source1.com"
            assert result[1]["title"] == "Source 2 Article"
            assert result[1]["source"] == "https://source2.com" 