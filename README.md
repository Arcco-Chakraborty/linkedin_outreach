# LinkedIn Outreach

A local CLI and Streamlit interface for finding people and looking up contact
emails through Apollo. Configuration, browser sessions and generated results stay
on your own machine.

## Setup

Use Python 3.12 or later:

```shell
python -m venv .venv
# Activate .venv using your platform's command, then:
pip install -r requirements.txt
python -m playwright install chromium
```

Copy `.env.example` to `.env`. Supply your own Apollo keys in `APOLLO_API_KEYS`
(comma-separated); leaving it empty disables Apollo lookups. Optionally set
`CHROME_EXECUTABLE` to an installed Chrome executable. Default browser behavior
is visible; `LINKEDIN_HEADLESS=true` changes subsequent saved-session launches.

Leave `linkedin_cookies.json` absent for the first run. The app opens LinkedIn
for manual sign-in and saves the resulting session locally. The committed
`linkedin_cookies.example.json` is an empty placeholder for reference; do not
copy it to the runtime filename because an empty existing cookie file skips
the first-run sign-in flow.

## Run

```shell
python main.py --criteria "co-founder" --max-results 25 --output-dir output
python run_ui.py
```

Results go to local verified/rejected CSV files. Current lookups use Apollo;
SMTP/email-pattern helpers remain in the code for separate use. Records in
`examples/` use invented names, reserved example domains and placeholder profile
links; they are demonstrations, not verified contacts.

## Development

```shell
python -m pytest
python tools/check_public_history.py
```

The historical pipeline tests target an earlier SMTP workflow and currently fail
against the Apollo pipeline; see `docs/HANDOFF.md`. Other tests mock external
services. Public history checks cover all reachable refs, generated/private file
paths and contact examples. Real configuration, cookies, lead exports, logs and
Python caches are ignored. Keep any custom output directories local as well.
