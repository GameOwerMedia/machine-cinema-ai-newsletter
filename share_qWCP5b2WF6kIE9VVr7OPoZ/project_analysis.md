# MachineCinemaPLNews - Project Analysis

## Overview
A daily static newsletter system in Polish about AI that:
- Builds automatically at 09:00 Europe/Warsaw
- Outputs HTML to `/site` directory
- Appends to `/site/archive.html`
- Deploys via GitHub Pages

## Key Components

### Python Scripts
1. **fetch_ai_news.py** - Fetches AI news from various sources
2. **make_posts.py** - Formats posts with appropriate styling
3. **generate_all.py** - Main newsletter generator
4. **filters.py** - Content filtering logic
5. **utils.py** - Utility functions
6. **send_email.py** - Optional email sending

### Configuration
- **config.yaml** - Main configuration file
  - `newsletter.mode`: "top" or "segments"
  - `newsletter.per_bucket`: default 5
  - `seen_cache.record_only_published`: true by default
  - `link_policy.allow_google_news`: true

### Content Categories
1. **GenerativeAI creators** 🧠
   - Prompt engineering
   - AI tools (Stable Diffusion, Midjourney, Runway)
   - Creative workflows
   - Media generation techniques

2. **Marketing / fun** 🚀
   - AI advertising campaigns
   - Social media trends
   - Case studies
   - Fun AI applications

3. **Biznes & dev** 💼
   - AI regulations
   - Investments and funding
   - Enterprise development
   - Developer tools

### Features
- Automatic news collection from various sources
- Intelligent categorization into 3 groups
- Content formatting with category-specific styling
- Duplicate prevention (tracks used articles in `data/seen.json`)
- Multi-format output (Markdown and HTML)
- Polish translations and localization

### Output Structure
```
out/YYYY-MM-DD_ALL.md        # Newsletter in Markdown
site/YYYY-MM-DD.html         # Newsletter in HTML
site/index.html              # Always latest newsletter
site/archive.html            # Archive of all newsletters
```

### Automation
- GitHub Actions workflow runs at 07:00 & 08:00 UTC (09:00 Warsaw time)
- Idempotency check - exits if today's newsletter exists (unless FORCE_RUN=1)
- Automatic deployment to GitHub Pages

### Data Management
- `data/seen.json` - Tracks already used articles
- `data/subscribers.txt` - Email subscriber list (optional)
- Reset seen cache: set RESET_SEEN=1 or delete data/seen.json

## Technical Requirements
- Python 3.x
- PyYAML
- HTML/CSS for site generation
- GitHub Actions for automation
- GitHub Pages for deployment
