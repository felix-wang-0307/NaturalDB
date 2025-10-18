"""
Query Operations for NaturalDB
Implements filtering, projection, grouping, aggregation, and join operations.
"""

from typing import Any, Dict, List, Optional, Union, Callable
import os
from ..entities import User, Database, Table, Record
from ..storage_system.storage import TableStorage


class QueryOperations:
    """
    Provides various query operations for NaturalDB records.
    """
    
    def __init__(self, user: User, database: Database, table: Table):
        self.user = user
        self.database = database
        self.table = table
        self.table_storage = TableStorage(user, database, table)
    
    def find_all(self) -> List[Record]:
        """
        Retrieve all records from the table.
        
        Returns:
            List of all records in the table
        """
        records_dict = self.table_storage.load_all_records()
        return list(records_dict.values())
    
    def find_by_id(self, record_id: str) -> Optional[Record]:
        """
        Find a record by its ID.
        
        Args:
            record_id: The ID of the record to find
            
        Returns:
            The record if found, None otherwise
        """
        try:
            return self.table_storage.load_record(record_id)
        except (FileNotFoundError, OSError):
            return None
    
    def filter(self, condition: Callable[[Record], bool]) -> List[Record]:
        """
        Filter records based on a condition function.
        
        Args:
            condition: A function that takes a Record and returns a boolean
            
        Returns:
            List of records that satisfy the condition
        """
        all_records = self.find_all()
        return [record for record in all_records if condition(record)]
    
    def filter_by_field(self, field_name: str, value: Any, operator: str = "eq") -> List[Record]:
        """
        Filter records by a specific field value.
        
        Args:
            field_name: Name of the field to filter by
            value: Value to compare against
            operator: Comparison operator ('eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'contains')
            
        Returns:
            List of filtered records
        """
        def condition(record: Record) -> bool:
            field_value = self._get_nested_field(record.data, field_name)
            
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
                raise ValueError(f"Unsupported operator: {operator}")
        
        return self.filter(condition)
    
    def project(self, records: List[Record], fields: List[str]) -> List[Dict[str, Any]]:
        """
        Project specific fields from records.
        
        Args:
            records: List of records to project
            fields: List of field names to include in the projection
            
        Returns:
            List of dictionaries containing only the specified fields
        """
        result = []
        for record in records:
            projected = {}
            for field in fields:
                field_value = self._get_nested_field(record.data, field)
                self._set_nested_field(projected, field, field_value)
            result.append(projected)
        
        return result
    
    def group_by(self, records: List[Record], field_name: str) -> Dict[Any, List[Record]]:
        """
        Group records by a specific field.
        
        Args:
            records: List of records to group
            field_name: Name of the field to group by
            
        Returns:
            Dictionary mapping field values to lists of records
        """
        groups = {}
        for record in records:
            group_key = self._get_nested_field(record.data, field_name)
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(record)
        
        return groups
    
    def aggregate(self, records: List[Record], field_name: str, operation: str) -> Any:
        """
        Perform aggregation on a field across records.
        
        Args:
            records: List of records to aggregate
            field_name: Name of the field to aggregate
            operation: Aggregation operation ('count', 'sum', 'avg', 'min', 'max')
            
        Returns:
            Aggregated value
        """
        if not records:
            return None
        
        if operation == "count":
            return len(records)
        
        values = []
        for record in records:
            value = self._get_nested_field(record.data, field_name)
            if value is not None:
                values.append(value)
        
        if not values:
            return None
        
        if operation == "sum":
            return sum(values)
        elif operation == "avg":
            return sum(values) / len(values)
        elif operation == "min":
            return min(values)
        elif operation == "max":
            return max(values)
        else:
            raise ValueError(f"Unsupported aggregation operation: {operation}")
    
    def sort(self, records: List[Record], field_name: str, ascending: bool = True) -> List[Record]:
        """
        Sort records by a specific field.
        
        Args:
            records: List of records to sort
            field_name: Name of the field to sort by
            ascending: Whether to sort in ascending order
            
        Returns:
            Sorted list of records
        """
        def sort_key(record: Record):
            value = self._get_nested_field(record.data, field_name)
            # Handle None values by putting them at the end
            return (value is None, value)
        
        return sorted(records, key=sort_key, reverse=not ascending)
    
    def limit(self, records: List[Record], count: int, offset: int = 0) -> List[Record]:
        """
        Limit the number of records returned.
        
        Args:
            records: List of records to limit
            count: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            Limited list of records
        """
        return records[offset:offset + count]
    
    def _get_nested_field(self, data: Dict[str, Any], field_path: str) -> Any:
        """
        Get a nested field value using dot notation.
        
        Args:
            data: Dictionary to search in
            field_path: Field path (e.g., 'specs.storage' or 'name')
            
        Returns:
            Field value or None if not found
        """
        if '.' not in field_path:
            return data.get(field_path)
        
        parts = field_path.split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current
    
    def _set_nested_field(self, data: Dict[str, Any], field_path: str, value: Any) -> None:
        """
        Set a nested field value using dot notation.
        
        Args:
            data: Dictionary to set value in
            field_path: Field path (e.g., 'specs.storage' or 'name')
            value: Value to set
        """
        if '.' not in field_path:
            data[field_path] = value
            return
        
        parts = field_path.split('.')
        current = data
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value


