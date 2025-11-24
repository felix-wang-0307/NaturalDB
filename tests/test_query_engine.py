"""
Test suite for NaturalDB Query Engine (Layer 2)
Tests QueryEngine, QueryOperations, and JoinOperations
"""

import pytest
import os
import tempfile
import shutil
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from naturaldb.entities import User, Database, Table, Record
from naturaldb.query_engine.query_engine import QueryEngine
from naturaldb.query_engine.operations import QueryOperations, JoinOperations
from naturaldb.storage_system.storage import Storage, DatabaseStorage


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_user():
    """Create a test user"""
    return User(id="test_user", name="Test User")


@pytest.fixture
def test_database():
    """Create a test database"""
    return Database(name="test_db")


@pytest.fixture
def query_engine(test_user, test_database, temp_data_dir, monkeypatch):
    """Create a QueryEngine instance with temporary storage"""
    monkeypatch.setenv('NATURALDB_DATA_PATH', temp_data_dir)
    return QueryEngine(test_user, test_database)


class TestQueryEngineBasicOperations:
    """Test basic CRUD operations of QueryEngine"""

    def test_create_table(self, query_engine, temp_data_dir):
        """Test creating a new table"""
        table = Table(name="users", indexes={})
        result = query_engine.create_table(table)
        assert result is True
        
        # Verify table directory exists in filesystem
        table_path = os.path.join(temp_data_dir, "test_user", "test_db", "users")
        assert os.path.exists(table_path), f"Table directory should exist at {table_path}"
        assert os.path.isdir(table_path), "Table path should be a directory"
        
        # Verify metadata.json exists
        metadata_path = os.path.join(table_path, "metadata.json")
        assert os.path.exists(metadata_path), "Table metadata file should exist"

    def test_create_duplicate_table(self, query_engine, temp_data_dir):
        """Test creating a table that already exists"""
        table = Table(name="products", indexes={})
        query_engine.create_table(table)
        
        # Verify first creation
        table_path = os.path.join(temp_data_dir, "test_user", "test_db", "products")
        assert os.path.exists(table_path)
        
        # Creating again should still succeed (idempotent)
        result = query_engine.create_table(table)
        assert result is True
        
        # Verify table still exists with same structure
        assert os.path.exists(table_path)
        assert os.path.exists(os.path.join(table_path, "metadata.json"))

    def test_insert_record(self, query_engine, temp_data_dir):
        """Test inserting a record into a table"""
        record = Record(id="1", data={"name": "Alice", "age": 30})
        result = query_engine.insert("users", record)
        assert result is True
        
        # Verify record file exists in filesystem
        record_path = os.path.join(temp_data_dir, "test_user", "test_db", "users", "1.json")
        assert os.path.exists(record_path), f"Record file should exist at {record_path}"
        assert os.path.isfile(record_path), "Record path should be a file"
        
        # Verify record content
        with open(record_path, 'r') as f:
            content = f.read()
            assert '"name"' in content or '"Alice"' in content, "Record should contain inserted data"
            assert '"age"' in content or '30' in content, "Record should contain age field"

    def test_insert_creates_table_if_not_exists(self, query_engine, temp_data_dir):
        """Test that insert creates table if it doesn't exist"""
        record = Record(id="1", data={"title": "Product A"})
        result = query_engine.insert("new_table", record)
        assert result is True
        
        # Verify table was created in filesystem
        table_path = os.path.join(temp_data_dir, "test_user", "test_db", "new_table")
        assert os.path.exists(table_path), "Table directory should be auto-created"
        assert os.path.exists(os.path.join(table_path, "metadata.json")), "Metadata should exist"
        
        # Verify record was created
        record_path = os.path.join(table_path, "1.json")
        assert os.path.exists(record_path), "Record should exist in new table"
        
        # Verify table can be queried
        found = query_engine.find_by_id("new_table", "1")
        assert found is not None
        assert found.data["title"] == "Product A"

    def test_find_by_id(self, query_engine):
        """Test finding a record by ID"""
        record = Record(id="user1", data={"name": "Bob", "email": "bob@example.com"})
        query_engine.insert("users", record)
        
        found = query_engine.find_by_id("users", "user1")
        assert found is not None
        assert found.id == "user1"
        assert found.data["name"] == "Bob"

    def test_find_by_id_nonexistent(self, query_engine):
        """Test finding a record that doesn't exist"""
        found = query_engine.find_by_id("users", "nonexistent")
        assert found is None

    def test_find_by_id_nonexistent_table(self, query_engine):
        """Test finding in a table that doesn't exist"""
        found = query_engine.find_by_id("nonexistent_table", "1")
        assert found is None

    def test_find_all_empty_table(self, query_engine):
        """Test finding all records in an empty table"""
        table = Table(name="empty_table", indexes={})
        query_engine.create_table(table)
        records = query_engine.find_all("empty_table")
        assert records == []

    def test_find_all_with_records(self, query_engine, temp_data_dir):
        """Test finding all records in a populated table"""
        records_to_insert = [
            Record(id="1", data={"name": "Alice"}),
            Record(id="2", data={"name": "Bob"}),
            Record(id="3", data={"name": "Charlie"})
        ]
        
        for record in records_to_insert:
            query_engine.insert("users", record)
        
        # Verify all files exist in filesystem
        table_path = os.path.join(temp_data_dir, "test_user", "test_db", "users")
        for record_id in ["1", "2", "3"]:
            record_path = os.path.join(table_path, f"{record_id}.json")
            assert os.path.exists(record_path), f"Record {record_id}.json should exist"
        
        # Verify correct number of JSON files (excluding metadata.json)
        json_files = [f for f in os.listdir(table_path) if f.endswith('.json') and f != 'metadata.json']
        assert len(json_files) == 3, f"Should have 3 record files, found {len(json_files)}"
        
        all_records = query_engine.find_all("users")
        assert len(all_records) == 3
        
        names = {r.data["name"] for r in all_records}
        assert names == {"Alice", "Bob", "Charlie"}

    def test_update_record(self, query_engine, temp_data_dir):
        """Test updating an existing record"""
        record = Record(id="1", data={"name": "Alice", "age": 30})
        query_engine.insert("users", record)
        
        # Verify initial state
        record_path = os.path.join(temp_data_dir, "test_user", "test_db", "users", "1.json")
        assert os.path.exists(record_path)
        with open(record_path, 'r') as f:
            initial_content = f.read()
            assert '30' in initial_content
        
        # Update record
        updated_record = Record(id="1", data={"name": "Alice", "age": 31})
        result = query_engine.update("users", updated_record)
        assert result is True
        
        # Verify file was updated
        assert os.path.exists(record_path), "Record file should still exist"
        with open(record_path, 'r') as f:
            updated_content = f.read()
            assert '31' in updated_content, "File should contain updated age"
            assert '30' not in updated_content or updated_content.count('30') == 0, "Old age should be replaced"
        
        # Verify through query engine
        found = query_engine.find_by_id("users", "1")
        assert found.data["age"] == 31

    def test_update_nonexistent_record(self, query_engine):
        """Test updating a record that doesn't exist"""
        record = Record(id="999", data={"name": "Ghost"})
        result = query_engine.update("users", record)
        assert result is False

    def test_update_nonexistent_table(self, query_engine):
        """Test updating in a table that doesn't exist"""
        record = Record(id="1", data={"name": "Test"})
        result = query_engine.update("nonexistent_table", record)
        assert result is False

    def test_delete_record(self, query_engine, temp_data_dir):
        """Test deleting a record"""
        record = Record(id="1", data={"name": "Alice"})
        query_engine.insert("users", record)
        
        # Verify record exists in filesystem
        record_path = os.path.join(temp_data_dir, "test_user", "test_db", "users", "1.json")
        assert os.path.exists(record_path), "Record should exist before deletion"
        
        # Delete record
        result = query_engine.delete("users", "1")
        assert result is True
        
        # Verify file is actually deleted from filesystem
        assert not os.path.exists(record_path), f"Record file should be deleted from {record_path}"
        
        # Verify through query engine
        found = query_engine.find_by_id("users", "1")
        assert found is None

    def test_delete_nonexistent_record(self, query_engine):
        """Test deleting a record that doesn't exist"""
        result = query_engine.delete("users", "999")
        assert result is False

    def test_delete_nonexistent_table(self, query_engine):
        """Test deleting from a table that doesn't exist"""
        result = query_engine.delete("nonexistent_table", "1")
        assert result is False


