"""Format posts to Markdown and HTML."""
from typing import List, Dict

def to_md(items: List[Dict], cfg: Dict, date_str: str) -> str:
    """Convert items to Markdown format."""
    title = cfg.get("newsletter", {}).get("title", "Newsletter AI")
    
    lines = [
        f"# {title} — {date_str}",
        "",
    ]
    
    # Group by category
    categories = cfg.get("categories", {})
    categorized = {}
    
    for item in items:
        cat = item.get("category", "general")
        if cat not in categorized:
            categorized[cat] = []
        categorized[cat].append(item)
    
    # Write each category
    for cat_key, cat_data in categories.items():
        if cat_key not in categorized or not categorized[cat_key]:
            continue
        
        cat_name = cat_data.get("name", cat_key)
        lines.append(f"## {cat_name}")
        lines.append("")
        
        for idx, item in enumerate(categorized[cat_key], 1):
            title_text = item.get("title", "Bez tytułu")
            summary = item.get("summary", "")
            url = item.get("url", "")
            source = item.get("source", "")
            
            lines.append(f"{idx}. **{title_text}**")
            if summary:
                lines.append(f"   {summary}")
            lines.append(f"   [Link]({url}) (Źródło: {source})")
            lines.append("")
    
    return "\n".join(lines)

def to_html_page(date_str: str, cfg: Dict, html_content: str, sel: List[Dict]) -> str:
    """Generate complete HTML page."""
    title = cfg.get("newsletter", {}).get("title", "Newsletter AI")
    categories = cfg.get("categories", {})
    
    # Build HTML content
    html_parts = []
    
    # Group by category
    categorized = {}
    for item in sel:
        cat = item.get("category", "general")
        if cat not in categorized:
            categorized[cat] = []
        categorized[cat].append(item)
    
    # Generate HTML for each category
    for cat_key, cat_data in categories.items():
        if cat_key not in categorized or not categorized[cat_key]:
            continue
        
        cat_name = cat_data.get("name", cat_key)
        html_parts.append(f'<section class="category">')
        html_parts.append(f'<h2>{cat_name}</h2>')
        html_parts.append('<ul class="news-list">')
        
        for item in categorized[cat_key]:
            title_text = item.get("title", "Bez tytułu")
            summary = item.get("summary", "")
            url = item.get("url", "")
            source = item.get("source", "")
            
            html_parts.append('<li class="news-item">')
            html_parts.append(f'<h3><a href="{url}" target="_blank" rel="noopener">{title_text}</a></h3>')
            if summary:
                html_parts.append(f'<p class="summary">{summary}</p>')
            html_parts.append(f'<p class="source">Źródło: {source}</p>')
            html_parts.append('</li>')
        
        html_parts.append('</ul>')
        html_parts.append('</section>')
    
    content_html = "\n".join(html_parts)
    
    # Complete HTML page
    html = f"""<!doctype html>
<html lang="pl">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title} – {date_str}</title>
  <link rel="stylesheet" href="assets/style.css" />
</head>
<body>
  <header>
    <h1>{title}</h1>
    <div class="date">{date_str}</div>
  </header>
  <main>
    {content_html}
  </main>
  <footer>
    <nav>
      <a href="archive.html">Archiwum</a> | 
      <a href="https://github.com/yourusername/machine-cinema-newsletter">GitHub</a>
    </nav>
  </footer>
</body>
</html>"""
    
    return html
