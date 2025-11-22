"""
Test suite for NaturalDB Storage System
Tests the Storage, DatabaseStorage, and TableStorage classes with thread safety and sanitization.
"""

import pytest
import os
import json
import shutil
import tempfile
import threading
import time
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from naturaldb.entities import User, Database, Table, Record
from naturaldb.storage_system.storage import Storage, DatabaseStorage, TableStorage
from naturaldb.storage_system.file_system import FileSystem


@pytest.fixture
def temp_data_dir(monkeypatch):
    """Create a temporary data directory for testing"""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    monkeypatch.chdir(temp_dir)
    yield temp_dir
    monkeypatch.chdir(original_cwd)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_user():
    """Create a sample user for testing"""
    return User(id="test_user", name="Test User")


@pytest.fixture
def sample_database():
    """Create a sample database for testing"""
    return Database(name="test_db")


@pytest.fixture
def sample_table():
    """Create a sample table for testing"""
    return Table(name="test_table", indexes={})


@pytest.fixture
def sample_record():
    """Create a sample record for testing"""
    return Record(
        id="record1",
        data={
            "name": "Test Product",
            "price": 99.99,
            "in_stock": True,
            "tags": ["electronics", "test"]
        }
    )


@pytest.fixture
def storage():
    """Create a Storage instance"""
    return Storage()


class TestStorage:
    """Test cases for the Storage class"""

    def test_get_path_user_only(self, temp_data_dir, sample_user):
        """Test getting path for user only"""
        path = Storage.get_path(sample_user)
        expected = os.path.join(temp_data_dir, "data", "test_user")
        # Resolve both paths to handle symlinks on macOS
        assert os.path.realpath(path) == os.path.realpath(expected)

    def test_get_path_with_database(self, temp_data_dir, sample_user, sample_database):
        """Test getting path for user and database"""
        path = Storage.get_path(sample_user, sample_database)
        expected = os.path.join(temp_data_dir, "data", "test_user", "test_db")
        # Resolve both paths to handle symlinks on macOS
        assert os.path.realpath(path) == os.path.realpath(expected)

    def test_get_path_with_table(self, temp_data_dir, sample_user, sample_database, sample_table):
        """Test getting path for user, database, and table"""
        path = Storage.get_path(sample_user, sample_database, sample_table)
        expected = os.path.join(temp_data_dir, "data", "test_user", "test_db", "test_table")
        # Resolve both paths to handle symlinks on macOS
        assert os.path.realpath(path) == os.path.realpath(expected)

    def test_get_path_with_record(self, temp_data_dir, sample_user, sample_database, sample_table, sample_record):
        """Test getting path for complete hierarchy"""
        path = Storage.get_path(sample_user, sample_database, sample_table, sample_record)
        expected = os.path.join(temp_data_dir, "data", "test_user", "test_db", "test_table", "record1.json")
        # Resolve both paths to handle symlinks on macOS
        assert os.path.realpath(path) == os.path.realpath(expected)

    def test_get_path_sanitizes_names(self, temp_data_dir):
        """Test that get_path sanitizes dangerous names"""
        user = User(id="user/../etc", name="Malicious")
        database = Database(name="db<script>")
        table = Table(name="table&test", indexes={})
        record = Record(id="rec/ord", data={})
        
        path = Storage.get_path(user, database, table, record)
        # Path should not contain dangerous characters
        assert "../" not in path
        assert "<" not in path
        assert ">" not in path
        assert "&" not in path

    def test_create_user(self, temp_data_dir, storage, sample_user):
        """Test creating a user directory"""
        storage.create_user(sample_user)
        user_path = Storage.get_path(sample_user)
        assert os.path.exists(user_path)
        assert os.path.isdir(user_path)

    def test_create_user_idempotent(self, temp_data_dir, storage, sample_user):
        """Test that creating a user twice doesn't fail"""
        storage.create_user(sample_user)
        storage.create_user(sample_user)  # Should not raise
        assert os.path.exists(Storage.get_path(sample_user))

    def test_delete_user(self, temp_data_dir, storage, sample_user):
        """Test deleting a user directory"""
        storage.create_user(sample_user)
        user_path = Storage.get_path(sample_user)
        assert os.path.exists(user_path)
        
        storage.delete_user(sample_user)
        assert not os.path.exists(user_path)

    def test_delete_nonexistent_user(self, temp_data_dir, storage, sample_user):
        """Test deleting a user that doesn't exist (should not raise)"""
        storage.delete_user(sample_user)  # Should not raise

    def test_create_database(self, temp_data_dir, storage, sample_user, sample_database):
        """Test creating a database"""
        storage.create_user(sample_user)
        storage.create_database(sample_user, sample_database)
        
        db_path = Storage.get_path(sample_user, sample_database)
        assert os.path.exists(db_path)
        assert os.path.isdir(db_path)
        
        # Check metadata file exists
        metadata_path = os.path.join(db_path, "metadata.json")
        assert os.path.exists(metadata_path)
        
        # Verify metadata content
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        assert metadata['name'] == "test_db"
        assert metadata['tables'] == []

    def test_delete_database(self, temp_data_dir, storage, sample_user, sample_database):
        """Test deleting a database"""
        storage.create_user(sample_user)
        storage.create_database(sample_user, sample_database)
        db_path = Storage.get_path(sample_user, sample_database)
        assert os.path.exists(db_path)
        
        storage.delete_database(sample_user, sample_database)
        assert not os.path.exists(db_path)

    def test_delete_database_with_tables(self, temp_data_dir, storage, sample_user, sample_database, sample_table):
        """Test deleting a database with tables inside"""
        storage.create_user(sample_user)
        storage.create_database(sample_user, sample_database)
        
        db_storage = DatabaseStorage(sample_user, sample_database)
        db_storage.create_table(sample_table)
        
        db_path = Storage.get_path(sample_user, sample_database)
        assert os.path.exists(db_path)
        
        storage.delete_database(sample_user, sample_database)
        assert not os.path.exists(db_path)


