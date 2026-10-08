from __future__ import annotations

from src.games.flames import normalize


def validate_name(raw, max_len: int = 30):
    """Return (ok, display_name, error_key)."""
    if not raw:
        return False, "", "empty"
    cleaned = " ".join("".join(c for c in raw if c.isprintable() or c.isspace()).split())
    if not cleaned:
        return False, "", "empty"
    if len(cleaned) > max_len:
        return False, "", "too_long"
    if not any(c.isalpha() for c in normalize(cleaned)):
        return False, "", "no_letters"
    return True, cleaned, None
