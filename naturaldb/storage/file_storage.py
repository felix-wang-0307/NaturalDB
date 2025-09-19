"""
File-based storage system for NaturalDB.

This module implements Layer 1: Storage System using a file-based key-value store.
- Tables are represented as folders (e.g., Products/ for Products table)
- Records are represented as JSON files (e.g., Products/1.json for record with id 1)
"""

import os
import json
import uuid
from typing import Dict, Any, Optional, List
from pathlib import Path


class FileStorage:
    """
    File-based storage system that stores JSON data efficiently.
    
    Uses a folder structure where:
    - Each table is a folder (e.g., Products/)
    - Each record is a JSON file (e.g., Products/1.json)
    """
    
    def __init__(self, base_path: str = "data"):
        """
        Initialize the file storage system.
        
        Args:
            base_path: Base directory for storing data files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_table_path(self, table_name: str) -> Path:
        """Get the path to a table directory."""
        return self.base_path / table_name
    
    def _get_record_path(self, table_name: str, record_id: str) -> Path:
        """Get the path to a specific record file."""
        return self._get_table_path(table_name) / f"{record_id}.json"
    
    def _ensure_table_exists(self, table_name: str):
        """Ensure that a table directory exists."""
        table_path = self._get_table_path(table_name)
        table_path.mkdir(parents=True, exist_ok=True)
    
    def create_record(self, table_name: str, data: Dict[str, Any], record_id: Optional[str] = None) -> str:
        """
        Create a new record in the specified table.
        
        Args:
            table_name: Name of the table
            data: JSON data to store
            record_id: Optional custom ID, if not provided, a UUID will be generated
            
        Returns:
            The ID of the created record
            
        Raises:
            ValueError: If record with the same ID already exists
        """
        if record_id is None:
            record_id = str(uuid.uuid4())
        
        self._ensure_table_exists(table_name)
        record_path = self._get_record_path(table_name, record_id)
        
        if record_path.exists():
            raise ValueError(f"Record with ID '{record_id}' already exists in table '{table_name}'")
        
        # Add the ID to the data if not present
        if 'id' not in data:
            data['id'] = record_id
        
        with open(record_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return record_id
    
    def read_record(self, table_name: str, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Read a record from the specified table.
        
        Args:
            table_name: Name of the table
            record_id: ID of the record to read
            
        Returns:
            The record data as a dictionary, or None if not found
        """
        record_path = self._get_record_path(table_name, record_id)
        
        if not record_path.exists():
            return None
        
        try:
            with open(record_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    
    def update_record(self, table_name: str, record_id: str, data: Dict[str, Any]) -> bool:
        """
        Update an existing record in the specified table.
        
        Args:
            table_name: Name of the table
            record_id: ID of the record to update
            data: New JSON data to store
            
        Returns:
            True if the record was updated, False if it doesn't exist
        """
        record_path = self._get_record_path(table_name, record_id)
        
        if not record_path.exists():
            return False
        
        # Ensure the ID is preserved
        if 'id' not in data:
            data['id'] = record_id
        
        with open(record_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return True
    
    def delete_record(self, table_name: str, record_id: str) -> bool:
        """
        Delete a record from the specified table.
        
        Args:
            table_name: Name of the table
            record_id: ID of the record to delete
            
        Returns:
            True if the record was deleted, False if it doesn't exist
        """
        record_path = self._get_record_path(table_name, record_id)
        
        if not record_path.exists():
            return False
        
        try:
            record_path.unlink()
            return True
        except OSError:
            return False
    
    def list_records(self, table_name: str) -> List[str]:
        """
        List all record IDs in the specified table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of record IDs
        """
        table_path = self._get_table_path(table_name)
        
        if not table_path.exists():
            return []
        
        record_ids = []
        for file_path in table_path.glob("*.json"):
            record_ids.append(file_path.stem)
        
        return sorted(record_ids)
    
    def list_tables(self) -> List[str]:
        """
        List all table names.
        
        Returns:
            List of table names
        """
        if not self.base_path.exists():
            return []
        
        tables = []
        for item in self.base_path.iterdir():
            if item.is_dir():
                tables.append(item.name)
        
        return sorted(tables)
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists.
        
        Args:
            table_name: Name of the table
            
        Returns:
            True if the table exists, False otherwise
        """
        return self._get_table_path(table_name).exists()
    
    def drop_table(self, table_name: str) -> bool:
        """
        Drop (delete) an entire table and all its records.
        
        Args:
            table_name: Name of the table to drop
            
        Returns:
            True if the table was dropped, False if it doesn't exist
        """
        table_path = self._get_table_path(table_name)
        
        if not table_path.exists():
            return False
        
        try:
            # Delete all files in the table directory
            for file_path in table_path.glob("*.json"):
                file_path.unlink()
            
            # Remove the directory
            table_path.rmdir()
            return True
        except OSError:
            return False
    
    def get_record_count(self, table_name: str) -> int:
        """
        Get the number of records in a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Number of records in the table
        """
        return len(self.list_records(table_name))