# NewsAPI Integration Guide

## Overview

Machine Cinema Poland now uses the **free NewsAPI proxy** at https://saurav.tech/NewsAPI/ to fetch real AI news articles with images. This service requires **no API key** and has **no rate limits**.

## How It Works

### 1. News Fetching (`scripts/fetch_newsapi.py`)

The Python script fetches news from multiple sources:
- **CNN** - Technology and general news
- **BBC News** - International coverage
- **Google News** - Aggregated news
- **Tech Headlines** - US technology category

### 2. AI Filtering

Articles are filtered using AI-related keywords:
- artificial intelligence, AI, machine learning, deep learning
- neural network, GPT, ChatGPT, OpenAI, generative AI
- LLM, large language model, computer vision, NLP
- natural language processing, automation, robotics

### 3. Automatic Categorization

Articles are categorized into 3 groups:

**🧠 GenerativeAI Creators** (cyan)
- Keywords: GPT, ChatGPT, Midjourney, DALL-E, Stable Diffusion, generative, OpenAI, Anthropic, Claude

**🚀 Marketing & Fun** (orange)
- Keywords: marketing, social media, advertising, campaign, viral, trend, entertainment

**💼 Biznes & Dev** (purple)
- Default category for business and development news

### 4. Image Extraction

Each article includes:
- `title` - Article headline
- `description` - Summary/excerpt
- `url` - Link to original article
- `source` - News source name
- `imageUrl` - Featured image URL (from NewsAPI)
- `publishedAt` - Publication timestamp
- `category` - Auto-assigned category

## Usage

### Manual Fetch (Admin Panel)

1. Log in as admin
2. Navigate to `/admin`
3. Click "Pobierz wiadomości teraz" (Fetch News Now)
4. Articles with images will be added to the database

### Automated Daily Fetch

Add to `server/_core/index.ts`:

```typescript
import { scheduleDailyNewsFetch } from '../newsService';

// After server starts
scheduleDailyNewsFetch();
```

Or use cron:
```bash
0 9 * * * cd /path/to/project && python3.11 scripts/fetch_newsapi.py
```

## Database Schema

The `articles` table includes:

```sql
CREATE TABLE articles (
  id INT AUTO_INCREMENT PRIMARY KEY,
  newsletter_id INT,
  title TEXT NOT NULL,
  summary TEXT,
  url TEXT NOT NULL,
  source VARCHAR(255),
  category VARCHAR(50),
  image_url TEXT,  -- ← New field for images
  published_at TIMESTAMP,
  createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Frontend Display

### Homepage (`client/src/pages/Home.tsx`)

Article cards now display:
- Real images from NewsAPI (with fallback gradient)
- Hover zoom effect on images
- Category badges
- Source attribution

```tsx
{article.imageUrl ? (
  <img
    src={article.imageUrl}
    alt={article.title}
    className="w-full h-full object-cover group-hover:scale-105 transition-transform"
  />
) : (
  <div className="bg-gradient-to-br from-gray-800 to-gray-600">
    <span className="text-white text-4xl font-bold opacity-20">AI</span>
  </div>
)}
```

### Article Page (`client/src/pages/Article.tsx`)

Full-size hero images for articles with `imageUrl`.

## Customization

### Change News Sources

Edit `scripts/fetch_newsapi.py`:

```python
# Available sources: 'cnn', 'bbc-news', 'fox-news', 'google-news'
sources = ['cnn', 'bbc-news', 'google-news', 'your-source']
```

### Adjust AI Keywords

```python
AI_KEYWORDS = [
    "your custom keyword",
    "another keyword",
    # ... add more
]
```

### Modify Categories

```python
def categorize_article(article):
    text = article.get('title', '').lower()
    
    if 'your keyword' in text:
        return 'your_category'
    
    return 'bizdev'  # default
```

## Advantages Over RSS

✅ **Real Images** - Every article includes a featured image  
✅ **No API Key** - Free proxy service, no registration  
✅ **No Rate Limits** - Unlimited requests  
✅ **Better Quality** - Curated content from major news sources  
✅ **Structured Data** - Consistent JSON format  
✅ **Duplicate Prevention** - URL-based deduplication in database

## Troubleshooting

### No articles fetched

Check if the NewsAPI proxy is accessible:
```bash
curl https://saurav.tech/NewsAPI/everything/cnn.json
```

### Images not displaying

- Check if `image_url` column exists in database
- Verify image URLs are not blocked by CORS
- Check browser console for image loading errors

### Python errors

Ensure Python 3.11+ is installed:
```bash
python3.11 --version
python3.11 scripts/fetch_newsapi.py
```

## API Endpoints

NewsAPI proxy provides:

- **Everything**: `https://saurav.tech/NewsAPI/everything/{source}.json`
- **Top Headlines**: `https://saurav.tech/NewsAPI/top-headlines/category/{category}/{country}.json`
- **Sources**: `https://saurav.tech/NewsAPI/sources.json`

## Credits

- NewsAPI Proxy: https://github.com/SauravKanchan/NewsAPI
- Original NewsAPI: https://newsapi.org

---

**Last Updated**: November 2025  
**Integration Status**: ✅ Fully Operational
