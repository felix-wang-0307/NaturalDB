"""
Path utilities for NaturalDB
Handles path construction and sanitization for the storage system.
"""

import os
import re
from pathlib import Path
from typing import Union


# Default base data directory
DEFAULT_DATA_DIR = "data"


def sanitize_path_component(component: str) -> str:
    """
    Sanitize a path component to prevent directory traversal attacks.
    
    Args:
        component: Path component to sanitize
        
    Returns:
        Sanitized path component
    """
    if not isinstance(component, str):
        component = str(component)
    
    # Remove dangerous characters and patterns
    # Allow only alphanumeric, underscore, hyphen, and dot
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', component)
    
    # Remove leading/trailing dots and underscores
    sanitized = sanitized.strip('._')
    
    # Ensure it's not empty after sanitization
    if not sanitized:
        sanitized = "unnamed"
    
    # Prevent reserved names
    reserved_names = {
        'con', 'prn', 'aux', 'nul',
        'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8', 'com9',
        'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'
    }
    
    if sanitized.lower() in reserved_names:
        sanitized = f"_{sanitized}_"
    
    return sanitized


def sanitize_path(path: str) -> str:
    """
    Sanitize a full path to prevent directory traversal attacks.
    
    Args:
        path: Path to sanitize
        
    Returns:
        Sanitized path
    """
    if not isinstance(path, str):
        path = str(path)
    
    # Split path into components and sanitize each
    components = path.split(os.sep)
    sanitized_components = [sanitize_path_component(comp) for comp in components if comp]
    
    return os.sep.join(sanitized_components)


def build_user_path(base_dir: str | None = None, user_id: str | None = None) -> str:
    """
    Build path to user's data directory.
    
    Args:
        base_dir: Base data directory (defaults to DEFAULT_DATA_DIR)
        user_id: User ID (defaults to 'default')
        
    Returns:
        Absolute path to user directory
    """
    if base_dir is None:
        base_dir = DEFAULT_DATA_DIR
    
    if user_id is None:
        user_id = 'default'
    
    sanitized_user_id = sanitize_path_component(user_id)
    user_path = os.path.join(base_dir, sanitized_user_id)
    
    return os.path.abspath(user_path)


def build_collection_path(base_dir: str | None = None, user_id: str | None = None, collection: str | None = None) -> str:
    """
    Build path to a collection directory.
    
    Args:
        base_dir: Base data directory
        user_id: User ID
        collection: Collection name
        
    Returns:
        Absolute path to collection directory
    """
    if collection is None:
        raise ValueError("Collection name is required")
    
    user_path = build_user_path(base_dir, user_id)
    sanitized_collection = sanitize_path_component(collection)
    collection_path = os.path.join(user_path, sanitized_collection)
    
    return os.path.abspath(collection_path)


def build_record_path(base_dir: str | None = None, user_id: str | None = None, 
                     collection: str | None = None, record_id: Union[str, int] | None = None) -> str:
    """
    Build path to a specific record file.
    
    Args:
        base_dir: Base data directory
        user_id: User ID
        collection: Collection name
        record_id: Record ID
        
    Returns:
        Absolute path to record file
    """
    if record_id is None:
        raise ValueError("Record ID is required")
    
    collection_path = build_collection_path(base_dir, user_id, collection)
    sanitized_record_id = sanitize_path_component(str(record_id))
    record_filename = f"{sanitized_record_id}.json"
    record_path = os.path.join(collection_path, record_filename)
    
    return os.path.abspath(record_path)


def extract_record_id_from_filename(filename: str) -> str:
    """
    Extract record ID from a JSON filename.
    
    Args:
        filename: Filename (e.g., "123.json")
        
    Returns:
        Record ID as string
    """
    if filename.endswith('.json'):
        return filename[:-5]  # Remove .json extension
    return filename


def get_collection_name_from_path(collection_path: str) -> str:
    """
    Extract collection name from collection path.
    
    Args:
        collection_path: Path to collection directory
        
    Returns:
        Collection name
    """
    return os.path.basename(os.path.normpath(collection_path))


def get_user_id_from_path(user_path: str) -> str:
    """
    Extract user ID from user path.
    
    Args:
        user_path: Path to user directory
        
    Returns:
        User ID
    """
    return os.path.basename(os.path.normpath(user_path))


def ensure_path_within_base(path: str, base_dir: str) -> bool:
    """
    Ensure that a path is within the base directory (prevent directory traversal).
    
    Args:
        path: Path to check
        base_dir: Base directory that should contain the path
        
    Returns:
        True if path is within base directory, False otherwise
    """
    try:
        # Resolve both paths to absolute paths
        abs_path = os.path.abspath(path)
        abs_base = os.path.abspath(base_dir)
        
        # Check if the path starts with the base directory
        return abs_path.startswith(abs_base)
    except (OSError, ValueError):
        return False


def get_relative_path(full_path: str, base_dir: str) -> str:
    """
    Get relative path from base directory.
    
    Args:
        full_path: Full path
        base_dir: Base directory
        
    Returns:
        Relative path from base directory
    """
    try:
        return os.path.relpath(full_path, base_dir)
    except ValueError:
        # Paths are on different drives (Windows)
        return full_path


def list_collections(base_dir: str | None = None, user_id: str | None = None) -> list[str]:
    """
    List all collections for a user.
    
    Args:
        base_dir: Base data directory
        user_id: User ID
        
    Returns:
        List of collection names
    """
    user_path = build_user_path(base_dir, user_id)
    
    if not os.path.exists(user_path):
        return []
    
    collections = []
    try:
        for item in os.listdir(user_path):
            item_path = os.path.join(user_path, item)
            if os.path.isdir(item_path):
                collections.append(item)
    except OSError:
        return []
    
    return sorted(collections)


def list_records(base_dir: str | None = None, user_id: str | None = None, collection: str | None = None) -> list[str]:
    """
    List all record IDs in a collection.
    
    Args:
        base_dir: Base data directory
        user_id: User ID
        collection: Collection name
        
    Returns:
        List of record IDs
    """
    if collection is None:
        return []
    
    collection_path = build_collection_path(base_dir, user_id, collection)
    
    if not os.path.exists(collection_path):
        return []
    
    record_ids = []
    try:
        for item in os.listdir(collection_path):
            if item.endswith('.json'):
                record_id = extract_record_id_from_filename(item)
                record_ids.append(record_id)
    except OSError:
        return []
    
    return sorted(record_ids)


def create_path_hierarchy(path: str) -> None:
    """
    Create directory hierarchy for a given path.
    
    Args:
        path: Path to create (can be file or directory)
    """
    if os.path.isfile(path) or path.endswith('.json'):
        # It's a file path, create parent directories
        parent_dir = os.path.dirname(path)
        if parent_dir:
            Path(parent_dir).mkdir(parents=True, exist_ok=True)
    else:
        # It's a directory path
        Path(path).mkdir(parents=True, exist_ok=True)