class TestQueryEngineFiltering:
    """Test filtering operations"""

    def setup_method(self):
        """Set up test data for filtering tests"""
        self.test_records = [
            Record(id="1", data={"name": "Alice", "age": 30, "city": "New York"}),
            Record(id="2", data={"name": "Bob", "age": 25, "city": "Los Angeles"}),
            Record(id="3", data={"name": "Charlie", "age": 35, "city": "New York"}),
            Record(id="4", data={"name": "Diana", "age": 28, "city": "Chicago"}),
            Record(id="5", data={"name": "Eve", "age": 30, "city": "Boston"})
        ]

    def test_filter_equality(self, query_engine):
        """Test filtering with equality operator"""
        for record in self.test_records:
            query_engine.insert("users", record)
        
        results = query_engine.filter("users", "age", 30, "eq")
        assert len(results) == 2
        names = {r.data["name"] for r in results}
        assert names == {"Alice", "Eve"}

    def test_filter_not_equal(self, query_engine):
        """Test filtering with not equal operator"""
        for record in self.test_records:
            query_engine.insert("users", record)
        
        results = query_engine.filter("users", "city", "New York", "ne")
        assert len(results) == 3

    def test_filter_greater_than(self, query_engine):
        """Test filtering with greater than operator"""
        for record in self.test_records:
            query_engine.insert("users", record)
        
        results = query_engine.filter("users", "age", 30, "gt")
        assert len(results) == 1
        assert results[0].data["name"] == "Charlie"

    def test_filter_greater_than_or_equal(self, query_engine):
        """Test filtering with greater than or equal operator"""
        for record in self.test_records:
            query_engine.insert("users", record)
        
        results = query_engine.filter("users", "age", 30, "gte")
        assert len(results) == 3

    def test_filter_less_than(self, query_engine):
        """Test filtering with less than operator"""
        for record in self.test_records:
            query_engine.insert("users", record)
        
        results = query_engine.filter("users", "age", 30, "lt")
        assert len(results) == 2

    def test_filter_less_than_or_equal(self, query_engine):
        """Test filtering with less than or equal operator"""
        for record in self.test_records:
            query_engine.insert("users", record)
        
        results = query_engine.filter("users", "age", 30, "lte")
        assert len(results) == 4

    def test_filter_contains(self, query_engine):
        """Test filtering with contains operator"""
        for record in self.test_records:
            query_engine.insert("users", record)
        
        results = query_engine.filter("users", "name", "li", "contains")
        assert len(results) == 2  # Alice and Charlie

    def test_filter_nonexistent_table(self, query_engine):
        """Test filtering on non-existent table"""
        results = query_engine.filter("nonexistent", "field", "value")
        assert results == []

    def test_filter_no_matches(self, query_engine):
        """Test filtering with no matches"""
        for record in self.test_records:
            query_engine.insert("users", record)
        
        results = query_engine.filter("users", "age", 100, "eq")
        assert results == []


