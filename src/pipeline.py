import sys

from src.apollo_client import lookup_email
from src.models import EmailResult, Profile
from src.sheets_writer import CSVWriter


def run_pipeline(
    profiles: list[Profile],
    context,
    writer: CSVWriter,
) -> tuple[int, int, int]:
    """
    For each profile, look up the email via Apollo and write to CSV.
    Returns (found_count, not_found_count, skipped_count).
    """
    found_count = not_found_count = skipped_count = 0

    for profile in profiles:
        try:
            if not profile.company_domain and not profile.company_name:
                result = EmailResult(profile=profile, email=None, status="no_domain")
                writer.write_rejected(result)
                not_found_count += 1
                continue

            email = lookup_email(
                first_name=profile.first_name,
                last_name=profile.last_name,
                domain=profile.company_domain,
                company=profile.company_name,
            )

            if email:
                result = EmailResult(profile=profile, email=email, status="found")
                writer.write_verified(result)
                found_count += 1
            else:
                result = EmailResult(profile=profile, email=None, status="not_found")
                writer.write_rejected(result)
                not_found_count += 1

        except Exception as exc:
            print(f"[pipeline] Skipping {profile.full_name}: {exc}", file=sys.stderr)
            skipped_count += 1

    return found_count, not_found_count, skipped_count
