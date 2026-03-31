from unittest.mock import MagicMock
from src.scraper import extract_profile_id, extract_profiles_from_page, resolve_company_domain


def test_extract_profile_id_standard():
    assert extract_profile_id("https://www.linkedin.com/in/jane-smith-123/") == "jane-smith-123"


def test_extract_profile_id_no_trailing_slash():
    assert extract_profile_id("https://www.linkedin.com/in/bob-jones") == "bob-jones"


def test_extract_profile_id_non_profile_url():
    assert extract_profile_id("https://www.linkedin.com/company/acme") == ""


def _mock_el(text: str) -> MagicMock:
    el = MagicMock()
    el.inner_text.return_value = text
    el.get_attribute.return_value = text
    return el


def test_extract_profiles_from_page_parses_card():
    card = MagicMock()
    card.query_selector.side_effect = lambda sel: {
        'a[href*="/in/"]': _mock_el("https://www.linkedin.com/in/jane-smith-123/"),
        ".entity-result__title-text": _mock_el("Jane Smith"),
        ".entity-result__primary-subtitle": _mock_el("Co-Founder at Acme Inc"),
        ".entity-result__secondary-subtitle": _mock_el("Acme Inc"),
    }.get(sel)

    profiles = extract_profiles_from_page([card])
    assert len(profiles) == 1
    p = profiles[0]
    assert p.full_name == "Jane Smith"
    assert p.first_name == "Jane"
    assert p.last_name == "Smith"
    assert p.profile_id == "jane-smith-123"
    assert p.title == "Co-Founder at Acme Inc"
    assert p.company_name == "Acme Inc"


def test_extract_profiles_skips_card_without_profile_link():
    card = MagicMock()
    card.query_selector.return_value = None
    profiles = extract_profiles_from_page([card])
    assert profiles == []


def test_resolve_company_domain_found():
    page = MagicMock()
    el = MagicMock()
    el.get_attribute.return_value = "https://www.acme.example/about"
    page.query_selector.return_value = el
    context = MagicMock()
    context.new_page.return_value = page

    domain = resolve_company_domain(context, "https://www.linkedin.com/company/acme")
    assert domain == "acme.example"


def test_resolve_company_domain_not_found():
    page = MagicMock()
    page.query_selector.return_value = None
    context = MagicMock()
    context.new_page.return_value = page

    domain = resolve_company_domain(context, "https://www.linkedin.com/company/acme")
    assert domain == ""
