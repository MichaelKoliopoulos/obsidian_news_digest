"""
Main entry point for the Obsidian News Digest application.
Orchestrates the news fetching, summarization, and publishing workflow.
"""
import sys
import argparse
from typing import List, Optional

from config import load_config
from news_fetcher import fetch_news
from summarizer import summarize_articles
from formatter import format_digest, get_digest_filename
from publisher import publish_to_obsidian
from intelligent_selector import get_article_urls


def create_news_digest(sources=None, max_articles_count=None, use_intelligent=None):
    """
    Execute the complete news digest workflow.
    
    Args:
        sources: Optional list of news source URLs
        max_articles_count: Optional maximum number of articles
        use_intelligent: Optional override for intelligent selection
        
    Returns:
        Path to the created digest file or None if error
    """
    try:
        # Load configuration
        config = load_config()
        
        # Use provided parameters or defaults from config
        if sources is None:
            sources = config.news_sources
            
        if max_articles_count is None:
            max_articles_count = config.max_articles
            
        # Override intelligent selection if specified
        if use_intelligent is not None:
            config.use_intelligent_selection = use_intelligent
        
        # Step 1a: Use intelligent selection if enabled
        if config.use_intelligent_selection:
            print("🧠 Using intelligent article selection...")
            article_urls = get_article_urls(config)
            
            if article_urls:
                print(f"📰 Found {len(article_urls)} articles through intelligent selection")
                articles = fetch_news(article_urls, max_articles_per_source=1)
                print(f"Retrieved {len(articles)} articles")
            else:
                print("⚠️ Intelligent selection found no articles, falling back to direct sources")
                # Fall back to direct source fetching if intelligent selection fails
                print(f"📰 Fetching news from {len(sources)} direct sources...")
                articles = fetch_news(
                    sources, 
                    max_articles_per_source=max_articles_count//len(sources)
                )
                print(f"Retrieved {len(articles)} articles from direct sources")
        
        # Step 1b: Traditional direct source fetching if intelligent selection is disabled
        else:
            print(f"📰 Fetching news from {len(sources)} sources...")
            articles = fetch_news(
                sources, 
                max_articles_per_source=max_articles_count//len(sources)
            )
            print(f"Retrieved {len(articles)} articles")
        
        # Take top articles if we have more than max_articles_count
        selected_articles = articles[:max_articles_count]
        print(f"Selected {len(selected_articles)} articles for summarization")
        
        # Step 2: Summarize articles
        print("🔍 Summarizing and formatting articles...")
        summarized_articles = summarize_articles(
            selected_articles, 
            api_key=config.api_key,
            model_name=config.model_name
        )
        
        # Step 3: Format the digest
        digest_content = format_digest(summarized_articles)
        digest_filename = get_digest_filename()
        
        # Step 4: Publish to Obsidian
        print("💾 Publishing to Obsidian...")
        file_path = publish_to_obsidian(
            content=digest_content,
            vault_path=config.vault_path,
            output_folder=config.output_folder,
            filename=digest_filename
        )
        
        print(f"✅ News digest published successfully to: {file_path}")
        return file_path
        
    except Exception as e:
        print(f"❌ Error in news digest pipeline: {e}")
        return None


def main():
    """
    Main entry point when script is run directly.
    Parses command line arguments and executes the workflow.
    """
    # Set up argument parsing
    parser = argparse.ArgumentParser(
        description="Generate a daily news digest in your Obsidian vault"
    )
    
    # Add command-line arguments
    parser.add_argument(
        "--sources",
        nargs="+",
        help="Specific news sources to use (space-separated URLs)"
    )
    
    parser.add_argument(
        "--max-articles",
        type=int,
        help="Maximum number of articles to include in the digest"
    )
    
    parser.add_argument(
        "--intelligent",
        action="store_true",
        help="Enable intelligent article selection (override config setting)"
    )
    
    parser.add_argument(
        "--direct-only",
        action="store_true",
        help="Use only direct source fetching, disable intelligent selection"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Determine whether to use intelligent selection (CLI args override config)
    use_intelligent = None
    if args.intelligent:
        use_intelligent = True
    elif args.direct_only:
        use_intelligent = False
    
    # Run the digest creation with command-line arguments
    result = create_news_digest(
        sources=args.sources,
        max_articles_count=args.max_articles,
        use_intelligent=use_intelligent
    )
    
    if result:
        print(f"\n🎉 Success! Your news digest is ready at: {result}")
        print("Check your Obsidian vault to see the complete digest.")
        return 0
    else:
        print("\n❌ Workflow failed. Check the error messages above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())