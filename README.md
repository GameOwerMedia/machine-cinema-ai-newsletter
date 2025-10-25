# Machine Cinema AI Newsletter

Daily automation that curates AI news into three themed buckets and publishes a Markdown + static HTML newsletter suitable for GitHub Pages and email delivery.

## Features
- Deterministic story ingestion from `data/news.json` with a "seen" cache so published links are never repeated.
- Weighted keyword scoring that favours domain diversity and backfills to keep each section full.
- Markdown newsletter rendering plus static HTML output for the public site.
- Optional SMTP delivery and GitHub Pages deployment so the newsletter is available in inboxes and on the web.

## Prerequisites
- Python 3.12+
- pip
- Recommended: a virtual environment (for example `python -m venv .venv && source .venv/bin/activate`).

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Running the generator
Fetch fresh stories, score them into the three sections, and render Markdown + HTML artefacts:

```bash
python generate_all.py
```

The command produces the following outputs for the current day:

- `out/YYYY-MM-DD_ALL.md` — Markdown master copy shared with email and archive flows.
- `site/YYYY-MM-DD.html` — static HTML for the dated daily page.
- `site/index.html` — latest edition promoted on the GitHub Pages site.
- `site/archive.html` — updated archive listing (built by the GitHub Pages workflow).

`generate_all.py` reads `sources.yml` to determine how many stories appear per bucket. Change `newsletter.per_bucket` to adjust the volume and re-run the generator for immediate effect.

## Automation & scheduling
- The daily cron is aligned to **09:00 Europe/Warsaw**, ensuring the newsletter lands at the start of the Polish workday.
- GitHub Actions triggers earlier in UTC (typically 07:00–08:00) so the run finishes before the public publish window, accounting for queue times and daylight-saving changes.
- Continuous integration executes `python -m pytest` to keep scoring helpers, cache logic, and formatting covered.

## GitHub Pages deployment
The repository ships a workflow at `.github/workflows/pages.yml` that:
1. Runs the generator.
2. Publishes the rendered HTML into the `site/` directory.
3. Pushes the artefacts to the `gh-pages` branch so GitHub Pages serves the newsletter automatically.

To test locally, open `site/index.html` in a browser after running the generator. When deploying via Actions, make sure GitHub Pages is configured to use the `gh-pages` branch and the workflow has permission to write to it.

## Email delivery
- `send_email.py` wraps SMTP delivery for the Markdown output. It reads environment variables `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, and `SMTP_FROM` plus the recipients list.
- The script expects the rendered Markdown (`out/YYYY-MM-DD_ALL.md`) and will inline the HTML version if present.
- Configure the GitHub Actions secrets named above to enable automated mail-outs in production. The SMTP user must support TLS.

## Subscriber management
- Newsletter signups arrive via GitHub Issues thanks to `.github/workflows/subscribe.yml`.
- Each approved address is appended to `data/subscribers.txt`, which the email sender reads while building the recipient list.
- To unsubscribe, contributors remove the address from that file in a pull request or comment on the Issue; the workflow keeps the file alphabetised to prevent duplicates.

## Configuration knobs (`sources.yml`)
- `newsletter.per_bucket` — number of stories per section (defaults to `5`).
- `newsletter.top_of_day` — enable a single-story digest instead of three sections.
- `feeds.curated` — curated datasets checked into the repo for deterministic test runs.
- `feeds.rss` — live RSS/Atom feeds polled in production pipelines.
- `keywords` — weighted hints for the scoring engine; adjust to fine-tune which stories land in each bucket.

After editing the YAML, re-run `python generate_all.py` to pick up the changes. Invalid values fall back to safe defaults and are logged during generation.

## Troubleshooting
- **No new stories generated** — ensure the curated dataset contains unpublished links and the seen cache (`.cache/seen.json`) is not removing everything. Delete the cache to force a refresh.
- **Google News links not canonical** — adjust the feed entry in `sources.yml` to use the publication's RSS endpoint instead of Google News wrappers so the canonical URL is preserved.
- **Daylight-saving drift** — the automation always targets 09:00 Europe/Warsaw; verify the GitHub cron is updated when DST changes to avoid early/late publishes.
- **SMTP failures** — confirm that all `SMTP_*` secrets are configured and that the server allows TLS connections from GitHub Actions.
- **Missing archive updates** — ensure the Pages workflow finished successfully; it regenerates `site/archive.html` by appending the new Markdown entry each day.

## Testing
Run the full unit suite (recommended before every commit):

```bash
python -m pytest
```

The tests cover the seen-cache helpers, Markdown formatting, and section selection logic so regressions surface quickly.
