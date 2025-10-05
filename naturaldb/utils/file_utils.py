"""
File utilities for NaturalDB
Handles file operations, locking, and atomic writes.
"""

import os
import shutil
import tempfile
import threading
from pathlib import Path
from contextlib import contextmanager
from typing import Any, Generator


def ensure_directory(path: str) -> None:
    """
    Ensure a directory exists, create it if it doesn't.
    
    Args:
        path: Directory path to ensure exists
    """
    Path(path).mkdir(parents=True, exist_ok=True)


@contextmanager
def safe_file_operation(filepath: str, operation: str = 'r') -> Generator[Any, None, None]:
    """
    Context manager for safe file operations with error handling.
    
    Args:
        filepath: Path to the file
        operation: File operation mode ('r', 'w', 'a', etc.)
    
    Yields:
        File handle
    """
    file_handle = None
    try:
        # Ensure parent directory exists
        parent_dir = os.path.dirname(filepath)
        if parent_dir:
            ensure_directory(parent_dir)
        
        file_handle = open(filepath, operation, encoding='utf-8')
        yield file_handle
    except IOError as e:
        raise IOError(f"File operation failed for {filepath}: {e}")
    finally:
        if file_handle:
            file_handle.close()


def atomic_write(filepath: str, content: str) -> None:
    """
    Atomically write content to a file using a temporary file.
    
    Args:
        filepath: Target file path
        content: Content to write
    """
    parent_dir = os.path.dirname(filepath)
    ensure_directory(parent_dir)
    
    # Create temporary file in the same directory
    with tempfile.NamedTemporaryFile(
        mode='w', 
        encoding='utf-8', 
        dir=parent_dir, 
        delete=False
    ) as temp_file:
        temp_file.write(content)
        temp_filepath = temp_file.name
    
    # Atomically move temp file to target location
    try:
        shutil.move(temp_filepath, filepath)
    except Exception:
        # Clean up temp file if move fails
        try:
            os.unlink(temp_filepath)
        except OSError:
            pass
        raise


# Simple file locking mechanism
_file_locks = {}
_lock_mutex = threading.Lock()


@contextmanager
def file_lock(filepath: str) -> Generator[None, None, None]:
    """
    Simple file locking mechanism for concurrent access control.
    
    Args:
        filepath: Path to the file to lock
    
    Yields:
        None
    """
    with _lock_mutex:
        if filepath not in _file_locks:
            _file_locks[filepath] = threading.Lock()
        lock = _file_locks[filepath]
    
    with lock:
        yield


def file_exists(filepath: str) -> bool:
    """
    Check if a file exists.
    
    Args:
        filepath: Path to check
        
    Returns:
        True if file exists, False otherwise
    """
    return Path(filepath).exists()


def get_file_size(filepath: str) -> int:
    """
    Get file size in bytes.
    
    Args:
        filepath: Path to the file
        
    Returns:
        File size in bytes
    """
    return Path(filepath).stat().st_size if file_exists(filepath) else 0


def list_files_in_directory(directory: str, extension: str | None = None) -> list[str]:
    """
    List all files in a directory, optionally filtered by extension.
    
    Args:
        directory: Directory to scan
        extension: File extension to filter by (e.g., '.json')
        
    Returns:
        List of file paths
    """
    if not os.path.isdir(directory):
        return []
    
    files = []
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            if extension is None or filename.endswith(extension):
                files.append(filepath)
    
    return sorted(files)