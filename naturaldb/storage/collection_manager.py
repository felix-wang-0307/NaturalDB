"""
Collection manager for NaturalDB
Provides high-level collection management operations.
"""

from typing import Any, Dict, List, Optional, Callable
from .file_storage import FileStorage
from ..utils.json_utils import JsonValue
from ..exceptions import StorageError, CollectionNotFoundError, handle_exception


class CollectionManager:
    """High-level collection management interface."""
    
    def __init__(self, storage: FileStorage):
        """
        Initialize collection manager.
        
        Args:
            storage: Underlying storage implementation
        """
        self.storage = storage
    
    @handle_exception
    def create_collection(self, name: str) -> bool:
        """
        Create a new collection.
        
        Args:
            name: Collection name
            
        Returns:
            True if successful
        """
        return self.storage.create_collection(name)
    
    @handle_exception
    def drop_collection(self, name: str) -> bool:
        """
        Drop a collection and all its records.
        
        Args:
            name: Collection name
            
        Returns:
            True if successful
        """
        return self.storage.delete_collection(name)
    
    def list_collections(self) -> List[str]:
        """
        List all collections.
        
        Returns:
            List of collection names
        """
        return self.storage.list_collections()
    
    def collection_exists(self, name: str) -> bool:
        """
        Check if a collection exists.
        
        Args:
            name: Collection name
            
        Returns:
            True if collection exists
        """
        return self.storage.collection_exists(name)
    
    @handle_exception
    def get_collection_info(self, name: str) -> Dict[str, Any]:
        """
        Get detailed information about a collection.
        
        Args:
            name: Collection name
            
        Returns:
            Dictionary with collection information
        """
        return self.storage.get_collection_info(name)
    
    @handle_exception
    def count_records(self, collection: str) -> int:
        """
        Count records in a collection.
        
        Args:
            collection: Collection name
            
        Returns:
            Number of records
        """
        if not self.collection_exists(collection):
            raise CollectionNotFoundError(f"Collection not found: {collection}", collection)
        
        return len(self.storage.list_records(collection))
    
    @handle_exception
    def is_empty(self, collection: str) -> bool:
        """
        Check if a collection is empty.
        
        Args:
            collection: Collection name
            
        Returns:
            True if collection is empty
        """
        return self.count_records(collection) == 0
    
    @handle_exception
    def copy_collection(self, source: str, destination: str, overwrite: bool = False) -> bool:
        """
        Copy a collection to a new name.
        
        Args:
            source: Source collection name
            destination: Destination collection name
            overwrite: Whether to overwrite destination if it exists
            
        Returns:
            True if successful
        """
        if not self.collection_exists(source):
            raise CollectionNotFoundError(f"Source collection not found: {source}", source)
        
        if self.collection_exists(destination) and not overwrite:
            raise StorageError(f"Destination collection already exists: {destination}")
        
        # Create destination collection
        if not self.create_collection(destination):
            return False
        
        # Copy all records
        record_ids = self.storage.list_records(source)
        
        success_count = 0
        for record_id in record_ids:
            try:
                data = self.storage.read_record(source, record_id)
                if data is not None:
                    if self.storage.create_record(destination, record_id, data):
                        success_count += 1
            except Exception:
                # Continue copying other records even if one fails
                continue
        
        return success_count == len(record_ids)
    
    @handle_exception
    def rename_collection(self, old_name: str, new_name: str) -> bool:
        """
        Rename a collection.
        
        Args:
            old_name: Current collection name
            new_name: New collection name
            
        Returns:
            True if successful
        """
        if not self.collection_exists(old_name):
            raise CollectionNotFoundError(f"Collection not found: {old_name}", old_name)
        
        if self.collection_exists(new_name):
            raise StorageError(f"Destination collection already exists: {new_name}")
        
        # Copy to new name
        if not self.copy_collection(old_name, new_name):
            return False
        
        # Delete old collection
        return self.drop_collection(old_name)
    
    @handle_exception
    def backup_collection(self, collection: str, backup_path: str) -> bool:
        """
        Backup a collection.
        
        Args:
            collection: Collection name
            backup_path: Path for backup
            
        Returns:
            True if successful
        """
        if hasattr(self.storage, 'backup_collection'):
            return self.storage.backup_collection(collection, backup_path)
        else:
            raise StorageError("Backup not supported by storage backend")
    
    @handle_exception
    def restore_collection(self, collection: str, backup_path: str, overwrite: bool = False) -> bool:
        """
        Restore a collection from backup.
        
        Args:
            collection: Collection name
            backup_path: Path to backup
            overwrite: Whether to overwrite existing collection
            
        Returns:
            True if successful
        """
        if hasattr(self.storage, 'restore_collection'):
            return self.storage.restore_collection(collection, backup_path, overwrite)
        else:
            raise StorageError("Restore not supported by storage backend")
    
    @handle_exception
    def get_all_records(self, collection: str) -> Dict[str, JsonValue]:
        """
        Get all records from a collection.
        
        Args:
            collection: Collection name
            
        Returns:
            Dictionary mapping record IDs to data
        """
        if not self.collection_exists(collection):
            raise CollectionNotFoundError(f"Collection not found: {collection}", collection)
        
        record_ids = self.storage.list_records(collection)
        return self.storage.batch_read(collection, record_ids)
    
    @handle_exception
    def filter_records(self, collection: str, predicate: Callable[[JsonValue], bool]) -> Dict[str, JsonValue]:
        """
        Filter records in a collection based on a predicate.
        
        Args:
            collection: Collection name
            predicate: Function that returns True for records to include
            
        Returns:
            Dictionary mapping record IDs to filtered data
        """
        all_records = self.get_all_records(collection)
        
        filtered = {}
        for record_id, data in all_records.items():
            if data is not None and predicate(data):
                filtered[record_id] = data
        
        return filtered
    
    @handle_exception
    def find_records_by_field(self, collection: str, field: str, value: Any) -> Dict[str, JsonValue]:
        """
        Find records where a field matches a specific value.
        
        Args:
            collection: Collection name
            field: Field name to search
            value: Value to match
            
        Returns:
            Dictionary mapping record IDs to matching data
        """
        def predicate(data: JsonValue) -> bool:
            if isinstance(data, dict) and field in data:
                return data[field] == value
            return False
        
        return self.filter_records(collection, predicate)
    
    @handle_exception
    def get_unique_values(self, collection: str, field: str) -> List[Any]:
        """
        Get unique values for a field across all records in a collection.
        
        Args:
            collection: Collection name
            field: Field name
            
        Returns:
            List of unique values
        """
        all_records = self.get_all_records(collection)
        
        unique_values = set()
        for data in all_records.values():
            if isinstance(data, dict) and field in data:
                unique_values.add(data[field])
        
        return list(unique_values)
    
    @handle_exception
    def get_collection_statistics(self, collection: str) -> Dict[str, Any]:
        """
        Get statistics about a collection.
        
        Args:
            collection: Collection name
            
        Returns:
            Dictionary with collection statistics
        """
        if not self.collection_exists(collection):
            raise CollectionNotFoundError(f"Collection not found: {collection}", collection)
        
        all_records = self.get_all_records(collection)
        
        stats = {
            'name': collection,
            'total_records': len(all_records),
            'empty_records': 0,
            'field_counts': {},
            'data_types': {}
        }
        
        for record_id, data in all_records.items():
            if data is None or (isinstance(data, dict) and not data):
                stats['empty_records'] += 1
                continue
            
            if isinstance(data, dict):
                for field, value in data.items():
                    # Count field occurrences
                    if field not in stats['field_counts']:
                        stats['field_counts'][field] = 0
                    stats['field_counts'][field] += 1
                    
                    # Count data types
                    value_type = type(value)
                    data_type = getattr(value_type, '__name__', str(value_type))
                    if field not in stats['data_types']:
                        stats['data_types'][field] = {}
                    if data_type not in stats['data_types'][field]:
                        stats['data_types'][field][data_type] = 0
                    stats['data_types'][field][data_type] += 1
        
        return stats