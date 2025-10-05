"""
Custom JSON utilities for NaturalDB
Implements a custom JSON parser without using the built-in json library.
"""

import re
from typing import Any, Dict, List, Union

JsonValue = Union[None, bool, int, float, str, List['JsonValue'], Dict[str, 'JsonValue']]


class JSONParseError(Exception):
    """Custom exception for JSON parsing errors."""
    pass


class JSONParser:
    """Custom JSON parser implementation."""
    
    def __init__(self, text: str):
        self.text = text.strip()
        self.pos = 0
        self.length = len(self.text)
    
    def parse(self) -> JsonValue:
        """Parse JSON text and return the parsed value."""
        value = self._parse_value()
        self._skip_whitespace()
        if self.pos < self.length:
            raise JSONParseError(f"Unexpected character at position {self.pos}: '{self.text[self.pos]}'")
        return value
    
    def _parse_value(self) -> JsonValue:
        """Parse a JSON value."""
        self._skip_whitespace()
        
        if self.pos >= self.length:
            raise JSONParseError("Unexpected end of input")
        
        char = self.text[self.pos]
        
        if char == '"':
            return self._parse_string()
        elif char == '{':
            return self._parse_object()
        elif char == '[':
            return self._parse_array()
        elif char == 't' or char == 'f':
            return self._parse_boolean()
        elif char == 'n':
            return self._parse_null()
        elif char == '-' or char.isdigit():
            return self._parse_number()
        else:
            raise JSONParseError(f"Unexpected character at position {self.pos}: '{char}'")
    
    def _parse_string(self) -> str:
        """Parse a JSON string."""
        if self.text[self.pos] != '"':
            raise JSONParseError(f"Expected '\"' at position {self.pos}")
        
        self.pos += 1  # Skip opening quote
        start = self.pos
        result = ""
        
        while self.pos < self.length:
            char = self.text[self.pos]
            
            if char == '"':
                result += self.text[start:self.pos]
                self.pos += 1  # Skip closing quote
                return result
            elif char == '\\':
                result += self.text[start:self.pos]
                self.pos += 1
                if self.pos >= self.length:
                    raise JSONParseError("Unexpected end of input in string escape")
                
                escape_char = self.text[self.pos]
                if escape_char == '"':
                    result += '"'
                elif escape_char == '\\':
                    result += '\\'
                elif escape_char == '/':
                    result += '/'
                elif escape_char == 'b':
                    result += '\b'
                elif escape_char == 'f':
                    result += '\f'
                elif escape_char == 'n':
                    result += '\n'
                elif escape_char == 'r':
                    result += '\r'
                elif escape_char == 't':
                    result += '\t'
                elif escape_char == 'u':
                    # Unicode escape sequence
                    if self.pos + 4 >= self.length:
                        raise JSONParseError("Invalid unicode escape sequence")
                    hex_digits = self.text[self.pos + 1:self.pos + 5]
                    try:
                        code_point = int(hex_digits, 16)
                        result += chr(code_point)
                        self.pos += 4
                    except ValueError:
                        raise JSONParseError("Invalid unicode escape sequence")
                else:
                    raise JSONParseError(f"Invalid escape sequence: \\{escape_char}")
                
                self.pos += 1
                start = self.pos
            else:
                self.pos += 1
        
        raise JSONParseError("Unterminated string")
    
    def _parse_object(self) -> Dict[str, JsonValue]:
        """Parse a JSON object."""
        if self.text[self.pos] != '{':
            raise JSONParseError(f"Expected '{{' at position {self.pos}")
        
        self.pos += 1  # Skip opening brace
        self._skip_whitespace()
        
        result = {}
        
        # Handle empty object
        if self.pos < self.length and self.text[self.pos] == '}':
            self.pos += 1
            return result
        
        while True:
            # Parse key
            self._skip_whitespace()
            if self.pos >= self.length:
                raise JSONParseError("Unexpected end of input in object")
            
            if self.text[self.pos] != '"':
                raise JSONParseError(f"Expected string key at position {self.pos}")
            
            key = self._parse_string()
            
            # Parse colon
            self._skip_whitespace()
            if self.pos >= self.length or self.text[self.pos] != ':':
                raise JSONParseError(f"Expected ':' at position {self.pos}")
            self.pos += 1
            
            # Parse value
            value = self._parse_value()
            result[key] = value
            
            # Check for continuation
            self._skip_whitespace()
            if self.pos >= self.length:
                raise JSONParseError("Unexpected end of input in object")
            
            char = self.text[self.pos]
            if char == '}':
                self.pos += 1
                break
            elif char == ',':
                self.pos += 1
                continue
            else:
                raise JSONParseError(f"Expected ',' or '}}' at position {self.pos}")
        
        return result
    
    def _parse_array(self) -> List[JsonValue]:
        """Parse a JSON array."""
        if self.text[self.pos] != '[':
            raise JSONParseError(f"Expected '[' at position {self.pos}")
        
        self.pos += 1  # Skip opening bracket
        self._skip_whitespace()
        
        result = []
        
        # Handle empty array
        if self.pos < self.length and self.text[self.pos] == ']':
            self.pos += 1
            return result
        
        while True:
            # Parse value
            value = self._parse_value()
            result.append(value)
            
            # Check for continuation
            self._skip_whitespace()
            if self.pos >= self.length:
                raise JSONParseError("Unexpected end of input in array")
            
            char = self.text[self.pos]
            if char == ']':
                self.pos += 1
                break
            elif char == ',':
                self.pos += 1
                continue
            else:
                raise JSONParseError(f"Expected ',' or ']' at position {self.pos}")
        
        return result
    
    def _parse_boolean(self) -> bool:
        """Parse a JSON boolean."""
        if self.text[self.pos:self.pos + 4] == 'true':
            self.pos += 4
            return True
        elif self.text[self.pos:self.pos + 5] == 'false':
            self.pos += 5
            return False
        else:
            raise JSONParseError(f"Invalid boolean at position {self.pos}")
    
    def _parse_null(self) -> None:
        """Parse a JSON null."""
        if self.text[self.pos:self.pos + 4] == 'null':
            self.pos += 4
            return None
        else:
            raise JSONParseError(f"Invalid null at position {self.pos}")
    
    def _parse_number(self) -> Union[int, float]:
        """Parse a JSON number."""
        start = self.pos
        
        # Handle negative sign
        if self.text[self.pos] == '-':
            self.pos += 1
        
        # Parse integer part
        if self.pos >= self.length or not self.text[self.pos].isdigit():
            raise JSONParseError(f"Invalid number at position {start}")
        
        if self.text[self.pos] == '0':
            self.pos += 1
        else:
            while self.pos < self.length and self.text[self.pos].isdigit():
                self.pos += 1
        
        is_float = False
        
        # Parse decimal part
        if self.pos < self.length and self.text[self.pos] == '.':
            is_float = True
            self.pos += 1
            if self.pos >= self.length or not self.text[self.pos].isdigit():
                raise JSONParseError(f"Invalid number at position {start}")
            while self.pos < self.length and self.text[self.pos].isdigit():
                self.pos += 1
        
        # Parse exponent part
        if self.pos < self.length and self.text[self.pos].lower() == 'e':
            is_float = True
            self.pos += 1
            if self.pos < self.length and self.text[self.pos] in '+-':
                self.pos += 1
            if self.pos >= self.length or not self.text[self.pos].isdigit():
                raise JSONParseError(f"Invalid number at position {start}")
            while self.pos < self.length and self.text[self.pos].isdigit():
                self.pos += 1
        
        number_str = self.text[start:self.pos]
        try:
            return float(number_str) if is_float else int(number_str)
        except ValueError:
            raise JSONParseError(f"Invalid number format: {number_str}")
    
    def _skip_whitespace(self) -> None:
        """Skip whitespace characters."""
        while self.pos < self.length and self.text[self.pos] in ' \t\n\r':
            self.pos += 1


