"""Content filtering and deduplication."""
from typing import List, Dict

# AI-related keywords for relevance filtering
AI_KEYWORDS = [
    "ai", "sztuczna inteligencja", "artificial intelligence",
    "machine learning", "deep learning", "neural network",
    "chatgpt", "gpt", "openai", "anthropic", "claude",
    "midjourney", "stable diffusion", "dall-e", "dalle",
    "generative", "generatywn", "llm", "model językowy",
    "automatyzacja", "automation", "robotyka", "robotic",
]

def is_relevant(item: Dict) -> bool:
    """Check if item is relevant to AI topics."""
    text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    
    # Check if any AI keyword is present
    for keyword in AI_KEYWORDS:
        if keyword.lower() in text:
            return True
    
    return False

def dedup(items: List[Dict]) -> List[Dict]:
    """Remove duplicate items based on URL and title similarity."""
    seen_urls = set()
    seen_titles = set()
    out: List[Dict] = []
    
    for item in items:
        url = item.get("url", "")
        title = item.get("title", "").lower().strip()
        
        # Skip if URL already seen
        if url in seen_urls:
            continue
        
        # Skip if very similar title already seen
        if title and title in seen_titles:
            continue
        
        seen_urls.add(url)
        if title:
            seen_titles.add(title)
        
        out.append(item)
    
    return out

def categorize_item(item: Dict, config: Dict) -> str:
    """Categorize item based on keywords."""
    text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    
    categories = config.get("categories", {})
    
    # Check each category
    for cat_key, cat_data in categories.items():
        keywords = cat_data.get("keywords", [])
        for keyword in keywords:
            if keyword.lower() in text:
                return cat_key
    
    # Default to first category
    return list(categories.keys())[0] if categories else "general"
