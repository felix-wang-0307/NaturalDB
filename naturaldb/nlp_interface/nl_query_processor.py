"""
Natural Language Query Processor for NaturalDB Layer 3
Handles communication with OpenAI API for function calling.
"""

from typing import List, Dict, Any, Optional
import json
import os


class NLQueryProcessor:
    """
    Processes natural language queries using OpenAI's function calling API.
    Converts user queries into structured function calls.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-turbo-preview"):
        """
        Initialize the Natural Language Query Processor.
        
        Args:
            api_key: OpenAI API key. If None, reads from OPENAI_API_KEY environment variable.
            model: OpenAI model to use for function calling
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass api_key parameter."
            )
        
        self.model = model
        self.conversation_history: List[Dict[str, Any]] = []
        
        # Try to import openai
        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "OpenAI package is required. Install it with: pip install openai"
            )

    def process_query(
        self,
        user_query: str,
        tools: List[Dict[str, Any]],
        context: Optional[str] = None,
        max_iterations: int = 5
    ) -> Dict[str, Any]:
        """
        Process a natural language query and convert it to function calls.
        
        Args:
            user_query: The natural language query from the user
            tools: List of available tools (from ToolRegistry)
            context: Optional context about the database state (e.g., available tables)
            max_iterations: Maximum number of function calling iterations
            
        Returns:
            Dictionary containing:
                - 'function_calls': List of function calls to execute
                - 'explanation': Explanation of what will be done
                - 'response': Final response message
        """
        # Build the system message
        system_message = self._build_system_message(context)
        
        # Add user query to conversation
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_query}
        ]
        
        function_calls = []
        iterations = 0
        
        while iterations < max_iterations:
            try:
                # Call OpenAI API with function calling
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,  # type: ignore
                    tools=tools,  # type: ignore
                    tool_choice="auto"
                )
                
                message = response.choices[0].message
                
                # Check if the model wants to call functions
                if message.tool_calls:
                    # Extract function calls
                    for tool_call in message.tool_calls:
                        function_call = {
                            "id": tool_call.id,
                            "name": tool_call.function.name,  # type: ignore
                            "arguments": json.loads(tool_call.function.arguments)  # type: ignore
                        }
                        function_calls.append(function_call)
                    
                    # For now, we'll return after first set of function calls
                    # In a more advanced implementation, we could execute and continue conversation
                    return {
                        "function_calls": function_calls,
                        "explanation": message.content or "Executing database operations...",
                        "response": None,
                        "finish_reason": response.choices[0].finish_reason
                    }
                else:
                    # No function call, return the text response
                    return {
                        "function_calls": [],
                        "explanation": None,
                        "response": message.content,
                        "finish_reason": response.choices[0].finish_reason
                    }
                
            except Exception as e:
                return {
                    "error": str(e),
                    "function_calls": [],
                    "explanation": None,
                    "response": None
                }
            
            iterations += 1
        
        return {
            "error": "Max iterations reached",
            "function_calls": function_calls,
            "explanation": None,
            "response": None
        }

    def process_with_execution(
        self,
        user_query: str,
        tools: List[Dict[str, Any]],
        executor_callback,
        context: Optional[str] = None,
        max_iterations: int = 5
    ) -> Dict[str, Any]:
        """
        Process a query with automatic function execution and multi-turn conversation.
        
        Args:
            user_query: The natural language query
            tools: List of available tools
            executor_callback: Callback function to execute function calls
                              Should accept (function_name, arguments) and return result
            context: Optional database context
            max_iterations: Maximum conversation turns
            
        Returns:
            Dictionary with final response and execution history
        """
        system_message = self._build_system_message(context)
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_query}
        ]
        
        execution_history = []
        
        for iteration in range(max_iterations):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,  # type: ignore
                    tools=tools,  # type: ignore
                    tool_choice="auto"
                )
                
                message = response.choices[0].message
                messages.append(message.model_dump())  # Add assistant's response
                
                # Check if function calls are needed
                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        function_name = tool_call.function.name  # type: ignore
                        arguments = json.loads(tool_call.function.arguments)  # type: ignore
                        
                        # Execute the function
                        result = executor_callback(function_name, arguments)
                        
                        # Record execution
                        execution_history.append({
                            "function": function_name,
                            "arguments": arguments,
                            "result": result
                        })
                        
                        # Add function result to conversation
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result)
                        })
                else:
                    # No more function calls, return final response
                    return {
                        "response": message.content,
                        "execution_history": execution_history,
                        "iterations": iteration + 1
                    }
                    
            except Exception as e:
                return {
                    "error": str(e),
                    "execution_history": execution_history,
                    "iterations": iteration + 1
                }
        
        return {
            "error": "Max iterations reached",
            "execution_history": execution_history,
            "iterations": max_iterations
        }

    def _build_system_message(self, context: Optional[str] = None) -> str:
        """Build the system message for the LLM."""
        base_message = """You are a helpful assistant for NaturalDB, a natural language-driven NoSQL database system.

Your role is to interpret user queries and convert them into appropriate database operations using the available functions.

Key guidelines:
1. Always use the provided functions to interact with the database
2. For queries, prefer using 'select' for complex operations or specific methods like 'filter', 'find_all', etc.
3. When inserting or updating data, ensure the data structure matches the table schema
4. For sensitive operations (update, delete), acknowledge that confirmation may be required
5. If you need more information from the user, ask clarifying questions
6. Provide clear explanations of what operations you're performing

Remember:
- Table names and field names are case-sensitive
- Support nested field access with dot notation (e.g., 'specs.price')
- Available operators: eq, ne, gt, gte, lt, lte, contains
"""
        
        if context:
            base_message += f"\n\nCurrent database context:\n{context}"
        
        return base_message

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
