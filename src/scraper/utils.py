"""Utility helpers for URL filtering and path conversion."""

from __future__ import annotations

from os.path import relpath
from pathlib import Path
from urllib.parse import urljoin, urlparse

SKIPPED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".svg",
    ".ico",
    ".pdf",
    ".zip",
    ".rar",
    ".7z",
    ".tar",
    ".gz",
    ".mp4",
    ".mp3",
    ".avi",
    ".mov",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".css",
    ".js",
}


def normalize_url(url: str) -> str:
    """Normalize URL by stripping fragment identifiers."""
    return url.split("#", maxsplit=1)[0]


def is_same_domain(url: str, start_domain: str) -> bool:
    """Return True if URL belongs to the starting domain."""
    return urlparse(url).netloc == start_domain


def should_skip_url(url: str) -> bool:
    """Return True for unsupported schemes or static asset URLs."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return True

    path = parsed.path.lower()
    for ext in SKIPPED_EXTENSIONS:
        if path.endswith(ext):
            return True
    return False


def matches_skipped_path(url: str, skipped_paths: list[str]) -> bool:
    """Return True when URL path starts with a configured skipped path prefix."""
    if not skipped_paths:
        return False

    path = urlparse(url).path or "/"
    for raw_prefix in skipped_paths:
        prefix = raw_prefix.strip()
        if not prefix:
            continue
        normalized_prefix = prefix if prefix.startswith("/") else f"/{prefix}"
        if path.startswith(normalized_prefix):
            return True
    return False


def matches_url_prefix(url: str, url_prefixes: list[str]) -> bool:
    """Return True when URL starts with one of the exact URL prefix filters."""
    if not url_prefixes:
        return True
    return any(url.startswith(prefix) for prefix in url_prefixes if prefix)


def url_to_output_path(url: str, output_dir: Path) -> Path:
    """Convert an absolute URL into an HTML output file path."""
    parsed = urlparse(url)
    relative = parsed.path.strip("/")

    if not relative:
        return output_dir / "index.html"

    candidate = output_dir / relative

    if candidate.suffix:
        return candidate.with_suffix(".html")

    return candidate.with_suffix(".html")


def to_relative_offline_link(
    current_url: str,
    raw_link: str,
    output_dir: Path,
    start_domain: str,
) -> str:
    """Map same-domain links to relative offline HTML paths."""
    raw = raw_link.strip()
    if not raw or raw.startswith(("#", "mailto:", "tel:", "javascript:")):
        return raw_link

    parsed_raw = urlparse(raw)
    if parsed_raw.scheme and parsed_raw.scheme not in {"http", "https"}:
        return raw_link
    if parsed_raw.netloc and parsed_raw.netloc != start_domain:
        return raw_link

    target_url = urljoin(current_url, raw)
    parsed_target = urlparse(target_url)
    if parsed_target.netloc != start_domain:
        return raw_link

    current_path = url_to_output_path(normalize_url(current_url), output_dir)
    target_path = url_to_output_path(normalize_url(target_url), output_dir)
    relative_target = Path(relpath(target_path, start=current_path.parent)).as_posix()

    if parsed_target.fragment:
        return f"{relative_target}#{parsed_target.fragment}"
    return relative_target
