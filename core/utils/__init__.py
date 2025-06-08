"""
Core Utilities

Provides organized utility functions for common operations across the application.
"""

# Validation utilities
from .validation_utils import (
    is_valid_email,
    is_strong_password,
    sanitize_input,
    validate_url,
    validate_phone_number,
    is_safe_filename,
    validate_json_string
)

# Datetime utilities
from .datetime_utils import (
    utc_now,
    format_datetime,
    parse_datetime,
    time_ago,
    to_iso_string,
    from_iso_string,
    start_of_day,
    end_of_day,
    add_business_days,
    is_business_day,
    get_timezone_offset,
    calculate_duration,
    calculate_age
)

# String utilities
from .string_utils import (
    clean_string,
    normalize_unicode,
    slugify,
    truncate_text,
    extract_keywords,
    normalize_search_text,
    camel_to_snake,
    snake_to_camel,
    mask_string,
    is_empty_or_whitespace
)

# Data utilities
from .data_utils import (
    safe_json_parse,
    flatten_dict,
    unflatten_dict,
    deep_merge,
    remove_none_values,
    paginate_results,
    chunk_list,
    unique_list,
    group_by,
    sort_by_keys,
    filter_by_criteria
)

__all__ = [
    # Validation
    'is_valid_email',
    'is_strong_password',
    'sanitize_input',
    'validate_url',
    'validate_phone_number',
    'is_safe_filename',
    'validate_json_string',
    
    # Datetime
    'utc_now',
    'format_datetime',
    'parse_datetime',
    'time_ago',
    'to_iso_string',
    'from_iso_string',
    'start_of_day',
    'end_of_day',
    'add_business_days',
    'is_business_day',
    'get_timezone_offset',
    'calculate_duration',
    'calculate_age',
    
    # String
    'clean_string',
    'normalize_unicode',
    'slugify',
    'truncate_text',
    'extract_keywords',
    'normalize_search_text',
    'camel_to_snake',
    'snake_to_camel',
    'mask_string',
    'is_empty_or_whitespace',
    
    # Data
    'safe_json_parse',
    'flatten_dict',
    'unflatten_dict',
    'deep_merge',
    'remove_none_values',
    'paginate_results',
    'chunk_list',
    'unique_list',
    'group_by',
    'sort_by_keys',
    'filter_by_criteria'
]