import re
import time
from urllib.parse import parse_qs, quote_plus, urlparse

from playwright.sync_api import BrowserContext, TimeoutError as PlaywrightTimeoutError

from src.models import Profile

_RESULT_CARD_SELECTORS = [
    "li.reusable-search__result-container",
    "li.search-results__list-item",
    "div.entity-result",
    "main li",
]

_PROFILE_LINK_SELECTOR = 'a[href*="/in/"]'
_NAME_SELECTORS = [
    ".entity-result__title-text",
    ".app-aware-link span[aria-hidden='true']",
]
_TITLE_SELECTORS = [
    ".entity-result__primary-subtitle",
    ".t-14.t-black.t-normal",
]
_COMPANY_SELECTORS = [
    ".entity-result__secondary-subtitle",
]
_BAD_DOMAIN_HINTS = {"linkedin.com", "facebook.com", "instagram.com", "x.com", "twitter.com", "youtube.com"}


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


def _first_element(card, selectors: list[str]):
    for selector in selectors:
        element = card.query_selector(selector)
        if element:
            return element
    return None


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _text_lines(value: str) -> list[str]:
    return [
        _clean_text(line)
        for line in (value or "").splitlines()
        if _clean_text(line)
    ]


def _is_noise_line(line: str) -> bool:
    lowered = line.lower()
    if not lowered:
        return True
    prefixes = (
        "view ",
        "status is ",
        "follow",
        "message",
        "connect",
        "premium",
    )
    if lowered.startswith(prefixes):
        return True
    if "degree connection" in lowered:
        return True
    if " followers" in lowered or lowered.endswith(" followers"):
        return True
    if lowered.startswith("provides services"):
        return True
    return False


def _looks_like_name(value: str) -> bool:
    if not value:
        return False
    if _is_noise_line(value):
        return False
    words = [word for word in re.split(r"\s+", value) if word]
    if not words or len(words) > 5:
        return False
    return all(re.search(r"[A-Za-z]", word) for word in words)


def _extract_name_from_link(link_el) -> str:
    lines = _text_lines(link_el.inner_text())
    for line in lines:
        if _looks_like_name(line):
            return line
    return ""


def _choose_profile_link(card):
    links = card.query_selector_all(_PROFILE_LINK_SELECTOR)
    if not isinstance(links, (list, tuple)):
        links = []
    if not links:
        single_link = card.query_selector(_PROFILE_LINK_SELECTOR)
        if single_link:
            links = [single_link]
    if not links:
        return None

    best_link = None
    best_score = -1
    for link in links:
        href = link.get_attribute("href") or ""
        text = _clean_text(link.inner_text())
        score = 0
        if "miniProfileUrn" in href:
            score += 2
        if "View " in text and "profile" in text:
            score += 3
        if _extract_name_from_link(link):
            score += 4
        if text.lower().startswith("status is"):
            score -= 5
        if "provides services" in text.lower():
            score -= 5
        if score > best_score:
            best_score = score
            best_link = link

    return best_link


def _fallback_profile_text(card) -> tuple[str, str, str]:
    lines = [line for line in _text_lines(card.inner_text()) if not _is_noise_line(line)]
    if not lines:
        return "", "", ""

    full_name = lines[0]
    title = lines[1] if len(lines) > 1 else ""
    company_name = ""

    company_name = _infer_company_name_from_title(title)

    return full_name, title, company_name


def _infer_company_name_from_title(title: str) -> str:
    if not title:
        return ""

    normalized = _clean_text(title)
    lowered = normalized.lower()

    if " at " in lowered:
        return normalized.split(" at ", 1)[1].split("|", 1)[0].strip(" ,-")

    if "@" in normalized:
        return normalized.split("@", 1)[1].split("|", 1)[0].strip(" ,-")

    prefix_match = re.match(
        r"^(?:co[- ]?founder|founder|ceo|co[- ]?founder\s*&\s*ceo|ceo\s*&\s*founder)\s*,\s*(.+)$",
        normalized,
        flags=re.IGNORECASE,
    )
    if prefix_match:
        return prefix_match.group(1).split("|", 1)[0].strip(" ,-")

    return ""


def _is_useful_domain(domain: str) -> bool:
    if not domain:
        return False
    lowered = domain.lower()
    return not any(lowered == bad or lowered.endswith(f".{bad}") for bad in _BAD_DOMAIN_HINTS)


def _extract_domain_from_href(href: str) -> str:
    if not href:
        return ""

    if href.startswith("//"):
        href = "https:" + href

    parsed = urlparse(href)
    if "duckduckgo.com" in parsed.netloc:
        target = parse_qs(parsed.query).get("uddg", [""])[0]
        if target:
            parsed = urlparse(target)

    return parsed.netloc.lower().lstrip("www.")


