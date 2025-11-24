"""
Test suite for NaturalDB JSON Parser
Tests the custom JSON parser without using the built-in json library.
"""

import pytest
import os
import tempfile
import sys
from typing import Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from naturaldb.json_parser import JSONParser, JSONParserError


class TestJSONParserBasicTypes:
    """Test parsing of basic JSON types"""

    def test_parse_null(self):
        """Test parsing null value"""
        result = JSONParser.parse_string("null")
        assert result is None

    def test_parse_true(self):
        """Test parsing boolean true"""
        result = JSONParser.parse_string("true")
        assert result is True

    def test_parse_false(self):
        """Test parsing boolean false"""
        result = JSONParser.parse_string("false")
        assert result is False

    def test_parse_integer(self):
        """Test parsing integer"""
        assert JSONParser.parse_string("42") == 42
        assert JSONParser.parse_string("0") == 0
        assert JSONParser.parse_string("-123") == -123

    def test_parse_float(self):
        """Test parsing floating point numbers"""
        assert JSONParser.parse_string("3.14") == 3.14
        assert JSONParser.parse_string("-0.5") == -0.5
        assert JSONParser.parse_string("2.0") == 2.0

    def test_parse_scientific_notation(self):
        """Test parsing numbers in scientific notation"""
        assert JSONParser.parse_string("1e10") == 1e10
        assert JSONParser.parse_string("1.5e-3") == 1.5e-3
        assert JSONParser.parse_string("2E+5") == 2E+5

    def test_parse_simple_string(self):
        """Test parsing simple strings"""
        assert JSONParser.parse_string('"hello"') == "hello"
        assert JSONParser.parse_string('""') == ""
        assert JSONParser.parse_string('"123"') == "123"

    def test_parse_string_with_spaces(self):
        """Test parsing strings with spaces"""
        assert JSONParser.parse_string('"hello world"') == "hello world"
        assert JSONParser.parse_string('"  spaces  "') == "  spaces  "


class TestJSONParserEscapeSequences:
    """Test parsing of escape sequences in strings"""

    def test_parse_escaped_quotes(self):
        """Test parsing escaped quotes"""
        assert JSONParser.parse_string(r'"say \"hello\""') == 'say "hello"'

    def test_parse_escaped_backslash(self):
        """Test parsing escaped backslash"""
        assert JSONParser.parse_string(r'"path\\to\\file"') == "path\\to\\file"

    def test_parse_escaped_slash(self):
        """Test parsing escaped forward slash"""
        assert JSONParser.parse_string(r'"a\/b"') == "a/b"

    def test_parse_escaped_control_chars(self):
        """Test parsing escaped control characters"""
        assert JSONParser.parse_string(r'"line1\nline2"') == "line1\nline2"
        assert JSONParser.parse_string(r'"tab\there"') == "tab\there"
        assert JSONParser.parse_string(r'"carriage\rreturn"') == "carriage\rreturn"
        assert JSONParser.parse_string(r'"form\ffeed"') == "form\ffeed"
        assert JSONParser.parse_string(r'"back\bspace"') == "back\bspace"

    def test_parse_unicode_escape(self):
        """Test parsing unicode escape sequences"""
        assert JSONParser.parse_string(r'"\u0041"') == "A"
        assert JSONParser.parse_string(r'"\u03B1"') == "α"
        assert JSONParser.parse_string(r'"\u4E2D"') == "中"


class TestJSONParserArrays:
    """Test parsing of JSON arrays"""

    def test_parse_empty_array(self):
        """Test parsing empty array"""
        assert JSONParser.parse_string("[]") == []

    def test_parse_simple_array(self):
        """Test parsing simple arrays"""
        assert JSONParser.parse_string("[1, 2, 3]") == [1, 2, 3]
        assert JSONParser.parse_string('["a", "b", "c"]') == ["a", "b", "c"]

    def test_parse_mixed_type_array(self):
        """Test parsing arrays with mixed types"""
        result = JSONParser.parse_string('[1, "two", true, null, 3.14]')
        assert result == [1, "two", True, None, 3.14]

    def test_parse_nested_arrays(self):
        """Test parsing nested arrays"""
        result = JSONParser.parse_string("[[1, 2], [3, 4], [5, 6]]")
        assert result == [[1, 2], [3, 4], [5, 6]]

    def test_parse_array_with_whitespace(self):
        """Test parsing arrays with various whitespace"""
        result = JSONParser.parse_string("[ 1 , 2 , 3 ]")
        assert result == [1, 2, 3]
        
        result = JSONParser.parse_string("""[
            1,
            2,
            3
        ]""")
        assert result == [1, 2, 3]


