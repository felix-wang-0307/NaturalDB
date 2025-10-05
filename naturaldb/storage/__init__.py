"""
Storage layer for NaturalDB
Implements file-based key-value storage with JSON records.
"""

from .base_storage import BaseStorage
from .file_storage import FileStorage
from .key_value_store import KeyValueStore
from .collection_manager import CollectionManager

__all__ = [
    'BaseStorage',
    'FileStorage', 
    'KeyValueStore',
    'CollectionManager'
]