"""Crawling logic for authenticated pages."""

from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from time import sleep
from typing import Callable
from urllib.parse import urlparse

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from scraper.saver import save_html
from scraper.utils import (
    is_same_domain,
    matches_skipped_path,
    matches_url_prefix,
    normalize_url,
    should_skip_url,
    url_to_output_path,
)


@dataclass(slots=True)
class CrawlResult:
    """Summary produced after a crawl run."""

    saved_pages: int
    visited_pages: int
    failed_pages: int


StatusCallback = Callable[[str, str, int, int, int, int], None]


@dataclass(slots=True)
class CrawlState:
    """Serializable crawl state for resumable crawling."""

    start_url: str
    domain_only: bool
    skipped_paths: list[str]
    url_prefixes: list[str]
    skip_existing: bool
    queue: list[str]
    visited: list[str]
    saved: int
    failed: int


def _load_state(state_file: Path) -> CrawlState:
    data = json.loads(state_file.read_text(encoding="utf-8"))
    return CrawlState(
        start_url=str(data["start_url"]),
        domain_only=bool(data["domain_only"]),
        skipped_paths=[str(item) for item in data.get("skipped_paths", [])],
        url_prefixes=[str(item) for item in data.get("url_prefixes", [])],
        skip_existing=bool(data.get("skip_existing", False)),
        queue=[str(item) for item in data.get("queue", [])],
        visited=[str(item) for item in data.get("visited", [])],
        saved=int(data.get("saved", 0)),
        failed=int(data.get("failed", 0)),
    )


def _save_state(
    state_file: Path,
    start_url: str,
    domain_only: bool,
    skipped_paths: list[str],
    url_prefixes: list[str],
    skip_existing: bool,
    queue: deque[str],
    visited: set[str],
    saved: int,
    failed: int,
) -> None:
    payload = {
        "start_url": start_url,
        "domain_only": domain_only,
        "skipped_paths": skipped_paths,
        "url_prefixes": url_prefixes,
        "skip_existing": skip_existing,
        "queue": list(queue),
        "visited": sorted(visited),
        "saved": saved,
        "failed": failed,
    }
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _is_state_compatible(
    state: CrawlState,
    start_url: str,
    domain_only: bool,
    skipped_paths: list[str],
    url_prefixes: list[str],
    skip_existing: bool,
) -> bool:
    return (
        normalize_url(state.start_url) == normalize_url(start_url)
        and state.domain_only == domain_only
        and sorted(state.skipped_paths) == sorted(skipped_paths)
        and sorted(state.url_prefixes) == sorted(url_prefixes)
        and state.skip_existing == skip_existing
    )


def crawl_site(
    start_url: str,
    output_dir: Path,
    auth_file: Path,
    max_pages: int,
    domain_only: bool,
    delay_seconds: float = 0.5,
    timeout_ms: int = 30_000,
    status_callback: StatusCallback | None = None,
    skipped_paths: list[str] | None = None,
    url_prefixes: list[str] | None = None,
    skip_existing: bool = False,
    resume: bool = False,
    state_file: Path | None = None,
) -> CrawlResult:
    """Crawl a website and save discovered HTML pages to disk."""
    normalized_start_url = normalize_url(start_url)
    start_domain = urlparse(normalized_start_url).netloc
    path_filters = skipped_paths or []
    prefix_filters = url_prefixes or []
    visited: set[str] = set()
    queue: deque[str] = deque([normalized_start_url])
    saved = 0
    failed = 0

    if resume and state_file and state_file.exists():
        state = _load_state(state_file)
        if _is_state_compatible(
            state, normalized_start_url, domain_only, path_filters, prefix_filters, skip_existing
        ):
            visited = set(state.visited)
            queue = deque(state.queue)
            saved = state.saved
            failed = state.failed

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=str(auth_file))
        page = context.new_page()

        while queue and len(visited) < max_pages:
            current_url = queue.popleft()
            if current_url in visited:
                continue
            if not matches_url_prefix(current_url, prefix_filters):
                visited.add(current_url)
                if status_callback:
                    status_callback("filtered", current_url, len(visited), saved, failed, len(queue))
                continue
            if matches_skipped_path(current_url, path_filters):
                visited.add(current_url)
                if status_callback:
                    status_callback("skipped", current_url, len(visited), saved, failed, len(queue))
                continue
            if skip_existing and url_to_output_path(current_url, output_dir).exists():
                visited.add(current_url)
                if status_callback:
                    status_callback("existing", current_url, len(visited), saved, failed, len(queue))
                continue

            visited.add(current_url)
            if status_callback:
                status_callback("visiting", current_url, len(visited), saved, failed, len(queue))

            try:
                page.goto(current_url, wait_until="domcontentloaded", timeout=timeout_ms)
                page.wait_for_load_state("networkidle", timeout=timeout_ms)
                html = page.content()
                save_html(current_url, html, output_dir, start_domain=start_domain)
                saved += 1
                if status_callback:
                    status_callback("saved", current_url, len(visited), saved, failed, len(queue))

                links = page.eval_on_selector_all("a", "els => els.map(e => e.href)")
                for raw_link in links:
                    if not raw_link:
                        continue
                    link = normalize_url(str(raw_link))
                    if should_skip_url(link):
                        continue
                    if not matches_url_prefix(link, prefix_filters):
                        continue
                    if matches_skipped_path(link, path_filters):
                        continue
                    if domain_only and not is_same_domain(link, start_domain):
                        continue
                    if link not in visited:
                        queue.append(link)
            except (PlaywrightTimeoutError, PlaywrightError):
                failed += 1
                if status_callback:
                    status_callback("failed", current_url, len(visited), saved, failed, len(queue))
                continue
            finally:
                if resume and state_file:
                    _save_state(
                        state_file=state_file,
                        start_url=normalized_start_url,
                        domain_only=domain_only,
                        skipped_paths=path_filters,
                        url_prefixes=prefix_filters,
                        skip_existing=skip_existing,
                        queue=queue,
                        visited=visited,
                        saved=saved,
                        failed=failed,
                    )
                sleep(delay_seconds)

        context.close()
        browser.close()

    if resume and state_file and not queue and state_file.exists():
        state_file.unlink()

    return CrawlResult(saved_pages=saved, visited_pages=len(visited), failed_pages=failed)
