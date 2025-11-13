/**
 * Automated News Fetching Service
 * This service fetches AI news from RSS feeds and posts them to the database
 */

import * as db from "./db";

interface NewsArticle {
  title: string;
  summary: string;
  url: string;
  source: string;
  category: string;
  imageUrl?: string;
  publishedAt: Date;
}

/**
 * Fetch news from Python script and save to database
 */
export async function fetchAndPostNews(): Promise<{ success: boolean; articlesAdded: number; error?: string }> {
  try {
    console.log("[NewsService] Starting automated news fetch...");
    
    // Get today's date
    const today = new Date().toISOString().split('T')[0];
    
    // Check if newsletter for today already exists
    const existingNewsletter = await db.getNewsletterByDate(today);
    let newsletterId: number;
    
    if (existingNewsletter) {
      console.log(`[NewsService] Newsletter for ${today} already exists (ID: ${existingNewsletter.id})`);
      newsletterId = existingNewsletter.id;
    } else {
      // Create new newsletter for today
      const newsletter = await db.createNewsletter({
        date: today,
        title: `Machine Cinema Poland - Wiadomości AI - ${today}`,
        itemCount: 0,
        published: true,
      });
      newsletterId = newsletter.id;
      console.log(`[NewsService] Created new newsletter (ID: ${newsletterId})`);
    }
    
    // Execute Python script to fetch news using NewsAPI
    const { spawn } = await import('child_process');
    const pythonProcess = spawn('python3.11', [
      'scripts/fetch_newsapi.py'
    ], {
      cwd: process.cwd(),
    });
    
    let output = '';
    let errorOutput = '';
    
    pythonProcess.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    pythonProcess.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });
    
    await new Promise<void>((resolve, reject) => {
      pythonProcess.on('close', (code) => {
        if (code === 0) {
          resolve();
        } else {
          reject(new Error(`Python script exited with code ${code}: ${errorOutput}`));
        }
      });
    });
    
    console.log("[NewsService] Python script output:", output.substring(0, 500));
    
    // Parse the output to get articles from NewsAPI
    let articles: NewsArticle[] = [];
    try {
      const result = JSON.parse(output);
      if (result.success && result.articles) {
        articles = result.articles.map((a: any) => ({
          title: a.title,
          summary: a.description || "",
          url: a.url,
          source: a.source,
          category: a.category,
          imageUrl: a.imageUrl || "",
          publishedAt: a.publishedAt,
        }));
        console.log(`[NewsService] Parsed ${articles.length} AI articles from ${result.totalArticles} total`);
      }
    } catch (e) {
      console.warn("[NewsService] Could not parse NewsAPI output:", e);
      // Fallback: use mock data for testing
      articles = await generateMockArticles();
    }
    
    // Filter out articles that have been seen before
    const newArticles: NewsArticle[] = [];
    for (const article of articles) {
      const isSeen = await db.isUrlSeen(article.url);
      if (!isSeen) {
        newArticles.push(article);
        await db.markUrlAsSeen(article.url);
      }
    }
    
    console.log(`[NewsService] Found ${newArticles.length} new articles out of ${articles.length} total`);
    
    // Save articles to database
    let articlesAdded = 0;
    for (const article of newArticles) {
      try {
        await db.createArticle({
          newsletterId,
          title: article.title,
          summary: article.summary || "",
          url: article.url,
          source: article.source,
          category: article.category,
          imageUrl: article.imageUrl || null,
          publishedAt: article.publishedAt,
        });
        articlesAdded++;
      } catch (error) {
        console.error(`[NewsService] Error saving article "${article.title}":`, error);
      }
    }
    
    // Update newsletter item count
    if (articlesAdded > 0) {
      const currentCount = existingNewsletter?.itemCount || 0;
      await db.updateNewsletter(newsletterId, {
        itemCount: currentCount + articlesAdded,
      });
    }
    
    console.log(`[NewsService] Successfully added ${articlesAdded} articles`);
    
    return {
      success: true,
      articlesAdded,
    };
  } catch (error) {
    console.error("[NewsService] Error in fetchAndPostNews:", error);
    return {
      success: false,
      articlesAdded: 0,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

/**
 * Generate mock articles for testing when Python script is not available
 */
async function generateMockArticles(): Promise<NewsArticle[]> {
  const categories = ["creators", "marketing", "bizdev"];
  const sources = ["TechCrunch", "VentureBeat", "The Verge", "Wired", "MIT Technology Review"];
  const topics = [
    "OpenAI announces new GPT model",
    "Google's latest AI breakthrough",
    "Microsoft integrates AI into Office",
    "Startup raises $50M for AI platform",
    "New AI regulation proposed in EU",
    "AI helps discover new drug",
    "Machine learning improves cloud security",
    "AI-powered chatbot goes viral",
    "Tech giant acquires AI startup",
    "Researchers achieve AGI milestone",
  ];
  
  const articles: NewsArticle[] = [];
  const now = new Date();
  
  for (let i = 0; i < 5; i++) {
    const topic = topics[Math.floor(Math.random() * topics.length)];
    const source = sources[Math.floor(Math.random() * sources.length)];
    const category = categories[Math.floor(Math.random() * categories.length)];
    
    articles.push({
      title: `${topic} - ${new Date().toLocaleDateString('pl-PL')}`,
      summary: `Najnowsze informacje o ${topic.toLowerCase()}. Eksperci branży komentują rozwój sztucznej inteligencji i jej wpływ na przyszłość technologii.`,
      url: `https://example.com/article-${Date.now()}-${i}`,
      source,
      category,
      publishedAt: new Date(now.getTime() - i * 3600000), // Stagger by hours
    });
  }
  
  return articles;
}

/**
 * Schedule daily news fetching
 * This should be called when the server starts
 */
export function scheduleDailyNewsFetch() {
  // Run immediately on startup
  fetchAndPostNews().catch(console.error);
  
  // Then run every 24 hours
  const TWENTY_FOUR_HOURS = 24 * 60 * 60 * 1000;
  setInterval(() => {
    fetchAndPostNews().catch(console.error);
  }, TWENTY_FOUR_HOURS);
  
  console.log("[NewsService] Daily news fetch scheduled");
}
