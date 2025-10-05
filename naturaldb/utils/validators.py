"""
Validation utilities for NaturalDB
Handles validation of user inputs, collection names, record IDs, etc.
"""

import re
from typing import Any


def validate_collection_name(name: str) -> bool:
    """
    Validate collection name.
    
    Rules:
    - Must be a non-empty string
    - Can contain letters, numbers, underscores, and hyphens
    - Must start with a letter or underscore
    - Must be between 1 and 64 characters
    
    Args:
        name: Collection name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(name, str) or not name:
        return False
    
    if len(name) > 64:
        return False
    
    # Must start with letter or underscore, followed by letters, numbers, underscores, or hyphens
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_-]*$'
    return bool(re.match(pattern, name))


def validate_record_id(record_id: Any) -> bool:
    """
    Validate record ID.
    
    Rules:
    - Can be string or integer
    - If string, must be non-empty and contain only alphanumeric characters, underscores, or hyphens
    - If integer, must be positive
    - String length must be between 1 and 100 characters
    
    Args:
        record_id: Record ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if isinstance(record_id, int):
        return record_id > 0
    
    if isinstance(record_id, str):
        if not record_id or len(record_id) > 100:
            return False
        
        # Allow alphanumeric characters, underscores, and hyphens
        pattern = r'^[a-zA-Z0-9_-]+$'
        return bool(re.match(pattern, record_id))
    
    return False


def validate_user_id(user_id: str) -> bool:
    """
    Validate user ID.
    
    Rules:
    - Must be a non-empty string
    - Can contain letters, numbers, underscores, hyphens, and dots
    - Must start with a letter or underscore
    - Must be between 1 and 50 characters
    
    Args:
        user_id: User ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(user_id, str) or not user_id:
        return False
    
    if len(user_id) > 50:
        return False
    
    # Must start with letter or underscore, followed by letters, numbers, underscores, hyphens, or dots
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_.-]*$'
    return bool(re.match(pattern, user_id))


def validate_json_data(data: Any) -> bool:
    """
    Validate that data is a valid JSON-serializable structure.
    
    Args:
        data: Data to validate
        
    Returns:
        True if data is JSON-serializable, False otherwise
    """
    try:
        _check_json_serializable(data)
        return True
    except (TypeError, ValueError):
        return False


def _check_json_serializable(obj: Any) -> None:
    """
    Recursively check if an object is JSON-serializable.
    
    Args:
        obj: Object to check
        
    Raises:
        TypeError: If object is not JSON-serializable
    """
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return
    elif isinstance(obj, list):
        for item in obj:
            _check_json_serializable(item)
    elif isinstance(obj, dict):
        for key, value in obj.items():
            if not isinstance(key, str):
                raise TypeError(f"Dictionary keys must be strings, got {type(key).__name__}")
            _check_json_serializable(value)
    else:
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def validate_query_params(params: dict[str, Any]) -> tuple[bool, str]:
    """
    Validate query parameters.
    
    Args:
        params: Query parameters to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(params, dict):
        return False, "Query parameters must be a dictionary"
    
    # Check for reserved parameter names
    reserved_names = {'__internal__', '__system__', '__meta__'}
    for key in params.keys():
        if not isinstance(key, str):
            return False, f"Parameter key must be string, got {type(key).__name__}"
        
        if key in reserved_names:
            return False, f"Parameter key '{key}' is reserved"
        
        if key.startswith('__') and key.endswith('__'):
            return False, f"Parameter key '{key}' uses reserved naming pattern"
    
    return True, ""


def validate_field_name(field_name: str) -> bool:
    """
    Validate field name for queries and operations.
    
    Rules:
    - Must be a non-empty string
    - Can contain letters, numbers, underscores, and dots (for nested fields)
    - Must start with a letter or underscore
    - Must be between 1 and 100 characters
    
    Args:
        field_name: Field name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(field_name, str) or not field_name:
        return False
    
    if len(field_name) > 100:
        return False
    
    # Allow letters, numbers, underscores, and dots
    # Must start with letter or underscore
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_.]*$'
    return bool(re.match(pattern, field_name))


def validate_operation_type(operation: str) -> bool:
    """
    Validate operation type.
    
    Args:
        operation: Operation type to validate
        
    Returns:
        True if valid, False otherwise
    """
    valid_operations = {
        'create', 'read', 'update', 'delete',
        'find', 'filter', 'project', 'group', 'aggregate', 'join',
        'count', 'distinct', 'sort', 'limit', 'skip'
    }
    
    return isinstance(operation, str) and operation.lower() in valid_operations


def sanitize_input(value: str, max_length: int = 1000) -> str:
    """
    Sanitize string input by removing potentially harmful characters.
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return str(value)
    
    # Truncate if too long
    if len(value) > max_length:
        value = value[:max_length]
    
    # Remove null bytes and control characters (except common whitespace)
    sanitized = ''.join(char for char in value 
                       if ord(char) >= 32 or char in '\t\n\r')
    
    return sanitized.strip()