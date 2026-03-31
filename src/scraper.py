import re
import time
from urllib.parse import urlparse

from playwright.sync_api import BrowserContext

from src.models import Profile


def extract_profile_id(url: str) -> str:
    match = re.search(r"linkedin\.com/in/([^/?#]+)", url)
    if not match:
        return ""
    return match.group(1).rstrip("/")


def _split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split()
    if not parts:
        return "", ""
    return parts[0], " ".join(parts[1:])


def extract_profiles_from_page(cards: list) -> list[Profile]:
    profiles = []
    for card in cards:
        link_el = card.query_selector('a[href*="/in/"]')
        name_el = card.query_selector(".entity-result__title-text")
        subtitle_el = card.query_selector(".entity-result__primary-subtitle")
        company_el = card.query_selector(".entity-result__secondary-subtitle")

        if not link_el or not name_el:
            continue

        profile_url = (link_el.get_attribute("href") or "").split("?")[0]
        full_name = name_el.inner_text().strip()
        title = subtitle_el.inner_text().strip() if subtitle_el else ""
        company_name = company_el.inner_text().strip() if company_el else ""

        if " at " in title and not company_name:
            company_name = title.split(" at ", 1)[1].strip()

        profile_id = extract_profile_id(profile_url)
        if not profile_id:
            continue

        first_name, last_name = _split_name(full_name)
        profiles.append(Profile(
            full_name=full_name,
            first_name=first_name,
            last_name=last_name,
            title=title,
            company_name=company_name,
            company_domain="",
            profile_url=profile_url,
            profile_id=profile_id,
        ))
    return profiles


def resolve_company_domain(context: BrowserContext, company_linkedin_url: str) -> str:
    page = context.new_page()
    try:
        page.goto(company_linkedin_url, wait_until="domcontentloaded", timeout=15_000)
        time.sleep(1)
        el = page.query_selector('a[data-field="website"]')
        if el is None:
            el = page.query_selector(".org-top-card-summary-info-list__info-item a")
        if el is None:
            return ""
        href = el.get_attribute("href") or ""
        if not href:
            return ""
        parsed = urlparse(href)
        return parsed.netloc.lstrip("www.")
    except Exception:
        return ""
    finally:
        page.close()


def search_people(
    context: BrowserContext,
    criteria: str,
    max_results: int = 100,
) -> list[Profile]:
    profiles: list[Profile] = []
    page_num = 1
    page = context.new_page()

    try:
        while len(profiles) < max_results:
            url = (
                f"https://www.linkedin.com/search/results/people/"
                f"?keywords={criteria}&page={page_num}"
            )
            page.goto(url, wait_until="networkidle", timeout=20_000)
            time.sleep(2)

            cards = page.query_selector_all("li.reusable-search__result-container")
            if not cards:
                break

            batch = extract_profiles_from_page(cards)
            if not batch:
                break

            profiles.extend(batch)

            next_btn = page.query_selector('button[aria-label="Next"]')
            if not next_btn or not next_btn.is_enabled():
                break

            page_num += 1
            time.sleep(1.5)
    finally:
        page.close()

    for p in profiles[:max_results]:
        if p.company_name and not p.company_domain:
            slug = p.company_name.lower().replace(" ", "-").replace(",", "")
            p.company_domain = resolve_company_domain(
                context, f"https://www.linkedin.com/company/{slug}"
            )
            time.sleep(1)

    return profiles[:max_results]
