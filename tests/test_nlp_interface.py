"""
Test suite for NaturalDB NLP Interface (Layer 3)
Tests automatic tool registration, function execution, and natural language interface
"""

import pytest
import os
import tempfile
import shutil
import sys
import json
from typing import Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from naturaldb.entities import User, Database, Table, Record
from naturaldb.query_engine.query_engine import QueryEngine
from naturaldb.nlp_interface.function_calling import OpenAiTool, ToolRegistry
from naturaldb.nlp_interface.tool_registry import DatabaseToolRegistry
from naturaldb.nlp_interface.executor import FunctionExecutor
from naturaldb.nlp_interface.naturaldb import NaturalDB


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_user():
    """Create a test user"""
    return User(id="nlp_test_user", name="NLP Test User")


@pytest.fixture
def test_database():
    """Create a test database"""
    return Database(name="nlp_test_db")


@pytest.fixture
def query_engine(test_user, test_database, temp_data_dir, monkeypatch):
    """Create a QueryEngine instance with temporary storage"""
    monkeypatch.setenv('NATURALDB_DATA_PATH', temp_data_dir)
    return QueryEngine(test_user, test_database)


@pytest.fixture
def executor(query_engine):
    """Create a FunctionExecutor instance"""
    return FunctionExecutor(query_engine)


@pytest.fixture
def naturaldb(test_user, test_database, temp_data_dir, monkeypatch):
    """Create a NaturalDB instance"""
    monkeypatch.setenv('NATURALDB_DATA_PATH', temp_data_dir)
    return NaturalDB(test_user, test_database)


class TestOpenAiTool:
    """Test OpenAiTool wrapper for function calling"""

    def test_create_tool_from_simple_function(self):
        """Test creating a tool from a simple function"""
        def sample_func(name: str, age: int) -> str:
            """A sample function for testing."""
            return f"{name} is {age} years old"

        tool = OpenAiTool(sample_func)
        tool_dict = tool.to_dict()

        assert tool_dict["name"] == "sample_func"
        assert "sample function" in tool_dict["description"].lower()
        assert "parameters" in tool_dict
        assert tool_dict["parameters"]["type"] == "object"
        assert "name" in tool_dict["parameters"]["properties"]
        assert "age" in tool_dict["parameters"]["properties"]
        assert tool_dict["parameters"]["properties"]["name"]["type"] == "string"
        assert tool_dict["parameters"]["properties"]["age"]["type"] == "integer"

    def test_create_tool_with_custom_description(self):
        """Test creating a tool with custom descriptions"""
        def add_numbers(a: int, b: int) -> int:
            """Add two numbers"""
            return a + b

        tool = OpenAiTool(
            add_numbers,
            description="Custom addition function",
            param_descriptions={"a": "First number", "b": "Second number"}
        )
        tool_dict = tool.to_dict()

        assert tool_dict["description"] == "Custom addition function"
        assert tool_dict["parameters"]["properties"]["a"]["description"] == "First number"
        assert tool_dict["parameters"]["properties"]["b"]["description"] == "Second number"

    def test_create_tool_with_optional_params(self):
        """Test creating a tool with optional parameters"""
        def greet(name: str, greeting: str = "Hello") -> str:
            """Greet someone"""
            return f"{greeting}, {name}!"

        tool = OpenAiTool(greet)
        tool_dict = tool.to_dict()

        # 'name' should be required, 'greeting' should be optional
        assert "name" in tool_dict["parameters"]["required"]
        assert "greeting" not in tool_dict["parameters"]["required"]


