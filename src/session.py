import asyncio
import json
import os
import sys
import time
from typing import Optional

from playwright.sync_api import sync_playwright, BrowserContext


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def save_cookies(cookies: list, path: str) -> None:
    with open(path, "w") as f:
        json.dump(cookies, f, indent=2)


def load_cookies(path: str) -> Optional[list]:
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def get_authenticated_context(cookies_file: str) -> BrowserContext:
    """
    Returns a Playwright BrowserContext with a valid LinkedIn session.

    First run (no cookies file): opens a visible browser for manual login.
    Waits for the LinkedIn feed, saves cookies, then returns the context.

    Subsequent runs: loads saved cookies into a headless browser.
    """
    if sys.platform == "win32":
        # Streamlit/Tornado overrides the event loop policy to SelectorEventLoop,
        # which doesn't support subprocess creation on Windows. Force ProactorEventLoop
        # so Playwright can spawn its browser process. The policy API is deprecated in
        # 3.14 and removed in 3.16, where ProactorEventLoop becomes the only option.
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except AttributeError:
            pass
    p = sync_playwright().start()
    cookies = load_cookies(cookies_file)

    exe = os.getenv("CHROME_EXECUTABLE") or None
    headless = _env_flag("LINKEDIN_HEADLESS", default=False)

    if cookies is None:
        browser = p.chromium.launch(headless=False, executable_path=exe)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://www.linkedin.com/login")
        print("\n[session] Log into LinkedIn in the browser window.")
        print("[session] Waiting until you reach the feed...")
        page.wait_for_url("**/feed/**", timeout=120_000)
        print("[session] Logged in. Saving cookies.")
        save_cookies(context.cookies(), cookies_file)
        page.close()
        return context
    else:
        browser = p.chromium.launch(headless=headless, executable_path=exe)
        context = browser.new_context()
        context.add_cookies(cookies)
        return context


def close_authenticated_context(context: BrowserContext) -> None:
    try:
        browser = getattr(context, "browser", None)
        context.close()
        if browser is not None:
            browser.close()
    except Exception:
        pass
