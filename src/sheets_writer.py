import gspread
from google.oauth2.service_account import Credentials

from src.models import EmailResult

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
_VERIFIED_SHEET = "Verified Leads"
_REJECTED_SHEET = "Rejected Leads"
_VERIFIED_HEADERS = ["Name", "Email", "Title", "Company", "LinkedIn URL"]
_REJECTED_HEADERS = ["Name", "Title", "Company", "LinkedIn URL", "Reason"]


def build_gspread_client(service_account_json_path: str) -> gspread.Client:
    creds = Credentials.from_service_account_file(service_account_json_path, scopes=_SCOPES)
    return gspread.authorize(creds)


class SheetsWriter:
    def __init__(self, gc: gspread.Client, spreadsheet_name: str):
        sheet = gc.open(spreadsheet_name)
        self._verified_ws = sheet.worksheet(_VERIFIED_SHEET)
        self._rejected_ws = sheet.worksheet(_REJECTED_SHEET)
        self._ensure_headers(self._verified_ws, _VERIFIED_HEADERS)
        self._ensure_headers(self._rejected_ws, _REJECTED_HEADERS)

    def _ensure_headers(self, ws, headers: list) -> None:
        if not ws.row_values(1):
            ws.append_row(headers)

    def write_verified(self, result: EmailResult) -> None:
        p = result.profile
        if result.status == "catch-all":
            email_display = f"⚠ unverified (catch-all): {result.email}"
        elif result.status == "blocked":
            email_display = f"⚠ unverified (server blocked): {result.email}"
        else:
            email_display = result.email
        self._verified_ws.append_row(
            [p.full_name, email_display, p.title, p.company_name, p.profile_url],
            value_input_option="USER_ENTERED",
        )

    def write_rejected(self, result: EmailResult) -> None:
        p = result.profile
        self._rejected_ws.append_row(
            [p.full_name, p.title, p.company_name, p.profile_url, result.status],
            value_input_option="USER_ENTERED",
        )
