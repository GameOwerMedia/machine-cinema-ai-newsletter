/**
 * Update the curated news dataset consumed by the static front-end.
 *
 * Optional dependencies:
 *   npm install
 * Compile:
 *   npm run build
 * Execute:
 *   node dist/updateNews.js
 */

import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import type { AiSignal, ProviderType } from "./fetchAiSignals.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, "..");
const DATA_DIR = path.join(PROJECT_ROOT, "data");
const RAW_SIGNALS_PATH = path.join(DATA_DIR, "ai_signals.json");
const NEWS_PATH = path.join(DATA_DIR, "news.json");
const PUBLISHED_NEWS_PATH = path.join(PROJECT_ROOT, "docs", "data", "news.json");

const MAX_NEWS_ITEMS = 75;

interface FrontendNewsItem {
  id: string;
  title: string;
  summary?: string;
  provider: string;
  source: string;
  sourceUrl?: string;
  url: string;
  language?: string;
  tags: string[];
  publishedAt: string;
}

type FetchAiSignalsFn = () => Promise<void>;

type ProviderMetadata = {
  type: ProviderType;
};

let fetchAiSignalsFn: FetchAiSignalsFn | undefined;
const providerMetadata = new Map<string, ProviderMetadata>();

async function loadFetchAiSignalsModule(): Promise<void> {
  try {
    const module = await import("./fetchAiSignals.js");
    const maybeModule = module as {
      main?: FetchAiSignalsFn;
      fetchAiSignals?: FetchAiSignalsFn;
      PROVIDERS?: Array<{ slug?: string; type?: ProviderType }>;
    };
    if (typeof maybeModule.main === "function") {
      fetchAiSignalsFn = maybeModule.main.bind(module);
    }
    if (typeof maybeModule.fetchAiSignals === "function") {
      fetchAiSignalsFn = maybeModule.fetchAiSignals.bind(module);
    }
    if (Array.isArray(maybeModule.PROVIDERS)) {
      for (const provider of maybeModule.PROVIDERS) {
        if (provider?.slug && provider?.type) {
          providerMetadata.set(provider.slug, { type: provider.type });
        }
      }
    }
  } catch (error) {
    const err = error as NodeJS.ErrnoException;
    if (err?.code === "ERR_MODULE_NOT_FOUND" || /Cannot find module/.test(String(err?.message ?? ""))) {
      console.warn("fetchAiSignals module not found. Continuing without refreshing raw signals.");
      return;
    }
    console.warn("Unable to load fetchAiSignals module:", error);
  }
}

async function maybeRefreshSignals(): Promise<void> {
  if (!fetchAiSignalsFn) {
    return;
  }
  try {
    await fetchAiSignalsFn();
  } catch (error) {
    console.warn("Failed to refresh AI signals via fetchAiSignals:", error);
  }
}

async function ensureDataDirectories(): Promise<void> {
  await fs.mkdir(DATA_DIR, { recursive: true });
  await fs.mkdir(path.dirname(PUBLISHED_NEWS_PATH), { recursive: true });
}

async function loadRawSignals(): Promise<AiSignal[]> {
  try {
    const raw = await fs.readFile(RAW_SIGNALS_PATH, "utf8");
    const parsed = JSON.parse(raw) as unknown;
    if (Array.isArray(parsed)) {
      return parsed.filter((item): item is AiSignal => typeof item === "object" && item !== null && "id" in item);
    }
  } catch (error) {
    const err = error as NodeJS.ErrnoException;
    if (err?.code !== "ENOENT") {
      console.warn("Unable to load ai_signals.json:", error);
    } else {
      console.warn("ai_signals.json not found. Run fetchAiSignals to populate it.");
    }
  }
  return [];
}

function convertLegacyNewsItem(raw: unknown): FrontendNewsItem | null {
  if (!raw || typeof raw !== "object") {
    return null;
  }
  const record = raw as Record<string, unknown>;
  const id = normaliseText(typeof record.id === "string" ? record.id : "");
  const url = normaliseText(typeof record.url === "string" ? record.url : "");
  const publishedRaw = typeof record.publishedAt === "string" ? record.publishedAt : undefined;
  const publishedAt = publishedRaw && !Number.isNaN(Date.parse(publishedRaw)) ? new Date(publishedRaw).toISOString() : undefined;
  if (!id || !url || !publishedAt) {
    return null;
  }
  const title = normaliseText(
    typeof record.title === "string"
      ? record.title
      : typeof record.title_en === "string"
        ? record.title_en
        : typeof record.titleEn === "string"
          ? record.titleEn
          : "",
  );
  const summary = normaliseText(
    typeof record.summary === "string"
      ? record.summary
      : typeof record.summary_en === "string"
        ? record.summary_en
        : typeof record.summaryEn === "string"
          ? record.summaryEn
          : "",
  );
  let provider = normaliseText(typeof record.provider === "string" ? record.provider : "");
  if (!provider) {
    provider = normaliseText(typeof record.source === "string" ? record.source : "");
  }
  if (!provider && typeof record.sourceUrl === "string") {
    try {
      const hostname = new URL(record.sourceUrl).hostname.replace(/^www\./, "");
      provider = normaliseText(hostname);
    } catch {
      provider = "";
    }
  }
  const sourceUrl = typeof record.sourceUrl === "string" ? normaliseText(record.sourceUrl) : undefined;
  const language = typeof record.language === "string" ? record.language : undefined;
  const tags = Array.isArray(record.tags)
    ? Array.from(
        new Set(
          record.tags
            .map((tag) => (typeof tag === "string" ? normaliseText(tag) : ""))
            .filter((tag): tag is string => Boolean(tag)),
        ),
      )
    : [];
  const safeTitle = title || normaliseText(typeof record.title_en === "string" ? record.title_en : "") || "Untitled";
  const safeProvider = provider || "AI News";
  return {
    id,
    title: safeTitle,
    summary: summary || undefined,
    provider: safeProvider,
    source: safeProvider,
    sourceUrl,
    url,
    language,
    tags,
    publishedAt,
  };
}

