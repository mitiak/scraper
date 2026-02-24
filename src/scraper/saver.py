"""Saving logic for offline HTML pages."""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup

from scraper.utils import to_relative_offline_link, url_to_output_path


def save_html(url: str, html: str, output_dir: Path, start_domain: str) -> Path:
    """Save page HTML content with same-domain links rewritten to relative paths."""
    soup = BeautifulSoup(html, "html.parser")
    for anchor in soup.find_all("a", href=True):
        href = str(anchor["href"])
        anchor["href"] = to_relative_offline_link(
            current_url=url,
            raw_link=href,
            output_dir=output_dir,
            start_domain=start_domain,
        )

    output_path = url_to_output_path(url=url, output_dir=output_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(str(soup), encoding="utf-8")
    return output_path


def count_saved_pages(output_dir: Path) -> int:
    """Count saved HTML pages under output directory."""
    if not output_dir.exists():
        return 0
    return sum(1 for path in output_dir.rglob("*.html") if path.is_file())