class TestQueryEngineProjection:
    """Test projection operations"""

    def test_project_simple_fields(self, query_engine):
        """Test projecting simple fields"""
        records = [
            Record(id="1", data={"name": "Alice", "age": 30, "city": "NYC"}),
            Record(id="2", data={"name": "Bob", "age": 25, "city": "LA"})
        ]
        
        for record in records:
            query_engine.insert("users", record)
        
        results = query_engine.project("users", ["name", "age"])
        assert len(results) == 2
        assert all("name" in r and "age" in r and "city" not in r for r in results)

    def test_project_single_field(self, query_engine):
        """Test projecting a single field"""
        records = [
            Record(id="1", data={"name": "Alice", "age": 30}),
            Record(id="2", data={"name": "Bob", "age": 25})
        ]
        
        for record in records:
            query_engine.insert("users", record)
        
        results = query_engine.project("users", ["name"])
        assert len(results) == 2
        assert all(list(r.keys()) == ["name"] for r in results)

    def test_project_with_conditions(self, query_engine):
        """Test projection with filtering conditions"""
        records = [
            Record(id="1", data={"name": "Alice", "age": 30, "city": "NYC"}),
            Record(id="2", data={"name": "Bob", "age": 25, "city": "LA"}),
            Record(id="3", data={"name": "Charlie", "age": 35, "city": "NYC"})
        ]
        
        for record in records:
            query_engine.insert("users", record)
        
        conditions = {"age": {"operator": "gt", "value": 26}}
        results = query_engine.project("users", ["name", "city"], conditions)
        assert len(results) == 2
        names = {r["name"] for r in results}
        assert names == {"Alice", "Charlie"}

    def test_project_nonexistent_field(self, query_engine):
        """Test projecting fields that don't exist"""
        record = Record(id="1", data={"name": "Alice", "age": 30})
        query_engine.insert("users", record)
        
        results = query_engine.project("users", ["name", "nonexistent"])
        assert len(results) == 1
        # Should only include existing fields
        assert "name" in results[0]

    def test_project_nonexistent_table(self, query_engine):
        """Test projection on non-existent table"""
        results = query_engine.project("nonexistent", ["field"])
        assert results == []


