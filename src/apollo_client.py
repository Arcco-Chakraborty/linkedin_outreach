import os

import requests
from dotenv import load_dotenv

load_dotenv()

APOLLO_API_URL = "https://api.apollo.io/v1/people/match"

_keys: list[str] = [k.strip() for k in os.getenv("APOLLO_API_KEYS", "").split(",") if k.strip()]
_key_index = 0


def _get_next_key() -> str | None:
    global _key_index
    if not _keys:
        return None
    key = _keys[_key_index % len(_keys)]
    _key_index += 1
    return key


def lookup_email(
    first_name: str,
    last_name: str,
    domain: str = "",
    company: str = "",
) -> str | None:
    """
    Call Apollo people/match and return the email string, or None if not found.
    Rotates keys on 429/401. Raises on network errors or if all keys are exhausted.
    """
    if not _keys:
        return None

    payload: dict = {"first_name": first_name, "last_name": last_name}
    if domain:
        payload["domain"] = domain
    if company:
        payload["organization_name"] = company

    tried: set[str] = set()
    last_err: Exception | None = None

    for _ in range(len(_keys)):
        api_key = _get_next_key()
        if not api_key or api_key in tried:
            continue
        tried.add(api_key)

        try:
            resp = requests.post(
                APOLLO_API_URL,
                json=payload,
                headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
                timeout=10,
            )

            if resp.status_code == 429:
                last_err = Exception("apollo: rate limited")
                continue

            if resp.status_code == 401:
                last_err = Exception("apollo: invalid API key")
                continue

            resp.raise_for_status()

            person = (resp.json() or {}).get("person") or {}
            email = (person.get("email") or "").strip().lower()
            return email if email else None

        except requests.RequestException as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status in (429, 401):
                last_err = exc
                continue
            raise

    raise last_err or Exception("apollo: all keys exhausted")
