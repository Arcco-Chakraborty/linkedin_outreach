import re
import time
from typing import Optional

from playwright.sync_api import BrowserContext

_CONTACT_PATHS = ["/", "/contact", "/about", "/team"]


def classify_local_part(local: str) -> Optional[str]:
    local = local.lower().strip()
    cleaned = local.replace(".", "").replace("-", "").replace("_", "")
    if not cleaned.isalpha() or len(cleaned) < 2:
        return None

    if "." in local:
        parts = local.split(".", 1)
        if len(parts[0]) == 1:
            return "f0.l"
        return "f.l"

    if len(local) <= 5:
        return "f"
    return "fl"


def detect_pattern(local_parts: list[str]) -> Optional[str]:
    votes: dict[str, int] = {}
    for local in local_parts:
        key = classify_local_part(local)
        if key:
            votes[key] = votes.get(key, 0) + 1
    if not votes:
        return None
    return max(votes, key=lambda k: votes[k])


def _extract_local_parts(text: str, domain: str) -> list[str]:
    pattern = re.compile(
        r"\b([a-z0-9._%+\-]+)@" + re.escape(domain) + r"\b",
        re.IGNORECASE,
    )
    return [m.group(1).lower() for m in pattern.finditer(text)]


def collect_emails_from_duckduckgo(context: BrowserContext, domain: str) -> list[str]:
    try:
        page = context.new_page()
        try:
            page.goto(
                f"https://duckduckgo.com/?q=%22%40{domain}%22&ia=web",
                wait_until="domcontentloaded",
                timeout=15_000,
            )
            time.sleep(2)
            snippets = page.query_selector_all(".result__snippet")
            local_parts: list[str] = []
            for el in snippets:
                text = el.inner_text()
                local_parts.extend(_extract_local_parts(text, domain))
            return list(dict.fromkeys(local_parts))
        finally:
            page.close()
    except Exception:
        return []


def collect_emails_from_website(context: BrowserContext, domain: str) -> list[str]:
    local_parts: list[str] = []
    try:
        page = context.new_page()
        try:
            for path in _CONTACT_PATHS:
                try:
                    page.goto(
                        f"https://{domain}{path}",
                        wait_until="domcontentloaded",
                        timeout=10_000,
                    )
                    time.sleep(1)
                    text = page.inner_text("body")
                    local_parts.extend(_extract_local_parts(text, domain))
                except Exception:
                    continue
        finally:
            page.close()
    except Exception:
        pass
    return list(dict.fromkeys(local_parts))


def get_domain_pattern(context: BrowserContext, domain: str) -> Optional[str]:
    local_parts = collect_emails_from_duckduckgo(context, domain)
    if len(local_parts) < 2:
        local_parts += collect_emails_from_website(context, domain)
    return detect_pattern(local_parts)
