# Scraper

Authenticated website offline mirror built with Playwright.

Supports: - Google login (manual once, session persisted) - Crawling
authenticated/premium pages - Saving HTML locally - CLI interface -
uv-based environment - Maintained README and CHANGELOG

------------------------------------------------------------------------

# Requirements

-   Python 3.12+
-   uv
-   Playwright

Install uv if not installed: https://docs.astral.sh/uv/

------------------------------------------------------------------------

# Installation

``` bash
uv init
uv add playwright typer rich beautifulsoup4
playwright install
```

------------------------------------------------------------------------

# Project Structure

    scraper/
    │
    ├── pyproject.toml
    ├── README.md
    ├── CHANGELOG.md
    ├── auth.json                # generated after login
    ├── src/
    │   └── scraper/
    │       ├── __init__.py
    │       ├── cli.py
    │       ├── auth.py
    │       ├── crawler.py
    │       ├── saver.py
    │       └── utils.py

Register CLI entrypoint in `pyproject.toml` so the command `scraper`
works via:

    uv run scraper

------------------------------------------------------------------------

# CLI Commands

## 1. Login

Opens browser (headful). User logs in manually via Google. Session is
saved to `auth.json`.

``` bash
uv run scraper login
```

Behavior: - Launch Chromium (headless=False) - Navigate to target site -
User completes Google login - Save `storage_state` to `auth.json` -
Close browser

------------------------------------------------------------------------

## 2. Crawl

Arguments: - `--start-url` - `--output-dir` - `--max-pages` -
`--domain-only`

Example:

``` bash
uv run scraper crawl   --start-url https://site.com   --output-dir ./offline   --max-pages 100   --domain-only
```

Behavior: - Load session from `auth.json` - Launch Playwright with
stored session - Maintain: - visited set - queue list - Extract links
using:

``` python
page.eval_on_selector_all("a", "els => els.map(e => e.href)")
```

-   Filter:
    -   Same domain only (if enabled)
    -   Skip static assets (images, pdf, zip, etc.)
-   Wait for: page.wait_for_load_state("networkidle")
-   Add small delay between requests
-   Stop at `max_pages`
-   Save each page as HTML

------------------------------------------------------------------------

## 3. Status

Shows: - Whether `auth.json` exists - Number of saved pages in output
directory

``` bash
uv run scraper status
```

------------------------------------------------------------------------

# Authentication Flow

1.  Run `login`
2.  Complete Google login manually
3.  Playwright saves session state
4.  All future crawl commands reuse session
5.  No repeated login required unless session expires

------------------------------------------------------------------------

# Saving Logic

For each page:

-   Convert URL to local file path
-   Preserve folder structure
-   Create directories automatically
-   Save full HTML content
-   Future enhancement: rewrite internal links to relative paths

Example:

https://site.com/docs/page1\
→\
offline/docs/page1.html

------------------------------------------------------------------------

# Error Handling

-   Graceful error if `auth.json` missing
-   Timeout protection
-   Skip failed pages
-   Continue crawling on recoverable errors
-   Clear CLI messages using `rich`

------------------------------------------------------------------------

# Code Quality Requirements

-   Type hints
-   Modular design
-   No global variables
-   Clear separation:
    -   auth logic
    -   crawling logic
    -   saving logic
    -   CLI interface
-   Docstrings on public functions

------------------------------------------------------------------------

# CHANGELOG.md

Use semantic versioning.

Initial content:

## \[0.1.0\] - Initial Release

-   CLI with login command
-   Auth persistence via Playwright storage_state
-   Basic crawler with internal link discovery
-   HTML saving to local directory
-   Status command

Future changes must append new version entries.

------------------------------------------------------------------------

# Legal Notice

Use only on websites you are authorized to access. Respect Terms of
Service and usage limits. Do not abuse scraping or overload servers.

------------------------------------------------------------------------

# Acceptance Criteria

Project is complete when:

-   `uv run scraper login` saves session
-   `uv run scraper crawl` downloads premium pages
-   Files open offline in browser
-   CLI works correctly
-   README allows clean setup from scratch
-   CHANGELOG exists and is properly formatted
