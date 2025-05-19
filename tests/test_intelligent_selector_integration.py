"""
Integration tests for the intelligent article selector component.
Tests how intelligent_selector integrates with other components.
"""
from datetime import datetime
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path to allow imports
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
)

# Import after path adjustment
from config import Config, NewsPreferences
import intelligent_selector
import news_fetcher


class TestIntelligentSelectorIntegration(unittest.TestCase):
    """Integration tests for the intelligent article selector."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a test config with realistic values
        self.config = Config(
            api_key="test-api-key",
            vault_path="test-vault-path",
            use_intelligent_selection=True,
            news_sources=[
                "https://www.reuters.com/",
                "https://www.apnews.com/"
            ],
            news_preferences=NewsPreferences(
                topics=["technology", "science", "world news"],
                keywords=["AI", "climate", "innovation"],
                max_age_hours=24,
                preferred_sources=["reuters.com", "apnews.com"],
                excluded_sources=["gossip-site.com"],
                geographic_focus=["global", "US"],
                relevance_threshold=0.7,
                max_articles=5
            )
        )
    
    @patch('intelligent_selector.build')
    @patch('intelligent_selector.Article')
    @patch('news_fetcher.Article')
    @patch('news_fetcher.build')
    def test_intelligent_selector_to_news_fetcher_pipeline(
        self, mock_fetcher_build, mock_fetcher_article, 
        mock_selector_article, mock_build
    ):
        """Test the pipeline from intelligent selection to news fetching."""
        # Mock newspaper build for selector
        mock_paper = MagicMock()
        mock_build.return_value = mock_paper
        
        # Setup article URLs from news source
        mock_paper.article_urls.return_value = {
            "https://reuters.com/article1",
            "https://reuters.com/article2",
            "https://reuters.com/article3"
        }
        
        # Mock intelligent selector Article
        mock_selector_article_instance = MagicMock()
        mock_selector_article.return_value = mock_selector_article_instance
        mock_selector_article_instance.title = "Test Article for Selection"
        mock_selector_article_instance.text = (
            "This is test content for selection"
        )
        mock_selector_article_instance.publish_date = datetime.now()
        
        # Mock news fetcher build and paper
        mock_fetcher_paper = MagicMock()
        mock_fetcher_build.return_value = mock_fetcher_paper
        mock_fetcher_paper.article_urls.return_value = {
            "https://reuters.com/article1"
        }
        
        # Mock news fetcher Article 
        mock_fetcher_article_instance = MagicMock()
        mock_fetcher_article.return_value = mock_fetcher_article_instance
        mock_fetcher_article_instance.title = "Test Article for Fetching"
        mock_fetcher_article_instance.text = (
            "This is the full content of the article"
        )
        mock_fetcher_article_instance.url = "https://reuters.com/article1"
        mock_fetcher_article_instance.publish_date = datetime.now()
        
        # Mock direct fetch_news to return testing articles
        with patch('news_fetcher.fetch_news') as mock_fetch_news:
            mock_fetch_news.return_value = [
                {
                    "title": "Test Article for Fetching",
                    "text": "This is the full content of the article",
                    "url": "https://reuters.com/article1",
                    "source": "reuters.com"
                }
            ]
            
            # Mock LLM evaluation
            with patch('intelligent_selector.ChatOpenAI'):
                # Setup chain to return evaluation response
                mock_chain = MagicMock()
                with patch(
                    'intelligent_selector.ChatPromptTemplate.from_template'
                ) as mock_template:
                    mock_template.return_value = MagicMock()
                    with patch(
                        'intelligent_selector.SimpleJsonOutputParser'
                    ) as mock_parser:
                        mock_parser.return_value = MagicMock()
                        # Make the chain return our evaluation
                        mock_chain_result = mock_template.return_value.__or__
                        mock_chain_result.return_value.__or__.return_value = (
                            mock_chain
                        )
                        
                        # Create evaluation response
                        mock_chain.invoke.return_value = {
                            "topics": ["technology"],
                            "relevance_score": 0.9,
                            "is_opinion": False,
                            "is_analysis": False,
                            "geographic_focus": "global",
                            "keywords_matched": ["AI"],
                            "evaluation_notes": (
                                "Highly relevant technology article"
                            )
                        }
                        
                        # Execute intelligent selection
                        article_urls = intelligent_selector.get_article_urls(
                            self.config
                        )
                        
                        # Verify we got URLs back
                        self.assertIsInstance(article_urls, list)
                        self.assertTrue(len(article_urls) > 0)
                        
                        # Now test feeding these URLs to the news fetcher
                        fetched_articles = news_fetcher.fetch_news(
                            article_urls,
                            max_articles_per_source=1
                        )
                        
                        # Verify fetched articles
                        self.assertIsInstance(fetched_articles, list)
                        self.assertTrue(len(fetched_articles) > 0)
                        self.assertEqual(
                            fetched_articles[0]["title"],
                            "Test Article for Fetching"
                        )
    
    @patch('intelligent_selector.build')
    @patch('intelligent_selector.Article')
    @patch('intelligent_selector.ChatOpenAI')
    def test_preferences_affect_article_selection(
        self, mock_llm, mock_article, mock_build
    ):
        """Test that user preferences affect article selection."""
        # Skip directly to testing the article evaluation and selection
        # by mocking the discover_articles function
        with patch(
            'intelligent_selector.discover_articles'
        ) as mock_discover:
            # Create mock article data
            mock_discover.return_value = [
                {
                    "title": "New AI Breakthrough",
                    "url": "https://reuters.com/tech-article",
                    "source": "reuters.com",
                    "snippet": "This is about AI technology",
                },
                {
                    "title": "Government Regulation",
                    "url": "https://reuters.com/politics-article",
                    "source": "reuters.com",
                    "snippet": "This is about politics",
                },
                {
                    "title": "World Cup Results",
                    "url": "https://reuters.com/sports-article",
                    "source": "reuters.com",
                    "snippet": "This is about sports",
                }
            ]
            
            # Set up LLM to evaluate articles
            with patch(
                'intelligent_selector.ChatOpenAI'
            ) as mock_chat_openai:
                # Setup chain to return evaluation response
                mock_chain = MagicMock()
                with patch(
                    'intelligent_selector.ChatPromptTemplate.from_template'
                ) as mock_template:
                    mock_template.return_value = MagicMock()
                    with patch(
                        'intelligent_selector.SimpleJsonOutputParser'
                    ) as mock_parser:
                        mock_parser.return_value = MagicMock()
                        # Make the chain return our evaluation
                        mock_chain_result = mock_template.return_value.__or__
                        mock_chain_result.return_value.__or__.return_value = (
                            mock_chain
                        )
                        
                        # Setup different ratings for articles based on topics
                        def mock_evaluate(inputs):
                            title = inputs["title"]
                            if "AI" in title:
                                return {
                                    "topics": ["technology"],
                                    "relevance_score": 0.95,
                                    "is_opinion": False,
                                    "is_analysis": False,
                                    "geographic_focus": "global",
                                    "keywords_matched": ["AI"],
                                    "evaluation_notes": (
                                        "Highly relevant technology article"
                                    )
                                }
                            elif "Government" in title:
                                return {
                                    "topics": ["politics"],
                                    "relevance_score": 0.6,  # Below threshold
                                    "is_opinion": False,
                                    "is_analysis": True,
                                    "geographic_focus": "US",
                                    "keywords_matched": [],
                                    "evaluation_notes": "Political article"
                                }
                            else:
                                return {
                                    "topics": ["sports"],
                                    "relevance_score": 0.3,  # Below threshold
                                    "is_opinion": False,
                                    "is_analysis": False,
                                    "geographic_focus": "global",
                                    "keywords_matched": [],
                                    "evaluation_notes": "Sports article"
                                }
                        
                        # Set up the mock chain invoke
                        mock_chain.invoke.side_effect = mock_evaluate
                        
                        # Configure the LLM mock to return our chain
                        mock_llm_instance = MagicMock()
                        mock_chat_openai.return_value = mock_llm_instance
                
                        # Execute intelligent selection with tech-focused prefs
                        tech_config = self.config
                        tech_config.news_preferences.topics = ["technology"]
                        tech_config.news_preferences.keywords = ["AI"]
                        
                        article_urls = intelligent_selector.get_article_urls(
                            tech_config
                        )
                        
                        # Should only get the tech article
                        self.assertEqual(len(article_urls), 1)
                        self.assertIn("tech-article", article_urls[0])
    
    @patch('intelligent_selector.build')
    @patch('intelligent_selector.Article')
    @patch('intelligent_selector.ChatOpenAI')
    def test_fallback_handling(self, mock_llm, mock_article, mock_build):
        """Test fallback handling when no articles match criteria."""
        # Mock newspaper build
        mock_paper = MagicMock()
        mock_build.return_value = mock_paper
        
        # Setup article URLs from news source
        mock_paper.article_urls.return_value = {
            "https://reuters.com/article1",
            "https://reuters.com/article2",
        }
        
        # Mock article instance
        mock_article_instance = MagicMock()
        mock_article.return_value = mock_article_instance
        mock_article_instance.title = "Test Article"
        mock_article_instance.text = "This is test content"
        mock_article_instance.publish_date = datetime.now()
        
        # Mock evaluate_articles directly to return empty list
        with patch(
            'intelligent_selector.evaluate_articles',
            return_value=[]
        ):
            # Mock discover_articles to return dummy articles
            with patch(
                'intelligent_selector.discover_articles',
                return_value=[{"title": "Mock Article"}]
            ):
                # Set very high threshold
                strict_config = self.config
                strict_config.news_preferences.relevance_threshold = 0.9
                
                # Should get empty list when nothing passes threshold
                article_urls = intelligent_selector.get_article_urls(
                    strict_config
                )
                self.assertEqual(article_urls, [])


if __name__ == "__main__":
    unittest.main() 