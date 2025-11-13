/**
 * Install dependencies:
 *   npm install node-fetch rss-parser cheerio dotenv
 * Compile the TypeScript source:
 *   npx tsc
 * Run the compiled script:
 *   node dist/fetchAiSignals.js
 */

import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import crypto from "node:crypto";
import fetch, { RequestInit, Response } from "node-fetch";
import Parser from "rss-parser";
import cheerio from "cheerio";
import dotenv from "dotenv";

export type ProviderType = "company" | "model" | "aggregator";

export interface AiProvider {
  slug: string;
  type: ProviderType;
  companyName: string;
  models?: string[];
  homepage: string;
  rssFeeds?: string[];
  newsPages?: string[];
  xHandles?: string[];
  hashtags?: string[];
}

export type SignalSource = "website" | "rss" | "x";

export interface AiSignal {
  id: string;
  providerSlug: string;
  providerName: string;
  source: SignalSource;
  origin: string;
  title: string;
  summary?: string;
  url: string;
  language?: string;
  tags: string[];
  publishedAt: string;
  collectedAt: string;
}

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const PROJECT_ROOT = path.resolve(__dirname, "..");
const DATA_PATH = path.join(PROJECT_ROOT, "data", "ai_signals.json");

const REQUEST_DELAY_MS = 1000;
const RSS_ITEM_LIMIT = 10;
const MAX_SIGNALS = 800;

const rssParser = new Parser();
const lastRequestPerHost = new Map<string, number>();

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

function slugifyTag(value: string): string {
  return value
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .replace(/-{2,}/g, "-");
}

function createSignalId(providerSlug: string, source: SignalSource, uniqueKey: string): string {
  const hash = crypto.createHash("sha256").update(uniqueKey).digest("hex").slice(0, 12);
  return `${providerSlug}-${source}-${hash}`;
}

function normaliseUrl(baseUrl: string, maybeRelative: string): string {
  try {
    return new URL(maybeRelative, baseUrl).toString();
  } catch (error) {
    console.warn(`Unable to normalise URL '${maybeRelative}' for base '${baseUrl}':`, error);
    return maybeRelative;
  }
}

function parseDate(value?: string | null): string | undefined {
  if (!value) {
    return undefined;
  }
  const trimmed = value.trim();
  if (!trimmed) {
    return undefined;
  }
  const timestamp = Date.parse(trimmed);
  if (!Number.isNaN(timestamp)) {
    return new Date(timestamp).toISOString();
  }
  return undefined;
}

async function fetchWithDelay(url: string, init?: RequestInit): Promise<Response> {
  const host = new URL(url).host;
  const lastRequestAt = lastRequestPerHost.get(host) ?? 0;
  const elapsed = Date.now() - lastRequestAt;
  if (elapsed < REQUEST_DELAY_MS) {
    await wait(REQUEST_DELAY_MS - elapsed);
  }
  const response = await fetch(url, init);
  lastRequestPerHost.set(host, Date.now());
  return response;
}

