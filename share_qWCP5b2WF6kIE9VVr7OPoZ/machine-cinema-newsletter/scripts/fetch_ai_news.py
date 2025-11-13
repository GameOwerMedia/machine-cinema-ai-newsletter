"""Fetch AI news from RSS feeds."""
from __future__ import annotations
import feedparser
from datetime import datetime, timedelta, timezone
from typing import List, Dict
from utils import canonical_or_allowed, now_pl

# RSS feeds for AI news (Google News RSS)
RSS_FEEDS = [
    "https://news.google.com/rss/search?q=sztuczna+inteligencja&hl=pl&gl=PL&ceid=PL:pl",
    "https://news.google.com/rss/search?q=AI+generatywne&hl=pl&gl=PL&ceid=PL:pl",
    "https://news.google.com/rss/search?q=OpenAI&hl=pl&gl=PL&ceid=PL:pl",
    "https://news.google.com/rss/search?q=ChatGPT&hl=pl&gl=PL&ceid=PL:pl",
    "https://news.google.com/rss/search?q=Midjourney&hl=pl&gl=PL&ceid=PL:pl",
    "https://news.google.com/rss/search?q=Stable+Diffusion&hl=pl&gl=PL&ceid=PL:pl",
]

def _live_fetch_24h(window_hours: int) -> List[Dict]:
    """Fetch news from RSS feeds within the time window."""
    cutoff = now_pl() - timedelta(hours=window_hours)
    out: List[Dict] = []
    
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:50]:  # Limit to 50 entries per feed
                # Extract data
                link = entry.get("link") or ""
                title = (entry.get("title") or "").strip()
                summary = (entry.get("summary") or "").strip()
                
                # Parse published date
                dt = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    except:
                        pass
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    try:
                        dt = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                    except:
                        pass
                else:
                    dt = now_pl()
                
                if dt and dt < cutoff:
                    continue
                
                out.append({
                    "title": title,
                    "summary": summary,
                    "url": canonical_or_allowed(link),
                    "source": feed.feed.get("title", "Google News"),
                    "published_at": dt.isoformat() if dt else now_pl().isoformat(),
                    "topic": "OGólne",
                })
        except Exception as ex:
            print(f"RSS fetch failed for {url}: {ex}")
            continue
    
    return out

def _load_curated() -> List[Dict]:
    """Load curated fallback data."""
    from pathlib import Path
    import json
    
    curated_path = Path("data/curated.json")
    if not curated_path.exists():
        return []
    
    try:
        with open(curated_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def normalize(items: List[Dict]) -> List[Dict]:
    """Normalize items to consistent format."""
    out: List[Dict] = []
    for it in items:
        url = canonical_or_allowed((it.get("url") or "").strip())
        if not url:
            continue
        
        out.append({
            "title": (it.get("title") or "").strip(),
            "summary": (it.get("summary") or "").strip(),
            "url": url,
            "source": (it.get("source") or "unknown").strip(),
            "published_at": it.get("published_at") or now_pl().isoformat(),
            "topic": it.get("topic") or "OGólne",
        })
    
    return out

def fetch(config: Dict) -> List[Dict]:
    """Main fetch function."""
    items: List[Dict] = []
    
    # Try live fetch
    if config.get("sources", {}).get("live_enabled", True):
        window_hours = config.get("time", {}).get("window_hours", 24)
        items = _live_fetch_24h(window_hours)
    
    # Fallback to curated
    if not items and config.get("sources", {}).get("curated_first", False):
        items = _load_curated()
    
    return normalize(items)
