from __future__ import annotations

import logging
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, List

import markdown
from zoneinfo import ZoneInfo

from .segments import Section

LOGGER = logging.getLogger(__name__)

TZ_PL = ZoneInfo("Europe/Warsaw")


def render_markdown(title: str, sections: Iterable[Section]) -> str:
    lines: List[str] = [f"# {title}", ""]
    counter = 1
    for section in sections:
        lines.append(f"## {section.title}")
        lines.append("")
        for story in section.stories:
            summary = story.summary.replace("\n", " ")
            lines.append(f"{counter}. [{story.title}]({story.link})  ")
            lines.append(f"   *{story.source}* — {summary}")
            lines.append("")
            counter += 1
    return "\n".join(lines).strip() + "\n"


def render_html(title: str, sections: Iterable[Section], generated: datetime) -> str:
    md_content = render_markdown(title, sections)
    html_content = markdown.markdown(md_content, extensions=["fenced_code", "tables"])
    banner_note = "09:00 (Warszawa) / 00:00 (Los Angeles)"
    now_pl = generated.astimezone(TZ_PL)
    formatted_date = now_pl.strftime("%Y-%m-%d")
    return f"""<!DOCTYPE html>
<html lang=\"pl\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Machine Cinema Poland – Daily AI Newsletter — {formatted_date}</title>
    <meta name=\"description\" content=\"Codzienny przegląd AI — Machine Cinema Poland\" />
    <link rel=\"stylesheet\" href=\"assets/custom.css\" />
    <link rel=\"icon\" href=\"assets/favicon.svg\" type=\"image/svg+xml\" />
    <meta name=\"theme-color\" content=\"#111\" />
  </head>
  <body>
    <header class=\"hero\">
      <div class=\"hero__branding\">
        <img src=\"assets/logo.svg\" alt=\"Machine Cinema logo\" class=\"hero__logo\" />
        <div>
          <h1>Machine Cinema Poland</h1>
          <p class=\"hero__tagline\">Daily AI Newsletter</p>
        </div>
      </div>
      <div class=\"hero__meta\">
        <p class=\"hero__date\">{formatted_date}</p>
        <p class=\"hero__schedule\">🕘 Aktualizacja {banner_note}</p>
      </div>
    </header>

    <nav class=\"top-nav\">
      <a href=\"index.html\" class=\"top-nav__item\">Najnowsze</a>
      <a href=\"archive.html\" class=\"top-nav__item\">Archiwum</a>
      <a href=\"https://machinecinema.ai/\" class=\"top-nav__item\" target=\"_blank\" rel=\"noopener\">Machine Cinema</a>
    </nav>

    <main class=\"content\">
      {html_content}
    </main>

    <footer class=\"footer\">
      <p>
        <a href=\"https://machinecinema.ai/\" target=\"_blank\" rel=\"noopener\">Machine Cinema</a>
        ·
        <a href=\"https://text.machinecinema.ai/\" target=\"_blank\" rel=\"noopener\">Wiadomości</a>
        ·
        <a href=\"https://luma.com/machinecinema\" target=\"_blank\" rel=\"noopener\">Wydarzenia</a>
        ·
        <a href=\"archive.html\">Archiwum</a>
      </p>
      <p class=\"footer__copy\">© {generated.year} Machine Cinema Poland</p>
    </footer>
  </body>
</html>"""


def write_outputs(
    day: date,
    title: str,
    sections: Iterable[Section],
    out_dir: Path = Path("out"),
    site_dir: Path = Path("site"),
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = out_dir / f"{day.isoformat()}_ALL.md"
    markdown_content = render_markdown(title, sections)
    markdown_path.write_text(markdown_content, encoding="utf-8")

    generated = datetime.now(TZ_PL)
    html_content = render_html(title, sections, generated)
    site_dir.mkdir(parents=True, exist_ok=True)
    daily_path = site_dir / f"{day.isoformat()}.html"
    daily_path.write_text(html_content, encoding="utf-8")
    (site_dir / "index.html").write_text(html_content, encoding="utf-8")
    LOGGER.info("Saved newsletter HTML to %s and site/index.html", daily_path)
    _update_archive(site_dir, day)


def _update_archive(site_dir: Path, day: date) -> None:
    archive_path = site_dir / "archive.html"
    available = {
        p.stem: p
        for p in site_dir.glob("*.html")
        if p.is_file() and _is_date_like(p.stem)
    }
    available[day.isoformat()] = site_dir / f"{day.isoformat()}.html"
    items = [key for key in sorted(available.keys(), reverse=True)]
    links = "\n".join(
        f"        <li><a href=\"{name}.html\">{name}</a></li>" for name in items
    )
    archive_html = f"""<!DOCTYPE html>
<html lang=\"pl\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Archiwum — Machine Cinema Poland</title>
    <link rel=\"stylesheet\" href=\"assets/custom.css\" />
  </head>
  <body class=\"archive\">
    <header class=\"hero hero--compact\">
      <div>
        <h1>Archiwum newslettera</h1>
        <p>Wszystkie wydania w jednym miejscu.</p>
      </div>
    </header>
    <main class=\"content\">
      <ul class=\"archive__list\">
{links}
      </ul>
    </main>
    <footer class=\"footer\">
      <p>
        <a href=\"index.html\">Najnowsze</a>
        ·
        <a href=\"https://machinecinema.ai/\" target=\"_blank\" rel=\"noopener\">Machine Cinema</a>
      </p>
      <p class=\"footer__copy\">© {datetime.now().year} Machine Cinema Poland</p>
    </footer>
  </body>
</html>"""
    archive_path.write_text(archive_html, encoding="utf-8")


def _is_date_like(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False
