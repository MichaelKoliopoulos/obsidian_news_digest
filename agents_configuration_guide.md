# LLM_config_guide

# Base Configuration (config.py)
    class Config(BaseModel)

# Article Selection Agent (intelligent_selector.py)

template = 
"""
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


# Summarization Agent (summarizer.py)

prompt = ChatPromptTemplate.from_template(
    """
    You are a Veteran News Journalist.
    Summarize this news article in 5 sentences. 
    Focus on the main facts and key details.
    
    Title: {title}
    
    Article: {text}
    
    Format your response in this exact format:
    
    ## {title}
    
    [Your 5 sentence summary here]
    
    *Source: {source_domain}*
    
    [Read more ↗]({url})
    
    ---
    """
)