class JoinOperations:
    """
    Provides join operations between tables.
    """
    
    @staticmethod
    def inner_join(
        left_records: List[Record],
        right_records: List[Record],
        left_field: str,
        right_field: str,
        left_alias: str = "left",
        right_alias: str = "right"
    ) -> List[Dict[str, Any]]:
        """
        Perform an inner join between two sets of records.
        
        Args:
            left_records: Records from the left table
            right_records: Records from the right table
            left_field: Field name to join on in left records
            right_field: Field name to join on in right records
            left_alias: Alias for left table fields
            right_alias: Alias for right table fields
            
        Returns:
            List of joined records
        """
        result = []
        
        # Create a lookup dictionary for right records
        right_lookup = {}
        for record in right_records:
            field_value = JoinOperations._get_nested_field_static(record.data, right_field)
            if field_value not in right_lookup:
                right_lookup[field_value] = []
            right_lookup[field_value].append(record)
        
        # Join with left records
        for left_record in left_records:
            left_value = JoinOperations._get_nested_field_static(left_record.data, left_field)
            
            if left_value in right_lookup:
                for right_record in right_lookup[left_value]:
                    joined = {
                        left_alias: left_record.data,
                        right_alias: right_record.data
                    }
                    result.append(joined)
        
        return result
    
    @staticmethod
    def left_join(
        left_records: List[Record],
        right_records: List[Record],
        left_field: str,
        right_field: str,
        left_alias: str = "left",
        right_alias: str = "right"
    ) -> List[Dict[str, Any]]:
        """
        Perform a left join between two sets of records.
        
        Args:
            left_records: Records from the left table
            right_records: Records from the right table
            left_field: Field name to join on in left records
            right_field: Field name to join on in right records
            left_alias: Alias for left table fields
            right_alias: Alias for right table fields
            
        Returns:
            List of joined records
        """
        result = []
        
        # Create a lookup dictionary for right records
        right_lookup = {}
        for record in right_records:
            field_value = JoinOperations._get_nested_field_static(record.data, right_field)
            if field_value not in right_lookup:
                right_lookup[field_value] = []
            right_lookup[field_value].append(record)
        
        # Join with left records
        for left_record in left_records:
            left_value = JoinOperations._get_nested_field_static(left_record.data, left_field)
            
            if left_value in right_lookup:
                for right_record in right_lookup[left_value]:
                    joined = {
                        left_alias: left_record.data,
                        right_alias: right_record.data
                    }
                    result.append(joined)
            else:
                # Left join includes records with no match
                joined = {
                    left_alias: left_record.data,
                    right_alias: None
                }
                result.append(joined)
        
        return result
    
    @staticmethod
    def _get_nested_field_static(data: Dict[str, Any], field_path: str) -> Any:
        """Static version of _get_nested_field for use in static methods"""
        if '.' not in field_path:
            return data.get(field_path)
        
        parts = field_path.split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current


# Remove the assignment at the end of the file
# QueryOperations._get_nested_field_static = JoinOperations._get_nested_field_static