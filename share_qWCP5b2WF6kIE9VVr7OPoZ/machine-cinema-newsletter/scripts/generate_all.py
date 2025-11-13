#!/usr/bin/env python3
"""Main newsletter generator."""
import os
import sys
from pathlib import Path
from typing import List, Dict

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils import (
    load_config, read_json, write_json, ensure_dirs,
    today_pl_date, now_pl, idempotent_guard_for_today
)
from fetch_ai_news import fetch
from filters import is_relevant, dedup, categorize_item
from make_posts import to_md, to_html_page

def apply_seen(items: List[Dict], cfg: Dict) -> tuple[List[Dict], Dict]:
    """Apply seen cache to filter out already used items."""
    seen_path = Path(cfg.get("seen_cache", {}).get("path", "data/seen.json"))
    seen = read_json(seen_path)
    
    ttl_days = cfg.get("seen_cache", {}).get("ttl_days", 30)
    cutoff = now_pl().timestamp() - (ttl_days * 86400)
    
    # Clean old entries
    seen = {k: v for k, v in seen.items() if v.get("ts", 0) >= cutoff}
    
    # Filter items
    out = []
    for it in items:
        url = it.get("url", "")
        if url and url not in seen:
            out.append(it)
    
    return out, seen

def commit_seen(items_to_record: List[Dict], cfg: Dict, prev_seen: Dict) -> None:
    """Record newly used items in seen cache."""
    seen_path = Path(cfg.get("seen_cache", {}).get("path", "data/seen.json"))
    now = now_pl()
    
    for it in items_to_record:
        url = it.get("url", "")
        if url:
            prev_seen[url] = {"ts": now.timestamp()}
    
    write_json(seen_path, prev_seen)

def select_items(items: List[Dict], cfg: Dict) -> List[Dict]:
    """Select items based on configuration."""
    mode = cfg.get("newsletter", {}).get("mode", "segments")
    per_bucket = cfg.get("newsletter", {}).get("per_bucket", 5)
    
    if mode == "top":
        # Take top N items sorted by published date
        items = sorted(items, key=lambda x: x.get("published_at", ""), reverse=True)
        return items[:per_bucket * 3]  # Total items
    
    elif mode == "segments":
        # Take N items per category
        categories = cfg.get("categories", {})
        selected = []
        
        for cat_key in categories.keys():
            cat_items = [it for it in items if it.get("category") == cat_key]
            cat_items = sorted(cat_items, key=lambda x: x.get("published_at", ""), reverse=True)
            selected.extend(cat_items[:per_bucket])
        
        return selected
    
    return items

def update_archive(date_str: str, title: str) -> None:
    """Update archive.html with new newsletter entry."""
    arch_path = Path("client/public/archive.html")
    
    if arch_path.exists():
        content = arch_path.read_text(encoding="utf-8")
    else:
        content = """<!doctype html>
<html lang="pl">
<head>
  <meta charset="utf-8" />
  <title>Archiwum – Machine Cinema AI Newsletter</title>
  <link rel="stylesheet" href="assets/style.css" />
</head>
<body>
  <header>
    <h1>Archiwum Newsletterów</h1>
  </header>
  <main>
    <ul class="archive">
"""
    
    # Insert new entry at the top of the list
    link = f'<li><a href="{date_str}.html">{date_str}</a></li>'
    
    if '<ul class="archive">' in content:
        content = content.replace(
            '<ul class="archive">',
            f'<ul class="archive">\n      {link}'
        )
    
    arch_path.write_text(content, encoding="utf-8")

def main():
    """Main execution function."""
    # Ensure directories
    ensure_dirs(Path("data"), Path("out"), Path("client/public"), Path("client/public/assets"))
    
    # Load configuration
    cfg = load_config()
    date_str = today_pl_date()
    
    # Check idempotency
    if idempotent_guard_for_today(Path("client/public"), date_str):
        print(f"Today's issue already exists. Exiting.")
        return
    
    print(f"Generating newsletter for {date_str}...")
    
    # Fetch news
    raw = fetch(cfg)
    print(f"Fetched {len(raw)} items")
    
    # Filter for relevance
    raw = [it for it in raw if is_relevant(it)]
    print(f"After relevance filter: {len(raw)} items")
    
    # Deduplicate
    raw = dedup(raw)
    print(f"After dedup: {len(raw)} items")
    
    # Categorize
    for item in raw:
        item["category"] = categorize_item(item, cfg)
    
    # Apply seen cache
    cand, prev_seen = apply_seen(raw, cfg)
    print(f"After seen filter: {len(cand)} items")
    
    # Select items
    sel = select_items(cand, cfg)
    print(f"Selected {len(sel)} items")
    
    if not sel:
        print("No items selected; aborting without writing outputs.")
        return
    
    # Generate Markdown
    out_md = Path(f"out/{date_str}_ALL.md")
    md_content = to_md(sel, cfg, date_str)
    out_md.write_text(md_content, encoding="utf-8")
    print(f"Wrote {out_md}")
    
    # Generate HTML
    site_html = Path(f"client/public/{date_str}.html")
    page_html = to_html_page(date_str, cfg, "", sel)
    site_html.write_text(page_html, encoding="utf-8")
    print(f"Wrote {site_html}")
    
    # Overwrite index.html
    index_html = Path("client/public/index.html")
    index_html.write_text(page_html, encoding="utf-8")
    print(f"Wrote {index_html}")
    
    # Update archive
    update_archive(date_str, cfg.get("newsletter", {}).get("title", "Newsletter"))
    print("Updated archive.html")
    
    # Commit seen
    record_only = cfg.get("seen_cache", {}).get("record_only_published", True)
    items_for_cache = sel if record_only else cand
    commit_seen(items_for_cache, cfg, prev_seen)
    print(f"Committed {len(items_for_cache)} items to seen cache")
    
    print(f"✅ Newsletter generated successfully!")

if __name__ == "__main__":
    main()
