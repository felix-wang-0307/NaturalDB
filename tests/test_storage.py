"""
Tests for Layer 1: Storage System
"""

import unittest
import tempfile
import shutil
import os
import json
from pathlib import Path

from naturaldb.storage import (
    Storage, StorageError, TableNotFoundError, 
    RecordNotFoundError, LockError
)


class TestStorage(unittest.TestCase):
    """Test cases for Storage class"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.storage = Storage(self.test_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        self.storage.close()
        shutil.rmtree(self.test_dir)
    
    def test_storage_initialization(self):
        """Test storage system initialization"""
        # Test with custom path
        custom_storage = Storage(self.test_dir)
        self.assertTrue(Path(self.test_dir).exists())
        custom_storage.close()
        
        # Test default path creation
        default_storage = Storage("test_default_data")
        self.assertTrue(Path("test_default_data").exists())
        default_storage.close()
        shutil.rmtree("test_default_data")
    
    def test_table_operations(self):
        """Test table creation, listing, and deletion"""
        # Initially no tables
        self.assertEqual(self.storage.list_tables(), [])
        
        # Create tables
        self.assertTrue(self.storage.create_table("Products"))
        self.assertTrue(self.storage.create_table("Users"))
        self.assertFalse(self.storage.create_table("Products"))  # Already exists
        
        # List tables
        tables = self.storage.list_tables()
        self.assertIn("Products", tables)
        self.assertIn("Users", tables)
        self.assertEqual(len(tables), 2)
        
        # Check table existence
        self.assertTrue(self.storage.table_exists("Products"))
        self.assertFalse(self.storage.table_exists("NonExistent"))
        
        # Drop tables
        self.assertTrue(self.storage.drop_table("Products"))
        self.assertFalse(self.storage.drop_table("Products"))  # Already dropped
        self.assertEqual(len(self.storage.list_tables()), 1)
    
    def test_record_crud_operations(self):
        """Test Create, Read, Update, Delete operations for records"""
        table = "Products"
        record_id = "1"
        
        # Test data
        product_data = {
            "id": 1,
            "name": "Test Product",
            "price": 99.99,
            "category": "Electronics"
        }
        
        # Insert record
        self.assertTrue(self.storage.insert(table, record_id, product_data))
        
        # Try to insert duplicate
        with self.assertRaises(StorageError):
            self.storage.insert(table, record_id, product_data)
        
        # Read record
        retrieved_data = self.storage.get(table, record_id)
        self.assertEqual(retrieved_data, product_data)
        
        # Read non-existent record
        self.assertIsNone(self.storage.get(table, "999"))
        
        # Update record
        updated_data = product_data.copy()
        updated_data["price"] = 79.99
        updated_data["on_sale"] = True
        
        self.assertTrue(self.storage.update(table, record_id, updated_data))
        retrieved_updated = self.storage.get(table, record_id)
        self.assertEqual(retrieved_updated, updated_data)
        
        # Try to update non-existent record
        with self.assertRaises(RecordNotFoundError):
            self.storage.update(table, "999", updated_data)
        
        # Delete record
        self.assertTrue(self.storage.delete(table, record_id))
        self.assertFalse(self.storage.delete(table, record_id))  # Already deleted
        self.assertIsNone(self.storage.get(table, record_id))
    
    def test_record_listing_and_counting(self):
        """Test record listing and counting operations"""
        table = "TestTable"
        
        # Empty table
        with self.assertRaises(TableNotFoundError):
            self.storage.list_records(table)
        
        self.assertEqual(self.storage.count_records(table), 0)
        
        # Add some records
        test_records = {
            "1": {"name": "Item 1", "value": 10},
            "2": {"name": "Item 2", "value": 20},
            "3": {"name": "Item 3", "value": 30},
        }
        
        for record_id, data in test_records.items():
            self.storage.insert(table, record_id, data)
        
        # List records
        record_ids = self.storage.list_records(table)
        self.assertEqual(set(record_ids), {"1", "2", "3"})
        
        # Count records
        self.assertEqual(self.storage.count_records(table), 3)
        
        # Get all records
        all_records = self.storage.get_all_records(table)
        self.assertEqual(len(all_records), 3)
        
        for record_id, expected_data in test_records.items():
            self.assertEqual(all_records[record_id], expected_data)
    
    def test_record_existence_check(self):
        """Test record existence checking"""
        table = "TestTable"
        record_id = "test_record"
        
        # Initially doesn't exist
        self.assertFalse(self.storage.record_exists(table, record_id))
        
        # Insert and check
        self.storage.insert(table, record_id, {"test": "data"})
        self.assertTrue(self.storage.record_exists(table, record_id))
        
        # Delete and check
        self.storage.delete(table, record_id)
        self.assertFalse(self.storage.record_exists(table, record_id))
    
    def test_file_structure(self):
        """Test that the file structure matches expectations"""
        table = "Products"
        record_id = "123"
        data = {"name": "Test Product"}
        
        # Insert record
        self.storage.insert(table, record_id, data)
        
        # Check file structure
        table_path = Path(self.test_dir) / table
        record_path = table_path / f"{record_id}.json"
        
        self.assertTrue(table_path.exists())
        self.assertTrue(table_path.is_dir())
        self.assertTrue(record_path.exists())
        self.assertTrue(record_path.is_file())
        
        # Check JSON content
        with open(record_path, 'r') as f:
            stored_data = json.load(f)
        self.assertEqual(stored_data, data)
    
    def test_invalid_json_handling(self):
        """Test handling of corrupted JSON files"""
        table = "TestTable"
        record_id = "corrupted"
        
        # Create table and write invalid JSON
        self.storage.create_table(table)
        record_path = Path(self.test_dir) / table / f"{record_id}.json"
        
        with open(record_path, 'w') as f:
            f.write("invalid json content {")
        
        # Should raise StorageError for corrupted JSON
        with self.assertRaises(StorageError):
            self.storage.get(table, record_id)
    
    def test_context_manager(self):
        """Test storage as context manager"""
        with Storage(self.test_dir) as storage:
            storage.insert("TestTable", "1", {"test": "data"})
            data = storage.get("TestTable", "1")
            self.assertEqual(data, {"test": "data"})
        
        # Storage should be properly closed
        self.assertEqual(len(storage._locked_files), 0)
    
    def test_numeric_record_ids(self):
        """Test using numeric record IDs"""
        table = "NumericIDs"
        
        # Insert with numeric IDs
        self.storage.insert(table, 1, {"name": "Record 1"})
        self.storage.insert(table, 2, {"name": "Record 2"})
        
        # Retrieve with numeric IDs
        record1 = self.storage.get(table, 1)
        record2 = self.storage.get(table, 2)
        
        self.assertEqual(record1["name"], "Record 1")
        self.assertEqual(record2["name"], "Record 2")
        
        # List should return string IDs (file stems)
        record_ids = self.storage.list_records(table)
        self.assertIn("1", record_ids)
        self.assertIn("2", record_ids)
    
    def test_complex_data_structures(self):
        """Test storage of complex nested data structures"""
        table = "ComplexData"
        record_id = "complex"
        
        complex_data = {
            "id": 1,
            "metadata": {
                "created_at": "2024-01-01T00:00:00Z",
                "tags": ["electronics", "mobile", "smartphone"],
                "specs": {
                    "cpu": "A15 Bionic",
                    "memory": "128GB",
                    "display": {
                        "size": 6.1,
                        "resolution": "2556x1179",
                        "technology": "OLED"
                    }
                }
            },
            "reviews": [
                {"rating": 5, "comment": "Excellent phone"},
                {"rating": 4, "comment": "Good battery life"}
            ],
            "in_stock": True,
            "price": 999.99
        }
        
        # Insert complex data
        self.storage.insert(table, record_id, complex_data)
        
        # Retrieve and verify
        retrieved = self.storage.get(table, record_id)
        self.assertEqual(retrieved, complex_data)
        
        # Verify nested access works
        self.assertEqual(retrieved["metadata"]["specs"]["display"]["size"], 6.1)
        self.assertEqual(len(retrieved["reviews"]), 2)


class TestStorageEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.storage = Storage(self.test_dir)
    
    def tearDown(self):
        """Clean up test environment"""
        self.storage.close()
        shutil.rmtree(self.test_dir)
    
    def test_special_characters_in_names(self):
        """Test handling of special characters in table and record names"""
        # Test table names with underscores and numbers
        special_table = "test_table_123"
        self.assertTrue(self.storage.create_table(special_table))
        
        # Test record IDs with special characters (that are filesystem-safe)
        special_records = {
            "record_1": {"data": "underscore"},
            "record-2": {"data": "hyphen"},
            "record.3": {"data": "dot"},
        }
        
        for record_id, data in special_records.items():
            self.storage.insert(special_table, record_id, data)
            retrieved = self.storage.get(special_table, record_id)
            self.assertEqual(retrieved, data)
    
    def test_empty_data_structures(self):
        """Test storage of empty data structures"""
        table = "EmptyData"
        
        test_cases = [
            ("empty_dict", {}),
            ("empty_list", {"items": []}),
            ("null_value", {"value": None}),
            ("empty_string", {"text": ""}),
            ("zero_number", {"count": 0}),
            ("false_boolean", {"flag": False}),
        ]
        
        for record_id, data in test_cases:
            self.storage.insert(table, record_id, data)
            retrieved = self.storage.get(table, record_id)
            self.assertEqual(retrieved, data)
    
    def test_large_record_storage(self):
        """Test storage of larger records"""
        table = "LargeRecords"
        
        # Create a larger record with many fields
        large_record = {
            "id": 1,
            "description": "A" * 1000,  # 1KB string
            "tags": [f"tag_{i}" for i in range(100)],  # 100 tags
            "properties": {f"prop_{i}": f"value_{i}" for i in range(50)},  # 50 properties
            "nested": {
                "level1": {
                    "level2": {
                        "level3": {
                            "data": [i for i in range(100)]
                        }
                    }
                }
            }
        }
        
        self.storage.insert(table, "large", large_record)
        retrieved = self.storage.get(table, "large")
        self.assertEqual(retrieved, large_record)


if __name__ == '__main__':
    unittest.main()