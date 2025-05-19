"""
Unit tests for the summarizer module
"""
import pytest
from unittest.mock import patch, MagicMock

from summarizer import summarize_articles


@pytest.fixture
def sample_articles():
    """Sample articles for testing"""
    return [
        {
            "title": "Test Article 1",
            "text": "This is the content of test article 1.",
            "url": "https://example.com/article1",
            "source": "https://example.com"
        },
        {
            "title": "Test Article 2",
            "text": "This is the content of test article 2.",
            "url": "https://example.com/article2",
            "source": "https://example.com"
        }
    ]


def test_summarize_articles_successful(sample_articles):
    """Test successful summarization of articles"""
    # Create response contents
    response_contents = []
    for i, article in enumerate(sample_articles):
        response_contents.append(f"""
## {article['title']}

This is a summary of article {i+1}.
It contains exactly five sentences.
Each sentence conveys important information.
The fourth sentence adds more context.
The fifth sentence concludes the summary.

*Source: example.com*

[Read more ↗]({article['url']})

---
""")
    
    # Mock the chat model
    mock_llm = MagicMock()
    
    # Mock the invoke responses
    mock_responses = []
    for content in response_contents:
        mock_response = MagicMock()
        mock_response.content = content
        mock_responses.append(mock_response)
    
    # Set up chain invoke to return our responses in sequence
    mock_chain = MagicMock()
    mock_chain.invoke.side_effect = mock_responses
    
    # Mock the or operator to return our mock chain
    mock_prompt = MagicMock()
    mock_prompt.__or__.return_value = mock_chain
    
    # Use patching for all necessary components
    with patch('summarizer.ChatOpenAI', return_value=mock_llm) as mock_chat_openai:
        with patch('summarizer.ChatPromptTemplate.from_template', 
                  return_value=mock_prompt) as mock_template:
            
            # Call the function
            result = summarize_articles(
                sample_articles, 
                api_key="test_api_key", 
                model_name="test_model"
            )
            
            # Verify the ChatOpenAI was initialized correctly
            mock_chat_openai.assert_called_once_with(
                api_key="test_api_key",
                model="test_model",
                temperature=0.2
            )
            
            # Verify prompt template was created
            mock_template.assert_called_once()
            
            # Verify the prompt was piped to the LLM at least once
            # The pipe operator is called for each article in the loop
            mock_prompt.__or__.assert_called_with(mock_llm)
            assert mock_prompt.__or__.call_count == len(sample_articles)
            
            # Verify we got summaries for all articles
            assert len(result) == len(sample_articles)
            
            # Verify each article was summarized correctly
            for i, article in enumerate(result):
                assert "summary" in article
                assert article["title"] == sample_articles[i]["title"]
                # Remove leading/trailing whitespace for comparison
                assert article["summary"].strip() == response_contents[i].strip()


def test_summarize_articles_error_handling(sample_articles):
    """Test handling of errors during summarization"""
    # Mock the chat model
    mock_llm = MagicMock()
    
    # Set up chain - the first invoke call will raise an exception
    mock_chain = MagicMock()
    # First invoke raises exception, second returns a successful result
    mock_successful_response = MagicMock()
    mock_successful_response.content = """
## Test Article 2

This is a summary of article 2.
It contains exactly five sentences.
Each sentence conveys important information.
The fourth sentence adds more context.
The fifth sentence concludes the summary.

*Source: example.com*

[Read more ↗](https://example.com/article2)

---
"""
    
    # First call raises exception, second returns success
    def mock_invoke_side_effect(params):
        if params["title"] == sample_articles[0]["title"]:
            raise Exception("API error")
        return mock_successful_response
    
    mock_chain.invoke.side_effect = mock_invoke_side_effect
    
    # Mock the or operator to return our mock chain
    mock_prompt = MagicMock()
    mock_prompt.__or__.return_value = mock_chain
    
    # Apply our mocks
    with patch('summarizer.ChatOpenAI', return_value=mock_llm):
        with patch('summarizer.ChatPromptTemplate.from_template', 
                  return_value=mock_prompt):
            
            # Call the function
            result = summarize_articles(
                sample_articles, 
                api_key="test_api_key", 
                model_name="test_model"
            )
    
    # Verify we got results for all articles
    assert len(result) == len(sample_articles)
    
    # First article should have error message
    assert "summary" in result[0]
    assert "Summary unavailable" in result[0]["summary"]
    
    # Second article should have proper summary
    assert "summary" in result[1]
    assert "This is a summary of article 2" in result[1]["summary"]


def test_source_domain_extraction(sample_articles):
    """Test extraction of source domain from URL"""
    # Create a more complex source URL
    complex_url = "https://www.test-news.example.com/section/news"
    sample_articles[0]["source"] = complex_url
    
    # Mock the chain to capture the invoke parameters
    mock_chain = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Test summary"
    mock_chain.invoke.return_value = mock_response
    
    # Mock the chat model and prompt
    mock_llm = MagicMock()
    mock_prompt = MagicMock()
    mock_prompt.__or__.return_value = mock_chain
    
    # Apply our mocks
    with patch('summarizer.ChatOpenAI', return_value=mock_llm):
        with patch('summarizer.ChatPromptTemplate.from_template', 
                  return_value=mock_prompt):
            
            # Call the function
            summarize_articles(
                [sample_articles[0]], 
                api_key="test_api_key", 
                model_name="test_model"
            )
    
    # Get the parameters passed to invoke
    invoke_args, _ = mock_chain.invoke.call_args
    
    # Verify the source domain was correctly extracted
    assert invoke_args[0]["source_domain"] == "test-news.example.com" 