async function loadExistingNews(): Promise<FrontendNewsItem[]> {
  const candidatePaths = [NEWS_PATH, PUBLISHED_NEWS_PATH];
  for (const candidate of candidatePaths) {
    try {
      const raw = await fs.readFile(candidate, "utf8");
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length) {
        const normalised = parsed
          .map((item) => (typeof item === "object" && item !== null && "provider" in item ? (item as FrontendNewsItem) : convertLegacyNewsItem(item)))
          .filter((item): item is FrontendNewsItem => item !== null);
        if (normalised.length) {
          return normalised;
        }
      }
    } catch (error) {
      const err = error as NodeJS.ErrnoException;
      if (err?.code !== "ENOENT") {
        console.warn(`Unable to read existing news from ${candidate}:`, error);
      }
    }
  }
  return [];
}

const AD_TEXT_KEYWORDS = [
  "sale",
  "discount",
  "limited offer",
  "limited-time",
  "limited time",
  "save %",
  "% off",
  "black friday",
  "cyber monday",
  "register now",
  "sign up now",
  "book your demo",
  "sponsored",
  "partner content",
  "ad:",
  "advertorial",
  "pricing",
  "plans & pricing",
  "upgrade now",
  "webinar",
  "join our webinar",
  "conference tickets",
  "early bird",
  "ebook",
  "download our",
  "watch the webinar",
  "reserve your seat",
  "get your ticket",
];

const AD_URL_KEYWORDS = [
  "/ads/",
  "/promo",
  "/promotions",
  "/sale",
  "/pricing",
  "/plans",
  "/webinar",
  "/events",
  "/sponsored",
];

const AGGREGATOR_LISTICLE_PATTERNS = [
  /top\s+\d+\s+(?:ai\s+)?tools/i,
  /best\s+(?:ai\s+)?tools/i,
  /must[-\s]+try\s+ai/i,
  /ultimate\s+guide\s+to\s+ai/i,
  /ai\s+tool\s+roundup/i,
];

const RELEVANT_CORE_KEYWORDS = [
  "model",
  "models",
  "multimodal",
  "text-to-video",
  "text-to-image",
  "vision",
  "ai agent",
  "agents",
  "assistant",
  "gpt",
  "llm",
  "large language",
  "diffusion",
  "gen-",
  "neural",
];

const RELEVANT_ACTION_KEYWORDS = [
  "release",
  "launch",
  "introducing",
  "now available",
  "available today",
  "update",
  "updated",
  "announces",
  "announced",
  "rolling out",
  "beta",
  "preview",
  "api",
  "sdk",
  "integration",
  "partnership",
  "collaboration",
  "ships",
  "support",
];

const AI_TAG_HINTS = [
  "ai",
  "ml",
  "llm",
  "openai",
  "anthropic",
  "gemini",
  "deepmind",
  "grok",
  "claude",
  "sora",
  "midjourney",
  "stability",
  "runway",
  "perplexity",
  "llama",
  "mistral",
  "watson",
  "copilot",
  "diffusion",
  "gen3",
  "aip",
];

function normaliseText(input?: string): string {
  return (input ?? "").normalize("NFKC").replace(/\s+/g, " ").trim();
}

function isAggregator(providerSlug: string): boolean {
  const metadata = providerMetadata.get(providerSlug);
  return metadata?.type === "aggregator";
}

