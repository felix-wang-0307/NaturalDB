"""
Main Query Engine for NaturalDB Layer 2
Provides high-level interface for database operations and query execution.
"""

from typing import Any, Dict, List, Optional, Union
import os
from ..entities import User, Database, Table, Record
from ..storage_system.storage import Storage, DatabaseStorage, TableStorage
from .json_parser import JSONParser
from .operations import QueryOperations, JoinOperations


class QueryEngine:
    """
    Main query engine that provides CRUD operations and advanced querying capabilities.
    """
    
    def __init__(self, user: User, database: Database):
        self.user = user
        self.database = database
        self.storage = Storage()
        self.database_storage = DatabaseStorage(user, database)
        
        # Ensure database exists
        if not os.path.exists(self.database_storage.base_path):
            self.storage.create_database(user, database)
    
    def create_table(self, table: Table) -> bool:
        """
        Create a new table in the database.
        
        Args:
            table: Table object to create
            
        Returns:
            True if table was created successfully
        """
        try:
            self.database_storage.create_table(table)
            return True
        except Exception as e:
            print(f"Error creating table: {e}")
            return False
    
    def get_table_operations(self, table_name: str) -> Optional[QueryOperations]:
        """
        Get query operations for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            QueryOperations instance or None if table doesn't exist
        """
        table = Table(name=table_name, indexes={})
        table_path = self.database_storage.get_table_path(table)
        
        if not os.path.exists(table_path):
            return None
        
        return QueryOperations(self.user, self.database, table)
    
    def insert(self, table_name: str, record: Record) -> bool:
        """
        Insert a record into a table.
        
        Args:
            table_name: Name of the table
            record: Record to insert
            
        Returns:
            True if record was inserted successfully
        """
        try:
            operations = self.get_table_operations(table_name)
            if not operations:
                # Create table if it doesn't exist
                table = Table(name=table_name, indexes={})
                if not self.create_table(table):
                    return False
                operations = self.get_table_operations(table_name)
            
            operations.table_storage.save_record(record)
            return True
        except Exception as e:
            print(f"Error inserting record: {e}")
            return False
    
    def find_by_id(self, table_name: str, record_id: str) -> Optional[Record]:
        """
        Find a record by ID in a table.
        
        Args:
            table_name: Name of the table
            record_id: ID of the record
            
        Returns:
            Record if found, None otherwise
        """
        operations = self.get_table_operations(table_name)
        if not operations:
            return None
        
        return operations.find_by_id(record_id)
    
    def find_all(self, table_name: str) -> List[Record]:
        """
        Find all records in a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of all records in the table
        """
        operations = self.get_table_operations(table_name)
        if not operations:
            return []
        
        return operations.find_all()
    
    def update(self, table_name: str, record: Record) -> bool:
        """
        Update a record in a table.
        
        Args:
            table_name: Name of the table
            record: Updated record
            
        Returns:
            True if record was updated successfully
        """
        try:
            operations = self.get_table_operations(table_name)
            if not operations:
                return False
            
            # Check if record exists
            existing = operations.find_by_id(record.id)
            if not existing:
                return False
            
            operations.table_storage.save_record(record)
            return True
        except Exception as e:
            print(f"Error updating record: {e}")
            return False
    
    def delete(self, table_name: str, record_id: str) -> bool:
        """
        Delete a record from a table.
        
        Args:
            table_name: Name of the table
            record_id: ID of the record to delete
            
        Returns:
            True if record was deleted successfully
        """
        try:
            operations = self.get_table_operations(table_name)
            if not operations:
                return False
            
            # Check if record exists
            existing = operations.find_by_id(record_id)
            if not existing:
                return False
            
            operations.table_storage.delete_record(record_id)
            return True
        except Exception as e:
            print(f"Error deleting record: {e}")
            return False
    
    def filter(self, table_name: str, field_name: str, value: Any, operator: str = "eq") -> List[Record]:
        """
        Filter records in a table by field value.
        
        Args:
            table_name: Name of the table
            field_name: Name of the field to filter by
            value: Value to compare against
            operator: Comparison operator
            
        Returns:
            List of filtered records
        """
        operations = self.get_table_operations(table_name)
        if not operations:
            return []
        
        return operations.filter_by_field(field_name, value, operator)
    
    def project(self, table_name: str, fields: List[str], conditions: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Project specific fields from records, optionally with filtering.
        
        Args:
            table_name: Name of the table
            fields: List of field names to include
            conditions: Optional filtering conditions
            
        Returns:
            List of projected records
        """
        operations = self.get_table_operations(table_name)
        if not operations:
            return []
        
        records = operations.find_all()
        
        # Apply filtering if conditions are provided
        if conditions:
            for field_name, condition in conditions.items():
                if isinstance(condition, dict):
                    operator = condition.get('operator', 'eq')
                    value = condition.get('value')
                else:
                    operator = 'eq'
                    value = condition
                
                records = [r for r in records if self._evaluate_condition(r, field_name, value, operator)]
        
        return operations.project(records, fields)
    
    def group_by(self, table_name: str, field_name: str, aggregations: Optional[Dict[str, str]] = None) -> Dict[Any, Any]:
        """
        Group records by a field and optionally apply aggregations.
        
        Args:
            table_name: Name of the table
            field_name: Field to group by
            aggregations: Optional aggregations to apply {'field_name': 'operation'}
            
        Returns:
            Dictionary of grouped results
        """
        operations = self.get_table_operations(table_name)
        if not operations:
            return {}
        
        records = operations.find_all()
        groups = operations.group_by(records, field_name)
        
        if not aggregations:
            return {k: len(v) for k, v in groups.items()}
        
        result = {}
        for group_key, group_records in groups.items():
            group_result = {'count': len(group_records)}
            
            for agg_field, agg_operation in aggregations.items():
                agg_value = operations.aggregate(group_records, agg_field, agg_operation)
                group_result[f'{agg_operation}_{agg_field}'] = agg_value
            
            result[group_key] = group_result
        
        return result
    
    def sort(self, table_name: str, field_name: str, ascending: bool = True, limit: Optional[int] = None) -> List[Record]:
        """
        Sort records in a table by a field.
        
        Args:
            table_name: Name of the table
            field_name: Field to sort by
            ascending: Sort order
            limit: Optional limit on number of records
            
        Returns:
            Sorted list of records
        """
        operations = self.get_table_operations(table_name)
        if not operations:
            return []
        
        records = operations.find_all()
        sorted_records = operations.sort(records, field_name, ascending)
        
        if limit:
            sorted_records = operations.limit(sorted_records, limit)
        
        return sorted_records
    
    def join(self, 
             left_table: str, 
             right_table: str, 
             left_field: str, 
             right_field: str, 
             join_type: str = "inner",
             left_alias: str = "left",
             right_alias: str = "right") -> List[Dict[str, Any]]:
        """
        Join two tables.
        
        Args:
            left_table: Name of the left table
            right_table: Name of the right table
            left_field: Field to join on in left table
            right_field: Field to join on in right table
            join_type: Type of join ('inner' or 'left')
            left_alias: Alias for left table
            right_alias: Alias for right table
            
        Returns:
            List of joined records
        """
        left_operations = self.get_table_operations(left_table)
        right_operations = self.get_table_operations(right_table)
        
        if not left_operations or not right_operations:
            return []
        
        left_records = left_operations.find_all()
        right_records = right_operations.find_all()
        
        if join_type == "inner":
            return JoinOperations.inner_join(left_records, right_records, left_field, right_field, left_alias, right_alias)
        elif join_type == "left":
            return JoinOperations.left_join(left_records, right_records, left_field, right_field, left_alias, right_alias)
        else:
            raise ValueError(f"Unsupported join type: {join_type}")
    
    def import_from_json_file(self, table_name: str, file_path: str) -> bool:
        """
        Import data from a JSON file into a table.
        
        Args:
            table_name: Name of the table
            file_path: Path to the JSON file
            
        Returns:
            True if import was successful
        """
        try:
            data = JSONParser.parse_file(file_path)
            
            if isinstance(data, list):
                # Array of records
                for i, record_data in enumerate(data):
                    if 'id' not in record_data:
                        record_data['id'] = str(i + 1)
                    
                    record = Record(id=str(record_data['id']), data=record_data)
                    if not self.insert(table_name, record):
                        return False
            elif isinstance(data, dict):
                # Single record
                if 'id' not in data:
                    data['id'] = '1'
                
                record = Record(id=str(data['id']), data=data)
                return self.insert(table_name, record)
            
            return True
        except Exception as e:
            print(f"Error importing from JSON file: {e}")
            return False
    
    def export_to_json_file(self, table_name: str, file_path: str, pretty: bool = True) -> bool:
        """
        Export table data to a JSON file.
        
        Args:
            table_name: Name of the table
            file_path: Path to save the JSON file
            pretty: Whether to format JSON with indentation
            
        Returns:
            True if export was successful
        """
        try:
            records = self.find_all(table_name)
            data = [record.data for record in records]
            
            json_str = JSONParser.to_json_string(data, indent=2 if pretty else None)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
            
            return True
        except Exception as e:
            print(f"Error exporting to JSON file: {e}")
            return False
    
    def list_tables(self) -> List[str]:
        """
        List all tables in the database.
        
        Returns:
            List of table names
        """
        try:
            if not os.path.exists(self.database_storage.base_path):
                return []
            
            tables = []
            for item in os.listdir(self.database_storage.base_path):
                item_path = os.path.join(self.database_storage.base_path, item)
                if os.path.isdir(item_path) and item != '__pycache__':
                    tables.append(item)
            
            return tables
        except Exception as e:
            print(f"Error listing tables: {e}")
            return []
    
    def _evaluate_condition(self, record: Record, field_name: str, value: Any, operator: str) -> bool:
        """
        Evaluate a condition against a record.
        
        Args:
            record: Record to evaluate
            field_name: Field name to check
            value: Value to compare
            operator: Comparison operator
            
        Returns:
            True if condition is satisfied
        """
        operations = QueryOperations(self.user, self.database, Table(name="temp", indexes={}))
        field_value = operations._get_nested_field(record.data, field_name)
        
        if operator == "eq":
            return field_value == value
        elif operator == "ne":
            return field_value != value
        elif operator == "gt":
            return field_value > value
        elif operator == "gte":
            return field_value >= value
        elif operator == "lt":
            return field_value < value
        elif operator == "lte":
            return field_value <= value
        elif operator == "contains":
            return value in str(field_value)
        else:
            return False