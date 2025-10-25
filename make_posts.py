import re
from urllib.parse import urlparse

def format_post(item, style="creators"):
    """Format a news item into a post with appropriate styling"""
    title = item.get("title", "").strip()
    link = item.get("link", "").strip()
    summary = item.get("summary", "").strip()
    
    # Clean up summary (remove HTML tags, etc.)
    summary = re.sub(r'<[^>]+>', '', summary)
    summary = summary.replace('&nbsp;', ' ').replace('&amp;', '&')
    
    # Extract domain for source attribution
    domain = "Unknown source"
    if link and "://" in link:
        try:
            domain = urlparse(link).netloc
            if domain.startswith("www."):
                domain = domain[4:]
        except:
            domain = link.split("/")[2] if len(link.split("/")) > 2 else "Unknown"
    
    # Style-specific symbols and formatting (using ASCII for Windows compatibility)
    symbols = {
        "creators": "[AI]",      # AI symbol for creative AI
        "marketing": "[MKT]",    # Marketing symbol
        "bizdev": "[BIZ]"       # Business symbol
    }
    
    style_hooks = {
        "creators": " — workflow i praktyka",
        "marketing": " — kampanie i trendy",  
        "bizdev": " — rozwój i regulacje"
    }
    
    symbol = symbols.get(style, "[NEWS]")  # News as default
    hook = style_hooks.get(style, "")
    
    # Build the formatted post
    parts = []
    
    # Title with symbol and style hook
    parts.append(f"{symbol} {title}{hook}")
    
    # Summary (if available)
    if summary and len(summary) > 10:
        # Truncate long summaries
        if len(summary) > 200:
            summary = summary[:197] + "..."
        parts.append(summary)
    
    # Link with source attribution
    source_text = f" (Źródło: {domain})" if domain != "Unknown source" else ""
    parts.append(f"LINK: {link}{source_text}")
    
    return "\n".join(parts)

def test_formatting():
    """Test function to verify formatting works correctly"""
    test_item = {
        "title": "OpenAI releases new GPT-5 model with enhanced capabilities",
        "link": "https://openai.com/blog/gpt-5-release",
        "summary": "The new GPT-5 model features improved reasoning, better memory, and enhanced multimodal capabilities that push the boundaries of what AI can achieve."
    }
    
    print("Creators style:")
    print(format_post(test_item, "creators"))
    print("\nMarketing style:")
    print(format_post(test_item, "marketing")) 
    print("\nBizdev style:")
    print(format_post(test_item, "bizdev"))

if __name__ == "__main__":
    test_formatting()
