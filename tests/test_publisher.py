"""
Unit tests for the publisher module
"""
import os
import pytest
from unittest.mock import patch, mock_open

from publisher import publish_to_obsidian


@pytest.fixture
def sample_content():
    """Sample markdown content for testing"""
    return """
# Daily News Digest - 2023-05-01

## Breaking News Headline

This is a summary of the article.
It contains important information about the event.
More details are included here.
The fourth sentence adds context.
The fifth sentence concludes the summary.

*Source: news.example.com*

[Read more ↗](https://news.example.com/article)

---
"""


def test_publish_to_obsidian_creates_directory(sample_content):
    """Test that the function creates the output directory if it doesn't exist"""
    with patch('os.makedirs') as mock_makedirs:
        with patch('builtins.open', mock_open()) as mock_file:
            # Call the function
            publish_to_obsidian(
                content=sample_content,
                vault_path="/path/to/vault",
                output_folder="News Digests",
                filename="digest-2023-05-01.md"
            )
            
            # Verify directory was created with exist_ok=True
            # Use os.path.join to handle platform-specific path separators
            expected_path = os.path.join("/path/to/vault", "News Digests")
            mock_makedirs.assert_called_once_with(
                expected_path, 
                exist_ok=True
            )
            
            # Verify file was opened with the correct path
            expected_file_path = os.path.join(
                expected_path, 
                "digest-2023-05-01.md"
            )
            mock_file.assert_called_once_with(
                expected_file_path, 
                "w", 
                encoding="utf-8"
            )
            
            # Verify content was written
            mock_file().write.assert_called_once_with(sample_content)


def test_publish_to_obsidian_writes_content(sample_content):
    """Test that the function writes the content to a file"""
    with patch('os.makedirs'):
        with patch('builtins.open', mock_open()) as mock_file:
            # Call the function
            result = publish_to_obsidian(
                content=sample_content,
                vault_path="/path/to/vault",
                output_folder="News Digests",
                filename="digest-2023-05-01.md"
            )
            
            # Verify content was written to the file
            mock_file().write.assert_called_once_with(sample_content)
            
            # Verify the function returns the correct path
            expected_path = os.path.join(
                "/path/to/vault", 
                "News Digests", 
                "digest-2023-05-01.md"
            )
            assert result == expected_path


def test_publish_to_obsidian_with_empty_content():
    """Test publishing with empty content"""
    with patch('os.makedirs'):
        with patch('builtins.open', mock_open()) as mock_file:
            # Call the function with empty content
            publish_to_obsidian(
                content="",
                vault_path="/path/to/vault",
                output_folder="News Digests",
                filename="empty-digest.md"
            )
            
            # Verify empty content was written
            mock_file().write.assert_called_once_with("")


def test_publish_to_obsidian_path_handling():
    """Test path handling with different inputs"""
    test_cases = [
        # Windows-style paths
        {
            "vault_path": "C:\\Users\\test\\Obsidian",
            "output_folder": "News\\Digests",
            "filename": "digest.md"
        },
        # Unix-style paths
        {
            "vault_path": "/home/user/obsidian",
            "output_folder": "news/digests",
            "filename": "digest.md"
        },
        # Mixed path styles (which could happen in Windows)
        {
            "vault_path": "C:\\Users\\test\\Obsidian",
            "output_folder": "News/Digests",
            "filename": "digest.md"
        }
    ]
    
    # Test each case
    for case in test_cases:
        with patch('os.makedirs') as mock_makedirs:
            with patch('builtins.open', mock_open()) as mock_file:
                # Call the function
                result = publish_to_obsidian(
                    content="Test content",
                    vault_path=case["vault_path"],
                    output_folder=case["output_folder"],
                    filename=case["filename"]
                )
                
                # Verify directory was created
                expected_dir = os.path.join(
                    case["vault_path"], 
                    case["output_folder"]
                )
                mock_makedirs.assert_called_once_with(
                    expected_dir, 
                    exist_ok=True
                )
                
                # Verify file was opened with the correct path
                expected_path = os.path.join(
                    expected_dir, 
                    case["filename"]
                )
                mock_file.assert_called_once_with(
                    expected_path, 
                    "w", 
                    encoding="utf-8"
                )
                
                # Verify the function returns the correct path
                assert result == expected_path 