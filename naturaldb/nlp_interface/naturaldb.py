"""
NaturalDB - Unified Natural Language Interface for Database Operations
"""

from typing import Optional, Dict, Any, Callable
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class NaturalDB:
    """
    Main interface for interacting with NaturalDB using natural language.
    Combines QueryEngine, NLQueryProcessor, and FunctionExecutor.
    """
    
    def __init__(
        self,
        user: Any,
        database: Any,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        confirmation_callback: Optional[Callable[[str, Dict[str, Any]], bool]] = None,
        data_path: Optional[str] = None
    ):
        """
        Initialize NaturalDB.
        
        Args:
            user: User entity
            database: Database entity
            api_key: OpenAI API key (optional, reads from env if not provided)
            model: OpenAI model to use
            confirmation_callback: Optional callback for confirming sensitive operations
            data_path: Optional custom data path for storage
        """
        from naturaldb.query_engine.query_engine import QueryEngine
        
        # Initialize query engine with user and database
        self.engine = QueryEngine(user, database)
        self.user = user
        self.database = database
        
        # Initialize NLP components if API key is available
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.nlp_enabled = False
        
        if api_key:
            try:
                from .nl_query_processor import NLQueryProcessor
                from .executor import FunctionExecutor
                from .tool_registry import DatabaseToolRegistry
                
                self.processor = NLQueryProcessor(api_key=api_key, model=model)
                self.executor = FunctionExecutor(
                    query_engine=self.engine,
                    confirmation_callback=confirmation_callback
                )
                self.tools = DatabaseToolRegistry.get_all_tools(self.engine)
                self.nlp_enabled = True
                
            except Exception as e:
                print(f"⚠️  NLP features disabled: {str(e)}")
                print("You can still use the QueryEngine directly via .engine")
        else:
            print("⚠️  No OpenAI API key found. NLP features disabled.")
            print("Set OPENAI_API_KEY environment variable to enable natural language queries.")
            print("You can still use the QueryEngine directly via .engine")
    
    def query(self, user_query: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a natural language query.
        
        Args:
            user_query: Natural language query
            context: Optional context information
        
        Returns:
            Dictionary with:
                - success: bool
                - result: Any (query result)
                - message: str (AI response)
                - error: Optional[str]
        """
        if not self.nlp_enabled:
            return {
                "success": False,
                "error": "NLP features are not enabled. Check your OpenAI API key.",
                "message": "Please set OPENAI_API_KEY environment variable"
            }
        
        # Add table list to context
        if context is None:
            tables = self.engine.list_tables()
            context = f"Available tables: {', '.join(tables)}"
        
        # Process the query
        result = self.processor.process_query(
            user_query=user_query,
            tools=self.tools,
            context=context
        )
        
        if not result['success']:
            return result
        
        # Execute function calls if any
        if result['function_calls']:
            execution_results = self.executor.execute_batch(result['function_calls'])
            
            # Return the first result (most common case)
            if execution_results:
                return execution_results[0]
            
            return {
                "success": True,
                "message": result['message'],
                "result": None
            }
        
        # No function calls, just return the message
        return {
            "success": True,
            "message": result['message'],
            "result": None
        }
    
    def query_interactive(
        self,
        user_query: str,
        context: Optional[str] = None,
        max_iterations: int = 5
    ) -> Dict[str, Any]:
        """
        Execute a natural language query with multi-turn conversation support.
        The LLM can execute multiple operations and adjust based on results.
        
        Args:
            user_query: Natural language query
            context: Optional context information
            max_iterations: Maximum number of conversation turns
        
        Returns:
            Dictionary with:
                - success: bool
                - response: str (final AI response)
                - execution_history: List[Dict] (all operations executed)
                - error: Optional[str]
        """
        if not self.nlp_enabled:
            return {
                "success": False,
                "error": "NLP features are not enabled. Check your OpenAI API key.",
                "response": "Please set OPENAI_API_KEY environment variable",
                "execution_history": []
            }
        
        # Add table list to context
        if context is None:
            tables = self.engine.list_tables()
            context = f"Available tables: {', '.join(tables)}"
        
        # Process with automatic execution
        def executor_callback(function_name: str, arguments: Dict[str, Any]) -> Any:
            return self.executor.execute(function_name, arguments)
        
        result = self.processor.process_with_execution(
            user_query=user_query,
            tools=self.tools,
            executor_callback=executor_callback,
            context=context,
            max_iterations=max_iterations
        )
        
        return result
    
    def get_context_summary(self) -> str:
        """
        Get a summary of the current database state for context.
        
        Returns:
            String with database summary
        """
        tables = self.engine.list_tables()
        
        if not tables:
            return "Database is empty. No tables exist yet."
        
        summary = f"Database: {self.database.name}\n"
        summary += f"Tables ({len(tables)}):\n"
        
        for table_name in tables:
            records = self.engine.find_all(table_name)
            summary += f"  - {table_name}: {len(records)} records\n"
        
        return summary
    
    @staticmethod
    def is_nlp_available() -> bool:
        """Check if NLP features are available."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return False
        
        try:
            import openai  # type: ignore
            return True
        except ImportError:
            return False
