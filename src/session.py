import json
import os
import time
from typing import Optional

from playwright.sync_api import sync_playwright, BrowserContext


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
    p = sync_playwright().start()
    cookies = load_cookies(cookies_file)

    if cookies is None:
        browser = p.chromium.launch(headless=False)
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
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        context.add_cookies(cookies)
        return context
