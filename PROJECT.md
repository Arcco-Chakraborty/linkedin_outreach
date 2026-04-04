# LinkedIn Outreach Project

Last updated: 2026-04-01

## Maintenance Rule

Whenever this project is changed, `PROJECT.md` should be updated in the same turn so it stays usable as a handoff document for other AI models or humans.

## What This Project Does

This is a local LinkedIn outreach lead-generation tool.

It does four main things:

1. Authenticates to LinkedIn using saved browser cookies.
2. Searches LinkedIn people results for a user-provided criteria such as `co-founder`.
3. Tries to infer company domains and generate likely email addresses.
4. Verifies candidate emails with SMTP heuristics and writes CSV outputs.

There are now two ways to use it:

- CLI flow via `main.py`
- Local UI flow via `ui.py` / `run_ui.py`

## Current State Snapshot

The project has been actively modified in this workspace and is not in a clean git state.

Important recent changes:

- Search parsing was hardened to work with the current LinkedIn people-search layout.
- Headless LinkedIn search was unreliable, so the session now defaults to a visible browser unless overridden.
- Output quality was improved by:
  - preferring better profile links
  - rejecting missing-domain rows instead of generating fake `name@`
  - treating `blocked` SMTP results as rejected rather than verified
  - adding fallback domain lookup from company name via DuckDuckGo
- A Streamlit UI was added.

## Important Files

### Root files

- `main.py`
  CLI entry point. Runs the outreach workflow with command-line flags.

- `ui.py`
  Streamlit UI for running searches and reviewing results in a browser.

- `run_ui.py`
  Small launcher for the Streamlit UI. Chooses a port and runs `ui.py`.

- `requirements.txt`
  Python dependencies. Now includes `streamlit`.

- `.env`
  Local environment file. Contains runtime config such as cookies path and Chrome executable path.
  Treat as local/private.

- `.env.example`
  Minimal example environment file.

- `linkedin_cookies.json`
  Saved LinkedIn session cookies.
  Treat as private/local.

- `pytest.ini`
  Pytest configuration.

- `PROJECT.md`
  This handoff and maintenance document.

### Source files in `src/`

- `src/models.py`
  Defines:
  - `Profile`
  - `EmailResult`

  `EmailResult` controls whether a row goes to verified vs rejected.

- `src/session.py`
  Playwright session management.

  Responsibilities:
  - load and save LinkedIn cookies
  - launch browser context
  - first-run login flow
  - close browser context cleanly

  Important behavior:
  - defaults to visible browser mode for saved-cookie runs
  - supports `LINKEDIN_HEADLESS=true` if explicitly desired

- `src/scraper.py`
  LinkedIn search scraping and company-domain resolution.

  Responsibilities:
  - build LinkedIn people search URL
  - wait for search results
  - parse current result-card layout
  - infer company names from titles like:
    - `Co-Founder @Swiggy`
    - `Co-Founder, Saplings HR`
    - `Founder at Acme`
  - resolve company domains from LinkedIn or fallback web search

  This file contains most of the brittle site-specific logic.

- `src/email_pattern_detector.py`
  Finds likely email naming patterns for a domain.

  Sources used:
  - DuckDuckGo snippets
  - company website pages such as `/contact`, `/about`, `/team`

- `src/email_generator.py`
  Normalizes names and creates candidate email formats.

  Supported patterns include:
  - `f.l`
  - `fl`
  - `f0.l`
  - `f0l`
  - `f`
  - `l`
  - `l.f`
  - `lf0`

- `src/smtp_verifier.py`
  MX lookup and SMTP probing.

  Possible statuses:
  - `valid`
  - `invalid`
  - `catch-all`
  - `blocked`

- `src/sheets_writer.py`
  CSV output writer.

  Writes:
  - `verified_leads.csv`
  - `rejected_leads.csv`

- `src/pipeline.py`
  Main per-profile workflow.

  Flow:
  - check domain
  - detect pattern
  - generate emails
  - verify via SMTP
  - write verified or rejected row

  Additional status used here:
  - `no_domain`
  - `no_pattern`

- `src/runner.py`
  Shared orchestration layer used by both CLI and UI.

  This is the cleanest place to call if another interface gets added later.

### Tests in `tests/`

- `tests/test_scraper.py`
  Covers scraping helpers and parsing logic.

- `tests/test_pipeline.py`
  Covers pipeline behavior and status routing.

- `tests/test_models.py`
  Covers `EmailResult` routing rules.

- `tests/test_session.py`
  Covers cookie save/load and session helper flags.

- `tests/test_email_generator.py`
  Covers normalization and candidate email generation.

- `tests/test_email_pattern_detector.py`
  Covers pattern detection logic.

- `tests/test_sheets_writer.py`
  Covers CSV writing.

- `tests/test_smtp_verifier.py`
  Covers MX/SMTP verification logic.

## Generated / Local-Only Folders

These are local artifacts, not core source:

- `.venv/`
  Local Python virtual environment.

- `__pycache__/`
  Python bytecode caches.

- `.pytest_cache/`
  Pytest cache.

- `.pytest_tmp_run3/`
  Local pytest temp folder. This folder has caused Windows permission issues.