class TestQueryEngineGrouping:
    """Test grouping and aggregation operations"""

    def test_group_by_simple(self, query_engine):
        """Test simple grouping"""
        records = [
            Record(id="1", data={"name": "Alice", "city": "NYC", "score": 90}),
            Record(id="2", data={"name": "Bob", "city": "LA", "score": 85}),
            Record(id="3", data={"name": "Charlie", "city": "NYC", "score": 95})
        ]
        
        for record in records:
            query_engine.insert("users", record)
        
        groups = query_engine.group_by("users", "city")
        assert "NYC" in groups
        assert "LA" in groups
        assert len(groups["NYC"]) == 2
        assert len(groups["LA"]) == 1

    def test_group_by_with_aggregation(self, query_engine):
        """Test grouping with aggregation"""
        records = [
            Record(id="1", data={"department": "Sales", "salary": 50000}),
            Record(id="2", data={"department": "Sales", "salary": 60000}),
            Record(id="3", data={"department": "Engineering", "salary": 80000}),
            Record(id="4", data={"department": "Engineering", "salary": 90000})
        ]
        
        for record in records:
            query_engine.insert("employees", record)
        
        aggregations = {"salary": "sum"}
        groups = query_engine.group_by("employees", "department", aggregations)
        
        # Verify aggregations
        assert "Sales" in groups
        assert "Engineering" in groups

    def test_group_by_nonexistent_table(self, query_engine):
        """Test grouping on non-existent table"""
        groups = query_engine.group_by("nonexistent", "field")
        assert groups == {}


