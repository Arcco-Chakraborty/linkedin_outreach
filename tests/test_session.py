import os

from src.session import save_cookies, load_cookies


def test_save_and_load_roundtrip(tmp_path):
    cookies = [
        {"name": "li_at", "value": "abc123", "domain": ".linkedin.com"},
        {"name": "JSESSIONID", "value": "xyz", "domain": ".linkedin.com"},
    ]
    path = str(tmp_path / "cookies.json")
    save_cookies(cookies, path)
    assert load_cookies(path) == cookies


def test_load_returns_none_when_missing(tmp_path):
    assert load_cookies(str(tmp_path / "nope.json")) is None


def test_headless_env_defaults_off(mocker):
    mocker.patch.dict(os.environ, {}, clear=True)
    from src.session import _env_flag

    assert _env_flag("LINKEDIN_HEADLESS", default=False) is False


def test_headless_env_reads_true(mocker):
    mocker.patch.dict(os.environ, {"LINKEDIN_HEADLESS": "true"}, clear=True)
    from src.session import _env_flag

    assert _env_flag("LINKEDIN_HEADLESS", default=False) is True
