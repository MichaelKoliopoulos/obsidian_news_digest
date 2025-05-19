"""
Unit tests for the config module.
"""
import os
import pytest
from unittest.mock import patch
from config import load_config, Config


def test_config_class_defaults():
    """Test Config class default values."""
    config = Config(
        api_key="test_key",
        vault_path="test_path"
    )
    
    # Test default values
    assert config.api_key == "test_key"
    assert config.vault_path == "test_path"
    assert config.news_sources == ["https://www.apnews.com/", "https://www.c-span.org/"]
    assert config.max_articles == 10
    assert config.output_folder == "Daily_news"
    assert config.model_name == "gpt-4.1-nano-2025-04-14"


def test_load_config_with_env_variables():
    """Test loading config with environment variables."""
    # Mock environment variables
    mock_env = {
        "OPENAI_API_KEY": "mock_api_key",
        "OBSIDIAN_VAULT_PATH": "/mock/path"
    }
    
    with patch.dict(os.environ, mock_env, clear=True):
        with patch('config.load_dotenv'):  # Mock load_dotenv to do nothing
            config = load_config()
            
            # Verify config was loaded correctly
            assert config.api_key == "mock_api_key"
            assert config.vault_path == "/mock/path"


def test_load_config_missing_api_key():
    """Test load_config raises ValueError when API key is missing."""
    # Mock environment with missing API key
    mock_env = {
        "OBSIDIAN_VAULT_PATH": "/mock/path"
    }
    
    with patch.dict(os.environ, mock_env, clear=True):
        with patch('config.load_dotenv'):
            with pytest.raises(ValueError) as excinfo:
                load_config()
            
            # Verify the error message
            assert "OPENAI_API_KEY not found" in str(excinfo.value)


def test_load_config_missing_vault_path():
    """Test load_config uses default path when vault path is missing."""
    # Mock environment with missing vault path
    mock_env = {
        "OPENAI_API_KEY": "mock_api_key"
    }
    
    with patch.dict(os.environ, mock_env, clear=True):
        with patch('config.load_dotenv'):
            with patch('config.print') as mock_print:
                config = load_config()
                
                # Verify default path was used
                assert config.vault_path == "./output"
                
                # Verify warning was printed
                mock_print.assert_any_call("⚠️ OBSIDIAN_VAULT_PATH not found! Using './output' as default.") 