"""
Test cases for Flask REST API controllers

This module contains unit tests for all Flask API endpoints including:
- User management
- Database management
- Table management
- Record management
- Query operations
"""

import pytest
import json
import os
import tempfile
import shutil
from naturaldb.api.app import create_app
from naturaldb.entities import User, Database, Table, Record
from naturaldb.storage_system.storage import Storage


@pytest.fixture
def app():
    """Create and configure a test Flask application"""
    # Create a temporary directory for test data
    test_data_dir = tempfile.mkdtemp()
    
    # Set environment variable for test data path
    os.environ['NATURALDB_DATA_PATH'] = test_data_dir
    os.environ['NATURALDB_BASE_PATH'] = test_data_dir
    
    # Create Flask app
    app = create_app()
    app.config['TESTING'] = True
    
    yield app
    
    # Cleanup: remove test data directory
    if os.path.exists(test_data_dir):
        shutil.rmtree(test_data_dir)


@pytest.fixture
def client(app):
    """Create a test client for the Flask app"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner"""
    return app.test_cli_runner()


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self, client):
        """Test /health endpoint returns 200"""
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'


class TestUserController:
    """Test user management endpoints"""
    
    def test_create_user(self, client):
        """Test creating a new user"""
        response = client.post('/api/users/', 
                              json={'user_id': 'testuser', 'name': 'Test User'})
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['user']['id'] == 'testuser'
    
    def test_create_user_missing_id(self, client):
        """Test creating user without user_id returns 400"""
        response = client.post('/api/users/', json={'name': 'Test User'})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_create_duplicate_user(self, client):
        """Test creating duplicate user returns 409"""
        client.post('/api/users/', json={'user_id': 'testuser'})
        response = client.post('/api/users/', json={'user_id': 'testuser'})
        assert response.status_code == 409
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_list_users(self, client):
        """Test listing all users"""
        # Create some users
        client.post('/api/users/', json={'user_id': 'user1'})
        client.post('/api/users/', json={'user_id': 'user2'})
        
        response = client.get('/api/users/')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['count'] == 2
        user_ids = [u['id'] for u in data['users']]
        assert 'user1' in user_ids
        assert 'user2' in user_ids
    
    def test_get_user(self, client):
        """Test getting specific user info"""
        client.post('/api/users/', json={'user_id': 'testuser'})
        
        response = client.get('/api/users/testuser')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['user']['id'] == 'testuser'
    
    def test_get_nonexistent_user(self, client):
        """Test getting user that doesn't exist returns 404"""
        response = client.get('/api/users/nonexistent')
        assert response.status_code == 404
    
    def test_get_user_stats(self, client):
        """Test getting user statistics"""
        client.post('/api/users/', json={'user_id': 'testuser'})
        
        response = client.get('/api/users/testuser/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'statistics' in data
        assert data['statistics']['databases'] == 0
    
    def test_delete_user(self, client):
        """Test deleting a user"""
        client.post('/api/users/', json={'user_id': 'testuser'})
        
        response = client.delete('/api/users/testuser')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Verify user is deleted
        response = client.get('/api/users/testuser')
        assert response.status_code == 404


class TestDatabaseController:
    """Test database management endpoints"""
    
    def test_create_database(self, client):
        """Test creating a new database"""
        # First create a user
        client.post('/api/users/', json={'user_id': 'testuser'})
        
        response = client.post('/api/databases/',
                              json={'user_id': 'testuser', 'db_name': 'testdb'})
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['db_name'] == 'testdb'
    
    def test_create_database_missing_params(self, client):
        """Test creating database without required params returns 400"""
        response = client.post('/api/databases/', json={'user_id': 'testuser'})
        assert response.status_code == 400
    
    def test_list_databases(self, client):
        """Test listing databases for a user"""
        client.post('/api/users/', json={'user_id': 'testuser'})
        client.post('/api/databases/', json={'user_id': 'testuser', 'db_name': 'db1'})
        client.post('/api/databases/', json={'user_id': 'testuser', 'db_name': 'db2'})
        
        response = client.get('/api/databases/?user_id=testuser')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'db1' in data['databases']
        assert 'db2' in data['databases']
    
    def test_list_databases_missing_user_id(self, client):
        """Test listing databases without user_id returns 400"""
        response = client.get('/api/databases/')
        assert response.status_code == 400
    
    def test_get_database(self, client):
        """Test getting database info"""
        client.post('/api/users/', json={'user_id': 'testuser'})
        client.post('/api/databases/', json={'user_id': 'testuser', 'db_name': 'testdb'})
        
        response = client.get('/api/databases/testuser/testdb')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['exists'] is True
    
    def test_get_nonexistent_database(self, client):
        """Test getting database that doesn't exist returns 404"""
        client.post('/api/users/', json={'user_id': 'testuser'})
        
        response = client.get('/api/databases/testuser/nonexistent')
        assert response.status_code == 404
    
    def test_delete_database(self, client):
        """Test deleting a database"""
        client.post('/api/users/', json={'user_id': 'testuser'})
        client.post('/api/databases/', json={'user_id': 'testuser', 'db_name': 'testdb'})
        
        response = client.delete('/api/databases/testuser/testdb')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True


class TestTableController:
    """Test table management endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self, client):
        """Setup: create user and database for table tests"""
        client.post('/api/users/', json={'user_id': 'testuser'})
        client.post('/api/databases/', json={'user_id': 'testuser', 'db_name': 'testdb'})
    
    def test_create_table(self, client):
        """Test creating a new table"""
        response = client.post('/api/databases/testuser/testdb/tables/',
                              json={'table_name': 'products'})
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_create_table_with_indexes(self, client):
        """Test creating table with indexes"""
        response = client.post('/api/databases/testuser/testdb/tables/',
                              json={'table_name': 'products', 'indexes': ['category', 'price']})
        assert response.status_code == 201
    
    def test_create_table_missing_name(self, client):
        """Test creating table without name returns 400"""
        response = client.post('/api/databases/testuser/testdb/tables/', json={})
        assert response.status_code == 400
    
    def test_list_tables(self, client):
        """Test listing tables in a database"""
        client.post('/api/databases/testuser/testdb/tables/', json={'table_name': 'table1'})
        client.post('/api/databases/testuser/testdb/tables/', json={'table_name': 'table2'})
        
        response = client.get('/api/databases/testuser/testdb/tables/')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'table1' in data['tables']
        assert 'table2' in data['tables']
    
    def test_get_table_info(self, client):
        """Test getting table information"""
        client.post('/api/databases/testuser/testdb/tables/', json={'table_name': 'products'})
        
        response = client.get('/api/databases/testuser/testdb/tables/products')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['table_name'] == 'products'
        assert data['record_count'] >= 0


class TestRecordController:
    """Test record management endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self, client):
        """Setup: create user, database, and table for record tests"""
        client.post('/api/users/', json={'user_id': 'testuser'})
        client.post('/api/databases/', json={'user_id': 'testuser', 'db_name': 'testdb'})
        client.post('/api/databases/testuser/testdb/tables/', json={'table_name': 'products'})
    
    def test_create_record(self, client):
        """Test creating a new record"""
        response = client.post('/api/databases/testuser/testdb/tables/products/records/',
                              json={
                                  'id': '1',
                                  'data': {'name': 'Laptop', 'price': 999.99}
                              })
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['record']['id'] == '1'
    
    def test_create_record_missing_id(self, client):
        """Test creating record without id returns 400"""
        response = client.post('/api/databases/testuser/testdb/tables/products/records/',
                              json={'data': {'name': 'Laptop'}})
        assert response.status_code == 400
    
    def test_create_record_missing_data(self, client):
        """Test creating record without data returns 400"""
        response = client.post('/api/databases/testuser/testdb/tables/products/records/',
                              json={'id': '1'})
        assert response.status_code == 400
    
    def test_list_records(self, client):
        """Test listing all records"""
        # Create some records
        client.post('/api/databases/testuser/testdb/tables/products/records/',
                   json={'id': '1', 'data': {'name': 'Laptop', 'price': 999}})
        client.post('/api/databases/testuser/testdb/tables/products/records/',
                   json={'id': '2', 'data': {'name': 'Mouse', 'price': 29}})
        
        response = client.get('/api/databases/testuser/testdb/tables/products/records/')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['count'] == 2
    
    def test_list_records_with_pagination(self, client):
        """Test listing records with pagination"""
        # Create multiple records
        for i in range(5):
            client.post('/api/databases/testuser/testdb/tables/products/records/',
                       json={'id': str(i), 'data': {'name': f'Product {i}'}})
        
        response = client.get('/api/databases/testuser/testdb/tables/products/records/?limit=2&offset=1')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['count'] == 2
        assert data['total'] == 5
    
    def test_get_record(self, client):
        """Test getting a specific record"""
        client.post('/api/databases/testuser/testdb/tables/products/records/',
                   json={'id': '1', 'data': {'name': 'Laptop', 'price': 999}})
        
        response = client.get('/api/databases/testuser/testdb/tables/products/records/1')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['record']['id'] == '1'
        assert data['record']['name'] == 'Laptop'
    
    def test_get_nonexistent_record(self, client):
        """Test getting record that doesn't exist returns 404"""
        response = client.get('/api/databases/testuser/testdb/tables/products/records/999')
        assert response.status_code == 404
    
    def test_update_record(self, client):
        """Test updating a record"""
        client.post('/api/databases/testuser/testdb/tables/products/records/',
                   json={'id': '1', 'data': {'name': 'Laptop', 'price': 999}})
        
        response = client.put('/api/databases/testuser/testdb/tables/products/records/1',
                             json={'data': {'name': 'Gaming Laptop', 'price': 1299}})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['record']['name'] == 'Gaming Laptop'
    
    def test_update_nonexistent_record(self, client):
        """Test updating record that doesn't exist returns 404"""
        response = client.put('/api/databases/testuser/testdb/tables/products/records/999',
                             json={'data': {'name': 'Product'}})
        assert response.status_code == 404
    
    def test_delete_record(self, client):
        """Test deleting a record"""
        client.post('/api/databases/testuser/testdb/tables/products/records/',
                   json={'id': '1', 'data': {'name': 'Laptop'}})
        
        response = client.delete('/api/databases/testuser/testdb/tables/products/records/1')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Verify record is deleted
        response = client.get('/api/databases/testuser/testdb/tables/products/records/1')
        assert response.status_code == 404
    
    def test_delete_nonexistent_record(self, client):
        """Test deleting record that doesn't exist returns 404"""
        response = client.delete('/api/databases/testuser/testdb/tables/products/records/999')
        assert response.status_code == 404