class TestToolRegistry:
    """Test automatic tool registration"""

    def test_register_class_methods(self):
        """Test registering all methods from a class"""
        class SampleClass:
            def method_one(self, x: int) -> int:
                """First method"""
                return x * 2

            def method_two(self, y: str) -> str:
                """Second method"""
                return y.upper()

            def _private_method(self):
                """Should be excluded"""
                pass

        tools = ToolRegistry.register_class_methods(SampleClass)

        # Should have 2 public methods
        assert len(tools) == 2
        
        tool_names = [t["function"]["name"] for t in tools]
        assert "method_one" in tool_names
        assert "method_two" in tool_names
        assert "_private_method" not in tool_names

    def test_register_with_exclusions(self):
        """Test excluding specific methods"""
        class SampleClass:
            def keep_this(self):
                """Keep this method"""
                pass

            def exclude_this(self):
                """Exclude this method"""
                pass

        tools = ToolRegistry.register_class_methods(
            SampleClass,
            exclude_methods=["exclude_this"]
        )

        tool_names = [t["function"]["name"] for t in tools]
        assert "keep_this" in tool_names
        assert "exclude_this" not in tool_names

    def test_register_specific_methods(self):
        """Test registering only specific methods"""
        class SampleClass:
            def method_a(self):
                pass

            def method_b(self):
                pass

            def method_c(self):
                pass

        tools = ToolRegistry.register_class_methods(
            SampleClass,
            method_names=["method_a", "method_c"]
        )

        assert len(tools) == 2
        tool_names = [t["function"]["name"] for t in tools]
        assert "method_a" in tool_names
        assert "method_c" in tool_names
        assert "method_b" not in tool_names


class TestDatabaseToolRegistry:
    """Test database-specific tool registration"""

    def test_get_all_tools(self):
        """Test getting all database tools"""
        tools = DatabaseToolRegistry.get_all_tools()

        # Should have multiple tools
        assert len(tools) > 10

        # Check some essential tools exist
        tool_names = [t["function"]["name"] for t in tools]
        assert "create_table" in tool_names
        assert "insert" in tool_names
        assert "find_all" in tool_names
        assert "filter" in tool_names
        assert "update" in tool_names
        assert "delete" in tool_names
        assert "join" in tool_names
        assert "group_by" in tool_names

    def test_tool_has_valid_schema(self):
        """Test that tools have valid OpenAI function calling schema"""
        tools = DatabaseToolRegistry.get_all_tools()

        for tool in tools:
            # Check top-level structure
            assert tool["type"] == "function"
            assert "function" in tool

            func = tool["function"]
            # Check function has required fields
            assert "name" in func
            assert "description" in func
            assert "parameters" in func

            # Check parameters structure
            params = func["parameters"]
            assert params["type"] == "object"
            assert "properties" in params
            assert "required" in params

    def test_sensitive_operations(self):
        """Test that sensitive operations are correctly identified"""
        sensitive = DatabaseToolRegistry.get_sensitive_operations()

        assert "update" in sensitive
        assert "delete" in sensitive
        assert "insert" not in sensitive
        assert "find_all" not in sensitive

    def test_get_tool_by_name(self):
        """Test getting a specific tool by name"""
        tools = DatabaseToolRegistry.get_all_tools()

        insert_tool = DatabaseToolRegistry.get_tool_by_name(tools, "insert")
        assert insert_tool is not None
        assert insert_tool["function"]["name"] == "insert"

        nonexistent = DatabaseToolRegistry.get_tool_by_name(tools, "nonexistent_tool")
        assert nonexistent is None


