from src.models import Profile, EmailResult


def _profile(first="Jane", last="Smith", domain="acme.example") -> Profile:
    return Profile(
        full_name=f"{first} {last}",
        first_name=first,
        last_name=last,
        title="Co-Founder",
        company_name="Acme Inc",
        company_domain=domain,
        profile_url=f"https://www.linkedin.com/in/{first.lower()}-{last.lower()}/",
        profile_id=f"{first.lower()}-{last.lower()}",
    )


def test_profile_fields():
    p = _profile()
    assert p.full_name == "Jane Smith"
    assert p.first_name == "Jane"
    assert p.company_domain == "acme.example"
    assert p.profile_id == "jane-smith"


def test_email_result_valid_goes_to_verified():
    r = EmailResult(profile=_profile(), email="jane@acme.example", status="valid")
    assert r.goes_to_verified is True
    assert r.goes_to_rejected is False


def test_email_result_catch_all_goes_to_verified():
    r = EmailResult(profile=_profile(), email="jane@acme.example", status="catch-all")
    assert r.goes_to_verified is True
    assert r.goes_to_rejected is False


def test_email_result_blocked_goes_to_verified():
    r = EmailResult(profile=_profile(), email="jane@acme.example", status="blocked")
    assert r.goes_to_verified is False
    assert r.goes_to_rejected is True


def test_email_result_invalid_goes_to_rejected():
    r = EmailResult(profile=_profile(), email=None, status="invalid")
    assert r.goes_to_verified is False
    assert r.goes_to_rejected is True


def test_email_result_no_pattern_goes_to_rejected():
    r = EmailResult(profile=_profile(), email=None, status="no_pattern")
    assert r.goes_to_verified is False
    assert r.goes_to_rejected is True


def test_email_result_no_domain_goes_to_rejected():
    r = EmailResult(profile=_profile(domain=""), email=None, status="no_domain")
    assert r.goes_to_verified is False
    assert r.goes_to_rejected is True