class TestQueryEngineOrdering:
    """Test ordering operations"""

    def test_order_by_ascending(self, query_engine):
        """Test ordering records in ascending order"""
        records = [
            Record(id="1", data={"name": "Charlie", "age": 35}),
            Record(id="2", data={"name": "Alice", "age": 30}),
            Record(id="3", data={"name": "Bob", "age": 25})
        ]
        
        for record in records:
            query_engine.insert("users", record)
        
        results = query_engine.order_by("users", "age", ascending=True)
        assert len(results) == 3
        assert results[0].data["age"] == 25
        assert results[1].data["age"] == 30
        assert results[2].data["age"] == 35

    def test_order_by_descending(self, query_engine):
        """Test ordering records in descending order"""
        records = [
            Record(id="1", data={"name": "Charlie", "age": 35}),
            Record(id="2", data={"name": "Alice", "age": 30}),
            Record(id="3", data={"name": "Bob", "age": 25})
        ]
        
        for record in records:
            query_engine.insert("users", record)
        
        results = query_engine.order_by("users", "age", ascending=False)
        assert len(results) == 3
        assert results[0].data["age"] == 35
        assert results[1].data["age"] == 30
        assert results[2].data["age"] == 25

    def test_order_by_string_field(self, query_engine):
        """Test ordering by string field"""
        records = [
            Record(id="1", data={"name": "Charlie"}),
            Record(id="2", data={"name": "Alice"}),
            Record(id="3", data={"name": "Bob"})
        ]
        
        for record in records:
            query_engine.insert("users", record)
        
        results = query_engine.order_by("users", "name", ascending=True)
        assert results[0].data["name"] == "Alice"
        assert results[1].data["name"] == "Bob"
        assert results[2].data["name"] == "Charlie"

    def test_order_by_nonexistent_table(self, query_engine):
        """Test ordering on non-existent table"""
        results = query_engine.order_by("nonexistent", "field")
        assert results == []


class TestQueryOperations:
    """Test QueryOperations class directly"""

    @pytest.fixture
    def query_operations(self, test_user, test_database, temp_data_dir, monkeypatch):
        """Create QueryOperations instance"""
        monkeypatch.setenv('NATURALDB_DATA_PATH', temp_data_dir)
        storage = Storage()
        database = Database(name="test_db")
        storage.create_database(test_user, database)
        
        table = Table(name="test_table", indexes={})
        db_storage = DatabaseStorage(test_user, database)
        db_storage.create_table(table)
        
        return QueryOperations(test_user, database, table)

    def test_find_all_empty(self, query_operations):
        """Test find_all on empty table"""
        results = query_operations.find_all()
        assert results == []

    def test_find_by_id_with_operations(self, query_operations):
        """Test find_by_id using QueryOperations"""
        record = Record(id="test1", data={"value": "data"})
        query_operations.table_storage.save_record(record)
        
        found = query_operations.find_by_id("test1")
        assert found is not None
        assert found.id == "test1"

    def test_filter_with_custom_condition(self, query_operations):
        """Test filter with custom condition function"""
        records = [
            Record(id="1", data={"age": 20}),
            Record(id="2", data={"age": 30}),
            Record(id="3", data={"age": 40})
        ]
        
        for record in records:
            query_operations.table_storage.save_record(record)
        
        results = query_operations.filter(lambda r: r.data["age"] >= 30)
        assert len(results) == 2

    def test_filter_by_field_nested(self, query_operations):
        """Test filtering by nested field"""
        records = [
            Record(id="1", data={"user": {"name": "Alice", "age": 30}}),
            Record(id="2", data={"user": {"name": "Bob", "age": 25}})
        ]
        
        for record in records:
            query_operations.table_storage.save_record(record)
        
        results = query_operations.filter_by_field("user.name", "Alice", "eq")
        assert len(results) == 1
        assert results[0].data["user"]["name"] == "Alice"

    def test_project_nested_fields(self, query_operations):
        """Test projecting nested fields"""
        records = [
            Record(id="1", data={"user": {"name": "Alice", "email": "alice@example.com"}, "active": True}),
            Record(id="2", data={"user": {"name": "Bob", "email": "bob@example.com"}, "active": False})
        ]
        
        for record in records:
            query_operations.table_storage.save_record(record)
        
        results = query_operations.project(query_operations.find_all(), ["user.name", "active"])
        assert len(results) == 2
        # Projection creates nested structure, not flat keys
        assert all("user" in r and "active" in r for r in results)
        assert all("name" in r["user"] for r in results)
        assert all("email" not in r["user"] for r in results)

    def test_group_by_operations(self, query_operations):
        """Test grouping operations"""
        records = [
            Record(id="1", data={"category": "A", "value": 10}),
            Record(id="2", data={"category": "B", "value": 20}),
            Record(id="3", data={"category": "A", "value": 15})
        ]
        
        for record in records:
            query_operations.table_storage.save_record(record)
        
        groups = query_operations.group_by(records, "category")
        assert "A" in groups
        assert "B" in groups
        assert len(groups["A"]) == 2
        assert len(groups["B"]) == 1