class TestDatabaseStorage:
    """Test cases for the DatabaseStorage class"""

    def test_initialization(self, temp_data_dir, sample_user, sample_database):
        """Test DatabaseStorage initialization creates directory"""
        db_storage = DatabaseStorage(sample_user, sample_database)
        assert os.path.exists(db_storage.base_path)

    def test_metadata_getter_nonexistent(self, temp_data_dir, sample_user, sample_database):
        """Test metadata getter when file doesn't exist"""
        db_storage = DatabaseStorage(sample_user, sample_database)
        metadata = db_storage.metadata
        assert metadata['name'] == sample_database.name
        assert metadata['tables'] == []

    def test_metadata_setter_and_getter(self, temp_data_dir, sample_user, sample_database):
        """Test setting and getting metadata"""
        db_storage = DatabaseStorage(sample_user, sample_database)
        
        new_metadata = {
            'name': 'test_db',
            'tables': ['table1', 'table2'],
            'version': '1.0'
        }
        db_storage.metadata = new_metadata
        
        # Read it back
        retrieved = db_storage.metadata
        assert retrieved == new_metadata

    def test_get_table_path(self, temp_data_dir, sample_user, sample_database, sample_table):
        """Test getting table path"""
        db_storage = DatabaseStorage(sample_user, sample_database)
        table_path = db_storage.get_table_path(sample_table)
        expected = os.path.join(db_storage.base_path, sample_table.name)
        assert table_path == expected

    def test_create_table(self, temp_data_dir, sample_user, sample_database, sample_table):
        """Test creating a table"""
        db_storage = DatabaseStorage(sample_user, sample_database)
        db_storage.create_table(sample_table)
        
        table_path = db_storage.get_table_path(sample_table)
        assert os.path.exists(table_path)
        assert os.path.isdir(table_path)
        
        # Check metadata exists
        metadata_path = db_storage.get_table_metadata_path(sample_table)
        assert os.path.exists(metadata_path)

    def test_save_table_metadata(self, temp_data_dir, sample_user, sample_database):
        """Test saving table metadata"""
        db_storage = DatabaseStorage(sample_user, sample_database)
        table = Table(name="products", indexes={}, keys=["id", "name"])
        
        db_storage.create_table(table)
        
        metadata_path = db_storage.get_table_metadata_path(table)
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        assert metadata['name'] == "products"
        assert metadata['keys'] == ["id", "name"]

    def test_delete_table(self, temp_data_dir, sample_user, sample_database, sample_table):
        """Test deleting a table"""
        db_storage = DatabaseStorage(sample_user, sample_database)
        db_storage.create_table(sample_table)
        
        table_path = db_storage.get_table_path(sample_table)
        assert os.path.exists(table_path)
        
        db_storage.delete_table(sample_table)
        assert not os.path.exists(table_path)

    def test_len(self, temp_data_dir, sample_user, sample_database):
        """Test __len__ returns number of tables"""
        db_storage = DatabaseStorage(sample_user, sample_database)
        
        # Initially should be 0
        assert len(db_storage) == 0
        
        # Add some tables to metadata
        db_storage.metadata = {
            'name': 'test_db',
            'tables': ['table1', 'table2', 'table3']
        }
        
        assert len(db_storage) == 3


