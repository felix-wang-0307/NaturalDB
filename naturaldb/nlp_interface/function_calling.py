from typing import Callable, Optional, List, Dict, Any, Union
import inspect
import re


class OpenAiTool:
    """
    A wrapper for an OpenAI-styled tool with function calling capabilities.
    A tool is a callable function with a name, description, and parameters.
    """

    def __init__(
        self,
        func: Callable,
        description: Optional[str] = None,
        param_descriptions: Optional[dict] = None,
    ) -> None:
        self.name = func.__name__
        self.description = description or func.__doc__ or "No description provided."
        self.parameters = inspect.signature(func).parameters
        self.param_descriptions = param_descriptions or {}
        self.func = func

    def _get_param_description(self, param: str) -> str:
        """
        Get the description for a given parameter.
        If a description is provided in param_descriptions, use it.
        Otherwise, retrieve from docstring if available, or use a default message.
        """
        if param in self.param_descriptions:
            return self.param_descriptions[param]
        doc = inspect.getdoc(self.func)
        if not doc:
            return f"The {param} parameter"
        # Simple regex to find parameter descriptions in the docstring
        pattern = re.compile(rf":param {param}:(.*)")
        match = pattern.search(doc)
        if match:
            return match.group(1).strip()
        # No specific description found, return a default message
        return f"The {param} parameter"

    def to_dict(self) -> dict:
        """
        Convert the tool to a dictionary representation suitable for OpenAI function calling.
        """
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self._wrap_parameters(),
        }

    def _wrap_parameters(self) -> dict:
        """
        Wrap parameters to match OpenAI function calling schema.
        Example:
        "parameters": {
            "type": "object",
            "properties": {
                "sign": {
                    "type": "string",
                    "description": "An astrological sign like Taurus or Aquarius",
                },
            },
            "required": ["sign"],
        }
        """

        props = {}
        required = []
        for param, p_type in self.parameters.items():
            # Skip 'return' parameter
            if param == "return":
                continue
            # Get description from provided descriptions or docstring
            props[param] = {
                "type": self._map_type(p_type.annotation),
                "description": self._get_param_description(param),
            }
            # Check if the parameter is required (no default value)
            if (
                param not in inspect.signature(self.func).parameters
                or inspect.signature(self.func).parameters[param].default
                == inspect.Parameter.empty
            ):
                required.append(param)
        return {"type": "object", "properties": props, "required": required}

    def _map_type(self, p_type: type) -> str:
        """
        Map Python types to OpenAI function calling types.
        Handles both simple types and typing module types (List, Dict, Optional, etc.)
        """
        # Handle None type
        if p_type is type(None):
            return "null"
        
        # Get the origin type for typing generics (e.g., List[str] -> list)
        origin = getattr(p_type, "__origin__", None)
        
        if origin is not None:
            # Handle Optional[X] which is Union[X, None]
            if origin is Union:
                args = getattr(p_type, "__args__", ())
                # Filter out NoneType
                non_none_args = [arg for arg in args if arg is not type(None)]
                if non_none_args:
                    # Use the first non-None type
                    return self._map_type(non_none_args[0])
            # Handle List, Dict, etc.
            elif origin is list:
                return "array"
            elif origin is dict:
                return "object"
        
        # Simple type mapping
        type_mapping = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            dict: "object",
            list: "array",
        }
        return type_mapping.get(p_type, "string")

    @staticmethod
    def create_tool_object(
        func: Callable,
        description: Optional[str] = None,
        param_descriptions: Optional[dict] = None,
    ) -> dict:
        """
        Static method to create a tool object dictionary directly from a function.
        """
        tool = OpenAiTool(
            func, description=description, param_descriptions=param_descriptions
        )
        return tool.to_dict()


class ToolRegistry:
    """
    Automatic tool registry that converts class methods into OpenAI function calling tools.
    """
    
    @staticmethod
    def register_class_methods(
        target_class: type,
        method_names: Optional[List[str]] = None,
        exclude_methods: Optional[List[str]] = None,
        method_descriptions: Optional[Dict[str, str]] = None,
        param_descriptions: Optional[Dict[str, Dict[str, str]]] = None,
        instance: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Automatically register methods from a class as OpenAI tools.
        
        Args:
            cls: The class to extract methods from
            method_names: Optional list of specific method names to register. If None, registers all public methods.
            exclude_methods: Optional list of method names to exclude from registration
            method_descriptions: Optional dict mapping method names to custom descriptions
            param_descriptions: Optional nested dict mapping method names to param descriptions
                               e.g., {"insert": {"table_name": "The table to insert into"}}
            instance: Optional instance to bind methods to (if None, uses unbound methods)
        
        Returns:
            List of OpenAI tool definitions
        """
        tools = []
        exclude_methods = exclude_methods or []
        method_descriptions = method_descriptions or {}
        param_descriptions = param_descriptions or {}
        
        # Get all methods from the class
        all_methods = inspect.getmembers(target_class, predicate=inspect.isfunction)
        
        for method_name, method in all_methods:
            # Skip private/magic methods and excluded methods
            if method_name.startswith('_') or method_name in exclude_methods:
                continue
            
            # If method_names is specified, only include those
            if method_names and method_name not in method_names:
                continue
            
            # Get custom description or use docstring
            description = method_descriptions.get(method_name)
            
            # Get parameter descriptions for this method
            method_param_desc = param_descriptions.get(method_name, {})
            
            # Create the tool
            if instance:
                # Bind to instance
                bound_method = getattr(instance, method_name)
                tool = OpenAiTool(
                    bound_method,
                    description=description,
                    param_descriptions=method_param_desc
                )
            else:
                # Use unbound method (will need to skip 'self' parameter)
                tool = OpenAiTool(
                    method,
                    description=description,
                    param_descriptions=method_param_desc
                )
            
            tool_dict = tool.to_dict()
            
            # Remove 'self' parameter if present (for unbound methods)
            if 'self' in tool_dict.get('parameters', {}).get('properties', {}):
                del tool_dict['parameters']['properties']['self']
                if 'self' in tool_dict.get('parameters', {}).get('required', []):
                    tool_dict['parameters']['required'].remove('self')
            
            # Wrap in function object for OpenAI format
            tools.append({
                "type": "function",
                "function": {
                    "name": tool_dict["name"],
                    "description": tool_dict["description"],
                    "parameters": tool_dict["parameters"]
                }
            })
        
        return tools
    
    @staticmethod
    def register_functions(
        functions: List[Callable],
        descriptions: Optional[Dict[str, str]] = None,
        param_descriptions: Optional[Dict[str, Dict[str, str]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Register a list of standalone functions as OpenAI tools.
        
        Args:
            functions: List of functions to register
            descriptions: Optional dict mapping function names to custom descriptions
            param_descriptions: Optional nested dict mapping function names to param descriptions
        
        Returns:
            List of OpenAI tool definitions
        """
        tools = []
        descriptions = descriptions or {}
        param_descriptions = param_descriptions or {}
        
        for func in functions:
            func_name = func.__name__
            description = descriptions.get(func_name)
            method_param_desc = param_descriptions.get(func_name, {})
            
            tool_dict = OpenAiTool.create_tool_object(
                func,
                description=description,
                param_descriptions=method_param_desc
            )
            
            # Wrap in function object for OpenAI format
            tools.append({
                "type": "function",
                "function": {
                    "name": tool_dict["name"],
                    "description": tool_dict["description"],
                    "parameters": tool_dict["parameters"]
                }
            })
        
        return tools
    
