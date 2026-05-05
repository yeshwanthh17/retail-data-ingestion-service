import re
from typing import Optional


WHITESPACE_RE = re.compile(r"\s+")
PHONE_RE = re.compile(r"^\+?[0-9][0-9\-\s]{6,31}$")


def normalize_whitespace(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value.strip())


def normalize_lookup_value(value: str) -> str:
    return normalize_whitespace(value)


def canonical_key(value: str) -> str:
    return normalize_lookup_value(value).casefold()


def coerce_optional_string(value: Optional[str]) -> str:
    if value is None:
        return ""
    return normalize_whitespace(str(value)) if str(value).strip() else ""


def is_valid_phone_number(value: str) -> bool:
    return bool(PHONE_RE.fullmatch(value))