class TestTableStorage:
    """Test cases for the TableStorage class"""

    def test_initialization(self, temp_data_dir, sample_user, sample_database, sample_table):
        """Test TableStorage initialization"""
        table_storage = TableStorage(sample_user, sample_database, sample_table)
        assert os.path.exists(table_storage.base_path)
        assert table_storage.user == sample_user
        assert table_storage.database == sample_database
        assert table_storage.table == sample_table

    def test_metadata_getter_nonexistent(self, temp_data_dir, sample_user, sample_database, sample_table):
        """Test metadata getter when file doesn't exist"""
        table_storage = TableStorage(sample_user, sample_database, sample_table)
        metadata = table_storage.metadata
        assert metadata['name'] == sample_table.name
        assert metadata['indexes'] == {}

    def test_metadata_setter_and_getter(self, temp_data_dir, sample_user, sample_database, sample_table):
        """Test setting and getting table metadata"""
        table_storage = TableStorage(sample_user, sample_database, sample_table)
        
        new_metadata = {
            'name': 'test_table',
            'indexes': {'price_idx': ['price']},
            'record_count': 100
        }
        table_storage.metadata = new_metadata
        
        retrieved = table_storage.metadata
        assert retrieved == new_metadata

    def test_get_record_path(self, temp_data_dir, sample_user, sample_database, sample_table, sample_record):
        """Test getting record path"""
        table_storage = TableStorage(sample_user, sample_database, sample_table)
        record_path = table_storage.get_record_path(sample_record)
        expected = os.path.join(table_storage.base_path, f"{sample_record.id}.json")
        assert record_path == expected

    def test_save_record(self, temp_data_dir, sample_user, sample_database, sample_table, sample_record):
        """Test saving a record"""
        table_storage = TableStorage(sample_user, sample_database, sample_table)
        table_storage.save_record(sample_record)
        
        record_path = table_storage.get_record_path(sample_record)
        assert os.path.exists(record_path)
        
        # Verify content
        with open(record_path, 'r') as f:
            data = json.load(f)
        assert data == sample_record.data

    def test_save_record_overwrites(self, temp_data_dir, sample_user, sample_database, sample_table):
        """Test that saving a record with same ID overwrites"""
        table_storage = TableStorage(sample_user, sample_database, sample_table)
        
        record1 = Record(id="test", data={"value": 1})
        record2 = Record(id="test", data={"value": 2})
        
        table_storage.save_record(record1)
        table_storage.save_record(record2)
        
        loaded = table_storage.load_record("test")
        assert loaded.data["value"] == 2

    def test_load_record(self, temp_data_dir, sample_user, sample_database, sample_table, sample_record):
        """Test loading a record"""
        table_storage = TableStorage(sample_user, sample_database, sample_table)
        table_storage.save_record(sample_record)
        
        loaded = table_storage.load_record(sample_record.id)
        assert loaded.id == sample_record.id
        assert loaded.data == sample_record.data

    def test_load_nonexistent_record(self, temp_data_dir, sample_user, sample_database, sample_table):
        """Test loading a record that doesn't exist"""
        table_storage = TableStorage(sample_user, sample_database, sample_table)
        
        with pytest.raises(FileNotFoundError):
            table_storage.load_record("nonexistent")

    def test_load_record_sanitizes_id(self, temp_data_dir, sample_user, sample_database, sample_table):
        """Test that load_record sanitizes the record ID"""
        table_storage = TableStorage(sample_user, sample_database, sample_table)
        
        # Save a record with safe ID
        safe_record = Record(id="safe_id", data={"test": "value"})
        table_storage.save_record(safe_record)
        
        # Try to load with dangerous ID - should not find it
        with pytest.raises(FileNotFoundError):
            table_storage.load_record("../etc/passwd")

    def test_load_all_records(self, temp_data_dir, sample_user, sample_database, sample_table):
        """Test loading all records"""
        table_storage = TableStorage(sample_user, sample_database, sample_table)
        
        # Save multiple records
        records = [
            Record(id="1", data={"name": "Product 1"}),
            Record(id="2", data={"name": "Product 2"}),
            Record(id="3", data={"name": "Product 3"}),
        ]
        
        for record in records:
            table_storage.save_record(record)
        
        all_records = table_storage.load_all_records()
        assert len(all_records) == 3
        assert "1" in all_records
        assert "2" in all_records
        assert "3" in all_records

    def test_load_all_records_ignores_metadata(self, temp_data_dir, sample_user, sample_database, sample_table):
        """Test that load_all_records ignores metadata.json"""
        table_storage = TableStorage(sample_user, sample_database, sample_table)
        
        # Set metadata
        table_storage.metadata = {"name": "test", "indexes": {}}
        
        # Save a record
        record = Record(id="1", data={"test": "value"})
        table_storage.save_record(record)
        
        all_records = table_storage.load_all_records()
        assert len(all_records) == 1
        assert "metadata" not in all_records

    def test_delete_record(self, temp_data_dir, sample_user, sample_database, sample_table, sample_record):
        """Test deleting a record"""
        table_storage = TableStorage(sample_user, sample_database, sample_table)
        table_storage.save_record(sample_record)
        
        record_path = table_storage.get_record_path(sample_record)
        assert os.path.exists(record_path)
        
        table_storage.delete_record(sample_record.id)
        assert not os.path.exists(record_path)

    def test_delete_nonexistent_record(self, temp_data_dir, sample_user, sample_database, sample_table):
        """Test deleting a record that doesn't exist (should not raise)"""
        table_storage = TableStorage(sample_user, sample_database, sample_table)
        table_storage.delete_record("nonexistent")  # Should not raise

    def test_list_records(self, temp_data_dir, sample_user, sample_database, sample_table):
        """Test listing all record IDs"""
        table_storage = TableStorage(sample_user, sample_database, sample_table)
        
        # Save multiple records
        for i in range(5):
            record = Record(id=str(i), data={"index": i})
            table_storage.save_record(record)
        
        record_ids = table_storage.list_records()
        assert len(record_ids) == 5
        for i in range(5):
            assert str(i) in record_ids

    def test_list_records_empty(self, temp_data_dir, sample_user, sample_database, sample_table):
        """Test listing records when table is empty"""
        table_storage = TableStorage(sample_user, sample_database, sample_table)
        record_ids = table_storage.list_records()
        assert record_ids == []

    def test_len(self, temp_data_dir, sample_user, sample_database, sample_table):
        """Test __len__ returns number of records"""
        table_storage = TableStorage(sample_user, sample_database, sample_table)
        assert len(table_storage) == 0
        
        # Add records
        for i in range(3):
            record = Record(id=str(i), data={"index": i})
            table_storage.save_record(record)
        
        assert len(table_storage) == 3