def parse_json(text: str) -> JsonValue:
    """
    Parse JSON text and return the parsed value.
    
    Args:
        text: JSON text to parse
        
    Returns:
        Parsed JSON value
        
    Raises:
        JSONParseError: If parsing fails
    """
    parser = JSONParser(text)
    return parser.parse()


def serialize_json(value: JsonValue, indent: int = 0) -> str:
    """
    Serialize a Python value to JSON string.
    
    Args:
        value: Value to serialize
        indent: Number of spaces for indentation (0 for compact output)
        
    Returns:
        JSON string representation
    """
    return _serialize_value(value, 0, indent)


def _serialize_value(value: JsonValue, current_indent: int, indent_size: int) -> str:
    """Helper function to serialize a value."""
    if value is None:
        return 'null'
    elif isinstance(value, bool):
        return 'true' if value else 'false'
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, str):
        return _serialize_string(value)
    elif isinstance(value, list):
        return _serialize_array(value, current_indent, indent_size)
    elif isinstance(value, dict):
        return _serialize_object(value, current_indent, indent_size)
    else:
        raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _serialize_string(s: str) -> str:
    """Serialize a string with proper escaping."""
    result = '"'
    for char in s:
        if char == '"':
            result += '\\"'
        elif char == '\\':
            result += '\\\\'
        elif char == '\b':
            result += '\\b'
        elif char == '\f':
            result += '\\f'
        elif char == '\n':
            result += '\\n'
        elif char == '\r':
            result += '\\r'
        elif char == '\t':
            result += '\\t'
        elif ord(char) < 32:
            result += f'\\u{ord(char):04x}'
        else:
            result += char
    result += '"'
    return result


