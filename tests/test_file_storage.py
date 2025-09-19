"""
Tests for the FileStorage system.
"""

import os
import tempfile
import shutil
import pytest
from pathlib import Path

from naturaldb.storage import FileStorage


class TestFileStorage:
    """Test cases for the FileStorage class."""
    
    def setup_method(self):
        """Set up test environment with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = FileStorage(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_create_record_with_auto_id(self):
        """Test creating a record with automatically generated ID."""
        data = {"name": "Test Product", "price": 99.99}
        record_id = self.storage.create_record("Products", data)
        
        assert record_id is not None
        assert len(record_id) > 0
        
        # Verify the record was created
        retrieved = self.storage.read_record("Products", record_id)
        assert retrieved is not None
        assert retrieved["name"] == "Test Product"
        assert retrieved["price"] == 99.99
        assert retrieved["id"] == record_id
    
    def test_create_record_with_custom_id(self):
        """Test creating a record with custom ID."""
        data = {"name": "Custom Product", "category": "Electronics"}
        record_id = self.storage.create_record("Products", data, "custom-123")
        
        assert record_id == "custom-123"
        
        # Verify the record was created
        retrieved = self.storage.read_record("Products", "custom-123")
        assert retrieved is not None
        assert retrieved["name"] == "Custom Product"
        assert retrieved["id"] == "custom-123"
    
    def test_create_duplicate_record_raises_error(self):
        """Test that creating a record with duplicate ID raises an error."""
        data = {"name": "First Product"}
        self.storage.create_record("Products", data, "duplicate-id")
        
        # Try to create another record with the same ID
        data2 = {"name": "Second Product"}
        with pytest.raises(ValueError):
            self.storage.create_record("Products", data2, "duplicate-id")
    
    def test_read_nonexistent_record(self):
        """Test reading a record that doesn't exist."""
        result = self.storage.read_record("Products", "nonexistent")
        assert result is None
    
    def test_update_record(self):
        """Test updating an existing record."""
        # Create a record
        data = {"name": "Original Product", "price": 50.0}
        record_id = self.storage.create_record("Products", data, "update-test")
        
        # Update the record
        updated_data = {"name": "Updated Product", "price": 75.0, "category": "New"}
        success = self.storage.update_record("Products", "update-test", updated_data)
        assert success is True
        
        # Verify the update
        retrieved = self.storage.read_record("Products", "update-test")
        assert retrieved["name"] == "Updated Product"
        assert retrieved["price"] == 75.0
        assert retrieved["category"] == "New"
        assert retrieved["id"] == "update-test"
    
    def test_update_nonexistent_record(self):
        """Test updating a record that doesn't exist."""
        data = {"name": "Some Product"}
        success = self.storage.update_record("Products", "nonexistent", data)
        assert success is False
    
    def test_delete_record(self):
        """Test deleting a record."""
        # Create a record
        data = {"name": "To Delete"}
        record_id = self.storage.create_record("Products", data, "delete-test")
        
        # Verify it exists
        assert self.storage.read_record("Products", "delete-test") is not None
        
        # Delete it
        success = self.storage.delete_record("Products", "delete-test")
        assert success is True
        
        # Verify it's gone
        assert self.storage.read_record("Products", "delete-test") is None
    
    def test_delete_nonexistent_record(self):
        """Test deleting a record that doesn't exist."""
        success = self.storage.delete_record("Products", "nonexistent")
        assert success is False
    
    def test_list_records(self):
        """Test listing all records in a table."""
        # Create some records
        self.storage.create_record("Products", {"name": "Product 1"}, "1")
        self.storage.create_record("Products", {"name": "Product 2"}, "2")
        self.storage.create_record("Products", {"name": "Product 3"}, "3")
        
        # List records
        record_ids = self.storage.list_records("Products")
        assert sorted(record_ids) == ["1", "2", "3"]
    
    def test_list_records_empty_table(self):
        """Test listing records from an empty table."""
        record_ids = self.storage.list_records("EmptyTable")
        assert record_ids == []
    
    def test_list_tables(self):
        """Test listing all tables."""
        # Create records in different tables
        self.storage.create_record("Products", {"name": "Product"}, "1")
        self.storage.create_record("Users", {"name": "User"}, "1")
        self.storage.create_record("Orders", {"total": 100}, "1")
        
        # List tables
        tables = self.storage.list_tables()
        assert sorted(tables) == ["Orders", "Products", "Users"]
    
    def test_table_exists(self):
        """Test checking if a table exists."""
        assert self.storage.table_exists("Products") is False
        
        # Create a record in the table
        self.storage.create_record("Products", {"name": "Product"}, "1")
        assert self.storage.table_exists("Products") is True
    
    def test_drop_table(self):
        """Test dropping a table."""
        # Create some records in a table
        self.storage.create_record("Products", {"name": "Product 1"}, "1")
        self.storage.create_record("Products", {"name": "Product 2"}, "2")
        
        # Verify table exists
        assert self.storage.table_exists("Products") is True
        assert len(self.storage.list_records("Products")) == 2
        
        # Drop the table
        success = self.storage.drop_table("Products")
        assert success is True
        
        # Verify table is gone
        assert self.storage.table_exists("Products") is False
        assert len(self.storage.list_records("Products")) == 0
    
    def test_drop_nonexistent_table(self):
        """Test dropping a table that doesn't exist."""
        success = self.storage.drop_table("NonexistentTable")
        assert success is False
    
    def test_get_record_count(self):
        """Test getting the number of records in a table."""
        # Empty table
        assert self.storage.get_record_count("Products") == 0
        
        # Add some records
        self.storage.create_record("Products", {"name": "Product 1"}, "1")
        assert self.storage.get_record_count("Products") == 1
        
        self.storage.create_record("Products", {"name": "Product 2"}, "2")
        assert self.storage.get_record_count("Products") == 2
        
        # Delete a record
        self.storage.delete_record("Products", "1")
        assert self.storage.get_record_count("Products") == 1
    
    def test_file_structure(self):
        """Test that the file structure matches the expected pattern."""
        # Create a record
        self.storage.create_record("Products", {"name": "Test"}, "123")
        
        # Verify folder structure
        products_dir = Path(self.temp_dir) / "Products"
        assert products_dir.exists()
        assert products_dir.is_dir()
        
        # Verify file structure
        record_file = products_dir / "123.json"
        assert record_file.exists()
        assert record_file.is_file()
        
        # Verify file content
        import json
        with open(record_file, 'r') as f:
            data = json.load(f)
        assert data["name"] == "Test"
        assert data["id"] == "123"