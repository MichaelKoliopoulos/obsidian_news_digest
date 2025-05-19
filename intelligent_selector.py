"""
Intelligent selector for the Obsidian News Digest application.
Directly accesses news sources and selects relevant articles based on user
preferences using LLM evaluation.
"""
import logging
import time
from typing import List, Dict, Any
from urllib.parse import urlparse

from newspaper import Article, build
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers.json import SimpleJsonOutputParser
from langchain_openai import ChatOpenAI

from config import Config, ArticleCandidate

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def extract_domain(url: str) -> str:
    """
    Extract the domain from a URL.
    
    Args:
        url: The URL to extract the domain from
        
    Returns:
        The domain of the URL
    """
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception as e:
        logger.warning(f"Error extracting domain from {url}: {e}")
        return ""


def discover_articles(
    news_sources: List[str], 
    max_articles_per_source: int = 10
) -> List[Dict[str, Any]]:
    """
    Discover articles from configured news sources using newspaper3k.
    
    Args:
        news_sources: List of news source URLs to fetch from
        max_articles_per_source: Maximum number of candidates per source
        
    Returns:
        List of article candidate dictionaries
    """
    all_articles = []
    
    for source_url in news_sources:
        try:
            logger.info(f"Discovering articles from {source_url}...")
            
            # Build newspaper from source URL
            paper = build(source_url)
            
            # Get all article URLs from the source
            article_urls = paper.article_urls()
            msg = f"Found {len(article_urls)} article links on {source_url}"
            logger.info(msg)
            
            # Convert to list and limit to avoid processing too many articles
            article_urls_list = list(article_urls)
            # Most news sites list headlines/important articles first
            max_urls = min(max_articles_per_source * 2, len(article_urls_list))
            sampled_urls = article_urls_list[:max_urls]
            
            source_articles = []
            for article_url in sampled_urls:
                try:
                    # Create an article object
                    article = Article(article_url)
                    
                    # Download just the article metadata (not full content)
                    article.download()
                    time.sleep(0.5)  # Pause briefly to be polite to the server
                    
                    # Parse the article to extract basic metadata
                    article.parse()
                    
                    # Skip articles with no title or minimal content
                    if not article.title:
                        continue
                    
                    # Create article candidate dictionary with basic info
                    source_domain = extract_domain(article_url)
                    # Get snippet for evaluation if available
                    snippet = article.text[:200] if article.text else None
                    
                    source_articles.append({
                        "title": article.title,
                        "url": article_url,
                        "source": source_domain,
                        "published_date": article.publish_date,
                        "snippet": snippet,
                        "original_source": source_url
                    })
                    
                    logger.info(f"Discovered: {article.title[:50]}...")
                    
                    # Stop once we have enough candidates
                    if len(source_articles) >= max_articles_per_source:
                        break
                        
                except Exception as e:
                    msg = f"Error processing article {article_url}: {e}"
                    logger.error(msg)
                    continue
            
            # Add articles from this source to our master list
            all_articles.extend(source_articles)
            msg = f"Found {len(source_articles)} articles from {source_url}"
            logger.info(msg)
            
        except Exception as e:
            logger.error(f"Error processing source {source_url}: {e}")
            continue
    
    return all_articles


