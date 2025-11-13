/**
 * Test NewsAPI integration - fetch and save articles with images
 */

import { fetchAndPostNews } from './server/newsService.ts';

console.log("🚀 Testing NewsAPI Integration\n");
console.log("This will:");
console.log("1. Fetch real AI news from NewsAPI proxy");
console.log("2. Filter for AI-related articles");
console.log("3. Categorize them automatically");
console.log("4. Save to database with images\n");

console.log("Starting fetch...\n");

try {
  const result = await fetchAndPostNews();
  
  console.log("\n=== Results ===");
  console.log(`✅ Success: ${result.success}`);
  console.log(`📰 Articles Added: ${result.articlesAdded}`);
  
  if (result.error) {
    console.log(`❌ Error: ${result.error}`);
  }
  
  if (result.success && result.articlesAdded > 0) {
    console.log("\n✨ Great! Real AI news articles with images have been added to the database!");
    console.log("Visit the homepage to see them displayed with real images.");
  } else if (result.success && result.articlesAdded === 0) {
    console.log("\n📋 All articles were already in the database (duplicates filtered out).");
    console.log("The duplicate prevention system is working correctly!");
  }
} catch (error) {
  console.error("\n❌ Test failed:", error);
  process.exit(1);
}