class TestFunctionExecutor:
    """Test function call execution"""

    def test_execute_create_table(self, executor):
        """Test creating a table through executor"""
        result = executor.execute("create_table", {
            "table_name": "test_table",
            "indexes": {}
        })

        assert result["success"] is True
        assert result["result"] is True

    def test_execute_insert(self, executor):
        """Test inserting a record through executor"""
        # First create table
        executor.execute("create_table", {"table_name": "products", "indexes": {}})

        # Then insert
        result = executor.execute("insert", {
            "table_name": "products",
            "record_id": "1",
            "data": {"name": "Laptop", "price": 999}
        })

        assert result["success"] is True

    def test_execute_find_all(self, executor):
        """Test finding all records through executor"""
        # Setup
        executor.execute("create_table", {"table_name": "users", "indexes": {}})
        executor.execute("insert", {
            "table_name": "users",
            "record_id": "1",
            "data": {"name": "Alice", "age": 30}
        })
        executor.execute("insert", {
            "table_name": "users",
            "record_id": "2",
            "data": {"name": "Bob", "age": 25}
        })

        # Execute find_all
        result = executor.execute("find_all", {"table_name": "users"})

        assert result["success"] is True
        assert len(result["result"]) == 2

    def test_execute_filter(self, executor):
        """Test filtering records through executor"""
        # Setup
        executor.execute("create_table", {"table_name": "products", "indexes": {}})
        executor.execute("insert", {
            "table_name": "products",
            "record_id": "1",
            "data": {"name": "Laptop", "price": 999}
        })
        executor.execute("insert", {
            "table_name": "products",
            "record_id": "2",
            "data": {"name": "Mouse", "price": 25}
        })

        # Filter by price > 500
        result = executor.execute("filter", {
            "table_name": "products",
            "field_name": "price",
            "value": 500,
            "operator": "gt"
        })

        assert result["success"] is True
        assert len(result["result"]) == 1
        assert result["result"][0]["data"]["name"] == "Laptop"

    def test_execute_group_by(self, executor):
        """Test group by operation through executor"""
        # Setup
        executor.execute("create_table", {"table_name": "orders", "indexes": {}})
        executor.execute("insert", {
            "table_name": "orders",
            "record_id": "1",
            "data": {"category": "Electronics", "amount": 100}
        })
        executor.execute("insert", {
            "table_name": "orders",
            "record_id": "2",
            "data": {"category": "Electronics", "amount": 200}
        })
        executor.execute("insert", {
            "table_name": "orders",
            "record_id": "3",
            "data": {"category": "Books", "amount": 50}
        })

        # Group by category
        result = executor.execute("group_by", {
            "table_name": "orders",
            "field_name": "category",
            "aggregations": {"amount": "sum"}
        })

        assert result["success"] is True
        assert "Electronics" in result["result"]
        assert "Books" in result["result"]

    def test_execute_sort(self, executor):
        """Test sorting through executor"""
        # Setup
        executor.execute("create_table", {"table_name": "scores", "indexes": {}})
        executor.execute("insert", {
            "table_name": "scores",
            "record_id": "1",
            "data": {"player": "Alice", "score": 100}
        })
        executor.execute("insert", {
            "table_name": "scores",
            "record_id": "2",
            "data": {"player": "Bob", "score": 200}
        })
        executor.execute("insert", {
            "table_name": "scores",
            "record_id": "3",
            "data": {"player": "Charlie", "score": 150}
        })

        # Sort by score descending
        result = executor.execute("sort", {
            "table_name": "scores",
            "field_name": "score",
            "ascending": False
        })

        assert result["success"] is True
        assert result["result"][0]["data"]["score"] == 200
        assert result["result"][1]["data"]["score"] == 150
        assert result["result"][2]["data"]["score"] == 100

    def test_execute_join(self, executor):
        """Test join operation through executor"""
        # Setup users table
        executor.execute("create_table", {"table_name": "users", "indexes": {}})
        executor.execute("insert", {
            "table_name": "users",
            "record_id": "1",
            "data": {"user_id": "u1", "name": "Alice"}
        })

        # Setup orders table
        executor.execute("create_table", {"table_name": "orders", "indexes": {}})
        executor.execute("insert", {
            "table_name": "orders",
            "record_id": "1",
            "data": {"user_id": "u1", "product": "Laptop", "total": 999}
        })

        # Join
        result = executor.execute("join", {
            "left_table": "users",
            "right_table": "orders",
            "left_field": "user_id",
            "right_field": "user_id",
            "join_type": "inner"
        })

        assert result["success"] is True
        assert len(result["result"]) == 1
        assert result["result"][0]["name"] == "Alice"
        assert result["result"][0]["product"] == "Laptop"

    def test_execute_batch(self, executor):
        """Test batch execution"""
        operations = [
            {
                "name": "create_table",
                "arguments": {"table_name": "batch_test", "indexes": {}}
            },
            {
                "name": "insert",
                "arguments": {
                    "table_name": "batch_test",
                    "record_id": "1",
                    "data": {"value": "first"}
                }
            },
            {
                "name": "insert",
                "arguments": {
                    "table_name": "batch_test",
                    "record_id": "2",
                    "data": {"value": "second"}
                }
            },
            {
                "name": "find_all",
                "arguments": {"table_name": "batch_test"}
            }
        ]

        results = executor.execute_batch(operations)

        assert len(results) == 4
        assert all(r["success"] for r in results)
        assert len(results[3]["result"]) == 2

    def test_sensitive_operation_without_callback(self, executor):
        """Test that sensitive operations require confirmation"""
        # Setup
        executor.execute("create_table", {"table_name": "temp", "indexes": {}})
        executor.execute("insert", {
            "table_name": "temp",
            "record_id": "1",
            "data": {"value": "test"}
        })

        # Try to delete without confirmation callback
        result = executor.execute("delete", {
            "table_name": "temp",
            "record_id": "1"
        })

        assert result["success"] is False
        assert result.get("confirmation_required") is True

    def test_sensitive_operation_with_callback(self, query_engine):
        """Test sensitive operations with confirmation callback"""
        confirmed = False

        def confirm_callback(operation: str, args: Dict[str, Any]) -> bool:
            nonlocal confirmed
            confirmed = True
            return True

        executor = FunctionExecutor(query_engine, confirmation_callback=confirm_callback)

        # Setup
        executor.execute("create_table", {"table_name": "temp", "indexes": {}})
        executor.execute("insert", {
            "table_name": "temp",
            "record_id": "1",
            "data": {"value": "test"}
        })

        # Delete with confirmation
        result = executor.execute("delete", {
            "table_name": "temp",
            "record_id": "1"
        })

        assert confirmed is True
        assert result["success"] is True

    def test_get_database_context(self, executor):
        """Test getting database context"""
        # Create some tables
        executor.execute("create_table", {"table_name": "table1", "indexes": {}})
        executor.execute("create_table", {"table_name": "table2", "indexes": {}})

        context = executor.get_database_context()

        assert "nlp_test_db" in context
        assert "nlp_test_user" in context
        assert "table1" in context
        assert "table2" in context

    def test_unknown_function(self, executor):
        """Test executing an unknown function"""
        result = executor.execute("nonexistent_function", {})

        assert result["success"] is False
        assert "Unknown function" in result["error"]


