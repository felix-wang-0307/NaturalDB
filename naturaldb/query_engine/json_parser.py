"""
Custom JSON Parser for NaturalDB
This implementation doesn't use the external json library as required by the README.
"""

from typing import Any, Dict, List, Union, Optional
from ..errors import NaturalDBError


class JSONParserError(NaturalDBError):
    """Custom exception for JSON parsing errors"""
    def __init__(self, message: str):
        super().__init__(message, type="JSONParserError")


class JSONParser:
    """
    A custom JSON parser that doesn't rely on the external json library.
    Supports parsing JSON strings and files into Python objects.
    """
    
    @staticmethod
    def parse_file(file_path: str) -> Any:
        """
        Parse a JSON file and return the corresponding Python object.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Parsed Python object (dict, list, etc.)
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return JSONParser.parse_string(content)
    
    @staticmethod
    def parse_string(json_str: str) -> Any:
        """
        Parse a JSON string and return the corresponding Python object.
        
        Args:
            json_str: JSON string to parse
            
        Returns:
            Parsed Python object (dict, list, etc.)
        """
        json_str = json_str.strip()
        if not json_str:
            raise JSONParserError("Empty JSON string")
        
        parser = _JSONStringParser(json_str)
        return parser.parse()
    
    @staticmethod
    def to_json_string(obj: Any, indent: Optional[int] = None) -> str:
        """
        Convert a Python object to JSON string.
        
        Args:
            obj: Python object to convert
            indent: Number of spaces for indentation (None for compact)
            
        Returns:
            JSON string representation
        """
        return _JSONStringBuilder.build(obj, indent)


class _JSONStringParser:
    """Internal parser class for JSON string parsing"""
    
    def __init__(self, json_str: str):
        self.json_str = json_str
        self.pos = 0
        self.length = len(json_str)
    
    def parse(self) -> Any:
        """Parse the JSON string"""
        self._skip_whitespace()
        if self.pos >= self.length:
            raise JSONParserError("Empty JSON string")
        
        result = self._parse_value()
        self._skip_whitespace()
        
        if self.pos < self.length:
            raise JSONParserError(f"Unexpected character at position {self.pos}")
        
        return result
    
    def _parse_value(self) -> Any:
        """Parse a JSON value"""
        self._skip_whitespace()
        
        if self.pos >= self.length:
            raise JSONParserError("Unexpected end of JSON")
        
        char = self.json_str[self.pos]
        
        if char == '"':
            return self._parse_string()
        elif char == '{':
            return self._parse_object()
        elif char == '[':
            return self._parse_array()
        elif char in '-0123456789':
            return self._parse_number()
        elif char == 't':
            return self._parse_literal('true', True)
        elif char == 'f':
            return self._parse_literal('false', False)
        elif char == 'n':
            return self._parse_literal('null', None)
        else:
            raise JSONParserError(f"Unexpected character '{char}' at position {self.pos}")
    
    def _parse_string(self) -> str:
        """Parse a JSON string"""
        if self.json_str[self.pos] != '"':
            raise JSONParserError(f"Expected '\"' at position {self.pos}")
        
        self.pos += 1  # Skip opening quote
        start = self.pos
        result = []
        
        while self.pos < self.length:
            char = self.json_str[self.pos]
            
            if char == '"':
                self.pos += 1  # Skip closing quote
                return ''.join(result)
            elif char == '\\':
                self.pos += 1
                if self.pos >= self.length:
                    raise JSONParserError("Unexpected end of string")
                
                escaped = self.json_str[self.pos]
                if escaped == '"':
                    result.append('"')
                elif escaped == '\\':
                    result.append('\\')
                elif escaped == '/':
                    result.append('/')
                elif escaped == 'b':
                    result.append('\b')
                elif escaped == 'f':
                    result.append('\f')
                elif escaped == 'n':
                    result.append('\n')
                elif escaped == 'r':
                    result.append('\r')
                elif escaped == 't':
                    result.append('\t')
                elif escaped == 'u':
                    # Unicode escape sequence
                    if self.pos + 4 >= self.length:
                        raise JSONParserError("Invalid unicode escape")
                    hex_digits = self.json_str[self.pos + 1:self.pos + 5]
                    try:
                        code_point = int(hex_digits, 16)
                        result.append(chr(code_point))
                        self.pos += 4
                    except ValueError:
                        raise JSONParserError("Invalid unicode escape")
                else:
                    raise JSONParserError(f"Invalid escape sequence '\\{escaped}'")
            else:
                result.append(char)
            
            self.pos += 1
        
        raise JSONParserError("Unterminated string")
    
    def _parse_object(self) -> Dict[str, Any]:
        """Parse a JSON object"""
        if self.json_str[self.pos] != '{':
            raise JSONParserError(f"Expected '{{' at position {self.pos}")
        
        self.pos += 1  # Skip opening brace
        result = {}
        
        self._skip_whitespace()
        
        # Empty object
        if self.pos < self.length and self.json_str[self.pos] == '}':
            self.pos += 1
            return result
        
        while True:
            self._skip_whitespace()
            
            # Parse key
            if self.pos >= self.length or self.json_str[self.pos] != '"':
                raise JSONParserError("Expected string key in object")
            
            key = self._parse_string()
            
            self._skip_whitespace()
            
            # Expect colon
            if self.pos >= self.length or self.json_str[self.pos] != ':':
                raise JSONParserError("Expected ':' after object key")
            
            self.pos += 1  # Skip colon
            
            # Parse value
            value = self._parse_value()
            result[key] = value
            
            self._skip_whitespace()
            
            if self.pos >= self.length:
                raise JSONParserError("Unterminated object")
            
            char = self.json_str[self.pos]
            if char == '}':
                self.pos += 1
                break
            elif char == ',':
                self.pos += 1
                continue
            else:
                raise JSONParserError(f"Expected ',' or '}}' in object at position {self.pos}")
        
        return result
    
    def _parse_array(self) -> List[Any]:
        """Parse a JSON array"""
        if self.json_str[self.pos] != '[':
            raise JSONParserError(f"Expected '[' at position {self.pos}")
        
        self.pos += 1  # Skip opening bracket
        result = []
        
        self._skip_whitespace()
        
        # Empty array
        if self.pos < self.length and self.json_str[self.pos] == ']':
            self.pos += 1
            return result
        
        while True:
            value = self._parse_value()
            result.append(value)
            
            self._skip_whitespace()
            
            if self.pos >= self.length:
                raise JSONParserError("Unterminated array")
            
            char = self.json_str[self.pos]
            if char == ']':
                self.pos += 1
                break
            elif char == ',':
                self.pos += 1
                continue
            else:
                raise JSONParserError(f"Expected ',' or ']' in array at position {self.pos}")
        
        return result
    
    def _parse_number(self) -> Union[int, float]:
        """Parse a JSON number"""
        start = self.pos
        
        # Handle negative sign
        if self.json_str[self.pos] == '-':
            self.pos += 1
        
        # Parse integer part
        if self.pos >= self.length or not self.json_str[self.pos].isdigit():
            raise JSONParserError("Invalid number format")
        
        if self.json_str[self.pos] == '0':
            self.pos += 1
        else:
            while self.pos < self.length and self.json_str[self.pos].isdigit():
                self.pos += 1
        
        is_float = False
        
        # Parse decimal part
        if self.pos < self.length and self.json_str[self.pos] == '.':
            is_float = True
            self.pos += 1
            
            if self.pos >= self.length or not self.json_str[self.pos].isdigit():
                raise JSONParserError("Invalid number format")
            
            while self.pos < self.length and self.json_str[self.pos].isdigit():
                self.pos += 1
        
        # Parse exponent part
        if self.pos < self.length and self.json_str[self.pos] in 'eE':
            is_float = True
            self.pos += 1
            
            if self.pos < self.length and self.json_str[self.pos] in '+-':
                self.pos += 1
            
            if self.pos >= self.length or not self.json_str[self.pos].isdigit():
                raise JSONParserError("Invalid number format")
            
            while self.pos < self.length and self.json_str[self.pos].isdigit():
                self.pos += 1
        
        number_str = self.json_str[start:self.pos]
        
        try:
            return float(number_str) if is_float else int(number_str)
        except ValueError:
            raise JSONParserError(f"Invalid number: {number_str}")
    
    def _parse_literal(self, literal: str, value: Any) -> Any:
        """Parse a JSON literal (true, false, null)"""
        if not self.json_str[self.pos:].startswith(literal):
            raise JSONParserError(f"Expected '{literal}' at position {self.pos}")
        
        self.pos += len(literal)
        return value
    
    def _skip_whitespace(self):
        """Skip whitespace characters"""
        while self.pos < self.length and self.json_str[self.pos] in ' \t\n\r':
            self.pos += 1


class _JSONStringBuilder:
    """Internal builder class for converting Python objects to JSON strings"""
    
    @staticmethod
    def build(obj: Any, indent: Optional[int] = None) -> str:
        """Build JSON string from Python object"""
        builder = _JSONStringBuilder()
        return builder._build_value(obj, 0, indent)
    
    def _build_value(self, obj: Any, depth: int, indent: Optional[int]) -> str:
        """Build JSON string for a value"""
        if obj is None:
            return 'null'
        elif obj is True:
            return 'true'
        elif obj is False:
            return 'false'
        elif isinstance(obj, str):
            return self._build_string(obj)
        elif isinstance(obj, (int, float)):
            return str(obj)
        elif isinstance(obj, list):
            return self._build_array(obj, depth, indent)
        elif isinstance(obj, dict):
            return self._build_object(obj, depth, indent)
        else:
            raise JSONParserError(f"Unsupported type: {type(obj)}")
    
    def _build_string(self, s: str) -> str:
        """Build JSON string representation"""
        result = ['"']
        
        for char in s:
            if char == '"':
                result.append('\\"')
            elif char == '\\':
                result.append('\\\\')
            elif char == '\b':
                result.append('\\b')
            elif char == '\f':
                result.append('\\f')
            elif char == '\n':
                result.append('\\n')
            elif char == '\r':
                result.append('\\r')
            elif char == '\t':
                result.append('\\t')
            elif ord(char) < 32:
                result.append(f'\\u{ord(char):04x}')
            else:
                result.append(char)
        
        result.append('"')
        return ''.join(result)
    
    def _build_array(self, arr: List[Any], depth: int, indent: Optional[int]) -> str:
        """Build JSON array representation"""
        if not arr:
            return '[]'
        
        if indent is None:
            items = [self._build_value(item, depth, indent) for item in arr]
            return '[' + ','.join(items) + ']'
        else:
            items = []
            for item in arr:
                item_str = self._build_value(item, depth + 1, indent)
                items.append(' ' * ((depth + 1) * indent) + item_str)
            
            return '[\n' + ',\n'.join(items) + '\n' + ' ' * (depth * indent) + ']'
    
    def _build_object(self, obj: Dict[str, Any], depth: int, indent: Optional[int]) -> str:
        """Build JSON object representation"""
        if not obj:
            return '{}'
        
        if indent is None:
            items = []
            for key, value in obj.items():
                key_str = self._build_string(key)
                value_str = self._build_value(value, depth, indent)
                items.append(f'{key_str}:{value_str}')
            return '{' + ','.join(items) + '}'
        else:
            items = []
            for key, value in obj.items():
                key_str = self._build_string(key)
                value_str = self._build_value(value, depth + 1, indent)
                items.append(' ' * ((depth + 1) * indent) + f'{key_str}: {value_str}')
            
            return '{\n' + ',\n'.join(items) + '\n' + ' ' * (depth * indent) + '}'