"""Typer CLI for auth and crawling workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import typer
from rich.console import Console
from rich.panel import Panel

from scraper.auth import auth_file_exists, login_and_save_session
from scraper.crawler import crawl_site
from scraper.saver import count_saved_pages

app = typer.Typer(help="Authenticated website offline mirror with Playwright")
console = Console()


def _project_root() -> Path:
    return Path.cwd()


def _auth_path() -> Path:
    return _project_root() / "auth.json"


def _print_crawl_status(
    event: str, url: str, visited: int, saved: int, failed: int, queued: int
) -> None:
    """Render a single crawl status line."""
    console.print(
        f"[cyan]{event.upper()}[/cyan] url={url} visited={visited} saved={saved} failed={failed} queued={queued}"
    )


@app.command()
def login(
    start_url: str = typer.Option(
        ...,
        "--start-url",
        help="Target URL where you complete Google login.",
    ),
    browser_channel: str = typer.Option(
        "chrome",
        "--browser-channel",
        help="Playwright browser channel: chrome, msedge, chrome-beta, or chromium.",
    ),
) -> None:
    """Open browser for manual login and persist Playwright session."""
    auth_file = _auth_path()
    console.print(Panel("Browser opened for manual login. Complete login before timeout."))

    try:
        login_and_save_session(
            target_url=start_url,
            auth_file=auth_file,
            browser_channel=browser_channel,
        )
    except RuntimeError as exc:
        console.print(f"[red]Login failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]Session saved to[/green] {auth_file}")


@app.command()
def crawl(
    start_url: str = typer.Option(..., "--start-url", help="Start URL for crawl."),
    output_dir: Path = typer.Option(Path("offline"), "--output-dir", help="Output directory."),
    max_pages: int = typer.Option(100, "--max-pages", min=1, help="Maximum pages to crawl."),
    domain_only: bool = typer.Option(
        False,
        "--domain-only",
        help="Restrict crawling to the same domain as --start-url.",
        is_flag=True,
    ),
    show_crawl_status: bool = typer.Option(
        False,
        "--show-crawl-status",
        help="Print live crawl progress for each page.",
        is_flag=True,
    ),
    skip_path: list[str] = typer.Option(
        [],
        "--skip-path",
        help="Skip pages whose URL path starts with this prefix. Repeat option to add multiple paths.",
    ),
    resume: bool = typer.Option(
        False,
        "--resume",
        help="Resume crawling from saved checkpoint state.",
        is_flag=True,
    ),
    state_file: Path | None = typer.Option(
        None,
        "--state-file",
        help="Path to checkpoint state file (used with --resume). Defaults to <output-dir>/.crawl_state.json.",
    ),
) -> None:
    """Crawl authenticated pages and save HTML to disk."""
    auth_file = _auth_path()
    if not auth_file_exists(auth_file):
        console.print("[red]Missing auth.json.[/red] Run `uv run scraper login` first.")
        raise typer.Exit(code=1)

    output_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_path = state_file or (output_dir / ".crawl_state.json")
    console.print(
        f"Starting crawl: start_url={start_url}, output_dir={output_dir}, max_pages={max_pages}, "
        f"domain_only={domain_only}, skip_path={skip_path}, resume={resume}, state_file={checkpoint_path}"
    )

    try:
        callback: Callable[[str, str, int, int, int, int], None] | None = (
            _print_crawl_status if show_crawl_status else None
        )
        result = crawl_site(
            start_url=start_url,
            output_dir=output_dir,
            auth_file=auth_file,
            max_pages=max_pages,
            domain_only=domain_only,
            status_callback=callback,
            skipped_paths=skip_path,
            resume=resume,
            state_file=checkpoint_path,
        )
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Crawl failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(
        Panel(
            f"Saved: {result.saved_pages}\nVisited: {result.visited_pages}\nFailed: {result.failed_pages}",
            title="Crawl Complete",
        )
    )


@app.command()
def status(output_dir: Path = typer.Option(Path("offline"), "--output-dir", help="Output directory.")) -> None:
    """Display auth status and saved page count."""
    auth_file = _auth_path()
    has_auth = auth_file_exists(auth_file)
    saved_count = count_saved_pages(output_dir)

    console.print(
        Panel(
            f"auth.json: {'present' if has_auth else 'missing'}\nSaved pages: {saved_count}\nOutput dir: {output_dir}",
            title="Scraper Status",
        )
    )


if __name__ == "__main__":
    app()