class TestNaturalDB:
    """Test NaturalDB unified interface"""

    def test_initialization(self, naturaldb):
        """Test NaturalDB initialization"""
        assert naturaldb.user.id == "nlp_test_user"
        assert naturaldb.database.name == "nlp_test_db"
        assert naturaldb.query_engine is not None
        assert naturaldb.executor is not None
        assert naturaldb.tools is not None
        assert len(naturaldb.tools) > 0

    def test_initialization_without_openai_key(self, test_user, test_database, temp_data_dir, monkeypatch):
        """Test NaturalDB works without OpenAI API key"""
        monkeypatch.setenv('NATURALDB_DATA_PATH', temp_data_dir)
        monkeypatch.delenv('OPENAI_API_KEY', raising=False)

        db = NaturalDB(test_user, test_database)

        assert db.nlp_enabled is False
        assert db.query_engine is not None
        assert db.executor is not None

    def test_direct_engine_access(self, naturaldb):
        """Test direct access to QueryEngine"""
        # Should be able to use engine directly
        table = Table(name="direct_test", indexes={})
        result = naturaldb.engine.create_table(table)

        assert result is True

        # Verify table was created
        tables = naturaldb.list_tables()
        assert "direct_test" in tables

    def test_list_tables(self, naturaldb):
        """Test listing tables"""
        # Create some tables
        naturaldb.engine.create_table(Table(name="table_a", indexes={}))
        naturaldb.engine.create_table(Table(name="table_b", indexes={}))

        tables = naturaldb.list_tables()

        assert "table_a" in tables
        assert "table_b" in tables

    def test_get_context(self, naturaldb):
        """Test getting database context"""
        context = naturaldb.get_context()

        assert "nlp_test_db" in context
        assert "nlp_test_user" in context

    def test_repr(self, naturaldb):
        """Test string representation"""
        repr_str = repr(naturaldb)

        assert "NaturalDB" in repr_str
        assert "nlp_test_user" in repr_str
        assert "nlp_test_db" in repr_str