- `.tmp/`
  Temporary local workspace used during testing.

- `output/`
- `output_test/`
- `output_test_clean/`
- `output_test_better/`
- `output_test_final/`
- `output_test_fixed/`

  These are generated CSV output folders from prior runs.

- `streamlit_ui.out.log`
- `streamlit_ui.err.log`

  Local log files from background Streamlit launches.

## Runtime Flow

### CLI path

`main.py` calls `src.runner.run_outreach(...)`

That shared runner:

1. Opens LinkedIn context with cookies.
2. Searches LinkedIn people results.
3. Builds CSV writer.
4. Runs the email pipeline.
5. Closes Playwright context.
6. Returns result counts and CSV row data.

### UI path

`run_ui.py` launches Streamlit, which serves `ui.py`.

`ui.py`:

1. Collects search inputs.
2. Calls `run_outreach(...)`.
3. Streams progress logs in the page.
4. Shows metrics.
5. Shows verified and rejected tables.
6. Offers CSV downloads.

## Output Semantics

### Verified CSV

Written to `verified_leads.csv`.

Currently includes:

- `valid`
- `catch-all`

Notes:

- `catch-all` rows are included because the domain accepts unknown recipients, but they are not as trustworthy as `valid`.

### Rejected CSV

Written to `rejected_leads.csv`.

Currently includes:

- `invalid`
- `no_pattern`
- `blocked`
- `no_domain`

This was changed intentionally so bad or uncertain rows are not mislabeled as verified.

## Commands

### Activate / use the venv

Project path:

```powershell
cd path/to/linkedin_outreach
```

### Run the CLI

```powershell
.venv\Scripts\python main.py --criteria "co-founder" --max-results 25 --output-dir output
```

### Run the UI

Preferred launcher:

```powershell
.venv\Scripts\python run_ui.py
```

Direct Streamlit form:

```powershell
.venv\Scripts\python -m streamlit run ui.py
```

Typical local URL:

```text
http://127.0.0.1:8501
```

If a port is occupied, `run_ui.py` is supposed to choose another free port in the `8501-8600` range.

### Run focused tests

```powershell
.venv\Scripts\python -m pytest tests\test_scraper.py tests\test_pipeline.py tests\test_models.py
```

## Known Working Behavior

The project has been verified to:

- find LinkedIn people results for `co-founder`
- produce both verified and rejected CSV rows
- run from both CLI and UI code paths
- infer some company names and domains successfully

Example recent output:

- `output_test_fixed/verified_leads.csv`
- `output_test_fixed/rejected_leads.csv`

That run produced:

- 2 verified rows
- 3 rejected rows

## Known Problems / Caveats

### 1. LinkedIn scraping is brittle

The scraper depends on LinkedIn DOM behavior and search-page structure.
Future breakage is likely.

### 2. Headless mode is unreliable

LinkedIn search returned empty/minimal content in headless mode in this environment.
That is why visible-browser mode is the default.

### 3. Company/domain inference is still heuristic

Some rows still end up with `no_domain`, especially if:

- the LinkedIn headline does not clearly expose the company
- the LinkedIn company page is hard to guess from the name
- the company website is hard to infer from search results

### 4. SMTP verification is imperfect by nature

Some mail servers:

- block probes
- use catch-all
- behave inconsistently

So even "valid" and "catch-all" are heuristics, not certainty.

### 5. Windows temp and cache permissions are messy in this workspace

Observed issues:

- pytest temp directory permission errors
- `.pyc` file lock issues in `__pycache__`
- some output files/folders staying locked after runs

These are environment issues, not only code issues.

### 6. There are many local generated artifacts in git status

The repo contains:

- cached bytecode
- output folders
- logs
- cookie files

Any cleanup or `.gitignore` improvement should be done carefully.

## Environment Notes

### Expected environment variables

Current usage expects:

- `LINKEDIN_COOKIES_FILE`
- `CHROME_EXECUTABLE`
- optional `LINKEDIN_HEADLESS`

### Chrome / Playwright

Playwright is installed in the venv.
This project also uses a Chrome executable path from `.env`.

## Suggested Next Improvements

If another model continues this project, the highest-leverage next steps are:

1. Improve company extraction by visiting each profile page and reading the current role/company directly.
2. Clean up temp/cache/output artifacts and add/update `.gitignore`.
3. Improve UI polish beyond basic Streamlit tables.
4. Add stronger structured logging and clearer error surfacing in the UI.
5. Add tests around domain fallback search and UI/runner behavior.
6. Consider storing richer run metadata instead of only CSV output.

## Handoff Notes For Other Models

If you are another AI model taking over:

- Start by reading:
  - `PROJECT.md`
  - `main.py`
  - `ui.py`
  - `src/runner.py`
  - `src/scraper.py`
  - `src/pipeline.py`
- Treat `.env` and `linkedin_cookies.json` as sensitive/local.
- Do not assume headless LinkedIn search works.
- Do not trust old output folders as canonical truth; some earlier ones contain bad rows from before fixes.
- Prefer `output_test_fixed/` as the best representative sample of the improved pipeline.
- Update `PROJECT.md` whenever you change behavior, commands, file structure, or known issues.
