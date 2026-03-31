import smtplib
from typing import Optional

import dns.resolver

_CATCH_ALL_PROBE_LOCAL = "xyz9q8w7e-definitely-invalid"
_INVALID_CODES = {550, 551, 553, 554}


def _get_mx_host(domain: str) -> str:
    records = dns.resolver.resolve(domain, "MX")
    best = min(records, key=lambda r: r.preference)
    return str(best.exchange).rstrip(".")


def verify_email(email: str, catch_all_cache: dict) -> str:
    """
    Probe a single email address via SMTP.
    Returns: "valid" | "invalid" | "catch-all" | "blocked"
    """
    domain = email.split("@")[1]

    if catch_all_cache.get(domain):
        return "catch-all"

    try:
        mx_host = _get_mx_host(domain)
    except Exception:
        return "blocked"

    try:
        with smtplib.SMTP(mx_host, 25, timeout=10) as smtp:
            smtp.ehlo("probe.local")
            smtp.mail("probe@probe.local")

            code, _ = smtp.rcpt(f"{_CATCH_ALL_PROBE_LOCAL}@{domain}")
            if code == 250:
                catch_all_cache[domain] = True
                return "catch-all"

            code, _ = smtp.rcpt(email)
            if code == 250:
                return "valid"
            elif code in _INVALID_CODES:
                return "invalid"
            else:
                return "blocked"
    except Exception:
        return "blocked"


def verify_first_valid(
    emails: list[str],
    catch_all_cache: dict,
) -> tuple[Optional[str], str]:
    """
    Probe multiple candidate emails in one SMTP session.
    Returns (matched_email, status).
    """
    if not emails:
        return None, "no_pattern"

    domain = emails[0].split("@")[1]

    if catch_all_cache.get(domain):
        return emails[0], "catch-all"

    try:
        mx_host = _get_mx_host(domain)
    except Exception:
        return emails[0], "blocked"

    try:
        with smtplib.SMTP(mx_host, 25, timeout=10) as smtp:
            smtp.ehlo("probe.local")
            smtp.mail("probe@probe.local")

            code, _ = smtp.rcpt(f"{_CATCH_ALL_PROBE_LOCAL}@{domain}")
            if code == 250:
                catch_all_cache[domain] = True
                return emails[0], "catch-all"

            for email in emails:
                code, _ = smtp.rcpt(email)
                if code == 250:
                    return email, "valid"

            return None, "invalid"
    except Exception:
        return emails[0], "blocked"
