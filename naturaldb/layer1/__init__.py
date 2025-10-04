"""
Layer 1: Storage System

This layer implements the file-based key-value store with:
- File-level locking mechanisms
- CRUD operations on JSON files
- Table management (directories)
- Transaction safety through file locks
"""

from .storage import Storage
from .locks import LockManager, FileLock
from .errors import (
    StorageError, TableNotFoundError, RecordNotFoundError,
    LockError, LockTimeoutError, DeadlockDetectedError
)

__all__ = [
    'Storage',
    'LockManager', 
    'FileLock',
    'StorageError',
    'TableNotFoundError', 
    'RecordNotFoundError',
    'LockError',
    'LockTimeoutError', 
    'DeadlockDetectedError'
]