class TestJSONParserObjects:
    """Test parsing of JSON objects"""

    def test_parse_empty_object(self):
        """Test parsing empty object"""
        assert JSONParser.parse_string("{}") == {}

    def test_parse_simple_object(self):
        """Test parsing simple objects"""
        result = JSONParser.parse_string('{"name": "John", "age": 30}')
        assert result == {"name": "John", "age": 30}

    def test_parse_object_with_various_types(self):
        """Test parsing objects with different value types"""
        json_str = '''
        {
            "string": "value",
            "number": 42,
            "float": 3.14,
            "boolean": true,
            "null_value": null,
            "array": [1, 2, 3]
        }
        '''
        result = JSONParser.parse_string(json_str)
        assert result["string"] == "value"
        assert result["number"] == 42
        assert result["float"] == 3.14
        assert result["boolean"] is True
        assert result["null_value"] is None
        assert result["array"] == [1, 2, 3]

    def test_parse_nested_objects(self):
        """Test parsing nested objects"""
        json_str = '''
        {
            "person": {
                "name": "Alice",
                "address": {
                    "city": "New York",
                    "zip": "10001"
                }
            }
        }
        '''
        result = JSONParser.parse_string(json_str)
        assert result["person"]["name"] == "Alice"
        assert result["person"]["address"]["city"] == "New York"
        assert result["person"]["address"]["zip"] == "10001"

    def test_parse_object_with_array_values(self):
        """Test parsing objects containing arrays"""
        json_str = '{"numbers": [1, 2, 3], "names": ["Alice", "Bob"]}'
        result = JSONParser.parse_string(json_str)
        assert result["numbers"] == [1, 2, 3]
        assert result["names"] == ["Alice", "Bob"]

    def test_parse_complex_structure(self):
        """Test parsing complex nested structure"""
        json_str = '''
        {
            "users": [
                {
                    "id": 1,
                    "name": "Alice",
                    "tags": ["admin", "user"]
                },
                {
                    "id": 2,
                    "name": "Bob",
                    "tags": ["user"]
                }
            ],
            "metadata": {
                "count": 2,
                "version": "1.0"
            }
        }
        '''
        result = JSONParser.parse_string(json_str)
        assert len(result["users"]) == 2
        assert result["users"][0]["name"] == "Alice"
        assert result["users"][1]["tags"] == ["user"]
        assert result["metadata"]["count"] == 2


class TestJSONParserWhitespace:
    """Test handling of whitespace"""

    def test_parse_with_leading_whitespace(self):
        """Test parsing with leading whitespace"""
        assert JSONParser.parse_string("   42") == 42
        assert JSONParser.parse_string("\n\t{\"a\": 1}") == {"a": 1}

    def test_parse_with_trailing_whitespace(self):
        """Test parsing with trailing whitespace"""
        assert JSONParser.parse_string("42   ") == 42
        assert JSONParser.parse_string("{\"a\": 1}\n\n") == {"a": 1}

    def test_parse_with_internal_whitespace(self):
        """Test parsing with various internal whitespace"""
        result = JSONParser.parse_string('{ "a" : 1 , "b" : 2 }')
        assert result == {"a": 1, "b": 2}


