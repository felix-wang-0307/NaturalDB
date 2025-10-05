"""
Base storage interface for NaturalDB
Defines the abstract interface for storage implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from ..utils.json_utils import JsonValue


class BaseStorage(ABC):
    """Abstract base class for storage implementations."""
    
    @abstractmethod
    def connect(self, **kwargs) -> None:
        """
        Connect to the storage backend.
        
        Args:
            **kwargs: Storage-specific connection parameters
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the storage backend."""
        pass
    
    @abstractmethod
    def create_record(self, collection: str, record_id: str, data: JsonValue) -> bool:
        """
        Create a new record in the specified collection.
        
        Args:
            collection: Collection name
            record_id: Unique record identifier
            data: Record data
            
        Returns:
            True if record was created successfully
            
        Raises:
            StorageError: If record creation fails
        """
        pass
    
    @abstractmethod
    def read_record(self, collection: str, record_id: str) -> Optional[JsonValue]:
        """
        Read a record from the specified collection.
        
        Args:
            collection: Collection name
            record_id: Record identifier
            
        Returns:
            Record data if found, None otherwise
            
        Raises:
            StorageError: If record reading fails
        """
        pass
    
    @abstractmethod
    def update_record(self, collection: str, record_id: str, data: JsonValue) -> bool:
        """
        Update an existing record in the specified collection.
        
        Args:
            collection: Collection name
            record_id: Record identifier
            data: Updated record data
            
        Returns:
            True if record was updated successfully
            
        Raises:
            StorageError: If record update fails
        """
        pass
    
    @abstractmethod
    def delete_record(self, collection: str, record_id: str) -> bool:
        """
        Delete a record from the specified collection.
        
        Args:
            collection: Collection name
            record_id: Record identifier
            
        Returns:
            True if record was deleted successfully
            
        Raises:
            StorageError: If record deletion fails
        """
        pass
    
    @abstractmethod
    def list_records(self, collection: str) -> List[str]:
        """
        List all record IDs in the specified collection.
        
        Args:
            collection: Collection name
            
        Returns:
            List of record IDs
            
        Raises:
            StorageError: If listing fails
        """
        pass
    
    @abstractmethod
    def record_exists(self, collection: str, record_id: str) -> bool:
        """
        Check if a record exists in the specified collection.
        
        Args:
            collection: Collection name
            record_id: Record identifier
            
        Returns:
            True if record exists, False otherwise
        """
        pass
    
    @abstractmethod
    def create_collection(self, collection: str) -> bool:
        """
        Create a new collection.
        
        Args:
            collection: Collection name
            
        Returns:
            True if collection was created successfully
            
        Raises:
            StorageError: If collection creation fails
        """
        pass
    
    @abstractmethod
    def delete_collection(self, collection: str) -> bool:
        """
        Delete a collection and all its records.
        
        Args:
            collection: Collection name
            
        Returns:
            True if collection was deleted successfully
            
        Raises:
            StorageError: If collection deletion fails
        """
        pass
    
    @abstractmethod
    def list_collections(self) -> List[str]:
        """
        List all collections.
        
        Returns:
            List of collection names
            
        Raises:
            StorageError: If listing fails
        """
        pass
    
    @abstractmethod
    def collection_exists(self, collection: str) -> bool:
        """
        Check if a collection exists.
        
        Args:
            collection: Collection name
            
        Returns:
            True if collection exists, False otherwise
        """
        pass
    
    @abstractmethod
    def get_collection_info(self, collection: str) -> Dict[str, Any]:
        """
        Get information about a collection.
        
        Args:
            collection: Collection name
            
        Returns:
            Dictionary with collection information
            
        Raises:
            StorageError: If collection doesn't exist or info retrieval fails
        """
        pass
    
    @abstractmethod
    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get general storage information.
        
        Returns:
            Dictionary with storage information
        """
        pass
    
    def batch_create(self, collection: str, records: Dict[str, JsonValue]) -> Dict[str, bool]:
        """
        Create multiple records in batch.
        
        Args:
            collection: Collection name
            records: Dictionary mapping record IDs to data
            
        Returns:
            Dictionary mapping record IDs to success status
        """
        results = {}
        for record_id, data in records.items():
            try:
                results[record_id] = self.create_record(collection, record_id, data)
            except Exception:
                results[record_id] = False
        return results
    
    def batch_read(self, collection: str, record_ids: List[str]) -> Dict[str, Optional[JsonValue]]:
        """
        Read multiple records in batch.
        
        Args:
            collection: Collection name
            record_ids: List of record IDs to read
            
        Returns:
            Dictionary mapping record IDs to data (or None if not found)
        """
        results = {}
        for record_id in record_ids:
            try:
                results[record_id] = self.read_record(collection, record_id)
            except Exception:
                results[record_id] = None
        return results
    
    def batch_update(self, collection: str, records: Dict[str, JsonValue]) -> Dict[str, bool]:
        """
        Update multiple records in batch.
        
        Args:
            collection: Collection name
            records: Dictionary mapping record IDs to updated data
            
        Returns:
            Dictionary mapping record IDs to success status
        """
        results = {}
        for record_id, data in records.items():
            try:
                results[record_id] = self.update_record(collection, record_id, data)
            except Exception:
                results[record_id] = False
        return results
    
    def batch_delete(self, collection: str, record_ids: List[str]) -> Dict[str, bool]:
        """
        Delete multiple records in batch.
        
        Args:
            collection: Collection name
            record_ids: List of record IDs to delete
            
        Returns:
            Dictionary mapping record IDs to success status
        """
        results = {}
        for record_id in record_ids:
            try:
                results[record_id] = self.delete_record(collection, record_id)
            except Exception:
                results[record_id] = False
        return results