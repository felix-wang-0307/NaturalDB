"""
Test cases for Layer 2 Query Engine's chainable API
Converted from demo_chainable_api.py
"""

import pytest
import os
import tempfile
import shutil
from naturaldb.entities import User, Database, Record
from naturaldb.query_engine.query_engine import QueryEngine


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data"""
    temp_dir = tempfile.mkdtemp()
    os.environ['NATURALDB_DATA_PATH'] = temp_dir
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def query_engine(temp_data_dir):
    """Create a query engine with test data"""
    user = User(id='test_user', name='Test User')
    db = Database(name='test_db')
    engine = QueryEngine(user, db)
    
    # Insert test data
    users = [
        Record(id='1', data={'name': 'Alice', 'age': 28, 'city': 'New York', 'active': True}),
        Record(id='2', data={'name': 'Bob', 'age': 35, 'city': 'San Francisco', 'active': True}),
        Record(id='3', data={'name': 'Charlie', 'age': 42, 'city': 'New York', 'active': False}),
        Record(id='4', data={'name': 'Diana', 'age': 31, 'city': 'Boston', 'active': True}),
        Record(id='5', data={'name': 'Eve', 'age': 25, 'city': 'New York', 'active': True}),
    ]
    
    for record in users:
        engine.insert('users', record)
    
    return engine


class TestChainableAPIBasics:
    """Test basic chainable API operations"""
    
    def test_basic_filter_and_sort(self, query_engine):
        """Test basic filtering and sorting"""
        results = query_engine.table('users').filter_by('active', True).sort('age').all()
        
        assert len(results) == 4
        # Check that results are sorted by age
        ages = [r.data['age'] for r in results]
        assert ages == sorted(ages)
    
    def test_where_clause_sql_style(self, query_engine):
        """Test WHERE clause (SQL style)"""
        results = query_engine.table('users').where('city', 'New York').order_by('name').all()
        
        assert len(results) == 3
        names = [r.data['name'] for r in results]
        assert names == sorted(names)
    
    def test_complex_conditions(self, query_engine):
        """Test complex conditions (age > 30)"""
        results = query_engine.table('users').filter_by('age', 30, 'gt').sort('age', False).all()
        
        assert len(results) == 3
        # Check descending order
        ages = [r.data['age'] for r in results]
        assert ages == sorted(ages, reverse=True)
    
    def test_limit_results(self, query_engine):
        """Test limiting results (TOP 3)"""
        results = query_engine.table('users').sort('age').limit(3).all()
        
        assert len(results) == 3
        # Should get the 3 youngest users
        assert results[0].data['name'] == 'Eve'  # age 25
        assert results[1].data['name'] == 'Alice'  # age 28
        assert results[2].data['name'] == 'Diana'  # age 31


class TestChainableAPIProjection:
    """Test field projection in chainable API"""
    
    def test_field_projection(self, query_engine):
        """Test field projection (select specific fields)"""
        results = query_engine.table('users').filter_by('active', True).select(['name', 'city'])
        
        assert len(results) == 4
        # Check that only selected fields are present
        for r in results:
            assert 'name' in r
            assert 'city' in r
            assert 'age' not in r  # age should not be included
            assert 'active' not in r  # active should not be included
    
    def test_to_dict_conversion(self, query_engine):
        """Test conversion to dictionary"""
        results = query_engine.table('users').limit(2).to_dict()
        
        assert len(results) == 2
        assert isinstance(results, list)
        assert all(isinstance(r, dict) for r in results)


class TestChainableAPIAggregation:
    """Test aggregation operations in chainable API"""
    
    def test_count(self, query_engine):
        """Test count operation"""
        count = query_engine.table('users').filter_by('active', True).count()
        
        assert count == 4
    
    def test_first_record(self, query_engine):
        """Test getting first record"""
        youngest = query_engine.table('users').sort('age').first()
        
        assert youngest is not None
        assert youngest.data['name'] == 'Eve'
        assert youngest.data['age'] == 25
    
    def test_last_record(self, query_engine):
        """Test getting last record"""
        oldest = query_engine.table('users').sort('age').last()
        
        assert oldest is not None
        assert oldest.data['name'] == 'Charlie'
        assert oldest.data['age'] == 42


class TestChainableAPIComplex:
    """Test complex chainable operations"""
    
    def test_complex_chain(self, query_engine):
        """Test complex chain of operations"""
        results = query_engine.table('users') \
            .filter_by('city', 'New York') \
            .filter_by('active', True) \
            .sort('age') \
            .limit(2) \
            .select(['name', 'age'])
        
        assert len(results) == 2
        # Should get the 2 youngest active users in New York
        assert results[0]['name'] == 'Eve'  # age 25
        assert results[1]['name'] == 'Alice'  # age 28
        
        # Check only selected fields are present
        for r in results:
            assert set(r.keys()) == {'name', 'age'}
    
    def test_multiple_filters(self, query_engine):
        """Test applying multiple filters"""
        results = query_engine.table('users') \
            .filter_by('active', True) \
            .filter_by('age', 30, 'lt') \
            .all()
        
        assert len(results) == 2  # Eve (25) and Alice (28)
    
    def test_skip_and_limit(self, query_engine):
        """Test skip and limit together"""
        # Get users 2-3 when sorted by age
        results = query_engine.table('users').sort('age').skip(1).limit(2).all()
        
        assert len(results) == 2
        assert results[0].data['age'] == 28  # Alice
        assert results[1].data['age'] == 31  # Diana


class TestChainableAPIEdgeCases:
    """Test edge cases in chainable API"""
    
    def test_empty_results(self, query_engine):
        """Test queries that return no results"""
        results = query_engine.table('users').filter_by('age', 100, 'gt').all()
        assert results == []
    
    def test_nonexistent_table(self, query_engine):
        """Test querying non-existent table"""
        results = query_engine.table('nonexistent').all()
        assert results == []
    
    def test_first_on_empty_results(self, query_engine):
        """Test first() on empty results"""
        result = query_engine.table('users').filter_by('age', 100, 'gt').first()
        assert result is None
    
    def test_last_on_empty_results(self, query_engine):
        """Test last() on empty results"""
        result = query_engine.table('users').filter_by('age', 100, 'gt').last()
        assert result is None
    
    def test_count_on_empty_results(self, query_engine):
        """Test count() on empty results"""
        count = query_engine.table('users').filter_by('age', 100, 'gt').count()
        assert count == 0
