import csv
from src.models import Profile, EmailResult
from src.sheets_writer import CSVWriter


def _result(status="valid", email="jane@acme.example") -> EmailResult:
    p = Profile(
        full_name="Jane Smith", first_name="Jane", last_name="Smith",
        title="Co-Founder", company_name="Acme Inc", company_domain="acme.example",
        profile_url="https://www.linkedin.com/in/jane-smith/",
        profile_id="jane-smith",
    )
    return EmailResult(profile=p, email=email, status=status)


def _read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


def test_writer_creates_files_with_headers(tmp_path):
    CSVWriter(output_dir=str(tmp_path))
    verified = _read_csv(tmp_path / "verified_leads.csv")
    rejected = _read_csv(tmp_path / "rejected_leads.csv")
    assert verified[0] == ["Name", "Email", "Title", "Company", "LinkedIn URL"]
    assert rejected[0] == ["Name", "Title", "Company", "LinkedIn URL", "Reason"]


def test_writer_skips_headers_when_files_already_exist(tmp_path):
    CSVWriter(output_dir=str(tmp_path))
    CSVWriter(output_dir=str(tmp_path))  # second init on same dir
    verified = _read_csv(tmp_path / "verified_leads.csv")
    assert verified.count(["Name", "Email", "Title", "Company", "LinkedIn URL"]) == 1


def test_write_verified_appends_correct_row(tmp_path):
    writer = CSVWriter(output_dir=str(tmp_path))
    writer.write_verified(_result(status="valid", email="jane@acme.example"))
    rows = _read_csv(tmp_path / "verified_leads.csv")
    assert rows[1] == ["Jane Smith", "jane@acme.example", "Co-Founder", "Acme Inc",
                       "https://www.linkedin.com/in/jane-smith/"]


def test_write_verified_formats_catch_all_email(tmp_path):
    writer = CSVWriter(output_dir=str(tmp_path))
    writer.write_verified(_result(status="catch-all", email="jane@acme.example"))
    rows = _read_csv(tmp_path / "verified_leads.csv")
    assert rows[1][1] == "⚠ unverified (catch-all): jane@acme.example"


def test_write_verified_formats_blocked_email(tmp_path):
    writer = CSVWriter(output_dir=str(tmp_path))
    writer.write_verified(_result(status="blocked", email="jane@acme.example"))
    rows = _read_csv(tmp_path / "verified_leads.csv")
    assert rows[1][1] == "⚠ unverified (server blocked): jane@acme.example"


def test_write_rejected_appends_correct_row(tmp_path):
    writer = CSVWriter(output_dir=str(tmp_path))
    writer.write_rejected(_result(status="invalid", email=None))
    rows = _read_csv(tmp_path / "rejected_leads.csv")
    assert rows[1] == ["Jane Smith", "Co-Founder", "Acme Inc",
                       "https://www.linkedin.com/in/jane-smith/", "invalid"]
