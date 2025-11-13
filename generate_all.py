# generate_all.py
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Dict, List, Tuple

from dateutil import parser as date_parser

from fetch_ai_news import gather, save_seen

N_PER_BUCKET = 5

# miękkie słowa-klucze do tria: creators / marketing / bizdev
CREATORS_KW = {
    # Tools & Platforms
    "stable diffusion", "midjourney", "runway", "comfyui", "automatic1111",
    "dall-e", "chatgpt", "gpt-4", "claude", "leonardo", "krea", "tensor",
    "pika", "veo", "kling", "sora", "luma", "animatediff", "openai", "anthropic",
    
    # Techniques
    "prompt", "prompt engineering", "lora", "controlnet", "inpainting",
    "outpainting", "img2img", "txt2img", "video2video", "style transfer",
    "fine-tuning", "dreambooth", "embeddings", "workflow", "pipeline",
    
    # Media Types
    "obraz", "image", "wideo", "video", "audio", "dźwięk", "muzyka",
    "3d", "model", "animacja", "generative", "gen-3", "gen-4", "multimodal",
    
    # Polish specific for creators
    "twórca", "twórcy", "kreatywny", "grafika", "projekt", "design", "artysta",
    "sztuka", "art", "creative", "content", "treść", "kreator", "generowanie",
    "projektant", "ilustrator", "fotograf", "filmowiec", "montaż", "postprodukcja"
}

MARKETING_KW = {
    # Campaign Types
    "kampania", "campaign", "marketing", "reklama", "ad", "ads", "advert",
    "promocja", "promotion", "brand", "branding", "wizerunek", "pr",
    
    # Social Media
    "tiktok", "instagram", "facebook", "youtube", "x ", "twitter", "linkedin",
    "social media", "social", "post", "story", "reels", "short", "shorts",
    
    # Trends & Virality
    "viral", "trend", "hot", "popular", "engagement", "interakcja", "engagement",
    "zasięg", "reach", "audience", "publiczność", "followers", "subscribers",
    
    # Analytics & Metrics
    "roi", "conversion", "ctr", "click", "impression", "analytics", "metrics",
    "statistics", "data", "insights", "performance", "results", "effectiveness",
    
    # Polish specific marketing
    "influencer", "influencerka", "content creator", "twórca treści", "bloger",
    "vloger", "youtuber", "tiktoker", "case study", "przypadek", "studium",
    "success", "sukces", "konkurs", "competition", "giveaway", "nagroda",
    "fun", "zabawa", "rozrywka", "entertainment", "humor", "mem", "meme"
}

BIZDEV_KW = {
    # Legal & Regulations
    "ustawa", "regulacja", "prawo", "law", "regulation", "compliance", "gdpr",
    "privacy", "prywatność", "license", "licencja", "copyright", "autorskie",
    "patent", "ip", "intellectual property", "własność intelektualna",
    
    # Business & Finance
    "funding", "investment", "inwestycja", "venture", "vc", "seed", "series",
    "ipo", "stock", "giełda", "exchange", "m&a", "acquisition", "merger",
    "finanse", "finance", "revenue", "przychód", "profit", "zysk", "loss", "strata",
    
    # Enterprise & Development
    "enterprise", "biznes", "business", "corporation", "firma", "company",
    "startup", "scaleup", "sme", "msme", "deweloper", "developer", "programista",
    "software", "oprogramowanie", "api", "sdk", "framework", "biblioteka",
    
    # Infrastructure & Cloud
    "cloud", "chmura", "aws", "azure", "gcp", "google cloud", "server", "serwer",
    "data center", "centrum danych", "hosting", "storage", "przechowywanie",
    "database", "baza danych", "sql", "nosql", "big data", "ai infrastructure",
    
    # Polish specific business
    "polski", "polska", "warszawa", "kraków", "wrocław", "poznań", "gdańsk",
    "poland", "europe", "europa", "ue", "unia europejska", "grant", "dotacja",
    "subsidy", "fundusz", "fund", "accelerator", "akcelerator", "incubator", "inkubator",
    "government", "rząd", "ministry", "ministerstwo", "digital", "cyfryzacja"
}

MONTHS_PL = {
    1: "stycznia",
    2: "lutego",
    3: "marca",
    4: "kwietnia",
    5: "maja",
    6: "czerwca",
    7: "lipca",
    8: "sierpnia",
    9: "września",
    10: "października",
    11: "listopada",
    12: "grudnia",
}

DEFAULT_IMAGE = "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?auto=format&fit=crop&w=1200&q=80"

