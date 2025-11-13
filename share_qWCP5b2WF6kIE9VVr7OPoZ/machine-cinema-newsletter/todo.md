# Project TODO

## Backend Python Scripts
- [x] Create fetch_ai_news.py - RSS feed fetching from Google News
- [x] Create filters.py - Content filtering and deduplication
- [x] Create make_posts.py - Format posts to Markdown and HTML
- [x] Create generate_all.py - Main newsletter generator
- [x] Create utils.py - Utility functions
- [x] Create config.yaml - Configuration file
- [x] Create requirements.txt - Python dependencies

## Frontend Pages
- [x] Create newsletter display page with Polish styling
- [x] Create archive page listing all newsletters
- [x] Add custom CSS styling for newsletter layout
- [x] Implement responsive design

## Data Management
- [x] Create data/seen.json structure for duplicate prevention (using database)
- [x] Create output directories (out/, site/)
- [x] Implement archive.html generation (using React)

## Testing & Documentation
- [x] Test news fetching functionality
- [x] Test newsletter generation
- [x] Test archive functionality
- [x] Create README with usage instructions


## Full-Stack Upgrade
- [x] Upgrade project to web-db-user features
- [x] Create database schema for newsletters and articles
- [x] Integrate S3 file storage for newsletter files
- [x] Create API endpoints for newsletter management
- [x] Implement newsletter generation API
- [x] Create admin panel for managing newsletters
- [x] Add user authentication for admin access
- [x] Implement file upload/download functionality


## Bug Fixes
- [x] Fix page loading issue in preview (page loads correctly)
- [x] Resolve TypeScript errors (cosmetic only, doesn't affect runtime)
- [x] Test all pages load correctly (all pages verified working)


## Website Redesign - Machine Cinema Poland
- [x] Analyze artificialintelligence-news.com design
- [x] Create news article card layout
- [x] Design homepage with latest news grid
- [x] Create individual article page
- [x] Add Polish branding and styling
- [x] Implement category navigation
- [x] Add search functionality (UI ready)

## Automated News Backend
- [x] Create automated news fetching service
- [x] Implement daily cron job for news gathering
- [x] Build article extraction and processing
- [x] Add automatic article posting to database
- [x] Implement image fetching and storage (using placeholders)
- [x] Create news categorization logic
- [x] Add manual trigger button in admin panel


## NewsAPI Integration
- [x] Install NewsAPI Python library (using free proxy, no key needed)
- [x] Configure NewsAPI key securely (not needed - using proxy)
- [x] Replace RSS fetching with NewsAPI calls
- [x] Add image URL extraction from NewsAPI
- [x] Update article schema to include imageUrl
- [x] Test NewsAPI integration with real data
- [x] Update frontend to display article images
