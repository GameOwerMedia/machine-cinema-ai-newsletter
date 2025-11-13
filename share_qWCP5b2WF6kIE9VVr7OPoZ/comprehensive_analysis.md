# MachineCinemaPLNews - Comprehensive Analysis

## Project Overview
A Polish AI news newsletter system that automatically generates daily static HTML newsletters at 09:00 Europe/Warsaw time, deploys to GitHub Pages, and maintains an archive.

## Core Functionality

### 1. News Fetching (fetch_ai_news.py)
- Fetches news from RSS feeds (Google News RSS feeds for AI topics)
- RSS feeds include various AI-related search queries
- Parses RSS feeds using feedparser
- Extracts: title, summary, URL, source, published date, topic
- Returns normalized list of news items
- Handles both live fetch and curated fallback

### 2. Content Filtering (filters.py)
- `is_relevant()` - filters relevant AI news
- `dedup()` - removes duplicate articles

### 3. Post Formatting (make_posts.py)
- `to_md()` - converts news items to Markdown format
- `to_html_page()` - converts to HTML with proper styling
- Handles different formatting for different categories

### 4. Main Generator (generate_all.py)
**Key Functions:**
- `apply_seen()` - checks against seen cache (data/seen.json) to prevent duplicates
- `commit_seen()` - records newly used articles
- `select_items()` - selects items based on mode (top/segments) and per_bucket config
- `update_archive()` - appends new newsletter to archive.html
- `main()` - orchestrates the entire process

**Workflow:**
1. Check if today's newsletter already exists (idempotency)
2. Load configuration from config.yaml
3. Fetch news from sources
4. Filter for relevance and deduplicate
5. Apply seen cache to exclude already used articles
6. Select items based on configuration
7. Generate outputs:
   - `out/YYYY-MM-DD_ALL.md` - Markdown version
   - `site/YYYY-MM-DD.html` - Daily HTML newsletter
   - `site/index.html` - Latest newsletter (copy)
   - `site/archive.html` - Updated archive
8. Commit used articles to seen cache

### 5. Email Sending (send_email.py)
- Optional feature
- Sends newsletter via SMTP
- Requires environment variables: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM

### 6. Utilities (utils.py)
- Helper functions for file operations
- Configuration loading
- Date handling

## Configuration (config.yaml)
```yaml
newsletter:
  mode: "top" or "segments"
  per_bucket: 5  # number of items per category
  
seen_cache:
  record_only_published: true
  
link_policy:
  allow_google_news: true
```

## Output Structure
```
out/
  └── YYYY-MM-DD_ALL.md          # Markdown newsletter

site/
  ├── assets/
  │   └── custom.css             # Styling
  ├── index.html                 # Latest newsletter
  ├── YYYY-MM-DD.html           # Daily newsletters
  └── archive.html              # Archive list

data/
  ├── seen.json                 # Seen articles cache
  └── subscribers.txt           # Email subscribers (optional)
```

## HTML Structure (from index.html)
```html
<!doctype html>
<html lang="pl">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Machine Cinema – AI News (PL) – 2025-10-25</title>
  <link rel="stylesheet" href="assets/custom.css" />
</head>
<body>
  <header>
    <h1>Machine Cinema – Przegląd AI (PL)</h1>
    <div class="date">2025-10-25</div>
  </header>
  <main>
    <ul class="news">
      <li>
        <a href="[URL]" target="_blank" rel="noopener">
          <span class="src">(Google News)</span>
        </a>
      </li>
      <!-- More news items -->
    </ul>
  </main>
  <footer>
    <nav>
      <a href="[GitHub URL]">GitHub</a> | 
      <a href="[Machine Cinema URL]">Machine Cinema</a>
    </nav>
  </footer>
</body>
</html>
```

## GitHub Actions Automation
- **daily-0900.yml**: Runs at 07:00 & 08:00 UTC (09:00 Warsaw time accounting for DST)
  - Runs generate_all.py
  - Commits generated files
- **pages.yml**: Deploys /site directory to GitHub Pages on push

## Key Features
1. **Idempotency**: Won't regenerate if today's newsletter exists (unless FORCE_RUN=1)
2. **Duplicate Prevention**: Tracks used articles in data/seen.json
3. **Reset Capability**: Set RESET_SEEN=1 to clear seen cache
4. **Multi-format Output**: Both Markdown and HTML
5. **Archive Management**: Automatically updates archive.html
6. **Polish Localization**: All content in Polish
7. **Category Support**: Can organize by categories (creators, marketing, business)

## Environment Variables
- `FORCE_RUN=1` - Force regeneration even if today's newsletter exists
- `RESET_SEEN=1` - Clear seen cache
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM` - For email sending

## Dependencies
- Python 3.x
- pyyaml - Configuration parsing
- feedparser - RSS feed parsing
- datetime, timedelta - Date handling
- pathlib - File operations
- zoneinfo - Timezone handling

## User Requirements (from attachment)
The user wants a similar system with:
- 3 categories: GenerativeAI creators, Marketing/fun, Biznes & dev
- Polish language
- Automatic daily generation
- HTML output with styling
- Archive functionality
- GitHub Pages deployment
- Duplicate prevention via seen_urls.txt
- Keyword-based categorization
