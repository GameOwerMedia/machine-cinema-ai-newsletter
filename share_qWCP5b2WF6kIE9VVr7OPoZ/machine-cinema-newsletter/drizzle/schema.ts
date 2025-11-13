import { int, mysqlEnum, mysqlTable, text, timestamp, varchar, boolean } from "drizzle-orm/mysql-core";

/**
 * Core user table backing auth flow.
 * Extend this file with additional tables as your product grows.
 * Columns use camelCase to match both database fields and generated types.
 */
export const users = mysqlTable("users", {
  /**
   * Surrogate primary key. Auto-incremented numeric value managed by the database.
   * Use this for relations between tables.
   */
  id: int("id").autoincrement().primaryKey(),
  /** Manus OAuth identifier (openId) returned from the OAuth callback. Unique per user. */
  openId: varchar("openId", { length: 64 }).notNull().unique(),
  name: text("name"),
  email: varchar("email", { length: 320 }),
  loginMethod: varchar("loginMethod", { length: 64 }),
  role: mysqlEnum("role", ["user", "admin"]).default("user").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  lastSignedIn: timestamp("lastSignedIn").defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

/**
 * Newsletters table - stores generated newsletters
 */
export const newsletters = mysqlTable("newsletters", {
  id: int("id").autoincrement().primaryKey(),
  date: varchar("date", { length: 10 }).notNull().unique(), // YYYY-MM-DD format
  title: text("title").notNull(),
  htmlFileKey: text("html_file_key"), // S3 key for HTML file
  htmlFileUrl: text("html_file_url"), // S3 URL for HTML file
  mdFileKey: text("md_file_key"), // S3 key for Markdown file
  mdFileUrl: text("md_file_url"), // S3 URL for Markdown file
  itemCount: int("item_count").default(0).notNull(),
  published: boolean("published").default(true).notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
});

export type Newsletter = typeof newsletters.$inferSelect;
export type InsertNewsletter = typeof newsletters.$inferInsert;

/**
 * News articles table - stores individual news items
 */
export const articles = mysqlTable("articles", {
  id: int("id").autoincrement().primaryKey(),
  newsletterId: int("newsletter_id").references(() => newsletters.id),
  title: text("title").notNull(),
  summary: text("summary"),
  url: text("url").notNull(),
  source: varchar("source", { length: 255 }),
  category: varchar("category", { length: 50 }), // creators, marketing, bizdev
  imageUrl: text("image_url"), // Article image URL from NewsAPI
  publishedAt: timestamp("published_at"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
});

export type Article = typeof articles.$inferSelect;
export type InsertArticle = typeof articles.$inferInsert;

/**
 * Seen URLs cache - tracks already used articles
 */
export const seenUrls = mysqlTable("seen_urls", {
  id: int("id").autoincrement().primaryKey(),
  url: text("url").notNull(),
  firstSeen: timestamp("first_seen").defaultNow().notNull(),
  lastSeen: timestamp("last_seen").defaultNow().notNull(),
});

export type SeenUrl = typeof seenUrls.$inferSelect;
export type InsertSeenUrl = typeof seenUrls.$inferInsert;