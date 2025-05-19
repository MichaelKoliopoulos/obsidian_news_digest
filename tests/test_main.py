"""
Unit tests for the main module
"""
import pytest
import argparse
from unittest.mock import patch, MagicMock

from main import create_news_digest, main


@pytest.fixture
def mock_config():
    """Mock configuration"""
    mock_config = MagicMock()
    mock_config.news_sources = [
        "https://example.com/news",
        "https://another-source.com"
    ]
    mock_config.max_articles = 10
    mock_config.api_key = "test_api_key"
    mock_config.model_name = "test_model"
    mock_config.vault_path = "/path/to/vault"
    mock_config.output_folder = "News Digests"
    mock_config.use_intelligent_selection = False
    return mock_config


@pytest.fixture
def mock_articles():
    """Mock news articles"""
    return [
        {
            "title": "Test Article 1",
            "text": "This is the content of test article 1.",
            "url": "https://example.com/article1",
            "source": "https://example.com/news"
        },
        {
            "title": "Test Article 2",
            "text": "This is the content of test article 2.",
            "url": "https://example.com/article2",
            "source": "https://example.com/news"
        }
    ]


@pytest.fixture
def mock_summarized_articles(mock_articles):
    """Mock summarized articles"""
    summarized = []
    for article in mock_articles:
        article_with_summary = article.copy()
        article_with_summary["summary"] = f"Summary of {article['title']}"
        summarized.append(article_with_summary)
    return summarized


def test_create_news_digest_successful(
    mock_config, mock_articles, mock_summarized_articles
):
    """Test create_news_digest with successful execution"""
    # Set up mocks for all imported functions
    with patch('main.load_config', return_value=mock_config) as mock_load_config:
        with patch('main.fetch_news', return_value=mock_articles) as mock_fetch:
            with patch(
                'main.summarize_articles',
                return_value=mock_summarized_articles
            ) as mock_summarize:
                with patch(
                    'main.format_digest',
                    return_value="Formatted digest content"
                ) as mock_format:
                    with patch(
                        'main.get_digest_filename',
                        return_value="digest-2023-05-01.md"
                    ) as mock_get_filename:
                        with patch(
                            'main.publish_to_obsidian',
                            return_value="/path/to/vault/News Digests/digest-2023-05-01.md"
                        ) as mock_publish:
                            
                            # Call the function
                            result = create_news_digest()
                            
                            # Verify all steps were called correctly
                            mock_load_config.assert_called_once()
                            mock_fetch.assert_called_once_with(
                                mock_config.news_sources,
                                max_articles_per_source=5  # 10 articles / 2 sources
                            )
                            mock_summarize.assert_called_once_with(
                                mock_articles,
                                api_key=mock_config.api_key,
                                model_name=mock_config.model_name
                            )
                            mock_format.assert_called_once_with(mock_summarized_articles)
                            mock_get_filename.assert_called_once()
                            mock_publish.assert_called_once_with(
                                content="Formatted digest content",
                                vault_path=mock_config.vault_path,
                                output_folder=mock_config.output_folder,
                                filename="digest-2023-05-01.md"
                            )
                            
                            # Verify the result is the published file path
                            assert result == "/path/to/vault/News Digests/digest-2023-05-01.md"


def test_create_news_digest_with_custom_parameters(
    mock_config, mock_articles, mock_summarized_articles
):
    """Test create_news_digest with custom parameters"""
    # Custom parameters
    custom_sources = ["https://custom-source.com"]
    custom_max_articles = 5
    
    # Set up mocks for all imported functions
    with patch('main.load_config', return_value=mock_config):
        with patch('main.fetch_news', return_value=mock_articles) as mock_fetch:
            with patch(
                'main.summarize_articles',
                return_value=mock_summarized_articles
            ):
                with patch(
                    'main.format_digest',
                    return_value="Formatted digest content"
                ):
                    with patch(
                        'main.get_digest_filename',
                        return_value="digest-2023-05-01.md"
                    ):
                        with patch(
                            'main.publish_to_obsidian',
                            return_value="/path/to/result.md"
                        ):
                            
                            # Call the function with custom parameters
                            result = create_news_digest(
                                sources=custom_sources,
                                max_articles_count=custom_max_articles
                            )
                            
                            # Verify fetch was called with custom parameters
                            mock_fetch.assert_called_once_with(
                                custom_sources,
                                max_articles_per_source=5  # 5 articles / 1 source
                            )
                            
                            # Verify the result is the published file path
                            assert result == "/path/to/result.md"


def test_create_news_digest_with_intelligent_selection(
    mock_config, mock_articles, mock_summarized_articles
):
    """Test create_news_digest with intelligent selection enabled"""
    # Enable intelligent selection
    mock_config.use_intelligent_selection = True
    article_urls = ["https://example.com/article1", "https://example.com/article2"]
    
    # Set up mocks for all imported functions
    with patch('main.load_config', return_value=mock_config):
        with patch('main.get_article_urls', return_value=article_urls) as mock_get_urls:
            with patch('main.fetch_news', return_value=mock_articles) as mock_fetch:
                with patch(
                    'main.summarize_articles',
                    return_value=mock_summarized_articles
                ):
                    with patch(
                        'main.format_digest',
                        return_value="Formatted digest content"
                    ):
                        with patch(
                            'main.get_digest_filename',
                            return_value="digest-2023-05-01.md"
                        ):
                            with patch(
                                'main.publish_to_obsidian',
                                return_value="/path/to/result.md"
                            ):
                                
                                # Call the function
                                result = create_news_digest()
                                
                                # Verify intelligence selection was used
                                mock_get_urls.assert_called_once_with(mock_config)
                                
                                # Verify fetch was called with article URLs
                                mock_fetch.assert_called_once_with(
                                    article_urls,
                                    max_articles_per_source=1
                                )
                                
                                # Verify the result is the published file path
                                assert result == "/path/to/result.md"


