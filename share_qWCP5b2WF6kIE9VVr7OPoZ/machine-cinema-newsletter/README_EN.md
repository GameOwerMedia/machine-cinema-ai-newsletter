# Machine Cinema Poland - Polish AI News Portal

Automated AI news aggregation website inspired by [artificialintelligence-news.com](https://www.artificialintelligence-news.com/), featuring daily news gathering from RSS feeds and a modern news portal interface.

## 🌟 Features

### Frontend
- **Modern News Portal Design**: Professional card-based layout inspired by AI News
- **Polish Language**: Full Polish localization throughout the interface
- **Responsive Design**: Mobile-first design that works on all devices
- **Article Cards**: Featured images, category badges, dates, and summaries
- **Individual Article Pages**: Dedicated pages for each news article
- **Newsletter Archive**: Historical newsletter browsing
- **Search Interface**: Search bar for finding specific articles
- **Dark Header & Footer**: Professional black header with cyan accents

### Backend
- **Automated News Fetching**: Daily RSS feed monitoring for AI news
- **Duplicate Prevention**: URL-based deduplication system
- **Category Classification**: Automatic categorization into 3 groups:
  - 🧠 GenerativeAI Creators (cyan)
  - 🚀 Marketing & Fun (orange)
  - 💼 Biznes & Dev (purple)
- **Database Storage**: MySQL/TiDB for articles, newsletters, and seen URLs
- **S3 File Storage**: Newsletter file storage with presigned URLs
- **Admin Panel**: Manual news fetch trigger and newsletter management
- **User Authentication**: Admin-only access to management features

## 🚀 Quick Start

### Prerequisites
- Node.js 22+ with pnpm
- Python 3.11+ with pip
- MySQL/TiDB database (automatically configured)

### Installation

1. **Install Node dependencies**:
```bash
pnpm install
```

2. **Set up Python virtual environment**:
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Configure RSS feeds** (edit `config.yaml`):
```yaml
rss_feeds:
  creators:
    - https://news.google.com/rss/search?q=generative+AI+when:1d&hl=pl&gl=PL&ceid=PL:pl
  marketing:
    - https://news.google.com/rss/search?q=AI+marketing+when:1d&hl=pl&gl=PL&ceid=PL:pl
  bizdev:
    - https://news.google.com/rss/search?q=AI+business+when:1d&hl=pl&gl=PL&ceid=PL:pl
```

4. **Start the development server**:
```bash
pnpm dev
```

5. **Access the site**:
   - Frontend: http://localhost:3000
   - Admin Panel: http://localhost:3000/admin

## 📖 Usage

### Manual News Fetching

1. Navigate to the Admin Panel (`/admin`)
2. Click "Pobierz wiadomości teraz" (Fetch News Now)
3. The system will:
   - Fetch articles from configured RSS feeds
   - Filter out duplicates
   - Categorize articles automatically
   - Save to database
   - Display on homepage

### Automated Daily Fetching

Add to your server startup code (`server/_core/index.ts`):

```typescript
import { scheduleDailyNewsFetch } from '../newsService';

// After server starts
scheduleDailyNewsFetch();
```

Or use cron:
```bash
# Runs at 9 AM daily
0 9 * * * cd /path/to/project && pnpm tsx -e "import('./server/newsService.ts').then(m => m.fetchAndPostNews())"
```

### Customizing Categories

Edit `config.yaml`:

```yaml
categories:
  creators:
    keywords:
      - "GPT"
      - "ChatGPT"
      - "Midjourney"
    rss_feeds:
      - "https://your-feed.com/rss"
```

## 🎨 Design Customization

### Category Colors

Edit `client/src/pages/Home.tsx`:

```typescript
const categoryColors: Record<string, string> = {
  creators: "bg-cyan-500",
  marketing: "bg-orange-500",
  bizdev: "bg-purple-500",
};
```

### Logo

1. Update `client/src/const.ts`
2. For favicon: Management UI → Settings → General

## 🗄️ Database Schema

- **newsletters**: Daily newsletter metadata
- **articles**: Individual news articles with category, source, URL
- **seen_urls**: Duplicate prevention tracking
- **users**: User authentication and roles

## 🔧 Configuration

| File | Purpose |
|------|---------|
| `config.yaml` | RSS feeds and categories |
| `requirements.txt` | Python dependencies |
| `drizzle/schema.ts` | Database schema |

## 📝 Python Scripts

- **fetch_ai_news.py**: RSS feed fetching
- **filters.py**: Content filtering
- **make_posts.py**: Article formatting
- **generate_all.py**: Main generator
- **utils.py**: Utilities

## 🚀 Deployment

1. Create checkpoint via admin panel
2. Click "Publish" in Management UI
3. Site goes live at `https://your-domain.manus.space`
4. Optional: Add custom domain in Settings → Domains

## 🛠️ Troubleshooting

### Python script fails
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### No articles
1. Check RSS feeds in `config.yaml`
2. Verify Python dependencies
3. Check admin panel for errors

## 📚 Tech Stack

- **Frontend**: React 19, Tailwind 4, shadcn/ui
- **Backend**: Node.js, tRPC, Express
- **Database**: MySQL/TiDB (Drizzle ORM)
- **Storage**: S3
- **Python**: feedparser, PyYAML

## 🤝 Credits

Based on [MachineCinemaPLNews](https://github.com/GameOwerMedia/MachineCinemaPLNews)

---

**Need Help?** Visit https://help.manus.im
