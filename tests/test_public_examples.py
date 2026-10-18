"""Validate safe setup references and ignored private runtime files."""
import csv
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_configuration_and_cookie_examples_have_no_credentials():
    assert json.loads((ROOT / "linkedin_cookies.example.json").read_text()) == []
    lines = (ROOT / ".env.example").read_text().splitlines()
    settings = dict(line.split("=", 1) for line in lines if line and not line.startswith("#"))
    assert settings["APOLLO_API_KEYS"] == ""
    assert settings["CHROME_EXECUTABLE"] == ""
    assert settings["LINKEDIN_COOKIES_FILE"] == "linkedin_cookies.json"
    assert not (ROOT / "linkedin_cookies.json").exists()


def test_csv_examples_are_synthetic_and_match_export_schema():
    for filename, headers in (
        ("verified_leads.csv", ["Name", "Email", "Title", "Company", "LinkedIn URL"]),
        ("rejected_leads.csv", ["Name", "Title", "Company", "LinkedIn URL", "Reason"]),
    ):
        with (ROOT / "examples" / filename).open(newline="") as handle:
            reader = csv.DictReader(handle)
            assert reader.fieldnames == headers
            records = list(reader)
        assert records
        for row in records:
            assert row["Name"] in {"Example Person", "Sample Person"}
            assert "placeholder" in row["LinkedIn URL"]
            if row.get("Email"):
                assert row["Email"].endswith(".example")


def test_git_ignores_private_runtime_files_but_keeps_examples():
    private = [".env", ".env.local", "linkedin_cookies.json", "custom_cookies.json",
               "service_account.json", "output/verified_leads.csv", "custom-results.csv",
               "streamlit_ui.err.log", "src/__pycache__/module.pyc.123", "data/seen_profiles.txt"]
    proc = subprocess.run(["git", "-C", str(ROOT), "check-ignore", "--no-index", "--stdin", "-z"],
                          input=("\0".join(private) + "\0").encode(), capture_output=True, check=True)
    assert set(proc.stdout.decode().split("\0")) - {""} == set(private)
    public = [".env.example", "linkedin_cookies.example.json", "examples/verified_leads.csv"]
    proc = subprocess.run(["git", "-C", str(ROOT), "check-ignore", "--no-index", "--stdin", "-z"],
                          input=("\0".join(public) + "\0").encode(), capture_output=True)
    assert proc.returncode == 1
    assert not proc.stdout
