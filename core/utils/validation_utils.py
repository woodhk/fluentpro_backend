import re
from typing import Optional
from email_validator import validate_email, EmailNotValidError

def is_valid_email(email: str) -> bool:
    """Validate email format using email-validator library"""
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False

def is_strong_password(password: str) -> tuple[bool, Optional[str]]:
    """Check password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character"
    
    return True, None

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input"""
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32)
    
    # Truncate to max length
    text = text[:max_length]
    
    # Remove multiple spaces
    text = ' '.join(text.split())
    
    return text.strip()

def validate_url(url: str) -> bool:
    """Validate URL format"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(url_pattern.match(url))

def validate_phone_number(phone: str) -> bool:
    """Validate phone number format (basic validation)"""
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Check if it has 10-15 digits (international format)
    return 10 <= len(digits) <= 15

def is_safe_filename(filename: str) -> bool:
    """Check if filename is safe for storage"""
    # Check for dangerous characters
    dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
    return not any(char in filename for char in dangerous_chars)

def validate_json_string(json_str: str) -> bool:
    """Validate if string is valid JSON"""
    import json
    try:
        json.loads(json_str)
        return True
    except (json.JSONDecodeError, TypeError):
        return False