def evaluate_articles(
    article_candidates: List[Dict[str, Any]], 
    config: Config
) -> List[ArticleCandidate]:
    """
    Evaluate article candidates using LLM based on user preferences.
    
    Args:
        article_candidates: List of article candidate dictionaries
        config: Application configuration
        
    Returns:
        List of evaluated ArticleCandidate objects
    """
    # Create LLM for evaluation
    llm = ChatOpenAI(
        api_key=config.api_key,
        model=config.model_name,
        temperature=0.2
    )
    
    preferences = config.news_preferences
    
    # Create evaluation prompt
    template = """
    As a news curator, evaluate this article candidate based on user 
    preferences.
    
    USER PREFERENCES:
    - Topics of interest: {topics}
    - Keywords to prioritize: {keywords}
    - Include opinion pieces: {include_opinion}
    - Include analysis articles: {include_analysis}
    - Geographic focus: {geographic_focus}
    
    ARTICLE CANDIDATE:
    - Title: {title}
    - Source: {source}
    - Snippet: {snippet}
    
    INSTRUCTIONS:
    Based on the information provided, evaluate this article:
    1. Is this article likely to be relevant to the user's topics of interest?
    2. Does the title contain any of the user's keywords?
    3. Determine if it's likely an opinion piece, analysis, or straight news
    4. Estimate its geographic focus
    5. Calculate an overall relevance score (0.0-1.0)
    
    Return your evaluation as a JSON object with these fields:
    - topics: list of likely topics covered
    - relevance_score: float between 0-1
    - is_opinion: boolean or null if can't determine
    - is_analysis: boolean or null if can't determine
    - geographic_focus: string or null
    - keywords_matched: list of matched keywords
    - evaluation_notes: string explaining your reasoning
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm | SimpleJsonOutputParser()
    
    # Process each article candidate
    evaluated_articles = []
    for candidate in article_candidates:
        try:
            # Skip excluded sources
            source_domain = candidate["source"]
            if source_domain in preferences.excluded_sources:
                logger.info(f"Skipping excluded source: {source_domain}")
                continue
            
            # Construct a clean snippet for evaluation
            snippet = candidate.get("snippet", "")
            title = candidate["title"]
            if not snippet:
                snippet = f"[No preview for {title}]"
            
            # Evaluate the article
            keywords = preferences.keywords if preferences.keywords else "N/A"
            geo_focus = preferences.geographic_focus
            
            eval_response = chain.invoke({
                "topics": ", ".join(preferences.topics),
                "keywords": ", ".join(keywords),
                "include_opinion": preferences.include_opinion,
                "include_analysis": preferences.include_analysis,
                "geographic_focus": ", ".join(geo_focus),
                "title": title,
                "source": source_domain,
                "snippet": snippet
            })
            
            # Create ArticleCandidate object
            article = ArticleCandidate(
                title=title,
                url=candidate["url"],
                source=source_domain,
                published_date=candidate.get("published_date"),
                snippet=snippet,
                topics=eval_response.get("topics", []),
                relevance_score=eval_response.get("relevance_score", 0.0),
                is_opinion=eval_response.get("is_opinion"),
                is_analysis=eval_response.get("is_analysis"),
                geographic_focus=eval_response.get("geographic_focus"),
                keywords_matched=eval_response.get("keywords_matched", []),
                evaluation_notes=eval_response.get("evaluation_notes"),
                selected=False  # Will be updated in the selection step
            )
            
            evaluated_articles.append(article)
            score = article.relevance_score
            logger.info(f"Evaluated: {title[:50]}... | Score: {score:.2f}")
            
        except Exception as e:
            logger.error(f"Error evaluating {candidate['title']}: {e}")
            continue
    
    return evaluated_articles


def select_articles(
    candidates: List[ArticleCandidate], 
    config: Config
) -> List[ArticleCandidate]:
    """
    Select the best articles from candidates based on user preferences.
    
    Args:
        candidates: List of evaluated article candidates
        config: Application configuration
        
    Returns:
        List of selected article candidates
    """
    preferences = config.news_preferences
    
    # First, filter out excluded sources
    filtered_candidates = [
        c for c in candidates 
        if c.source not in preferences.excluded_sources
    ]
    
    # Then filter by minimum relevance score
    relevant_candidates = [
        c for c in filtered_candidates 
        if c.relevance_score >= preferences.relevance_threshold
    ]
    
    # Apply content type filters
    if not preferences.include_opinion:
        relevant_candidates = [
            c for c in relevant_candidates 
            if not c.is_opinion
        ]
        
    if not preferences.include_analysis:
        relevant_candidates = [
            c for c in relevant_candidates 
            if not c.is_analysis
        ]
    
    # Prioritize preferred sources
    for candidate in relevant_candidates:
        if candidate.source in preferences.preferred_sources:
            # Boost score for preferred sources (but keep max at 1.0)
            boost_factor = 1.2
            new_score = candidate.relevance_score * boost_factor
            candidate.relevance_score = min(new_score, 1.0)
    
    # Sort by relevance score (descending)
    sorted_candidates = sorted(
        relevant_candidates, 
        key=lambda x: x.relevance_score, 
        reverse=True
    )
    
    # Select top articles up to max_articles
    selected_candidates = sorted_candidates[:preferences.max_articles]
    
    # Mark selected articles
    for candidate in selected_candidates:
        candidate.selected = True
    
    total = len(candidates)
    selected = len(selected_candidates)
    msg = f"Selected {selected} articles from {total} candidates"
    logger.info(msg)
    return selected_candidates


def get_article_urls(config: Config) -> List[str]:
    """
    Main function to get relevant article URLs based on user preferences.
    
    Args:
        config: Application configuration
        
    Returns:
        List of article URLs to fetch
    """
    try:
        # Step 1: Discover articles from configured news sources
        max_per_source = config.news_preferences.max_articles
        article_candidates = discover_articles(
            news_sources=config.news_sources,
            max_articles_per_source=max_per_source
        )
        
        if not article_candidates:
            logger.warning("No articles discovered from configured sources")
            return []
        
        # Step 2: Evaluate article candidates
        evaluated_candidates = evaluate_articles(article_candidates, config)
        
        if not evaluated_candidates:
            logger.warning("No articles passed evaluation criteria")
            return []
        
        # Step 3: Select the best articles
        selected = select_articles(evaluated_candidates, config)
        
        # Return URLs of selected articles
        urls = [article.url for article in selected]
        
        logger.info(f"Selected {len(urls)} articles for fetching")
        return urls
        
    except Exception as e:
        logger.error(f"Error in intelligent article selection: {e}")
        return [] 