class TestQueryController:
    """Test query endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self, client):
        """Setup: create test data for query tests"""
        client.post('/api/users/', json={'user_id': 'testuser'})
        client.post('/api/databases/', json={'user_id': 'testuser', 'db_name': 'testdb'})
        client.post('/api/databases/testuser/testdb/tables/', json={'table_name': 'products'})
        
        # Create test records
        records = [
            {'id': '1', 'data': {'name': 'Laptop', 'price': 999, 'category': 'Electronics'}},
            {'id': '2', 'data': {'name': 'Mouse', 'price': 29, 'category': 'Electronics'}},
            {'id': '3', 'data': {'name': 'Desk', 'price': 199, 'category': 'Furniture'}},
            {'id': '4', 'data': {'name': 'Chair', 'price': 149, 'category': 'Furniture'}},
        ]
        for record in records:
            client.post('/api/databases/testuser/testdb/tables/products/records/', json=record)
    
    def test_query_with_filters(self, client):
        """Test query with filter conditions"""
        response = client.post('/api/databases/testuser/testdb/query/',
                              json={
                                  'table': 'products',
                                  'filters': [
                                      {'field': 'category', 'operator': 'eq', 'value': 'Electronics'}
                                  ]
                              })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['count'] == 2
    
    def test_query_with_multiple_filters(self, client):
        """Test query with multiple filter conditions"""
        response = client.post('/api/databases/testuser/testdb/query/',
                              json={
                                  'table': 'products',
                                  'filters': [
                                      {'field': 'category', 'operator': 'eq', 'value': 'Electronics'},
                                      {'field': 'price', 'operator': 'lt', 'value': 100}
                                  ]
                              })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['count'] == 1
        assert data['results'][0]['name'] == 'Mouse'
    
    def test_query_with_sort(self, client):
        """Test query with sorting"""
        response = client.post('/api/databases/testuser/testdb/query/',
                              json={
                                  'table': 'products',
                                  'sort': [{'field': 'price', 'direction': 'desc'}]
                              })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        # Should be sorted by price descending
        # Verify that prices are in descending order
        prices = [r['price'] for r in data['results']]
        assert prices == sorted(prices, reverse=True), f"Prices not in descending order: {prices}"
    
    def test_query_with_limit(self, client):
        """Test query with limit"""
        response = client.post('/api/databases/testuser/testdb/query/',
                              json={
                                  'table': 'products',
                                  'limit': 2
                              })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['count'] == 2
    
    def test_query_with_skip(self, client):
        """Test query with skip offset"""
        response = client.post('/api/databases/testuser/testdb/query/',
                              json={
                                  'table': 'products',
                                  'skip': 2
                              })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['count'] == 2
    
    def test_query_with_projection(self, client):
        """Test query with field projection"""
        response = client.post('/api/databases/testuser/testdb/query/',
                              json={
                                  'table': 'products',
                                  'project': ['name', 'price']
                              })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        # Check that only projected fields are returned
        for result in data['results']:
            assert 'name' in result
            assert 'price' in result
            assert 'category' not in result
    
    def test_query_missing_table(self, client):
        """Test query without table name returns 400"""
        response = client.post('/api/databases/testuser/testdb/query/',
                              json={'filters': []})
        assert response.status_code == 400
    
    def test_count_query(self, client):
        """Test count query"""
        response = client.post('/api/databases/testuser/testdb/query/count',
                              json={
                                  'table': 'products',
                                  'filters': [
                                      {'field': 'category', 'operator': 'eq', 'value': 'Electronics'}
                                  ]
                              })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['count'] == 2
    
    def test_aggregate_query(self, client):
        """Test aggregation query"""
        response = client.post('/api/databases/testuser/testdb/query/aggregate',
                              json={
                                  'table': 'products',
                                  'group_by': ['category'],
                                  'aggregations': {
                                      'total_price': {'field': 'price', 'operation': 'sum'},
                                      'count': {'field': '*', 'operation': 'count'}
                                  }
                              })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['count'] == 2  # Two categories
        
        # Find Electronics group
        electronics = next((r for r in data['results'] if r['category'] == 'Electronics'), None)
        assert electronics is not None
        assert electronics['count'] == 2
        assert electronics['total_price'] == 1028  # 999 + 29
    
    def test_aggregate_query_missing_params(self, client):
        """Test aggregation without required params returns 400"""
        response = client.post('/api/databases/testuser/testdb/query/aggregate',
                              json={'table': 'products'})
        assert response.status_code == 400


class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_complete_workflow(self, client):
        """Test a complete workflow: create user -> db -> table -> records -> query"""
        # 1. Create user
        response = client.post('/api/users/', json={'user_id': 'alice'})
        assert response.status_code == 201
        
        # 2. Create database
        response = client.post('/api/databases/', 
                              json={'user_id': 'alice', 'db_name': 'shop'})
        assert response.status_code == 201
        
        # 3. Create table
        response = client.post('/api/databases/alice/shop/tables/',
                              json={'table_name': 'products'})
        assert response.status_code == 201
        
        # 4. Insert records
        products = [
            {'id': '1', 'data': {'name': 'Laptop', 'price': 999, 'stock': 10}},
            {'id': '2', 'data': {'name': 'Mouse', 'price': 29, 'stock': 50}},
            {'id': '3', 'data': {'name': 'Keyboard', 'price': 79, 'stock': 30}},
        ]
        for product in products:
            response = client.post('/api/databases/alice/shop/tables/products/records/',
                                  json=product)
            assert response.status_code == 201
        
        # 5. Query records
        response = client.post('/api/databases/alice/shop/query/',
                              json={
                                  'table': 'products',
                                  'filters': [
                                      {'field': 'price', 'operator': 'lt', 'value': 100}
                                  ],
                                  'sort': [{'field': 'price', 'direction': 'asc'}]
                              })
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['count'] == 2
        # Verify prices are in ascending order
        prices = [r['price'] for r in data['results']]
        assert prices == sorted(prices), f"Prices not in ascending order: {prices}"
        
        # 6. Update record
        response = client.put('/api/databases/alice/shop/tables/products/records/1',
                             json={'data': {'name': 'Gaming Laptop', 'price': 1299, 'stock': 5}})
        assert response.status_code == 200
        
        # 7. Get user stats
        response = client.get('/api/users/alice/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['statistics']['databases'] == 1
        assert data['statistics']['tables'] == 1
        assert data['statistics']['records'] == 3
        
        # 8. Delete record
        response = client.delete('/api/databases/alice/shop/tables/products/records/3')
        assert response.status_code == 200
        
        # 9. Verify deletion
        response = client.get('/api/databases/alice/shop/tables/products/records/')
        data = json.loads(response.data)
        assert data['count'] == 2