class TestIntegration:
    """Integration tests for Layer 3 components"""

    def test_full_workflow(self, executor):
        """Test a complete workflow from tool registration to execution"""
        # Get tools
        tools = DatabaseToolRegistry.get_all_tools()
        assert len(tools) > 0

        # Simulate what OpenAI would return
        function_calls = [
            {
                "name": "create_table",
                "arguments": {"table_name": "products", "indexes": {}}
            },
            {
                "name": "insert",
                "arguments": {
                    "table_name": "products",
                    "record_id": "1",
                    "data": {"name": "Laptop", "price": 999, "category": "Electronics"}
                }
            },
            {
                "name": "insert",
                "arguments": {
                    "table_name": "products",
                    "record_id": "2",
                    "data": {"name": "Mouse", "price": 25, "category": "Electronics"}
                }
            },
            {
                "name": "filter",
                "arguments": {
                    "table_name": "products",
                    "field_name": "price",
                    "value": 100,
                    "operator": "lt"
                }
            }
        ]

        # Execute all operations
        results = executor.execute_batch(function_calls)

        # Verify all succeeded
        assert all(r["success"] for r in results)

        # Verify filter result
        filtered_products = results[3]["result"]
        assert len(filtered_products) == 1
        assert filtered_products[0]["data"]["name"] == "Mouse"

    def test_complex_query_simulation(self, executor):
        """Simulate a complex multi-step query"""
        # Simulate: "Create an orders table, add some orders, 
        # then show me the total sales by category"

        steps = [
            # Create table
            {
                "name": "create_table",
                "arguments": {"table_name": "orders", "indexes": {}}
            },
            # Add orders
            {
                "name": "insert",
                "arguments": {
                    "table_name": "orders",
                    "record_id": "1",
                    "data": {"category": "Electronics", "amount": 100}
                }
            },
            {
                "name": "insert",
                "arguments": {
                    "table_name": "orders",
                    "record_id": "2",
                    "data": {"category": "Electronics", "amount": 200}
                }
            },
            {
                "name": "insert",
                "arguments": {
                    "table_name": "orders",
                    "record_id": "3",
                    "data": {"category": "Books", "amount": 50}
                }
            },
            {
                "name": "insert",
                "arguments": {
                    "table_name": "orders",
                    "record_id": "4",
                    "data": {"category": "Books", "amount": 75}
                }
            },
            # Group by category with sum
            {
                "name": "group_by",
                "arguments": {
                    "table_name": "orders",
                    "field_name": "category",
                    "aggregations": {"amount": "sum"}
                }
            }
        ]

        results = executor.execute_batch(steps)

        assert all(r["success"] for r in results)

        # Check grouping result
        grouped = results[5]["result"]
        assert "Electronics" in grouped
        assert "Books" in grouped
        assert grouped["Electronics"]["sum_amount"] == 300
        assert grouped["Books"]["sum_amount"] == 125

    def test_error_handling(self, executor):
        """Test error handling in execution"""
        # Try to insert into non-existent table
        result = executor.execute("insert", {
            "table_name": "nonexistent",
            "record_id": "1",
            "data": {"value": "test"}
        })

        # Should succeed (auto-creates table) or handle gracefully
        assert "success" in result

    def test_tool_parameter_validation(self):
        """Test that tool parameters are properly defined"""
        tools = DatabaseToolRegistry.get_all_tools()

        for tool in tools:
            func = tool["function"]
            params = func["parameters"]

            # All parameters should have descriptions
            for param_name, param_info in params["properties"].items():
                assert "description" in param_info, f"Missing description for {param_name} in {func['name']}"
                assert "type" in param_info, f"Missing type for {param_name} in {func['name']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