class TestJoinOperations:
    """Test join operations between tables"""

    @pytest.fixture
    def join_setup(self, test_user, test_database, temp_data_dir, monkeypatch):
        """Set up tables for join operations"""
        monkeypatch.setenv('NATURALDB_DATA_PATH', temp_data_dir)
        
        storage = Storage()
        storage.create_database(test_user, test_database)
        
        # Create users table
        users_table = Table(name="users", indexes={})
        users_ops = QueryOperations(test_user, test_database, users_table)
        db_storage = DatabaseStorage(test_user, test_database)
        db_storage.create_table(users_table)
        
        # Create orders table
        orders_table = Table(name="orders", indexes={})
        orders_ops = QueryOperations(test_user, test_database, orders_table)
        db_storage.create_table(orders_table)
        
        # Insert test data
        users_data = [
            Record(id="1", data={"user_id": 1, "name": "Alice"}),
            Record(id="2", data={"user_id": 2, "name": "Bob"}),
            Record(id="3", data={"user_id": 3, "name": "Charlie"})
        ]
        
        orders_data = [
            Record(id="1", data={"order_id": 101, "user_id": 1, "amount": 100}),
            Record(id="2", data={"order_id": 102, "user_id": 2, "amount": 200}),
            Record(id="3", data={"order_id": 103, "user_id": 1, "amount": 150})
        ]
        
        for record in users_data:
            users_ops.table_storage.save_record(record)
        
        for record in orders_data:
            orders_ops.table_storage.save_record(record)
        
        return users_ops, orders_ops

    def test_inner_join(self, join_setup):
        """Test inner join operation"""
        users_ops, orders_ops = join_setup
        
        users = users_ops.find_all()
        orders = orders_ops.find_all()
        
        join_ops = JoinOperations()
        results = join_ops.inner_join(users, orders, "user_id", "user_id")
        
        assert len(results) == 3
        # Results should be flattened with all fields at top level
        assert all("name" in r and "order_id" in r and "user_id" in r for r in results)
        # Check that we have the expected matches
        user_ids = [r["user_id"] for r in results]
        assert user_ids.count(1) == 2  # Alice has 2 orders
        assert user_ids.count(2) == 1  # Bob has 1 order

    def test_left_join(self, join_setup):
        """Test left join operation"""
        users_ops, orders_ops = join_setup
        
        users = users_ops.find_all()
        orders = orders_ops.find_all()
        
        join_ops = JoinOperations()
        results = join_ops.left_join(users, orders, "user_id", "user_id")
        
        # Should include all users, even those without orders
        assert len(results) >= 3


class TestQueryEngineEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_database(self, query_engine):
        """Test operations on empty database"""
        records = query_engine.find_all("nonexistent_table")
        assert records == []

    def test_special_characters_in_names(self, query_engine):
        """Test handling special characters in table/field names"""
        # Table names should be sanitized
        record = Record(id="1", data={"name": "Test"})
        result = query_engine.insert("test-table_123", record)
        assert result is True

    def test_large_record_data(self, query_engine):
        """Test handling large record data"""
        large_data = {f"field_{i}": f"value_{i}" for i in range(1000)}
        record = Record(id="large", data=large_data)
        
        result = query_engine.insert("large_records", record)
        assert result is True
        
        found = query_engine.find_by_id("large_records", "large")
        assert found is not None
        assert len(found.data) == 1000

    def test_unicode_in_data(self, query_engine):
        """Test handling Unicode characters in data"""
        record = Record(id="1", data={
            "name": "用户",
            "city": "北京",
            "emoji": "😀🎉"
        })
        
        result = query_engine.insert("unicode_test", record)
        assert result is True
        
        found = query_engine.find_by_id("unicode_test", "1")
        assert found.data["name"] == "用户"
        assert found.data["emoji"] == "😀🎉"

    def test_null_values_in_data(self, query_engine):
        """Test handling None/null values"""
        record = Record(id="1", data={
            "name": "Alice",
            "middle_name": None,
            "age": 30
        })
        
        result = query_engine.insert("users", record)
        assert result is True
        
        found = query_engine.find_by_id("users", "1")
        assert found.data["middle_name"] is None

    def test_boolean_values(self, query_engine):
        """Test handling boolean values"""
        record = Record(id="1", data={"active": True, "verified": False})
        
        query_engine.insert("users", record)
        results = query_engine.filter("users", "active", True, "eq")
        
        assert len(results) == 1
        assert results[0].data["active"] is True

    def test_nested_data_structures(self, query_engine):
        """Test handling deeply nested data"""
        record = Record(id="1", data={
            "user": {
                "profile": {
                    "personal": {
                        "name": "Alice",
                        "age": 30
                    },
                    "professional": {
                        "title": "Engineer",
                        "years": 5
                    }
                }
            }
        })
        
        result = query_engine.insert("users", record)
        assert result is True
        
        found = query_engine.find_by_id("users", "1")
        assert found.data["user"]["profile"]["personal"]["name"] == "Alice"


