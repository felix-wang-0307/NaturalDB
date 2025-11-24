"""
Table Controller
Handles table CRUD operations
"""

from flask import Blueprint, request, jsonify
from ...entities import User, Database, Table
from ...query_engine.query_engine import QueryEngine

table_bp = Blueprint('table', __name__)


@table_bp.route('/', methods=['GET'])
def list_tables(user_id, db_name):
    """List all tables in a database"""
    try:
        user = User(id=user_id, name=user_id)
        database = Database(name=db_name)
        engine = QueryEngine(user, database)
        
        tables = engine.list_tables()
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'db_name': db_name,
            'tables': tables
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@table_bp.route('/', methods=['POST'])
def create_table(user_id, db_name):
    """
    Create a new table
    
    Request body:
        {
            "table_name": "string",
            "indexes": {}  // optional
        }
    """
    data = request.get_json()
    
    if not data or 'table_name' not in data:
        return jsonify({'error': 'table_name is required'}), 400
    
    table_name = data['table_name']
    indexes = data.get('indexes', {})
    
    try:
        user = User(id=user_id, name=user_id)
        database = Database(name=db_name)
        table = Table(name=table_name, indexes=indexes)
        
        engine = QueryEngine(user, database)
        success = engine.create_table(table)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Table {table_name} created successfully',
                'table_name': table_name
            }), 201
        else:
            return jsonify({'error': 'Failed to create table'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@table_bp.route('/<table_name>', methods=['GET'])
def get_table_info(user_id, db_name, table_name):
    """Get table information"""
    try:
        user = User(id=user_id, name=user_id)
        database = Database(name=db_name)
        engine = QueryEngine(user, database)
        
        tables = engine.list_tables()
        if table_name not in tables:
            return jsonify({'error': 'Table not found'}), 404
        
        # Get record count
        records = engine.find_all(table_name)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'db_name': db_name,
            'table_name': table_name,
            'record_count': len(records),
            'exists': True
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@table_bp.route('/<table_name>', methods=['DELETE'])
def delete_table(user_id, db_name, table_name):
    """Delete a table (note: not implemented in Storage yet)"""
    return jsonify({
        'error': 'Table deletion not yet implemented'
    }), 501