def test_create_news_digest_fallback_to_direct_sources(
    mock_config, mock_articles, mock_summarized_articles
):
    """Test fallback to direct sources when intelligent selection returns no results"""
    # Enable intelligent selection
    mock_config.use_intelligent_selection = True
    
    # Set up mocks for all imported functions
    with patch('main.load_config', return_value=mock_config):
        with patch('main.get_article_urls', return_value=[]) as mock_get_urls:
            with patch('main.fetch_news', return_value=mock_articles) as mock_fetch:
                with patch(
                    'main.summarize_articles',
                    return_value=mock_summarized_articles
                ):
                    with patch(
                        'main.format_digest',
                        return_value="Formatted digest content"
                    ):
                        with patch(
                            'main.get_digest_filename',
                            return_value="digest-2023-05-01.md"
                        ):
                            with patch(
                                'main.publish_to_obsidian',
                                return_value="/path/to/result.md"
                            ):
                                
                                # Call the function
                                result = create_news_digest()
                                
                                # Verify intelligence selection was used
                                mock_get_urls.assert_called_once_with(mock_config)
                                
                                # Verify fetch was called with direct sources as fallback
                                mock_fetch.assert_called_once_with(
                                    mock_config.news_sources,
                                    max_articles_per_source=5  # 10 articles / 2 sources
                                )
                                
                                # Verify the result is the published file path
                                assert result == "/path/to/result.md"


def test_create_news_digest_override_intelligent_selection(
    mock_config, mock_articles, mock_summarized_articles
):
    """Test overriding the intelligent selection setting"""
    # Disable intelligent selection in config
    mock_config.use_intelligent_selection = False
    
    # Set up mocks for all imported functions
    with patch('main.load_config', return_value=mock_config):
        with patch('main.get_article_urls') as mock_get_urls:
            with patch('main.fetch_news', return_value=mock_articles) as mock_fetch:
                with patch(
                    'main.summarize_articles',
                    return_value=mock_summarized_articles
                ):
                    with patch(
                        'main.format_digest',
                        return_value="Formatted digest content"
                    ):
                        with patch(
                            'main.get_digest_filename',
                            return_value="digest-2023-05-01.md"
                        ):
                            with patch(
                                'main.publish_to_obsidian',
                                return_value="/path/to/result.md"
                            ):
                                
                                # Call the function with intelligent selection enabled
                                result = create_news_digest(use_intelligent=True)
                                
                                # Verify config was updated
                                assert mock_config.use_intelligent_selection is True
                                
                                # Verify intelligent article selection was called
                                mock_get_urls.assert_called_once_with(mock_config)
                                
                                # Verify the result is the published file path
                                assert result == "/path/to/result.md"


def test_create_news_digest_error_handling():
    """Test error handling in create_news_digest"""
    # Set up mock to raise an exception
    with patch('main.load_config', side_effect=Exception("Test error")):
        # Call the function
        result = create_news_digest()
        
        # Verify the result is None when an error occurs
        assert result is None


@patch('main.argparse.ArgumentParser')
@patch('main.create_news_digest')
def test_main_with_cli_args(mock_create_digest, mock_arg_parser):
    """Test main function with command-line arguments"""
    # Set up mock arguments
    mock_args = MagicMock()
    mock_args.sources = ["https://testsource.com"]
    mock_args.max_articles = 5
    mock_args.intelligent = True
    mock_args.direct_only = False
    
    # Set up mock parser
    mock_parser = MagicMock()
    mock_parser.parse_args.return_value = mock_args
    mock_arg_parser.return_value = mock_parser
    
    # Set up mock return value for create_news_digest
    mock_create_digest.return_value = "/path/to/result.md"
    
    # Call the function
    return_code = main()
    
    # Verify create_news_digest was called with correct args
    mock_create_digest.assert_called_once_with(
        sources=mock_args.sources,
        max_articles_count=mock_args.max_articles,
        use_intelligent=True
    )
    
    # Verify the return code is 0 (success)
    assert return_code == 0


@patch('main.argparse.ArgumentParser')
@patch('main.create_news_digest')
def test_main_with_direct_only_flag(mock_create_digest, mock_arg_parser):
    """Test main function with direct-only flag"""
    # Set up mock arguments
    mock_args = MagicMock()
    mock_args.sources = None
    mock_args.max_articles = None
    mock_args.intelligent = False
    mock_args.direct_only = True
    
    # Set up mock parser
    mock_parser = MagicMock()
    mock_parser.parse_args.return_value = mock_args
    mock_arg_parser.return_value = mock_parser
    
    # Set up mock return value for create_news_digest
    mock_create_digest.return_value = "/path/to/result.md"
    
    # Call the function
    return_code = main()
    
    # Verify create_news_digest was called with correct args
    mock_create_digest.assert_called_once_with(
        sources=None,
        max_articles_count=None,
        use_intelligent=False
    )
    
    # Verify the return code is 0 (success)
    assert return_code == 0


def test_main_failure():
    """Test main function with failure"""
    with patch('main.create_news_digest', return_value=None) as mock_create_digest:
        with patch('main.argparse.ArgumentParser') as mock_arg_parser:
            # Set up mock parser
            mock_parser = MagicMock()
            mock_parser.parse_args.return_value = MagicMock(
                sources=None,
                max_articles=None,
                intelligent=False,
                direct_only=False
            )
            mock_arg_parser.return_value = mock_parser
            
            # Call the function
            return_code = main()
            
            # Verify create_news_digest was called
            mock_create_digest.assert_called_once()
            
            # Verify the return code is 1 (error)
            assert return_code == 1 