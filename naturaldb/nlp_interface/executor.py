"""
Function Call Executor for NaturalDB Layer 3
Executes function calls returned by OpenAI on the actual QueryEngine.
"""

from typing import Any, Dict, List, Optional, Callable
from ..entities import User, Database, Table, Record
from ..query_engine.query_engine import QueryEngine
from ..json_parser import JSONParser
import json


class FunctionExecutor:
    """
    Executes function calls on the QueryEngine.
    Maps function names to QueryEngine methods and handles parameter conversion.
    """

    def __init__(
        self,
        query_engine: QueryEngine,
        confirmation_callback: Optional[Callable[[str, Dict[str, Any]], bool]] = None
    ):
        """
        Initialize the function executor.
        
        Args:
            query_engine: The QueryEngine instance to execute operations on
            confirmation_callback: Optional callback for sensitive operations
                                  Should accept (operation_name, parameters) and return bool
        """
        self.query_engine = query_engine
        self.confirmation_callback = confirmation_callback
        self.sensitive_operations = ["update", "delete"]

    def execute(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a function call.
        
        Args:
            function_name: Name of the function to execute
            arguments: Dictionary of function arguments
            
        Returns:
            Dictionary containing:
                - 'success': Whether the operation succeeded
                - 'result': The operation result (if successful)
                - 'error': Error message (if failed)
                - 'confirmation_required': Whether user confirmation is needed
        """
        # Check if confirmation is needed for sensitive operations
        if function_name in self.sensitive_operations:
            if self.confirmation_callback:
                if not self.confirmation_callback(function_name, arguments):
                    return {
                        "success": False,
                        "error": "Operation cancelled by user",
                        "confirmation_required": True
                    }
            else:
                # No callback provided but operation is sensitive
                return {
                    "success": False,
                    "error": f"Confirmation required for {function_name} operation",
                    "confirmation_required": True,
                    "operation": function_name,
                    "arguments": arguments
                }

        # Map function name to executor method
        executor_method = getattr(self, f"_execute_{function_name}", None)
        
        if executor_method:
            try:
                result = executor_method(arguments)
                return {
                    "success": True,
                    "result": result
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        else:
            return {
                "success": False,
                "error": f"Unknown function: {function_name}"
            }

    def execute_batch(self, function_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute multiple function calls in sequence.
        
        Args:
            function_calls: List of function call dictionaries with 'name' and 'arguments'
            
        Returns:
            List of execution results
        """
        results = []
        for call in function_calls:
            result = self.execute(call["name"], call["arguments"])
            results.append(result)
            
            # Stop on error unless it's just a confirmation requirement
            if not result["success"] and not result.get("confirmation_required"):
                break
                
        return results

    # QueryEngine method executors
    
    def _execute_create_table(self, args: Dict[str, Any]) -> Any:
        """Execute create_table operation."""
        table = Table(name=args["table_name"], indexes=args.get("indexes", {}))
        return self.query_engine.create_table(table)

    def _execute_list_tables(self, args: Dict[str, Any]) -> Any:
        """Execute list_tables operation."""
        return self.query_engine.list_tables()

    def _execute_insert(self, args: Dict[str, Any]) -> Any:
        """Execute insert operation."""
        record = Record(id=args["record_id"], data=args["data"])
        return self.query_engine.insert(args["table_name"], record)

    def _execute_find_by_id(self, args: Dict[str, Any]) -> Any:
        """Execute find_by_id operation."""
        record = self.query_engine.find_by_id(args["table_name"], args["record_id"])
        if record:
            return {"id": record.id, "data": record.data}
        return None

    def _execute_find_all(self, args: Dict[str, Any]) -> Any:
        """Execute find_all operation."""
        records = self.query_engine.find_all(args["table_name"])
        return [{"id": r.id, "data": r.data} for r in records]

    def _execute_update(self, args: Dict[str, Any]) -> Any:
        """Execute update operation (sensitive)."""
        record = Record(id=args["record_id"], data=args["data"])
        return self.query_engine.update(args["table_name"], record)

    def _execute_delete(self, args: Dict[str, Any]) -> Any:
        """Execute delete operation (sensitive)."""
        return self.query_engine.delete(args["table_name"], args["record_id"])

    def _execute_filter(self, args: Dict[str, Any]) -> Any:
        """Execute filter operation."""
        records = self.query_engine.filter(
            args["table_name"],
            args["field_name"],
            args["value"],
            args.get("operator", "eq")
        )
        return [{"id": r.id, "data": r.data} for r in records]

    def _execute_project(self, args: Dict[str, Any]) -> Any:
        """Execute project operation."""
        return self.query_engine.project(
            args["table_name"],
            args["fields"],
            args.get("conditions")
        )

    def _execute_rename(self, args: Dict[str, Any]) -> Any:
        """Execute rename operation."""
        return self.query_engine.rename(
            args["table_name"],
            args["field_mapping"],
            args.get("conditions")
        )

    def _execute_select(self, args: Dict[str, Any]) -> Any:
        """Execute select operation."""
        return self.query_engine.select(
            from_table=args["from_table"],
            fields=args.get("fields", "*"),
            where=args.get("where"),
            group_by=args.get("group_by"),
            having=args.get("having"),
            order_by=args.get("order_by"),
            ascending=args.get("ascending", True),
            limit=args.get("limit")
        )

    def _execute_group_by(self, args: Dict[str, Any]) -> Any:
        """Execute group_by operation."""
        result = self.query_engine.group_by(
            args["table_name"],
            args["field_name"],
            args.get("aggregations")
        )
        # Convert to serializable format
        if isinstance(result, dict):
            serializable = {}
            for key, value in result.items():
                if isinstance(value, list):
                    # List of records
                    serializable[str(key)] = [{"id": r.id, "data": r.data} for r in value]
                else:
                    # Aggregated values
                    serializable[str(key)] = value
            return serializable
        return result

    def _execute_sort(self, args: Dict[str, Any]) -> Any:
        """Execute sort operation."""
        records = self.query_engine.sort(
            args["table_name"],
            args["field_name"],
            args.get("ascending", True),
            args.get("limit")
        )
        return [{"id": r.id, "data": r.data} for r in records]

    def _execute_order_by(self, args: Dict[str, Any]) -> Any:
        """Execute order_by operation (alias for sort)."""
        return self._execute_sort(args)

    def _execute_join(self, args: Dict[str, Any]) -> Any:
        """Execute join operation."""
        return self.query_engine.join(
            args["left_table"],
            args["right_table"],
            args["left_field"],
            args["right_field"],
            args.get("join_type", "inner"),
            args.get("left_prefix", ""),
            args.get("right_prefix", "")
        )

    def _execute_import_from_json_file(self, args: Dict[str, Any]) -> Any:
        """Execute import_from_json_file operation."""
        return self.query_engine.import_from_json_file(
            args["table_name"],
            args["file_path"]
        )

    def _execute_export_to_json_file(self, args: Dict[str, Any]) -> Any:
        """Execute export_to_json_file operation."""
        return self.query_engine.export_to_json_file(
            args["table_name"],
            args["file_path"],
            args.get("pretty", True)
        )

    def get_database_context(self) -> str:
        """
        Get current database context for the LLM.
        
        Returns:
            String describing the current database state
        """
        try:
            tables = self.query_engine.list_tables()
            context = f"Database: {self.query_engine.database.name}\n"
            context += f"User: {self.query_engine.user.id}\n"
            context += f"Available tables: {', '.join(tables) if tables else 'None'}\n"
            return context
        except Exception as e:
            return f"Could not retrieve database context: {str(e)}"