function isProbablyAdLike(signal: AiSignal): boolean {
  const combinedText = `${normaliseText(signal.title)} ${normaliseText(signal.summary)}`.toLowerCase();
  if (combinedText) {
    for (const keyword of AD_TEXT_KEYWORDS) {
      if (combinedText.includes(keyword)) {
        return true;
      }
    }
  }

  const url = (signal.url || "").toLowerCase();
  if (url) {
    for (const keyword of AD_URL_KEYWORDS) {
      if (url.includes(keyword)) {
        return true;
      }
    }
  }

  const tagMatchesMarketing = (signal.tags ?? []).some((tag) => tag.toLowerCase().includes("marketing"));
  if (tagMatchesMarketing) {
    return true;
  }

  if (isAggregator(signal.providerSlug)) {
    for (const pattern of AGGREGATOR_LISTICLE_PATTERNS) {
      if (pattern.test(signal.title ?? "") || pattern.test(signal.summary ?? "")) {
        return true;
      }
    }
  }

  return false;
}

function isRelevantAiNews(signal: AiSignal): boolean {
  const combinedText = `${normaliseText(signal.title)} ${normaliseText(signal.summary)}`.toLowerCase();
  const hasCoreKeyword = RELEVANT_CORE_KEYWORDS.some((keyword) => combinedText.includes(keyword));
  if (!hasCoreKeyword) {
    return false;
  }

  const hasActionKeyword = RELEVANT_ACTION_KEYWORDS.some((keyword) => combinedText.includes(keyword));
  const slug = (signal.providerSlug ?? "").toLowerCase();
  const tagSet = new Set((signal.tags ?? []).map((tag) => tag.toLowerCase()));
  const hasAiHint = AI_TAG_HINTS.some((hint) => slug.includes(hint) || tagSet.has(hint) || Array.from(tagSet).some((tag) => tag.includes(hint)));

  return hasActionKeyword || hasAiHint;
}

function resolvePublishedAt(signal: AiSignal): string | undefined {
  const candidates = [signal.publishedAt, signal.collectedAt];
  for (const candidate of candidates) {
    if (!candidate) {
      continue;
    }
    const timestamp = Date.parse(candidate);
    if (!Number.isNaN(timestamp)) {
      return new Date(timestamp).toISOString();
    }
  }
  return undefined;
}

function sortSignalsDescending(signals: AiSignal[]): AiSignal[] {
  return [...signals].sort((a, b) => {
    const aTime = Date.parse(resolvePublishedAt(a) ?? "") || 0;
    const bTime = Date.parse(resolvePublishedAt(b) ?? "") || 0;
    return bTime - aTime;
  });
}

function dedupeSignals(signals: AiSignal[]): AiSignal[] {
  const seen = new Set<string>();
  const deduped: AiSignal[] = [];
  for (const signal of signals) {
    const key = `${signal.providerSlug}::${signal.url}`;
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    deduped.push(signal);
  }
  return deduped;
}

function toFrontendNewsItem(signal: AiSignal): FrontendNewsItem | null {
  const publishedAt = resolvePublishedAt(signal);
  if (!publishedAt) {
    return null;
  }

  const tags = Array.from(new Set((signal.tags ?? []).map((tag) => normaliseText(tag)).filter(Boolean)));

  return {
    id: signal.id,
    title: normaliseText(signal.title),
    summary: normaliseText(signal.summary) || undefined,
    provider: normaliseText(signal.providerName) || signal.providerSlug,
    source: normaliseText(signal.providerName) || signal.providerSlug,
    sourceUrl: signal.url,
    url: signal.url,
    language: signal.language,
    tags,
    publishedAt,
  };
}

async function writeNews(items: FrontendNewsItem[]): Promise<void> {
  await ensureDataDirectories();
  const serialised = `${JSON.stringify(items, null, 2)}\n`;
  await fs.writeFile(NEWS_PATH, serialised, "utf8");
  await fs.writeFile(PUBLISHED_NEWS_PATH, serialised, "utf8");
}

async function main(): Promise<void> {
  await loadFetchAiSignalsModule();
  await maybeRefreshSignals();

  const existingNews = await loadExistingNews();
  const rawSignals = await loadRawSignals();
  if (!rawSignals.length) {
    console.warn("No raw AI signals available. Writing an empty news dataset.");
  }

  const cleaned = rawSignals
    .filter((signal) => !isProbablyAdLike(signal))
    .filter((signal) => isRelevantAiNews(signal));

  const sorted = sortSignalsDescending(dedupeSignals(cleaned));
  const limited = sorted.slice(0, MAX_NEWS_ITEMS);

  const frontendItems = limited
    .map((signal) => toFrontendNewsItem(signal))
    .filter((item): item is FrontendNewsItem => item !== null);

  const nextItems = frontendItems.length ? frontendItems : existingNews;
  if (!frontendItems.length && existingNews.length) {
    console.warn(`No curated items produced. Keeping existing dataset with ${existingNews.length} entries.`);
  }

  await writeNews(nextItems);

  console.log(`Wrote ${nextItems.length} curated news items to ${path.relative(PROJECT_ROOT, NEWS_PATH)}`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error("updateNews failed:", error);
    process.exit(1);
  });
}

export type { FrontendNewsItem };
export { isProbablyAdLike, isRelevantAiNews, main };
