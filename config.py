"""
Configuration module for the Obsidian News Digest application.
Loads and validates environment variables and provides configuration settings.
"""
import os
from typing import List, Optional
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel, Field


class NewsPreferences(BaseModel):
    """User preferences for news article selection."""
    
    # Primary topic interests - high-level categories
    topics: List[str] = Field(
        default=["world news", "technology", "science"],
        description="Primary topics of interest for news selection"
    )
    
    # Specific keywords to prioritize in searches
    keywords: List[str] = Field(
        default=[],
        description="Specific keywords to prioritize in article selection"
    )
    
    # Content recency preference (in hours)
    max_age_hours: int = Field(
        default=24,
        description="Maximum age of news articles in hours"
    )
    
    # Preferred news sources to prioritize
    preferred_sources: List[str] = Field(
        default=[],
        description="News sources to prioritize if available"
    )
    
    # Sources to exclude
    excluded_sources: List[str] = Field(
        default=[],
        description="News sources to exclude from selection"
    )
    
    # Content type preferences
    include_opinion: bool = Field(
        default=True,
        description="Whether to include opinion pieces"
    )
    
    include_analysis: bool = Field(
        default=True,
        description="Whether to include analysis articles"
    )
    
    # Geographic focus
    geographic_focus: List[str] = Field(
        default=["global"],
        description=(
            "Geographic regions to focus on (e.g., 'US', 'Europe', 'global')"
        )
    )
    
    # Search relevance threshold (0-1)
    relevance_threshold: float = Field(
        default=0.7,
        description="Minimum relevance score for article selection (0-1)",
        ge=0.0,
        le=1.0
    )
    
    # Maximum articles to select
    max_articles: int = Field(
        default=10,
        description=(
            "Maximum number of articles to select through intelligent selection"
        ),
        ge=1
    )


class SearchResult(BaseModel):
    """Search result data model from DuckDuckGo."""
    
    title: str = Field(..., description="Title of the search result")
    link: str = Field(..., description="URL of the search result")
    snippet: Optional[str] = Field(
        None, 
        description="Text snippet from search result"
    )
    source: Optional[str] = Field(
        None, 
        description="Source domain of the result"
    )
    published_date: Optional[datetime] = Field(
        None, 
        description="Publication date if available"
    )
    query: str = Field(..., description="The query that generated this result")


class ArticleCandidate(BaseModel):
    """Candidate article for intelligent selection."""
    
    title: str = Field(..., description="Title of the article")
    url: str = Field(..., description="URL of the article")
    source: Optional[str] = Field(None, description="Source domain/publisher")
    published_date: Optional[datetime] = Field(
        None, 
        description="Publication date if available"
    )
    snippet: Optional[str] = Field(
        None, 
        description="Snippet or summary from search results"
    )
    topics: List[str] = Field(
        default=[], 
        description="Topics/categories of the article"
    )
    relevance_score: float = Field(
        default=0.0, 
        description="Score indicating relevance to user preferences",
        ge=0.0,
        le=1.0
    )
    is_opinion: Optional[bool] = Field(
        None, 
        description="Whether this is an opinion piece"
    )
    is_analysis: Optional[bool] = Field(
        None, 
        description="Whether this is an analysis article"
    )
    geographic_focus: Optional[str] = Field(
        None, 
        description="Geographic focus of the article"
    )
    keywords_matched: List[str] = Field(
        default=[], 
        description="User keywords matched in the article"
    )
    evaluation_notes: Optional[str] = Field(
        None, 
        description="Notes from the LLM evaluation"
    )
    selected: bool = Field(
        default=False, 
        description="Whether this article was selected for inclusion"
    )


class Config(BaseModel):
    """Configuration settings for the Obsidian News Digest application."""
    
    api_key: str = Field(..., description="OpenAI API key")
    vault_path: str = Field(..., description="Path to Obsidian vault")
    news_sources: List[str] = Field(
        default=["https://www.apnews.com/", "https://www.c-span.org/"],
        description=(
            "List of news source URLs for direct fetching (used as fallback)"
        )
    )
    max_articles: int = Field(
        default=10, 
        description="Maximum number of articles in the digest"
    )
    output_folder: str = Field(
        default="Daily_news", 
        description="Folder within Obsidian vault for saving digests"
    )
    model_name: str = Field(
        default="gpt-4.1-nano-2025-04-14", 
        description="OpenAI model to use for summarization"
    )
    
    # New fields for intelligent selection
    use_intelligent_selection: bool = Field(
        default=True,
        description="Whether to use intelligent article selection"
    )
    
    # Intelligent selection preferences
    news_preferences: NewsPreferences = Field(
        default_factory=NewsPreferences,
        description="User preferences for intelligent article selection"
    )
    
    # Maximum search queries to run
    max_search_queries: int = Field(
        default=3,
        description="Maximum number of search queries to generate"
    )
    
    # Number of search results to process per query
    results_per_query: int = Field(
        default=5,
        description="Number of search results to process per query"
    )


