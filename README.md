# Scraper

Authenticated website offline mirror built with Playwright.

## Features

- Manual Google login once, with persisted session in `auth.json`
- Crawl authenticated and premium pages with stored session
- Save full HTML locally with preserved URL path structure
- CLI commands: `login`, `crawl`, `status`
- `uv`-managed Python environment

## Requirements

- Python 3.12+
- uv
- Playwright browser binaries

## Installation

```bash
uv init
uv add playwright typer rich beautifulsoup4
uv run playwright install
```

## Usage

### 1. Login

Open a non-headless browser and complete Google login manually. Session is saved to `auth.json`.

Provide target URL:

```bash
uv run scraper login --start-url <START_URL>
```

If Google blocks sign-in in bundled Chromium, use your local Chrome channel explicitly:

```bash
uv run scraper login --start-url <START_URL> --browser-channel chrome
```

### 2. Crawl

```bash
uv run scraper crawl \
  --start-url <START_URL> \
  --output-dir ./offline \
  --max-pages 1000 \
  --url-prefix <START_URL>/docs \
  --skip-path /logout \
  --skip-path /account \
  --skip-existing \
  --domain-only \
  --resume \
  --show-crawl-status
```

Behavior:

- Loads session from `auth.json`
- Crawls with queue + visited set
- Extracts links via `page.eval_on_selector_all("a", "els => els.map(e => e.href)")`
- Filters non-http(s) and static assets
- Optionally restricts to same domain
- Optionally limits crawl to exact URL prefixes via `--url-prefix`
- Optionally skips pages by path prefix with `--skip-path`
- Optionally skips URLs with existing local HTML via `--skip-existing`
- Optionally resumes interrupted crawl from checkpoint with `--resume`
- Waits for `networkidle`
- Saves HTML for each page with same-domain links rewritten as relative paths
- Optional live crawl status output via `--show-crawl-status`

Resume details:

- Default checkpoint file: `./offline/.crawl_state.json`
- Override checkpoint path with `--state-file`
- Checkpoint is updated during crawl and automatically removed when crawl completes the queue
- Resume compatibility checks include `--skip-existing`, `--skip-path`, and `--url-prefix` settings

### 3. Status

Show auth availability and saved page count:

```bash
uv run scraper status
```

Optional output directory:

```bash
uv run scraper status --output-dir ./offline
```

## Examples

### Basic login and crawl

Use this for a first run with minimal filtering.

```bash
uv run scraper login --start-url <START_URL>
uv run scraper crawl --start-url <START_URL> --output-dir ./offline --max-pages 200
```

### Crawl only one section by exact URL prefix

Use this when you only want a specific area like docs or blog.

```bash
uv run scraper crawl \
  --start-url <START_URL> \
  --url-prefix <START_URL>/docs \
  --max-pages 500
```

### Exclude known unwanted paths

Use this to avoid logout/account or noisy areas.

```bash
uv run scraper crawl \
  --start-url <START_URL> \
  --skip-path /logout \
  --skip-path /account \
  --skip-path /settings
```

### Continue interrupted crawl

Use this after stopping a long run; queue and visited state are restored.

```bash
uv run scraper crawl \
  --start-url <START_URL> \
  --output-dir ./offline \
  --resume
```

### Continue crawl and avoid re-downloading existing files

Use this for incremental updates in an existing offline mirror.

```bash
uv run scraper crawl \
  --start-url <START_URL> \
  --output-dir ./offline \
  --resume \
  --skip-existing
```

### Show live crawl progress

Use this to monitor what is being visited, saved, skipped, filtered, or failed.

```bash
uv run scraper crawl \
  --start-url <START_URL> \
  --show-crawl-status
```

### Use a custom checkpoint file

Use this when running multiple independent crawl sessions.

```bash
uv run scraper crawl \
  --start-url <START_URL> \
  --resume \
  --state-file ./offline/session-docs-state.json
```

### Check crawl output quickly

Use this to confirm login state and how many pages were saved.

```bash
uv run scraper status --output-dir ./offline
```

## Option Combinations Cheat Sheet

| Goal | Recommended options |
| --- | --- |
| First full crawl | `--start-url <START_URL> --output-dir ./offline --max-pages 200` |
| Long crawl with restart safety | `--resume --state-file ./offline/crawl-state.json` |
| Incremental updates only | `--resume --skip-existing` |
| Restrict to a specific section | `--url-prefix <START_URL>/docs` |
| Avoid sensitive/noisy endpoints | `--skip-path /logout --skip-path /account` |
| Stay inside the same domain | `--domain-only` |
| Watch progress live | `--show-crawl-status` |
| Safe targeted incremental docs crawl | `--url-prefix <START_URL>/docs --resume --skip-existing --show-crawl-status` |

## Saved Output Mapping

Example:

`/docs/page1` -> `offline/docs/page1.html`

## Error Handling

- Graceful message when `auth.json` is missing
- Timeout protection
- Recoverable crawl failures are skipped
- Clear CLI output with `rich`

## Legal Notice

Use only on websites you are authorized to access. Respect Terms of Service and usage limits. Do not abuse scraping or overload servers.