def score_for(bucket, item):
    title = (item.get("title") or "")
    summ = (item.get("summary") or "")
    text = f"{title} {summ}".lower()
    s = 0
    if bucket == "creators":
        for k in CREATORS_KW:
            if k in text: s += 2
    elif bucket == "marketing":
        for k in MARKETING_KW:
            if k in text: s += 2
    else:  # bizdev
        for k in BIZDEV_KW:
            if k in text: s += 2
    s += 1 if item.get("summary") else 0
    s -= min(len(title), 140)/200.0
    return s

def pick_top(items, bucket, n, already_used, scorer):
    ranked = sorted(items, key=lambda it: scorer(bucket, it), reverse=True)
    chosen, seen_domains = [], set()

    # 1) wybór pod bucket + różnorodność domen + brak duplikatów
    for it in ranked:
        if it["link"] in already_used:
            continue
        dom = (it["link"].split("/")[2] if "://" in it["link"] else it["link"]).lower()
        if dom in seen_domains:
            continue
        seen_domains.add(dom)
        chosen.append(it)
        already_used.add(it["link"])
        if len(chosen) >= n:
            break

    # 2) BACKFILL: dobierz z reszty świeżych (bez limitu domen), nadal bez duplikatów
    if len(chosen) < n:
        fallback = sorted(
            [x for x in items if x["link"] not in already_used],
            key=lambda x: len(x.get("title",""))
        )
        for it in fallback:
            chosen.append(it)
            already_used.add(it["link"])
            if len(chosen) >= n:
                break
    return chosen


