import re
import unicodedata
from typing import Optional

from src.models import Profile

PATTERN_ORDER = ["f.l", "fl", "f0.l", "f0l", "f", "l", "l.f", "lf0"]

_PATTERN_FUNCS = {
    "f.l":  lambda f, l: f"{f}.{l}",
    "fl":   lambda f, l: f"{f}{l}",
    "f0.l": lambda f, l: f"{f[0]}.{l}",
    "f0l":  lambda f, l: f"{f[0]}{l}",
    "f":    lambda f, l: f,
    "l":    lambda f, l: l,
    "l.f":  lambda f, l: f"{l}.{f}",
    "lf0":  lambda f, l: f"{l}{f[0]}",
}


def normalize_name(name: str) -> str:
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z]", "", ascii_str.lower())


def generate_emails(profile: Profile, pattern: Optional[str], domain: str) -> list[str]:
    f = normalize_name(profile.first_name)
    l = normalize_name(profile.last_name)

    if not f and not l:
        return []

    f = f or "x"
    l = l or "x"

    if pattern and pattern in _PATTERN_FUNCS:
        local = _PATTERN_FUNCS[pattern](f, l)
        return [f"{local}@{domain}"]

    results = []
    for key in PATTERN_ORDER:
        try:
            local = _PATTERN_FUNCS[key](f, l)
            if local:
                results.append(f"{local}@{domain}")
        except (IndexError, TypeError):
            pass
    return results
