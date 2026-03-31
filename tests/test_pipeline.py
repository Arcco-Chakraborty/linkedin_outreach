from unittest.mock import MagicMock
from src.models import Profile
from src.pipeline import run_pipeline


def _profile(name="Jane Smith", domain="acme.example") -> Profile:
    first, *rest = name.split()
    return Profile(
        full_name=name, first_name=first, last_name=" ".join(rest),
        title="Co-Founder", company_name="Acme", company_domain=domain,
        profile_url=f"https://www.linkedin.com/in/{name.lower().replace(' ','-')}/",
        profile_id=name.lower().replace(" ", "-"),
    )


def test_valid_email_goes_to_write_verified(mocker):
    mocker.patch("src.pipeline.get_domain_pattern", return_value="f.l")
    mocker.patch("src.pipeline.generate_emails", return_value=["jane.smith@acme.example"])
    mocker.patch("src.pipeline.verify_email", return_value="valid")
    mock_writer = MagicMock()

    v, r, s = run_pipeline([_profile()], context=MagicMock(), writer=mock_writer)

    assert v == 1 and r == 0 and s == 0
    mock_writer.write_verified.assert_called_once()
    result = mock_writer.write_verified.call_args[0][0]
    assert result.email == "jane.smith@acme.example"
    assert result.status == "valid"


def test_invalid_email_goes_to_write_rejected(mocker):
    mocker.patch("src.pipeline.get_domain_pattern", return_value="f.l")
    mocker.patch("src.pipeline.generate_emails", return_value=["jane.smith@acme.example"])
    mocker.patch("src.pipeline.verify_email", return_value="invalid")
    mock_writer = MagicMock()

    v, r, s = run_pipeline([_profile()], context=MagicMock(), writer=mock_writer)
    assert v == 0 and r == 1 and s == 0
    mock_writer.write_rejected.assert_called_once()


def test_catch_all_goes_to_write_verified(mocker):
    mocker.patch("src.pipeline.get_domain_pattern", return_value="f.l")
    mocker.patch("src.pipeline.generate_emails", return_value=["jane.smith@acme.example"])
    mocker.patch("src.pipeline.verify_email", return_value="catch-all")
    mock_writer = MagicMock()

    v, r, s = run_pipeline([_profile()], context=MagicMock(), writer=mock_writer)
    assert v == 1 and r == 0 and s == 0
    mock_writer.write_verified.assert_called_once()


def test_no_pattern_uses_brute_force(mocker):
    mocker.patch("src.pipeline.get_domain_pattern", return_value=None)
    all_8 = [f"p{i}@acme.example" for i in range(8)]
    mocker.patch("src.pipeline.generate_emails", return_value=all_8)
    mocker.patch("src.pipeline.verify_first_valid", return_value=("p2@acme.example", "valid"))
    mock_writer = MagicMock()

    v, r, s = run_pipeline([_profile()], context=MagicMock(), writer=mock_writer)
    assert v == 1
    result = mock_writer.write_verified.call_args[0][0]
    assert result.email == "p2@acme.example"


def test_no_emails_generated_goes_to_rejected(mocker):
    mocker.patch("src.pipeline.get_domain_pattern", return_value=None)
    mocker.patch("src.pipeline.generate_emails", return_value=[])
    mock_writer = MagicMock()

    v, r, s = run_pipeline([_profile()], context=MagicMock(), writer=mock_writer)
    assert r == 1
    result = mock_writer.write_rejected.call_args[0][0]
    assert result.status == "no_pattern"


def test_domain_pattern_cached_across_profiles(mocker):
    mock_get_pattern = mocker.patch("src.pipeline.get_domain_pattern", return_value="f.l")
    mocker.patch("src.pipeline.generate_emails", return_value=["x@acme.example"])
    mocker.patch("src.pipeline.verify_email", return_value="valid")
    mock_writer = MagicMock()

    profiles = [_profile(f"Person {i}") for i in range(3)]
    run_pipeline(profiles, context=MagicMock(), writer=mock_writer)
    assert mock_get_pattern.call_count == 1


def test_per_profile_exception_is_skipped(mocker):
    mocker.patch("src.pipeline.get_domain_pattern", side_effect=Exception("scrape failed"))
    mock_writer = MagicMock()

    v, r, s = run_pipeline([_profile()], context=MagicMock(), writer=mock_writer)
    assert s == 1
    mock_writer.write_verified.assert_not_called()
    mock_writer.write_rejected.assert_not_called()