function buildBaseTags(provider: AiProvider): string[] {
  const tags = new Set<string>();
  tags.add(provider.slug);
  for (const model of provider.models ?? []) {
    const slug = slugifyTag(model);
    if (slug) {
      tags.add(slug);
    }
  }
  for (const hash of provider.hashtags ?? []) {
    const tag = slugifyTag(hash.replace(/^#/, ""));
    if (tag) {
      tags.add(tag);
    }
  }
  return Array.from(tags);
}

async function fetchRssSignals(provider: AiProvider): Promise<AiSignal[]> {
  const signals: AiSignal[] = [];
  const collectedAt = new Date().toISOString();
  if (!provider.rssFeeds?.length) {
    return signals;
  }
  for (const feedUrl of provider.rssFeeds) {
    try {
      const response = await fetchWithDelay(feedUrl);
      if (!response.ok) {
        console.warn(`RSS request failed for ${feedUrl}: ${response.status} ${response.statusText}`);
        continue;
      }
      const xml = await response.text();
      const feed = await rssParser.parseString(xml);
      const items = feed.items?.slice(0, RSS_ITEM_LIMIT) ?? [];
      for (const item of items) {
        if (!item.link || !item.title) {
          continue;
        }
        const publishedAt = item.isoDate ?? item.pubDate ?? collectedAt;
        const tags = buildBaseTags(provider);
        const signal: AiSignal = {
          id: createSignalId(provider.slug, "rss", item.link),
          providerSlug: provider.slug,
          providerName: provider.companyName,
          source: "rss",
          origin: `${provider.slug}-rss`,
          title: item.title.trim(),
          summary: item.contentSnippet?.trim() ?? item.content?.trim(),
          url: item.link,
          language: (item as Record<string, string | undefined>).language,
          tags,
          publishedAt: new Date(publishedAt).toISOString(),
          collectedAt,
        };
        signals.push(signal);
      }
    } catch (error) {
      console.warn(`Failed to parse RSS for ${feedUrl}:`, error);
    }
  }
  return signals;
}

function deriveOriginFromUrl(provider: AiProvider, pageUrl: string): string {
  const url = new URL(pageUrl);
  const normalisedPath = url.pathname.replace(/\/+/g, "/");
  const pathSlug = slugifyTag(normalisedPath);
  if (pathSlug) {
    return `${provider.slug}-${pathSlug}`;
  }
  return `${provider.slug}-${slugifyTag(url.hostname)}`;
}

async function scrapeNewsPage(provider: AiProvider, pageUrl: string): Promise<AiSignal[]> {
  const collectedAt = new Date().toISOString();
  try {
    const response = await fetchWithDelay(pageUrl);
    if (!response.ok) {
      console.warn(`News page request failed for ${pageUrl}: ${response.status} ${response.statusText}`);
      return [];
    }
    const html = await response.text();
    const $ = cheerio.load(html);
    const baseTags = buildBaseTags(provider);
    const elements = $("article").toArray();
    const containers = elements.length ? elements : $("section,div,li").filter((_, el) => $(el).find("h1,h2,h3").length > 0).toArray();
    const origin = deriveOriginFromUrl(provider, pageUrl);
    const signals: AiSignal[] = [];

    for (const element of containers.slice(0, 20)) {
      const heading = $(element).find("h1,h2,h3").first();
      const title = heading.text().trim();
      if (!title) {
        continue;
      }
      const linkHref = heading.find("a").attr("href") ?? $(element).find("a").first().attr("href");
      if (!linkHref) {
        continue;
      }
      const absoluteUrl = normaliseUrl(pageUrl, linkHref);
      const summary = $(element).find("p").first().text().trim() || undefined;
      const timeElement = $(element).find("time").first();
      const datetime = timeElement.attr("datetime") ?? timeElement.text();
      const alternativeDateText = $(element)
        .find(".date,.published,.time,.meta time,.entry-date")
        .first()
        .text();
      const publishedAtIso = parseDate(datetime) ?? parseDate(alternativeDateText) ?? collectedAt;

      const signal: AiSignal = {
        id: createSignalId(provider.slug, "website", absoluteUrl),
        providerSlug: provider.slug,
        providerName: provider.companyName,
        source: "website",
        origin,
        title,
        summary,
        url: absoluteUrl,
        tags: baseTags,
        publishedAt: publishedAtIso,
        collectedAt,
      };
      signals.push(signal);
    }

    return signals;
  } catch (error) {
    console.warn(`Failed to scrape news page ${pageUrl}:`, error);
    return [];
  }
}

async function fetchWebsiteSignals(provider: AiProvider): Promise<AiSignal[]> {
  const signals: AiSignal[] = [];
  if (!provider.newsPages?.length) {
    return signals;
  }
  for (const page of provider.newsPages) {
    const pageSignals = await scrapeNewsPage(provider, page);
    signals.push(...pageSignals);
  }
  return signals;
}

interface TwitterApiTweet {
  id: string;
  text: string;
  created_at: string;
  lang?: string;
  author_id: string;
}

interface TwitterApiUser {
  id: string;
  username: string;
  name: string;
}

interface TwitterSearchResponse {
  data?: TwitterApiTweet[];
  includes?: {
    users?: TwitterApiUser[];
  };
  errors?: unknown;
}

function extractHashtags(text: string): string[] {
  const matches = text.match(/#[\p{L}0-9_]+/gu) ?? [];
  return matches.map((tag) => slugifyTag(tag.replace(/^#/, ""))).filter(Boolean);
}

async function fetchXSignals(provider: AiProvider, token: string | undefined): Promise<AiSignal[]> {
  if (!token) {
    return [];
  }
  const queryParts: string[] = [];
  for (const handle of provider.xHandles ?? []) {
    const trimmed = handle.trim();
    if (trimmed) {
      queryParts.push(`@${trimmed}`);
    }
  }
  for (const hashtag of provider.hashtags ?? []) {
    const trimmed = hashtag.trim();
    if (trimmed) {
      queryParts.push(hashtag.startsWith("#") ? hashtag : `#${trimmed}`);
    }
  }
  if (!queryParts.length) {
    return [];
  }
  const baseQuery = queryParts.length === 1 ? queryParts[0] : `(${queryParts.join(" OR ")})`;
  const searchQuery = `${baseQuery} lang:en -is:retweet`;
  const searchParams = new URLSearchParams({
    query: searchQuery,
    "max_results": "20",
    "tweet.fields": "created_at,lang,author_id",
    expansions: "author_id",
    "user.fields": "username"
  });
  const url = `https://api.twitter.com/2/tweets/search/recent?${searchParams.toString()}`;
  try {
    const response = await fetchWithDelay(url, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!response.ok) {
      console.warn(`X API request failed for provider ${provider.slug}: ${response.status} ${response.statusText}`);
      return [];
    }
    const payload = (await response.json()) as TwitterSearchResponse;
    const tweets = payload.data ?? [];
    if (!tweets.length) {
      return [];
    }
    const users = new Map<string, TwitterApiUser>();
    for (const user of payload.includes?.users ?? []) {
      users.set(user.id, user);
    }
    const baseTags = buildBaseTags(provider);
    const collectedAt = new Date().toISOString();
    const signals: AiSignal[] = [];
    for (const tweet of tweets) {
      const author = users.get(tweet.author_id);
      const username = author?.username;
      const tweetUrl = username
        ? `https://x.com/${username}/status/${tweet.id}`
        : `https://x.com/i/web/status/${tweet.id}`;
      const cleanText = tweet.text.replace(/\s+/g, " ").trim();
      const title = cleanText.length > 120 ? `${cleanText.slice(0, 117)}...` : cleanText;
      const tags = new Set<string>([...baseTags, ...extractHashtags(tweet.text)]);
      const signal: AiSignal = {
        id: createSignalId(provider.slug, "x", tweet.id),
        providerSlug: provider.slug,
        providerName: provider.companyName,
        source: "x",
        origin: "x",
        title: title || provider.companyName,
        summary: cleanText,
        url: tweetUrl,
        language: tweet.lang,
        tags: Array.from(tags),
        publishedAt: new Date(tweet.created_at).toISOString(),
        collectedAt,
      };
      signals.push(signal);
    }
    return signals;
  } catch (error) {
    console.warn(`Failed to fetch X signals for provider ${provider.slug}:`, error);
    return [];
  }
}

async function loadExistingSignals(): Promise<AiSignal[]> {
  try {
    const raw = await fs.readFile(DATA_PATH, "utf8");
    const parsed = JSON.parse(raw) as AiSignal[];
    return Array.isArray(parsed) ? parsed : [];
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      return [];
    }
    console.warn("Failed to load existing ai_signals.json:", error);
    return [];
  }
}

async function ensureDataDirectory(): Promise<void> {
  await fs.mkdir(path.dirname(DATA_PATH), { recursive: true });
}

function dedupeSignals(signals: AiSignal[]): AiSignal[] {
  const seen = new Set<string>();
  const deduped: AiSignal[] = [];
  for (const signal of signals) {
    const key = `${signal.providerSlug}|${signal.source}|${signal.url}`;
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    deduped.push(signal);
  }
  return deduped;
}

function summarizeResults(newSignals: AiSignal[], existingSignals: AiSignal[]): { uniqueNew: number; providersCount: number } {
  const existingKeys = new Set(existingSignals.map((signal) => `${signal.providerSlug}|${signal.source}|${signal.url}`));
  const newKeys = new Set<string>();
  const providers = new Set<string>();
  for (const signal of newSignals) {
    const key = `${signal.providerSlug}|${signal.source}|${signal.url}`;
    if (existingKeys.has(key) || newKeys.has(key)) {
      continue;
    }
    newKeys.add(key);
    providers.add(signal.providerSlug);
  }
  return { uniqueNew: newKeys.size, providersCount: providers.size };
}

function sortSignals(signals: AiSignal[]): AiSignal[] {
  return [...signals].sort((a, b) => {
    const dateA = Date.parse(a.publishedAt);
    const dateB = Date.parse(b.publishedAt);
    return dateB - dateA;
  });
}

export const PROVIDERS: AiProvider[] = [
  {
    slug: "openai",
    type: "company",
    companyName: "OpenAI",
    models: ["ChatGPT", "GPT-4o", "Sora"],
    homepage: "https://openai.com",
    rssFeeds: ["https://openai.com/blog/rss.xml"],
    newsPages: ["https://openai.com/news", "https://openai.com/blog"],
    xHandles: ["OpenAI"],
    hashtags: ["#OpenAI", "#ChatGPT", "#GPT4o", "#SoraAI"],
  },
  {
    slug: "anthropic",
    type: "company",
    companyName: "Anthropic",
    models: ["Claude 3.5"],
    homepage: "https://www.anthropic.com",
    newsPages: ["https://www.anthropic.com/news"],
    xHandles: ["AnthropicAI"],
    hashtags: ["#ClaudeAI", "#Anthropic", "#Claude35"],
  },
  {
    slug: "xai",
    type: "company",
    companyName: "xAI",
    models: ["Grok-2"],
    homepage: "https://x.ai",
    newsPages: ["https://x.ai/news"],
    xHandles: ["xai", "grok"],
    hashtags: ["#Grok", "#xAI", "#Grok2"],
  },
  {
    slug: "deepmind",
    type: "company",
    companyName: "Google DeepMind",
    models: ["Gemini 1.5", "Veo 3"],
    homepage: "https://deepmind.google",
    newsPages: ["https://deepmind.google/news", "https://deepmind.google/technologies/veo"],
    xHandles: ["GoogleDeepMind"],
    hashtags: ["#DeepMind", "#GeminiAI", "#Veo3"],
  },
  {
    slug: "meta-ai",
    type: "company",
    companyName: "Meta AI",
    models: ["Llama 3.1"],
    homepage: "https://ai.meta.com",
    newsPages: ["https://ai.meta.com/blog"],
    xHandles: ["MetaAI", "Llama_AI"],
    hashtags: ["#Llama3", "#Llama31", "#MetaAI"],
  },
  {
    slug: "microsoft-ai",
    type: "company",
    companyName: "Microsoft AI",
    models: ["Copilot", "Azure AI"],
    homepage: "https://www.microsoft.com/en-us/ai",
    newsPages: ["https://www.microsoft.com/en-us/ai", "https://blogs.microsoft.com/ai"],
    xHandles: ["Microsoft", "MSFTResearch"],
    hashtags: ["#MicrosoftAI", "#Copilot", "#AzureAI"],
  },
  {
    slug: "ibm-watson",
    type: "company",
    companyName: "IBM Watson",
    models: ["Watsonx"],
    homepage: "https://www.ibm.com/watson",
    newsPages: ["https://research.ibm.com/blog"],
    hashtags: ["#Watsonx", "#IBMAI"],
  },
  {
    slug: "cohere",
    type: "company",
    companyName: "Cohere",
    models: ["Command R+"],
    homepage: "https://cohere.com",
    newsPages: ["https://cohere.com/blog"],
    hashtags: ["#Cohere", "#CommandR"],
  },
  {
    slug: "stability-ai",
    type: "company",
    companyName: "Stability AI",
    models: ["Stable Diffusion 3"],
    homepage: "https://stability.ai",
    newsPages: ["https://stability.ai/news"],
    hashtags: ["#StableDiffusion", "#SD3", "#StabilityAI"],
  },
  {
    slug: "palantir",
    type: "company",
    companyName: "Palantir",
    models: ["AIP"],
    homepage: "https://www.palantir.com",
    newsPages: ["https://www.palantir.com/blog"],
    hashtags: ["#Palantir", "#PalantirAIP"],
  },
  {
    slug: "minimax",
    type: "company",
    companyName: "MiniMax",
    models: ["Hailuo 2.3"],
    homepage: "https://minimax.io",
    newsPages: ["https://minimax.io/news"],
    hashtags: ["#MiniMax", "#Hailuo"],
  },
  {
    slug: "bytedance-seed",
    type: "company",
    companyName: "ByteDance Seed",
    models: ["Seedance 1.0"],
    homepage: "https://seed.bytedance.com",
    newsPages: ["https://seed.bytedance.com/en/seedance"],
    hashtags: ["#Seedance", "#ByteDanceAI"],
  },
  {
    slug: "chatgpt",
    type: "model",
    companyName: "ChatGPT",
    models: ["ChatGPT"],
    homepage: "https://chat.openai.com",
    hashtags: ["#ChatGPT", "#ChatGPT4"],
  },
  {
    slug: "claude",
    type: "model",
    companyName: "Claude",
    models: ["Claude"],
    homepage: "https://claude.ai",
    hashtags: ["#ClaudeAI", "#Claude35"],
  },
  {
    slug: "grok",
    type: "model",
    companyName: "Grok",
    models: ["Grok"],
    homepage: "https://grok.x.ai",
    hashtags: ["#Grok", "#GrokAI"],
  },
  {
    slug: "gemini",
    type: "model",
    companyName: "Gemini",
    models: ["Gemini"],
    homepage: "https://gemini.google.com",
    hashtags: ["#GeminiAI", "#GoogleGemini"],
  },
  {
    slug: "llama",
    type: "model",
    companyName: "Llama",
    models: ["Llama"],
    homepage: "https://llama.meta.com",
    hashtags: ["#Llama3", "#LlamaAI"],
  },
  {
    slug: "midjourney",
    type: "model",
    companyName: "Midjourney",
    models: ["Midjourney"],
    homepage: "https://www.midjourney.com",
    hashtags: ["#Midjourney", "#MidjourneyAI"],
  },
  {
    slug: "runway-gen-3",
    type: "model",
    companyName: "Runway Gen-3",
    models: ["Runway Gen-3"],
    homepage: "https://runwayml.com",
    hashtags: ["#Runway", "#RunwayGen3"],
  },
  {
    slug: "luma-dream-machine",
    type: "model",
    companyName: "Luma Dream Machine",
    models: ["Dream Machine"],
    homepage: "https://lumalabs.ai/dream-machine",
    hashtags: ["#LumaAI", "#DreamMachine"],
  },
  {
    slug: "stable-diffusion",
    type: "model",
    companyName: "Stable Diffusion",
    models: ["Stable Diffusion"],
    homepage: "https://stability.ai/stable-diffusion",
    hashtags: ["#StableDiffusion", "#StableDiffusion3"],
  },
  {
    slug: "perplexity",
    type: "model",
    companyName: "Perplexity",
    models: ["Perplexity"],
    homepage: "https://www.perplexity.ai",
    hashtags: ["#Perplexity", "#PerplexityAI"],
  },
  {
    slug: "kling",
    type: "model",
    companyName: "Kling",
    models: ["Kling"],
    homepage: "https://klingai.com",
    hashtags: ["#KlingAI", "#KlingVideo"],
  },
  {
    slug: "vidu",
    type: "model",
    companyName: "Vidu",
    models: ["Vidu"],
    homepage: "https://vidu.com",
    hashtags: ["#ViduAI", "#ViduVideo"],
  },
  {
    slug: "sora",
    type: "model",
    companyName: "Sora",
    models: ["Sora"],
    homepage: "https://openai.com/sora",
    hashtags: ["#Sora", "#SoraAI", "#SoraVideo"],
  },
  {
    slug: "veo",
    type: "model",
    companyName: "Veo",
    models: ["Veo"],
    homepage: "https://deepmind.google/technologies/veo",
    hashtags: ["#Veo", "#VeoAI", "#VeoVideo"],
  },
  {
    slug: "ltx-studio",
    type: "model",
    companyName: "LTX Studio",
    models: ["LTX Studio"],
    homepage: "https://ltx.studio",
    hashtags: ["#LTXStudio", "#LTXAI"],
  },
  {
    slug: "hailuo",
    type: "model",
    companyName: "Hailuo",
    models: ["Hailuo"],
    homepage: "https://hailuoai.video",
    hashtags: ["#Hailuo", "#HailuoAI"],
  },
  {
    slug: "seedance",
    type: "model",
    companyName: "Seedance",
    models: ["Seedance"],
    homepage: "https://seed.bytedance.com/en/seedance",
    hashtags: ["#Seedance", "#SeedanceAI"],
  },
  {
    slug: "krea",
    type: "aggregator",
    companyName: "Krea.ai",
    homepage: "https://krea.ai",
    hashtags: ["#KreaAI", "#Krea"],
  },
  {
    slug: "freepik-ai",
    type: "aggregator",
    companyName: "Freepik AI",
    homepage: "https://www.freepik.com/ai",
    hashtags: ["#FreepikAI", "#Freepik"],
  },
  {
    slug: "hugging-face",
    type: "aggregator",
    companyName: "Hugging Face",
    homepage: "https://huggingface.co",
    hashtags: ["#HuggingFace", "#HFHub"],
  },
  {
    slug: "perplexity-aggregator",
    type: "aggregator",
    companyName: "Perplexity (Aggregator)",
    homepage: "https://www.perplexity.ai",
    hashtags: ["#Perplexity", "#PerplexityAI"],
  },
  {
    slug: "replicate",
    type: "aggregator",
    companyName: "Replicate",
    homepage: "https://replicate.com",
    hashtags: ["#Replicate", "#ReplicateAI"],
  },
  {
    slug: "aixploria",
    type: "aggregator",
    companyName: "AIxploria",
    homepage: "https://aixploria.com",
    hashtags: ["#AIxploria"],
  },
  {
    slug: "toolify",
    type: "aggregator",
    companyName: "Toolify",
    homepage: "https://www.toolify.ai",
    hashtags: ["#Toolify", "#ToolifyAI"],
  },
  {
    slug: "synthesia",
    type: "aggregator",
    companyName: "Synthesia",
    homepage: "https://www.synthesia.io",
    hashtags: ["#Synthesia", "#SynthesiaAI"],
  }
];

async function gatherProviderSignals(provider: AiProvider, xToken: string | undefined): Promise<AiSignal[]> {
  const signals: AiSignal[] = [];
  const rssSignals = await fetchRssSignals(provider);
  signals.push(...rssSignals);
  const websiteSignals = await fetchWebsiteSignals(provider);
  signals.push(...websiteSignals);
  const xSignals = await fetchXSignals(provider, xToken);
  signals.push(...xSignals);
  return signals;
}

export async function main(): Promise<void> {
  const envPath = path.join(PROJECT_ROOT, ".env");
  try {
    await fs.access(envPath);
    dotenv.config({ path: envPath });
  } catch {
    dotenv.config();
  }

  await ensureDataDirectory();
  const existingSignals = await loadExistingSignals();
  const xToken = process.env.X_BEARER_TOKEN;
  if (!xToken) {
    console.log("X_BEARER_TOKEN not set, skipping X/Twitter search");
  }

  const allNewSignals: AiSignal[] = [];
  for (const provider of PROVIDERS) {
    try {
      const providerSignals = await gatherProviderSignals(provider, xToken);
      if (providerSignals.length) {
        allNewSignals.push(...providerSignals);
      }
    } catch (error) {
      console.warn(`Failed to collect signals for provider ${provider.slug}:`, error);
    }
  }

  const { uniqueNew, providersCount } = summarizeResults(allNewSignals, existingSignals);
  const combined = dedupeSignals([...allNewSignals, ...existingSignals]);
  const sorted = sortSignals(combined).slice(0, MAX_SIGNALS);
  await fs.writeFile(DATA_PATH, `${JSON.stringify(sorted, null, 2)}\n`, "utf8");

  console.log(`Fetched ${uniqueNew} new signals from ${providersCount} providers`);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error("fetchAiSignals failed:", error);
    process.exit(1);
  });
}
