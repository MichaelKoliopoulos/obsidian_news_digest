"""
Unit tests for the intelligent article selector component.
Uses mocks for external dependencies (LangChain, newspaper3k).
"""
import unittest
import sys
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config, NewsPreferences, ArticleCandidate
import intelligent_selector


class TestIntelligentSelector(unittest.TestCase):
    """Test cases for the intelligent article selector."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock config
        self.config = Config(
            api_key="test-api-key",
            vault_path="test-vault-path",
            use_intelligent_selection=True,
            news_sources=["https://www.example.com", "https://www.reuters.com"],
            news_preferences=NewsPreferences(
                topics=["technology", "science"],
                keywords=["AI", "climate"],
                max_age_hours=24,
                preferred_sources=["reuters.com"],
                excluded_sources=["fakenews.com"],
                geographic_focus=["global"],
                relevance_threshold=0.7
            )
        )
    
    def test_extract_domain(self):
        """Test domain extraction from URLs."""
        # Test basic URL
        self.assertEqual(
            intelligent_selector.extract_domain("https://www.example.com/article"),
            "example.com"
        )
        
        # Test URL with subdomain
        self.assertEqual(
            intelligent_selector.extract_domain("https://news.example.com/article"),
            "news.example.com"
        )
        
        # Test URL with path
        self.assertEqual(
            intelligent_selector.extract_domain("https://example.com/path/to/article"),
            "example.com"
        )
        
        # Test URL with query parameters
        self.assertEqual(
            intelligent_selector.extract_domain("https://example.com/article?id=123"),
            "example.com"
        )
        
        # Test invalid URL
        self.assertEqual(
            intelligent_selector.extract_domain("not-a-url"),
            ""
        )
    
    @patch('intelligent_selector.build')
    @patch('intelligent_selector.Article')
    def test_discover_articles(self, mock_article, mock_build):
        """Test article discovery from news sources."""
        # Set up mocks
        mock_paper = MagicMock()
        mock_build.return_value = mock_paper
        
        # Mock article URLs
        mock_paper.article_urls.return_value = {
            "https://example.com/article1",
            "https://example.com/article2",
            "https://example.com/article3"
        }
        
        # Mock Article instances
        mock_article_instance = MagicMock()
        mock_article.return_value = mock_article_instance
        mock_article_instance.title = "Test Article"
        mock_article_instance.text = "This is a test article content"
        mock_article_instance.publish_date = datetime.now()
        
        # Call the function
        news_sources = ["https://example.com"]
        results = intelligent_selector.discover_articles(news_sources, max_articles_per_source=2)
        
        # Assertions
        self.assertEqual(len(results), 2)  # Should limit to 2 articles
        self.assertEqual(results[0]["title"], "Test Article")
        self.assertEqual(results[0]["source"], "example.com")
        
        # Verify mock calls
        mock_build.assert_called_once_with("https://example.com")
        mock_paper.article_urls.assert_called_once()
        self.assertEqual(mock_article.call_count, 2)
        mock_article_instance.download.assert_called()
        mock_article_instance.parse.assert_called()
    
    @patch('intelligent_selector.ChatOpenAI')
    def test_evaluate_articles(self, mock_chat_openai):
        """Test article evaluation."""
        # Set up mock
        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm
        
        # Create test article candidates
        article_candidates = [
            {
                "title": "Test Article 1",
                "url": "https://example.com/article1",
                "source": "example.com",
                "snippet": "This is a test article about technology",
                "published_date": datetime.now()
            },
            {
                "title": "Test Article 2",
                "url": "https://reuters.com/article2",
                "source": "reuters.com",
                "snippet": "This is a test article about science",
                "published_date": datetime.now()
            }
        ]
        
        # Mock chain behavior
        mock_chain = MagicMock()
        mock_chain.invoke.side_effect = [
            {
                "topics": ["technology"],
                "relevance_score": 0.8,
                "is_opinion": False,
                "is_analysis": True,
                "geographic_focus": "global",
                "keywords_matched": ["AI"],
                "evaluation_notes": "Relevant article about technology"
            },
            {
                "topics": ["science"],
                "relevance_score": 0.9,
                "is_opinion": False,
                "is_analysis": False,
                "geographic_focus": "global",
                "keywords_matched": ["climate"],
                "evaluation_notes": "Relevant article about science"
            }
        ]
        
        # Patch the prompt | llm | parser chain
        with patch('intelligent_selector.ChatPromptTemplate.from_template') as mock_prompt_template:
            mock_prompt_template.return_value = MagicMock()
            with patch('intelligent_selector.SimpleJsonOutputParser') as mock_parser:
                mock_parser.return_value = MagicMock()
                # Make the | operator return our mock_chain
                mock_prompt_template.return_value.__or__.return_value.__or__.return_value = mock_chain
                
                # Call the function
                candidates = intelligent_selector.evaluate_articles(article_candidates, self.config)
                
                # Assertions
                self.assertEqual(len(candidates), 2)
                self.assertEqual(candidates[0].title, "Test Article 1")
                self.assertEqual(candidates[0].relevance_score, 0.8)
                self.assertEqual(candidates[0].topics, ["technology"])
                self.assertEqual(candidates[1].title, "Test Article 2")
                self.assertEqual(candidates[1].relevance_score, 0.9)
                self.assertEqual(candidates[1].topics, ["science"])
                
                # Verify mock calls
                mock_chat_openai.assert_called_once()
    
    def test_select_articles(self):
        """Test article selection based on relevance and preferences."""
        # Create test article candidates
        candidates = [
            ArticleCandidate(
                title="Test Article 1",
                url="https://example.com/article1",
                source="example.com",
                relevance_score=0.8,
                is_opinion=False,
                is_analysis=True,
                topics=["technology"],
                keywords_matched=["AI"]
            ),
            ArticleCandidate(
                title="Test Article 2",
                url="https://reuters.com/article2",
                source="reuters.com",  # This is a preferred source
                relevance_score=0.75,
                is_opinion=False,
                is_analysis=False,
                topics=["science"],
                keywords_matched=["climate"]
            ),
            ArticleCandidate(
                title="Test Article 3",
                url="https://example.com/article3",
                source="example.com",
                relevance_score=0.65,  # Below threshold
                is_opinion=False,
                is_analysis=False,
                topics=["technology"],
                keywords_matched=[]
            ),
            ArticleCandidate(
                title="Test Article 4",
                url="https://fakenews.com/article4",  # Excluded source
                source="fakenews.com",
                relevance_score=0.9,
                is_opinion=True,
                is_analysis=False,
                topics=["technology"],
                keywords_matched=["AI"]
            )
        ]
        
        # Override max_articles in the test config to match our test
        test_config = self.config
        test_config.news_preferences.max_articles = 2
        
        # Call the function with our adjusted config
        selected = intelligent_selector.select_articles(candidates, test_config)
        
        # Assertions
        self.assertEqual(len(selected), 2)  # Should select 2 articles
        
        # reuters.com should be boosted and become first
        self.assertEqual(selected[0].source, "reuters.com")
        self.assertTrue(selected[0].relevance_score > 0.75)  # Boosted score
        
        # example.com article should be second
        self.assertEqual(selected[1].source, "example.com")
        
        # Both should be marked as selected
        self.assertTrue(selected[0].selected)
        self.assertTrue(selected[1].selected)
        
        # fakenews.com should be excluded (already filtered in evaluate_articles)
        # Article 3 should be excluded due to low relevance score
        for article in selected:
            self.assertNotEqual(article.source, "fakenews.com")
            self.assertNotEqual(article.url, "https://example.com/article3")
    
    @patch('intelligent_selector.discover_articles')
    @patch('intelligent_selector.evaluate_articles')
    @patch('intelligent_selector.select_articles')
    def test_get_article_urls(self, mock_select, mock_evaluate, mock_discover):
        """Test the full article selection pipeline."""
        # Set up mocks
        mock_discover.return_value = [
            {"title": "Test Article 1", "url": "https://example.com/article1"},
            {"title": "Test Article 2", "url": "https://reuters.com/article2"}
        ]
        
        mock_evaluated = [
            ArticleCandidate(
                title="Test Article 1",
                url="https://example.com/article1",
                relevance_score=0.8
            ),
            ArticleCandidate(
                title="Test Article 2",
                url="https://reuters.com/article2",
                relevance_score=0.9
            )
        ]
        mock_evaluate.return_value = mock_evaluated
        
        mock_selected = [
            ArticleCandidate(
                title="Test Article 2",
                url="https://reuters.com/article2",
                relevance_score=0.9,
                selected=True
            ),
            ArticleCandidate(
                title="Test Article 1",
                url="https://example.com/article1",
                relevance_score=0.8,
                selected=True
            )
        ]
        mock_select.return_value = mock_selected
        
        # Call the function
        urls = intelligent_selector.get_article_urls(self.config)
        
        # Assertions
        self.assertEqual(len(urls), 2)
        self.assertEqual(urls[0], "https://reuters.com/article2")
        self.assertEqual(urls[1], "https://example.com/article1")
        
        # Verify mock calls
        mock_discover.assert_called_once()
        mock_evaluate.assert_called_once()
        mock_select.assert_called_once()
    
    def test_get_article_urls_error_handling(self):
        """Test error handling in get_article_urls."""
        # Test when discover_articles raises an exception
        with patch('intelligent_selector.discover_articles', side_effect=Exception("Test error")):
            urls = intelligent_selector.get_article_urls(self.config)
            self.assertEqual(urls, [])  # Should return empty list on error
        
        # Test when discover_articles returns empty list
        with patch('intelligent_selector.discover_articles', return_value=[]):
            urls = intelligent_selector.get_article_urls(self.config)
            self.assertEqual(urls, [])  # Should return empty list
        
        # Test when evaluate_articles returns empty list
        with patch('intelligent_selector.discover_articles', return_value=["mock_article"]):
            with patch('intelligent_selector.evaluate_articles', return_value=[]):
                urls = intelligent_selector.get_article_urls(self.config)
                self.assertEqual(urls, [])  # Should return empty list


if __name__ == "__main__":
    unittest.main() 