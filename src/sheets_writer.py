import csv
import os

from src.models import EmailResult

_VERIFIED_FILE = "verified_leads.csv"
_REJECTED_FILE = "rejected_leads.csv"
_VERIFIED_HEADERS = ["Name", "Email", "Title", "Company", "LinkedIn URL"]
_REJECTED_HEADERS = ["Name", "Title", "Company", "LinkedIn URL", "Reason"]


class CSVWriter:
    def __init__(self, output_dir: str = "."):
        os.makedirs(output_dir, exist_ok=True)
        self._verified_path = os.path.join(output_dir, _VERIFIED_FILE)
        self._rejected_path = os.path.join(output_dir, _REJECTED_FILE)
        self._ensure_headers(self._verified_path, _VERIFIED_HEADERS)
        self._ensure_headers(self._rejected_path, _REJECTED_HEADERS)

    def _ensure_headers(self, path: str, headers: list) -> None:
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            with open(path, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(headers)

    def _append_row(self, path: str, row: list) -> None:
        with open(path, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(row)

    def write_verified(self, result: EmailResult) -> None:
        p = result.profile
        if result.status == "catch-all":
            email_display = f"⚠ unverified (catch-all): {result.email}"
        elif result.status == "blocked":
            email_display = f"⚠ unverified (server blocked): {result.email}"
        else:
            email_display = result.email
        self._append_row(
            self._verified_path,
            [p.full_name, email_display, p.title, p.company_name, p.profile_url],
        )

    def write_rejected(self, result: EmailResult) -> None:
        p = result.profile
        self._append_row(
            self._rejected_path,
            [p.full_name, p.title, p.company_name, p.profile_url, result.status],
        )
