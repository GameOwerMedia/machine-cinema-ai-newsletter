# generate_all.py
import os
from datetime import datetime
from fetch_ai_news import gather, save_seen
import markdown
from zoneinfo import ZoneInfo
from make_posts import format_post

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

def main(outfile_format="md"):
    os.makedirs("out", exist_ok=True)
    items = gather()
    if not items:
        print("Brak nowych artykułów w ostatnich 24h.")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    title = f"Newsletter AI — Machine Cinema Poland — {today}"
    out_path = f"out/{today}_ALL.{outfile_format}"

    # sekcje i styl hooków (bez pytań)
    sections = [
        ("GenerativeAI creators", "creators", "creators"),
        ("Marketing / fun", "marketing", "marketing"),
        ("Biznes & dev", "bizdev", "bizdev"),
    ]

    used = set()
    rendered = []
    for section_title, bucket, style in sections:
        top = pick_top(items, bucket, 5, already_used=used, scorer=score_for)
        posts = [format_post(it, style=style) for it in top]
        rendered.append((section_title, posts))

    # zapis jednego pliku
    if outfile_format == "md":
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            idx = 1
            for sec, posts in rendered:
                f.write(f"## {sec}\n\n")
                for p in posts:
                    f.write(f"{idx}. {p}\n\n")
                    idx += 1
    else:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(f"{title}\n\n")
            idx = 1
            for sec, posts in rendered:
                f.write(sec.upper() + "\n\n")
                for p in posts:
                    f.write(f"{idx}. {p}\n\n")
                    idx += 1

    # zapamiętaj, co wykorzystano
    save_seen([it["link"] for it in items])

    # --- Static HTML builder (no Jekyll required) ---
    TZ_PL = ZoneInfo("Europe/Warsaw")
    TZ_LA = ZoneInfo("America/Los_Angeles")

    def build_html(today_str: str, md_path: str) -> str:
        with open(md_path, "r", encoding="utf-8") as f:
            md_src = f.read()
        html_content = markdown.markdown(md_src, extensions=["fenced_code", "tables"])

        now_pl = datetime.now(TZ_PL)
        now_la = now_pl.astimezone(TZ_LA)
        banner_note = f"Automatyczny update: 09:00 (Warszawa) / 00:00 (Los Angeles)"

        return f"""<!DOCTYPE html>
<html lang=\"pl\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Machine Cinema Poland - Daily AI Newsletter — {today_str}</title>
  <meta name=\"description\" content=\"Codzienny przegląd AI — Machine Cinema Poland\" />
  <link rel=\"stylesheet\" href=\"assets/custom.css\" />
  <link rel=\"icon\" href=\"assets/favicon.svg\" type=\"image/svg+xml\" />
  <meta name=\"theme-color\" content=\"#ff2b2b\" />
  <meta name=\"robots\" content=\"index,follow\" />
</head>
<body>
  <header>
    <h1>
      🧠 <a href=\"https://machinecinema.ai/\" target=\"_blank\" rel=\"noopener\">Machine Cinema</a> Poland
      <span class=\"subtitle\">– Daily AI Newsletter</span>
    </h1>
    <p class=\"tagline\">Codzienny przegląd AI</p>
  </header>

  <div class=\"banner\">\n    <span class=\"clock\">🕘</span> {banner_note}\n  </div>

  <main>
    <section class=\"newsletter\">
      {html_content}
    </section>
  </main>

  <footer class=\"footer\">
    <hr>
    <p>
      Chcesz wiedzieć więcej? <br>
      Zajrzyj na stronę
      <a href=\"https://machinecinema.ai/\" target=\"_blank\" rel=\"noopener\">Machine Cinema</a>,
      sprawdź <a href=\"https://text.machinecinema.ai/\" target=\"_blank\" rel=\"noopener\">wiadomości ze świata</a>
      oraz aktualne
      <a href=\"https://luma.com/machinecinema\" target=\"_blank\" rel=\"noopener\">oficjalne wydarzenia w Twojej okolicy</a>.
    </p>
    <p class=\"copyright\">© {today_str[:4]} Machine Cinema Poland</p>
  </footer>
</body>
</html>"""

    html = build_html(today, out_path)
    os.makedirs("site", exist_ok=True)
    dated = os.path.join("site", f"{today}.html")
    with open(dated, "w", encoding="utf-8") as f:
        f.write(html)
    with open(os.path.join("site", "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Zapisano: {dated} oraz site/index.html")

if __name__ == "__main__":
    main(outfile_format="md")