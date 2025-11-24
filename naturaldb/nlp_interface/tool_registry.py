"""
Database Tool Registry - Maps QueryEngine methods to OpenAI tools
"""

from typing import List, Dict, Any, Optional
from .function_calling import ToolRegistry


class DatabaseToolRegistry:
    """
    Automatically registers all QueryEngine operations as OpenAI tools.
    """
    
    # Sensitive operations that require confirmation
    SENSITIVE_OPERATIONS = {'update', 'delete', 'drop_table'}
    
    @staticmethod
    def get_all_tools(query_engine_instance: Optional[Any] = None) -> List[Dict[str, Any]]:
        """
        Get all database operation tools.
        
        Args:
            query_engine_instance: Optional QueryEngine instance to bind methods to
        
        Returns:
            List of OpenAI tool definitions
        """
        from naturaldb.query_engine.query_engine import QueryEngine
        
        # Method descriptions
        method_descriptions = {
            'create_table': 'Create a new table in the database',
            'drop_table': 'Delete a table from the database (SENSITIVE OPERATION)',
            'list_tables': 'List all tables in the database',
            'insert': 'Insert a new record into a table',
            'find_by_id': 'Find a record by its ID',
            'find_all': 'Find all records in a table',
            'update': 'Update an existing record (SENSITIVE OPERATION)',
            'delete': 'Delete a record from a table (SENSITIVE OPERATION)',
            'filter': 'Filter records based on conditions',
            'project': 'Select specific fields from records',
            'rename': 'Rename fields in query results',
            'select': 'Execute a complex SQL-style query with filters, projection, sorting, and pagination',
            'group_by': 'Group records by a field and perform aggregations',
            'sort': 'Sort records by a field',
            'order_by': 'Sort records by a field (alias for sort)',
            'join': 'Join two tables on a common field',
            'import_from_json_file': 'Import data from a JSON file into a table',
            'export_to_json_file': 'Export table data to a JSON file',
        }
        
        # Parameter descriptions
        param_descriptions = {
            'create_table': {
                'table_name': 'Name of the table to create',
                'indexes': 'Optional dictionary of indexes for the table (default: empty dict)',
            },
            'drop_table': {
                'table_name': 'Name of the table to delete',
            },
            'insert': {
                'table_name': 'Name of the table to insert into',
                'record_id': 'Unique identifier for the record',
                'data': 'Dictionary containing the record data',
            },
            'find_by_id': {
                'table_name': 'Name of the table to search',
                'record_id': 'ID of the record to find',
            },
            'find_all': {
                'table_name': 'Name of the table to query',
            },
            'update': {
                'table_name': 'Name of the table containing the record',
                'record_id': 'ID of the record to update',
                'data': 'Dictionary with updated field values',
            },
            'delete': {
                'table_name': 'Name of the table containing the record',
                'record_id': 'ID of the record to delete',
            },
            'filter': {
                'table_name': 'Name of the table to filter',
                'filters': 'List of filter dictionaries. Each filter has: field (str), operator ("eq", "ne", "gt", "gte", "lt", "lte", "in", "nin", "contains"), value (any)',
            },
            'select': {
                'table_name': 'Name of the table to query',
                'filters': 'Optional list of filter conditions',
                'project': 'Optional list of fields to include in results',
                'sort': 'Optional list of sort dictionaries with field and direction ("asc" or "desc")',
                'limit': 'Optional maximum number of results to return',
                'skip': 'Optional number of results to skip (for pagination)',
            },
            'group_by': {
                'table_name': 'Name of the table to group',
                'group_field': 'Field name to group by',
                'aggregations': 'Dictionary of aggregations. Keys are result field names, values are dicts with "field" and "operation" ("count", "sum", "avg", "min", "max")',
            },
            'join': {
                'left_table': 'Name of the left table',
                'right_table': 'Name of the right table',
                'left_key': 'Field name in left table to join on',
                'right_key': 'Field name in right table to join on',
                'join_type': 'Type of join: "inner", "left", "right", or "outer" (default: "inner")',
            },
        }
        
        # Exclude private methods and internal methods
        exclude_methods = [
            'get_storage',
            '__init__',
            '__str__',
            '__repr__',
        ]
        
        # Register all QueryEngine methods as tools
        tools = ToolRegistry.register_class_methods(
            target_class=QueryEngine,
            exclude_methods=exclude_methods,
            method_descriptions=method_descriptions,
            param_descriptions=param_descriptions,
            instance=query_engine_instance
        )
        
        return tools
    
    @staticmethod
    def get_sensitive_operations() -> set:
        """Get set of operation names that require confirmation."""
        return DatabaseToolRegistry.SENSITIVE_OPERATIONS
    
    @staticmethod
    def is_sensitive_operation(operation_name: str) -> bool:
        """Check if an operation is sensitive and requires confirmation."""
        return operation_name in DatabaseToolRegistry.SENSITIVE_OPERATIONS
