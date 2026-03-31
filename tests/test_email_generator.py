from src.models import Profile
from src.email_generator import normalize_name, generate_emails


def _profile(first="Jane", last="Smith", domain="acme.example") -> Profile:
    return Profile(
        full_name=f"{first} {last}", first_name=first, last_name=last,
        title="Co-Founder", company_name="Acme", company_domain=domain,
        profile_url="https://www.linkedin.com/in/jane-smith/",
        profile_id="jane-smith",
    )


def test_normalize_removes_accents():
    assert normalize_name("Héloïse") == "heloise"


def test_normalize_removes_non_alpha():
    assert normalize_name("O'Brien") == "obrien"


def test_normalize_lowercases():
    assert normalize_name("JOHN") == "john"


def test_generate_emails_known_pattern_f_dot_l():
    assert generate_emails(_profile(), pattern="f.l", domain="acme.example") == ["jane.smith@acme.example"]


def test_generate_emails_known_pattern_f0l():
    assert generate_emails(_profile(), pattern="f0l", domain="acme.example") == ["jsmith@acme.example"]


def test_generate_emails_known_pattern_f0_dot_l():
    assert generate_emails(_profile(), pattern="f0.l", domain="acme.example") == ["j.smith@acme.example"]


def test_generate_emails_known_pattern_fl():
    assert generate_emails(_profile(), pattern="fl", domain="acme.example") == ["janesmith@acme.example"]


def test_generate_emails_unknown_pattern_returns_all_8():
    emails = generate_emails(_profile(), pattern=None, domain="acme.example")
    assert len(emails) == 8
    assert "jane.smith@acme.example" in emails
    assert "janesmith@acme.example" in emails
    assert "j.smith@acme.example" in emails
    assert "jsmith@acme.example" in emails
    assert "jane@acme.example" in emails
    assert "smith@acme.example" in emails
    assert "smith.jane@acme.example" in emails
    assert "smithj@acme.example" in emails


def test_generate_emails_strips_accents():
    p = _profile(first="Héloïse", last="Dubois")
    assert generate_emails(p, pattern="f.l", domain="beta-fr.example") == ["heloise.dubois@beta-fr.example"]


def test_generate_emails_empty_when_no_name():
    p = _profile(first="", last="")
    assert generate_emails(p, pattern="f.l", domain="acme.example") == []