def _search_company_domain(context: BrowserContext, company_name: str) -> str:
    page = context.new_page()
    try:
        query = quote_plus(f"{company_name} official website")
        page.goto(
            f"https://duckduckgo.com/html/?q={query}",
            wait_until="domcontentloaded",
            timeout=15_000,
        )
        time.sleep(2)

        links = page.query_selector_all("a.result__a")
        for link in links:
            href = link.get_attribute("href") or ""
            domain = _extract_domain_from_href(href)
            if _is_useful_domain(domain):
                return domain
    except Exception:
        return ""
    finally:
        page.close()
    return ""


def build_people_search_url(criteria: str, page_num: int) -> str:
    encoded_criteria = quote_plus(criteria.strip())
    return (
        "https://www.linkedin.com/search/results/people/"
        f"?keywords={encoded_criteria}&origin=GLOBAL_SEARCH_HEADER&page={page_num}"
    )


def _get_result_cards(page) -> list:
    for selector in _RESULT_CARD_SELECTORS:
        cards = page.query_selector_all(selector)
        if cards:
            return cards
    return []


def _wait_for_search_results(page) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=5_000)
        return
    except PlaywrightTimeoutError:
        pass

    for selector in _RESULT_CARD_SELECTORS:
        try:
            page.wait_for_selector(selector, timeout=3_000)
            return
        except PlaywrightTimeoutError:
            continue


def _is_login_page(page) -> bool:
    return "/login" in page.url or page.query_selector("form.login__form") is not None


def extract_profiles_from_page(cards: list) -> list[Profile]:
    profiles = []
    for card in cards:
        link_el = _choose_profile_link(card)
        name_el = _first_element(card, _NAME_SELECTORS)
        subtitle_el = _first_element(card, _TITLE_SELECTORS)
        company_el = _first_element(card, _COMPANY_SELECTORS)

        if not link_el:
            continue

        profile_url = (link_el.get_attribute("href") or "").split("?")[0]
        full_name = _clean_text(name_el.inner_text()) if name_el else ""
        if not full_name:
            full_name = _extract_name_from_link(link_el)
        title = _clean_text(subtitle_el.inner_text()) if subtitle_el else ""
        company_name = _clean_text(company_el.inner_text()) if company_el else ""

        if not _looks_like_name(full_name) or not title:
            fallback_name, fallback_title, fallback_company = _fallback_profile_text(card)
            if not _looks_like_name(full_name):
                full_name = fallback_name
            title = title or fallback_title
            company_name = company_name or fallback_company

        if not company_name:
            company_name = _infer_company_name_from_title(title)

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


def resolve_company_domain(
    context: BrowserContext,
    company_linkedin_url: str,
    company_name: str = "",
) -> str:
    page = context.new_page()
    try:
        page.goto(company_linkedin_url, wait_until="domcontentloaded", timeout=15_000)
        time.sleep(1)
        el = page.query_selector('a[data-field="website"]')
        if el is None:
            el = page.query_selector(".org-top-card-summary-info-list__info-item a")
        if el is None:
            return _search_company_domain(context, company_name) if company_name else ""
        href = el.get_attribute("href") or ""
        if not href:
            return _search_company_domain(context, company_name) if company_name else ""
        parsed = urlparse(href)
        domain = parsed.netloc.lstrip("www.")
        if _is_useful_domain(domain):
            return domain
        return _search_company_domain(context, company_name) if company_name else ""
    except Exception:
        return _search_company_domain(context, company_name) if company_name else ""
    finally:
        page.close()


def search_people(
    context: BrowserContext,
    criteria: str,
    max_results: int = 100,
) -> list[Profile]:
    profiles: list[Profile] = []
    seen_profile_ids: set[str] = set()
    page_num = 1
    page = context.new_page()

    try:
        while len(profiles) < max_results:
            url = build_people_search_url(criteria, page_num)
            page.goto(url, wait_until="domcontentloaded", timeout=20_000)
            _wait_for_search_results(page)
            time.sleep(1)

            if _is_login_page(page):
                break

            cards = _get_result_cards(page)
            if not cards:
                break

            batch = extract_profiles_from_page(cards)
            if not batch:
                break

            for profile in batch:
                if profile.profile_id in seen_profile_ids:
                    continue
                seen_profile_ids.add(profile.profile_id)
                profiles.append(profile)
                if len(profiles) >= max_results:
                    break

            next_btn = page.query_selector('button[aria-label="Next"]')
            if not next_btn:
                next_btn = page.query_selector("button.artdeco-pagination__button--next")
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
                context,
                f"https://www.linkedin.com/company/{slug}",
                company_name=p.company_name,
            )
            time.sleep(1)

    return profiles[:max_results]
