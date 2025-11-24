"""
User Controller
Handles user management operations
"""

from flask import Blueprint, request, jsonify
from ...storage_system.storage import Storage
from ...entities import User
from ...env_config import config
import os

user_bp = Blueprint('user', __name__)


def get_storage():
    """Get base path for storage"""
    return config.get_data_path()


@user_bp.route('/', methods=['GET'])
def list_users():
    """
    List all users
    
    Returns all directories in the base path as users
    """
    try:
        base_path = get_storage()
        
        # List all directories in base path
        users = []
        if os.path.exists(base_path):
            for entry in os.listdir(base_path):
                user_path = os.path.join(base_path, entry)
                if os.path.isdir(user_path):
                    # Get database count
                    db_count = 0
                    if os.path.exists(user_path):
                        db_count = len([d for d in os.listdir(user_path) 
                                      if os.path.isdir(os.path.join(user_path, d))])
                    
                    users.append({
                        'id': entry,
                        'name': entry,
                        'database_count': db_count
                    })
        
        return jsonify({
            'success': True,
            'count': len(users),
            'users': users
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@user_bp.route('/', methods=['POST'])
def create_user():
    """
    Create a new user
    
    Request body:
        {
            "user_id": "string",  // required
            "name": "string"      // optional
        }
    """
    data = request.get_json()
    
    if not data or 'user_id' not in data:
        return jsonify({'error': 'user_id is required'}), 400
    
    user_id = data['user_id']
    user_name = data.get('name', user_id)
    
    try:
        base_path = get_storage()
        user_path = os.path.join(base_path, user_id)
        
        # Check if user already exists
        if os.path.exists(user_path):
            return jsonify({'error': f'User {user_id} already exists'}), 409
        
        # Create user directory
        os.makedirs(user_path, exist_ok=True)
        
        return jsonify({
            'success': True,
            'message': f'User {user_id} created successfully',
            'user': {
                'id': user_id,
                'name': user_name
            }
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@user_bp.route('/<user_id>', methods=['GET'])
def get_user(user_id):
    """Get user information including databases"""
    try:
        base_path = get_storage()
        user_path = os.path.join(base_path, user_id)
        
        # Check if user exists
        if not os.path.exists(user_path):
            return jsonify({'error': f'User {user_id} not found'}), 404
        
        # Get databases
        databases = []
        if os.path.exists(user_path):
            for entry in os.listdir(user_path):
                db_path = os.path.join(user_path, entry)
                if os.path.isdir(db_path):
                    # Get table count
                    table_count = 0
                    if os.path.exists(db_path):
                        table_count = len([t for t in os.listdir(db_path) 
                                         if os.path.isdir(os.path.join(db_path, t))])
                    
                    databases.append({
                        'name': entry,
                        'table_count': table_count
                    })
        
        return jsonify({
            'success': True,
            'user': {
                'id': user_id,
                'name': user_id,
                'database_count': len(databases),
                'databases': databases
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@user_bp.route('/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Delete a user and all their databases
    
    WARNING: This will delete all data for this user!
    """
    try:
        base_path = get_storage()
        user_path = os.path.join(base_path, user_id)
        
        # Check if user exists
        if not os.path.exists(user_path):
            return jsonify({'error': f'User {user_id} not found'}), 404
        
        # Delete user directory and all contents
        import shutil
        shutil.rmtree(user_path)
        
        return jsonify({
            'success': True,
            'message': f'User {user_id} and all their data deleted successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@user_bp.route('/<user_id>/stats', methods=['GET'])
def get_user_stats(user_id):
    """
    Get detailed statistics for a user
    
    Returns database count, table count, and record count
    """
    try:
        base_path = get_storage()
        user_path = os.path.join(base_path, user_id)
        
        # Check if user exists
        if not os.path.exists(user_path):
            return jsonify({'error': f'User {user_id} not found'}), 404
        
        total_dbs = 0
        total_tables = 0
        total_records = 0
        
        # Count databases, tables, and records
        if os.path.exists(user_path):
            for db_entry in os.listdir(user_path):
                db_path = os.path.join(user_path, db_entry)
                if os.path.isdir(db_path):
                    total_dbs += 1
                    
                    # Count tables
                    for table_entry in os.listdir(db_path):
                        table_path = os.path.join(db_path, table_entry)
                        if os.path.isdir(table_path):
                            total_tables += 1
                            
                            # Count records (JSON files excluding metadata.json)
                            for file_entry in os.listdir(table_path):
                                if file_entry.endswith('.json') and file_entry != 'metadata.json':
                                    total_records += 1
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'statistics': {
                'databases': total_dbs,
                'tables': total_tables,
                'records': total_records
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
