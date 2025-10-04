"""
Layer 1: Storage System
File-based key-value store implementation for NaturalDB

Features:
- Folders map to tables (e.g., Products/ = Products collection)
- Files map to records (e.g., Products/1.json = product with ID 1)
- File-locking for minimal transaction safety
- CRUD operations (Create, Read, Update, Delete)
"""

import os
import json
import fcntl
import tempfile
import shutil
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import time


class StorageError(Exception):
    """Base exception for storage operations"""
    pass


class TableNotFoundError(StorageError):
    """Raised when a table does not exist"""
    pass


class RecordNotFoundError(StorageError):
    """Raised when a record does not exist"""
    pass


class LockError(StorageError):
    """Raised when file locking fails"""
    pass


class Storage:
    """
    File-based storage system for NaturalDB
    
    This class implements a simple file-based key-value store where:
    - Directories represent tables/collections
    - JSON files represent individual records
    - File locking provides minimal transaction safety
    """
    
    def __init__(self, storage_path: str = "data"):
        """
        Initialize storage system
        
        Args:
            storage_path: Root directory for data storage
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        
        # Track locked files for this instance
        self._locked_files = {}
    
    def _get_table_path(self, table: str) -> Path:
        """Get the directory path for a table"""
        return self.storage_path / table
    
    def _get_record_path(self, table: str, record_id: Union[str, int]) -> Path:
        """Get the file path for a specific record"""
        return self._get_table_path(table) / f"{record_id}.json"
    
    def _ensure_table_exists(self, table: str) -> None:
        """Create table directory if it doesn't exist"""
        table_path = self._get_table_path(table)
        table_path.mkdir(exist_ok=True)
    
    def _acquire_lock(self, file_path: Path, mode: str = 'r') -> Optional[Any]:
        """
        Acquire a file lock for transaction safety
        
        Args:
            file_path: Path to the file to lock
            mode: File open mode ('r', 'w', etc.)
            
        Returns:
            File handle with lock acquired
        """
        try:
            if mode == 'w':
                # For write operations, ensure parent directory exists
                file_path.parent.mkdir(exist_ok=True)
                file_handle = open(file_path, 'w')
            else:
                # For read operations, file must exist
                if not file_path.exists():
                    return None
                file_handle = open(file_path, 'r')
            
            # Acquire exclusive lock for writes, shared lock for reads
            lock_type = fcntl.LOCK_EX if mode == 'w' else fcntl.LOCK_SH
            fcntl.flock(file_handle.fileno(), lock_type | fcntl.LOCK_NB)
            
            # Track the locked file
            self._locked_files[str(file_path)] = file_handle
            return file_handle
            
        except (IOError, OSError) as e:
            if hasattr(e, 'errno') and e.errno in [11, 35]:  # EAGAIN or EWOULDBLOCK
                raise LockError(f"Could not acquire lock on {file_path}")
            raise StorageError(f"Error accessing file {file_path}: {e}")
    
    def _release_lock(self, file_path: Path) -> None:
        """Release a file lock"""
        file_key = str(file_path)
        if file_key in self._locked_files:
            file_handle = self._locked_files[file_key]
            try:
                fcntl.flock(file_handle.fileno(), fcntl.LOCK_UN)
                file_handle.close()
            finally:
                del self._locked_files[file_key]
    
    def create_table(self, table: str) -> bool:
        """
        Create a new table (directory)
        
        Args:
            table: Table name
            
        Returns:
            True if table was created, False if it already existed
        """
        table_path = self._get_table_path(table)
        if table_path.exists():
            return False
        
        table_path.mkdir(parents=True)
        return True
    
    def drop_table(self, table: str) -> bool:
        """
        Drop a table and all its records
        
        Args:
            table: Table name
            
        Returns:
            True if table was dropped, False if it didn't exist
        """
        table_path = self._get_table_path(table)
        if not table_path.exists():
            return False
        
        shutil.rmtree(table_path)
        return True
    
    def list_tables(self) -> List[str]:
        """
        List all tables in the storage system
        
        Returns:
            List of table names
        """
        if not self.storage_path.exists():
            return []
        
        return [
            item.name for item in self.storage_path.iterdir() 
            if item.is_dir()
        ]
    
    def insert(self, table: str, record_id: Union[str, int], data: Dict[str, Any]) -> bool:
        """
        Insert a new record into a table
        
        Args:
            table: Table name
            record_id: Unique identifier for the record
            data: Record data as dictionary
            
        Returns:
            True if record was inserted
            
        Raises:
            StorageError: If record already exists or other error
        """
        self._ensure_table_exists(table)
        record_path = self._get_record_path(table, record_id)
        
        if record_path.exists():
            raise StorageError(f"Record {record_id} already exists in table {table}")
        
        file_handle = None
        try:
            file_handle = self._acquire_lock(record_path, 'w')
            json.dump(data, file_handle, indent=2)
            return True
        finally:
            if file_handle:
                self._release_lock(record_path)
    
    def get(self, table: str, record_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        """
        Retrieve a record from a table
        
        Args:
            table: Table name
            record_id: Record identifier
            
        Returns:
            Record data or None if not found
        """
        record_path = self._get_record_path(table, record_id)
        
        file_handle = None
        try:
            file_handle = self._acquire_lock(record_path, 'r')
            if file_handle is None:
                return None
            
            return json.load(file_handle)
        except json.JSONDecodeError:
            raise StorageError(f"Invalid JSON in record {record_id} from table {table}")
        finally:
            if file_handle:
                self._release_lock(record_path)
    
    def update(self, table: str, record_id: Union[str, int], data: Dict[str, Any]) -> bool:
        """
        Update an existing record
        
        Args:
            table: Table name
            record_id: Record identifier
            data: New record data
            
        Returns:
            True if record was updated
            
        Raises:
            RecordNotFoundError: If record doesn't exist
        """
        record_path = self._get_record_path(table, record_id)
        
        if not record_path.exists():
            raise RecordNotFoundError(f"Record {record_id} not found in table {table}")
        
        file_handle = None
        try:
            file_handle = self._acquire_lock(record_path, 'w')
            json.dump(data, file_handle, indent=2)
            return True
        finally:
            if file_handle:
                self._release_lock(record_path)
    
    def delete(self, table: str, record_id: Union[str, int]) -> bool:
        """
        Delete a record from a table
        
        Args:
            table: Table name
            record_id: Record identifier
            
        Returns:
            True if record was deleted, False if it didn't exist
        """
        record_path = self._get_record_path(table, record_id)
        
        if not record_path.exists():
            return False
        
        record_path.unlink()
        return True
    
    def list_records(self, table: str) -> List[str]:
        """
        List all record IDs in a table
        
        Args:
            table: Table name
            
        Returns:
            List of record IDs
            
        Raises:
            TableNotFoundError: If table doesn't exist
        """
        table_path = self._get_table_path(table)
        
        if not table_path.exists():
            raise TableNotFoundError(f"Table {table} not found")
        
        return [
            item.stem for item in table_path.iterdir()
            if item.is_file() and item.suffix == '.json'
        ]
    
    def get_all_records(self, table: str) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve all records from a table
        
        Args:
            table: Table name
            
        Returns:
            Dictionary mapping record IDs to record data
            
        Raises:
            TableNotFoundError: If table doesn't exist
        """
        record_ids = self.list_records(table)
        result = {}
        
        for record_id in record_ids:
            data = self.get(table, record_id)
            if data is not None:
                result[record_id] = data
        
        return result
    
    def count_records(self, table: str) -> int:
        """
        Count the number of records in a table
        
        Args:
            table: Table name
            
        Returns:
            Number of records
        """
        try:
            return len(self.list_records(table))
        except TableNotFoundError:
            return 0
    
    def table_exists(self, table: str) -> bool:
        """
        Check if a table exists
        
        Args:
            table: Table name
            
        Returns:
            True if table exists
        """
        return self._get_table_path(table).exists()
    
    def record_exists(self, table: str, record_id: Union[str, int]) -> bool:
        """
        Check if a record exists
        
        Args:
            table: Table name
            record_id: Record identifier
            
        Returns:
            True if record exists
        """
        return self._get_record_path(table, record_id).exists()
    
    def close(self) -> None:
        """
        Close storage system and release all locks
        """
        # Release all remaining locks
        for file_path in list(self._locked_files.keys()):
            self._release_lock(Path(file_path))
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()