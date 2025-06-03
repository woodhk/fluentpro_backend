"""
Shared utility functions for the FluentPro Backend application.
"""

import re
import json
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


def clean_string(value: str, max_length: Optional[int] = None) -> str:
    """
    Clean and sanitize a string value.
    
    Args:
        value: String to clean
        max_length: Maximum length to truncate to
        
    Returns:
        str: Cleaned string
    """
    if not isinstance(value, str):
        return str(value)
    
    cleaned = value.strip()
    
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length].strip()
    
    return cleaned


def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if email is valid
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate password strength according to FluentPro requirements.
    
    Args:
        password: Password to validate
        
    Returns:
        Dict containing validation results
    """
    result = {
        'is_valid': True,
        'errors': []
    }
    
    if len(password) < 8:
        result['errors'].append("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        result['errors'].append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        result['errors'].append("Password must contain at least one lowercase letter")
    
    if not re.search(r'[0-9]', password):
        result['errors'].append("Password must contain at least one number")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        result['errors'].append("Password must contain at least one special character")
    
    result['is_valid'] = len(result['errors']) == 0
    
    return result


def calculate_age(date_of_birth: Union[str, date]) -> int:
    """
    Calculate age from date of birth.
    
    Args:
        date_of_birth: Date of birth as string (YYYY-MM-DD) or date object
        
    Returns:
        int: Age in years
    """
    if isinstance(date_of_birth, str):
        dob = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
    else:
        dob = date_of_birth
    
    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    
    return age


def format_response_data(data: Any, exclude_fields: Optional[List[str]] = None) -> Any:
    """
    Format data for API response, removing sensitive or unnecessary fields.
    
    Args:
        data: Data to format
        exclude_fields: List of field names to exclude
        
    Returns:
        Formatted data
    """
    if exclude_fields is None:
        exclude_fields = ['password', 'secret', 'private_key', 'auth0_id']
    
    if isinstance(data, dict):
        return {
            key: format_response_data(value, exclude_fields)
            for key, value in data.items()
            if key not in exclude_fields
        }
    elif isinstance(data, list):
        return [format_response_data(item, exclude_fields) for item in data]
    else:
        return data


def generate_search_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """
    Generate search keywords from text.
    
    Args:
        text: Text to extract keywords from
        max_keywords: Maximum number of keywords to return
        
    Returns:
        List of keywords
    """
    if not text:
        return []
    
    # Convert to lowercase and remove special characters
    clean_text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
    
    # Split into words and filter
    words = clean_text.split()
    
    # Remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
        'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could',
        'may', 'might', 'must', 'shall', 'can', 'this', 'that', 'these', 'those'
    }
    
    keywords = [
        word for word in words 
        if len(word) > 2 and word not in stop_words
    ]
    
    # Remove duplicates while preserving order
    unique_keywords = []
    seen = set()
    for keyword in keywords:
        if keyword not in seen:
            unique_keywords.append(keyword)
            seen.add(keyword)
    
    return unique_keywords[:max_keywords]


def convert_to_iso_datetime(dt: Union[str, datetime]) -> Optional[str]:
    """
    Convert datetime to ISO format string.
    
    Args:
        dt: Datetime as string or datetime object
        
    Returns:
        ISO formatted datetime string or None if conversion fails
    """
    try:
        if isinstance(dt, str):
            # Try to parse common formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                try:
                    parsed_dt = datetime.strptime(dt, fmt)
                    return parsed_dt.isoformat()
                except ValueError:
                    continue
            return None
        elif isinstance(dt, datetime):
            return dt.isoformat()
        else:
            return None
    except Exception as e:
        logger.warning(f"Failed to convert datetime to ISO format: {str(e)}")
        return None


def safe_json_parse(data: Union[str, bytes], default: Any = None) -> Any:
    """
    Safely parse JSON data with fallback.
    
    Args:
        data: JSON string or bytes to parse
        default: Default value to return if parsing fails
        
    Returns:
        Parsed JSON data or default value
    """
    try:
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        return json.loads(data)
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
        return default


def flatten_dict(data: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    Flatten a nested dictionary.
    
    Args:
        data: Dictionary to flatten
        parent_key: Parent key prefix
        sep: Separator for nested keys
        
    Returns:
        Flattened dictionary
    """
    items = []
    
    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep).items())
        else:
            items.append((new_key, value))
    
    return dict(items)


def normalize_search_text(text: str) -> str:
    """
    Normalize text for search operations.
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    normalized = text.lower()
    
    # Remove extra whitespace
    normalized = ' '.join(normalized.split())
    
    # Remove special characters but keep spaces and alphanumeric
    normalized = re.sub(r'[^a-z0-9\s]', ' ', normalized)
    
    # Remove extra spaces again
    normalized = ' '.join(normalized.split())
    
    return normalized


def paginate_results(
    results: List[Any], 
    page: int = 1, 
    page_size: int = 20
) -> Dict[str, Any]:
    """
    Paginate a list of results.
    
    Args:
        results: List of results to paginate
        page: Page number (1-based)
        page_size: Number of items per page
        
    Returns:
        Dictionary with pagination info and paginated results
    """
    total_count = len(results)
    total_pages = (total_count + page_size - 1) // page_size
    
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    
    paginated_results = results[start_index:end_index]
    
    return {
        'results': paginated_results,
        'pagination': {
            'current_page': page,
            'page_size': page_size,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_previous': page > 1
        }
    }


def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mask sensitive data in dictionary for logging.
    
    Args:
        data: Dictionary that may contain sensitive data
        
    Returns:
        Dictionary with sensitive fields masked
    """
    sensitive_fields = {
        'password', 'secret', 'key', 'token', 'auth', 'credential',
        'private', 'confidential', 'ssn', 'social_security'
    }
    
    masked_data = {}
    
    for key, value in data.items():
        key_lower = key.lower()
        
        # Check if key contains sensitive terms
        is_sensitive = any(term in key_lower for term in sensitive_fields)
        
        if is_sensitive:
            masked_data[key] = "***MASKED***"
        elif isinstance(value, dict):
            masked_data[key] = mask_sensitive_data(value)
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            masked_data[key] = [mask_sensitive_data(item) for item in value]
        else:
            masked_data[key] = value
    
    return masked_data


def get_client_ip(request) -> str:
    """
    Get client IP address from request.
    
    Args:
        request: Django request object
        
    Returns:
        Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    return ip or 'unknown'