def load_config() -> Config:
    """
    Load and validate configuration from environment variables.
    
    Returns:
        Config: Validated configuration object
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Check if required environment variables are set
    api_key = os.getenv("OPENAI_API_KEY")
    vault_path = os.getenv("OBSIDIAN_VAULT_PATH")
    
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found! Make sure to set it in your .env file."
        )
        
    if not vault_path:
        print("⚠️ OBSIDIAN_VAULT_PATH not found! Using './output' as default.")
        vault_path = "./output"  # Default output folder
    
    # Load user preferences from environment variables if available
    use_intelligent = os.getenv("USE_INTELLIGENT_SELECTION")
    use_intelligent_selection = (
        use_intelligent.lower() in ('true', 'yes', '1') 
        if use_intelligent else None
    )
    
    topics_str = os.getenv("NEWS_TOPICS")
    topics = topics_str.split(",") if topics_str else None
    
    keywords_str = os.getenv("NEWS_KEYWORDS")
    keywords = keywords_str.split(",") if keywords_str else None
    
    max_age = os.getenv("NEWS_MAX_AGE_HOURS")
    max_age_hours = int(max_age) if max_age and max_age.isdigit() else None
    
    preferred_sources_str = os.getenv("NEWS_PREFERRED_SOURCES")
    preferred_sources = (
        preferred_sources_str.split(",") if preferred_sources_str else None
    )
    
    excluded_sources_str = os.getenv("NEWS_EXCLUDED_SOURCES")
    excluded_sources = (
        excluded_sources_str.split(",") if excluded_sources_str else None
    )
    
    include_opinion_str = os.getenv("NEWS_INCLUDE_OPINION")
    include_opinion = (
        include_opinion_str.lower() in ('true', 'yes', '1') 
        if include_opinion_str else None
    )
    
    include_analysis_str = os.getenv("NEWS_INCLUDE_ANALYSIS")
    include_analysis = (
        include_analysis_str.lower() in ('true', 'yes', '1') 
        if include_analysis_str else None
    )
    
    geo_focus_str = os.getenv("NEWS_GEOGRAPHIC_FOCUS")
    geographic_focus = geo_focus_str.split(",") if geo_focus_str else None
    
    relevance_str = os.getenv("NEWS_RELEVANCE_THRESHOLD")
    is_valid_float = (
        relevance_str and 
        relevance_str.replace('.', '', 1).isdigit()
    )
    relevance_threshold = float(relevance_str) if is_valid_float else None
    
    max_intel_articles_str = os.getenv("NEWS_MAX_ARTICLES")
    max_intel_articles = (
        int(max_intel_articles_str) 
        if (max_intel_articles_str and 
            max_intel_articles_str.isdigit()) 
        else None
    )
    
    # Create news preferences object if any preferences are specified
    news_prefs_kwargs = {}
    if topics:
        news_prefs_kwargs["topics"] = topics
    if keywords:
        news_prefs_kwargs["keywords"] = keywords
    if max_age_hours is not None:
        news_prefs_kwargs["max_age_hours"] = max_age_hours
    if preferred_sources:
        news_prefs_kwargs["preferred_sources"] = preferred_sources
    if excluded_sources:
        news_prefs_kwargs["excluded_sources"] = excluded_sources
    if include_opinion is not None:
        news_prefs_kwargs["include_opinion"] = include_opinion
    if include_analysis is not None:
        news_prefs_kwargs["include_analysis"] = include_analysis
    if geographic_focus:
        news_prefs_kwargs["geographic_focus"] = geographic_focus
    if relevance_threshold is not None:
        news_prefs_kwargs["relevance_threshold"] = relevance_threshold
    if max_intel_articles is not None:
        news_prefs_kwargs["max_articles"] = max_intel_articles
    
    # Create config object with basic settings
    config_kwargs = {
        "api_key": api_key,
        "vault_path": vault_path,
    }
    
    # Add intelligent selection flag if specified
    if use_intelligent_selection is not None:
        config_kwargs["use_intelligent_selection"] = use_intelligent_selection
    
    # Add news preferences if any are specified
    if news_prefs_kwargs:
        config_kwargs["news_preferences"] = NewsPreferences(
            **news_prefs_kwargs
        )
    
    # Create the config object
    config = Config(**config_kwargs)
    
    print("✅ Configuration loaded")
    print(
        f"📁 Output path: {os.path.join(config.vault_path, config.output_folder)}"
    )
    print(f"📰 News sources: {len(config.news_sources)} sources configured")
    print(f"📊 Max articles: {config.max_articles}")
    
    # Print intelligent selection info if enabled
    if config.use_intelligent_selection:
        print("🧠 Intelligent article selection: Enabled")
        topics_str = ', '.join(config.news_preferences.topics[:3])
        more_topics = ""
        if len(config.news_preferences.topics) > 3:
            more_count = len(config.news_preferences.topics) - 3
            more_topics = f" and {more_count} more"
        print(f"🔍 Topics: {topics_str}{more_topics}")
        
        if config.news_preferences.keywords:
            keywords_str = ', '.join(config.news_preferences.keywords[:3])
            more_keywords = ""
            if len(config.news_preferences.keywords) > 3:
                more_count = len(config.news_preferences.keywords) - 3
                more_keywords = f" and {more_count} more"
            print(f"🔑 Keywords: {keywords_str}{more_keywords}")
    else:
        print("🧠 Intelligent article selection: Disabled")
    
    return config