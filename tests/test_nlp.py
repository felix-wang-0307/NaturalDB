"""
Test NLP Interface
Tests for natural language query processing
"""

import pytest
import os
from naturaldb.entities import User, Database
from naturaldb.nlp_interface.naturaldb import NaturalDB


class TestNaturalDB:
    """Test NaturalDB main interface"""
    
    @pytest.mark.skip(reason="Module-level import caching makes this test unreliable")
    def test_initialization_without_api_key(self):
        """Test NaturalDB initialization without OpenAI API key"""
        # Temporarily remove API key
        old_key = os.environ.get('OPENAI_API_KEY')
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        
        try:
            # Force module reload to pick up environment change
            import sys
            if 'naturaldb.nlp_interface.naturaldb' in sys.modules:
                del sys.modules['naturaldb.nlp_interface.naturaldb']
            
            from naturaldb.nlp_interface.naturaldb import NaturalDB
            
            user = User(id="test_user", name="Test User")
            database = Database("test_db")
            
            db = NaturalDB(user, database, api_key=None)  # Explicitly pass None
            
            # NLP should be disabled
            assert not db.nlp_enabled
            assert db.engine is not None  # QueryEngine should still work
            
        finally:
            # Restore API key
            if old_key:
                os.environ['OPENAI_API_KEY'] = old_key
    
    def test_initialization_with_api_key(self):
        """Test NaturalDB initialization with OpenAI API key"""
        # Skip if no API key
        if not os.getenv('OPENAI_API_KEY'):
            pytest.skip("OPENAI_API_KEY not set")
        
        user = User(id="test_user", name="Test User")
        database = Database("test_db")
        
        db = NaturalDB(user, database)
        
        # NLP should be enabled
        assert db.nlp_enabled
        assert db.processor is not None
        assert db.executor is not None
        assert db.tools is not None
    
    def test_query_without_api_key(self):
        """Test query method without API key"""
        old_key = os.environ.get('OPENAI_API_KEY')
        if 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']
        
        try:
            user = User(id="test_user", name="Test User")
            database = Database("test_db")
            
            db = NaturalDB(user, database)
            result = db.query("show me all tables")
            
            assert not result['success']
            assert 'error' in result
            
        finally:
            if old_key:
                os.environ['OPENAI_API_KEY'] = old_key
    
    def test_is_nlp_available_static_method(self):
        """Test static method for checking NLP availability"""
        # This will depend on whether API key is set
        available = NaturalDB.is_nlp_available()
        
        if os.getenv('OPENAI_API_KEY'):
            assert available
        else:
            assert not available
    
    def test_get_context_summary(self):
        """Test database context summary"""
        user = User(id="demo_user", name="Demo User")
        database = Database("amazon")
        
        db = NaturalDB(user, database)
        summary = db.get_context_summary()
        
        assert isinstance(summary, str)
        assert "Database:" in summary or "empty" in summary.lower()


class TestToolRegistry:
    """Test tool registry functionality"""
    
    def test_get_all_tools(self):
        """Test getting all tools from registry"""
        from naturaldb.nlp_interface.tool_registry import DatabaseToolRegistry
        from naturaldb.entities import User, Database
        from naturaldb.query_engine.query_engine import QueryEngine
        
        user = User(id="test_user", name="Test User")
        database = Database("test_db")
        engine = QueryEngine(user, database)
        
        tools = DatabaseToolRegistry.get_all_tools(engine)
        
        assert isinstance(tools, list)
        assert len(tools) > 0
        
        # Check that each tool has required fields
        for tool in tools:
            assert 'type' in tool
            assert tool['type'] == 'function'
            assert 'function' in tool
            assert 'name' in tool['function']
            assert 'description' in tool['function']
            assert 'parameters' in tool['function']


class TestExecutor:
    """Test function executor"""
    
    def test_execute_simple_operation(self):
        """Test executing a simple operation"""
        from naturaldb.nlp_interface.executor import FunctionExecutor
        from naturaldb.entities import User, Database
        from naturaldb.query_engine.query_engine import QueryEngine
        
        user = User(id="demo_user", name="Demo User")
        database = Database("amazon")
        engine = QueryEngine(user, database)
        
        executor = FunctionExecutor(engine)
        
        # Execute list_tables
        result = executor.execute("list_tables", {})
        
        assert result['success']
        assert 'results' in result  # Changed from 'result' to 'results'
        assert isinstance(result['results'], list)
    
    def test_serialize_result(self):
        """Test result serialization"""
        from naturaldb.nlp_interface.executor import FunctionExecutor
        from naturaldb.entities import User, Database, Record
        from naturaldb.query_engine.query_engine import QueryEngine
        
        user = User(id="test_user", name="Test User")
        database = Database("test_db")
        engine = QueryEngine(user, database)
        
        executor = FunctionExecutor(engine)
        
        # Test list serialization (returns wrapped format)
        result = executor._serialize_result([1, 2, 3])
        assert result['success']
        assert 'results' in result
        assert result['results'] == [1, 2, 3]
        
        # Test dict serialization
        result = executor._serialize_result({"a": 1, "b": 2})
        assert result['success']
        assert 'result' in result
        assert result['result'] == {"a": 1, "b": 2}
        
        # Test Record serialization
        record = Record(id="1", data={"name": "test"})
        result = executor._serialize_result(record)
        assert result['success']
        assert 'result' in result
        assert isinstance(result['result'], dict)
        assert result['result']['id'] == "1"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