class TestJSONParserErrors:
    """Test error handling"""

    def test_parse_empty_string(self):
        """Test parsing empty string raises error"""
        with pytest.raises(JSONParserError):
            JSONParser.parse_string("")

    def test_parse_invalid_json(self):
        """Test parsing invalid JSON raises error"""
        with pytest.raises(JSONParserError):
            JSONParser.parse_string("invalid")

    def test_parse_unterminated_string(self):
        """Test parsing unterminated string raises error"""
        with pytest.raises(JSONParserError):
            JSONParser.parse_string('"unterminated')

    def test_parse_unterminated_array(self):
        """Test parsing unterminated array raises error"""
        with pytest.raises(JSONParserError):
            JSONParser.parse_string("[1, 2, 3")

    def test_parse_unterminated_object(self):
        """Test parsing unterminated object raises error"""
        with pytest.raises(JSONParserError):
            JSONParser.parse_string('{"key": "value"')

    def test_parse_invalid_number(self):
        """Test parsing invalid number raises error"""
        with pytest.raises(JSONParserError):
            JSONParser.parse_string("123.456.789")

    def test_parse_trailing_comma_array(self):
        """Test parsing array with trailing comma"""
        with pytest.raises(JSONParserError):
            JSONParser.parse_string("[1, 2, 3,]")

    def test_parse_trailing_comma_object(self):
        """Test parsing object with trailing comma"""
        with pytest.raises(JSONParserError):
            JSONParser.parse_string('{"a": 1,}')

    def test_parse_missing_colon(self):
        """Test parsing object with missing colon"""
        with pytest.raises(JSONParserError):
            JSONParser.parse_string('{"key" "value"}')

    def test_parse_invalid_escape_sequence(self):
        """Test parsing invalid escape sequence"""
        with pytest.raises(JSONParserError):
            JSONParser.parse_string(r'"invalid\x escape"')


class TestJSONStringBuilder:
    """Test JSON string generation"""

    def test_to_json_null(self):
        """Test converting None to JSON"""
        assert JSONParser.to_json_string(None) == "null"

    def test_to_json_boolean(self):
        """Test converting booleans to JSON"""
        assert JSONParser.to_json_string(True) == "true"
        assert JSONParser.to_json_string(False) == "false"

    def test_to_json_number(self):
        """Test converting numbers to JSON"""
        assert JSONParser.to_json_string(42) == "42"
        assert JSONParser.to_json_string(3.14) == "3.14"
        assert JSONParser.to_json_string(-123) == "-123"

    def test_to_json_string(self):
        """Test converting strings to JSON"""
        assert JSONParser.to_json_string("hello") == '"hello"'
        assert JSONParser.to_json_string("") == '""'

    def test_to_json_string_with_escapes(self):
        """Test converting strings with special characters"""
        assert JSONParser.to_json_string('say "hello"') == r'"say \"hello\""'
        assert JSONParser.to_json_string("line1\nline2") == r'"line1\nline2"'
        assert JSONParser.to_json_string("tab\there") == r'"tab\there"'

    def test_to_json_array(self):
        """Test converting arrays to JSON"""
        assert JSONParser.to_json_string([]) == "[]"
        assert JSONParser.to_json_string([1, 2, 3]) == "[1,2,3]"
        assert JSONParser.to_json_string(["a", "b"]) == '["a","b"]'

    def test_to_json_object(self):
        """Test converting objects to JSON"""
        assert JSONParser.to_json_string({}) == "{}"
        result = JSONParser.to_json_string({"a": 1, "b": 2})
        # Order might vary, so check both are valid
        assert result in ['{"a":1,"b":2}', '{"b":2,"a":1}']

    def test_to_json_with_indent(self):
        """Test converting with indentation"""
        obj = {"name": "John", "age": 30}
        result = JSONParser.to_json_string(obj, indent=2)
        assert "\n" in result
        assert "  " in result

    def test_to_json_nested_structure(self):
        """Test converting nested structures"""
        data = {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ]
        }
        result = JSONParser.to_json_string(data)
        # Should be valid JSON that can be parsed back
        parsed = JSONParser.parse_string(result)
        assert parsed["users"][0]["name"] == "Alice"


class TestJSONParserFileOperations:
    """Test file parsing operations"""

    def test_parse_file(self):
        """Test parsing JSON from a file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"test": "value", "number": 42}')
            temp_path = f.name

        try:
            result = JSONParser.parse_file(temp_path)
            assert result["test"] == "value"
            assert result["number"] == 42
        finally:
            os.unlink(temp_path)

    def test_parse_file_with_array(self):
        """Test parsing array from file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('[1, 2, 3, 4, 5]')
            temp_path = f.name

        try:
            result = JSONParser.parse_file(temp_path)
            assert result == [1, 2, 3, 4, 5]
        finally:
            os.unlink(temp_path)

    def test_parse_file_complex_structure(self):
        """Test parsing complex structure from file"""
        data = '''
        {
            "products": [
                {
                    "id": 1,
                    "name": "Product A",
                    "price": 99.99,
                    "in_stock": true
                },
                {
                    "id": 2,
                    "name": "Product B",
                    "price": 149.99,
                    "in_stock": false
                }
            ],
            "total": 2
        }
        '''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(data)
            temp_path = f.name

        try:
            result = JSONParser.parse_file(temp_path)
            assert result["total"] == 2
            assert len(result["products"]) == 2
            assert result["products"][0]["price"] == 99.99
        finally:
            os.unlink(temp_path)


