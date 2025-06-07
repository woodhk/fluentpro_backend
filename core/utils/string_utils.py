import re
import unicodedata
from typing import List, Optional

def clean_string(value: str, max_length: Optional[int] = None) -> str:
    """Clean and sanitize a string value"""
    if not isinstance(value, str):
        return str(value)
    
    cleaned = value.strip()
    
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length].strip()
    
    return cleaned

def normalize_unicode(text: str) -> str:
    """Normalize unicode text for consistent processing"""
    return unicodedata.normalize('NFKC', text)

def slugify(text: str, max_length: int = 50) -> str:
    """Convert text to URL-friendly slug"""
    # Normalize unicode
    text = normalize_unicode(text)
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace spaces and special characters with hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    
    # Remove leading/trailing hyphens
    text = text.strip('-')
    
    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length].rstrip('-')
    
    return text

def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to specified length with suffix"""
    if len(text) <= max_length:
        return text
    
    truncated_length = max_length - len(suffix)
    return text[:truncated_length] + suffix

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Extract keywords from text"""
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

def normalize_search_text(text: str) -> str:
    """Normalize text for search operations"""
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

def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def snake_to_camel(name: str, capitalize_first: bool = False) -> str:
    """Convert snake_case to camelCase"""
    components = name.split('_')
    if capitalize_first:
        return ''.join(word.capitalize() for word in components)
    else:
        return components[0] + ''.join(word.capitalize() for word in components[1:])

def mask_string(text: str, visible_chars: int = 4, mask_char: str = '*') -> str:
    """Mask string showing only specified number of characters"""
    if len(text) <= visible_chars:
        return mask_char * len(text)
    
    return text[:visible_chars] + mask_char * (len(text) - visible_chars)

def is_empty_or_whitespace(text: str) -> bool:
    """Check if string is empty or contains only whitespace"""
    return not text or text.strip() == ''