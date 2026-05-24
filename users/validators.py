# users/validators.py
import re
from urllib.parse import urlparse

from django.core.exceptions import ValidationError

from users.constants import GITHUB_HOSTNAMES, PHONE_REGEX_PATTERN


PHONE_RE = re.compile(PHONE_REGEX_PATTERN)


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 11 and digits.startswith("8"):
        digits = f"7{digits[1:]}"
    if len(digits) == 11 and digits.startswith("7"):
        normalized = f"+{digits}"
        if PHONE_RE.match(normalized):
            return normalized
    raise ValidationError("Введите номер в формате +7XXXXXXXXXX или 8XXXXXXXXXX.")


def validate_github_url(value: str) -> None:
    if not value:
        return
    parsed = urlparse(value)
    hostname = (parsed.hostname or "").lower()
    if hostname not in GITHUB_HOSTNAMES:
        raise ValidationError("Укажите ссылку на github.com.")