class TestJSONParserRoundTrip:
    """Test round-trip conversion (parse -> stringify -> parse)"""

    def test_roundtrip_simple_object(self):
        """Test round-trip with simple object"""
        original = {"name": "Alice", "age": 30, "active": True}
        json_str = JSONParser.to_json_string(original)
        parsed = JSONParser.parse_string(json_str)
        assert parsed == original

    def test_roundtrip_nested_structure(self):
        """Test round-trip with nested structure"""
        original = {
            "user": {
                "name": "Bob",
                "scores": [95, 87, 92],
                "metadata": {
                    "created": "2024-01-01",
                    "active": True
                }
            }
        }
        json_str = JSONParser.to_json_string(original)
        parsed = JSONParser.parse_string(json_str)
        assert parsed == original

    def test_roundtrip_array_of_objects(self):
        """Test round-trip with array of objects"""
        original = [
            {"id": 1, "value": "first"},
            {"id": 2, "value": "second"},
            {"id": 3, "value": "third"}
        ]
        json_str = JSONParser.to_json_string(original)
        parsed = JSONParser.parse_string(json_str)
        assert parsed == original

    def test_roundtrip_with_special_characters(self):
        """Test round-trip with special characters"""
        original = {
            "text": "Hello\nWorld\t!",
            "quote": 'She said "hello"',
            "path": "C:\\Users\\test"
        }
        json_str = JSONParser.to_json_string(original)
        parsed = JSONParser.parse_string(json_str)
        assert parsed == original


class TestJSONParserEdgeCases:
    """Test edge cases and boundary conditions"""
    def test_parse_deeply_nested(self):
        """Test parsing deeply nested structures"""
        # Create a deeply nested object
        nested: dict[str, Any] = {"level": 1}
        current: dict[str, Any] = nested
        for i in range(2, 20):
            next_level: dict[str, Any] = {"level": i}
            current["next"] = next_level
            current = next_level
        
        json_str = JSONParser.to_json_string(nested)
        parsed = JSONParser.parse_string(json_str)
        
        # Verify depth
        current = parsed
        for i in range(1, 20):
            assert current["level"] == i
            if i < 19:
                current = current["next"]
                current = current["next"]

    def test_parse_large_array(self):
        """Test parsing large arrays"""
        large_array = list(range(1000))
        json_str = JSONParser.to_json_string(large_array)
        parsed = JSONParser.parse_string(json_str)
        assert parsed == large_array

    def test_parse_object_with_many_keys(self):
        """Test parsing object with many keys"""
        many_keys = {f"key_{i}": i for i in range(100)}
        json_str = JSONParser.to_json_string(many_keys)
        parsed = JSONParser.parse_string(json_str)
        assert parsed == many_keys

    def test_parse_very_long_string(self):
        """Test parsing very long string"""
        long_string = "a" * 10000
        json_str = JSONParser.to_json_string(long_string)
        parsed = JSONParser.parse_string(json_str)
        assert parsed == long_string

    def test_parse_unicode_characters(self):
        """Test parsing various unicode characters"""
        unicode_data = {
            "chinese": "你好世界",
            "japanese": "こんにちは",
            "arabic": "مرحبا",
            "emoji": "😀🎉🚀",
            "symbols": "©®™"
        }
        json_str = JSONParser.to_json_string(unicode_data)
        parsed = JSONParser.parse_string(json_str)
        assert parsed == unicode_data

    def test_parse_numbers_edge_cases(self):
        """Test parsing edge case numbers"""
        numbers = {
            "zero": 0,
            "negative_zero": -0,
            "large": 9999999999999999,
            "small": -9999999999999999,
            "decimal": 0.0000001
        }
        json_str = JSONParser.to_json_string(numbers)
        parsed = JSONParser.parse_string(json_str)
        assert parsed["zero"] == 0
        assert parsed["large"] == 9999999999999999


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
