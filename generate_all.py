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
    "prompt","workflow","lora","style","comfyui","stable diffusion","sdxl",
    "veo","runway","kling","pika","krea","midjourney","gen-3","controlnet",
    "inpainting","outpainting","frame","storyboard","editor","video generation",
    "image-to-video","ip-adapter","rag video","image","video","audio","media"
}
MARKETING_KW = {
    "campaign","marketing","ads","reklama","brand","viral","trend",
    "influencer","case study","cmo","konkurs","social","mem","fun","creative",
    "tiktok","instagram","youtube","x "
}
BIZDEV_KW = {
    "ustawa","regulacja","prawo","funding","seed","series","ipo","m&a",
    "nvidia","tsmc","intel","amd","factory","fabryka","data center",
    "cloud","sla","api","sdk","benchmark","latency","throughput","token",
    "enterprise","security","compliance","eu ai act","governance","llm",
    "invest","inwestycja","rynek","biznes","deweloper","developer","stack"
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
    print(f"\u2714 Zapisano: {dated} oraz site/index.html")

if __name__ == "__main__":
    main(outfile_format="md")
