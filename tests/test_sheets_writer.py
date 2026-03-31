from unittest.mock import MagicMock
from src.models import Profile, EmailResult
from src.sheets_writer import SheetsWriter


def _result(status="valid", email="jane@acme.example") -> EmailResult:
    p = Profile(
        full_name="Jane Smith", first_name="Jane", last_name="Smith",
        title="Co-Founder", company_name="Acme Inc", company_domain="acme.example",
        profile_url="https://www.linkedin.com/in/jane-smith/",
        profile_id="jane-smith",
    )
    return EmailResult(profile=p, email=email, status=status)


def _make_writer(empty_sheet=True):
    mock_gc = MagicMock()
    mock_spreadsheet = MagicMock()
    mock_gc.open.return_value = mock_spreadsheet
    mock_verified_ws = MagicMock()
    mock_rejected_ws = MagicMock()
    mock_verified_ws.row_values.return_value = [] if empty_sheet else ["Name"]
    mock_rejected_ws.row_values.return_value = [] if empty_sheet else ["Name"]
    mock_spreadsheet.worksheet.side_effect = lambda name: {
        "Verified Leads": mock_verified_ws,
        "Rejected Leads": mock_rejected_ws,
    }[name]
    writer = SheetsWriter(gc=mock_gc, spreadsheet_name="My Leads")
    return writer, mock_verified_ws, mock_rejected_ws


def test_writer_adds_headers_to_empty_sheet():
    writer, verified_ws, rejected_ws = _make_writer(empty_sheet=True)
    verified_ws.append_row.assert_called_once_with(
        ["Name", "Email", "Title", "Company", "LinkedIn URL"]
    )
    rejected_ws.append_row.assert_called_once_with(
        ["Name", "Title", "Company", "LinkedIn URL", "Reason"]
    )


def test_writer_skips_headers_when_already_present():
    writer, verified_ws, rejected_ws = _make_writer(empty_sheet=False)
    verified_ws.append_row.assert_not_called()
    rejected_ws.append_row.assert_not_called()


def test_write_verified_appends_correct_row():
    writer, verified_ws, _ = _make_writer(empty_sheet=False)
    writer.write_verified(_result(status="valid", email="jane@acme.example"))
    verified_ws.append_row.assert_called_once_with(
        ["Jane Smith", "jane@acme.example", "Co-Founder", "Acme Inc",
         "https://www.linkedin.com/in/jane-smith/"],
        value_input_option="USER_ENTERED",
    )


def test_write_verified_formats_catch_all_email():
    writer, verified_ws, _ = _make_writer(empty_sheet=False)
    writer.write_verified(_result(status="catch-all", email="jane@acme.example"))
    row = verified_ws.append_row.call_args[0][0]
    assert row[1] == "⚠ unverified (catch-all): jane@acme.example"


def test_write_verified_formats_blocked_email():
    writer, verified_ws, _ = _make_writer(empty_sheet=False)
    writer.write_verified(_result(status="blocked", email="jane@acme.example"))
    row = verified_ws.append_row.call_args[0][0]
    assert row[1] == "⚠ unverified (server blocked): jane@acme.example"


def test_write_rejected_appends_correct_row():
    writer, _, rejected_ws = _make_writer(empty_sheet=False)
    writer.write_rejected(_result(status="invalid", email=None))
    rejected_ws.append_row.assert_called_once_with(
        ["Jane Smith", "Co-Founder", "Acme Inc",
         "https://www.linkedin.com/in/jane-smith/", "invalid"],
        value_input_option="USER_ENTERED",
    )
