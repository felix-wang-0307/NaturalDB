"""
Database Controller
Handles database CRUD operations
"""

from flask import Blueprint, request, jsonify
from ...entities import User, Database
from ...storage_system.storage import Storage
import os

database_bp = Blueprint('database', __name__)
storage = Storage()


@database_bp.route('/', methods=['GET'])
def list_databases():
    """
    List all databases for a user
    
    Query params:
        user_id: User ID (required)
    """
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    try:
        user = User(id=user_id, name=user_id)
        user_path = Storage.get_path(user)
        
        databases = []
        if os.path.exists(user_path):
            for entry in os.listdir(user_path):
                db_path = os.path.join(user_path, entry)
                if os.path.isdir(db_path):
                    databases.append(entry)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'databases': databases
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@database_bp.route('/', methods=['POST'])
def create_database():
    """
    Create a new database
    
    Request body:
        {
            "user_id": "string",
            "db_name": "string"
        }
    """
    data = request.get_json()
    
    if not data or 'user_id' not in data or 'db_name' not in data:
        return jsonify({'error': 'user_id and db_name are required'}), 400
    
    user_id = data['user_id']
    db_name = data['db_name']
    
    try:
        user = User(id=user_id, name=user_id)
        database = Database(name=db_name)
        
        storage.create_database(user, database)
        
        return jsonify({
            'success': True,
            'message': f'Database {db_name} created successfully',
            'user_id': user_id,
            'db_name': db_name
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@database_bp.route('/<user_id>/<db_name>', methods=['GET'])
def get_database(user_id, db_name):
    """Get database information"""
    try:
        user = User(id=user_id, name=user_id)
        database = Database(name=db_name)
        
        # Check if database exists
        db_path = Storage.get_path(user, database)
        if not os.path.exists(db_path):
            return jsonify({'error': 'Database not found'}), 404
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'db_name': db_name,
            'exists': True
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@database_bp.route('/<user_id>/<db_name>', methods=['DELETE'])
def delete_database(user_id, db_name):
    """Delete a database"""
    try:
        user = User(id=user_id, name=user_id)
        database = Database(name=db_name)
        
        storage.delete_database(user, database)
        
        return jsonify({
            'success': True,
            'message': f'Database {db_name} deleted successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
