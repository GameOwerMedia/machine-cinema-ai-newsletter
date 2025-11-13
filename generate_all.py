# generate_all.py
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Dict, List, Optional, Tuple

from dateutil import parser as date_parser

from fetch_ai_news import gather, save_seen

try:  # Optional dependency, falls back gracefully when unavailable
    from googletrans import Translator  # type: ignore
except Exception:  # pragma: no cover - optional import guard
    Translator = None

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

_TRANSLATOR = None


def _get_translator():
    global _TRANSLATOR
    if _TRANSLATOR is False:
        return None
    if _TRANSLATOR is None and Translator is not None:
        try:
            _TRANSLATOR = Translator()
        except Exception:
            _TRANSLATOR = False
    return None if _TRANSLATOR is False else _TRANSLATOR


def _translate_batch(texts, dest="en"):
    translator = _get_translator()
    if not texts:
        return []
    if translator is None:
        return [None] * len(texts)

    translated_texts: List[Optional[str]] = []
    for text in texts:
        try:
            result = translator.translate(text, dest=dest)
        except Exception:
            translated_texts.append(None)
            continue

        translated_texts.append(getattr(result, "text", None))

    return translated_texts


def _ensure_translations(items: List[Dict[str, str]]) -> None:
    texts = []
    lookup: List[Tuple[int, str]] = []
    for idx, item in enumerate(items):
        for key in ("title", "summary"):
            value = (item.get(key) or "").strip()
            if value:
                texts.append(value)
                lookup.append((idx, key))

    translations = _translate_batch(texts, dest="en") if texts else []

    for (idx, key), translated in zip(lookup, translations):
        english_value = translated or (items[idx].get(key) or "")
        items[idx][f"{key}_en"] = english_value

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


def _format_datetime_en(value: str) -> str:
    dt = _parse_iso(value).astimezone(ZoneInfo("Europe/Warsaw"))
    return dt.strftime("%d %B %Y, %H:%M")


def _render_latest_list(articles: List[Dict[str, str]]) -> str:
    items = []
    for art in articles[:6]:
        items.append(
            f"""
            <li>
              <a href=\"{art['link']}\" target=\"_blank\" rel=\"noopener\">
                <span data-lang-content=\"pl\">{art['title']}</span>
                <span data-lang-content=\"en\">{art.get('title_en', art['title'])}</span>
              </a>
              <span class=\"latest-source\">
                <span data-lang-content=\"pl\">{art['source']}</span>
                <span data-lang-content=\"en\">{art['source']}</span>
              </span>
            </li>
            """.strip()
        )
    return "\n".join(items)


def _render_card(article: Dict[str, str]) -> str:
    image = article.get("image") or DEFAULT_IMAGE
    summary = article.get("summary", "")
    if len(summary) > 220:
        summary = summary[:217] + "..."
    summary_en = article.get("summary_en", summary)
    if len(summary_en) > 220:
        summary_en = summary_en[:217] + "..."
    meta_pl = f"{article['source']} • {_format_datetime_pl(article['published'])}"
    meta_en = f"{article['source']} • {_format_datetime_en(article['published'])}"
    return f"""
    <article class=\"news-card\">
      <a class=\"card-image\" href=\"{article['link']}\" target=\"_blank\" rel=\"noopener\">
        <img src=\"{image}\" alt=\"{article['title']}\" loading=\"lazy\" />
      </a>
      <div class=\"card-body\">
        <h3>
          <a href=\"{article['link']}\" target=\"_blank\" rel=\"noopener\" data-lang-content=\"pl\">{article['title']}</a>
          <a href=\"{article['link']}\" target=\"_blank\" rel=\"noopener\" data-lang-content=\"en\">{article.get('title_en', article['title'])}</a>
        </h3>
        <p class=\"meta\">
          <span data-lang-content=\"pl\">{meta_pl}</span>
          <span data-lang-content=\"en\">{meta_en}</span>
        </p>
        <p class=\"summary\">
          <span data-lang-content=\"pl\">{summary}</span>
          <span data-lang-content=\"en\">{summary_en}</span>
        </p>
      </div>
    </article>
    """.strip()


