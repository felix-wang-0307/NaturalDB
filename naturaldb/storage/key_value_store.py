"""
Key-Value store implementation for NaturalDB
Provides a higher-level interface over the file storage.
"""

from typing import Any, Dict, List, Optional, Union
from .file_storage import FileStorage
from ..utils.json_utils import JsonValue
from ..exceptions import StorageError, ValidationError, handle_exception


class KeyValueStore:
    """High-level key-value store interface."""
    
    def __init__(self, storage: FileStorage):
        """
        Initialize key-value store.
        
        Args:
            storage: Underlying storage implementation
        """
        self.storage = storage
    
    @handle_exception
    def put(self, collection: str, key: str, value: JsonValue) -> bool:
        """
        Store a key-value pair.
        
        Args:
            collection: Collection name
            key: Key
            value: Value to store
            
        Returns:
            True if successful
        """
        return self.storage.create_record(collection, key, value)
    
    @handle_exception
    def get(self, collection: str, key: str) -> Optional[JsonValue]:
        """
        Retrieve a value by key.
        
        Args:
            collection: Collection name
            key: Key
            
        Returns:
            Value if found, None otherwise
        """
        return self.storage.read_record(collection, key)
    
    @handle_exception
    def update(self, collection: str, key: str, value: JsonValue) -> bool:
        """
        Update a key-value pair.
        
        Args:
            collection: Collection name
            key: Key
            value: New value
            
        Returns:
            True if successful
        """
        return self.storage.update_record(collection, key, value)
    
    @handle_exception
    def delete(self, collection: str, key: str) -> bool:
        """
        Delete a key-value pair.
        
        Args:
            collection: Collection name
            key: Key
            
        Returns:
            True if successful
        """
        return self.storage.delete_record(collection, key)
    
    def exists(self, collection: str, key: str) -> bool:
        """
        Check if a key exists.
        
        Args:
            collection: Collection name
            key: Key
            
        Returns:
            True if key exists
        """
        return self.storage.record_exists(collection, key)
    
    def keys(self, collection: str) -> List[str]:
        """
        Get all keys in a collection.
        
        Args:
            collection: Collection name
            
        Returns:
            List of keys
        """
        return self.storage.list_records(collection)
    
    @handle_exception
    def put_many(self, collection: str, items: Dict[str, JsonValue]) -> Dict[str, bool]:
        """
        Store multiple key-value pairs.
        
        Args:
            collection: Collection name
            items: Dictionary of key-value pairs
            
        Returns:
            Dictionary mapping keys to success status
        """
        return self.storage.batch_create(collection, items)
    
    @handle_exception
    def get_many(self, collection: str, keys: List[str]) -> Dict[str, Optional[JsonValue]]:
        """
        Retrieve multiple values by keys.
        
        Args:
            collection: Collection name
            keys: List of keys
            
        Returns:
            Dictionary mapping keys to values
        """
        return self.storage.batch_read(collection, keys)
    
    @handle_exception
    def delete_many(self, collection: str, keys: List[str]) -> Dict[str, bool]:
        """
        Delete multiple key-value pairs.
        
        Args:
            collection: Collection name
            keys: List of keys
            
        Returns:
            Dictionary mapping keys to success status
        """
        return self.storage.batch_delete(collection, keys)
    
    def clear_collection(self, collection: str) -> bool:
        """
        Clear all key-value pairs from a collection.
        
        Args:
            collection: Collection name
            
        Returns:
            True if successful
        """
        keys = self.keys(collection)
        if not keys:
            return True
        
        results = self.delete_many(collection, keys)
        return all(results.values())
    
    def size(self, collection: str) -> int:
        """
        Get the number of key-value pairs in a collection.
        
        Args:
            collection: Collection name
            
        Returns:
            Number of pairs
        """
        return len(self.keys(collection))
    
    def is_empty(self, collection: str) -> bool:
        """
        Check if a collection is empty.
        
        Args:
            collection: Collection name
            
        Returns:
            True if collection is empty
        """
        return self.size(collection) == 0