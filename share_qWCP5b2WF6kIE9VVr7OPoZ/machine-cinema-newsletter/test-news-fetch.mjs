/**
 * Test script to verify news fetching functionality
 */

import { fetchAndPostNews } from './server/newsService.ts';

console.log("Testing automated news fetch...\n");

try {
  const result = await fetchAndPostNews();
  
  console.log("\n=== Test Results ===");
  console.log(`Success: ${result.success}`);
  console.log(`Articles Added: ${result.articlesAdded}`);
  if (result.error) {
    console.log(`Error: ${result.error}`);
  }
  
  if (result.success) {
    console.log("\n✅ News fetching service is working correctly!");
  } else {
    console.log("\n❌ News fetching failed. Check the error above.");
  }
} catch (error) {
  console.error("\n❌ Test failed with error:", error);
  process.exit(1);
}
