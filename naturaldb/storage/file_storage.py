"""
File-based storage implementation for NaturalDB
Implements storage using the local file system.
"""

import os
import time
from typing import Any, Dict, List, Optional
from pathlib import Path

from .base_storage import BaseStorage
from ..utils.json_utils import JsonValue, parse_json, serialize_json
from ..utils.file_utils import (
    ensure_directory, safe_file_operation, atomic_write, 
    file_lock, file_exists, list_files_in_directory
)
from ..utils.path_utils import (
    build_user_path, build_collection_path, build_record_path,
    list_collections, list_records, extract_record_id_from_filename
)
from ..utils.validators import (
    validate_collection_name, validate_record_id, validate_json_data
)
from ..exceptions import (
    StorageError, ValidationError, RecordNotFoundError, 
    CollectionNotFoundError, handle_exception
)


class FileStorage(BaseStorage):
    """File-based storage implementation."""
    
    def __init__(self, base_dir: str = "data", user_id: str = "default"):
        """
        Initialize file storage.
        
        Args:
            base_dir: Base directory for data storage
            user_id: User ID for data isolation
        """
        self.base_dir = os.path.abspath(base_dir)
        self.user_id = user_id
        self.user_path = build_user_path(self.base_dir, self.user_id)
        self._connected = False
    
    @handle_exception
    def connect(self, **kwargs) -> None:
        """
        Connect to file storage (ensure directory structure exists).
        
        Args:
            **kwargs: Additional connection parameters (unused for file storage)
        """
        try:
            ensure_directory(self.user_path)
            self._connected = True
        except Exception as e:
            raise StorageError(f"Failed to connect to file storage: {e}", "connect", self.user_path)
    
    def disconnect(self) -> None:
        """Disconnect from file storage."""
        self._connected = False
    
    def _ensure_connected(self) -> None:
        """Ensure storage is connected."""
        if not self._connected:
            raise StorageError("Storage not connected", "check_connection")
    
    def _validate_collection_name(self, collection: str) -> None:
        """Validate collection name."""
        if not validate_collection_name(collection):
            raise ValidationError(f"Invalid collection name: {collection}", "collection", collection)
    
    def _validate_record_id(self, record_id: str) -> None:
        """Validate record ID."""
        if not validate_record_id(record_id):
            raise ValidationError(f"Invalid record ID: {record_id}", "record_id", record_id)
    
    @handle_exception
    def create_record(self, collection: str, record_id: str, data: JsonValue) -> bool:
        """Create a new record."""
        self._ensure_connected()
        self._validate_collection_name(collection)
        self._validate_record_id(record_id)
        
        if not validate_json_data(data):
            raise ValidationError("Invalid JSON data", "data")
        
        record_path = build_record_path(self.base_dir, self.user_id, collection, record_id)
        
        # Check if record already exists
        if file_exists(record_path):
            raise StorageError(f"Record already exists: {record_id}", "create", record_path)
        
        try:
            with file_lock(record_path):
                # Serialize data to JSON
                json_content = serialize_json(data, indent=2)
                
                # Atomically write the file
                atomic_write(record_path, json_content)
                
                return True
                
        except Exception as e:
            raise StorageError(f"Failed to create record: {e}", "create", record_path)
    
    @handle_exception
    def read_record(self, collection: str, record_id: str) -> Optional[JsonValue]:
        """Read a record."""
        self._ensure_connected()
        self._validate_collection_name(collection)
        self._validate_record_id(record_id)
        
        record_path = build_record_path(self.base_dir, self.user_id, collection, record_id)
        
        if not file_exists(record_path):
            return None
        
        try:
            with file_lock(record_path):
                with safe_file_operation(record_path, 'r') as f:
                    content = f.read()
                    return parse_json(content)
                    
        except Exception as e:
            raise StorageError(f"Failed to read record: {e}", "read", record_path)
    
    @handle_exception
    def update_record(self, collection: str, record_id: str, data: JsonValue) -> bool:
        """Update an existing record."""
        self._ensure_connected()
        self._validate_collection_name(collection)
        self._validate_record_id(record_id)
        
        if not validate_json_data(data):
            raise ValidationError("Invalid JSON data", "data")
        
        record_path = build_record_path(self.base_dir, self.user_id, collection, record_id)
        
        if not file_exists(record_path):
            raise RecordNotFoundError(f"Record not found: {record_id}", collection, record_id)
        
        try:
            with file_lock(record_path):
                # Serialize data to JSON
                json_content = serialize_json(data, indent=2)
                
                # Atomically write the file
                atomic_write(record_path, json_content)
                
                return True
                
        except Exception as e:
            raise StorageError(f"Failed to update record: {e}", "update", record_path)
    
    @handle_exception
    def delete_record(self, collection: str, record_id: str) -> bool:
        """Delete a record."""
        self._ensure_connected()
        self._validate_collection_name(collection)
        self._validate_record_id(record_id)
        
        record_path = build_record_path(self.base_dir, self.user_id, collection, record_id)
        
        if not file_exists(record_path):
            return False  # Record doesn't exist, consider it successfully deleted
        
        try:
            with file_lock(record_path):
                os.unlink(record_path)
                return True
                
        except Exception as e:
            raise StorageError(f"Failed to delete record: {e}", "delete", record_path)
    
    @handle_exception
    def list_records(self, collection: str) -> List[str]:
        """List all record IDs in a collection."""
        self._ensure_connected()
        self._validate_collection_name(collection)
        
        return list_records(self.base_dir, self.user_id, collection)
    
    def record_exists(self, collection: str, record_id: str) -> bool:
        """Check if a record exists."""
        self._ensure_connected()
        self._validate_collection_name(collection)
        self._validate_record_id(record_id)
        
        record_path = build_record_path(self.base_dir, self.user_id, collection, record_id)
        return file_exists(record_path)
    
    @handle_exception
    def create_collection(self, collection: str) -> bool:
        """Create a new collection."""
        self._ensure_connected()
        self._validate_collection_name(collection)
        
        collection_path = build_collection_path(self.base_dir, self.user_id, collection)
        
        try:
            ensure_directory(collection_path)
            return True
        except Exception as e:
            raise StorageError(f"Failed to create collection: {e}", "create_collection", collection_path)
    
    @handle_exception
    def delete_collection(self, collection: str) -> bool:
        """Delete a collection and all its records."""
        self._ensure_connected()
        self._validate_collection_name(collection)
        
        collection_path = build_collection_path(self.base_dir, self.user_id, collection)
        
        if not os.path.exists(collection_path):
            return False  # Collection doesn't exist
        
        try:
            import shutil
            shutil.rmtree(collection_path)
            return True
        except Exception as e:
            raise StorageError(f"Failed to delete collection: {e}", "delete_collection", collection_path)
    
    def list_collections(self) -> List[str]:
        """List all collections."""
        self._ensure_connected()
        return list_collections(self.base_dir, self.user_id)
    
    def collection_exists(self, collection: str) -> bool:
        """Check if a collection exists."""
        self._ensure_connected()
        self._validate_collection_name(collection)
        
        collection_path = build_collection_path(self.base_dir, self.user_id, collection)
        return os.path.isdir(collection_path)
    
    @handle_exception
    def get_collection_info(self, collection: str) -> Dict[str, Any]:
        """Get information about a collection."""
        self._ensure_connected()
        self._validate_collection_name(collection)
        
        if not self.collection_exists(collection):
            raise CollectionNotFoundError(f"Collection not found: {collection}", collection, self.user_id)
        
        collection_path = build_collection_path(self.base_dir, self.user_id, collection)
        
        try:
            record_ids = self.list_records(collection)
            
            # Get collection statistics
            total_size = 0
            for record_id in record_ids:
                record_path = build_record_path(self.base_dir, self.user_id, collection, record_id)
                if file_exists(record_path):
                    total_size += os.path.getsize(record_path)
            
            # Get creation and modification times
            stat = os.stat(collection_path)
            
            return {
                'name': collection,
                'path': collection_path,
                'record_count': len(record_ids),
                'total_size_bytes': total_size,
                'created_time': stat.st_ctime,
                'modified_time': stat.st_mtime,
                'record_ids': record_ids
            }
            
        except Exception as e:
            raise StorageError(f"Failed to get collection info: {e}", "get_info", collection_path)
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get general storage information."""
        self._ensure_connected()
        
        try:
            collections = self.list_collections()
            
            total_records = 0
            total_size = 0
            
            for collection in collections:
                try:
                    info = self.get_collection_info(collection)
                    total_records += info['record_count']
                    total_size += info['total_size_bytes']
                except Exception:
                    # Skip collections that can't be read
                    continue
            
            return {
                'storage_type': 'file_storage',
                'base_directory': self.base_dir,
                'user_id': self.user_id,
                'user_path': self.user_path,
                'connected': self._connected,
                'collection_count': len(collections),
                'total_record_count': total_records,
                'total_size_bytes': total_size,
                'collections': collections
            }
            
        except Exception as e:
            raise StorageError(f"Failed to get storage info: {e}", "get_storage_info")
    
    def compact_collection(self, collection: str) -> Dict[str, Any]:
        """
        Compact a collection by removing fragmentation (not applicable for file storage).
        
        Args:
            collection: Collection name
            
        Returns:
            Dictionary with compaction results
        """
        self._ensure_connected()
        self._validate_collection_name(collection)
        
        # For file storage, we can't really compact, but we can provide info
        info = self.get_collection_info(collection)
        
        return {
            'collection': collection,
            'compacted': False,
            'reason': 'File storage does not require compaction',
            'record_count': info['record_count'],
            'size_bytes': info['total_size_bytes']
        }
    
    def backup_collection(self, collection: str, backup_path: str) -> bool:
        """
        Backup a collection to the specified path.
        
        Args:
            collection: Collection name
            backup_path: Path where backup should be created
            
        Returns:
            True if backup was successful
        """
        self._ensure_connected()
        self._validate_collection_name(collection)
        
        if not self.collection_exists(collection):
            raise CollectionNotFoundError(f"Collection not found: {collection}", collection, self.user_id)
        
        collection_path = build_collection_path(self.base_dir, self.user_id, collection)
        
        try:
            import shutil
            
            # Ensure backup directory exists
            ensure_directory(os.path.dirname(backup_path))
            
            # Copy the entire collection directory
            shutil.copytree(collection_path, backup_path, dirs_exist_ok=True)
            
            return True
            
        except Exception as e:
            raise StorageError(f"Failed to backup collection: {e}", "backup", collection_path)
    
    def restore_collection(self, collection: str, backup_path: str, overwrite: bool = False) -> bool:
        """
        Restore a collection from backup.
        
        Args:
            collection: Collection name
            backup_path: Path to backup
            overwrite: Whether to overwrite existing collection
            
        Returns:
            True if restore was successful
        """
        self._ensure_connected()
        self._validate_collection_name(collection)
        
        if not os.path.exists(backup_path):
            raise StorageError(f"Backup path does not exist: {backup_path}", "restore")
        
        if self.collection_exists(collection) and not overwrite:
            raise StorageError(f"Collection already exists: {collection}", "restore")
        
        collection_path = build_collection_path(self.base_dir, self.user_id, collection)
        
        try:
            import shutil
            
            # Remove existing collection if overwriting
            if overwrite and self.collection_exists(collection):
                shutil.rmtree(collection_path)
            
            # Copy backup to collection path
            shutil.copytree(backup_path, collection_path, dirs_exist_ok=True)
            
            return True
            
        except Exception as e:
            raise StorageError(f"Failed to restore collection: {e}", "restore", collection_path)