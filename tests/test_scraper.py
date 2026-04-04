from unittest.mock import MagicMock
from src.scraper import (
    build_people_search_url,
    extract_profile_id,
    extract_profiles_from_page,
    _infer_company_name_from_title,
    resolve_company_domain,
)


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


def test_extract_profiles_uses_link_text_when_name_element_missing():
    card = MagicMock()
    link = _mock_el("Jane Smith")
    link.get_attribute.return_value = "https://www.linkedin.com/in/jane-smith-123/"
    card.query_selector.side_effect = lambda sel: {
        'a[href*="/in/"]': link,
        ".entity-result__primary-subtitle": _mock_el("Founder"),
        ".entity-result__secondary-subtitle": _mock_el("Acme Inc"),
    }.get(sel)

    profiles = extract_profiles_from_page([card])
    assert len(profiles) == 1
    assert profiles[0].full_name == "Jane Smith"
    assert profiles[0].profile_id == "jane-smith-123"


def test_extract_profiles_falls_back_to_card_text():
    card = MagicMock()
    link = _mock_el("")
    link.get_attribute.return_value = "https://www.linkedin.com/in/jane-smith-123/"
    card.query_selector.side_effect = lambda sel: {
        'a[href*="/in/"]': link,
    }.get(sel)
    card.inner_text.return_value = "\n".join([
        "Jane Smith",
        "View Jane Smith's profile",
        "3rd+ degree connection",
        "Co-Founder @Acme Inc | GTM",
        "Delhi, India",
        "Follow",
    ])

    profiles = extract_profiles_from_page([card])
    assert len(profiles) == 1
    assert profiles[0].full_name == "Jane Smith"
    assert profiles[0].title == "Co-Founder @Acme Inc | GTM"
    assert profiles[0].company_name == "Acme Inc"


def test_extract_profiles_ignores_status_link_and_uses_real_name_link():
    card = MagicMock()
    avatar_link = _mock_el("Status is reachable")
    avatar_link.get_attribute.return_value = "https://www.linkedin.com/in/jane-smith-123?miniProfileUrn=123"
    name_link = _mock_el("Jane Smith\nView Jane Smith's profile")
    name_link.get_attribute.return_value = "https://www.linkedin.com/in/jane-smith-123?miniProfileUrn=123"

    def query_selector(sel):
        mapping = {
            ".entity-result__primary-subtitle": _mock_el("Co-Founder @Acme Inc"),
        }
        return mapping.get(sel)

    card.query_selector.side_effect = query_selector
    card.query_selector_all.side_effect = lambda sel: [avatar_link, name_link] if sel == 'a[href*="/in/"]' else []
    card.inner_text.return_value = "\n".join([
        "Status is reachable",
        "Jane Smith",
        "View Jane Smith's profile",
        "Co-Founder @Acme Inc",
    ])

    profiles = extract_profiles_from_page([card])
    assert len(profiles) == 1
    assert profiles[0].full_name == "Jane Smith"


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


def test_build_people_search_url_encodes_criteria():
    url = build_people_search_url("co founder & ceo", 3)
    assert "keywords=co+founder+%26+ceo" in url
    assert "page=3" in url


def test_infer_company_name_from_title_at():
    assert _infer_company_name_from_title("Co-Founder at Acme Inc") == "Acme Inc"


def test_infer_company_name_from_title_at_symbol():
    assert _infer_company_name_from_title("Co-Founder @Swiggy | Growth") == "Swiggy"


def test_infer_company_name_from_title_comma():
    assert _infer_company_name_from_title("Co-Founder, Saplings HR") == "Saplings HR"
