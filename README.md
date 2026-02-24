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
  --skip-path /logout \
  --skip-path /account \
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
- Optionally skips pages by path prefix with `--skip-path`
- Optionally resumes interrupted crawl from checkpoint with `--resume`
- Waits for `networkidle`
- Saves HTML for each page with same-domain links rewritten as relative paths
- Optional live crawl status output via `--show-crawl-status`

Resume details:

- Default checkpoint file: `./offline/.crawl_state.json`
- Override checkpoint path with `--state-file`
- Checkpoint is updated during crawl and automatically removed when crawl completes the queue

### 3. Status

Show auth availability and saved page count:

```bash
uv run scraper status
```

Optional output directory:

```bash
uv run scraper status --output-dir ./offline
```

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
