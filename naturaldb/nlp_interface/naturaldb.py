"""
NaturalDB Main Interface (Layer 3)
Unified natural language interface for database operations.
"""

from typing import Optional, Dict, Any, Callable, List
from ..entities import User, Database
from ..query_engine.query_engine import QueryEngine
from .tool_registry import DatabaseToolRegistry
from .nl_query_processor import NLQueryProcessor
from .executor import FunctionExecutor
import json


class NaturalDB:
    """
    Main interface for NaturalDB with natural language support.
    Combines QueryEngine with natural language processing capabilities.
    """

    def __init__(
        self,
        user: User,
        database: Database,
        openai_api_key: Optional[str] = None,
        openai_model: str = "gpt-4-turbo-preview",
        confirmation_callback: Optional[Callable[[str, Dict[str, Any]], bool]] = None
    ):
        """
        Initialize NaturalDB with natural language capabilities.
        
        Args:
            user: User object for database access
            database: Database object to work with
            openai_api_key: OpenAI API key (optional, can use OPENAI_API_KEY env var)
            openai_model: OpenAI model to use for natural language processing
            confirmation_callback: Optional callback for sensitive operations
                                  Should accept (operation_name, parameters) and return bool
        """
        # Initialize core components
        self.user = user
        self.database = database
        self.query_engine = QueryEngine(user, database)
        
        # Initialize NLP components
        try:
            self.nl_processor = NLQueryProcessor(
                api_key=openai_api_key,
                model=openai_model
            )
            self.nlp_enabled = True
        except (ValueError, ImportError) as e:
            print(f"Warning: NLP features disabled. {str(e)}")
            self.nl_processor = None
            self.nlp_enabled = False
        
        # Initialize function executor
        self.executor = FunctionExecutor(
            query_engine=self.query_engine,
            confirmation_callback=confirmation_callback
        )
        
        # Get available tools
        self.tools = DatabaseToolRegistry.get_all_tools()

    def query(self, natural_language_query: str) -> Dict[str, Any]:
        """
        Execute a natural language query.
        
        Args:
            natural_language_query: The query in natural language
                                   Examples:
                                   - "Show me all products"
                                   - "Find orders with total > 100"
                                   - "Create a table called customers"
            
        Returns:
            Dictionary containing:
                - 'success': Whether the operation succeeded
                - 'result': The query result (if successful)
                - 'explanation': Explanation of what was done
                - 'error': Error message (if failed)
                - 'confirmation_required': If user confirmation is needed
        """
        if not self.nlp_enabled:
            return {
                "success": False,
                "error": "Natural language processing is not enabled. Please provide OpenAI API key."
            }

        try:
            # Get database context
            context = self.executor.get_database_context()
            
            # Process the natural language query
            nl_result = self.nl_processor.process_query(  # type: ignore
                user_query=natural_language_query,
                tools=self.tools,
                context=context
            )
            
            # Check for errors
            if "error" in nl_result:
                return {
                    "success": False,
                    "error": nl_result["error"]
                }
            
            # Check if we got function calls
            if nl_result.get("function_calls"):
                # Execute the function calls
                execution_results = self.executor.execute_batch(nl_result["function_calls"])
                
                # Check if any required confirmation
                confirmation_needed = any(r.get("confirmation_required") for r in execution_results)
                
                if confirmation_needed:
                    return {
                        "success": False,
                        "confirmation_required": True,
                        "pending_operations": [
                            {
                                "operation": r.get("operation"),
                                "arguments": r.get("arguments")
                            }
                            for r in execution_results
                            if r.get("confirmation_required")
                        ],
                        "explanation": "Sensitive operations require confirmation"
                    }
                
                # Check for execution errors
                failed = [r for r in execution_results if not r["success"]]
                if failed:
                    return {
                        "success": False,
                        "error": failed[0]["error"],
                        "execution_results": execution_results
                    }
                
                # Success!
                return {
                    "success": True,
                    "result": [r["result"] for r in execution_results],
                    "explanation": nl_result.get("explanation"),
                    "function_calls": nl_result["function_calls"],
                    "execution_results": execution_results
                }
            else:
                # Just a text response, no database operations needed
                return {
                    "success": True,
                    "response": nl_result.get("response"),
                    "explanation": "No database operations required"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }

    def query_interactive(self, natural_language_query: str, max_turns: int = 5) -> Dict[str, Any]:
        """
        Execute a natural language query with interactive multi-turn conversation.
        The LLM can execute multiple operations and refine based on results.
        
        Args:
            natural_language_query: The query in natural language
            max_turns: Maximum number of conversation turns
            
        Returns:
            Dictionary with final response and execution history
        """
        if not self.nlp_enabled:
            return {
                "success": False,
                "error": "Natural language processing is not enabled."
            }

        try:
            context = self.executor.get_database_context()
            
            # Use the interactive processor with automatic execution
            def executor_callback(function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
                """Callback for executing functions during conversation."""
                result = self.executor.execute(function_name, arguments)
                # Convert result to JSON-serializable format
                if result.get("success"):
                    return {"success": True, "data": result.get("result")}
                else:
                    return {"success": False, "error": result.get("error")}
            
            result = self.nl_processor.process_with_execution(  # type: ignore
                user_query=natural_language_query,
                tools=self.tools,
                executor_callback=executor_callback,
                context=context,
                max_iterations=max_turns
            )
            
            if "error" in result:
                return {
                    "success": False,
                    "error": result["error"],
                    "execution_history": result.get("execution_history", [])
                }
            
            return {
                "success": True,
                "response": result.get("response"),
                "execution_history": result.get("execution_history", []),
                "iterations": result.get("iterations", 0)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }

    def confirm_and_execute(self, pending_operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute pending operations after user confirmation.
        
        Args:
            pending_operations: List of operations from a query result with confirmation_required
            
        Returns:
            Execution results
        """
        results = []
        for op in pending_operations:
            result = self.executor.execute(op["operation"], op["arguments"])
            results.append(result)
        
        failed = [r for r in results if not r["success"]]
        if failed:
            return {
                "success": False,
                "error": failed[0]["error"],
                "results": results
            }
        
        return {
            "success": True,
            "results": results
        }

    # Direct access to QueryEngine methods (for non-NLP usage)
    
    @property
    def engine(self) -> QueryEngine:
        """Get direct access to the QueryEngine."""
        return self.query_engine

    def list_tables(self) -> List[str]:
        """List all tables in the database."""
        return self.query_engine.list_tables()

    def get_context(self) -> str:
        """Get current database context as a string."""
        return self.executor.get_database_context()

    def __repr__(self) -> str:
        return f"NaturalDB(user='{self.user.id}', database='{self.database.name}', nlp_enabled={self.nlp_enabled})"
