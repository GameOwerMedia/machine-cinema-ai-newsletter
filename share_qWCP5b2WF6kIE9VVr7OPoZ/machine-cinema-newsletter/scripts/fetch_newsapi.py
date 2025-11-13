#!/usr/bin/env python3
"""
Fetch AI news from NewsAPI proxy (no API key needed)
Uses https://saurav.tech/NewsAPI/ which is a free proxy
"""

import json
import sys
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# NewsAPI proxy base URL (no API key needed!)
BASE_URL = "https://saurav.tech/NewsAPI"

# AI-related keywords for filtering
AI_KEYWORDS = [
    "artificial intelligence", "AI", "machine learning", "deep learning",
    "neural network", "GPT", "ChatGPT", "OpenAI", "generative AI",
    "LLM", "large language model", "computer vision", "NLP",
    "natural language processing", "automation", "robotics"
]

def fetch_news_from_source(source_id):
    """Fetch news from a specific source"""
    url = f"{BASE_URL}/everything/{source_id}.json"
    
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get('articles', [])
    except (URLError, HTTPError) as e:
        print(f"Error fetching from {source_id}: {e}", file=sys.stderr)
        return []

def fetch_tech_headlines(country='us'):
    """Fetch technology headlines from a country"""
    url = f"{BASE_URL}/top-headlines/category/technology/{country}.json"
    
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get('articles', [])
    except (URLError, HTTPError) as e:
        print(f"Error fetching tech headlines: {e}", file=sys.stderr)
        return []

def is_ai_related(article):
    """Check if article is AI-related"""
    text = f"{article.get('title', '')} {article.get('description', '')}".lower()
    return any(keyword.lower() in text for keyword in AI_KEYWORDS)

def categorize_article(article):
    """Categorize article based on content"""
    text = f"{article.get('title', '')} {article.get('description', '')}".lower()
    
    # GenerativeAI creators keywords
    if any(kw in text for kw in ['gpt', 'chatgpt', 'midjourney', 'dall-e', 'stable diffusion', 'generative', 'openai', 'anthropic', 'claude']):
        return 'creators'
    
    # Marketing & fun keywords
    if any(kw in text for kw in ['marketing', 'social media', 'advertising', 'campaign', 'viral', 'trend', 'entertainment']):
        return 'marketing'
    
    # Default to bizdev
    return 'bizdev'

def main():
    """Main function to fetch and categorize AI news"""
    all_articles = []
    
    # Fetch from major news sources
    sources = ['cnn', 'bbc-news', 'google-news']
    
    for source in sources:
        articles = fetch_news_from_source(source)
        all_articles.extend(articles)
    
    # Also fetch tech headlines
    tech_articles = fetch_tech_headlines('us')
    all_articles.extend(tech_articles)
    
    # Filter for AI-related articles
    ai_articles = [article for article in all_articles if is_ai_related(article)]
    
    # Categorize and format articles
    categorized_articles = []
    for article in ai_articles:
        categorized_articles.append({
            'title': article.get('title', ''),
            'description': article.get('description', ''),
            'url': article.get('url', ''),
            'source': article.get('source', {}).get('name', 'Unknown'),
            'imageUrl': article.get('urlToImage', ''),
            'publishedAt': article.get('publishedAt', datetime.now().isoformat()),
            'category': categorize_article(article)
        })
    
    # Output as JSON
    print(json.dumps({
        'success': True,
        'totalArticles': len(all_articles),
        'aiArticles': len(categorized_articles),
        'articles': categorized_articles
    }, indent=2))

if __name__ == '__main__':
    main()
