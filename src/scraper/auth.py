"""Authentication logic for persistent Playwright session state."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


def login_and_save_session(
    target_url: str,
    auth_file: Path,
    timeout_ms: int = 120_000,
    browser_channel: str = "chrome",
) -> None:
    """Open a browser for manual login and save resulting storage state."""
    auth_file.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        channel: Optional[str] = None if browser_channel == "chromium" else browser_channel
        browser = p.chromium.launch(
            headless=False,
            channel=channel,
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
        )
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto(target_url, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_timeout(timeout_ms)
            context.storage_state(path=str(auth_file))
        except (PlaywrightTimeoutError, PlaywrightError) as exc:
            raise RuntimeError(f"Login flow failed: {exc}") from exc
        finally:
            context.close()
            browser.close()


def auth_file_exists(auth_file: Path) -> bool:
    """Return True if saved auth state file exists."""
    return auth_file.exists()