class TestThreadSafety:
    """Test cases for thread safety"""

    def test_concurrent_writes(self, temp_data_dir, sample_user, sample_database, sample_table):
        """Test concurrent writes to different records"""
        table_storage = TableStorage(sample_user, sample_database, sample_table)
        errors = []
        
        def write_record(record_id, value):
            try:
                record = Record(id=str(record_id), data={"value": value})
                table_storage.save_record(record)
            except Exception as e:
                errors.append(e)
        
        threads = []
        for i in range(10):
            t = threading.Thread(target=write_record, args=(i, i * 10))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(errors) == 0
        assert len(table_storage) == 10

    def test_concurrent_read_write(self, temp_data_dir, sample_user, sample_database, sample_table):
        """Test concurrent reads and writes"""
        table_storage = TableStorage(sample_user, sample_database, sample_table)
        
        # Pre-populate with some records
        for i in range(5):
            record = Record(id=str(i), data={"value": i})
            table_storage.save_record(record)
        
        errors = []
        results = []
        
        def read_record(record_id):
            try:
                record = table_storage.load_record(str(record_id))
                results.append(record.data)
            except Exception as e:
                errors.append(e)
        
        def write_record(record_id, value):
            try:
                record = Record(id=str(record_id), data={"value": value})
                table_storage.save_record(record)
            except Exception as e:
                errors.append(e)
        
        threads = []
        
        # Mix of reads and writes
        for i in range(10):
            if i % 2 == 0:
                t = threading.Thread(target=read_record, args=(i % 5,))
            else:
                t = threading.Thread(target=write_record, args=(i, i * 10))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(errors) == 0

    def test_concurrent_metadata_updates(self, temp_data_dir, sample_user, sample_database):
        """Test concurrent metadata updates"""
        db_storage = DatabaseStorage(sample_user, sample_database)
        errors = []
        
        def update_metadata(thread_id):
            try:
                meta = db_storage.metadata
                meta['thread_' + str(thread_id)] = thread_id
                db_storage.metadata = meta
                time.sleep(0.001)  # Small delay to increase contention
            except Exception as e:
                errors.append(e)
        
        threads = []
        for i in range(5):
            t = threading.Thread(target=update_metadata, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Should complete without errors (though some updates might be lost due to race conditions)
        # The important thing is no crashes/exceptions
        assert len(errors) == 0


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_very_long_names(self, temp_data_dir, storage):
        """Test handling of very long names"""
        long_name = "a" * 500
        user = User(id=long_name, name="Test")
        
        # Should still work (sanitize_name might truncate)
        storage.create_user(user)
        path = Storage.get_path(user)
        assert os.path.exists(path)

    def test_special_characters_in_names(self, temp_data_dir, storage):
        """Test handling of special characters"""
        special_user = User(id="user@#$%^&*()", name="Special")
        storage.create_user(special_user)
        
        # Should create directory (sanitized)
        path = Storage.get_path(special_user)
        assert os.path.exists(path)

    def test_unicode_in_names(self, temp_data_dir, storage):
        """Test handling of unicode characters"""
        unicode_user = User(id="用户_🎉", name="Unicode User")
        storage.create_user(unicode_user)
        
        path = Storage.get_path(unicode_user)
        assert os.path.exists(path)

    def test_empty_record_data(self, temp_data_dir, sample_user, sample_database, sample_table):
        """Test saving and loading record with empty data"""
        table_storage = TableStorage(sample_user, sample_database, sample_table)
        empty_record = Record(id="empty", data={})
        
        table_storage.save_record(empty_record)
        loaded = table_storage.load_record("empty")
        assert loaded.data == {}

    def test_nested_record_data(self, temp_data_dir, sample_user, sample_database, sample_table):
        """Test saving and loading deeply nested record data"""
        table_storage = TableStorage(sample_user, sample_database, sample_table)
        
        nested_data = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "value": "deep"
                        }
                    }
                }
            },
            "array": [1, 2, [3, 4, [5, 6]]]
        }
        
        record = Record(id="nested", data=nested_data)
        table_storage.save_record(record)
        
        loaded = table_storage.load_record("nested")
        assert loaded.data == nested_data

    def test_large_record_data(self, temp_data_dir, sample_user, sample_database, sample_table):
        """Test saving and loading large record"""
        table_storage = TableStorage(sample_user, sample_database, sample_table)
        
        # Create a large data structure
        large_data = {
            "items": [{"id": i, "value": f"item_{i}" * 100} for i in range(100)]
        }
        
        record = Record(id="large", data=large_data)
        table_storage.save_record(record)
        
        loaded = table_storage.load_record("large")
        assert len(loaded.data["items"]) == 100


