from dataclasses import dataclass
from typing import Optional


@dataclass
class Profile:
    full_name: str
    first_name: str
    last_name: str
    title: str
    company_name: str
    company_domain: str
    profile_url: str
    profile_id: str


@dataclass
class EmailResult:
    profile: Profile
    email: Optional[str]
    status: str  # "valid" | "invalid" | "catch-all" | "blocked" | "no_pattern" | "no_domain"

    @property
    def goes_to_verified(self) -> bool:
        return self.status in ("valid", "catch-all")

    @property
    def goes_to_rejected(self) -> bool:
        return self.status in ("invalid", "no_pattern", "blocked", "no_domain")