def _render_section(name_pl: str, name_en: str, anchor: str, articles: List[Dict[str, str]]) -> str:
    cards = "\n".join(_render_card(article) for article in articles)
    return f"""
    <section class=\"section-block\" id=\"{anchor}\">
      <header class=\"section-header\">
        <h2>
          <span data-lang-content=\"pl\">{name_pl}</span>
          <span data-lang-content=\"en\">{name_en}</span>
        </h2>
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
    summary_en = article.get("summary_en", summary)
    if len(summary_en) > 280:
        summary_en = summary_en[:277] + "..."
    meta_pl = f"{article['source']} • {_format_datetime_pl(article['published'])}"
    meta_en = f"{article['source']} • {_format_datetime_en(article['published'])}"
    return f"""
    <article class=\"hero-article\">
      <a class=\"hero-image\" href=\"{article['link']}\" target=\"_blank\" rel=\"noopener\">
        <img src=\"{image}\" alt=\"{article['title']}\" />
      </a>
      <div class=\"hero-content\">
        <span class=\"pill\" data-lang-content=\"pl\">Najważniejszy temat</span>
        <span class=\"pill\" data-lang-content=\"en\">Top story</span>
        <h2>
          <a href=\"{article['link']}\" target=\"_blank\" rel=\"noopener\" data-lang-content=\"pl\">{article['title']}</a>
          <a href=\"{article['link']}\" target=\"_blank\" rel=\"noopener\" data-lang-content=\"en\">{article.get('title_en', article['title'])}</a>
        </h2>
        <p class=\"meta\">
          <span data-lang-content=\"pl\">{meta_pl}</span>
          <span data-lang-content=\"en\">{meta_en}</span>
        </p>
        <p class=\"summary\">
          <span data-lang-content=\"pl\">{summary}</span>
          <span data-lang-content=\"en\">{summary_en}</span>
        </p>
        <a class=\"hero-button\" href=\"{article['link']}\" target=\"_blank\" rel=\"noopener\" data-lang-content=\"pl\">Czytaj artykuł →</a>
        <a class=\"hero-button\" href=\"{article['link']}\" target=\"_blank\" rel=\"noopener\" data-lang-content=\"en\">Read article →</a>
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

    sections_cfg: List[Tuple[str, str, str, str]] = [
        ("Twórcy generatywnej AI", "Generative AI creators", "creators", "creator"),
        ("Marketing i rozrywka", "Marketing & entertainment", "marketing", "marketing"),
        ("Biznes i rozwój", "Business & development", "bizdev", "bizdev"),
    ]

    section_payloads: List[Tuple[str, str, str, List[Dict[str, str]]]] = []
    for title_pl, title_en, bucket, anchor in sections_cfg:
        top_articles = pick_top(items, bucket, 4, already_used=used_links, scorer=score_for)
        section_payloads.append((title_pl, title_en, anchor, top_articles))

    # Optional markdown export for archival purposes
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# Machine Cinema Poland — {today}\n\n")
        f.write("## Najważniejsze artykuły\n\n")
        f.write(f"1. {featured_article['title']} — {featured_article['link']}\n\n")
        for idx, (title_pl, _, anchor, articles) in enumerate(section_payloads, start=2):
            f.write(f"## {title_pl}\n\n")
            for article in articles:
                f.write(f"- {article['title']} — {article['link']}\n")
            f.write("\n")

    if save_seen_urls:
        save_seen([it["link"] for it in items])

    TZ_PL = ZoneInfo("Europe/Warsaw")
    TZ_LA = ZoneInfo("America/Los_Angeles")
    _ensure_translations(items)
    hero_html = _render_featured(featured_article)
    sections_html = "\n".join(
        _render_section(name_pl, name_en, anchor, arts)
        for name_pl, name_en, anchor, arts in section_payloads
        if arts
    )
    latest_html = _render_latest_list(items)

    def build_html(today_str: str) -> str:
        now_pl = datetime.now(TZ_PL)
        now_la = now_pl.astimezone(TZ_LA)
        banner_note_pl = (
            f"Aktualizacja: {now_pl:%d.%m.%Y, %H:%M} (Warszawa) "
            f"/ {now_la:%d.%m.%Y, %H:%M} (Los Angeles)"
        )
        banner_note_en = (
            f"Updated: {now_pl:%d.%m.%Y, %H:%M} (Warsaw) "
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
<body class=\"lang-pl\">
  <header class=\"top-bar\">
    <div class=\"logo-wrap\">
      <span class=\"logo-mark\">🧠</span>
      <div>
        <a class=\"brand\" href=\"https://machinecinema.ai/\" target=\"_blank\" rel=\"noopener\">Machine Cinema Poland</a>
        <p class=\"strapline\" data-lang-content=\"pl\">Portal wiadomości o sztucznej inteligencji</p>
        <p class=\"strapline\" data-lang-content=\"en\">Newsroom focused on artificial intelligence</p>
      </div>
    </div>
    <div class=\"lang-toggle\">
      <button type=\"button\" class=\"lang-button active\" data-lang=\"pl\">PL</button>
      <button type=\"button\" class=\"lang-button\" data-lang=\"en\">EN</button>
    </div>
    <nav class=\"primary-nav\">
      <a href=\"#creator\"><span data-lang-content=\"pl\">Twórcy</span><span data-lang-content=\"en\">Creators</span></a>
      <a href=\"#marketing\"><span data-lang-content=\"pl\">Marketing</span><span data-lang-content=\"en\">Marketing</span></a>
      <a href=\"#bizdev\"><span data-lang-content=\"pl\">Biznes &amp; dev</span><span data-lang-content=\"en\">Business &amp; dev</span></a>
    </nav>
  </header>

  <div class=\"banner\"><span class=\"clock\">🕘</span><span data-lang-content=\"pl\">{banner_note_pl}</span><span data-lang-content=\"en\">{banner_note_en}</span></div>

  <main class=\"page\">
    <section class=\"hero\">
      {hero_html}
      <aside class=\"latest\">
        <h3>
          <span data-lang-content=\"pl\">W skrócie</span>
          <span data-lang-content=\"en\">In brief</span>
        </h3>
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
      <a href=\"https://text.machinecinema.ai/\" target=\"_blank\" rel=\"noopener\">
        <span data-lang-content=\"pl\">Globalne wiadomości</span>
        <span data-lang-content=\"en\">Global news</span>
      </a>
      <a href=\"https://luma.com/machinecinema\" target=\"_blank\" rel=\"noopener\">
        <span data-lang-content=\"pl\">Wydarzenia</span>
        <span data-lang-content=\"en\">Events</span>
      </a>
      <a href=\"mailto:contact@machinecinema.ai\">
        <span data-lang-content=\"pl\">Kontakt redakcji</span>
        <span data-lang-content=\"en\">Contact the newsroom</span>
      </a>
    </div>
    <p>
      <span data-lang-content=\"pl\">© {today_str[:4]} Machine Cinema Poland — codziennie najświeższe informacje o AI.</span>
      <span data-lang-content=\"en\">© {today_str[:4]} Machine Cinema Poland — daily insights on artificial intelligence.</span>
    </p>
  </footer>
  <script>
    const langButtons = document.querySelectorAll('.lang-button');
    function applyLanguage(lang) {{
      document.documentElement.setAttribute('lang', lang);
      document.body.classList.remove('lang-pl', 'lang-en');
      document.body.classList.add('lang-' + lang);
      langButtons.forEach((btn) => {{
        btn.classList.toggle('active', btn.dataset.lang === lang);
      }});
    }}
    langButtons.forEach((btn) => {{
      btn.addEventListener('click', () => applyLanguage(btn.dataset.lang));
    }});
    applyLanguage('pl');
  </script>
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