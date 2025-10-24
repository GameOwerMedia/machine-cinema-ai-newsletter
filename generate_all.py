# generate_all.py
import os
from datetime import datetime
from pathlib import Path
from typing import List, Sequence, Tuple

import markdown
from zoneinfo import ZoneInfo

from fetch_ai_news import gather, save_seen_links
from make_posts import format_post

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency
    yaml = None


N_PER_BUCKET = 5
CONFIG_PATH = Path("sources.yml")

Section = Tuple[str, str, str]

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


def _default_sections() -> Sequence[Section]:
    return (
        ("GenerativeAI creators", "creators", "creators"),
        ("Marketing / fun", "marketing", "marketing"),
        ("Biznes & dev", "bizdev", "bizdev"),
    )


def generate_sections(items: Sequence[dict], per_bucket: int) -> Tuple[List[Tuple[str, List[str]]], List[str]]:
    """Return rendered sections and the links that were actually published."""

    used_links = set()
    rendered: List[Tuple[str, List[str]]] = []
    published_links: List[str] = []

    for section_title, bucket, style in _default_sections():
        top_items = pick_top(items, bucket, per_bucket, already_used=used_links, scorer=score_for)
        published_links.extend([it["link"] for it in top_items])
        posts = [format_post(it, style=style) for it in top_items]
        rendered.append((section_title, posts))

    return rendered, published_links


def load_config(path: Path = CONFIG_PATH) -> dict:
    """Load configuration from ``sources.yml`` if it exists."""

    if yaml is None or not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    if not isinstance(data, dict):
        return {}

    return data


def per_bucket_from_config(config: dict | None) -> int:
    """Extract and validate the per-bucket value from the loaded config."""

    if not isinstance(config, dict):
        return N_PER_BUCKET

    newsletter = config.get("newsletter") or {}
    if isinstance(newsletter, dict):
        value = newsletter.get("per_bucket")
        try:
            per_bucket = int(value)
        except (TypeError, ValueError):
            return N_PER_BUCKET
        return max(1, per_bucket)

    return N_PER_BUCKET

def main(outfile_format="md", out_dir: str = "out", site_dir: str = "site"):
    os.makedirs(out_dir, exist_ok=True)
    items = gather()
    if not items:
        print("Brak nowych artykułów w ostatnich 24h.")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    title = f"Newsletter AI — Machine Cinema Poland — {today}"
    out_path = os.path.join(out_dir, f"{today}_ALL.{outfile_format}")

    config = load_config()
    per_bucket = per_bucket_from_config(config)
    rendered, published_links = generate_sections(items, per_bucket)

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
    save_seen_links(published_links)

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
    os.makedirs(site_dir, exist_ok=True)
    dated = os.path.join(site_dir, f"{today}.html")
    with open(dated, "w", encoding="utf-8") as f:
        f.write(html)
    site_index_path = os.path.join(site_dir, "index.html")
    with open(site_index_path, "w", encoding="utf-8") as f:
        f.write(html)
    root_index_parent = Path(site_dir).resolve().parent
    redirect_target = os.path.relpath(Path(site_index_path).resolve(), root_index_parent)
    root_redirect = f"""<!DOCTYPE html>
<html lang=\"pl\">
<head>
  <meta charset=\"UTF-8\" />
  <meta http-equiv=\"refresh\" content=\"0; url={redirect_target}\" />
  <link rel=\"canonical\" href=\"{redirect_target}\" />
  <title>Machine Cinema Poland - Daily AI Newsletter</title>
  <script>
    window.location.replace('{redirect_target}');
  </script>
</head>
<body>
  <p>Przekierowanie do najnowszego wydania: <a href=\"{redirect_target}\">{redirect_target}</a></p>
</body>
</html>
"""
    with open(root_index_parent / "index.html", "w", encoding="utf-8") as f:
        f.write(root_redirect)
    print(f"\u2714 Zapisano: {dated} oraz {site_index_path}")

if __name__ == "__main__":
    main(outfile_format="md")