class TestIntegration:
    """Integration tests for the complete storage system"""

    def test_complete_workflow(self, temp_data_dir):
        """Test complete workflow from user creation to record manipulation"""
        # Setup
        user = User(id="integration_user", name="Integration User")
        database = Database(name="integration_db")
        table = Table(name="products", indexes={})
        
        storage = Storage()
        
        # Create user
        storage.create_user(user)
        assert os.path.exists(Storage.get_path(user))
        
        # Create database
        storage.create_database(user, database)
        db_path = Storage.get_path(user, database)
        assert os.path.exists(db_path)
        
        # Create table
        db_storage = DatabaseStorage(user, database)
        db_storage.create_table(table)
        
        # Add records
        table_storage = TableStorage(user, database, table)
        
        products = [
            Record(id="1", data={"name": "Laptop", "price": 999.99}),
            Record(id="2", data={"name": "Mouse", "price": 29.99}),
            Record(id="3", data={"name": "Keyboard", "price": 79.99}),
        ]
        
        for product in products:
            table_storage.save_record(product)
        
        # Verify all records exist
        all_records = table_storage.load_all_records()
        assert len(all_records) == 3
        
        # Update a record
        updated = Record(id="2", data={"name": "Gaming Mouse", "price": 59.99})
        table_storage.save_record(updated)
        
        loaded = table_storage.load_record("2")
        assert loaded.data["name"] == "Gaming Mouse"
        assert loaded.data["price"] == 59.99
        
        # Delete a record
        table_storage.delete_record("3")
        assert len(table_storage.list_records()) == 2
        
        # Clean up
        storage.delete_database(user, database)
        assert not os.path.exists(db_path)

    def test_multiple_databases_and_tables(self, temp_data_dir, sample_user):
        """Test working with multiple databases and tables"""
        storage = Storage()
        storage.create_user(sample_user)
        
        # Create multiple databases
        db1 = Database(name="db1")
        db2 = Database(name="db2")
        
        storage.create_database(sample_user, db1)
        storage.create_database(sample_user, db2)
        
        # Create tables in each database
        table1 = Table(name="table1", indexes={})
        table2 = Table(name="table2", indexes={})
        
        db1_storage = DatabaseStorage(sample_user, db1)
        db1_storage.create_table(table1)
        db1_storage.create_table(table2)
        
        db2_storage = DatabaseStorage(sample_user, db2)
        db2_storage.create_table(table1)
        
        # Add records to each table
        ts1_1 = TableStorage(sample_user, db1, table1)
        ts1_2 = TableStorage(sample_user, db1, table2)
        ts2_1 = TableStorage(sample_user, db2, table1)
        
        ts1_1.save_record(Record(id="1", data={"db": "db1", "table": "table1"}))
        ts1_2.save_record(Record(id="1", data={"db": "db1", "table": "table2"}))
        ts2_1.save_record(Record(id="1", data={"db": "db2", "table": "table1"}))
        
        # Verify isolation
        r1 = ts1_1.load_record("1")
        r2 = ts1_2.load_record("1")
        r3 = ts2_1.load_record("1")
        
        assert r1.data["table"] == "table1"
        assert r2.data["table"] == "table2"
        assert r3.data["db"] == "db2"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
