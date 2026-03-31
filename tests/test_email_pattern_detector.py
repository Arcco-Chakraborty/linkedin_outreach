from unittest.mock import MagicMock
from src.email_pattern_detector import (
    classify_local_part,
    detect_pattern,
    collect_emails_from_duckduckgo,
    collect_emails_from_website,
    get_domain_pattern,
)


def test_classify_dot_with_initial():
    assert classify_local_part("j.doe") == "f0.l"


def test_classify_dot_with_full_name():
    assert classify_local_part("john.doe") == "f.l"


def test_classify_no_dot_short():
    assert classify_local_part("john") == "f"


def test_classify_no_dot_long():
    assert classify_local_part("johndoe") == "fl"


def test_classify_returns_none_for_numeric():
    assert classify_local_part("info123") is None


def test_detect_pattern_votes_correctly():
    local_parts = ["john.doe", "jane.smith", "mike.jones", "j.test"]
    assert detect_pattern(local_parts) == "f.l"


def test_detect_pattern_returns_none_when_empty():
    assert detect_pattern([]) is None


def _snippet_el(text: str) -> MagicMock:
    el = MagicMock()
    el.inner_text.return_value = text
    return el


def test_collect_emails_from_duckduckgo(mocker):
    page = MagicMock()
    page.query_selector_all.return_value = [
        _snippet_el("Contact john.doe@acme.example for info"),
        _snippet_el("Reach jane.smith@acme.example at HQ"),
    ]
    context = MagicMock()
    context.new_page.return_value = page

    emails = collect_emails_from_duckduckgo(context, "acme.example")
    assert "john.doe" in emails
    assert "jane.smith" in emails


def test_collect_emails_returns_empty_on_exception():
    context = MagicMock()
    context.new_page.side_effect = Exception("Network error")
    emails = collect_emails_from_duckduckgo(context, "acme.example")
    assert emails == []


def test_collect_emails_from_website(mocker):
    page = MagicMock()
    page.inner_text.return_value = "Email us at hello@beta-io.example or support@beta-io.example"
    context = MagicMock()
    context.new_page.return_value = page

    emails = collect_emails_from_website(context, "beta-io.example")
    assert "hello" in emails
    assert "support" in emails


def test_get_domain_pattern_uses_duckduckgo_first(mocker):
    mocker.patch(
        "src.email_pattern_detector.collect_emails_from_duckduckgo",
        return_value=["john.doe", "jane.smith", "bob.jones"],
    )
    mock_website = mocker.patch("src.email_pattern_detector.collect_emails_from_website")

    pattern = get_domain_pattern(MagicMock(), "acme.example")
    assert pattern == "f.l"
    mock_website.assert_not_called()


def test_get_domain_pattern_falls_back_to_website(mocker):
    mocker.patch(
        "src.email_pattern_detector.collect_emails_from_duckduckgo",
        return_value=["john.doe"],
    )
    mocker.patch(
        "src.email_pattern_detector.collect_emails_from_website",
        return_value=["jane.smith", "bob.jones"],
    )
    pattern = get_domain_pattern(MagicMock(), "acme.example")
    assert pattern == "f.l"


def test_get_domain_pattern_returns_none_when_no_emails(mocker):
    mocker.patch("src.email_pattern_detector.collect_emails_from_duckduckgo", return_value=[])
    mocker.patch("src.email_pattern_detector.collect_emails_from_website", return_value=[])
    assert get_domain_pattern(MagicMock(), "acme.example") is None
