import { eq, desc } from "drizzle-orm";
import { drizzle } from "drizzle-orm/mysql2";
import { InsertUser, users, newsletters, articles, seenUrls, Newsletter, Article, InsertNewsletter, InsertArticle, InsertSeenUrl } from "../drizzle/schema";
import { ENV } from './_core/env';

let _db: ReturnType<typeof drizzle> | null = null;

// Lazily create the drizzle instance so local tooling can run without a DB.
export async function getDb() {
  if (!_db && process.env.DATABASE_URL) {
    try {
      _db = drizzle(process.env.DATABASE_URL);
    } catch (error) {
      console.warn("[Database] Failed to connect:", error);
      _db = null;
    }
  }
  return _db;
}

export async function upsertUser(user: InsertUser): Promise<void> {
  if (!user.openId) {
    throw new Error("User openId is required for upsert");
  }

  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot upsert user: database not available");
    return;
  }

  try {
    const values: InsertUser = {
      openId: user.openId,
    };
    const updateSet: Record<string, unknown> = {};

    const textFields = ["name", "email", "loginMethod"] as const;
    type TextField = (typeof textFields)[number];

    const assignNullable = (field: TextField) => {
      const value = user[field];
      if (value === undefined) return;
      const normalized = value ?? null;
      values[field] = normalized;
      updateSet[field] = normalized;
    };

    textFields.forEach(assignNullable);

    if (user.lastSignedIn !== undefined) {
      values.lastSignedIn = user.lastSignedIn;
      updateSet.lastSignedIn = user.lastSignedIn;
    }
    if (user.role !== undefined) {
      values.role = user.role;
      updateSet.role = user.role;
    } else if (user.openId === ENV.ownerOpenId) {
      values.role = 'admin';
      updateSet.role = 'admin';
    }

    if (!values.lastSignedIn) {
      values.lastSignedIn = new Date();
    }

    if (Object.keys(updateSet).length === 0) {
      updateSet.lastSignedIn = new Date();
    }

    await db.insert(users).values(values).onDuplicateKeyUpdate({
      set: updateSet,
    });
  } catch (error) {
    console.error("[Database] Failed to upsert user:", error);
    throw error;
  }
}

export async function getUserByOpenId(openId: string) {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot get user: database not available");
    return undefined;
  }

  const result = await db.select().from(users).where(eq(users.openId, openId)).limit(1);

  return result.length > 0 ? result[0] : undefined;
}

// Newsletter functions
export async function createNewsletter(data: InsertNewsletter): Promise<Newsletter> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  const result = await db.insert(newsletters).values(data);
  const id = Number(result[0].insertId);
  
  const created = await db.select().from(newsletters).where(eq(newsletters.id, id)).limit(1);
  return created[0];
}

export async function getNewsletterByDate(date: string): Promise<Newsletter | undefined> {
  const db = await getDb();
  if (!db) return undefined;
  
  const result = await db.select().from(newsletters).where(eq(newsletters.date, date)).limit(1);
  return result[0];
}

export async function getAllNewsletters(): Promise<Newsletter[]> {
  const db = await getDb();
  if (!db) return [];
  
  return db.select().from(newsletters).orderBy(desc(newsletters.date));
}

export async function updateNewsletter(id: number, data: Partial<InsertNewsletter>): Promise<void> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  await db.update(newsletters).set(data).where(eq(newsletters.id, id));
}

// Article functions
export async function createArticle(data: InsertArticle): Promise<Article> {
  const db = await getDb();
  if (!db) throw new Error("Database not available");
  
  const result = await db.insert(articles).values(data);
  const id = Number(result[0].insertId);
  
  const created = await db.select().from(articles).where(eq(articles.id, id)).limit(1);
  return created[0];
}

export async function getArticlesByNewsletterId(newsletterId: number): Promise<Article[]> {
  const db = await getDb();
  if (!db) return [];
  
  return db.select().from(articles).where(eq(articles.newsletterId, newsletterId));
}

export async function getLatestArticles(limit: number = 12): Promise<Article[]> {
  const db = await getDb();
  if (!db) return [];
  
  return db.select().from(articles).orderBy(desc(articles.publishedAt)).limit(limit);
}

export async function getArticleById(id: number): Promise<Article | null> {
  const db = await getDb();
  if (!db) return null;
  
  const result = await db.select().from(articles).where(eq(articles.id, id)).limit(1);
  return result[0] || null;
}

// Seen URLs functions
export async function isUrlSeen(url: string): Promise<boolean> {
  const db = await getDb();
  if (!db) return false;
  
  const result = await db.select().from(seenUrls).where(eq(seenUrls.url, url)).limit(1);
  return result.length > 0;
}

export async function markUrlAsSeen(url: string): Promise<void> {
  const db = await getDb();
  if (!db) return;
  
  const existing = await db.select().from(seenUrls).where(eq(seenUrls.url, url)).limit(1);
  
  if (existing.length > 0) {
    await db.update(seenUrls).set({ lastSeen: new Date() }).where(eq(seenUrls.url, url));
  } else {
    await db.insert(seenUrls).values({ url });
  }
}

export async function getSeenUrls(): Promise<string[]> {
  const db = await getDb();
  if (!db) return [];
  
  const results = await db.select({ url: seenUrls.url }).from(seenUrls);
  return results.map(r => r.url);
}
