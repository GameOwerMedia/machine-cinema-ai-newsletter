# Machine Cinema AI Newsletter

Automated toolkit for assembling the Machine Cinema Poland AI daily newsletter. The generator can work with a curated dataset or live RSS/Google News feeds, renders Markdown and HTML output, maintains an archive and pushes static pages to GitHub Pages.

## Features

- Dual data modes: curated JSON file or live feeds (Google News, RSS).
- Automatic fallback from curated to live when the dataset is missing.
- Segment or top-story layouts with configurable bucket size in `sources.yml`.
- Hardened seen-cache with TTL, reset and daily/rolling scopes to avoid duplicates.
- Deterministic Markdown + branded HTML rendering with an archive index.
- GitHub Actions to build every morning (07:00/08:00 UTC) and deploy `site/` to Pages.
- Optional SMTP helper to send the latest edition.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The project uses Python 3.11+.

## Configuration (`sources.yml`)

`sources.yml` defines newsletter settings and live feeds.

```yaml
newsletter:
  per_bucket: 5         # stories per bucket or total when mode=top
  mode: segments        # segments | top
  buckets:              # optional custom labels/keywords
    creators:
      label: GenerativeAI creators
      style: creators
curated:
  path: data/news.json  # curated dataset path
live:
  feeds:
    - name: Google AI
      kind: google
      query: artificial intelligence
    - name: OpenAI
      kind: rss
      url: https://openai.com/blog/rss
```

## Running the generator

```bash
python generate_all.py --mode curated
```

Key flags:

- `--mode {curated|live}` – select the data pipeline; curated falls back to live when the dataset is missing.
- `--config PATH` – alternative configuration file.
- `--reset-seen` – wipe the seen cache before generation.
- `--seen-ttl DAYS` – expire entries older than N days.
- `--seen-scope {daily|rolling}` – keep per-day caches or reuse across runs.
- `--verbose` – enable debug logging.

Outputs:

- Markdown digest: `out/YYYY-MM-DD_ALL.md`
- HTML issue + latest copy: `site/YYYY-MM-DD.html`, `site/index.html`
- Archive index: `site/archive.html`

## Archive and navigation

Each run refreshes `site/archive.html` with links to every dated HTML issue. The HTML layout includes navigation links (“Najnowsze”, “Archiwum”) and a footer with Machine Cinema resources.

## Seen cache behaviour

The cache stores only the links that were actually published. Configure scope and TTL using CLI flags. Files live in `.cache/` alongside per-day lock files to keep runs idempotent.

## Automation

### GitHub Pages deployment

`.github/workflows/pages.yml` builds the newsletter on push to `main` and publishes `site/` to GitHub Pages.

### Daily cron build

`.github/workflows/daily-0900.yml` runs at 07:00 and 08:00 UTC to cover daylight saving. The job installs dependencies, runs `python generate_all.py --mode curated`, commits any updated `out/` and `site/` assets, and reuses the Pages workflow for deployment. Optional SMTP secrets can trigger email delivery.

### Email delivery (optional)

`send_email.py` sends the latest HTML issue via SMTP. Provide the following environment variables or GitHub secrets:

- `SMTP_HOST`, `SMTP_PORT`
- `SMTP_USERNAME`, `SMTP_PASSWORD`
- `NEWSLETTER_FROM`, `NEWSLETTER_TO`

Usage:

```bash
python send_email.py --html site/index.html --subject "Machine Cinema AI Newsletter"
```

## Testing

Run smoke tests locally:

```bash
pytest
```

Tests cover curated/live mode behaviour, top/segment sizing, archive updates and seen-cache TTL pruning.

## Troubleshooting

- **`FileNotFoundError: data/news.json`** – either supply the curated file or run with `--mode live`.
- **Empty newsletter** – check that live feeds return results; enable `--verbose` for debugging.
- **Repeated links** – ensure you do not reset the seen cache unless necessary and adjust TTL/scope.
- **Pages deployment issues** – confirm the `GH_TOKEN`/`GITHUB_TOKEN` has permissions for the Pages workflow.

Feel free to adapt the configuration for new feeds or bucket strategies.
