import re
from typing import Optional


def is_valid_email(email: str) -> bool:
    """Validate email format using regex."""
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(email_pattern, email))


def is_strong_password(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength.
    Returns (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"

    return True, None


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """Sanitize string input by stripping whitespace and optionally truncating."""
    sanitized = value.strip()
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    return sanitized


def normalize_email(email: str) -> str:
    """Normalize email to lowercase."""
    return email.strip().lower()


# Additional validators for future use


def format_phone_number(phone: str) -> Optional[str]:
    """Format phone number to a consistent format."""
    digits = re.sub(r"\D", "", phone)

    if len(digits) == 10:
        return f"+1{digits}"
    elif len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    elif len(digits) > 10:
        return f"+{digits}"

    return None


def is_valid_uuid(uuid_string: str) -> bool:
    """Validate UUID format."""
    uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    return bool(re.match(uuid_pattern, uuid_string.lower()))


def is_valid_language_code(code: str) -> bool:
    """Validate ISO 639-1 language code format."""
    return bool(re.match(r"^[a-z]{2}$", code.lower()))


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to specified length with suffix."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix
