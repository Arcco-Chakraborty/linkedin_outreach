import csv
import os
from typing import Callable

from src.pipeline import run_pipeline
from src.scraper import search_people
from src.session import close_authenticated_context, get_authenticated_context
from src.sheets_writer import CSVWriter


def _read_csv_rows(path: str) -> list[dict[str, str]]:
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def run_outreach(
    criteria: str,
    max_results: int = 50,
    output_dir: str = "output",
    cookies_file: str = "linkedin_cookies.json",
    log: Callable[[str], None] | None = None,
) -> dict:
    logger = log or (lambda _: None)

    logger(f"[1/4] Authenticating with LinkedIn (cookies: {cookies_file})...")
    context = get_authenticated_context(cookies_file)

    try:
        logger(f"[2/4] Searching LinkedIn for '{criteria}' (max {max_results})...")
        profiles = search_people(context, criteria=criteria, max_results=max_results)
        if not profiles:
            return {
                "profiles_found": 0,
                "verified": 0,
                "rejected": 0,
                "skipped": 0,
                "verified_path": os.path.join(output_dir, "verified_leads.csv"),
                "rejected_path": os.path.join(output_dir, "rejected_leads.csv"),
                "verified_rows": [],
                "rejected_rows": [],
            }

        logger(f"      Found {len(profiles)} profiles.")
        logger(f"[3/4] Preparing output directory: '{output_dir}'...")
        writer = CSVWriter(output_dir=output_dir)

        logger("[4/4] Finding and verifying emails (this may take a few minutes)...")
        verified, rejected, skipped = run_pipeline(
            profiles=profiles,
            context=context,
            writer=writer,
        )

        verified_path = os.path.join(output_dir, "verified_leads.csv")
        rejected_path = os.path.join(output_dir, "rejected_leads.csv")
        return {
            "profiles_found": len(profiles),
            "verified": verified,
            "rejected": rejected,
            "skipped": skipped,
            "verified_path": verified_path,
            "rejected_path": rejected_path,
            "verified_rows": _read_csv_rows(verified_path),
            "rejected_rows": _read_csv_rows(rejected_path),
        }
    finally:
        close_authenticated_context(context)
