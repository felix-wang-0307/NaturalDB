"""
Tool Registry for NaturalDB Layer 3
Automatically converts QueryEngine methods into OpenAI function calling tools.
"""

from typing import List, Dict, Any, Optional
from .function_calling import ToolRegistry as AutoToolRegistry
from ..query_engine.query_engine import QueryEngine


class DatabaseToolRegistry:
    """
    Registry that automatically converts QueryEngine operations into OpenAI function calling tools.
    Uses the automated registration system from function_calling.py.
    """

    @staticmethod
    def get_all_tools() -> List[Dict[str, Any]]:
        """
        Get all available database operation tools for OpenAI function calling.
        Automatically generates tools from QueryEngine methods.
        
        Returns:
            List of tool definitions in OpenAI format
        """
        
        # Define custom descriptions for methods to provide better context for LLM
        method_descriptions = {
            "create_table": "Create a new table in the database. Use this when the user wants to create a new collection or table.",
            "list_tables": "List all tables in the database. Use this when the user wants to see what tables exist.",
            "insert": "Insert a new record into a table. Use this when the user wants to add, create, or insert data.",
            "find_by_id": "Find a specific record by its ID. Use this when the user wants to get, retrieve, or find a record by ID.",
            "find_all": "Find all records in a table. Use this when the user wants to get all data, list all records, or see everything in a table.",
            "update": "Update an existing record in a table. Use this when the user wants to update, modify, or change existing data. This is a SENSITIVE operation that requires confirmation.",
            "delete": "Delete a record from a table. Use this when the user wants to delete or remove a record. This is a SENSITIVE operation that requires confirmation.",
            "filter": "Filter records based on field conditions. Use this for WHERE clauses or when the user wants to find records matching certain criteria.",
            "project": "Select specific fields from records, optionally with filtering. Use this for SELECT clauses when the user only wants certain fields.",
            "rename": "Rename fields in records (like SQL AS clause). Use this when the user wants to rename or alias field names in the result.",
            "select": "Execute a complex SQL-like SELECT query with filtering, grouping, sorting, and limiting. Use this for comprehensive queries that combine multiple operations.",
            "group_by": "Group records by a field and optionally apply aggregations. Use this for GROUP BY queries with COUNT, SUM, AVG, MIN, MAX.",
            "sort": "Sort records by a field. Use this for ORDER BY queries when the user wants sorted results.",
            "order_by": "Alias for sort. Sort records by a field in ascending or descending order.",
            "join": "Join two tables together. Use this for JOIN queries when the user wants to combine data from multiple tables.",
            "import_from_json_file": "Import data from a JSON file into a table. Use this when the user wants to load or import data from a file.",
            "export_to_json_file": "Export table data to a JSON file. Use this when the user wants to export or save data to a file.",
        }
        
        # Define custom parameter descriptions for better clarity
        param_descriptions = {
            "create_table": {
                "table": "Table object containing name and indexes configuration"
            },
            "insert": {
                "table_name": "The name of the table to insert the record into",
                "record": "Record object containing an id and data dictionary"
            },
            "find_by_id": {
                "table_name": "The name of the table to search in",
                "record_id": "The unique identifier of the record to find"
            },
            "find_all": {
                "table_name": "The name of the table to retrieve all records from"
            },
            "update": {
                "table_name": "The name of the table containing the record to update",
                "record": "Record object with updated data and the same id as the existing record"
            },
            "delete": {
                "table_name": "The name of the table containing the record to delete",
                "record_id": "The unique identifier of the record to delete"
            },
            "filter": {
                "table_name": "The name of the table to filter records from",
                "field_name": "The field name to filter by (supports dot notation for nested fields like 'specs.price')",
                "value": "The value to compare against",
                "operator": "Comparison operator: 'eq' (equal), 'ne' (not equal), 'gt' (greater than), 'gte' (>=), 'lt' (less than), 'lte' (<=), 'contains' (substring match). Default is 'eq'."
            },
            "project": {
                "table_name": "The name of the table to query",
                "fields": "List of field names to include in results (supports dot notation for nested fields)",
                "conditions": "Optional filtering conditions as a dictionary, e.g., {'age': 30} or {'age': {'operator': 'gt', 'value': 30}}"
            },
            "rename": {
                "table_name": "The name of the table to query",
                "field_mapping": "Dictionary mapping original field names to new names, e.g., {'user_id': 'id', 'user_name': 'name'}",
                "conditions": "Optional filtering conditions before renaming"
            },
            "select": {
                "from_table": "The table to query (FROM clause)",
                "fields": "Fields to select, comma-separated or '*' for all fields (SELECT clause)",
                "where": "Filtering conditions (WHERE clause) as dictionary, e.g., {'age': {'operator': 'gt', 'value': 30}}",
                "group_by": "Field name to group by (GROUP BY clause)",
                "having": "Filtering conditions applied after grouping (HAVING clause)",
                "order_by": "Field name to order results by (ORDER BY clause)",
                "ascending": "Sort order: True for ascending (ASC), False for descending (DESC). Default is True.",
                "limit": "Maximum number of results to return (LIMIT clause)"
            },
            "group_by": {
                "table_name": "The name of the table to group records from",
                "field_name": "The field to group records by",
                "aggregations": "Optional aggregations to apply, as a dictionary mapping field names to operations: {'field_name': 'sum'|'avg'|'min'|'max'|'count'}"
            },
            "sort": {
                "table_name": "The name of the table to sort records from",
                "field_name": "The field to sort records by",
                "ascending": "Sort order: True for ascending (ASC), False for descending (DESC). Default is True.",
                "limit": "Optional maximum number of results to return"
            },
            "join": {
                "left_table": "The name of the left (first) table in the join",
                "right_table": "The name of the right (second) table in the join",
                "left_field": "The field in the left table to join on",
                "right_field": "The field in the right table to join on",
                "join_type": "Type of join: 'inner' (only matching records) or 'left' (all left records plus matching right records). Default is 'inner'.",
                "left_prefix": "Optional prefix for left table fields in results (e.g., 'user_')",
                "right_prefix": "Optional prefix for right table fields in results (e.g., 'order_')"
            },
            "import_from_json_file": {
                "table_name": "The name of the table to import data into",
                "file_path": "The absolute or relative path to the JSON file to import"
            },
            "export_to_json_file": {
                "table_name": "The name of the table to export data from",
                "file_path": "The absolute or relative path where the JSON file will be saved",
                "pretty": "Whether to format JSON with indentation for readability. Default is True."
            }
        }
        
        # Methods to exclude (internal or not useful for natural language interface)
        exclude_methods = [
            "get_table_operations",  # Internal helper
            "_evaluate_condition",    # Internal helper
        ]
        
        # Automatically register all QueryEngine methods
        tools = AutoToolRegistry.register_class_methods(
            target_class=QueryEngine,
            exclude_methods=exclude_methods,
            method_descriptions=method_descriptions,
            param_descriptions=param_descriptions
        )
        
        return tools

    @staticmethod
    def get_sensitive_operations() -> List[str]:
        """
        Get list of operations that require confirmation/authorization.
        
        Returns:
            List of sensitive operation names
        """
        return ["update", "delete"]
    
    @staticmethod
    def get_tool_by_name(tools: List[Dict[str, Any]], name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific tool by its function name.
        
        Args:
            tools: List of tool definitions
            name: The function name to search for
            
        Returns:
            The tool definition or None if not found
        """
        for tool in tools:
            if tool.get("function", {}).get("name") == name:
                return tool
        return None

