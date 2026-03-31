from unittest.mock import MagicMock
from src.smtp_verifier import verify_email, verify_first_valid


def _mock_smtp(rcpt_side_effects: list):
    smtp_instance = MagicMock()
    smtp_instance.rcpt.side_effect = rcpt_side_effects
    smtp_class = MagicMock()
    smtp_class.return_value.__enter__ = MagicMock(return_value=smtp_instance)
    smtp_class.return_value.__exit__ = MagicMock(return_value=False)
    return smtp_class


def test_verify_email_valid(mocker):
    mocker.patch("src.smtp_verifier._get_mx_host", return_value="mx.acme.example")
    mocker.patch("src.smtp_verifier.smtplib.SMTP",
                 _mock_smtp([(550, b"No such user"), (250, b"OK")]))
    assert verify_email("jane@acme.example", {}) == "valid"


def test_verify_email_invalid(mocker):
    mocker.patch("src.smtp_verifier._get_mx_host", return_value="mx.acme.example")
    mocker.patch("src.smtp_verifier.smtplib.SMTP",
                 _mock_smtp([(550, b"No such user"), (550, b"No such user")]))
    assert verify_email("bad@acme.example", {}) == "invalid"


def test_verify_email_catch_all(mocker):
    mocker.patch("src.smtp_verifier._get_mx_host", return_value="mx.acme.example")
    mocker.patch("src.smtp_verifier.smtplib.SMTP",
                 _mock_smtp([(250, b"OK")]))
    cache = {}
    assert verify_email("jane@acme.example", cache) == "catch-all"
    assert cache["acme.example"] is True


def test_verify_email_uses_catch_all_cache(mocker):
    mock_smtp = mocker.patch("src.smtp_verifier.smtplib.SMTP")
    cache = {"acme.example": True}
    assert verify_email("jane@acme.example", cache) == "catch-all"
    mock_smtp.assert_not_called()


def test_verify_email_blocked_on_connection_error(mocker):
    mocker.patch("src.smtp_verifier._get_mx_host", return_value="mx.acme.example")
    smtp_class = MagicMock()
    smtp_class.return_value.__enter__ = MagicMock(side_effect=ConnectionRefusedError())
    smtp_class.return_value.__exit__ = MagicMock(return_value=False)
    mocker.patch("src.smtp_verifier.smtplib.SMTP", smtp_class)
    assert verify_email("jane@acme.example", {}) == "blocked"


def test_verify_email_blocked_when_mx_lookup_fails(mocker):
    mocker.patch("src.smtp_verifier._get_mx_host", side_effect=Exception("DNS error"))
    assert verify_email("jane@acme.example", {}) == "blocked"


def test_verify_first_valid_returns_first_hit(mocker):
    mocker.patch("src.smtp_verifier._get_mx_host", return_value="mx.acme.example")
    mocker.patch("src.smtp_verifier.smtplib.SMTP",
                 _mock_smtp([(550, b""), (550, b""), (250, b"OK")]))
    email, status = verify_first_valid(["jane.smith@acme.example", "jsmith@acme.example"], {})
    assert email == "jsmith@acme.example"
    assert status == "valid"


def test_verify_first_valid_all_invalid(mocker):
    mocker.patch("src.smtp_verifier._get_mx_host", return_value="mx.acme.example")
    mocker.patch("src.smtp_verifier.smtplib.SMTP",
                 _mock_smtp([(550, b"")] * 9))
    email, status = verify_first_valid(["a@acme.example", "b@acme.example", "c@acme.example"], {})
    assert email is None
    assert status == "invalid"


def test_verify_first_valid_empty_list():
    email, status = verify_first_valid([], {})
    assert email is None
    assert status == "no_pattern"
