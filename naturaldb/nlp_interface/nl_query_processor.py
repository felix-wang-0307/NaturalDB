"""
Natural Language Query Processor - Converts natural language to function calls using OpenAI
"""

from typing import List, Dict, Any, Optional, Callable
import os
import json


class NLQueryProcessor:
    """
    Processes natural language queries and converts them to function calls using OpenAI API.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize the NL Query Processor.
        
        Args:
            api_key: OpenAI API key (if None, reads from OPENAI_API_KEY env var)
            model: OpenAI model to use (default: gpt-4o-mini for cost efficiency)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY environment variable")
        
        self.model = model
        
        try:
            from openai import OpenAI  # type: ignore
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
    
    def process_query(
        self,
        user_query: str,
        tools: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a natural language query and return function calls.
        
        Args:
            user_query: The natural language query from the user
            tools: List of available tools (from DatabaseToolRegistry)
            system_prompt: Optional custom system prompt
            context: Optional context information (e.g., available tables, current state)
        
        Returns:
            Dictionary with:
                - success: bool
                - message: str (AI response)
                - function_calls: List[Dict] (function calls to execute)
                - error: Optional[str] (error message if failed)
        """
        if not system_prompt:
            system_prompt = self._get_default_system_prompt()
        
        # Add context to system prompt if provided
        if context:
            system_prompt += f"\n\nContext:\n{context}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore
                tools=tools,  # type: ignore
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            
            # Extract function calls if any
            function_calls = []
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    function_calls.append({
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": json.loads(tool_call.function.arguments)
                    })
            
            return {
                "success": True,
                "message": message.content or "Operation completed",
                "function_calls": function_calls,
                "raw_response": message
            }
        
        except Exception as e:
            return {
                "success": False,
                "message": "",
                "function_calls": [],
                "error": str(e)
            }
    
    def process_with_execution(
        self,
        user_query: str,
        tools: List[Dict[str, Any]],
        executor_callback: Callable[[str, Dict[str, Any]], Any],
        system_prompt: Optional[str] = None,
        context: Optional[str] = None,
        max_iterations: int = 5
    ) -> Dict[str, Any]:
        """
        Process query and automatically execute function calls in a multi-turn conversation.
        
        Args:
            user_query: The natural language query
            tools: Available tools
            executor_callback: Callback function that executes a function call
                              Should accept (function_name, arguments) and return result
            system_prompt: Optional custom system prompt
            context: Optional context information
            max_iterations: Maximum number of back-and-forth iterations
        
        Returns:
            Dictionary with:
                - success: bool
                - response: str (final AI response)
                - execution_history: List[Dict] (history of function calls and results)
                - error: Optional[str]
        """
        if not system_prompt:
            system_prompt = self._get_default_system_prompt()
        
        if context:
            system_prompt += f"\n\nContext:\n{context}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
        
        execution_history = []
        
        try:
            for iteration in range(max_iterations):
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,  # type: ignore
                    tools=tools,  # type: ignore
                    tool_choice="auto"
                )
                
                message = response.choices[0].message
                messages.append(message)  # type: ignore
                
                # If no tool calls, we're done
                if not message.tool_calls:
                    return {
                        "success": True,
                        "response": message.content or "Operation completed",
                        "execution_history": execution_history
                    }
                
                # Execute each tool call
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    # Execute the function
                    try:
                        result = executor_callback(function_name, arguments)
                        result_str = json.dumps(result) if not isinstance(result, str) else result
                        
                        execution_history.append({
                            "function": function_name,
                            "arguments": arguments,
                            "result": result,
                            "success": True
                        })
                        
                        # Add function result to conversation
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result_str
                        })
                    
                    except Exception as e:
                        error_msg = f"Error executing {function_name}: {str(e)}"
                        execution_history.append({
                            "function": function_name,
                            "arguments": arguments,
                            "error": str(e),
                            "success": False
                        })
                        
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": error_msg
                        })
            
            # Max iterations reached
            return {
                "success": True,
                "response": "Maximum iterations reached. Some operations may be incomplete.",
                "execution_history": execution_history
            }
        
        except Exception as e:
            return {
                "success": False,
                "response": "",
                "execution_history": execution_history,
                "error": str(e)
            }
    
    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt for database operations."""
        return """You are a helpful database assistant for NaturalDB, a NoSQL database system.

Your role is to help users interact with their database using natural language. You can:
- Create and manage tables
- Insert, update, and delete records
- Query data using filters, projections, and aggregations
- Perform joins between tables
- Import and export data

Guidelines:
- Be precise and confirm sensitive operations (updates, deletes)
- When creating filters, use the correct operators: eq, ne, gt, gte, lt, lte, in, nin, contains
- For aggregations, use operations: count, sum, avg, min, max
- Always provide clear feedback about what you're doing
- If a user's request is ambiguous, ask for clarification

Available operators for filters:
- eq (equal), ne (not equal), gt (greater than), gte (greater than or equal)
- lt (less than), lte (less than or equal), in (in list), nin (not in list)
- contains (substring match)

Remember: Execute operations only when you're confident about the user's intent."""
    
    @staticmethod
    def is_available() -> bool:
        """Check if OpenAI API is available."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return False
        try:
            import openai  # type: ignore
            return True
        except ImportError:
            return False
