import json
from typing import Any, Dict, List, Optional, Union

def safe_json_parse(data: Union[str, bytes], default: Any = None) -> Any:
    """Safely parse JSON data with fallback"""
    try:
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        return json.loads(data)
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
        return default

def flatten_dict(data: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten a nested dictionary"""
    items = []
    
    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep).items())
        else:
            items.append((new_key, value))
    
    return dict(items)

def unflatten_dict(data: Dict[str, Any], sep: str = '.') -> Dict[str, Any]:
    """Unflatten a dictionary with dotted keys"""
    result = {}
    
    for key, value in data.items():
        keys = key.split(sep)
        current = result
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    return result

def deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result

def remove_none_values(data: Dict[str, Any], recursive: bool = True) -> Dict[str, Any]:
    """Remove None values from dictionary"""
    cleaned = {}
    
    for key, value in data.items():
        if value is None:
            continue
        elif recursive and isinstance(value, dict):
            cleaned_value = remove_none_values(value, recursive)
            if cleaned_value:  # Only add if not empty
                cleaned[key] = cleaned_value
        elif isinstance(value, list) and recursive:
            cleaned_list = []
            for item in value:
                if item is None:
                    continue
                elif isinstance(item, dict):
                    cleaned_item = remove_none_values(item, recursive)
                    if cleaned_item:  # Only add if not empty
                        cleaned_list.append(cleaned_item)
                else:
                    cleaned_list.append(item)
            if cleaned_list:  # Only add if not empty
                cleaned[key] = cleaned_list
        else:
            cleaned[key] = value
    
    return cleaned

def paginate_results(results: List[Any], page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    """Paginate a list of results"""
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

def chunk_list(data: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks of specified size"""
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

def unique_list(data: List[Any], key_func=None) -> List[Any]:
    """Remove duplicates from list while preserving order"""
    if key_func is None:
        seen = set()
        result = []
        for item in data:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result
    else:
        seen = set()
        result = []
        for item in data:
            key = key_func(item)
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result

def group_by(data: List[Dict[str, Any]], key: str) -> Dict[str, List[Dict[str, Any]]]:
    """Group list of dictionaries by specified key"""
    groups = {}
    
    for item in data:
        group_key = item.get(key)
        if group_key not in groups:
            groups[group_key] = []
        groups[group_key].append(item)
    
    return groups

def sort_by_keys(data: List[Dict[str, Any]], keys: List[str], reverse: bool = False) -> List[Dict[str, Any]]:
    """Sort list of dictionaries by multiple keys"""
    def sort_key(item):
        return tuple(item.get(key) for key in keys)
    
    return sorted(data, key=sort_key, reverse=reverse)

def filter_by_criteria(data: List[Dict[str, Any]], criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Filter list of dictionaries by criteria"""
    filtered = []
    
    for item in data:
        match = True
        for key, value in criteria.items():
            if key not in item or item[key] != value:
                match = False
                break
        if match:
            filtered.append(item)
    
    return filtered