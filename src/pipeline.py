import sys

from src.email_generator import generate_emails
from src.email_pattern_detector import get_domain_pattern
from src.models import EmailResult, Profile
from src.sheets_writer import SheetsWriter
from src.smtp_verifier import verify_email, verify_first_valid


def run_pipeline(
    profiles: list[Profile],
    context,
    writer: SheetsWriter,
) -> tuple[int, int, int]:
    """
    Process each profile: pattern detect → generate → SMTP verify → write.
    Returns (verified_count, rejected_count, skipped_count).
    """
    verified_count = rejected_count = skipped_count = 0
    pattern_cache: dict = {}
    catch_all_cache: dict = {}

    for profile in profiles:
        try:
            domain = profile.company_domain

            if domain not in pattern_cache:
                pattern_cache[domain] = get_domain_pattern(context, domain)
            pattern = pattern_cache[domain]

            emails = generate_emails(profile, pattern=pattern, domain=domain)

            if not emails:
                result = EmailResult(profile=profile, email=None, status="no_pattern")
                writer.write_rejected(result)
                rejected_count += 1
                continue

            if len(emails) == 1:
                status = verify_email(emails[0], catch_all_cache)
                email = emails[0]
            else:
                email, status = verify_first_valid(emails, catch_all_cache)

            result = EmailResult(profile=profile, email=email, status=status)

            if result.goes_to_verified:
                writer.write_verified(result)
                verified_count += 1
            else:
                writer.write_rejected(result)
                rejected_count += 1

        except Exception as exc:
            print(f"[pipeline] Skipping {profile.full_name}: {exc}", file=sys.stderr)
            skipped_count += 1

    return verified_count, rejected_count, skipped_count
