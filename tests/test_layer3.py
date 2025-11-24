"""
Comprehensive test suite for NaturalDB Layer 3
Tests automatic tool registration, executor functionality, and NaturalDB interface.
Can run without OpenAI API key for basic tests.
"""

from naturaldb.entities import User, Database, Table, Record
from naturaldb.nlp_interface.tool_registry import DatabaseToolRegistry
from naturaldb.nlp_interface.executor import FunctionExecutor
from naturaldb.nlp_interface.function_calling import OpenAiTool, ToolRegistry
from naturaldb.nlp_interface.naturaldb import NaturalDB
from naturaldb.query_engine.query_engine import QueryEngine
import json
import os


def test_tool_registration():
    """Test automatic tool registration from QueryEngine."""
    print("=" * 60)
    print("Test 1: Automatic Tool Registration")
    print("=" * 60)
    
    # Get all registered tools
    tools = DatabaseToolRegistry.get_all_tools()
    
    print(f"\n✅ Total tools registered: {len(tools)}")
    
    # Show some example tools
    print("\nSample registered tools:")
    for i, tool in enumerate(tools[:3]):
        func_info = tool.get("function", {})
        print(f"\n{i+1}. {func_info.get('name')}")
        print(f"   Description: {func_info.get('description')}")
        params = func_info.get('parameters', {}).get('properties', {})
        print(f"   Parameters: {list(params.keys())}")
    
    # Verify sensitive operations
    sensitive = DatabaseToolRegistry.get_sensitive_operations()
    print(f"\n✅ Sensitive operations: {sensitive}")
    
    return tools


def test_executor():
    """Test function executor without OpenAI."""
    print("\n" + "=" * 60)
    print("Test 2: Function Executor")
    print("=" * 60)
    
    # Setup
    user = User(id="test_user", name="Test User")
    database = Database(name="test_db")
    engine = QueryEngine(user, database)
    executor = FunctionExecutor(engine)
    
    # Test 1: Create table
    print("\n📝 Test 2.1: Create Table")
    result = executor.execute("create_table", {"table_name": "products", "indexes": {}})
    print(f"Result: {result}")
    assert result['success'], "Create table failed"
    
    # Test 2: Insert record
    print("\n📝 Test 2.2: Insert Record")
    result = executor.execute("insert", {
        "table_name": "products",
        "record_id": "1",
        "data": {"name": "Laptop", "price": 999, "category": "Electronics"}
    })
    print(f"Result: {result}")
    assert result['success'], "Insert failed"
    
    # Test 3: Find all
    print("\n📝 Test 2.3: Find All Records")
    result = executor.execute("find_all", {"table_name": "products"})
    print(f"Result: {json.dumps(result, indent=2)}")
    assert result['success'], "Find all failed"
    assert len(result['result']) == 1, "Should have 1 record"
    
    # Test 4: Filter
    print("\n📝 Test 2.4: Filter Records")
    result = executor.execute("filter", {
        "table_name": "products",
        "field_name": "price",
        "value": 500,
        "operator": "gt"
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    assert result['success'], "Filter failed"
    assert len(result['result']) == 1, "Should find 1 product with price > 500"
    
    # Test 5: Batch execution
    print("\n📝 Test 2.5: Batch Execution")
    batch_calls = [
        {
            "name": "insert",
            "arguments": {
                "table_name": "products",
                "record_id": "2",
                "data": {"name": "Mouse", "price": 25, "category": "Electronics"}
            }
        },
        {
            "name": "insert",
            "arguments": {
                "table_name": "products",
                "record_id": "3",
                "data": {"name": "Keyboard", "price": 75, "category": "Electronics"}
            }
        },
        {
            "name": "find_all",
            "arguments": {"table_name": "products"}
        }
    ]
    
    results = executor.execute_batch(batch_calls)
    print(f"Batch results: {len(results)} operations executed")
    for i, r in enumerate(results):
        print(f"  Operation {i+1}: {'✅ Success' if r['success'] else '❌ Failed'}")
    
    assert all(r['success'] for r in results), "Batch execution failed"
    
    # Test 6: Get database context
    print("\n📝 Test 2.6: Database Context")
    context = executor.get_database_context()
    print(f"Context:\n{context}")
    
    print("\n✅ All executor tests passed!")


def test_tool_schema():
    """Verify the OpenAI tool schema is correct."""
    print("\n" + "=" * 60)
    print("Test 3: Tool Schema Validation")
    print("=" * 60)
    
    tools = DatabaseToolRegistry.get_all_tools()
    
    # Check a specific tool's schema
    insert_tool = DatabaseToolRegistry.get_tool_by_name(tools, "insert")
    
    if insert_tool:
        print("\n📋 'insert' tool schema:")
        print(json.dumps(insert_tool, indent=2))
        
        # Verify required fields
        func = insert_tool.get("function", {})
        assert func.get("name") == "insert", "Function name mismatch"
        assert "description" in func, "Missing description"
        assert "parameters" in func, "Missing parameters"
        
        params = func.get("parameters", {})
        assert params.get("type") == "object", "Parameters should be object type"
        assert "properties" in params, "Missing properties"
        assert "required" in params, "Missing required fields"
        
        print("\n✅ Tool schema validation passed!")
    else:
        print("❌ 'insert' tool not found")


def test_confirmation_required():
    """Test that sensitive operations require confirmation."""
    print("\n" + "=" * 60)
    print("Test 4: Sensitive Operation Confirmation")
    print("=" * 60)
    
    user = User(id="test_user", name="Test User")
    database = Database(name="test_db")
    engine = QueryEngine(user, database)
    
    # Without confirmation callback
    executor = FunctionExecutor(engine)
    
    # Create and insert test data
    executor.execute("create_table", {"table_name": "temp", "indexes": {}})
    executor.execute("insert", {
        "table_name": "temp",
        "record_id": "1",
        "data": {"value": "test"}
    })
    
    # Try to delete (should require confirmation)
    print("\n📝 Attempting delete without confirmation callback...")
    result = executor.execute("delete", {
        "table_name": "temp",
        "record_id": "1"
    })
    
    print(f"Result: {result}")
    assert result.get('confirmation_required'), "Delete should require confirmation"
    assert not result['success'], "Should not succeed without confirmation"
    
    print("\n✅ Confirmation requirement works correctly!")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("NaturalDB Layer 3 - Unit Tests")
    print("(No OpenAI API required for these tests)")
    print("=" * 60)
    
    try:
        # Run all tests
        test_tool_registration()
        test_executor()
        test_tool_schema()
        test_confirmation_required()
        
        print("\n" + "=" * 60)
        print("🎉 All tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        raise