class TestQueryEngineRenameOperations:
    """Test field renaming (SQL AS clause functionality)"""
    
    def test_rename_simple_fields(self, query_engine, temp_data_dir):
        """Test renaming simple fields"""
        query_engine.create_table("users")
        query_engine.insert("users", {"id": "1", "user_id": 101, "user_name": "Alice", "age": 30})
        query_engine.insert("users", {"id": "2", "user_id": 102, "user_name": "Bob", "age": 25})
        
        # Rename user_id -> id, user_name -> name
        results = query_engine.rename("users", {"user_id": "id", "user_name": "name"})
        
        assert len(results) == 2
        assert "id" in results[0]
        assert "name" in results[0]
        assert "user_id" not in results[0]
        assert "user_name" not in results[0]
        assert results[0]["id"] == 101
        assert results[0]["name"] == "Alice"
    
    def test_rename_with_conditions(self, query_engine, temp_data_dir):
        """Test renaming with filtering conditions"""
        query_engine.create_table("users")
        query_engine.insert("users", {"id": "1", "user_id": 101, "user_name": "Alice", "age": 30})
        query_engine.insert("users", {"id": "2", "user_id": 102, "user_name": "Bob", "age": 25})
        
        # Rename only for users with age > 25
        results = query_engine.rename(
            "users",
            {"user_id": "id", "user_name": "name"},
            conditions={"age": {"operator": "gt", "value": 25}}
        )
        
        assert len(results) == 1
        assert results[0]["id"] == 101
        assert results[0]["name"] == "Alice"
    
    def test_select_without_aliases(self, query_engine, temp_data_dir):
        """Test SQL-like SELECT without aliases"""
        query_engine.create_table("users")
        query_engine.insert("users", {"id": "1", "user_id": 101, "user_name": "Alice", "age": 30})
        query_engine.insert("users", {"id": "2", "user_id": 102, "user_name": "Bob", "age": 25})
        
        # SELECT user_id, user_name FROM users
        results = query_engine.select("users", fields=["user_id", "user_name"])
        
        assert len(results) == 2
        assert set(results[0].keys()) == {"user_id", "user_name"}
    
    def test_select_with_aliases(self, query_engine, temp_data_dir):
        """Test SQL-like SELECT with field aliases"""
        query_engine.create_table("users")
        query_engine.insert("users", {"id": "1", "user_id": 101, "user_name": "Alice", "age": 30})
        query_engine.insert("users", {"id": "2", "user_id": 102, "user_name": "Bob", "age": 25})
        
        # SELECT user_id AS id, user_name AS name FROM users
        results = query_engine.select(
            "users",
            fields=["user_id", "user_name"],
            aliases={"user_id": "id", "user_name": "name"}
        )
        
        assert len(results) == 2
        assert "id" in results[0]
        assert "name" in results[0]
        assert results[0]["id"] == 101
        assert results[0]["name"] == "Alice"
    
    def test_select_with_aliases_and_conditions(self, query_engine, temp_data_dir):
        """Test SELECT with aliases and WHERE clause"""
        query_engine.create_table("users")
        query_engine.insert("users", {"id": "1", "user_id": 101, "user_name": "Alice", "age": 30})
        query_engine.insert("users", {"id": "2", "user_id": 102, "user_name": "Bob", "age": 25})
        query_engine.insert("users", {"id": "3", "user_id": 103, "user_name": "Charlie", "age": 35})
        
        # SELECT user_id AS id, user_name AS name FROM users WHERE age >= 30
        results = query_engine.select(
            "users",
            fields=["user_id", "user_name"],
            aliases={"user_id": "id", "user_name": "name"},
            conditions={"age": {"operator": "gte", "value": 30}}
        )
        
        assert len(results) == 2
        assert results[0]["name"] in ["Alice", "Charlie"]
        assert all("id" in r and "name" in r for r in results)
    
    def test_select_all_fields_with_aliases(self, query_engine, temp_data_dir):
        """Test SELECT * with aliases"""
        query_engine.create_table("users")
        query_engine.insert("users", {"id": "1", "user_id": 101, "user_name": "Alice", "age": 30})
        
        # SELECT * with some fields aliased
        results = query_engine.select(
            "users",
            aliases={"user_id": "id", "user_name": "name"}
        )
        
        assert len(results) == 1
        assert "id" in results[0]  # user_id renamed to id
        assert "name" in results[0]  # user_name renamed to name
        assert "age" in results[0]  # age not aliased, keeps original name
    
    def test_rename_nested_fields(self, query_engine, temp_data_dir):
        """Test renaming nested fields"""
        query_engine.create_table("users")
        query_engine.insert("users", {
            "id": "1",
            "profile": {
                "name": "Alice",
                "contact": {
                    "email": "alice@example.com"
                }
            }
        })
        
        # Rename nested fields
        results = query_engine.rename("users", {
            "profile.name": "username",
            "profile.contact.email": "email"
        })
        
        assert len(results) == 1
        assert "username" in results[0]
        assert "email" in results[0]
        assert results[0]["username"] == "Alice"
        assert results[0]["email"] == "alice@example.com"
    
    def test_rename_nonexistent_table(self, query_engine, temp_data_dir):
        """Test rename on non-existent table"""
        results = query_engine.rename("nonexistent", {"field": "alias"})
        assert results == []
    
    def test_select_empty_table(self, query_engine, temp_data_dir):
        """Test SELECT on empty table"""
        query_engine.create_table("users")
        
        results = query_engine.select("users", aliases={"user_id": "id"})
        assert results == []
    
    def test_rename_partial_fields(self, query_engine, temp_data_dir):
        """Test renaming only some fields from a record"""
        query_engine.create_table("users")
        query_engine.insert("users", {
            "id": "1",
            "user_id": 101,
            "user_name": "Alice",
            "age": 30,
            "email": "alice@example.com"
        })
        
        # Only rename user_id and user_name
        results = query_engine.rename("users", {
            "user_id": "id",
            "user_name": "name"
        })
        
        assert len(results) == 1
        # Only the renamed fields should be present
        assert set(results[0].keys()) == {"id", "name"}
        assert results[0]["id"] == 101
        assert results[0]["name"] == "Alice"



if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
