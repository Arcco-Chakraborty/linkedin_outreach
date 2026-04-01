# LinkedIn Scraper v2 — Design Spec
_2026-04-01_

## Goal

Upgrade the LinkedIn scraper to:
1. Remember every profile scraped across all runs (global deduplication)
2. Scale to arbitrarily large `max_results` by expanding search criteria automatically
3. Process each person one at a time (scrape → email → verify → write → next) instead of batch
4. Show a live progress counter + per-person log line in the UI

This lays the groundwork for a future multi-campaign outreach platform.

---

## New File: `src/seen_profiles.py`

A file-backed set of LinkedIn profile IDs persisted across runs.

```
SeenProfiles(path: str)
  ├── _ids: set[str]         — loaded from file on init
  ├── __contains__(id)       — O(1) lookup
  ├── add(id)                — appends to file immediately (crash-safe)
  └── __len__()
```

- Storage format: plain `.txt`, one `profile_id` per line
- Appending line-by-line means partial runs are never lost
- Default path: `data/seen_profiles.txt` (configurable via UI and CLI)
- Shared across all campaigns — a person seen in any run is never re-processed

---

## Scraper Changes: `src/scraper.py`

### `search_people` → `search_people_stream` (generator)

Signature:
```python
def search_people_stream(
    context: BrowserContext,
    criteria: str,
    max_results: int,
    seen_ids: SeenProfiles | set,
) -> Iterator[Profile]
```

Behaviour:
- Builds a `criteria_queue` via `_expand_criteria(criteria)`
- For each criteria in the queue, paginates through LinkedIn search pages
- For each card on each page:
  - Skips if `profile_id` in `seen_ids` (cross-run dedup) or `local_seen` (in-run dedup)
  - Resolves company domain inline (one browser page open/close per profile)
  - `yield Profile`
- Stops when `max_results` reached or all criteria exhausted
- `local_seen: set[str]` — a local set initialised at the start of each `search_people_stream` call, tracks profile IDs yielded in this run
- Two dedup layers prevent the same person appearing twice regardless of how many search terms matched them

### `_expand_criteria(criteria: str) -> list[str]`

Returns `[original] + expansions`. Two expansion strategies:

**1. Known-title synonym map (~20 titles)**

If any word in `criteria` matches a known key (e.g. `founder`, `ceo`, `cto`, `engineer`, `recruiter`), its synonyms are appended. Examples:
- `"co-founder"` → `["cofounder", "co founder", "founder", "startup founder", ...]`
- `"fintech founder"` → original + founder synonyms

**2. Generic suffix expansion (for any criteria)**

Always appended regardless of content:
```
"{criteria} alumni"
"{criteria} graduate"
"{criteria} engineer"
"{criteria} founder"
"{criteria} cto"
"{criteria} developer"
"{criteria} manager"
"{criteria} recruiter"
```

This ensures arbitrary criteria like `"bits pilani"` or `"Y Combinator"` still yield useful result sets beyond LinkedIn's per-query cap.

---

## Pipeline Changes: `src/pipeline.py`

### `run_pipeline` signature update

```python
def run_pipeline(
    profiles: Iterable[Profile],       # was list[Profile]
    context,
    writer: CSVWriter,
    log: Callable[[str], None] | None = None,
    on_profile_done: Callable[[str], None] | None = None,
) -> tuple[int, int, int]
```

- `profiles` is now any iterable — lists still work (backwards compatible)
- After each profile is fully processed and written:
  - Calls `log(f"[{n}] Name @ Company → email (status)")`
  - Calls `on_profile_done(profile_id)` — used to mark profile as seen
- Profile is marked seen **after** full processing, so interrupted runs retry cleanly

---

## Runner Changes: `src/runner.py`

```python
def run_outreach(
    criteria: str,
    max_results: int = 50,
    output_dir: str = "output",
    cookies_file: str = "linkedin_cookies.json",
    seen_profiles_file: str = "data/seen_profiles.txt",
    log: Callable[[str], None] | None = None,
) -> dict
```

Flow:
1. Authenticate (existing)
2. Load `SeenProfiles(seen_profiles_file)` — log how many already seen
3. `profiles_stream = search_people_stream(..., seen_ids=seen)`
4. `run_pipeline(profiles_stream, ..., log=log, on_profile_done=seen.add)`
5. Return same summary dict shape as today

---

## UI Changes: `ui.py`

**New sidebar field:**
```
Seen profiles file    [data/seen_profiles.txt]
```

**Progress display during run:**
```
[12/500] Processing...
  ✓ verified: 7   ✗ rejected: 4   ⚠ skipped: 1
─────────────────────────────────────────────
[12] John Smith @ acme.example → john@acme.example (valid)
[11] Jane Doe @ techcorp.io → no domain
...
```

Counter and log update after each person. Final table and download buttons appear at the end (unchanged).

---

## CLI Changes: `main.py`

One new flag:
```
--seen-profiles-file   PATH   [default: data/seen_profiles.txt]
```

All existing flags unchanged.

---

## What Is Not Changing

- `models.py` — `Profile` and `EmailResult` unchanged
- `smtp_verifier.py` — unchanged
- `email_generator.py` — unchanged
- `email_pattern_detector.py` — unchanged
- `sheets_writer.py` (CSVWriter) — unchanged
- `session.py` — unchanged
- All 72 existing tests — still pass (pipeline accepts iterables, lists are iterables)

---

## Future Extension Points

- `criteria_queue` can be user-supplied (multi-campaign support)
- `SeenProfiles` path can be per-campaign or global depending on use case
- `run_pipeline` callbacks allow future progress WebSocket/SSE streaming
- `_expand_criteria` synonym map can be user-extensible via config file
