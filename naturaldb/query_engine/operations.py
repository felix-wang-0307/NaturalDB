"""
Query Operations for NaturalDB
Implements filtering, projection, grouping, aggregation, and join operations.
"""

from typing import Any, Dict, List, Optional, Union, Callable
from ..entities import User, Database, Table, Record
from ..storage_system.storage import TableStorage


class QueryOperations:
    """
    Provides various query operations for NaturalDB records.
    Pure operations on List[Record] - no storage dependencies.
    """
    
    @staticmethod
    def filter(records: List[Record], condition: Callable[[Record], bool]) -> List[Record]:
        """
        Filter records based on a condition function.
        
        Args:
            records: List of records to filter
            condition: A function that takes a Record and returns a boolean
            
        Returns:
            List of records that satisfy the condition
        """
        return [record for record in records if condition(record)]
    
    @staticmethod
    def filter_by_field(records: List[Record], field_name: str, value: Any, operator: str = "eq") -> List[Record]:
        """
        Filter records by a specific field value.
        
        Args:
            records: List of records to filter
            field_name: Name of the field to filter by
            value: Value to compare against
            operator: Comparison operator ('eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'contains')
            
        Returns:
            List of filtered records
        """
        def condition(record: Record) -> bool:
            field_value = QueryOperations._get_nested_field(record.data, field_name)
            
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
        
        return QueryOperations.filter(records, condition)
    
    @staticmethod
    def project(records: List[Record], fields: List[str]) -> List[Dict[str, Any]]:
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
                field_value = QueryOperations._get_nested_field(record.data, field)
                QueryOperations._set_nested_field(projected, field, field_value)
            result.append(projected)
        
        return result
    
    @staticmethod
    def group_by(records: List[Record], field_name: str) -> Dict[Any, List[Record]]:
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
            group_key = QueryOperations._get_nested_field(record.data, field_name)
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(record)
        
        return groups
    
    @staticmethod
    def aggregate(records: List[Record], field_name: str, operation: str) -> Any:
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
            value = QueryOperations._get_nested_field(record.data, field_name)
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
    
    @staticmethod
    def sort(records: List[Record], field_name: str, ascending: bool = True) -> List[Record]:
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
            value = QueryOperations._get_nested_field(record.data, field_name)
            # Handle None values by putting them at the end
            return (value is None, value)
        
        return sorted(records, key=sort_key, reverse=not ascending)
    
    @staticmethod
    def limit(records: List[Record], count: int, offset: int = 0) -> List[Record]:
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
    
    @staticmethod
    def _get_nested_field(data: Dict[str, Any], field_path: str) -> Any:
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
    
    @staticmethod
    def _set_nested_field(data: Dict[str, Any], field_path: str, value: Any) -> None:
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
        left_prefix: str = "",
        right_prefix: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Perform an inner join between two sets of records.
        
        Args:
            left_records: Records from the left table
            right_records: Records from the right table
            left_field: Field name to join on in left records
            right_field: Field name to join on in right records
            left_prefix: Optional prefix for left table fields (e.g., "user_")
            right_prefix: Optional prefix for right table fields (e.g., "order_")
            
        Returns:
            List of flattened joined records with all fields merged
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
                    # Merge both records into a single flat dictionary
                    joined = {}
                    # Add left record fields with optional prefix
                    for key, value in left_record.data.items():
                        joined[f"{left_prefix}{key}"] = value
                    # Add right record fields with optional prefix
                    for key, value in right_record.data.items():
                        joined[f"{right_prefix}{key}"] = value
                    result.append(joined)
        
        return result
    
    @staticmethod
    def left_join(
        left_records: List[Record],
        right_records: List[Record],
        left_field: str,
        right_field: str,
        left_prefix: str = "",
        right_prefix: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Perform a left join between two sets of records.
        
        Args:
            left_records: Records from the left table
            right_records: Records from the right table
            left_field: Field name to join on in left records
            right_field: Field name to join on in right records
            left_prefix: Optional prefix for left table fields (e.g., "user_")
            right_prefix: Optional prefix for right table fields (e.g., "order_")
            
        Returns:
            List of flattened joined records with all fields merged
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
                    # Merge both records into a single flat dictionary
                    joined = {}
                    # Add left record fields with optional prefix
                    for key, value in left_record.data.items():
                        joined[f"{left_prefix}{key}"] = value
                    # Add right record fields with optional prefix
                    for key, value in right_record.data.items():
                        joined[f"{right_prefix}{key}"] = value
                    result.append(joined)
            else:
                # Left join includes records with no match (only left fields)
                joined = {}
                for key, value in left_record.data.items():
                    joined[f"{left_prefix}{key}"] = value
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


class TableQuery:
    """
    Chainable query builder for table operations - MongoDB style.
    
    Example:
        query = TableQuery(records)
        result = query.filter_by('age', 30, 'gt').sort('name').limit(10).execute()
    """
    
    def __init__(self, records: List[Record]):
        """
        Initialize with a list of records.
        
        Args:
            records: Initial list of records to query
        """
        self._records = records
    
    def filter(self, condition: Callable[[Record], bool]) -> 'TableQuery':
        """
        Filter records based on a condition function.
        Returns self for chaining.
        """
        self._records = QueryOperations.filter(self._records, condition)
        return self
    
    def filter_by(self, field_name: str, value: Any, operator: str = "eq") -> 'TableQuery':
        """
        Filter records by a specific field value.
        Returns self for chaining.
        """
        self._records = QueryOperations.filter_by_field(self._records, field_name, value, operator)
        return self
    
    def where(self, field_name: str, value: Any, operator: str = "eq") -> 'TableQuery':
        """
        Alias for filter_by - more SQL-like syntax.
        Returns self for chaining.
        """
        return self.filter_by(field_name, value, operator)
    
    def project(self, fields: List[str]) -> List[Dict[str, Any]]:
        """
        Project specific fields from records.
        This is a terminal operation (returns data, not chainable).
        """
        return QueryOperations.project(self._records, fields)
    
    def select(self, fields: List[str]) -> List[Dict[str, Any]]:
        """
        Alias for project - more SQL-like syntax.
        This is a terminal operation.
        """
        return self.project(fields)
    
    def sort(self, field_name: str, ascending: bool = True) -> 'TableQuery':
        """
        Sort records by a field.
        Returns self for chaining.
        """
        self._records = QueryOperations.sort(self._records, field_name, ascending)
        return self
    
    def order_by(self, field_name: str, ascending: bool = True) -> 'TableQuery':
        """
        Alias for sort - more SQL-like syntax.
        Returns self for chaining.
        """
        return self.sort(field_name, ascending)
    
    def limit(self, count: int, offset: int = 0) -> 'TableQuery':
        """
        Limit the number of records.
        Returns self for chaining.
        """
        self._records = QueryOperations.limit(self._records, count, offset)
        return self
    
    def skip(self, offset: int) -> 'TableQuery':
        """
        Skip a number of records - MongoDB style.
        Returns self for chaining.
        """
        self._records = self._records[offset:]
        return self
    
    def group_by(self, field_name: str) -> Dict[Any, List[Record]]:
        """
        Group records by a field.
        This is a terminal operation.
        """
        return QueryOperations.group_by(self._records, field_name)
    
    def count(self) -> int:
        """
        Count the number of records.
        This is a terminal operation.
        """
        return len(self._records)
    
    def first(self) -> Optional[Record]:
        """
        Get the first record.
        This is a terminal operation.
        """
        return self._records[0] if self._records else None
    
    def last(self) -> Optional[Record]:
        """
        Get the last record.
        This is a terminal operation.
        """
        return self._records[-1] if self._records else None
    
    def all(self) -> List[Record]:
        """
        Get all records.
        This is a terminal operation.
        """
        return self._records
    
    def execute(self) -> List[Record]:
        """
        Execute the query and return results.
        Alias for all() - more explicit.
        """
        return self._records
    
    def to_dict(self) -> List[Dict[str, Any]]:
        """
        Convert all records to list of dictionaries.
        This is a terminal operation.
        """
        return [record.data for record in self._records]