def _serialize_array(arr: List[JsonValue], current_indent: int, indent_size: int) -> str:
    """Serialize an array."""
    if not arr:
        return '[]'
    
    if indent_size == 0:
        items = [_serialize_value(item, 0, 0) for item in arr]
        return '[' + ','.join(items) + ']'
    else:
        new_indent = current_indent + indent_size
        indent_str = ' ' * new_indent
        close_indent_str = ' ' * current_indent
        
        items = []
        for item in arr:
            serialized = _serialize_value(item, new_indent, indent_size)
            items.append(f'{indent_str}{serialized}')
        
        return '[\n' + ',\n'.join(items) + f'\n{close_indent_str}]'


def _serialize_object(obj: Dict[str, JsonValue], current_indent: int, indent_size: int) -> str:
    """Serialize an object."""
    if not obj:
        return '{}'
    
    if indent_size == 0:
        items = []
        for key, value in obj.items():
            key_str = _serialize_string(key)
            value_str = _serialize_value(value, 0, 0)
            items.append(f'{key_str}:{value_str}')
        return '{' + ','.join(items) + '}'
    else:
        new_indent = current_indent + indent_size
        indent_str = ' ' * new_indent
        close_indent_str = ' ' * current_indent
        
        items = []
        for key, value in obj.items():
            key_str = _serialize_string(key)
            value_str = _serialize_value(value, new_indent, indent_size)
            items.append(f'{indent_str}{key_str}: {value_str}')
        
        return '{\n' + ',\n'.join(items) + f'\n{close_indent_str}}}'


def validate_json_structure(data: JsonValue, expected_keys: list[str] | None = None) -> bool:
    """
    Validate JSON structure and optionally check for expected keys.
    
    Args:
        data: Parsed JSON data
        expected_keys: List of keys that should be present in the object
        
    Returns:
        True if validation passes, False otherwise
    """
    if expected_keys is None:
        return True
    
    if not isinstance(data, dict):
        return False
    
    return all(key in data for key in expected_keys)