def _parse_iso(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        dt = date_parser.parse(value)
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt


def _format_datetime_pl(value: str) -> str:
    dt = _parse_iso(value).astimezone(ZoneInfo("Europe/Warsaw"))
    month = MONTHS_PL.get(dt.month, "")
    return f"{dt.day} {month} {dt.year}, {dt:%H:%M}"


def _render_latest_list(articles: List[Dict[str, str]]) -> str:
    items = []
    for art in articles[:6]:
        items.append(
            f"<li><a href=\"{art['link']}\" target=\"_blank\" rel=\"noopener\">"
            f"{art['title']}</a><span>{art['source']}</span></li>"
        )
    return "\n".join(items)


def _render_card(article: Dict[str, str]) -> str:
    image = article.get("image") or DEFAULT_IMAGE
    summary = article.get("summary", "")
    if len(summary) > 220:
        summary = summary[:217] + "..."
    return f"""
    <article class=\"news-card\">
      <a class=\"card-image\" href=\"{article['link']}\" target=\"_blank\" rel=\"noopener\">
        <img src=\"{image}\" alt=\"{article['title']}\" loading=\"lazy\" />
      </a>
      <div class=\"card-body\">
        <h3><a href=\"{article['link']}\" target=\"_blank\" rel=\"noopener\">{article['title']}</a></h3>
        <p class=\"meta\">{article['source']} • {_format_datetime_pl(article['published'])}</p>
        <p class=\"summary\">{summary}</p>
      </div>
    </article>
    """.strip()


def _render_section(name: str, anchor: str, articles: List[Dict[str, str]]) -> str:
    cards = "\n".join(_render_card(article) for article in articles)
    return f"""
    <section class=\"section-block\" id=\"{anchor}\">
      <header class=\"section-header\">
        <h2>{name}</h2>
      </header>
      <div class=\"news-grid\">
        {cards}
      </div>
    </section>
    """.strip()


def _render_featured(article: Dict[str, str]) -> str:
    image = article.get("image") or DEFAULT_IMAGE
    summary = article.get("summary", "")
    if len(summary) > 280:
        summary = summary[:277] + "..."
    return f"""
    <article class=\"hero-article\">
      <a class=\"hero-image\" href=\"{article['link']}\" target=\"_blank\" rel=\"noopener\">
        <img src=\"{image}\" alt=\"{article['title']}\" />
      </a>
      <div class=\"hero-content\">
        <span class=\"pill\">Najważniejszy temat</span>
        <h2><a href=\"{article['link']}\" target=\"_blank\" rel=\"noopener\">{article['title']}</a></h2>
        <p class=\"meta\">{article['source']} • {_format_datetime_pl(article['published'])}</p>
        <p class=\"summary\">{summary}</p>
        <a class=\"hero-button\" href=\"{article['link']}\" target=\"_blank\" rel=\"noopener\">Czytaj artykuł →</a>
      </div>
    </article>
    """.strip()

def main(outfile_format="md", site_dir="docs", date_override=None, save_seen_urls=True):
    os.makedirs("out", exist_ok=True)
    items = gather()
    if not items:
        print("Brak nowych artykułów w ostatnich 24h.")
        return

    today = date_override or datetime.now().strftime("%Y-%m-%d")
    out_path = f"out/{today}_ALL.{outfile_format}"

    featured_article = items[0]
    used_links = {featured_article["link"]}

    sections_cfg: List[Tuple[str, str, str]] = [
        ("GenerativeAI creators", "creators", "creator"),
        ("Marketing / fun", "marketing", "marketing"),
        ("Biznes & dev", "bizdev", "bizdev"),
    ]

    section_payloads: List[Tuple[str, str, List[Dict[str, str]]]] = []
    for section_title, bucket, anchor in sections_cfg:
        top_articles = pick_top(items, bucket, 4, already_used=used_links, scorer=score_for)
        section_payloads.append((section_title, anchor, top_articles))

    # Optional markdown export for archival purposes
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# Machine Cinema Poland — {today}\n\n")
        f.write("## Najważniejsze artykuły\n\n")
        f.write(f"1. {featured_article['title']} — {featured_article['link']}\n\n")
        for idx, (section_title, anchor, articles) in enumerate(section_payloads, start=2):
            f.write(f"## {section_title}\n\n")
            for article in articles:
                f.write(f"- {article['title']} — {article['link']}\n")
            f.write("\n")

    if save_seen_urls:
        save_seen([it["link"] for it in items])

    TZ_PL = ZoneInfo("Europe/Warsaw")
    TZ_LA = ZoneInfo("America/Los_Angeles")
    hero_html = _render_featured(featured_article)
    sections_html = "\n".join(
        _render_section(name, anchor, arts) for name, anchor, arts in section_payloads if arts
    )
    latest_html = _render_latest_list(items)

    def build_html(today_str: str) -> str:
        now_pl = datetime.now(TZ_PL)
        now_la = now_pl.astimezone(TZ_LA)
        banner_note = (
            f"Aktualizacja: {now_pl:%d.%m.%Y, %H:%M} (Warszawa) "
            f"/ {now_la:%d.%m.%Y, %H:%M} (Los Angeles)"
        )

        return f"""<!DOCTYPE html>
<html lang=\"pl\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Machine Cinema Poland — AI News Portal — {today_str}</title>
  <meta name=\"description\" content=\"Codzienny portal wiadomości o sztucznej inteligencji w Polsce\" />
  <link rel=\"stylesheet\" href=\"assets/custom.css\" />
  <link rel=\"icon\" href=\"assets/favicon.svg\" type=\"image/svg+xml\" />
  <meta name=\"theme-color\" content=\"#b80000\" />
  <meta name=\"robots\" content=\"index,follow\" />
</head>
<body>
  <header class=\"top-bar\">
    <div class=\"logo-wrap\">
      <span class=\"logo-mark\">🧠</span>
      <div>
        <a class=\"brand\" href=\"https://machinecinema.ai/\" target=\"_blank\" rel=\"noopener\">Machine Cinema Poland</a>
        <p class=\"strapline\">Portal wiadomości o sztucznej inteligencji</p>
      </div>
    </div>
    <nav class=\"primary-nav\">
      <a href=\"#creator\">Twórcy</a>
      <a href=\"#marketing\">Marketing</a>
      <a href=\"#bizdev\">Biznes &amp; dev</a>
    </nav>
  </header>

  <div class=\"banner\"><span class=\"clock\">🕘</span>{banner_note}</div>

  <main class=\"page\">
    <section class=\"hero\">
      {hero_html}
      <aside class=\"latest\">
        <h3>W skrócie</h3>
        <ul>
          {latest_html}
        </ul>
      </aside>
    </section>

    <section class=\"sections\">
      {sections_html}
    </section>
  </main>

  <footer class=\"footer\">
    <div class=\"footer-links\">
      <a href=\"https://text.machinecinema.ai/\" target=\"_blank\" rel=\"noopener\">Globalne wiadomości</a>
      <a href=\"https://luma.com/machinecinema\" target=\"_blank\" rel=\"noopener\">Wydarzenia</a>
      <a href=\"mailto:contact@machinecinema.ai\">Kontakt redakcji</a>
    </div>
    <p>© {today_str[:4]} Machine Cinema Poland — codziennie najświeższe informacje o AI.</p>
  </footer>
</body>
</html>"""

    html = build_html(today)
    os.makedirs(site_dir, exist_ok=True)
    dated = os.path.join(site_dir, f"{today}.html")
    with open(dated, "w", encoding="utf-8") as f:
        f.write(html)
    with open(os.path.join(site_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Zapisano: {dated} oraz {os.path.join(site_dir, 'index.html')}")

if __name__ == "__main__":
    main(outfile_format="md")